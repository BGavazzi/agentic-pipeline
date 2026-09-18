from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.kpi_history import append_snapshot, build_snapshot, summarize


BASE, HEAD = "a" * 40, "b" * 40


def report(path: Path, value: float) -> Path:
    path.write_text(json.dumps({"schema_version": 1, "metrics": {"risk": value,
                              "duration": value * 2}}), encoding="utf-8")
    return path


def snapshot(tmp_path: Path, run_id: str, value: float):
    return build_snapshot([report(tmp_path / "metrics.json", value)],
                          "repo", HEAD, run_id, "2026-09-18T12:00:00Z")


def test_snapshot_is_compact_versioned_and_hashes_inputs(tmp_path: Path):
    result = snapshot(tmp_path, "run-1", 2.0)
    assert result["embedding"]["dimension"] == 2
    assert result["embedding"]["feature_names"] == sorted(result["embedding"]["feature_names"])
    assert result["policy"]["raw_logs_retained"] is False
    assert len(result["input_hashes"]) == 1


def test_history_reports_variance_and_is_idempotent(tmp_path: Path):
    journal = tmp_path / "kpi.sqlite"
    assert append_snapshot(journal, snapshot(tmp_path, "run-1", 1.0))["status"] == "appended"
    assert append_snapshot(journal, snapshot(tmp_path, "run-2", 3.0))["status"] == "appended"
    duplicate = append_snapshot(journal, snapshot(tmp_path, "run-1", 1.0))
    assert duplicate["status"] == "duplicate"
    report_value = summarize(journal, "2026-09-18T13:00:00Z")
    metric = report_value["metrics"]["metrics.json:metrics.risk"]
    assert metric["observations"] == 2
    assert metric["mean"] == 2.0
    assert metric["variance"] == 1.0
    assert report_value["policy"]["admission_authority"] is False


def test_conflicting_run_id_and_invalid_empty_features_block(tmp_path: Path):
    journal = tmp_path / "kpi.sqlite"
    first = snapshot(tmp_path, "run-1", 1.0)
    append_snapshot(journal, first)
    changed = snapshot(tmp_path, "run-1", 2.0)
    with pytest.raises(ValueError, match="different KPI evidence"):
        append_snapshot(journal, changed)
    (tmp_path / "empty.json").write_text(json.dumps({"status": "pass"}), encoding="utf-8")
    with pytest.raises(ValueError, match="no numeric features"):
        build_snapshot([tmp_path / "empty.json"], "repo", HEAD, "run-3", "2026-09-18T12:00:00Z")


def test_window_excludes_old_observations(tmp_path: Path):
    journal = tmp_path / "kpi.sqlite"
    old = snapshot(tmp_path, "old", 1.0)
    old["occurred_at"] = "2026-09-17T12:00:00+00:00"
    append_snapshot(journal, old)
    append_snapshot(journal, snapshot(tmp_path, "new", 3.0))
    report_value = summarize(journal, "2026-09-18T13:00:00Z", window_seconds=3600)
    assert report_value["metrics"]["metrics.json:metrics.risk"]["observations"] == 1
