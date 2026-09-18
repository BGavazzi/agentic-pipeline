#!/usr/bin/env python3
"""Append-only local journal for replayable quality receipts.

The journal is a small SQLite event store for one host. SQLite gives concurrent
workers transactions and WAL durability without inventing a queue service.
Events are immutable: duplicate event IDs with the same receipt digest are
idempotent; reusing an ID for different evidence is rejected. Triggers reject
updates/deletes. The journal stores receipt payloads, not credentials, and has
no network or GitHub behavior.

This is descriptive evidence storage, not an admission controller. Consumers
must still validate receipt schemas, exact commit identity and policy freshness.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
SHA_RE = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")
EVENT_RE = re.compile(r"^[a-z][a-z0-9._-]{1,63}$")
TEST_ID_RE = re.compile(r"^[^\r\n\t]{1,240}$")
TEST_STATUSES = {"pass", "fail", "error", "skip"}


def connect(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path)
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA foreign_keys=ON")
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS journal_meta (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
        INSERT OR IGNORE INTO journal_meta(key, value) VALUES ('schema_version', '1');
        CREATE TABLE IF NOT EXISTS events (
            event_id TEXT PRIMARY KEY,
            event_type TEXT NOT NULL,
            base_sha TEXT NOT NULL,
            head_sha TEXT NOT NULL,
            receipt_sha256 TEXT NOT NULL,
            receipt_json TEXT NOT NULL,
            source TEXT NOT NULL,
            occurred_at TEXT NOT NULL,
            received_at TEXT NOT NULL,
            prev_event_sha256 TEXT,
            event_sha256 TEXT
        );
        CREATE TRIGGER IF NOT EXISTS events_no_update
        BEFORE UPDATE ON events BEGIN SELECT RAISE(ABORT, 'receipt journal is append-only'); END;
        CREATE TRIGGER IF NOT EXISTS events_no_delete
        BEFORE DELETE ON events BEGIN SELECT RAISE(ABORT, 'receipt journal is append-only'); END;
        """
    )
    columns = {row[1] for row in db.execute("PRAGMA table_info(events)")}
    if "prev_event_sha256" not in columns:
        db.execute("ALTER TABLE events ADD COLUMN prev_event_sha256 TEXT")
    if "event_sha256" not in columns:
        db.execute("ALTER TABLE events ADD COLUMN event_sha256 TEXT")
    db.commit()
    version = db.execute("SELECT value FROM journal_meta WHERE key='schema_version'").fetchone()
    if version != (str(SCHEMA_VERSION),):
        db.close()
        raise ValueError("unsupported journal schema version")
    return db


def _sha(value: str, label: str) -> None:
    if not isinstance(value, str) or not SHA_RE.fullmatch(value):
        raise ValueError(f"{label} must be a full hexadecimal commit SHA")


