#!/usr/bin/env python3
"""Validate the trust boundary before a worker receives candidate code.

GitHub-hosted workers are accepted as the untrusted-code default. A
self-hosted worker is eligible only when it is explicitly labelled for the
pool, ephemeral, unused, clean, and has no mounted secrets. This produces a
receipt; the caller must stop before checkout when the receipt is blocked.

Exit codes: 0 eligible, 1 blocked, 2 invalid input.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

SCHEMA_VERSION = 1


def evaluate(
    worker_kind: str,
    fork_pr: bool,
    labels: list[str],
    ephemeral: bool,
    jobs_completed: int,
    workspace_clean: bool,
    mounted_secret_count: int,
    docker_reachable: bool,
    require_docker: bool = False,
) -> dict:
    if worker_kind not in {"github-hosted", "self-hosted"}:
        raise ValueError("worker_kind must be github-hosted or self-hosted")
    if jobs_completed < 0 or mounted_secret_count < 0:
        raise ValueError("worker counters must be non-negative")
    labels = sorted(set(labels))
    blockers: dict[str, str] = {}
    self_hosted = worker_kind == "self-hosted"
    if fork_pr and self_hosted:
        blockers["fork_pr"] = "self_hosted_forbidden"
    if self_hosted and "homelab-pool" not in labels:
        blockers["pool_label"] = "homelab-pool_missing"
    if self_hosted and not ephemeral:
        blockers["ephemeral"] = "persistent_worker_forbidden"
    if self_hosted and jobs_completed != 0:
        blockers["worker_age"] = f"jobs_completed={jobs_completed}"
    if self_hosted and not workspace_clean:
        blockers["workspace"] = "cleanup_not_verified"
    if self_hosted and mounted_secret_count != 0:
        blockers["secrets"] = f"mounted_secret_count={mounted_secret_count}"
    if require_docker and not docker_reachable:
        blockers["docker"] = "docker_unreachable"
    return {
        "schema_version": SCHEMA_VERSION,
        "preflight_version": 1,
        "eligible": not blockers,
        "worker_kind": worker_kind,
        "blockers": blockers,
        "metrics": {
            "worker_age_jobs": jobs_completed,
            "mounted_secret_count": mounted_secret_count,
            "cleanup_verified": workspace_clean,
            "docker_reachable": docker_reachable,
            "fork_pr_pool_routes": int(fork_pr and self_hosted),
        },
        "policy": {
            "fork_pr_may_use_pool": False,
            "self_hosted_requires_ephemeral": True,
            "human_review_required_after_staging": True,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worker-kind", choices=["github-hosted", "self-hosted"], required=True)
    parser.add_argument("--fork-pr", action="store_true")
    parser.add_argument("--labels", default="", help="comma-separated runner labels")
    parser.add_argument("--ephemeral", action="store_true")
    parser.add_argument("--jobs-completed", type=int, default=0)
    parser.add_argument("--workspace-clean", action="store_true")
    parser.add_argument("--mounted-secret-count", type=int, default=0)
    parser.add_argument("--docker-reachable", action="store_true")
    parser.add_argument("--require-docker", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = evaluate(
            args.worker_kind, args.fork_pr,
            [label for label in args.labels.split(",") if label],
            args.ephemeral, args.jobs_completed, args.workspace_clean,
            args.mounted_secret_count, args.docker_reachable, args.require_docker,
        )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    except (OSError, TypeError, ValueError) as exc:
        print("ERROR: invalid worker preflight: " + type(exc).__name__, flush=True)
        return 2
    print(f"worker_preflight: eligible={str(result['eligible']).lower()} kind={args.worker_kind}")
    return 0 if result["eligible"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
