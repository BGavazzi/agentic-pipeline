#!/usr/bin/env python3
"""Exercise admission fail-closed behavior against deterministic mutations.

This is a safety contract for the gate itself, not a security proof. Each
mutation starts from a complete high-risk receipt set and must either raise a
validation error or return ``admitted=false``. A mutation that still admits is
reported as an unsafe survivor and makes the benchmark fail.
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
    from .blast_radius import required_gates_for
except ImportError:  # pragma: no cover - exercised by the CLI entry point.
    from admission_gate import evaluate
    from blast_radius import required_gates_for

SCHEMA_VERSION = 1
BENCHMARK_VERSION = "1.0"
BASE_SHA = "a" * 40
HEAD_SHA = "b" * 40


def _documents() -> tuple[dict[str, Any], dict[str, Any]]:
    identity = {"schema_version": 1, "base_sha": BASE_SHA, "head_sha": HEAD_SHA}
    required = required_gates_for("high", [])
    risk = dict(identity, risk_level="high", risk_triggers=[], required_gates=required)
    receipts = dict(identity, gates=[
        {"gate": gate, "status": "pass"}
        for gate in sorted(set(required) | {"sast", "sca", "secrets", "policy"})
    ])
    return risk, receipts


def _mutations() -> dict[str, Callable[[dict[str, Any], dict[str, Any]], None]]:
    def stale_head(risk: dict[str, Any], receipts: dict[str, Any]) -> None:
        receipts["head_sha"] = "c" * 40

    def unsupported_schema(risk: dict[str, Any], receipts: dict[str, Any]) -> None:
        receipts["schema_version"] = 2

    def duplicate_gate(risk: dict[str, Any], receipts: dict[str, Any]) -> None:
        receipts["gates"].append(copy.deepcopy(receipts["gates"][0]))

    def unknown_gate(risk: dict[str, Any], receipts: dict[str, Any]) -> None:
        receipts["gates"][0]["gate"] = "magic"

    def removed_obligation(risk: dict[str, Any], receipts: dict[str, Any]) -> None:
        risk["required_gates"] = ["unit"]

    def empty_obligation(risk: dict[str, Any], receipts: dict[str, Any]) -> None:
        risk["required_gates"] = []

    def failed_unit(risk: dict[str, Any], receipts: dict[str, Any]) -> None:
        next(item for item in receipts["gates"] if item["gate"] == "unit")["status"] = "fail"

    def missing_policy(risk: dict[str, Any], receipts: dict[str, Any]) -> None:
        receipts["gates"] = [item for item in receipts["gates"] if item["gate"] != "policy"]

    def malformed_receipt(risk: dict[str, Any], receipts: dict[str, Any]) -> None:
        receipts["gates"][0] = "not-an-object"

    return {
        "stale-head": stale_head,
        "unsupported-schema": unsupported_schema,
        "duplicate-gate": duplicate_gate,
        "unknown-gate": unknown_gate,
        "removed-obligation": removed_obligation,
        "empty-obligation": empty_obligation,
        "failed-unit": failed_unit,
        "missing-policy": missing_policy,
        "malformed-receipt": malformed_receipt,
    }


def run_benchmark() -> dict[str, Any]:
    started = time.monotonic()
    cases: list[dict[str, Any]] = []
    for name, mutate in _mutations().items():
        risk, receipts = _documents()
        mutate(risk, receipts)
        try:
            result = evaluate(risk, receipts, BASE_SHA, HEAD_SHA)
            blocked = result.get("admitted") is False
            outcome = "blocked" if blocked else "unsafe-admitted"
            error_type = None
        except (TypeError, ValueError, KeyError) as exc:
            blocked = True
            outcome = "rejected"
            error_type = type(exc).__name__
        cases.append({"name": name, "outcome": outcome, "blocked": blocked, "error_type": error_type})
    unsafe = [case["name"] for case in cases if not case["blocked"]]
    blocked = sum(case["blocked"] for case in cases)
    return {
        "schema_version": SCHEMA_VERSION,
        "benchmark_version": BENCHMARK_VERSION,
        "status": "pass" if cases and not unsafe else "fail",
        "metrics": {
            "mutations_total": len(cases),
            "mutations_blocked": blocked,
            "mutations_unsafe": len(unsafe),
            "fail_closed_rate": blocked / len(cases) if cases else 0.0,
            "duration_seconds": round(time.monotonic() - started, 3),
        },
        "unsafe_mutations": unsafe,
        "cases": cases,
        "policy": {"complete_evidence_fixture_is_not_a_production_approval": True},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        report = run_benchmark()
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    except (OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print("ERROR: receipt mutation benchmark failed: " + type(exc).__name__, flush=True)
        return 2
    print(
        f"receipt_mutation_benchmark: {report['status']} "
        f"blocked={report['metrics']['mutations_blocked']}/{report['metrics']['mutations_total']}"
    )
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
