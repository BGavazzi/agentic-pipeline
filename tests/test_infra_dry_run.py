from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import infra_dry_run


def repo_with_commits(tmp_path: Path, infra: bool) -> tuple[Path, str, str]:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "README.md").write_text("base\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "tests@example.invalid"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "infra tests"], cwd=repo, check=True)
    subprocess.run(["git", "add", "README.md"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-qm", "base"], cwd=repo, check=True)
    base = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
    path = repo / ("infra/main.tf" if infra else "src/main.py")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("candidate\n", encoding="utf-8")
    subprocess.run(["git", "add", str(path)], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-qm", "candidate"], cwd=repo, check=True)
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
    return repo, base, head


def test_non_infrastructure_change_is_not_applicable(tmp_path):
    repo, base, head = repo_with_commits(tmp_path, infra=False)

    result = infra_dry_run.run_dry_run(repo, "0027", base, head)

    assert result["status"] == "not_applicable"
    assert result["changed_infra_files"] == []


def test_infrastructure_change_without_profile_fails_closed(tmp_path):
    repo, base, head = repo_with_commits(tmp_path, infra=True)

    result = infra_dry_run.run_dry_run(repo, "0027", base, head)

    assert result["status"] == "error"
    assert result["changed_infra_files"] == ["infra/main.tf"]


def test_infrastructure_profile_runs_in_clean_candidate_workspace(tmp_path):
    repo, base, head = repo_with_commits(tmp_path, infra=True)
    (repo / "untracked-secret.txt").write_text("must not enter\n", encoding="utf-8")
    command = [sys.executable, "-c",
               "from pathlib import Path; assert Path('infra/main.tf').exists(); "
               "assert not Path('untracked-secret.txt').exists()"]

    result = infra_dry_run.run_dry_run(repo, "0027", base, head, command)

    assert result["status"] == "pass"
    assert result["isolated"] is True
    assert result["metrics"]["exit_code"] == 0


def test_failed_infrastructure_profile_is_not_pass(tmp_path):
    repo, base, head = repo_with_commits(tmp_path, infra=True)

    result = infra_dry_run.run_dry_run(
        repo, "0027", base, head, [sys.executable, "-c", "raise SystemExit(9)"],
    )

    assert result["status"] == "fail"
    assert result["metrics"]["exit_code"] == 9


def test_invalid_identity_is_rejected(tmp_path):
    repo, _, head = repo_with_commits(tmp_path, infra=False)
    with pytest.raises(ValueError, match="full hexadecimal"):
        infra_dry_run.run_dry_run(repo, "0027", "short", head)
