import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from quality_scorecard import build_scorecard


BASE, HEAD = "a" * 40, "b" * 40


def files(tmp_path, *, blocked=False):
    risk = tmp_path / "risk.json"
    receipts = tmp_path / "receipts.json"
    statuses = [
        {"gate": "integration", "status": "fail" if blocked else "pass"},
        {"gate": "sast", "status": "pass"},
        {"gate": "sca", "status": "pass"},
        {"gate": "secrets", "status": "pass"},
        {"gate": "unit", "status": "pass"},
        {"gate": "ultrareview", "status": "fail" if blocked else "pass"},
        {"gate": "policy", "status": "pass"},
    ]
    risk.write_text(json.dumps({
        "schema_version": 1, "base_sha": BASE, "head_sha": HEAD,
        "risk_level": "high", "risk_triggers": ["gate-script"],
        "required_gates": ["unit", "integration", "sast", "sca", "ultrareview"],
        "changed_files": ["scripts/x.py"], "affected_modules": ["scripts"],
    }))
    receipts.write_text(json.dumps({
        "schema_version": 1, "base_sha": BASE, "head_sha": HEAD,
        "gates": statuses,
    }))
    return risk, receipts


def test_complete_evidence_is_green_and_measured(tmp_path):
    risk, receipts = files(tmp_path)
    result = build_scorecard(risk, receipts, BASE, HEAD)
    assert result["quality_band"] == "green"
    assert result["admitted"] is True
    assert result["metrics"]["evidence_completeness"] == 1.0
    assert result["metrics"]["changed_file_count"] == 1


def test_blocked_evidence_is_not_green(tmp_path):
    risk, receipts = files(tmp_path, blocked=True)
    result = build_scorecard(risk, receipts, BASE, HEAD)
    assert result["quality_band"] == "blocked"
    assert result["admitted"] is False
    assert result["blockers"]["integration"] == "fail"


def test_optional_execution_metrics_are_provenance_bound(tmp_path):
    risk, receipts = files(tmp_path)
    integration = tmp_path / "integration.json"
    integration.write_text(json.dumps({
        "base_sha": BASE, "head_sha": HEAD, "isolated": True,
        "metrics": {"duration_seconds": 12.5},
    }))
    result = build_scorecard(risk, receipts, BASE, HEAD, integration_path=integration)
    assert result["metrics"]["integration_duration_seconds"] == 12.5
    assert result["metrics"]["integration_isolated"] is True


def test_stale_optional_report_is_rejected(tmp_path):
    risk, receipts = files(tmp_path)
    integration = tmp_path / "integration.json"
    integration.write_text(json.dumps({"base_sha": BASE, "head_sha": "c" * 40}))
    with pytest.raises(ValueError, match="integration report"):
        build_scorecard(risk, receipts, BASE, HEAD, integration_path=integration)
