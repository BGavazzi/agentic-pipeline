#!/usr/bin/env python3
"""Run conservative test-impact selection in a clean-room shadow job.

The full suite remains the correctness authority. This runner measures whether
the selected subset passes and records the selection policy alongside the
clean-room execution receipt; it never promotes a partial run to admission.

Exit codes:
    0 -- selected/full shadow command passed
    1 -- shadow command failed
    2 -- invalid input, analysis, or clean-room error
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:  # Package import for pytest; direct import for the CLI entry point.
    from .integration_gate import run_integration
    from .test_impact import analyze
except ImportError:  # pragma: no cover - exercised by `python scripts/...`.
    from integration_gate import run_integration
    from test_impact import analyze


def run_shadow(
    repo: Path,
    task_id: str,
    base_sha: str,
    head_sha: str,
    timeout_seconds: int = 900,
) -> dict:
    """Analyze the diff, execute the conservative selection, and return evidence."""
    impact = analyze(repo, base_sha, head_sha)
    selected = impact["selected_tests"]
    if impact["mode"] == "full" or not selected:
        command = [sys.executable, "-m", "pytest", "tests", "-q"]
    else:
        command = [sys.executable, "-m", "pytest", *selected, "-q"]
    execution = run_integration(
        repo,
        task_id,
        base_sha,
        head_sha,
        command=command,
        timeout_seconds=timeout_seconds,
    )
    return {
        "schema_version": 1,
        "gate": "test-impact-shadow",
        "task": task_id,
        "base_sha": base_sha,
        "head_sha": head_sha,
        "status": execution["status"],
        "authoritative": False,
        "policy": impact["policy"],
        "impact": impact,
        "execution": execution,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("task_id")
    parser.add_argument("--base-sha", required=True)
    parser.add_argument("--head-sha", required=True)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--impact-output", type=Path, required=True)
    parser.add_argument("--timeout", type=int, default=900)
    args = parser.parse_args()
    try:
        report = run_shadow(
            args.repo.resolve(),
            args.task_id,
            args.base_sha,
            args.head_sha,
            args.timeout,
        )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        args.impact_output.parent.mkdir(parents=True, exist_ok=True)
        args.impact_output.write_text(
            json.dumps(report["impact"], indent=2) + "\n", encoding="utf-8"
        )
    except (OSError, RuntimeError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print("ERROR: test-impact shadow failed: " + type(exc).__name__, flush=True)
        return 2
    print(
        f"impact_runner: mode={report['impact']['mode']} "
        f"status={report['status']}"
    )
    return {"pass": 0, "fail": 1, "error": 2}[report["status"]]


if __name__ == "__main__":
    raise SystemExit(main())
