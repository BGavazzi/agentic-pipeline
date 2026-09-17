from __future__ import annotations

import json
import sys
import subprocess
import shutil
from pathlib import Path

from scripts.meta_test_dispatch import dispatch

BASE, HEAD = "a" * 40, "b" * 40
FIXTURES = Path(__file__).parent / "skills" / "fixtures"


def source_repo(tmp_path):
    root = tmp_path / "candidate"
    skill = root / ".claude/skills/builder/SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_text("Test builder instruction fixture")
    def git(*args):
        return subprocess.check_output(["git", "-c", "user.name=Test", "-c",
            "user.email=test@example.invalid", *args], cwd=root, text=True).strip()
    git("init", "-q")
    git("add", "-A")
    git("commit", "-qm", "candidate")
    return root, git("rev-parse", "HEAD")


def facts(path: Path, **overrides) -> Path:
    value = {
        "worker_kind": "self-hosted",
        "fork_pr": False,
        "labels": ["self-hosted", "homelab-pool"],
        "ephemeral": True,
        "jobs_completed": 0,
        "workspace_clean": True,
        "mounted_secret_count": 0,
        "docker_reachable": True,
    }
    value.update(overrides)
    path.write_text(json.dumps(value), encoding="utf-8")
    return path


WORKER = r'''
import json, os, subprocess
from pathlib import Path
root = Path(os.environ["PIPELINE_META_TEST_SANDBOX"])
subprocess.run(["git", "checkout", "-qb", "feat/0001-worker"], cwd=root, check=True)
task = root / ".docs" / "tasks" / "0001-add-greeting.md"
task.write_text("---\nstatus: done\n---\n# 0001\n\n## Exit Conditions\n- [x] Add greeting\n\n## Required Documentation (Closure Law)\n- [x] CHANGELOG\n- [x] tests\n", encoding="utf-8")
(root / "README.md").write_text("hello\n", encoding="utf-8")
(root / "CHANGELOG.md").write_text("entry\n", encoding="utf-8")
subprocess.run(["git", "add", "README.md", "CHANGELOG.md", ".docs/tasks/0001-add-greeting.md"], cwd=root, check=True)
subprocess.run(["git", "commit", "-qm", "feat: greeting"], cwd=root, check=True)
assert 'PIPELINE_WORKER_POST_FACTS' not in os.environ
print(json.dumps({"task_status_final": "done", "conditions_marked_done": 1,
    "closure": {"CHANGELOG": "yes", "tests": "yes"},
    "tool_calls": ["Read", "Edit", "Bash"]}))
'''


def test_dispatch_binds_meta_receipt_to_lifecycle(tmp_path: Path):
    candidate, head = source_repo(tmp_path)
    worker = tmp_path / "worker.py"
    worker.write_text(WORKER, encoding="utf-8")
    before = facts(tmp_path / "before.json")
    after = tmp_path / "after.json"
    output = tmp_path / "meta.json"
    cleanup = tmp_path / "cleanup.py"
    cleanup.write_text('import json, os\nprint(json.dumps({"attempt_id": os.environ["PIPELINE_CLEANUP_ATTEMPT"], "jobs_completed": 1, "workspace_clean": True, "mounted_secret_count": 0, "registered": False}))\n')
    observer = tmp_path / "observer.py"
    observer.write_text('import json\nprint(json.dumps({"tests_passed": True, "tool_calls": ["Read", "Edit", "Bash"]}))\n')
    fixture_root = tmp_path / "fixtures"
    shutil.copytree(FIXTURES / "001-trivial-readme-edit", fixture_root / "001-trivial-readme-edit")
    report = dispatch(before, after, fixture_root, output, head, head,
                      [sys.executable, str(worker)], worker_timeout=30,
                      meta_timeout=30, cleanup_command=[sys.executable, str(cleanup)],
                      observer_command=[sys.executable, str(observer)], source_repo=candidate,
                      require_observer=True)
    assert report["status"] == "pass"
    assert report["runner_lifecycle"]["status"] == "pass"
    assert report["runner_lifecycle"]["metrics"]["deregistered"] is True
    assert output.is_file()
    assert report["producer"]["kind"] == "meta-test-producer"
    assert report["producer"]["observer_execution"] == "separate-process"
    assert report["metrics"]["observer_present"] is True


def test_dispatch_requires_independent_observer(tmp_path: Path):
    candidate, head = source_repo(tmp_path)
    output = tmp_path / "meta.json"
    report = dispatch(
        facts(tmp_path / "before.json"), tmp_path / "after.json", FIXTURES, output,
        head, head, [sys.executable, "-c", "print('{}')"], source_repo=candidate,
        require_observer=True,
    )
    assert report["status"] == "error"
    assert report["error"] == "independent observer is required"
    assert report["producer"]["observer_required"] is True


def test_dispatch_does_not_fabricate_receipt_when_worker_is_blocked(tmp_path: Path):
    candidate, head = source_repo(tmp_path)
    before = facts(tmp_path / "before.json", ephemeral=False)
    after = tmp_path / "after.json"
    output = tmp_path / "meta.json"
    report = dispatch(before, after, FIXTURES, output, head, head,
                      [sys.executable, "-c", "raise SystemExit(0)"],
                      worker_timeout=30, meta_timeout=30, source_repo=candidate)
    assert report["status"] == "error"
    assert report["runner_lifecycle"]["status"] == "blocked"
    assert report["metrics"]["fixtures_total"] == 0
