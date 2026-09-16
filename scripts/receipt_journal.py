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
            received_at TEXT NOT NULL
        );
        CREATE TRIGGER IF NOT EXISTS events_no_update
        BEFORE UPDATE ON events BEGIN SELECT RAISE(ABORT, 'receipt journal is append-only'); END;
        CREATE TRIGGER IF NOT EXISTS events_no_delete
        BEFORE DELETE ON events BEGIN SELECT RAISE(ABORT, 'receipt journal is append-only'); END;
        """
    )
    db.commit()
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
    db = connect(journal)
    try:
        existing = db.execute(
            "SELECT receipt_sha256, base_sha, head_sha FROM events WHERE event_id = ?",
            (event_id,),
        ).fetchone()
        if existing:
            if existing[0] != digest or existing[1] != base_sha or existing[2] != head_sha:
                raise ValueError("event_id already exists with different evidence")
            return {"status": "duplicate", "event_id": event_id, "receipt_sha256": digest}
        db.execute(
            "INSERT INTO events VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (event_id, event_type, base_sha, head_sha, digest, payload_json,
             source, timestamp, datetime.now(timezone.utc).isoformat()),
        )
        db.commit()
        return {"status": "appended", "event_id": event_id, "receipt_sha256": digest}
    finally:
        db.close()


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
    }


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
    args = parser.parse_args()
    try:
        if args.command == "append":
            result = append_event(args.journal, args.event_id, args.event_type,
                                  args.receipt, args.base_sha, args.head_sha,
                                  args.source, args.occurred_at)
            print(json.dumps(result, sort_keys=True))
        else:
            result = summarize(args.journal)
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
            print(json.dumps(result, sort_keys=True))
    except (OSError, TypeError, ValueError, json.JSONDecodeError, sqlite3.Error) as exc:
        print(f"ERROR: receipt journal failed: {type(exc).__name__}")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
