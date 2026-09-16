#!/usr/bin/env python3
"""Run the agent-skill meta-test through the one-shot worker boundary.

This is the operator/runtime adapter between a trusted worker pool and the
deterministic ``meta_test.py`` contract. The agent command is supplied by the
runtime as an argv list; this module never selects a model, opens a remote,
mounts secrets, or uses a shell. The worker must create the post-facts file so
the supervisor can prove cleanup and deregistration. Missing proof is an
error, never a successful meta-test.

The output is a single schema-v1 ``meta-test`` receipt enriched with the
``worker-lifecycle`` evidence. It is suitable for the existing receipt
aggregator once a protected dispatcher uploads it to CI.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

try:  # package import for tests; direct import for CLI use
    from . import meta_test, worker_supervisor
except ImportError:  # pragma: no cover
    import meta_test  # type: ignore
    import worker_supervisor  # type: ignore

SCHEMA_VERSION = 1
SHA_RE = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")


def dispatch(
    facts_path: Path,
    post_facts_path: Path,
    fixtures: Path,
    output: Path,
    base_sha: str,
    head_sha: str,
    worker_command: list[str],
    *,
    worker_timeout: int = worker_supervisor.DEFAULT_TIMEOUT_SECONDS,
    meta_timeout: int = meta_test.DEFAULT_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    if not SHA_RE.fullmatch(base_sha) or not SHA_RE.fullmatch(head_sha):
        raise ValueError("base/head must be full hexadecimal commit SHAs")
    if not worker_command:
        raise ValueError("worker command must not be empty")
    if not fixtures.is_dir():
        raise ValueError("meta-test fixtures directory does not exist")

    meta_output = output.with_name(output.stem + ".worker.json")
    lifecycle_output = output.with_name(output.stem + ".lifecycle.json")
    meta_command = [
        sys.executable,
        str(Path(meta_test.__file__).resolve()),
        "--fixtures", str(fixtures.resolve()),
        "--output", str(meta_output.resolve()),
        "--base-sha", base_sha,
        "--head-sha", head_sha,
        "--timeout", str(meta_timeout),
        "--command", *worker_command,
    ]
    lifecycle = worker_supervisor.supervise(
        facts_path.resolve(), post_facts_path.resolve(), meta_command,
        timeout_seconds=worker_timeout,
    )
    lifecycle_output.parent.mkdir(parents=True, exist_ok=True)
    lifecycle_output.write_text(json.dumps(lifecycle, indent=2) + "\n", encoding="utf-8")

    if not meta_output.is_file():
        report: dict[str, Any] = {
            "schema_version": SCHEMA_VERSION,
            "gate": "meta-test",
            "base_sha": base_sha,
            "head_sha": head_sha,
            "status": "error",
            "metrics": {"fixtures_total": 0, "fixtures_passed": 0},
            "runner_lifecycle": lifecycle,
            "error": "worker did not produce meta-test receipt",
        }
    else:
        report = json.loads(meta_output.read_text(encoding="utf-8"))
        if not isinstance(report, dict) or report.get("gate") != "meta-test":
            raise ValueError("worker receipt is not a meta-test report")
        if report.get("base_sha") != base_sha or report.get("head_sha") != head_sha:
            raise ValueError("worker receipt has stale commit identity")
        report["runner_lifecycle"] = lifecycle
        if lifecycle.get("status") != "pass":
            report["status"] = "error" if lifecycle.get("status") in {"blocked", "error"} else "fail"
            report.setdefault("errors", []).append("worker lifecycle did not pass")

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--facts", type=Path, required=True)
    parser.add_argument("--post-facts", type=Path, required=True)
    parser.add_argument("--fixtures", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--base-sha", required=True)
    parser.add_argument("--head-sha", required=True)
    parser.add_argument("--worker-timeout", type=int, default=worker_supervisor.DEFAULT_TIMEOUT_SECONDS)
    parser.add_argument("--meta-timeout", type=int, default=meta_test.DEFAULT_TIMEOUT_SECONDS)
    parser.add_argument("--worker-command", nargs=argparse.REMAINDER, required=True)
    args = parser.parse_args()
    command = list(args.worker_command)
    if command[:1] == ["--"]:
        command = command[1:]
    try:
        report = dispatch(args.facts, args.post_facts, args.fixtures, args.output,
                          args.base_sha, args.head_sha, command,
                          worker_timeout=args.worker_timeout,
                          meta_timeout=args.meta_timeout)
    except (OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: meta-test dispatcher failed: {type(exc).__name__}", file=sys.stderr)
        return 2
    print(f"meta_test_dispatch: status={report['status']}")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
