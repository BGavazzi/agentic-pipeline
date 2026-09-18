#!/usr/bin/env python3
"""Export local quality reports as provider-neutral OTLP JSON metrics.

The adapter is deliberately file-only: it never sends telemetry or credentials
to a collector. A later deployment may upload this validated payload through a
protected, configured exporter. Numeric report fields are emitted with a
denominator-preserving report label; strings and paths are not copied into
metric attributes.
"""
from __future__ import annotations

import argparse
import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
SHA_RE = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")
NAME_RE = re.compile(r"[^a-z0-9_]+")


def _timestamp(value: str) -> int:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        raise ValueError("timestamp requires a timezone")
    return int(parsed.astimezone(timezone.utc).timestamp() * 1_000_000_000)


def _metric_name(path: tuple[str, ...]) -> str:
    parts = [NAME_RE.sub("_", part.lower()).strip("_") for part in path]
    return "agentic_pipeline_" + "_".join(part for part in parts if part)


def _numeric(value: Any) -> bool:
    return type(value) in (int, float) and math.isfinite(float(value))


def _walk(value: Any, path: tuple[str, ...] = ()) -> list[tuple[str, float]]:
    if _numeric(value) and path:
        return [(_metric_name(path), float(value))]
    if isinstance(value, dict):
        result: list[tuple[str, float]] = []
        for key in sorted(value):
            if isinstance(key, str) and key not in {"timestamp", "occurred_at"}:
                result.extend(_walk(value[key], path + (key,)))
        return result
    return []


def build_payload(inputs: list[Path], repository: str, commit: str,
                  run_id: str, timestamp: str) -> dict[str, Any]:
    if not repository or len(repository) > 200:
        raise ValueError("repository is required and bounded")
    if not SHA_RE.fullmatch(commit):
        raise ValueError("commit must be a full hexadecimal commit SHA")
    if not run_id or len(run_id) > 240 or any(c in run_id for c in "\r\n\t"):
        raise ValueError("run_id must be non-empty, single-line and bounded")
    timestamp_ns = _timestamp(timestamp)
    if not inputs:
        raise ValueError("at least one report is required")
    metrics: dict[str, list[dict[str, Any]]] = {}
    for path in sorted(inputs):
        value = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise ValueError("each report must be a JSON object")
        observations = _walk(value)
        report_label = path.name[:120]
        for name, numeric in observations:
            metrics.setdefault(name, []).append({
                "asDouble": numeric,
                "timeUnixNano": str(timestamp_ns),
                "attributes": [{"key": "report", "value": {"stringValue": report_label}}],
            })
    metric_items = [{"name": name, "gauge": {"dataPoints": points}}
                    for name, points in sorted(metrics.items())]
    return {
        "schema_version": SCHEMA_VERSION,
        "telemetry_version": 1,
        "resourceMetrics": [{
            "resource": {"attributes": [
                {"key": "service.name", "value": {"stringValue": "agentic-pipeline"}},
                {"key": "service.repository", "value": {"stringValue": repository}},
                {"key": "vcs.commit.sha", "value": {"stringValue": commit}},
                {"key": "ci.run.id", "value": {"stringValue": run_id}},
            ]},
            "scopeMetrics": [{"scope": {"name": "agentic-pipeline", "version": "1"},
                              "metrics": metric_items}],
        }],
        "policy": {"network_export": False, "secret_free_attributes": True,
                    "descriptive_only": True},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, action="append", required=True)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--timestamp", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        payload = build_payload(args.input, args.repository, args.commit,
                                args.run_id, args.timestamp)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    except (OSError, TypeError, ValueError, UnicodeError, json.JSONDecodeError) as exc:
        print(f"ERROR: CI telemetry export failed: {type(exc).__name__}")
        return 2
    metric_count = sum(len(metric["gauge"]["dataPoints"])
                       for metric in payload["resourceMetrics"][0]["scopeMetrics"][0]["metrics"])
    print(f"ci_telemetry: metrics={metric_count} network_export=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
