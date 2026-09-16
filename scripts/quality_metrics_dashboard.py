#!/usr/bin/env python3
"""Aggregate PR-intelligence receipts into a denominator-first dashboard.

The dashboard is descriptive telemetry, not an admission controller. It
accepts one or more JSON files/directories, validates the receipt identity
shape, reports invalid inputs separately, and emits JSON plus Markdown. Rates
always include their denominator; a small sample is labeled as calibration and
never presented as a risk guarantee.
"""
from __future__ import annotations

import argparse
import json
import math
import statistics
from collections import Counter
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
DASHBOARD_VERSION = 1


def discover(inputs: list[Path]) -> list[Path]:
    paths: set[Path] = set()
    for item in inputs:
        if item.is_file() and item.suffix.lower() == ".json":
            paths.add(item)
        elif item.is_dir():
            paths.update(item.rglob("*.json"))
    return sorted(paths)


def load_reports(paths: list[Path]) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    valid: list[dict[str, Any]] = []
    invalid: list[dict[str, str]] = []
    for path in paths:
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(value, dict) or value.get("schema_version") != 1 \
                    or value.get("intelligence_version") != 1:
                raise ValueError("unsupported intelligence schema")
            if not isinstance(value.get("base_sha"), str) or not isinstance(value.get("head_sha"), str):
                raise ValueError("missing commit identity")
            valid.append(value)
        except (OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
            invalid.append({"path": str(path), "error": type(exc).__name__})
    return valid, invalid


def p95(values: list[float]) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = max(0, math.ceil(0.95 * len(ordered)) - 1)
    return ordered[index]


def build_dashboard(reports: list[dict[str, Any]], invalid_count: int = 0) -> dict[str, Any]:
    risk = Counter(str(item.get("risk", {}).get("level", "unknown")) for item in reports)
    decisions = Counter(str(item.get("human_review", {}).get("decision", "unknown")) for item in reports)
    gate_status = [item.get("gates", {}) for item in reports]
    gate_blocked = sum(gate.get("status") != "complete" for gate in gate_status)
    review_required = sum(item.get("human_review", {}).get("decision") == "required_before_staging" for item in reports)
    churn = [float(item.get("diff", {}).get("churn")) for item in reports
             if isinstance(item.get("diff", {}).get("churn"), (int, float))]
    completeness = [float(item.get("gates", {}).get("evidence_completeness")) for item in reports
                    if isinstance(item.get("gates", {}).get("evidence_completeness"), (int, float))]
    ratios = [float(item["diff"]["test_to_source_file_ratio"]) for item in reports
              if isinstance(item.get("diff", {}).get("test_to_source_file_ratio"), (int, float))]
    impact_status = Counter(str(item.get("test_impact", {}).get("status", "missing")) for item in reports)
    return {
        "schema_version": SCHEMA_VERSION,
        "dashboard_version": DASHBOARD_VERSION,
        "sample": {
            "valid_receipt_count": len(reports),
            "invalid_receipt_count": invalid_count,
            "calibration_only": len(reports) < 30,
        },
        "risk": {"counts": dict(sorted(risk.items())),
                 "high_rate": (risk.get("high", 0) / len(reports)) if reports else None},
        "human_review": {
            "decision_counts": dict(sorted(decisions.items())),
            "required_before_staging_count": review_required,
            "required_before_staging_rate": (review_required / len(reports)) if reports else None,
        },
        "evidence": {
            "blocked_evidence_count": gate_blocked,
            "blocked_evidence_rate": (gate_blocked / len(reports)) if reports else None,
            "completeness_mean": statistics.fmean(completeness) if completeness else None,
        },
        "diff": {
            "churn_mean": statistics.fmean(churn) if churn else None,
            "churn_p95": p95(churn),
            "test_source_ratio_mean": statistics.fmean(ratios) if ratios else None,
        },
        "test_impact": {
            "status_counts": dict(sorted(impact_status.items())),
            "available_rate": ((len(reports) - impact_status.get("missing", 0)) / len(reports)) if reports else None,
        },
        "limitations": [
            "This is descriptive telemetry, not proof of correctness or absence of escaped defects.",
            "Rates are not statistically stable until the declared sample reaches 30 eligible changes.",
            "Admission remains a non-compensating veto policy; this dashboard never overrides a gate.",
        ],
    }


def markdown(report: dict[str, Any]) -> str:
    sample = report["sample"]
    risk = report["risk"]
    hitl = report["human_review"]
    evidence = report["evidence"]
    diff = report["diff"]
    impact = report["test_impact"]
    lines = [
        "# Agentic quality metrics dashboard",
        "",
        f"Sample: **{sample['valid_receipt_count']} valid receipts**; invalid inputs: **{sample['invalid_receipt_count']}**; calibration-only: **{sample['calibration_only']}**.",
        "",
        "| Dimension | Metric | Value |",
        "|---|---|---:|",
        f"| Risk | High-risk rate | {risk['high_rate']} |",
        f"| HITL | Required before staging | {hitl['required_before_staging_count']}/{sample['valid_receipt_count']} ({hitl['required_before_staging_rate']}) |",
        f"| Evidence | Non-complete evidence | {evidence['blocked_evidence_count']}/{sample['valid_receipt_count']} ({evidence['blocked_evidence_rate']}) |",
        f"| Evidence | Completeness mean | {evidence['completeness_mean']} |",
        f"| Diff | Churn p95 | {diff['churn_p95']} |",
        f"| Diff | Test/source ratio mean | {diff['test_source_ratio_mean']} |",
        f"| TIA | Available rate | {impact['available_rate']} |",
        "",
        "Admission is still fail-closed and non-compensating; these measurements do not create a quality score that can offset a failed gate.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, required=True)
    args = parser.parse_args()
    try:
        paths = discover(args.input)
        reports, invalid = load_reports(paths)
        report = build_dashboard(reports, len(invalid))
        report["inputs"] = {"files": [str(path) for path in paths], "invalid": invalid}
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        args.markdown_output.write_text(markdown(report), encoding="utf-8")
    except (OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: metrics dashboard failed: {type(exc).__name__}")
        return 2
    print(f"quality_metrics_dashboard: receipts={len(reports)} invalid={len(invalid)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
