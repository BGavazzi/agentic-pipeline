from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

SCRIPT_PATH = Path(__file__).resolve().parent.parent / "scripts" / "worker_preflight.py"
spec = importlib.util.spec_from_file_location("worker_preflight", SCRIPT_PATH)
worker_preflight = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(worker_preflight)


def clean_worker(**overrides):
    args = {
        "worker_kind": "self-hosted",
        "fork_pr": False,
        "labels": ["homelab-pool", "self-hosted"],
        "ephemeral": True,
        "jobs_completed": 0,
        "workspace_clean": True,
        "mounted_secret_count": 0,
        "docker_reachable": True,
        "require_docker": True,
    }
    args.update(overrides)
    return worker_preflight.evaluate(**args)


def test_clean_ephemeral_homelab_worker_is_eligible():
    result = clean_worker()

    assert result["eligible"] is True
    assert result["metrics"]["worker_age_jobs"] == 0
    assert result["metrics"]["mounted_secret_count"] == 0


@pytest.mark.parametrize(
    ("change", "blocker"),
    [
        ({"fork_pr": True}, "fork_pr"),
        ({"ephemeral": False}, "ephemeral"),
        ({"jobs_completed": 1}, "worker_age"),
        ({"workspace_clean": False}, "workspace"),
        ({"mounted_secret_count": 1}, "secrets"),
        ({"docker_reachable": False}, "docker"),
        ({"labels": ["self-hosted"]}, "pool_label"),
    ],
)
def test_unsafe_worker_is_blocked(change, blocker):
    result = clean_worker(**change)

    assert result["eligible"] is False
    assert blocker in result["blockers"]


def test_github_hosted_worker_is_safe_default_for_fork_pr():
    result = worker_preflight.evaluate(
        worker_kind="github-hosted", fork_pr=True, labels=[], ephemeral=False,
        jobs_completed=17, workspace_clean=False, mounted_secret_count=0,
        docker_reachable=False,
    )

    assert result["eligible"] is True
    assert result["metrics"]["fork_pr_pool_routes"] == 0


def test_negative_counters_are_invalid():
    with pytest.raises(ValueError, match="non-negative"):
        clean_worker(jobs_completed=-1)
