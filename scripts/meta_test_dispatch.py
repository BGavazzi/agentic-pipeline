#!/usr/bin/env python3
"""Run the agent-skill meta-test through the one-shot worker boundary.

This is the operator/runtime adapter between a trusted worker pool and the
deterministic ``meta_test.py`` contract. The agent command is supplied by the
runtime as an argv list; this module never selects a model, opens a remote,
mounts secrets, or uses a shell. A separate trusted host teardown command
must supply fresh cleanup and deregistration evidence. Missing proof is an
error, never a successful meta-test.

The output is a single schema-v1 ``meta-test`` receipt enriched with the
``worker-lifecycle`` evidence. It is suitable for the existing receipt
aggregator once a protected dispatcher uploads it to CI.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import uuid
from pathlib import Path
import hashlib
import subprocess
from typing import Any

try:  # package import for tests; direct import for CLI use
    from . import meta_test, worker_supervisor
except ImportError:  # pragma: no cover
    import meta_test  # type: ignore
    import worker_supervisor  # type: ignore

SCHEMA_VERSION = 1
SHA_RE = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")
PRODUCER_VERSION = 1


def _argv_digest(command: list[str] | None) -> str | None:
    if command is None:
        return None
    return hashlib.sha256(json.dumps(command, separators=(",", ":"), ensure_ascii=True).encode()).hexdigest()


def _corpus_digest(fixtures: Path) -> str:
    return hashlib.sha256(b"".join(
        p.relative_to(fixtures).as_posix().encode() + p.read_bytes()
        for p in sorted(fixtures.rglob("*")) if p.is_file()
    )).hexdigest()


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
    cleanup_command: list[str] | None = None,
    observer_command: list[str] | None = None,
    source_repo: Path | None = None,
    boundary_facts: Path | None = None,
    require_boundary: bool = False,
    require_observer: bool = False,
) -> dict[str, Any]:
    if not SHA_RE.fullmatch(base_sha) or not SHA_RE.fullmatch(head_sha):
        raise ValueError("base/head must be full hexadecimal commit SHAs")
    if not worker_command:
        raise ValueError("worker command must not be empty")
    if not fixtures.is_dir():
        raise ValueError("meta-test fixtures directory does not exist")
    # The skill implementation being tested must be the named candidate, not
    # whichever checkout happened to launch the dispatcher.
    repo_root = source_repo or Path(meta_test.__file__).resolve().parents[1]
    try:
        from .integration_gate import commit_sha
    except ImportError:
        from integration_gate import commit_sha
    if commit_sha(repo_root, "HEAD") != head_sha:
        raise ValueError("dispatcher checkout does not match candidate head")
    dirty = subprocess.run(["git", "status", "--porcelain", "--", ".claude/skills"],
                           cwd=repo_root, capture_output=True, text=True, check=True)
    if dirty.stdout:
        raise ValueError("candidate skills contain uncommitted changes")

    attempt = uuid.uuid4().hex
    producer = {
        "schema_version": PRODUCER_VERSION,
        "kind": "meta-test-producer",
        "adapter": "scripts/meta_test_dispatch.py",
        "invocation_id": attempt,
        "roles": {
            "worker": "candidate-runtime",
            "observer": "trusted-independent-observer" if observer_command else None,
        },
        "observer_required": require_observer,
        "observer_execution": "separate-process" if observer_command else "none",
        "worker_command_sha256": _argv_digest(worker_command),
        "observer_command_sha256": _argv_digest(observer_command),
        "fixture_corpus_sha256": _corpus_digest(fixtures),
        "runtime": {
            "python": sys.version.split()[0],
            "ci": os.environ.get("CI") == "1",
        },
    }
    if require_observer and observer_command is None:
        report = {
            "schema_version": SCHEMA_VERSION,
            "gate": "meta-test",
            "base_sha": base_sha,
            "head_sha": head_sha,
            "status": "error",
            "metrics": {"fixtures_total": 0, "fixtures_passed": 0,
                        "observer_present": False},
            "producer": producer,
            "error": "independent observer is required",
        }
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        return report
    meta_output = output.with_name(output.stem + f".{attempt}.worker.json")
    lifecycle_output = output.with_name(output.stem + f".{attempt}.lifecycle.json")
    meta_command = [
        sys.executable,
        str(Path(meta_test.__file__).resolve()),
        "--fixtures", str(fixtures.resolve()),
        "--output", str(meta_output.resolve()),
        "--base-sha", base_sha,
        "--head-sha", head_sha,
        "--timeout", str(meta_timeout),
        "--skills-root", str((repo_root / ".claude/skills").resolve()),
    ]
    if observer_command:
        meta_command.extend(["--observer-command", *observer_command])
    meta_command.extend(["--command", *worker_command])
    lifecycle = worker_supervisor.supervise(
        facts_path.resolve(), post_facts_path.resolve(), meta_command,
        timeout_seconds=worker_timeout,
        cleanup_command=cleanup_command,
        boundary_facts_path=boundary_facts,
        require_boundary=require_boundary,
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
    report["fixture_corpus_sha256"] = producer["fixture_corpus_sha256"]
    report["producer"] = producer
    report.setdefault("metrics", {})["observer_present"] = observer_command is not None
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
    parser.add_argument("--cleanup-command", nargs="+", required=True)
    parser.add_argument("--observer-command", nargs="+")
    parser.add_argument("--source-repo", type=Path)
    parser.add_argument("--boundary-facts", type=Path,
                        help="external sandbox attestation for a real self-hosted run")
    parser.add_argument("--require-boundary", action="store_true")
    parser.add_argument("--require-observer", action="store_true",
                        help="fail unless an independent observer command is supplied")
    parser.add_argument("--worker-command", nargs=argparse.REMAINDER, required=True)
    args = parser.parse_args()
    command = list(args.worker_command)
    if command[:1] == ["--"]:
        command = command[1:]
    try:
        report = dispatch(args.facts, args.post_facts, args.fixtures, args.output,
                          args.base_sha, args.head_sha, command,
                          worker_timeout=args.worker_timeout,
                          meta_timeout=args.meta_timeout, cleanup_command=args.cleanup_command,
                          observer_command=args.observer_command, source_repo=args.source_repo,
                          boundary_facts=args.boundary_facts,
                          require_boundary=args.require_boundary,
                          require_observer=args.require_observer)
    except (OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: meta-test dispatcher failed: {type(exc).__name__}", file=sys.stderr)
        return 2
    print(f"meta_test_dispatch: status={report['status']}")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