def append_event(journal: Path, event_id: str, event_type: str, receipt_path: Path,
                 base_sha: str, head_sha: str, source: str = "unknown",
                 occurred_at: str | None = None) -> dict[str, Any]:
    if not event_id or len(event_id) > 200:
        raise ValueError("event_id must be non-empty and bounded")
    if not EVENT_RE.fullmatch(event_type):
        raise ValueError("event_type has invalid format")
    _sha(base_sha, "base_sha")
    _sha(head_sha, "head_sha")
    if not source or len(source) > 200:
        raise ValueError("source must be non-empty and bounded")
    payload = json.loads(receipt_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("receipt must be a JSON object")
    payload_json = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(payload_json.encode("utf-8")).hexdigest()
    timestamp = occurred_at or datetime.now(timezone.utc).isoformat()
    parsed = datetime.fromisoformat(timestamp)
    if parsed.tzinfo is None:
        raise ValueError("occurred_at requires a timezone")
    timestamp = parsed.astimezone(timezone.utc).isoformat()
    return _append_payload(journal, event_id, event_type, payload,
                           base_sha, head_sha, source, timestamp)


def _append_payload(journal: Path, event_id: str, event_type: str,
                    payload: dict[str, Any], base_sha: str, head_sha: str,
                    source: str, timestamp: str) -> dict[str, Any]:
    payload_json = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(payload_json.encode("utf-8")).hexdigest()
    db = connect(journal)
    try:
        db.execute("BEGIN IMMEDIATE")
        existing = db.execute(
            "SELECT receipt_sha256, base_sha, head_sha, event_type, source FROM events WHERE event_id = ?",
            (event_id,),
        ).fetchone()
        if existing:
            if existing != (digest, base_sha, head_sha, event_type, source):
                raise ValueError("event_id already exists with different evidence")
            return {"status": "duplicate", "event_id": event_id, "receipt_sha256": digest}
        previous = db.execute(
            "SELECT event_sha256 FROM events "
            "ORDER BY received_at DESC, event_id DESC LIMIT 1"
        ).fetchone()
        previous_digest = previous[0] if previous and previous[0] else None
        event_material = json.dumps({
            "event_id": event_id, "event_type": event_type,
            "base_sha": base_sha, "head_sha": head_sha,
            "receipt_sha256": digest, "source": source,
            "occurred_at": timestamp, "prev_event_sha256": previous_digest,
        }, sort_keys=True, separators=(",", ":")).encode("utf-8")
        event_digest = hashlib.sha256(event_material).hexdigest()
        db.execute(
            "INSERT INTO events "
            "(event_id, event_type, base_sha, head_sha, receipt_sha256, "
            "receipt_json, source, occurred_at, received_at, prev_event_sha256, event_sha256) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (event_id, event_type, base_sha, head_sha, digest, payload_json,
             source, timestamp, datetime.now(timezone.utc).isoformat(),
             previous_digest, event_digest),
        )
        db.commit()
        return {"status": "appended", "event_id": event_id,
                "receipt_sha256": digest, "event_sha256": event_digest}
    finally:
        db.close()


def append_test_result(journal: Path, event_id: str, test_id: str,
                       status: str, duration_ms: int, base_sha: str,
                       head_sha: str, run_id: str, source: str = "unknown",
                       occurred_at: str | None = None) -> dict[str, Any]:
    """Append one replayable per-test result for future TIA selection.

    This records history only. It does not authorize skipping tests; the full
    suite remains authoritative until a separately validated promotion policy
    consumes this history.
    """
    if not isinstance(test_id, str) or not TEST_ID_RE.fullmatch(test_id):
        raise ValueError("test_id must be non-empty, single-line and bounded")
    if status not in TEST_STATUSES:
        raise ValueError("test status is invalid")
    if type(duration_ms) is not int or duration_ms < 0 or duration_ms > 86_400_000:
        raise ValueError("duration_ms must be a bounded non-negative integer")
    if not isinstance(run_id, str) or not run_id or len(run_id) > 240:
        raise ValueError("run_id must be non-empty and bounded")
    _sha(base_sha, "base_sha")
    _sha(head_sha, "head_sha")
    if not source or len(source) > 200:
        raise ValueError("source must be non-empty and bounded")
    timestamp = occurred_at or datetime.now(timezone.utc).isoformat()
    parsed = datetime.fromisoformat(timestamp)
    if parsed.tzinfo is None:
        raise ValueError("occurred_at requires a timezone")
    timestamp = parsed.astimezone(timezone.utc).isoformat()
    payload = {"schema_version": SCHEMA_VERSION, "kind": "test-result",
               "test_id": test_id, "status": status,
               "duration_ms": duration_ms, "run_id": run_id}
    return _append_payload(journal, event_id, "test-result", payload,
                           base_sha, head_sha, source, timestamp)


