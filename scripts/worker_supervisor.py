#!/usr/bin/env python3
"""Supervise one ephemeral worker process and emit lifecycle evidence.

This is the host-side contract around a GitHub runner or equivalent worker.
The operator supplies pre-run facts, a no-shell argv, and post-run facts. The
supervisor refuses an unsafe self-hosted worker before it receives candidate
code, launches at most one process, and fails closed when cleanup or
deregistration cannot be proven.

The supervisor does not mint registration tokens, register runners, or mount
credentials. Those remain host/operator responsibilities.

Exit codes:
    0 -- one worker completed and cleanup/deregistration evidence passed
    1 -- worker blocked, failed, or cleanup evidence failed
    2 -- invalid input, timeout, or supervisor error
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import time
from pathlib import Path
from typing import Any

try:
    from .worker_preflight import evaluate
except ImportError:  # pragma: no cover - direct CLI execution.
    from worker_preflight import evaluate

SCHEMA_VERSION = 1
DEFAULT_TIMEOUT_SECONDS = 3600
SENSITIVE_ENV = re.compile(r"(TOKEN|SECRET|PASSWORD|PRIVATE_KEY|API_KEY)", re.IGNORECASE)


def _facts(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("worker facts must be a JSON object")
    return value


def _preflight(facts: dict[str, Any], fork_pr: bool, require_docker: bool) -> dict:
    worker_kind = facts.get("worker_kind")
    labels = facts.get("labels", [])
    if not isinstance(labels, list):
        raise ValueError("worker labels must be a list")
    return evaluate(
        worker_kind,
        fork_pr,
        [str(label) for label in labels],
        bool(facts.get("ephemeral", False)),
        int(facts.get("jobs_completed", 0)),
        bool(facts.get("workspace_clean", False)),
        int(facts.get("mounted_secret_count", 0)),
        bool(facts.get("docker_reachable", False)),
        require_docker or bool(facts.get("require_docker", False)),
    )


def _safe_environment() -> dict[str, str]:
    """Preserve runtime basics while excluding obvious credential variables."""
    return {
        key: value for key, value in os.environ.items()
        if not SENSITIVE_ENV.search(key)
    }


def _postconditions(post: dict[str, Any]) -> dict[str, str]:
    blockers: dict[str, str] = {}
    if int(post.get("jobs_completed", 0)) != 1:
        blockers["worker_age"] = f"jobs_completed_after={post.get('jobs_completed', 0)}"
    if post.get("workspace_clean") is not True:
        blockers["workspace"] = "cleanup_not_verified"
    if int(post.get("mounted_secret_count", 0)) != 0:
        blockers["secrets"] = f"mounted_secret_count_after={post.get('mounted_secret_count')}"
    if post.get("registered", False) is not False:
        blockers["registration"] = "worker_still_registered"
    return blockers


def supervise(
    facts_path: Path,
    post_facts_path: Path,
    command: list[str],
    *,
    fork_pr: bool = False,
    require_docker: bool = False,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    started = time.monotonic()
    if not command:
        raise ValueError("worker command must not be empty")
    if timeout_seconds <= 0:
        raise ValueError("timeout must be positive")
    facts = _facts(facts_path)
    preflight = _preflight(facts, fork_pr, require_docker)
    report: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "gate": "worker-lifecycle",
        "status": "blocked" if not preflight["eligible"] else "error",
        "preflight": preflight,
        "metrics": {
            "queue_wait_seconds": facts.get("queue_wait_seconds"),
            "worker_age_jobs_before": preflight["metrics"]["worker_age_jobs"],
            "mounted_secret_count_before": preflight["metrics"]["mounted_secret_count"],
            "fork_pr_pool_routes": preflight["metrics"]["fork_pr_pool_routes"],
        },
    }
    if not preflight["eligible"]:
        report["blockers"] = preflight["blockers"]
        report["metrics"]["worker_duration_seconds"] = 0.0
        return report

    env = _safe_environment()
    env.update({
        "CI": "1",
        "PIPELINE_WORKER_SINGLE_USE": "1",
        "PIPELINE_WORKER_FACTS": str(facts_path),
        "PIPELINE_WORKER_POST_FACTS": str(post_facts_path),
    })
    try:
        process = subprocess.run(
            command,
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_seconds,
            shell=False,
            close_fds=True,
        )
    except subprocess.TimeoutExpired:
        report["status"] = "error"
        report["error"] = "worker_timeout"
        report["metrics"]["worker_duration_seconds"] = round(time.monotonic() - started, 3)
        return report
    report["metrics"].update({
        "worker_exit_code": process.returncode,
        "worker_duration_seconds": round(time.monotonic() - started, 3),
        "stdout_bytes": len(process.stdout.encode("utf-8")),
        "stderr_bytes": len(process.stderr.encode("utf-8")),
    })
    if process.returncode != 0:
        report["status"] = "fail"
        report["blockers"] = {"worker": f"exit_code={process.returncode}"}
        return report
    if not post_facts_path.is_file():
        report["status"] = "error"
        report["blockers"] = {"post_facts": "missing"}
        return report
    try:
        post = _facts(post_facts_path)
    except (OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
        report["status"] = "error"
        report["blockers"] = {"post_facts": type(exc).__name__}
        return report
    blockers = _postconditions(post)
    report["post_facts"] = {
        "jobs_completed": post.get("jobs_completed"),
        "workspace_clean": post.get("workspace_clean"),
        "mounted_secret_count": post.get("mounted_secret_count"),
        "registered": post.get("registered"),
    }
    report["metrics"].update({
        "worker_age_jobs_after": post.get("jobs_completed"),
        "workspace_cleanup": post.get("workspace_clean") is True,
        "mounted_secret_count_after": post.get("mounted_secret_count"),
        "deregistered": post.get("registered") is False,
    })
    report["status"] = "pass" if not blockers else "fail"
    if blockers:
        report["blockers"] = blockers
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--facts", type=Path, required=True)
    parser.add_argument("--post-facts", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--fork-pr", action="store_true")
    parser.add_argument("--require-docker", action="store_true")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT_SECONDS)
    parser.add_argument("--command", nargs=argparse.REMAINDER, required=True)
    args = parser.parse_args()
    command = list(args.command)
    if command[:1] == ["--"]:
        command = command[1:]
    try:
        report = supervise(
            args.facts.resolve(), args.post_facts.resolve(), command,
            fork_pr=args.fork_pr, require_docker=args.require_docker,
            timeout_seconds=args.timeout,
        )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    except (OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print("ERROR: worker supervisor failed: " + type(exc).__name__, flush=True)
        return 2
    print(f"worker_supervisor: status={report['status']}")
    return {"pass": 0, "fail": 1, "blocked": 1, "error": 2}[report["status"]]


if __name__ == "__main__":
    raise SystemExit(main())
