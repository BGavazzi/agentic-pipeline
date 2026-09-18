from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import scripts.local_integration_loop as loop_module
from scripts.local_integration_loop import (
    Candidate,
    _safe_env,
    classify_candidate,
    discover_open,
    integrate,
    load_manifest,
    run_loop,
)


def git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True,
                          text=True).stdout.strip()


def repo_with_candidates(tmp_path: Path) -> tuple[Path, str, str, str]:
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "-b", "master")
    git(repo, "config", "user.name", "tests")
    git(repo, "config", "user.email", "tests@example.invalid")
    (repo / "app.py").write_text("value = 1\n", encoding="utf-8")
    git(repo, "add", ".")
    git(repo, "commit", "-m", "base")
    base = git(repo, "rev-parse", "HEAD")
    git(repo, "checkout", "-b", "routine")
    (repo / "app.py").write_text("value = 2\n", encoding="utf-8")
    (repo / "feature.py").write_text("value = 2\n", encoding="utf-8")
    git(repo, "add", ".")
    git(repo, "commit", "-m", "routine")
    routine = git(repo, "rev-parse", "HEAD")
    git(repo, "checkout", "-b", "acute", base)
    (repo / ".github" / "workflows").mkdir(parents=True)
    (repo / ".github" / "workflows" / "ci.yml").write_text("name: test\n", encoding="utf-8")
    git(repo, "add", ".")
    git(repo, "commit", "-m", "workflow")
    acute = git(repo, "rev-parse", "HEAD")
    git(repo, "checkout", "master")
    return repo, base, routine, acute


def test_classification_marks_workflow_change_acute(tmp_path: Path):
    repo, base, _, acute = repo_with_candidates(tmp_path)
    result = classify_candidate(repo, base, Candidate(2, "workflow", acute), acute)
    assert result["classification"] == "acute"
    assert "CI/workflow" in result["contact_surfaces"]


def test_loop_merges_routine_and_holds_acute_without_remote_write(tmp_path: Path):
    repo, base, routine, acute = repo_with_candidates(tmp_path)
    result = integrate(repo, "master", [Candidate(1, "routine", routine),
                                         Candidate(2, "acute", acute)],
                       (sys.executable, "-c", "raise SystemExit(0)"), timeout=30)
    assert result["status"] == "review_required"
    assert result["included_prs"] == [1]
    assert result["held_prs"] == [2]
    assert result["remote_write"] is False
    assert result["policy"]["credential_env_scrubbed"] is True
    assert not list(repo.glob("pipeline-local-integration-*"))


def test_fork_candidate_is_held_before_ref_resolution(tmp_path: Path):
    repo, _, _, _ = repo_with_candidates(tmp_path)
    result = integrate(
        repo,
        "master",
        [Candidate(9, "fork", "ref-that-must-not-be-fetched", is_cross_repository=True)],
        (sys.executable, "-c", "raise SystemExit(0)"),
        timeout=30,
    )
    item = result["candidates"][0]
    assert result["held_prs"] == [9]
    assert item["reason"] == "fork_pr_requires_human_review"
    assert item["risk_level"] == "high"
    assert item["required_gates"][-1] == "ultrareview"


def test_base_ref_mismatch_is_held_before_resolution(tmp_path: Path):
    repo, _, routine, _ = repo_with_candidates(tmp_path)
    result = integrate(repo, "master", [Candidate(10, "wrong-base", routine,
                                                   base_ref="integration")], timeout=30)
    assert result["held_prs"] == [10]
    assert result["candidates"][0]["reason"] == "candidate_base_ref_mismatch"


def test_unexpected_runner_exception_rolls_back_before_next_candidate(tmp_path: Path, monkeypatch):
    repo, _, routine, _ = repo_with_candidates(tmp_path)
    calls = 0

    def flaky_runner(worktree, command, timeout):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise OSError("simulated worker launch failure")
        return {"status": "pass", "exit_code": 0, "duration_seconds": 0.0,
                "stdout_bytes": 0, "stderr_bytes": 0}

    monkeypatch.setattr(loop_module, "_run_command", flaky_runner)
    result = integrate(repo, "master", [Candidate(11, "first", routine),
                                         Candidate(12, "second", routine)], timeout=30)
    assert result["held_prs"] == [11]
    assert result["included_prs"] == [12]


def test_failed_routine_is_held_and_local_merge_is_reverted(tmp_path: Path):
    repo, _, routine, _ = repo_with_candidates(tmp_path)
    result = integrate(
        repo,
        "master",
        [Candidate(1, "routine", routine)],
        (sys.executable, "-c", "from pathlib import Path; Path('orphan.txt').write_text('x'); raise SystemExit(7)"),
        timeout=30,
    )
    assert result["included_prs"] == []
    assert result["held_prs"] == [1]
    assert result["candidates"][0]["reason"] == "integration_failed"
    assert not (repo / "feature.py").exists()
    assert not (repo / "orphan.txt").exists()


