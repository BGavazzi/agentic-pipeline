from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from scripts import staging_pr


BASE = "a" * 40
HEAD = "b" * 40


def eligibility(path: Path, eligible: bool = True):
    path.write_text(json.dumps({
        "schema_version": 1, "target": "staging-review", "eligible": eligible,
        "blockers": {} if eligible else {"admission": "blocked"},
        "base_sha": BASE, "head_sha": HEAD,
        "metrics": {"evidence_completeness": 1.0},
        "provenance": {"human_review_required": True},
    }))


def fake_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "staging tests"], cwd=repo, check=True)
    (repo / "README.md").write_text("candidate\n")
    subprocess.run(["git", "add", "README.md"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-qm", "candidate"], cwd=repo, check=True)
    return repo


def test_blocked_receipt_never_queries_or_creates_pr(tmp_path, monkeypatch):
    report = tmp_path / "eligibility.json"
    eligibility(report, eligible=False)
    called = []
    monkeypatch.setattr(staging_pr, "git_sha", lambda *args: HEAD)
    monkeypatch.setattr(staging_pr, "gh_json", lambda args: called.append(args))

    with pytest.raises(PermissionError):
        staging_pr.create_staging_pr(
            report, tmp_path, "owner/repo", "candidate", "staging",
            "Stage candidate", tmp_path / "body.md",
        )
    assert called == []


def test_dry_run_is_idempotent_and_returns_argv(tmp_path, monkeypatch):
    report = tmp_path / "eligibility.json"
    body = tmp_path / "body.md"
    eligibility(report)
    body.write_text("review me\n")
    monkeypatch.setattr(staging_pr, "git_sha", lambda *args: HEAD)
    monkeypatch.setattr(staging_pr, "gh_json", lambda args: [])

    result = staging_pr.create_staging_pr(
        report, tmp_path, "owner/repo", "candidate", "staging",
        "Stage candidate", body, dry_run=True,
    )

    assert result["status"] == "dry_run"
    assert result["command"][:4] == ["gh", "pr", "create", "--repo"]


def test_existing_open_pr_is_not_duplicated(tmp_path, monkeypatch):
    report = tmp_path / "eligibility.json"
    body = tmp_path / "body.md"
    eligibility(report)
    body.write_text("review me\n")
    monkeypatch.setattr(staging_pr, "git_sha", lambda *args: HEAD)
    monkeypatch.setattr(staging_pr, "gh_json", lambda args: [{"number": 7, "url": "https://example.test/7"}])

    result = staging_pr.create_staging_pr(
        report, tmp_path, "owner/repo", "candidate", "staging",
        "Stage candidate", body,
    )

    assert result["status"] == "already_exists"
    assert result["url"].endswith("/7")
