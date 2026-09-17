#!/usr/bin/env python3
"""Run a clean-room integration command and emit schema-v1 evidence.

The integration gate is an execution boundary, not a second opinion in prose:
it archives the candidate's committed HEAD into a temporary workspace, runs a
provided argv without a shell, and records only machine-checkable status and
bounded metrics. The workspace is deleted when the command finishes.

Usage:
    python scripts/integration_gate.py <task_id> --base-sha SHA --head-sha SHA \
        --output .docs/integration-reports/<task_id>.json \
        --command COMMAND [ARGS...]

Exit codes:
    0 -- command completed successfully
    1 -- command completed with a non-zero exit code
    2 -- staging, timeout, invocation, or usage error
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tarfile
import tempfile
import time
from contextlib import contextmanager
from io import BytesIO
from pathlib import Path
from typing import Iterator

SCHEMA_VERSION = 1
DEFAULT_TIMEOUT_SECONDS = 900
DEFAULT_COMMAND = (sys.executable, "-m", "pytest", "tests", "-q")
FULL_SHA = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")


def commit_sha(repo: Path, ref: str) -> str:
    result = subprocess.run(["git", "rev-parse", "--verify", "--end-of-options",
                             ref + "^{commit}"], cwd=repo, capture_output=True,
                            text=True, timeout=60)
    if result.returncode or not FULL_SHA.fullmatch(result.stdout.strip()):
        raise ValueError("commit does not exist or is not a commit")
    return result.stdout.strip()


def execution_tree(repo: Path, head_sha: str, base_sha: str | None = None) -> str:
    if commit_sha(repo, head_sha) != head_sha:
        raise ValueError("candidate must be an exact commit SHA")
    if base_sha is None:
        return head_sha
    if commit_sha(repo, base_sha) != base_sha:
        raise ValueError("base must be an exact commit SHA")
    merged = subprocess.run(["git", "merge-tree", "--write-tree", base_sha, head_sha],
                            cwd=repo, capture_output=True, text=True, timeout=60)
    tree = merged.stdout.splitlines()[0] if merged.stdout else ""
    if merged.returncode or not FULL_SHA.fullmatch(tree):
        raise ValueError("candidate cannot merge cleanly with the exact base")
    return tree


@contextmanager
def staged_workspace(repo: Path, head_sha: str | None = None,
                     base_sha: str | None = None) -> Iterator[Path]:
    """Yield a temporary tree containing only the committed candidate HEAD."""
    tree = execution_tree(repo, head_sha or commit_sha(repo, "HEAD"), base_sha)
    with tempfile.TemporaryDirectory(prefix="pipeline-integration-") as raw:
        workspace = Path(raw)
        archive = subprocess.run(
            ["git", "archive", "--format=tar", tree],
            cwd=repo,
            capture_output=True,
            timeout=60,
        )
        if archive.returncode != 0:
            raise RuntimeError("could not archive candidate HEAD")
        with tarfile.open(fileobj=BytesIO(archive.stdout), mode="r:") as bundle:
            bundle.extractall(workspace, filter="data")
        yield workspace


def _validate_identity(base_sha: str, head_sha: str) -> None:
    if not FULL_SHA.fullmatch(base_sha) or not FULL_SHA.fullmatch(head_sha):
        raise ValueError("base/head must be full hexadecimal commit SHAs")


def run_integration(
    repo: Path,
    task_id: str,
    base_sha: str,
    head_sha: str,
    command: list[str] | tuple[str, ...] = DEFAULT_COMMAND,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
) -> dict:
    """Run ``command`` in a committed, temporary copy and return evidence."""
    _validate_identity(base_sha, head_sha)
    tree = execution_tree(repo, head_sha, base_sha)
    if not command:
        raise ValueError("integration command must not be empty")
    if timeout_seconds <= 0:
        raise ValueError("timeout must be positive")

    started = time.monotonic()
    report = {
        "schema_version": SCHEMA_VERSION,
        "task": task_id,
        "base_sha": base_sha,
        "head_sha": head_sha,
        "status": "error",
        "isolated": True,
        "workspace_source": "git-archive-merge-tree",
        "executed_tree": tree,
        "integration_mode": "base-head-merge",
        "security_isolation": "external-worker-required",
        "command": list(command),
        "metrics": {},
    }
    try:
        with staged_workspace(repo, head_sha, base_sha) as workspace:
            env = dict(os.environ)
            # Never import modules from the originating checkout in a clean run.
            env.pop("PYTHONPATH", None)
            env.pop("PYTHONHOME", None)
            env.update({"CI": "1", "PYTHONDONTWRITEBYTECODE": "1"})
            try:
                result = subprocess.run(
                    list(command),
                    cwd=workspace,
                    env=env,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=timeout_seconds,
                )
            except subprocess.TimeoutExpired:
                report["error"] = "integration command timed out"
                report["metrics"] = {
                    "exit_code": None,
                    "duration_seconds": round(time.monotonic() - started, 3),
                }
                return report
            report["status"] = "pass" if result.returncode == 0 else "fail"
            report["metrics"] = {
                "exit_code": result.returncode,
                "duration_seconds": round(time.monotonic() - started, 3),
                "stdout_bytes": len(result.stdout.encode("utf-8")),
                "stderr_bytes": len(result.stderr.encode("utf-8")),
            }
    except (OSError, RuntimeError, tarfile.TarError) as exc:
        report["error"] = "integration workspace failed: " + type(exc).__name__
        report["metrics"] = {"duration_seconds": round(time.monotonic() - started, 3)}
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("task_id")
    parser.add_argument("--base-sha", required=True)
    parser.add_argument("--head-sha", required=True)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT_SECONDS)
    parser.add_argument("--command", nargs=argparse.REMAINDER,
                        help="argv to run; defaults to pytest tests -q")
    args = parser.parse_args()
    command = list(args.command or [])
    if not command:
        command = list(DEFAULT_COMMAND)
    try:
        report = run_integration(args.repo.resolve(), args.task_id, args.base_sha,
                                 args.head_sha, command, args.timeout)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    except (OSError, ValueError, TypeError) as exc:
        report = {
            "schema_version": SCHEMA_VERSION,
            "task": args.task_id,
            "status": "error",
            "error": "invalid integration input: " + type(exc).__name__,
        }
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print("ERROR: integration gate could not run", flush=True)
        return 2
    print(f"integration_gate: task {args.task_id} -> status={report['status']}")
    if report["status"] == "pass":
        return 0
    return 1 if report["status"] == "fail" else 2


if __name__ == "__main__":
    raise SystemExit(main())
