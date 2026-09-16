#!/usr/bin/env python3
"""Run a deterministic fixture corpus against the harness admission contract.

This is a self-test of policy composition, not a substitute for the normal
candidate gates. Fixtures exercise pass, missing-obligation, stale-identity,
and unknown-gate cases so a refactor cannot silently make the harness permissive.
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

try:  # Package import for pytest; direct import for the CLI entry point.
    from .admission_gate import evaluate
except ImportError:  # pragma: no cover - exercised by `python scripts/...`.
    from admission_gate import evaluate

SCHEMA_VERSION = 1


def run_case(path: Path) -> dict:
    case = json.loads(path.read_text(encoding="utf-8"))
    base_sha = case["base_sha"]
    head_sha = case["head_sha"]
    expected = case["expect"]
    try:
        observed = evaluate(case["risk"], case["receipts"], base_sha, head_sha)
        if "admitted" in expected:
            passed = observed["admitted"] is expected["admitted"]
        else:
            passed = False
        result = {"admitted": observed["admitted"]}
    except (TypeError, ValueError) as exc:
        passed = expected.get("error_type") == type(exc).__name__
        result = {"error_type": type(exc).__name__}
    return {
        "name": path.stem,
        "status": "pass" if passed else "fail",
        "expected": expected,
        "observed": result,
    }


def run_suite(fixtures_dir: Path) -> dict:
    started = time.monotonic()
    cases = [run_case(path) for path in sorted(fixtures_dir.glob("*.json"))]
    passed = sum(case["status"] == "pass" for case in cases)
    return {
        "schema_version": SCHEMA_VERSION,
        "harness_version": "0.1",
        "status": "pass" if cases and passed == len(cases) else "fail",
        "metrics": {
            "cases_total": len(cases),
            "cases_passed": passed,
            "cases_failed": len(cases) - passed,
            "duration_seconds": round(time.monotonic() - started, 3),
        },
        "cases": cases,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixtures", type=Path, default=Path("tests/harness/fixtures"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        report = run_suite(args.fixtures.resolve())
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    except (OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print("ERROR: harness self-test failed: " + type(exc).__name__, flush=True)
        return 2
    print(
        f"harness_selftest: {report['status']} "
        f"{report['metrics']['cases_passed']}/{report['metrics']['cases_total']} cases"
    )
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
