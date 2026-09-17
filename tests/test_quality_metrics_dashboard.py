from __future__ import annotations

from scripts.quality_metrics_dashboard import build_dashboard, markdown


def receipt(risk: str, decision: str, churn: int, impact: str, completeness: float):
    return {
        "schema_version": 1, "intelligence_version": 1,
        "base_sha": "a" * 40, "head_sha": ("b" if risk == "high" else "c") * 40,
        "risk": {"level": risk},
        "human_review": {"decision": decision},
        "diff": {"churn": churn, "test_to_source_file_ratio": 0.5},
        "gates": {"status": "complete" if completeness == 1 else "blocked",
                  "evidence_completeness": completeness},
        "test_impact": {"status": impact},
    }


def test_dashboard_keeps_denominators_and_marks_small_sample():
    result = build_dashboard([
        receipt("high", "required_before_staging", 100, "pass", 1.0),
        receipt("low", "standard", 10, "missing", 0.5),
    ], invalid_count=1)
    assert result["sample"] == {
        "valid_receipt_count": 2, "invalid_receipt_count": 1, "calibration_only": True,
        "duplicate_receipt_count": 0,
    }
    assert result["risk"]["counts"] == {"high": 1, "low": 1}
    assert result["human_review"]["required_before_staging_count"] == 1
    assert result["human_review"]["required_before_staging_rate"] == 0.5
    assert result["evidence"]["blocked_evidence_rate"] == 0.5
    assert result["diff"]["churn_p95"] == 100.0
    assert result["test_impact"]["available_rate"] == 0.5


def test_dashboard_markdown_does_not_claim_proof():
    text = markdown(build_dashboard([receipt("high", "required_before_staging", 1, "missing", 0.0)]))
    assert "calibration-only: **True**" in text
    assert "not proof of correctness" in text
    assert "fail-closed and non-compensating" in text