def summarize_test_history(journal: Path, as_of: str | None = None,
                           stale_after_seconds: int = 86_400) -> dict[str, Any]:
    """Summarize per-test freshness, flakiness and duration deterministically."""
    if type(stale_after_seconds) is not int or stale_after_seconds < 0:
        raise ValueError("stale_after_seconds must be a non-negative integer")
    reference = datetime.fromisoformat(as_of) if as_of else datetime.now(timezone.utc)
    if reference.tzinfo is None:
        raise ValueError("as_of requires a timezone")
    reference = reference.astimezone(timezone.utc)
    db = connect(journal)
    try:
        rows = db.execute(
            "SELECT receipt_json, occurred_at, received_at FROM events "
            "WHERE event_type = 'test-result' ORDER BY occurred_at, received_at, event_id"
        ).fetchall()
    finally:
        db.close()
    by_test: dict[str, list[tuple[dict[str, Any], str]]] = {}
    for raw, occurred_at, _received_at in rows:
        payload = json.loads(raw)
        if payload.get("kind") != "test-result":
            continue
        test_id = payload.get("test_id")
        if isinstance(test_id, str):
            by_test.setdefault(test_id, []).append((payload, occurred_at))
    stale = 0
    flaky = 0
    latest_statuses: dict[str, int] = {}
    durations: list[int] = []
    max_age = 0.0
    tests: list[dict[str, Any]] = []
    for test_id in sorted(by_test):
        history = by_test[test_id]
        statuses = sorted({str(item["status"]) for item, _ in history})
        if "pass" in statuses and any(value in statuses for value in ("fail", "error")):
            flaky += 1
        latest, latest_at = history[-1]
        observed = (reference - datetime.fromisoformat(latest_at).astimezone(timezone.utc)).total_seconds()
        max_age = max(max_age, observed)
        is_stale = observed > stale_after_seconds
        stale += int(is_stale)
        latest_statuses[str(latest["status"])] = latest_statuses.get(str(latest["status"]), 0) + 1
        durations.extend(int(item["duration_ms"]) for item, _ in history)
        tests.append({"test_id": test_id, "latest_status": latest["status"],
                      "latest_occurred_at": latest_at, "runs": len(history),
                      "statuses": statuses, "stale": is_stale})
    return {"schema_version": SCHEMA_VERSION, "history_version": 1,
            "as_of": reference.isoformat(), "stale_after_seconds": stale_after_seconds,
            "test_count": len(tests), "result_event_count": len(rows),
            "flaky_test_count": flaky, "stale_test_count": stale,
            "freshness_ratio": round((len(tests) - stale) / len(tests), 4) if tests else 0.0,
            "max_age_seconds": round(max_age, 3) if tests else 0.0,
            "latest_status_counts": dict(sorted(latest_statuses.items())),
            "mean_duration_ms": round(sum(durations) / len(durations), 3) if durations else 0.0,
            "tests": tests}


def summarize(journal: Path) -> dict[str, Any]:
    db = connect(journal)
    try:
        rows = db.execute(
            "SELECT event_type, base_sha, head_sha, receipt_json, occurred_at FROM events "
            "ORDER BY received_at, event_id"
        ).fetchall()
    finally:
        db.close()
    statuses: dict[str, int] = {}
    types: dict[str, int] = {}
    candidates: set[tuple[str, str]] = set()
    occurred = []
    for event_type, base, head, raw, timestamp in rows:
        types[event_type] = types.get(event_type, 0) + 1
        candidates.add((base, head))
        occurred.append(timestamp)
        status = json.loads(raw).get("status", "unknown")
        statuses[str(status)] = statuses.get(str(status), 0) + 1
    chain = verify_chain(journal)
    return {
        "schema_version": SCHEMA_VERSION,
        "journal": str(journal),
        "append_only": True,
        "replayable": True,
        "event_count": len(rows),
        "candidate_pair_count": len(candidates),
        "event_type_counts": dict(sorted(types.items())),
        "status_counts": dict(sorted(statuses.items())),
        "first_occurred_at": min(occurred) if occurred else None,
        "last_occurred_at": max(occurred) if occurred else None,
        "chain_valid": chain["valid"],
        "chain_event_count": chain["event_count"],
        "chain_break_count": chain["break_count"],
    }


