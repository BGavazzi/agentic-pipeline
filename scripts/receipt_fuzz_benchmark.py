#!/usr/bin/env python3
"""Run a bounded deterministic property-style receipt fuzz benchmark.

The generated inputs are synthetic malformed values for authoritative nested
admission fields. Every case must either be rejected by the evaluator or
return ``admitted=false``. This is regression evidence for fail-closed
handling, not authenticity proof for a producer, runner, or CI platform.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import random
import sys
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
DEFAULT_SEED = 20260917
DEFAULT_CASES = 128
DEFAULT_MAX_DEPTH = 3
MAX_CASES = 512
MAX_DEPTH = 6
BASE_SHA = "a" * 40
HEAD_SHA = "b" * 40


def _fixture() -> tuple[dict[str, Any], dict[str, Any]]:
    required = required_gates_for("high", [])
    identity = {"schema_version": 1, "base_sha": BASE_SHA, "head_sha": HEAD_SHA}
    risk = dict(identity, risk_level="high", risk_triggers=[], required_gates=required)
    receipts = dict(identity, gates=[
        {"gate": gate, "status": "pass"}
        for gate in sorted(set(required) | {"sast", "sca", "secrets", "policy"})
    ])
    return risk, receipts


def _value_depth(value: Any) -> int:
    if isinstance(value, dict):
        return 1 + max((_value_depth(item) for item in value.values()), default=0)
    if isinstance(value, list):
        return 1 + max((_value_depth(item) for item in value), default=0)
    return 0


def _malformed_value(rng: random.Random, remaining_depth: int) -> Any:
    """Generate JSON-shaped noise with a hard recursive depth bound."""
    if remaining_depth <= 0:
        return rng.choice([None, False, 0, 2, "not-an-evidence-value"])
    shape = rng.randrange(5)
    if shape == 0:
        return None
    if shape == 1:
        return rng.choice([False, 0, 2, "not-an-evidence-value"])
    if shape == 2:
        return [_malformed_value(rng, remaining_depth - 1)]
    if shape == 3:
        return {"nested": _malformed_value(rng, remaining_depth - 1)}
    return {
        "nested": _malformed_value(rng, remaining_depth - 1),
        "shadow": _malformed_value(rng, max(0, remaining_depth - 1)),
    }


def _case_specs() -> tuple[tuple[str, Callable[[dict[str, Any], dict[str, Any], Any], None]], ...]:
    """Return mutations for fields consumed by ``admission_gate.evaluate``."""

    def risk_field(name: str) -> Callable[[dict[str, Any], dict[str, Any], Any], None]:
        return lambda risk, receipts, payload: risk.__setitem__(name, payload)

    def receipt_field(name: str) -> Callable[[dict[str, Any], dict[str, Any], Any], None]:
        return lambda risk, receipts, payload: receipts.__setitem__(name, payload)

    def gate_field(name: str) -> Callable[[dict[str, Any], dict[str, Any], Any], None]:
        return lambda risk, receipts, payload: receipts["gates"][0].__setitem__(name, payload)

    return (
        ("risk.schema_version", risk_field("schema_version")),
        ("risk.base_sha", risk_field("base_sha")),
        ("risk.head_sha", risk_field("head_sha")),
        ("risk.risk_level", risk_field("risk_level")),
        ("risk.risk_triggers", risk_field("risk_triggers")),
        ("risk.required_gates", risk_field("required_gates")),
        ("receipts.schema_version", receipt_field("schema_version")),
        ("receipts.base_sha", receipt_field("base_sha")),
        ("receipts.head_sha", receipt_field("head_sha")),
        ("receipts.gates", receipt_field("gates")),
        ("receipts.gates[0]", lambda risk, receipts, payload: receipts["gates"].__setitem__(0, payload)),
        ("receipts.gates[0].gate", gate_field("gate")),
        ("receipts.gates[0].status", gate_field("status")),
    )


def _payload(path: str, rng: random.Random, max_depth: int) -> Any:
    """Create a path-specific invalid replacement without exceeding max depth."""
    if path == "risk.risk_triggers":
        if max_depth == 0:
            return None
        return {"nested": _malformed_value(rng, max_depth - 1)}
    if path == "risk.required_gates":
        # The outer list is part of the replacement's measured depth.
        return [_malformed_value(rng, max_depth - 1)] if max_depth else None
    return _malformed_value(rng, max_depth)


def _payload_digest(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()[:16]


def run_benchmark(seed: int = DEFAULT_SEED, case_count: int = DEFAULT_CASES,
                  max_depth: int = DEFAULT_MAX_DEPTH) -> dict[str, Any]:
    """Generate and evaluate a bounded deterministic malformed-input corpus."""
    if type(seed) is not int:
        raise ValueError("seed must be an integer")
    if type(case_count) is not int or not 1 <= case_count <= MAX_CASES:
        raise ValueError(f"case_count must be between 1 and {MAX_CASES}")
    if type(max_depth) is not int or not 0 <= max_depth <= MAX_DEPTH:
        raise ValueError(f"max_depth must be between 0 and {MAX_DEPTH}")

    rng = random.Random(seed)
    specs = _case_specs()
    cases: list[dict[str, Any]] = []
    for index in range(case_count):
        spec_index = index if index < len(specs) else rng.randrange(len(specs))
        path, mutate = specs[spec_index]
        payload = _payload(path, rng, max_depth)
        risk, receipts = _fixture()
        mutate(risk, receipts, copy.deepcopy(payload))
        try:
            result = evaluate(risk, receipts, BASE_SHA, HEAD_SHA)
        except (AttributeError, IndexError, KeyError, TypeError, ValueError) as exc:
            outcome = "rejected"
            blocked = True
            error_type = type(exc).__name__
        else:
            blocked = result.get("admitted") is False
            outcome = "blocked" if blocked else "unsafe-admitted"
            error_type = None
        cases.append({
            "case_id": f"case-{index:04d}",
            "mutation_path": path,
            "payload_sha256_16": _payload_digest(payload),
            "payload_depth": _value_depth(payload),
            "outcome": outcome,
            "blocked": blocked,
            "error_type": error_type,
        })

    rejected = sum(case["outcome"] == "rejected" for case in cases)
    blocked = sum(case["outcome"] == "blocked" for case in cases)
    unsafe = [case["case_id"] for case in cases if case["outcome"] == "unsafe-admitted"]
    fail_closed = rejected + blocked
    return {
        "schema_version": SCHEMA_VERSION,
        "benchmark_version": BENCHMARK_VERSION,
        "status": "pass" if cases and not unsafe else "fail",
        "seed": seed,
        "bounds": {"cases_requested": case_count, "max_payload_depth": max_depth,
                    "hard_case_limit": MAX_CASES, "hard_depth_limit": MAX_DEPTH},
        "metrics": {
            "cases_total": len(cases),
            "cases_rejected": rejected,
            "cases_blocked": blocked,
            "cases_fail_closed": fail_closed,
            "cases_unsafe": len(unsafe),
            "fail_closed_rate": fail_closed / len(cases) if cases else 0.0,
            "max_observed_payload_depth": max((case["payload_depth"] for case in cases), default=0),
            "mutation_paths_covered": len({case["mutation_path"] for case in cases}),
        },
        "unsafe_survivors": unsafe,
        "cases": cases,
        "policy": {
            "property": "malformed authoritative nested input never admits",
            "synthetic_fuzz_evidence": True,
            "authenticity_proven": False,
            "full_suite_remains_authoritative": True,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--cases", type=int, default=DEFAULT_CASES)
    parser.add_argument("--max-depth", type=int, default=DEFAULT_MAX_DEPTH)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        report = run_benchmark(args.seed, args.cases, args.max_depth)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except (OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print("ERROR: receipt fuzz benchmark failed: " + type(exc).__name__, file=sys.stderr)
        return 2
    print(
        f"receipt_fuzz_benchmark: {report['status']} "
        f"fail_closed={report['metrics']['cases_fail_closed']}/{report['metrics']['cases_total']} "
        f"unsafe={report['metrics']['cases_unsafe']}"
    )
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
