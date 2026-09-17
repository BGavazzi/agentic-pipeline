#!/usr/bin/env python3
"""Run an independent reviewer command and normalize its JSON receipt.

The command is supplied by the worker runtime (for example, a homelab agent
worker) and is executed as an argv list in a fresh committed-HEAD workspace.
It must print one ultrareview report JSON object to stdout. This wrapper never
turns a missing reviewer, timeout, malformed output, or invalid evidence into
PASS; it writes an explicit ``status=error`` receipt when possible.

Exit codes:
    0 -- independent reviewer produced a valid PASS receipt
    1 -- independent reviewer produced a valid BLOCK receipt
    2 -- worker unavailable, malformed output, timeout, or usage error
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from integration_gate import staged_workspace
from ultrareview_receipt import SCHEMA_VERSION, validate_report

DEFAULT_TIMEOUT_SECONDS = 900


def _error_receipt(task_id: str, base_sha: str, head_sha: str, error: str) -> dict:
    return {
        "schema_version": SCHEMA_VERSION,
        "gate": "ultrareview",
        "task": task_id,
        "base_sha": base_sha,
        "head_sha": head_sha,
        "status": "error",
        "error": error,
    }


def run_reviewer(repo: Path, task_id: str, base_sha: str, head_sha: str,
                 command: list[str], timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS) -> dict:
    """Run a reviewer in isolation and return canonical or error evidence."""
    if not command:
        return _error_receipt(task_id, base_sha, head_sha, "reviewer command is empty")
    started = time.monotonic()
    try:
        diff = subprocess.run(
            ["git", "diff", "--no-ext-diff", "--unified=3", f"{base_sha}..{head_sha}"],
            cwd=repo, capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=60,
        )
        if diff.returncode != 0:
            return _error_receipt(task_id, base_sha, head_sha, "could not build review diff")
        with staged_workspace(repo, head_sha) as workspace:
            context_dir = workspace / ".pipeline-review-context"
            context_dir.mkdir()
            diff_path = context_dir / "diff.patch"
            diff_path.write_text(diff.stdout, encoding="utf-8")
            context_path = context_dir / "review.json"
            context_path.write_text(json.dumps({
                "task": task_id,
                "base_sha": base_sha,
                "head_sha": head_sha,
                "diff_path": str(diff_path),
            }, indent=2) + "\n", encoding="utf-8")
            env = dict(os.environ)
            env.update({
                "CI": "1",
                "PIPELINE_REVIEW_CONTEXT": str(context_path),
                "PIPELINE_REVIEW_BASE_SHA": base_sha,
                "PIPELINE_REVIEW_HEAD_SHA": head_sha,
                "PIPELINE_REVIEW_TASK": task_id,
            })
            try:
                result = subprocess.run(
                    command, cwd=workspace, env=env, capture_output=True, text=True,
                    encoding="utf-8", errors="replace", timeout=timeout_seconds,
                )
            except subprocess.TimeoutExpired:
                return _error_receipt(task_id, base_sha, head_sha, "reviewer timed out")
            if result.returncode != 0:
                return _error_receipt(task_id, base_sha, head_sha, "reviewer exited non-zero")
            try:
                raw = json.loads(result.stdout)
                receipt = validate_report(raw, base_sha, head_sha)
            except (TypeError, ValueError, json.JSONDecodeError):
                return _error_receipt(task_id, base_sha, head_sha, "reviewer output was invalid")
            receipt["metrics"] = dict(receipt.get("metrics", {}))
            receipt["metrics"]["worker_duration_seconds"] = round(time.monotonic() - started, 3)
            return receipt
    except (OSError, ValueError, RuntimeError):
        return _error_receipt(task_id, base_sha, head_sha, "reviewer workspace failed")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("task_id")
    parser.add_argument("--base-sha", required=True)
    parser.add_argument("--head-sha", required=True)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT_SECONDS)
    parser.add_argument("--command", nargs=argparse.REMAINDER, required=True,
                        help="reviewer argv; its stdout must be one JSON report")
    args = parser.parse_args()
    command = list(args.command)
    if command[:1] == ["--"]:
        command = command[1:]
    report = run_reviewer(args.repo.resolve(), args.task_id, args.base_sha,
                          args.head_sha, command, args.timeout)
    try:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    except OSError:
        print("ERROR: could not write ultrareview evidence", flush=True)
        return 2
    print(f"ultrareview_runner: status={report['status']}")
    return {"pass": 0, "fail": 1, "error": 2}[report["status"]]


if __name__ == "__main__":
    raise SystemExit(main())
