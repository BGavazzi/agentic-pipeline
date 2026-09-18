from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.ci_telemetry import build_payload


SHA = "a" * 40


def test_builds_deterministic_otlp_metrics_without_secret_attributes(tmp_path: Path):
    report = tmp_path / "scorecard.json"
    report.write_text(json.dumps({"schema_version": 1, "metrics": {
        "evidence_completeness": 0.75, "affected_module_count": 3,
    }, "secret": "must-not-be-exported"}), encoding="utf-8")
    payload = build_payload([report], "BGavazzi/agentic-pipeline", SHA, "run 1",
                            "2026-09-18T12:00:00Z")
    assert payload["telemetry_version"] == 1
    assert payload["policy"] == {"network_export": False, "secret_free_attributes": True,
                                  "descriptive_only": True}
    attrs = payload["resourceMetrics"][0]["resource"]["attributes"]
    assert all("secret" not in item["key"] for item in attrs)
    metrics = payload["resourceMetrics"][0]["scopeMetrics"][0]["metrics"]
    assert [item["name"] for item in metrics] == [
        "agentic_pipeline_metrics_affected_module_count",
        "agentic_pipeline_metrics_evidence_completeness",
        "agentic_pipeline_schema_version",
    ]


def test_rejects_invalid_identity_or_non_object_report(tmp_path: Path):
    report = tmp_path / "bad.json"
    report.write_text("[]", encoding="utf-8")
    with pytest.raises(ValueError, match="JSON object"):
        build_payload([report], "repo", SHA, "run", "2026-09-18T12:00:00Z")
    report.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="commit"):
        build_payload([report], "repo", "short", "run", "2026-09-18T12:00:00Z")
