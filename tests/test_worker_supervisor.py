from __future__ import annotations

import json
import sys
from pathlib import Path

from scripts.worker_supervisor import supervise


def facts(path: Path, **overrides) -> Path:
    value = {
        "worker_kind": "self-hosted",
        "labels": ["self-hosted", "homelab-pool"],
        "ephemeral": True,
        "jobs_completed": 0,
        "workspace_clean": True,
        "mounted_secret_count": 0,
        "docker_reachable": True,
        "queue_wait_seconds": 12,
    }
    value.update(overrides)
    path.write_text(json.dumps(value), encoding="utf-8")
    return path


POST_WORKER = r'''
import json
import os
from pathlib import Path
Path(os.environ["PIPELINE_WORKER_POST_FACTS"]).write_text(json.dumps({
    "jobs_completed": 1,
    "workspace_clean": True,
    "mounted_secret_count": 0,
    "registered": False,
}), encoding="utf-8")
'''


def command(tmp_path: Path) -> list[str]:
    worker = tmp_path / "runner.py"
    worker.write_text(POST_WORKER, encoding="utf-8")
    return [sys.executable, str(worker)]


def test_single_use_worker_passes_with_cleanup_and_deregistration(tmp_path):
    before = facts(tmp_path / "before.json")
    after = tmp_path / "after.json"
    result = supervise(before, after, command(tmp_path), timeout_seconds=20)
    assert result["status"] == "pass"
    assert result["metrics"]["queue_wait_seconds"] == 12
    assert result["metrics"]["worker_age_jobs_after"] == 1
    assert result["metrics"]["workspace_cleanup"] is True
    assert result["metrics"]["deregistered"] is True


def test_persistent_worker_is_blocked_before_launch(tmp_path):
    before = facts(tmp_path / "before.json", ephemeral=False)
    after = tmp_path / "after.json"
    result = supervise(before, after, command(tmp_path), timeout_seconds=20)
    assert result["status"] == "blocked"
    assert result["blockers"]["ephemeral"] == "persistent_worker_forbidden"
    assert not after.exists()


def test_cleanup_failure_is_not_a_success(tmp_path):
    before = facts(tmp_path / "before.json")
    after = tmp_path / "after.json"
    worker = tmp_path / "dirty-runner.py"
    worker.write_text(
        "import json, os; open(os.environ['PIPELINE_WORKER_POST_FACTS'], 'w').write(json.dumps({\"jobs_completed\": 1, \"workspace_clean\": False, \"mounted_secret_count\": 0, \"registered\": True}))\n",
        encoding="utf-8",
    )
    result = supervise(before, after, [sys.executable, str(worker)], timeout_seconds=20)
    assert result["status"] == "fail"
    assert "workspace" in result["blockers"]
    assert "registration" in result["blockers"]

