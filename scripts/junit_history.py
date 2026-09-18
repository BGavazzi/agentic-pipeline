#!/usr/bin/env python3
"""Normalize one JUnit XML report into versioned per-test evidence.

This is an evidence adapter, not a retry policy and not a test-selection
authority. It accepts the common JUnit ``testsuite``/``testcase`` shape,
rejects ambiguous or unsafe input, and emits the history shape consumed by
``flake_gate.py``. Cross-run persistence remains a separate concern.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from defusedxml import ElementTree as ET

SCHEMA_VERSION = 1
SHA_RE = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")
# Pytest parameterized IDs may contain spaces, commas and JSON punctuation.
# Reject only control whitespace so IDs remain safe single-line evidence keys.
TEST_ID_RE = re.compile(r"^[^\r\n\t]{1,240}$")


def _sha(value: str, label: str) -> None:
    if not isinstance(value, str) or not SHA_RE.fullmatch(value):
        raise ValueError(f"{label} must be a full hexadecimal commit SHA")


def _timestamp(value: str) -> str:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        raise ValueError("occurred_at requires a timezone")
    return parsed.astimezone(timezone.utc).isoformat()


def _duration_ms(value: str | None) -> int:
    if value is None or value == "":
        return 0
    try:
        seconds = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("JUnit testcase time must be numeric") from exc
    if not math.isfinite(seconds) or seconds < 0 or seconds > 86_400:
        raise ValueError("JUnit testcase time is out of bounds")
    return round(seconds * 1000)


def _test_id(case: ET.Element) -> str:
    name = case.attrib.get("name", "")
    classname = case.attrib.get("classname", "")
    test_id = f"{classname}::{name}" if classname else name
    if not TEST_ID_RE.fullmatch(test_id):
        raise ValueError("JUnit testcase requires a bounded single-line name")
    return test_id


def _status(case: ET.Element) -> str:
    # An error is the strongest failure classification when malformed tools
    # emit more than one child node. Do not infer pass from a missing result
    # if an explicit failure/error/skipped node is present.
    if case.find("error") is not None:
        return "error"
    if case.find("failure") is not None:
        return "fail"
    if case.find("skipped") is not None:
        return "skip"
    return "pass"


def parse_junit(path: Path) -> list[dict[str, Any]]:
    raw = path.read_bytes()
    # Keep the explicit declaration check as a clear contract, and use
    # defusedxml for the parser-level XXE/entity-expansion defense.
    upper = raw.upper()
    if b"<!DOCTYPE" in upper or b"<!ENTITY" in upper:
        raise ValueError("JUnit XML must not contain DTD or entity declarations")
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as exc:
        raise ValueError("JUnit XML is malformed") from exc
    cases = list(root.iter("testcase"))
    if not cases:
        raise ValueError("JUnit report contains no testcase elements")
    tests: list[dict[str, Any]] = []
    seen: set[str] = set()
    for case in cases:
        test_id = _test_id(case)
        if test_id in seen:
            raise ValueError(f"duplicate JUnit testcase id: {test_id}")
        seen.add(test_id)
        status = _status(case)
        tests.append({"test_id": test_id, "status": status,
                      "duration_ms": _duration_ms(case.attrib.get("time"))})
    return sorted(tests, key=lambda item: item["test_id"])


def build_history(report: Path, base_sha: str, head_sha: str, run_id: str,
                  occurred_at: str) -> dict[str, Any]:
    _sha(base_sha, "base_sha")
    _sha(head_sha, "head_sha")
    if not isinstance(run_id, str) or not run_id or len(run_id) > 240 or any(c in run_id for c in "\r\n\t"):
        raise ValueError("run_id must be non-empty, single-line and bounded")
    normalized_at = _timestamp(occurred_at)
    tests = parse_junit(report)
    return {"schema_version": SCHEMA_VERSION, "history_version": 1,
            "source": "junit", "report_sha256": hashlib.sha256(report.read_bytes()).hexdigest(),
            "base_sha": base_sha, "head_sha": head_sha, "run_id": run_id,
            "occurred_at": normalized_at, "test_count": len(tests), "tests": tests}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--junit", type=Path, required=True)
    parser.add_argument("--base-sha", required=True)
    parser.add_argument("--head-sha", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--occurred-at", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        history = build_history(args.junit, args.base_sha, args.head_sha,
                                args.run_id, args.occurred_at)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(history, indent=2) + "\n", encoding="utf-8")
    except (OSError, TypeError, ValueError, UnicodeError) as exc:
        print(f"ERROR: JUnit history normalization failed: {type(exc).__name__}")
        return 2
    print(f"junit_history: tests={history['test_count']} report_sha256={history['report_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