def test_later_candidate_conflict_is_held_after_prior_survivor(tmp_path: Path):
    repo, base, routine, _ = repo_with_candidates(tmp_path)
    git(repo, "checkout", "-b", "conflict", base)
    (repo / "app.py").write_text("value = 3\n", encoding="utf-8")
    git(repo, "add", ".")
    git(repo, "commit", "-m", "conflict")
    conflict = git(repo, "rev-parse", "HEAD")
    git(repo, "checkout", "master")
    result = integrate(repo, "master", [Candidate(1, "routine", routine),
                                         Candidate(3, "conflict", conflict)],
                       (sys.executable, "-c", "raise SystemExit(0)"), timeout=30)
    assert result["included_prs"] == [1]
    assert result["held_prs"] == [3]
    assert result["candidates"][1]["reason"] == "merge_conflict"


def test_safe_environment_drops_credential_like_names(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("GH_TOKEN", "must-not-cross-boundary")
    monkeypatch.setenv("GIT_DIR", "must-not-redirect-git")
    monkeypatch.setenv("SSH_AUTH_SOCK", "must-not-forward-agent")
    monkeypatch.setenv("PIPELINE_MODE", "safe")
    env = _safe_env()
    assert "GH_TOKEN" not in env
    assert "GIT_DIR" not in env
    assert "SSH_AUTH_SOCK" not in env
    assert env["PIPELINE_MODE"] == "safe"


def test_local_merge_commit_bypasses_repository_hooks(tmp_path: Path):
    repo, _, routine, _ = repo_with_candidates(tmp_path)
    hooks = tmp_path / "hooks"
    hooks.mkdir()
    (hooks / "pre-commit").write_text("#!/bin/sh\nexit 77\n", encoding="utf-8")
    git(repo, "config", "core.hooksPath", str(hooks))
    result = integrate(repo, "master", [Candidate(13, "routine", routine)],
                       (sys.executable, "-c", "raise SystemExit(0)"), timeout=30)
    assert result["included_prs"] == [13]


def test_discovery_normalizes_origin_prefix(monkeypatch):
    seen: list[list[str]] = []

    class Result:
        returncode = 0
        stdout = '[{"number": 7, "title": "routine", "headRefName": "feature", "headRefOid": "' + 'a' * 40 + '"}]'

    def fake_run(args, **kwargs):
        seen.append(args)
        return Result()

    monkeypatch.setattr("scripts.local_integration_loop.subprocess.run", fake_run)
    candidates = discover_open("OWNER/REPO", "origin/feat/base")
    assert candidates[0].number == 7
    assert seen[0][seen[0].index("--base") + 1] == "feat/base"


def test_stateful_loop_skips_same_immutable_head(tmp_path: Path):
    repo, _, routine, _ = repo_with_candidates(tmp_path)
    state = tmp_path / "state.json"
    candidate = Candidate(1, "routine", routine, head_sha=routine)
    command = (sys.executable, "-c", "raise SystemExit(0)")
    first = run_loop(repo, "master", [candidate], command, timeout=30, state_path=state)
    second = run_loop(repo, "master", [candidate], command, timeout=30, state_path=state)
    assert first["included_prs"] == [1]
    assert second["included_prs"] == []
    assert second["metrics"]["skipped_processed_count"] == 1
    assert second["metrics"]["rounds_completed"] == 0


def test_stateful_loop_keeps_acute_hold_visible(tmp_path: Path):
    repo, _, _, acute = repo_with_candidates(tmp_path)
    state = tmp_path / "state.json"
    candidate = Candidate(2, "workflow", acute, head_sha=acute)
    command = (sys.executable, "-c", "raise SystemExit(0)")
    first = run_loop(repo, "master", [candidate], command, timeout=30, state_path=state)
    second = run_loop(repo, "master", [candidate], command, timeout=30, state_path=state, max_rounds=2)
    assert first["held_prs"] == [2]
    assert second["held_prs"] == [2]
    assert second["metrics"]["candidates_total"] == 2
    assert second["metrics"]["bundle_unique_count"] == 1
    assert second["metrics"]["skipped_processed_count"] == 0


def test_manifest_is_deterministic_and_validates_duplicate_ids(tmp_path: Path):
    path = tmp_path / "candidates.json"
    value = {"candidates": [{"number": 2, "title": "two", "ref": "abc"},
                             {"number": 1, "title": "one", "ref": "def"}]}
    path.write_text(json.dumps(value), encoding="utf-8")
    assert [item.number for item in load_manifest(path)] == [1, 2]