def verify_chain(journal: Path) -> dict[str, Any]:
    """Verify the append-only event hash chain without changing the journal."""
    db = connect(journal)
    try:
        rows = db.execute(
            "SELECT event_id, event_type, base_sha, head_sha, receipt_sha256, "
            "source, occurred_at, prev_event_sha256, event_sha256 "
            "FROM events ORDER BY received_at, event_id"
        ).fetchall()
    finally:
        db.close()
    previous = None
    breaks = 0
    for (event_id, event_type, base_sha, head_sha, receipt_sha, source,
         occurred_at, prev_digest, event_digest) in rows:
        material = json.dumps({
            "event_id": event_id, "event_type": event_type,
            "base_sha": base_sha, "head_sha": head_sha,
            "receipt_sha256": receipt_sha, "source": source,
            "occurred_at": occurred_at, "prev_event_sha256": prev_digest,
        }, sort_keys=True, separators=(",", ":")).encode("utf-8")
        expected = hashlib.sha256(material).hexdigest()
        if prev_digest != previous or event_digest != expected:
            breaks += 1
        previous = event_digest
    return {"valid": breaks == 0, "event_count": len(rows), "break_count": breaks}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    append = sub.add_parser("append")
    append.add_argument("--journal", type=Path, required=True)
    append.add_argument("--event-id", required=True)
    append.add_argument("--event-type", required=True)
    append.add_argument("--receipt", type=Path, required=True)
    append.add_argument("--base-sha", required=True)
    append.add_argument("--head-sha", required=True)
    append.add_argument("--source", default="unknown")
    append.add_argument("--occurred-at")
    summary = sub.add_parser("summary")
    summary.add_argument("--journal", type=Path, required=True)
    summary.add_argument("--output", type=Path, required=True)
    test_append = sub.add_parser("test-result-append")
    test_append.add_argument("--journal", type=Path, required=True)
    test_append.add_argument("--event-id", required=True)
    test_append.add_argument("--test-id", required=True)
    test_append.add_argument("--status", choices=sorted(TEST_STATUSES), required=True)
    test_append.add_argument("--duration-ms", type=int, required=True)
    test_append.add_argument("--base-sha", required=True)
    test_append.add_argument("--head-sha", required=True)
    test_append.add_argument("--run-id", required=True)
    test_append.add_argument("--source", default="unknown")
    test_append.add_argument("--occurred-at")
    test_summary = sub.add_parser("test-result-summary")
    test_summary.add_argument("--journal", type=Path, required=True)
    test_summary.add_argument("--output", type=Path, required=True)
    test_summary.add_argument("--as-of")
    test_summary.add_argument("--stale-after-seconds", type=int, default=86_400)
    args = parser.parse_args()
    try:
        if args.command == "append":
            result = append_event(args.journal, args.event_id, args.event_type,
                                  args.receipt, args.base_sha, args.head_sha,
                                  args.source, args.occurred_at)
            print(json.dumps(result, sort_keys=True))
        elif args.command == "summary":
            result = summarize(args.journal)
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
            print(json.dumps(result, sort_keys=True))
        elif args.command == "test-result-append":
            result = append_test_result(args.journal, args.event_id, args.test_id,
                                        args.status, args.duration_ms, args.base_sha,
                                        args.head_sha, args.run_id, args.source,
                                        args.occurred_at)
            print(json.dumps(result, sort_keys=True))
        else:
            result = summarize_test_history(args.journal, args.as_of,
                                            args.stale_after_seconds)
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
            print(json.dumps(result, sort_keys=True))
    except (OSError, TypeError, ValueError, json.JSONDecodeError, sqlite3.Error) as exc:
        print(f"ERROR: receipt journal failed: {type(exc).__name__}")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
