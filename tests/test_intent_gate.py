from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from scripts import intent_gate


def git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True,
                          text=True).stdout.strip()


def repo_with_change(tmp_path: Path, filename: str = "scripts/change.py") -> tuple[Path, str, str]:
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "-b", "master")
    git(repo, "config", "user.name", "tests")
    git(repo, "config", "user.email", "tests@example.invalid")
    target = repo / filename
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("before\n", encoding="utf-8")
    git(repo, "add", ".")
    git(repo, "commit", "-m", "base")
    base = git(repo, "rev-parse", "HEAD")
    target.write_text("after\n", encoding="utf-8")
    git(repo, "add", ".")
    git(repo, "commit", "-m", "change")
    head = git(repo, "rev-parse", "HEAD")
    return repo, base, head


def intent(**overrides):
    value = {
        "schema_version": 1, "intent_version": 1, "task_id": "0081",
        "allowed_paths": ["scripts/**", "tests/**"], "forbidden_paths": [".github/**"],
        "allowed_effects": ["local-test"], "declared_effects": ["local-test"],
        "allowed_data_classes": ["public-source"], "data_classes": ["public-source"],
        "forbidden_effects": ["deploy", "external-write"], "observed_effects": [],
        "negative_tests": [],
    }
    value.update(overrides)
    return value


def test_valid_scope_is_eligible(tmp_path: Path):
    repo, base, head = repo_with_change(tmp_path)
    report = intent_gate.evaluate(intent(), repo, base, head)
    assert report["eligible"] is True
    assert report["human_review_required"] is True
    assert report["metrics"]["changed_file_count"] == 1


def test_path_outside_scope_blocks(tmp_path: Path):
    repo, base, head = repo_with_change(tmp_path, "app.py")
    report = intent_gate.evaluate(intent(), repo, base, head)
    assert report["eligible"] is False
    assert any(item["code"] == "path-outside-scope" for item in report["blockers"])


def test_forbidden_path_blocks_even_when_allowed(tmp_path: Path):
    repo, base, head = repo_with_change(tmp_path, ".github/workflows/ci.yml")
    value = intent(allowed_paths=["**"], forbidden_paths=[".github/**"])
    report = intent_gate.evaluate(value, repo, base, head)
    assert any(item["code"] == "forbidden-path" for item in report["blockers"])


def test_undeclared_effect_blocks(tmp_path: Path):
    repo, base, head = repo_with_change(tmp_path)
    report = intent_gate.evaluate(intent(declared_effects=["remote-write"]), repo, base, head)
    assert any(item["code"] == "effect-not-allowed" for item in report["blockers"])


def test_observed_effect_outside_allowlist_blocks(tmp_path: Path):
    repo, base, head = repo_with_change(tmp_path)
    report = intent_gate.evaluate(intent(observed_effects=["remote-write"]), repo, base, head)
    assert any(item["code"] == "observed-effect-not-allowed" for item in report["blockers"])


def test_sensitive_intent_requires_passing_negative_tests(tmp_path: Path):
    repo, base, head = repo_with_change(tmp_path)
    missing = intent(data_classes=["personal-data"], allowed_data_classes=["personal-data"])
    report = intent_gate.evaluate(missing, repo, base, head)
    assert any(item["code"] == "negative-tests-missing" for item in report["blockers"])

    passing = intent(data_classes=["personal-data"], allowed_data_classes=["personal-data"],
                     negative_tests=[{"name": "reject-unauthorized-read", "status": "pass"}])
    assert intent_gate.evaluate(passing, repo, base, head)["eligible"] is True


def test_failed_negative_test_blocks(tmp_path: Path):
    repo, base, head = repo_with_change(tmp_path)
    report = intent_gate.evaluate(
        intent(data_classes=["credentials"], allowed_data_classes=["credentials"],
               negative_tests=[{"name": "reject-secret-export", "status": "fail"}]),
        repo, base, head,
    )
    assert any(item["code"] == "negative-test-failed" for item in report["blockers"])


def test_invalid_schema_is_rejected(tmp_path: Path):
    repo, base, head = repo_with_change(tmp_path)
    with pytest.raises(ValueError, match="schema/version"):
        intent_gate.evaluate(intent(schema_version=2), repo, base, head)
