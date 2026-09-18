from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.flake_gate import evaluate


HISTORY = {"schema_version": 1, "history_version": 1, "tests": [
    {"test_id": "test_a", "statuses": ["fail", "pass"]},
    {"test_id": "test_b", "statuses": ["pass"]},
]}
AS_OF = "2026-09-18T12:00:00+00:00"


def manifest(path: Path, expires_at: str):
    path.write_text(json.dumps({"schema_version": 1, "quarantines": [{
        "test_id": "test_a", "owner": "team", "reason": "investigate",
        "expires_at": expires_at,
    }]}), encoding="utf-8")


def test_active_quarantine_is_degraded_not_green(tmp_path: Path):
    path = tmp_path / "quarantine.json"
    manifest(path, "2026-09-19T00:00:00Z")
    report = evaluate(HISTORY, path, AS_OF)
    assert report["status"] == "degraded"
    assert report["metrics"]["active_quarantines"] == 1
    assert report["policy"]["quarantined_is_not_green"] is True


def test_expired_and_missing_quarantines_block(tmp_path: Path):
    path = tmp_path / "quarantine.json"
    manifest(path, "2026-09-17T00:00:00Z")
    expired = evaluate(HISTORY, path, AS_OF)
    assert expired["status"] == "block"
    path.write_text(json.dumps({"schema_version": 1, "quarantines": []}), encoding="utf-8")
    missing = evaluate(HISTORY, path, AS_OF)
    assert missing["metrics"]["unquarantined_flakes"] == 1
    assert missing["status"] == "block"


def test_invalid_manifest_is_rejected(tmp_path: Path):
    path = tmp_path / "quarantine.json"
    path.write_text(json.dumps({"schema_version": 1, "quarantines": [{"test_id": "test_a"}]}), encoding="utf-8")
    with pytest.raises(ValueError, match="owner and reason"):
        evaluate(HISTORY, path, AS_OF)
