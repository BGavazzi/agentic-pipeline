import subprocess
from pathlib import Path

from scripts.policy_integrity import build_report


def commit(repo: Path, message: str) -> str:
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", message], cwd=repo, check=True)
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()


def init_repo(tmp_path: Path) -> tuple[Path, str]:
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "policy@example.invalid"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Policy Fixture"], cwd=tmp_path, check=True)
    workflow = tmp_path / ".github" / "workflows"
    workflow.mkdir(parents=True)
    (workflow / "ci.yml").write_text("name: ci\n", encoding="utf-8")
    (tmp_path / "src.py").write_text("value = 1\n", encoding="utf-8")
    return tmp_path, commit(tmp_path, "base")


def test_product_change_does_not_require_policy_review(tmp_path: Path):
    repo, base = init_repo(tmp_path)
    (repo / "src.py").write_text("value = 2\n", encoding="utf-8")
    head = commit(repo, "product")
    report = build_report(repo, base, head)
    assert report["status"] == "pass"
    assert report["changed_policy_files"] == []


def test_workflow_change_requires_policy_review(tmp_path: Path):
    repo, base = init_repo(tmp_path)
    (repo / ".github" / "workflows" / "ci.yml").write_text("name: changed\n", encoding="utf-8")
    head = commit(repo, "policy")
    report = build_report(repo, base, head)
    assert report["status"] == "review_required"
    assert report["changed_policy_files"] == [".github/workflows/ci.yml"]
