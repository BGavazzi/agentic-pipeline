#!/usr/bin/env python3
"""Decide whether conservative test-impact selection is promotion-ready.

The full integration suite remains authoritative. This receipt is an explicit
optimization boundary: a dispatcher may use an impacted subset only when the
versioned benchmark, the candidate selection, the shadow execution, and the
full execution all provide matching evidence. Unknown or stale evidence is
blocked rather than treated as permission to skip tests.

Exit codes:
    0 -- eligible, or explicitly not applicable because selection fell back full
    1 -- valid evidence but promotion is blocked
    2 -- invalid or stale evidence
"""
from __future__ import annotations

import argparse
import json
import re
import time
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
FULL_SHA = re.compile(r"^[0-9a-f]{40,64}$")


def _read(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"report is not an object: {path}")
    return value


def _identity(report: dict[str, Any], base_sha: str, head_sha: str, name: str) -> None:
    if report.get("base_sha") != base_sha or report.get("head_sha") != head_sha:
        raise ValueError(f"{name} report is for a different commit pair")


def evaluate(
    benchmark: dict[str, Any],
    impact: dict[str, Any],
    shadow: dict[str, Any],
    integration: dict[str, Any],
    base_sha: str,
    head_sha: str,
) -> dict[str, Any]:
    if not FULL_SHA.fullmatch(base_sha) or not FULL_SHA.fullmatch(head_sha):
        raise ValueError("base/head must be full hexadecimal commit SHAs")
    for report, name in ((impact, "impact"), (shadow, "shadow"), (integration, "integration")):
        _identity(report, base_sha, head_sha, name)
    if benchmark.get("schema_version") != 1 or benchmark.get("status") != "pass":
        raise ValueError("benchmark is missing schema-v1 pass status")
    if impact.get("schema_version") != 1 or shadow.get("schema_version") != 1:
        raise ValueError("impact/shadow report schema is unsupported")

    started = time.monotonic()
    mode = impact.get("mode")
    selected = impact.get("selected_tests", [])
    impact_metrics = impact.get("metrics", {})
    blockers: dict[str, str] = {}
    if mode != "impacted":
        return {
            "schema_version": SCHEMA_VERSION,
            "gate": "impact-promotion",
            "base_sha": base_sha,
            "head_sha": head_sha,
            "status": "not_applicable",
            "eligible": False,
            "blockers": {"selection": f"mode={mode!r}; full-suite fallback remains authoritative"},
            "metrics": {
                "selection_ratio": impact_metrics.get("selection_ratio", 1.0),
                "selected_test_count": len(selected) if isinstance(selected, list) else 0,
                "available_test_count": impact_metrics.get("available_test_count", 0),
                "evaluation_duration_seconds": round(time.monotonic() - started, 3),
            },
        }
    if benchmark.get("promotion_ready") is not True:
        blockers["benchmark"] = "promotion_ready=false"
    if shadow.get("status") != "pass" or shadow.get("execution", {}).get("status") != "pass":
        blockers["shadow"] = str(shadow.get("status", "missing"))
    if integration.get("status") != "pass":
        blockers["integration"] = str(integration.get("status", "missing"))
    if not isinstance(selected, list) or not selected:
        blockers["selection"] = "selected_tests_empty"
    benchmark_metrics = benchmark.get("metrics", {})
    shadow_duration = shadow.get("execution", {}).get("metrics", {}).get("duration_seconds")
    full_duration = integration.get("metrics", {}).get("duration_seconds")
    selected_count = len(selected) if isinstance(selected, list) else 0
    available_count = int(impact_metrics.get("available_test_count", 0))
    report = {
        "schema_version": SCHEMA_VERSION,
        "gate": "impact-promotion",
        "base_sha": base_sha,
        "head_sha": head_sha,
        "status": "pass" if not blockers else "fail",
        "eligible": not blockers,
        "blockers": blockers,
        "metrics": {
            "benchmark_version": benchmark.get("benchmark_version"),
            "benchmark_mean_precision": benchmark_metrics.get("mean_precision"),
            "benchmark_mean_recall": benchmark_metrics.get("mean_recall"),
            "selection_ratio": impact_metrics.get("selection_ratio"),
            "selected_test_count": selected_count,
            "available_test_count": available_count,
            "tests_avoided": max(0, available_count - selected_count),
            "shadow_duration_seconds": shadow_duration,
            "full_duration_seconds": full_duration,
            "observed_duration_savings_seconds": (
                round(float(full_duration) - float(shadow_duration), 3)
                if isinstance(full_duration, (int, float)) and isinstance(shadow_duration, (int, float))
                else None
            ),
            "evaluation_duration_seconds": round(time.monotonic() - started, 3),
        },
        "policy": {
            "full_suite_authoritative": True,
            "fallback_on_unknown": True,
            "promotion_requires_benchmark_and_shadow": True,
        },
    }
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--benchmark", type=Path, required=True)
    parser.add_argument("--impact", type=Path, required=True)
    parser.add_argument("--shadow", type=Path, required=True)
    parser.add_argument("--integration", type=Path, required=True)
    parser.add_argument("--base-sha", required=True)
    parser.add_argument("--head-sha", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        report = evaluate(
            _read(args.benchmark), _read(args.impact), _read(args.shadow),
            _read(args.integration), args.base_sha, args.head_sha,
        )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    except (OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print("ERROR: impact promotion failed: " + type(exc).__name__, flush=True)
        return 2
    print(f"impact_promotion: status={report['status']} eligible={str(report['eligible']).lower()}")
    return 0 if report["status"] == "pass" or report["status"] == "not_applicable" else 1


if __name__ == "__main__":
    raise SystemExit(main())
