import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import integration_gate


BASE, HEAD = "a" * 40, "b" * 40


def git_fixture(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "tracked.txt").write_text("tracked\n", encoding="utf-8")
    (repo / "untracked.txt").write_text("must not enter the archive\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "tests@example.invalid"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "integration tests"], cwd=repo, check=True)
    subprocess.run(["git", "add", "tracked.txt"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-qm", "fixture"], cwd=repo, check=True)
    return repo


def test_staged_workspace_contains_only_committed_head(tmp_path):
    repo = git_fixture(tmp_path)
    with integration_gate.staged_workspace(repo) as workspace:
        assert (workspace / "tracked.txt").read_text(encoding="utf-8") == "tracked\n"
        assert not (workspace / "untracked.txt").exists()


def test_run_integration_passes_in_clean_workspace(tmp_path):
    repo = git_fixture(tmp_path)
    command = [sys.executable, "-c",
               "from pathlib import Path; assert Path('tracked.txt').exists(); "
               "assert not Path('untracked.txt').exists()"]
    report = integration_gate.run_integration(repo, "0010", BASE, HEAD, command)
    assert report["status"] == "pass"
    assert report["isolated"] is True
    assert report["metrics"]["exit_code"] == 0


def test_nonzero_command_is_a_failed_integration(tmp_path):
    report = integration_gate.run_integration(
        git_fixture(tmp_path), "0010", BASE, HEAD,
        [sys.executable, "-c", "raise SystemExit(7)"],
    )
    assert report["status"] == "fail"
    assert report["metrics"]["exit_code"] == 7


def test_timeout_is_an_error_not_a_pass(tmp_path):
    report = integration_gate.run_integration(
        git_fixture(tmp_path), "0010", BASE, HEAD,
        [sys.executable, "-c", "import time; time.sleep(2)"],
        timeout_seconds=1,
    )
    assert report["status"] == "error"
    assert report["metrics"]["exit_code"] is None


def test_cli_writes_machine_readable_report(tmp_path):
    repo = git_fixture(tmp_path)
    output = tmp_path / "reports" / "0010.json"
    result = subprocess.run(
        [sys.executable, str(Path(__file__).parents[1] / "scripts" / "integration_gate.py"),
         "0010", "--base-sha", BASE, "--head-sha", HEAD, "--repo", str(repo),
         "--output", str(output), "--command", sys.executable, "-c", "pass"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0
    data = json.loads(output.read_text(encoding="utf-8"))
    assert data["schema_version"] == 1
    assert data["status"] == "pass"


def test_invalid_identity_is_rejected(tmp_path):
    with pytest.raises(ValueError, match="full hexadecimal"):
        integration_gate.run_integration(git_fixture(tmp_path), "0010", "short", HEAD)
