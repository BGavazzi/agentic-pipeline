#!/usr/bin/env python3
"""Store compact, versioned KPI vectors and summarize long-run variance.

This intentionally stores numerical features and input hashes, not raw logs.
The vector is an embedding-like representation for trend analysis, not a
semantic-model embedding and never an admission signal. Feature names are
sorted and schema-versioned so changes in dimensionality are observable.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
FEATURE_SCHEMA_VERSION = 1
SHA_RE = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")
SKIP_KEYS = {"schema_version", "timestamp", "occurred_at", "received_at",
             "base_sha", "head_sha", "run_id", "repository", "commit"}


def _timestamp(value: str) -> str:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        raise ValueError("timestamp requires a timezone")
    return parsed.astimezone(timezone.utc).isoformat()


def _walk(value: Any, path: tuple[str, ...] = ()) -> list[tuple[str, float]]:
    if type(value) in (int, float) and math.isfinite(float(value)) and path:
        return [(".".join(path), float(value))]
    if isinstance(value, dict):
        result: list[tuple[str, float]] = []
        for key in sorted(value):
            if isinstance(key, str) and key not in SKIP_KEYS:
                result.extend(_walk(value[key], path + (key,)))
        return result
    if isinstance(value, list):
        result = []
        for index, item in enumerate(value):
            result.extend(_walk(item, path + (str(index),)))
        return result
    return []


def _safe_name(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_.-]+", "_", value)[:160]


def build_snapshot(inputs: list[Path], repository: str, commit: str,
                   run_id: str, timestamp: str) -> dict[str, Any]:
    if not inputs:
        raise ValueError("at least one KPI report is required")
    if not repository or len(repository) > 200:
        raise ValueError("repository is required and bounded")
    if not isinstance(commit, str) or not SHA_RE.fullmatch(commit):
        raise ValueError("commit must be a full hexadecimal SHA")
    if not isinstance(run_id, str) or not run_id or len(run_id) > 240 \
            or any(char in run_id for char in "\r\n\t"):
        raise ValueError("run_id must be non-empty and single-line")
    occurred_at = _timestamp(timestamp)
    features: dict[str, float] = {}
    input_hashes: dict[str, str] = {}
    for path in sorted(inputs):
        raw = path.read_bytes()
        payload = json.loads(raw.decode("utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("each KPI report must be a JSON object")
        label = _safe_name(path.name)
        input_hashes[label] = hashlib.sha256(raw).hexdigest()
        for name, value in _walk(payload):
            key = f"{label}:{name}"
            if key in features:
                raise ValueError(f"duplicate KPI feature: {key}")
            features[key] = value
    if not features:
        raise ValueError("KPI reports contain no numeric features")
    names = sorted(features)
    values = [features[name] for name in names]
    return {
        "schema_version": SCHEMA_VERSION,
        "feature_schema_version": FEATURE_SCHEMA_VERSION,
        "kind": "kpi-vector",
        "repository": repository,
        "commit": commit,
        "run_id": run_id,
        "occurred_at": occurred_at,
        "input_hashes": input_hashes,
        "embedding": {
            "kind": "deterministic-numeric-kpi-vector",
            "feature_names": names,
            "values": values,
            "dimension": len(values),
        },
        "policy": {"raw_logs_retained": False, "descriptive_only": True,
                   "admission_authority": False},
    }


def _snapshot_digest(snapshot: dict[str, Any]) -> str:
    material = json.dumps(snapshot, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def connect(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path)
    db.executescript("""
        CREATE TABLE IF NOT EXISTS snapshots (
            run_id TEXT PRIMARY KEY,
            repository TEXT NOT NULL,
            commit_sha TEXT NOT NULL,
            feature_schema_version INTEGER NOT NULL,
            occurred_at TEXT NOT NULL,
            snapshot_sha256 TEXT NOT NULL,
            snapshot_json TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS kpi_points (
            run_id TEXT NOT NULL,
            feature_name TEXT NOT NULL,
            value REAL NOT NULL,
            occurred_at TEXT NOT NULL,
            PRIMARY KEY (run_id, feature_name),
            FOREIGN KEY (run_id) REFERENCES snapshots(run_id)
        );
        CREATE TRIGGER IF NOT EXISTS snapshots_no_update
        BEFORE UPDATE ON snapshots BEGIN SELECT RAISE(ABORT, 'KPI history is append-only'); END;
        CREATE TRIGGER IF NOT EXISTS snapshots_no_delete
        BEFORE DELETE ON snapshots BEGIN SELECT RAISE(ABORT, 'KPI history is append-only'); END;
        CREATE TRIGGER IF NOT EXISTS kpi_points_no_update
        BEFORE UPDATE ON kpi_points BEGIN SELECT RAISE(ABORT, 'KPI history is append-only'); END;
        CREATE TRIGGER IF NOT EXISTS kpi_points_no_delete
        BEFORE DELETE ON kpi_points BEGIN SELECT RAISE(ABORT, 'KPI history is append-only'); END;
    """)
    db.commit()
    return db


def append_snapshot(journal: Path, snapshot: dict[str, Any]) -> dict[str, Any]:
    if snapshot.get("schema_version") != SCHEMA_VERSION \
            or snapshot.get("feature_schema_version") != FEATURE_SCHEMA_VERSION:
        raise ValueError("unsupported KPI snapshot schema")
    embedding = snapshot.get("embedding")
    if not isinstance(embedding, dict):
        raise ValueError("KPI embedding is required")
    names, values = embedding.get("feature_names"), embedding.get("values")
    if not isinstance(names, list) or not isinstance(values, list) \
            or len(names) != len(values) or not names:
        raise ValueError("KPI feature names and values must be non-empty and aligned")
    if embedding.get("dimension") != len(names) or names != sorted(names):
        raise ValueError("KPI feature ordering/dimension is invalid")
    if any(not isinstance(name, str) or type(value) not in (int, float)
           or not math.isfinite(float(value)) for name, value in zip(names, values)):
        raise ValueError("KPI features must be finite numeric values")
    run_id = snapshot.get("run_id")
    if not isinstance(run_id, str) or not run_id:
        raise ValueError("KPI snapshot run_id is required")
    digest = _snapshot_digest(snapshot)
    payload = json.dumps(snapshot, sort_keys=True, separators=(",", ":"))
    db = connect(journal)
    try:
        db.execute("BEGIN IMMEDIATE")
        existing = db.execute(
            "SELECT snapshot_sha256 FROM snapshots WHERE run_id = ?", (run_id,)
        ).fetchone()
        if existing:
            if existing[0] != digest:
                raise ValueError("run_id already exists with different KPI evidence")
            return {"status": "duplicate", "run_id": run_id, "snapshot_sha256": digest}
        db.execute(
            "INSERT INTO snapshots VALUES (?, ?, ?, ?, ?, ?, ?)",
            (run_id, snapshot["repository"], snapshot["commit"],
             snapshot["feature_schema_version"], snapshot["occurred_at"], digest, payload),
        )
        db.executemany(
            "INSERT INTO kpi_points VALUES (?, ?, ?, ?)",
            [(run_id, name, float(value), snapshot["occurred_at"])
             for name, value in zip(names, values)],
        )
        db.commit()
        return {"status": "appended", "run_id": run_id, "snapshot_sha256": digest}
    finally:
        db.close()


def summarize(journal: Path, as_of: str | None = None,
              window_seconds: int | None = None) -> dict[str, Any]:
    reference = datetime.now(timezone.utc) if as_of is None else datetime.fromisoformat(as_of)
    if reference.tzinfo is None:
        raise ValueError("as_of requires a timezone")
    reference = reference.astimezone(timezone.utc)
    if window_seconds is not None and (type(window_seconds) is not int or window_seconds < 0):
        raise ValueError("window_seconds must be non-negative")
    db = connect(journal)
    try:
        rows = db.execute(
            "SELECT run_id, feature_name, value, occurred_at FROM kpi_points "
            "ORDER BY occurred_at, run_id, feature_name"
        ).fetchall()
    finally:
        db.close()
    grouped: dict[str, list[tuple[float, datetime]]] = {}
    run_ids: set[str] = set()
    for run_id, name, value, occurred_at in rows:
        run_ids.add(run_id)
        timestamp = datetime.fromisoformat(occurred_at).astimezone(timezone.utc)
        if window_seconds is not None and (reference - timestamp).total_seconds() > window_seconds:
            continue
        grouped.setdefault(name, []).append((float(value), timestamp))
    metrics = {}
    for name, points in sorted(grouped.items()):
        values = [value for value, _ in points]
        mean = sum(values) / len(values)
        variance = sum((value - mean) ** 2 for value in values) / len(values)
        ordered = sorted(values)
        p95_index = max(0, math.ceil(0.95 * len(ordered)) - 1)
        latest_at = max(timestamp for _, timestamp in points)
        metrics[name] = {
            "observations": len(values), "mean": mean, "variance": variance,
            "stddev": math.sqrt(variance), "min": min(values), "max": max(values),
            "p95": ordered[p95_index], "latest": values[-1],
            "latest_age_seconds": max(0.0, (reference - latest_at).total_seconds()),
        }
    return {
        "schema_version": SCHEMA_VERSION,
        "feature_schema_version": FEATURE_SCHEMA_VERSION,
        "kind": "kpi-timeseries-summary",
        "as_of": reference.isoformat(),
        "window_seconds": window_seconds,
        "snapshot_count": len(run_ids),
        "kpi_count": len(metrics),
        "metrics": metrics,
        "policy": {"raw_logs_retained": False, "descriptive_only": True,
                   "admission_authority": False},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    append = sub.add_parser("append")
    append.add_argument("--journal", type=Path, required=True)
    append.add_argument("--snapshot", type=Path, required=True)
    summary = sub.add_parser("summary")
    summary.add_argument("--journal", type=Path, required=True)
    summary.add_argument("--output", type=Path, required=True)
    summary.add_argument("--as-of")
    summary.add_argument("--window-seconds", type=int)
    args = parser.parse_args()
    try:
        if args.command == "append":
            result = append_snapshot(args.journal, json.loads(args.snapshot.read_text(encoding="utf-8")))
            print(json.dumps(result, sort_keys=True))
        else:
            result = summarize(args.journal, args.as_of, args.window_seconds)
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
            print(json.dumps(result, sort_keys=True))
    except (OSError, TypeError, ValueError, UnicodeError, json.JSONDecodeError, sqlite3.Error) as exc:
        print(f"ERROR: KPI history failed: {type(exc).__name__}")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
