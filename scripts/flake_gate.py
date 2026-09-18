#!/usr/bin/env python3
"""Evaluate test-history flakes against an explicit quarantine manifest.

An active quarantine is ``degraded``, never ``pass``. An expired or missing
quarantine is ``block``. This makes temporary containment visible to agents
and humans without allowing retries or quarantine entries to become a green
admission receipt.
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
TEST_ID_RE = re.compile(r"^[^\r\n\t]{1,240}$")


def _timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        raise ValueError("timestamps require a timezone")
    return parsed.astimezone(timezone.utc)


def _manifest(path: Path, as_of: datetime) -> dict[str, dict[str, Any]]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or value.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("unsupported quarantine manifest schema")
    entries = value.get("quarantines")
    if not isinstance(entries, list):
        raise ValueError("quarantines must be a list")
    result: dict[str, dict[str, Any]] = {}
    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get("test_id"), str) \
                or not TEST_ID_RE.fullmatch(entry["test_id"]):
            raise ValueError("quarantine test_id is invalid")
        if entry["test_id"] in result:
            raise ValueError("duplicate quarantine test_id")
        owner = entry.get("owner")
        reason = entry.get("reason")
        expires_at = entry.get("expires_at")
        if not isinstance(owner, str) or not owner.strip() or not isinstance(reason, str) or not reason.strip():
            raise ValueError("quarantine owner and reason are required")
        expiry = _timestamp(expires_at) if isinstance(expires_at, str) else None
        if expiry is None:
            raise ValueError("quarantine expires_at is required")
        result[entry["test_id"]] = {"owner": owner, "reason": reason,
                                     "expires_at": expiry.isoformat(),
                                     "expired": expiry <= as_of}
    return result


def evaluate(history: dict[str, Any], manifest_path: Path, as_of: str) -> dict[str, Any]:
    reference = _timestamp(as_of)
    if history.get("schema_version") != 1 or history.get("history_version") != 1:
        raise ValueError("unsupported test history schema")
    tests = history.get("tests")
    if not isinstance(tests, list):
        raise ValueError("test history tests must be a list")
    quarantines = _manifest(manifest_path, reference)
    flaky = [item for item in tests if isinstance(item, dict)
             and "pass" in item.get("statuses", [])
             and any(status in item.get("statuses", []) for status in ("fail", "error"))]
    details = []
    for item in flaky:
        test_id = item.get("test_id")
        quarantine = quarantines.get(test_id)
        details.append({"test_id": test_id,
                        "quarantine": quarantine,
                        "classification": ("expired" if quarantine and quarantine["expired"]
                                            else "quarantined" if quarantine else "unquarantined")})
    expired = sum(item["classification"] == "expired" for item in details)
    active = sum(item["classification"] == "quarantined" for item in details)
    unquarantined = sum(item["classification"] == "unquarantined" for item in details)
    status = "pass" if not details else "block" if expired or unquarantined else "degraded"
    return {"schema_version": SCHEMA_VERSION, "flake_gate_version": 1,
            "status": status, "as_of": reference.isoformat(),
            "metrics": {"tests_total": len(tests), "flaky_tests": len(details),
                        "active_quarantines": active, "expired_quarantines": expired,
                        "unquarantined_flakes": unquarantined,
                        "quarantine_coverage": round(active / len(details), 4) if details else 1.0},
            "tests": details,
            "policy": {"quarantined_is_not_green": True,
                       "expired_quarantine_blocks": True}}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--history", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--as-of", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        history = json.loads(args.history.read_text(encoding="utf-8"))
        report = evaluate(history, args.manifest, args.as_of)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    except (OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: flake gate failed: {type(exc).__name__}")
        return 2
    print(f"flake_gate: status={report['status']} flaky={report['metrics']['flaky_tests']} "
          f"unquarantined={report['metrics']['unquarantined_flakes']}")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
