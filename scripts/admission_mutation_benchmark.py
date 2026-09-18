#!/usr/bin/env python3
"""Measure whether admission fail-closed mutations are detected.

The benchmark starts from one known-admitted fixture and applies deterministic
mutations to risk/receipt identity, obligations, statuses, and gate names. A
mutation is killed when admission blocks or rejects it. This is a correctness
metric only; it never changes the admission result of a real candidate.
"""
from __future__ import annotations

import argparse
import copy
import json
import time
from pathlib import Path
from typing import Any, Callable

try:
    from .admission_gate import evaluate
except ImportError:  # pragma: no cover
    from admission_gate import evaluate

SCHEMA_VERSION = 1
MUTATION_VERSION = "0.1"


def _mutations(case: dict[str, Any]) -> list[tuple[str, Callable[[dict[str, Any], dict[str, Any]], None]]]:
    def drop_policy(_risk, receipts):
        receipts["gates"] = [item for item in receipts["gates"] if item["gate"] != "policy"]

    def fail_unit(_risk, receipts):
        next(item for item in receipts["gates"] if item["gate"] == "unit")["status"] = "fail"

    def stale_head(_risk, receipts):
        receipts["head_sha"] = "c" * 40

    def unknown_gate(_risk, receipts):
        receipts["gates"][0]["gate"] = "unknown"

    def remove_obligation(risk, _receipts):
        risk["required_gates"] = []

    return [("missing-policy", drop_policy), ("failed-unit", fail_unit),
            ("stale-receipt-head", stale_head), ("unknown-gate", unknown_gate),
            ("removed-risk-obligation", remove_obligation)]


def run_benchmark(fixture: Path) -> dict[str, Any]:
    started = time.monotonic()
    raw = json.loads(fixture.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("mutation fixture must be an object")
    base_sha, head_sha = raw["base_sha"], raw["head_sha"]
    risk, receipts = raw["risk"], raw["receipts"]
    baseline = evaluate(risk, receipts, base_sha, head_sha)
    if baseline["admitted"] is not True:
        raise ValueError("mutation fixture baseline must be admitted")
    cases = []
    for name, mutate in _mutations(raw):
        mutated_risk, mutated_receipts = copy.deepcopy(risk), copy.deepcopy(receipts)
        mutate(mutated_risk, mutated_receipts)
        try:
            observed = evaluate(mutated_risk, mutated_receipts, base_sha, head_sha)
            killed = observed["admitted"] is not True
            outcome = {"admitted": observed["admitted"]}
        except (TypeError, ValueError) as exc:
            killed = True
            outcome = {"error_type": type(exc).__name__}
        cases.append({"name": name, "killed": killed, "outcome": outcome})
    killed = sum(case["killed"] for case in cases)
    total = len(cases)
    return {
        "schema_version": SCHEMA_VERSION,
        "mutation_version": MUTATION_VERSION,
        "fixture": fixture.name,
        "status": "pass" if total and killed == total else "fail",
        "metrics": {
            "mutations_total": total, "mutations_killed": killed,
            "mutations_survived": total - killed,
            "mutation_score": killed / total if total else 0.0,
            "duration_seconds": round(time.monotonic() - started, 6),
        },
        "baseline": {"admitted": True}, "cases": cases,
        "policy": {"descriptive_only": True, "admission_authority": False},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", type=Path,
                        default=Path("tests/harness/fixtures/001-admission-pass.json"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        report = run_benchmark(args.fixture.resolve())
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    except (OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print("ERROR: admission mutation benchmark failed: " + type(exc).__name__, flush=True)
        return 2
    print(f"admission_mutation_benchmark: {report['status']} "
          f"score={report['metrics']['mutation_score']:.3f}")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
