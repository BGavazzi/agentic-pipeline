from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from scripts import staging_dispatch

BASE = "a" * 40
HEAD = "b" * 40


def test_compose_body_keeps_evidence_visible(tmp_path: Path):
    body = tmp_path / "body.md"
    intelligence = tmp_path / "intelligence.json"
    body.write_text("Candidate survived isolated integration.\n", encoding="utf-8")
    intelligence.write_text(json.dumps({"schema_version": 1, "intelligence_version": 1,
        "base_sha": BASE, "head_sha": HEAD,
        "risk": {"level": "high", "triggers": [], "affected_module_count": 0, "required_gate_count": 1},
        "diff": {"changed_file_count": 1, "churn": 1, "additions": 1, "deletions": 0},
        "gates": {"passed_count": 1, "observed_count": 1, "status": "complete"},
        "test_impact": {}, "human_review": {"checkpoint": "before staging", "decision": "required_before_staging", "triggers": []},
        "contact_surfaces": {}}), encoding="utf-8")
    result = staging_dispatch.compose_body(body, intelligence, BASE, HEAD)
    assert "isolated integration" in result
    assert "`high`" in result
    assert "---" in result


def test_dispatch_is_dry_run_by_default_and_checks_base_and_head(tmp_path, monkeypatch):
    eligibility = tmp_path / "eligibility.json"
    eligibility.write_text(json.dumps({
        "schema_version": 1, "target": "staging-review", "eligible": True,
        "blockers": {}, "base_sha": BASE, "head_sha": HEAD,
        "provenance": {"human_review_required": True},
    }), encoding="utf-8")
    body = tmp_path / "body.md"
    body.write_text("review\n", encoding="utf-8")
    calls = []
    monkeypatch.setattr(staging_dispatch.staging_pr, "git_sha",
                        lambda _repo, ref: BASE if ref == "staging" else HEAD)
    monkeypatch.setattr(staging_dispatch.staging_pr, "create_staging_pr",
                        lambda *args, **kwargs: calls.append((args, kwargs)) or {"status": "dry_run"})
    result = staging_dispatch.dispatch(eligibility, tmp_path, "owner/repo",
                                      "candidate", "staging", "Stage", body)
    assert result["status"] == "dry_run"
    assert result["write_authorized"] is False
    assert result["human_review_required"] is True
    assert calls[0][1]["dry_run"] is True


def test_dispatch_rejects_stale_staging_base(tmp_path, monkeypatch):
    eligibility = tmp_path / "eligibility.json"
    eligibility.write_text(json.dumps({
        "schema_version": 1, "target": "staging-review", "eligible": True,
        "blockers": {}, "base_sha": BASE, "head_sha": HEAD,
        "provenance": {"human_review_required": True},
    }), encoding="utf-8")
    body = tmp_path / "body.md"
    body.write_text("review\n", encoding="utf-8")
    monkeypatch.setattr(staging_dispatch.staging_pr, "git_sha",
                        lambda _repo, ref: "c" * 40 if ref == "staging" else HEAD)
    with pytest.raises(ValueError, match="base SHA"):
        staging_dispatch.dispatch(eligibility, tmp_path, "owner/repo",
                                 "candidate", "staging", "Stage", body)
