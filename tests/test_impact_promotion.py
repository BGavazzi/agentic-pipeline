from __future__ import annotations

import pytest
import hashlib
from pathlib import Path

from scripts.impact_promotion import evaluate


BASE = "a" * 40
HEAD = "b" * 40


def reports():
    benchmark = {
        "schema_version": 1,
        "benchmark_version": "0.4",
        "selector_sha256": hashlib.sha256((Path(__file__).parents[1] / "scripts/test_impact.py").read_bytes()).hexdigest(),
        "corpus_sha256": hashlib.sha256(b"".join(p.name.encode() + p.read_bytes()
                           for p in sorted((Path(__file__).parent / "impact/fixtures").glob("*.json")))).hexdigest(),
        "status": "pass",
        "promotion_ready": True,
        "metrics": {"mean_precision": 1.0, "mean_recall": 1.0},
    }
    impact = {
        "schema_version": 1,
        "base_sha": BASE,
        "head_sha": HEAD,
        "mode": "impacted",
        "selected_tests": ["tests/test_service.py"],
        "metrics": {
            "available_test_count": 4,
            "selected_test_count": 1,
            "selection_ratio": 0.25,
        },
    }
    shadow = {
        "schema_version": 1,
        "base_sha": BASE,
        "head_sha": HEAD,
        "status": "pass",
        "impact": impact,
        "execution": {"base_sha": BASE, "head_sha": HEAD, "status": "pass", "metrics": {"duration_seconds": 3.0}},
    }
    integration = {
        "schema_version": 1,
        "base_sha": BASE,
        "head_sha": HEAD,
        "status": "pass",
        "metrics": {"duration_seconds": 10.0},
    }
    return benchmark, impact, shadow, integration


def test_eligible_receipt_reports_savings_without_replacing_full_authority():
    result = evaluate(*reports(), BASE, HEAD)
    assert result["status"] == "pass"
    assert result["eligible"] is True
    assert result["metrics"]["tests_avoided"] == 3
    assert result["metrics"]["observed_duration_savings_seconds"] == 7.0
    assert result["policy"]["full_suite_authoritative"] is True


def test_benchmark_or_shadow_failure_blocks_promotion():
    benchmark, impact, shadow, integration = reports()
    benchmark["promotion_ready"] = False
    shadow["status"] = "fail"
    result = evaluate(benchmark, impact, shadow, integration, BASE, HEAD)
    assert result["status"] == "fail"
    assert result["eligible"] is False
    assert set(result["blockers"]) == {"benchmark", "shadow"}


def test_full_fallback_is_explicitly_not_applicable():
    benchmark, impact, shadow, integration = reports()
    impact["mode"] = "full"
    result = evaluate(benchmark, impact, shadow, integration, BASE, HEAD)
    assert result["status"] == "not_applicable"
    assert result["eligible"] is False
    assert "full-suite fallback" in result["blockers"]["selection"]


def test_stale_evidence_is_rejected():
    benchmark, impact, shadow, integration = reports()
    shadow["head_sha"] = "c" * 40
    with pytest.raises(ValueError, match="shadow report"):
        evaluate(benchmark, impact, shadow, integration, BASE, HEAD)
