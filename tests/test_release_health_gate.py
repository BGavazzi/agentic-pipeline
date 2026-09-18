from __future__ import annotations

import pytest

from scripts.release_health_gate import evaluate


CANDIDATE = "a" * 40
ROLLBACK = "b" * 40


def evidence(status: str = "pass"):
    return {"schema_version": 1, "health_version": 1, "commit_sha": CANDIDATE,
            "environment": "staging", "status": status,
            "checks": [{"name": "http", "status": status}]}


def rollback():
    return {"schema_version": 1, "rollback_version": 1, "target_sha": ROLLBACK,
            "environment": "staging", "owner": "release-team",
            "runbook": "docs/rollback.md", "dry_run_verified": True}


def test_healthy_evidence_and_valid_rollback_plan_pass_without_authority():
    report = evaluate(evidence(), rollback(), CANDIDATE, "staging")
    assert report["status"] == "pass"
    assert report["rollback_plan_valid"] is True
    assert report["trusted_producer_observed"] is False
    assert report["command_execution"] is False


def test_failed_health_blocks_even_with_valid_rollback_plan():
    report = evaluate(evidence("fail"), rollback(), CANDIDATE, "staging")
    assert report["status"] == "block"
    assert "http" in report["health_failures"]


@pytest.mark.parametrize("mutation", [
    {"commit_sha": "c" * 40},
    {"environment": "production"},
])
def test_stale_health_identity_blocks(mutation):
    health = evidence()
    health.update(mutation)
    with pytest.raises(ValueError, match="different"):
        evaluate(health, rollback(), CANDIDATE, "staging")


def test_unverified_rollback_plan_is_rejected():
    plan = rollback()
    plan["dry_run_verified"] = False
    with pytest.raises(ValueError, match="dry_run"):
        evaluate(evidence(), plan, CANDIDATE, "staging")
