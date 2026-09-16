#!/usr/bin/env python3
"""Validate an independent ultrareview verdict and emit a gate receipt.

This adapter does not perform an LLM review. An independent reviewer produces
the input JSON; this script rejects unverifiable or malformed claims and emits
the canonical schema-v1 status consumed by ``ci_receipts.py``. A PASS without
evidence, an absent independence marker, or a BLOCK without findings can never
be normalized into admission evidence.

Exit codes:
    0 -- valid PASS verdict
    1 -- valid BLOCK verdict
    2 -- invalid or stale report
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

SCHEMA_VERSION = 1
FULL_SHA = re.compile(r"^[0-9a-f]{40,64}$")


def _text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_report(report: dict, base_sha: str, head_sha: str) -> dict:
    """Return a canonical receipt or raise ``ValueError`` for weak evidence."""
    if not isinstance(report, dict) or report.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("unsupported schema version")
    if not FULL_SHA.fullmatch(base_sha) or not FULL_SHA.fullmatch(head_sha):
        raise ValueError("expected full commit SHAs")
    if report.get("base_sha") != base_sha or report.get("head_sha") != head_sha:
        raise ValueError("stale or mismatched commit identity")
    if not _text(report.get("task")):
        raise ValueError("missing task identity")
    verdict = report.get("verdict")
    if verdict not in {"pass", "block"}:
        raise ValueError("verdict must be pass or block")
    if report.get("independent") is not True:
        raise ValueError("independence marker is required")

    reviewer = report.get("reviewer")
    if not isinstance(reviewer, dict) or not _text(reviewer.get("kind")) \
            or not _text(reviewer.get("invocation_id")):
        raise ValueError("reviewer kind and invocation_id are required")

    evidence = report.get("evidence")
    if not isinstance(evidence, list) or not evidence:
        raise ValueError("at least one evidence citation is required")
    for item in evidence:
        if not isinstance(item, dict) or not _text(item.get("kind")) \
                or not _text(item.get("citation")):
            raise ValueError("each evidence item needs kind and citation")

    findings = report.get("findings")
    if not isinstance(findings, list):
        raise ValueError("findings must be a list")
    if verdict == "block" and not findings:
        raise ValueError("block verdict needs at least one finding")
    if verdict == "pass" and findings:
        raise ValueError("pass verdict cannot contain blocking findings")

    metrics = report.get("metrics")
    if not isinstance(metrics, dict):
        raise ValueError("metrics are required")
    reviewed_files = metrics.get("reviewed_files")
    if type(reviewed_files) is not int or reviewed_files < 0:
        raise ValueError("metrics.reviewed_files must be a non-negative integer")

    return {
        "schema_version": SCHEMA_VERSION,
        "gate": "ultrareview",
        "task": report["task"],
        "base_sha": base_sha,
        "head_sha": head_sha,
        "status": "pass" if verdict == "pass" else "fail",
        "verdict": verdict,
        "independent": True,
        "reviewer": reviewer,
        "evidence": evidence,
        "findings": findings,
        "metrics": metrics,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--base-sha", required=True)
    parser.add_argument("--head-sha", required=True)
    args = parser.parse_args()
    try:
        raw = json.loads(args.input.read_text(encoding="utf-8"))
        receipt = validate_report(raw, args.base_sha, args.head_sha)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    except (OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print("ERROR: invalid ultrareview evidence: " + type(exc).__name__, flush=True)
        return 2
    print(f"ultrareview_receipt: status={receipt['status']}")
    return 0 if receipt["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
