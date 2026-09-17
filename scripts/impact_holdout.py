#!/usr/bin/env python3
"""Evaluate test-impact analysis on a versioned held-out mutation corpus.

The ordinary impact benchmark is a development contract. This companion gate
keeps a separately named corpus of seeded changes so selector changes cannot
silently overfit the fixtures used to build them. It never authorizes skipping
the full suite; it only emits evidence that a future promotion decision can
consume.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path
from typing import Any

try:
    from .impact_benchmark import run_benchmark, run_case
except ImportError:  # pragma: no cover - exercised by the CLI entry point.
    from impact_benchmark import run_benchmark, run_case

SCHEMA_VERSION = 1
HOLDOUT_BENCHMARK_VERSION = "1.0"
MIN_HOLDOUT_CASES = 3


def _corpus_hash(fixtures: Path) -> str:
    material = b"".join(
        path.name.encode() + path.read_bytes()
        for path in sorted(fixtures.glob("*.json"))
    )
    return hashlib.sha256(material).hexdigest()


def _holdout_case(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"holdout fixture is not an object: {path}")
    if value.get("corpus") != "holdout":
        raise ValueError(f"fixture must declare corpus=holdout: {path}")
    if not isinstance(value.get("fault_seed"), str) or not value["fault_seed"]:
        raise ValueError(f"fixture needs a non-empty fault_seed: {path}")
    if not isinstance(value.get("fault_type"), str) or not value["fault_type"]:
        raise ValueError(f"fixture needs a non-empty fault_type: {path}")
    result = run_case(path)
    result["fault_seed"] = value["fault_seed"]
    result["fault_type"] = value["fault_type"]
    return result


def run_holdout_benchmark(training: Path, holdout: Path) -> dict[str, Any]:
    """Run the ordinary corpus plus an independent seeded-fault corpus."""
    started = time.monotonic()
    training_report = run_benchmark(training)
    cases = [_holdout_case(path) for path in sorted(holdout.glob("*.json"))]
    passed = sum(case["status"] == "pass" for case in cases)
    recalls = [case["metrics"]["recall"] for case in cases]
    precisions = [case["metrics"]["precision"] for case in cases]
    fault_types = sorted({case["fault_type"] for case in cases})
    holdout_pass = bool(cases) and passed == len(cases)
    sufficient = len(cases) >= MIN_HOLDOUT_CASES
    promotion_ready = bool(
        training_report["status"] == "pass"
        and training_report["promotion_ready"]
        and holdout_pass
        and sufficient
        and min(recalls, default=0.0) >= 1.0
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "benchmark_version": HOLDOUT_BENCHMARK_VERSION,
        "corpus": {
            "training_sha256": training_report["corpus_sha256"],
            "holdout_sha256": _corpus_hash(holdout),
            "holdout_case_count": len(cases),
            "minimum_holdout_cases": MIN_HOLDOUT_CASES,
        },
        "status": "pass" if training_report["status"] == "pass" and holdout_pass else "fail",
        "promotion_ready": promotion_ready,
        "metrics": {
            "training_cases": training_report["metrics"]["cases_total"],
            "training_mean_recall": training_report["metrics"]["mean_recall"],
            "holdout_cases": len(cases),
            "holdout_passed": passed,
            "holdout_failed": len(cases) - passed,
            "holdout_mean_precision": sum(precisions) / len(precisions) if precisions else 0.0,
            "holdout_mean_recall": sum(recalls) / len(recalls) if recalls else 0.0,
            "holdout_worst_recall": min(recalls, default=0.0),
            "fault_types": fault_types,
            "duration_seconds": round(time.monotonic() - started, 3),
        },
        "training": training_report,
        "holdout_cases": cases,
        "policy": {
            "full_suite_remains_authoritative": True,
            "promotion_requires_independent_holdout": True,
            "promotion_requires_worst_case_recall": 1.0,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--training", type=Path, default=Path("tests/impact/fixtures"))
    parser.add_argument("--holdout", type=Path, default=Path("tests/impact/holdout"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        report = run_holdout_benchmark(args.training.resolve(), args.holdout.resolve())
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    except (OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print("ERROR: held-out impact benchmark failed: " + type(exc).__name__, flush=True)
        return 2
    print(
        f"impact_holdout: {report['status']} "
        f"recall={report['metrics']['holdout_worst_recall']:.3f} "
        f"promotion_ready={report['promotion_ready']}"
    )
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
