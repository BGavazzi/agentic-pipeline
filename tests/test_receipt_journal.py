from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from scripts.receipt_journal import append_event, summarize, verify_chain

BASE, HEAD = "a" * 40, "b" * 40


def receipt(path: Path, status: str = "pass") -> Path:
    path.write_text(json.dumps({"schema_version": 1, "gate": "unit", "status": status}), encoding="utf-8")
    return path


def test_append_is_idempotent_and_summary_is_replayable(tmp_path: Path):
    journal = tmp_path / "receipts.sqlite"
    item = receipt(tmp_path / "receipt.json")
    first = append_event(journal, "run-1", "unit", item, BASE, HEAD, "worker-a", "2026-09-16T00:00:00Z")
    second = append_event(journal, "run-1", "unit", item, BASE, HEAD, "worker-a", "2026-09-16T00:00:00Z")
    assert first["status"] == "appended"
    assert second["status"] == "duplicate"
    report = summarize(journal)
    assert report["event_count"] == 1
    assert report["candidate_pair_count"] == 1
    assert report["status_counts"] == {"pass": 1}
    assert report["replayable"] is True
    assert report["chain_valid"] is True
    assert report["chain_event_count"] == 1


def test_event_chain_binds_order_and_receipt_identity(tmp_path: Path):
    journal = tmp_path / "receipts.sqlite"
    first = receipt(tmp_path / "first.json")
    second = receipt(tmp_path / "second.json", "fail")
    one = append_event(journal, "run-1", "unit", first, BASE, HEAD)
    two = append_event(journal, "run-2", "unit", second, BASE, HEAD)
    assert one["event_sha256"] != two["event_sha256"]
    assert verify_chain(journal) == {"valid": True, "event_count": 2, "break_count": 0}


def test_conflicting_event_id_is_rejected(tmp_path: Path):
    journal = tmp_path / "receipts.sqlite"
    first = receipt(tmp_path / "first.json", "pass")
    second = receipt(tmp_path / "second.json", "fail")
    append_event(journal, "run-1", "unit", first, BASE, HEAD)
    with pytest.raises(ValueError, match="different evidence"):
        append_event(journal, "run-1", "unit", second, BASE, HEAD)


def test_update_and_delete_are_rejected(tmp_path: Path):
    journal = tmp_path / "receipts.sqlite"
    item = receipt(tmp_path / "receipt.json")
    append_event(journal, "run-1", "unit", item, BASE, HEAD)
    db = sqlite3.connect(journal)
    with pytest.raises(sqlite3.IntegrityError, match="append-only"):
        db.execute("DELETE FROM events WHERE event_id = 'run-1'")
    with pytest.raises(sqlite3.IntegrityError, match="append-only"):
        db.execute("UPDATE events SET source = 'changed' WHERE event_id = 'run-1'")
    db.close()
