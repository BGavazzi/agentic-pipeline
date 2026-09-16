from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

SCRIPT_PATH = Path(__file__).resolve().parent.parent / "scripts" / "staging_gate.py"
spec = importlib.util.spec_from_file_location("staging_gate", SCRIPT_PATH)
staging_gate = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(staging_gate)

BASE = "a" * 40
HEAD = "b" * 40


def scorecard(admitted: bool = True) -> dict:
    return {
        "schema_version": 1,
        "scorecard_version": 1,
        "base_sha": BASE,
        "head_sha": HEAD,
        "admitted": admitted,
        "quality_band": "green" if admitted else "blocked",
        "risk_level": "medium",
        "metrics": {"evidence_completeness": 1.0},
    }


def integration(status: str = "pass", isolated: bool = True) -> dict:
    return {
        "schema_version": 1,
        "base_sha": BASE,
        "head_sha": HEAD,
        "status": status,
        "isolated": isolated,
        "metrics": {"duration_seconds": 12.5},
    }


def test_admitted_isolated_candidate_is_eligible_for_staging():
    result = staging_gate.evaluate(scorecard(), integration(), BASE, HEAD)

    assert result["eligible"] is True
    assert result["target"] == "staging-review"
    assert result["metrics"] == {
        "evidence_completeness": 1.0,
        "integration_duration_seconds": 12.5,
        "integration_isolated": True,
        "risk_level": "medium",
    }


@pytest.mark.parametrize(
    ("card", "run", "expected"),
    [
        (scorecard(False), integration(), "admission"),
        (scorecard(), integration("fail"), "integration"),
        (scorecard(), integration(isolated=False), "integration_isolation"),
    ],
)
def test_failed_autonomous_evidence_blocks_staging(card, run, expected):
    result = staging_gate.evaluate(card, run, BASE, HEAD)

    assert result["eligible"] is False
    assert expected in result["blockers"]


def test_stale_commit_pair_is_rejected():
    run = integration()
    run["head_sha"] = "c" * 40

    with pytest.raises(ValueError, match="different commit pair"):
        staging_gate.evaluate(scorecard(), run, BASE, HEAD)


def test_incomplete_evidence_blocks_without_becoming_green():
    card = scorecard()
    card["metrics"]["evidence_completeness"] = 0.75

    result = staging_gate.evaluate(card, integration(), BASE, HEAD)

    assert result["eligible"] is False
    assert result["blockers"]["evidence_completeness"] == "0.750"


def test_invalid_sha_is_rejected():
    with pytest.raises(ValueError, match="base_sha"):
        staging_gate.evaluate(scorecard(), integration(), "not-a-sha", HEAD)
