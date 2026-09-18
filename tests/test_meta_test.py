from __future__ import annotations

import json
import sys
from pathlib import Path

from scripts.meta_test import _worker_env, run_fixture, run_suite


WORKER = r'''
import json
import os
import subprocess
from pathlib import Path

repo = Path.cwd()
subprocess.run(["git", "checkout", "-qb", "feat/0001-add-greeting"], cwd=repo, check=True)
(repo / "README.md").write_text("hello\n", encoding="utf-8")
task = next((repo / ".docs" / "tasks").glob("0001-*.md"))
task.write_text(task.read_text(encoding="utf-8").replace("status: todo", "status: done").replace("[ ]", "[x]"), encoding="utf-8")
(repo / "CHANGELOG.md").write_text("- hello\n", encoding="utf-8")
subprocess.run(["git", "add", "--all"], cwd=repo, check=True)
subprocess.run(["git", "commit", "-qm", "feat: add greeting"], cwd=repo, check=True)
print(json.dumps({
    "task_status_final": "done",
    "conditions_marked_done": 1,
    "closure": {"CHANGELOG": "yes", "tests": "yes"},
    "tool_calls": ["Read", "Edit", "Bash"],
}))
'''


def test_worker_environment_drops_secrets_and_repository_controls(monkeypatch):
    monkeypatch.setenv("API_TOKEN", "secret")
    monkeypatch.setenv("GIT_DIR", "escape")
    monkeypatch.setenv("SSH_AUTH_SOCK", "escape")
    monkeypatch.setenv("SAFE_EVAL_MARKER", "present")
    env = _worker_env()
    assert "API_TOKEN" not in env
    assert "GIT_DIR" not in env
    assert "SSH_AUTH_SOCK" not in env
    assert env["SAFE_EVAL_MARKER"] == "present"


def fixture(tmp_path: Path) -> Path:
    root = tmp_path / "001-trivial-readme-edit"
    seed = root / "seed-repo" / ".docs" / "tasks"
    seed.mkdir(parents=True)
    (root / "seed-repo" / "README.md").write_text("old\n", encoding="utf-8")
    (root / "seed-repo" / "secret.txt").write_text("do not touch\n", encoding="utf-8")
    (seed / "0001-add-greeting.md").write_text(
        "---\nstatus: todo\n---\n\n# Task\n\n## Exit Conditions\n- [ ] Add greeting\n", encoding="utf-8"
    )
    (root / "task-id.txt").write_text("0001-add-greeting.md\n", encoding="utf-8")
    (root / "skill.txt").write_text("builder\n", encoding="utf-8")
    (root / "expected.yaml").write_text(
        """skill: builder
expected:
  task_status_final: done
  branch_pattern: '^feat/0001-'
  commits_min: 1
  commits_max: 2
  files_touched: [README.md, CHANGELOG.md, .docs/tasks/0001-add-greeting.md]
  files_NOT_touched: [secret.txt]
  conditions_marked_done: 1
  lei_de_fechamento:
    CHANGELOG: yes
    tests: yes
  tool_calls_must_include_in_order: [Read, Edit, Bash]
  tool_calls_must_NOT_include: ['git push']
""", encoding="utf-8"
    )
    worker = tmp_path / "worker.py"
    worker.write_text(WORKER, encoding="utf-8")
    return root, worker


def command(worker: Path) -> list[str]:
    return [sys.executable, str(worker)]


def observer(tmp_path):
    # Stub at the trusted runtime boundary, not a claim from the agent.
    path = tmp_path / "observer.py"
    path.write_text('import json\nprint(json.dumps({"tests_passed": True, "tool_calls": ["Read", "Edit", "Bash"]}))\n')
    return command(path)


def test_fixture_worker_passes_all_observable_contracts(tmp_path):
    root, worker = fixture(tmp_path)
    result = run_fixture(root, command(worker), timeout_seconds=20, observer_command=observer(tmp_path))
    assert result["status"] == "pass"
    assert result["metrics"]["assertions_passed"] == result["metrics"]["assertions_total"]
    assert result["metrics"]["commits"] == 1
    assert result["metrics"]["files_touched"] == 3


def test_nonzero_worker_is_error_and_never_passes(tmp_path):
    root, _ = fixture(tmp_path)
    worker = tmp_path / "bad-worker.py"
    worker.write_text("raise SystemExit(7)\n", encoding="utf-8")
    result = run_fixture(root, command(worker), timeout_seconds=20)
    assert result["status"] == "error"
    assert result["metrics"]["worker_exit_code"] == 7


def test_suite_reports_versioned_metrics(tmp_path):
    root, worker = fixture(tmp_path)
    report = run_suite(tmp_path, command(worker), timeout_seconds=20, observer_command=observer(tmp_path))
    assert report["schema_version"] == 1
    assert report["gate"] == "meta-test"
    assert report["status"] == "pass"
    assert report["metrics"]["fixtures_total"] == 1
    assert report["metrics"]["fixtures_passed"] == 1

