from __future__ import annotations

from pathlib import Path

import pytest

from scripts.receipt_journal import append_test_result, summarize_test_history


BASE, HEAD = "a" * 40, "b" * 40
AS_OF = "2026-09-18T12:00:00+00:00"


def add(journal: Path, event_id: str, test_id: str, status: str, when: str):
    return append_test_result(journal, event_id, test_id, status, 100,
                              BASE, HEAD, event_id, "worker-a", when)


def test_history_reports_flakes_and_stale_tests(tmp_path: Path):
    journal = tmp_path / "receipts.sqlite"
    add(journal, "run-1", "tests/test_a.py::test_a", "pass", "2026-09-18T10:00:00Z")
    add(journal, "run-2", "tests/test_a.py::test_a", "fail", "2026-09-18T11:00:00Z")
    add(journal, "run-3", "tests/test_b.py::test_b", "pass", "2026-09-16T00:00:00Z")
    report = summarize_test_history(journal, AS_OF, stale_after_seconds=3_600)
    assert report["test_count"] == 2
    assert report["result_event_count"] == 3
    assert report["flaky_test_count"] == 1
    assert report["stale_test_count"] == 1
    assert report["latest_status_counts"] == {"fail": 1, "pass": 1}
    assert report["freshness_ratio"] == 0.5
    assert report["tests"][0]["test_id"] == "tests/test_a.py::test_a"


def test_identical_result_replay_is_idempotent_and_conflict_is_rejected(tmp_path: Path):
    journal = tmp_path / "receipts.sqlite"
    first = add(journal, "run-1", "test_a", "pass", "2026-09-18T10:00:00Z")
    second = add(journal, "run-1", "test_a", "pass", "2026-09-18T10:00:00Z")
    assert first["status"] == "appended"
    assert second["status"] == "duplicate"
    with pytest.raises(ValueError, match="different evidence"):
        add(journal, "run-1", "test_a", "fail", "2026-09-18T10:00:00Z")


def test_invalid_result_is_rejected(tmp_path: Path):
    with pytest.raises(ValueError, match="duration_ms"):
        append_test_result(tmp_path / "receipts.sqlite", "run-1", "test_a", "pass",
                           -1, BASE, HEAD, "run-1")
