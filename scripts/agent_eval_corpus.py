#!/usr/bin/env python3
"""Run and summarize a versioned agent-evaluation corpus.

The corpus runner composes the existing ``meta_test`` fixture boundary with
denominator-preserving metrics. It intentionally reports ``insufficient_corpus``
until the configured minimum number of representative cases exists; one green
fixture is calibration evidence, not a quality claim. The worker command and
configuration contents are never written to the report—only a digest binds
the evaluated configuration to the result.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import statistics
import sys
from pathlib import Path
from typing import Any

try:
    from . import meta_test
except ImportError:  # pragma: no cover
    import meta_test  # type: ignore

SCHEMA_VERSION = 1
EVAL_VERSION = 1
SHA_RE = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")


def configuration_digest(command: list[str], configuration: Any = None) -> str:
    """Bind the worker invocation and model/config metadata without storing it."""
    payload = json.dumps({"command": command, "configuration": configuration},
                         sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _p95(values: list[float]) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    return ordered[max(0, math.ceil(len(ordered) * 0.95) - 1)]


def summarize(meta_report: dict[str, Any], *, min_cases: int = 20,
              baseline: dict[str, Any] | None = None) -> dict[str, Any]:
    if not isinstance(min_cases, int) or min_cases < 1:
        raise ValueError("min_cases must be positive")
    cases = meta_report.get("cases")
    if not isinstance(cases, list):
        raise ValueError("meta-test report must contain cases")
    passed = sum(case.get("status") == "pass" for case in cases if isinstance(case, dict))
    failed = len(cases) - passed
    durations = [float(case["metrics"]["duration_seconds"])
                 for case in cases if isinstance(case, dict)
                 and isinstance(case.get("metrics"), dict)
                 and isinstance(case["metrics"].get("duration_seconds"), (int, float))]
    tokens = [float(case["metrics"]["tokens"])
              for case in cases if isinstance(case, dict)
              and isinstance(case.get("metrics"), dict)
              and isinstance(case["metrics"].get("tokens"), (int, float))]
    costs = [float(case["metrics"]["cost_usd"])
             for case in cases if isinstance(case, dict)
             and isinstance(case.get("metrics"), dict)
             and isinstance(case["metrics"].get("cost_usd"), (int, float))]
    for value in [*durations, *tokens, *costs]:
        if not math.isfinite(value) or value < 0:
            raise ValueError("eval metrics must be finite and non-negative")
    pass_rate = passed / len(cases) if cases else None
    baseline_rate = None
    if baseline is not None:
        baseline_rate = baseline.get("metrics", {}).get("pass_rate")
        if not isinstance(baseline_rate, (int, float)) or not math.isfinite(float(baseline_rate)):
            raise ValueError("baseline pass_rate is invalid")
    regression = (pass_rate is not None and baseline_rate is not None
                  and pass_rate < float(baseline_rate))
    if regression:
        status = "regression"
    elif failed:
        status = "fail"
    elif len(cases) < min_cases:
        status = "insufficient_corpus"
    else:
        status = "pass"
    return {
        "schema_version": SCHEMA_VERSION,
        "eval_version": EVAL_VERSION,
        "status": status,
        "metrics": {
            "cases_total": len(cases),
            "cases_passed": passed,
            "cases_failed": failed,
            "pass_rate": pass_rate,
            "min_cases": min_cases,
            "corpus_ready": len(cases) >= min_cases,
            "duration_p50_seconds": statistics.median(durations) if durations else None,
            "duration_p95_seconds": _p95(durations),
            "duration_count": len(durations),
            "tokens_total": sum(tokens) if tokens else None,
            "tokens_count": len(tokens),
            "cost_usd_total": sum(costs) if costs else None,
            "cost_count": len(costs),
            "baseline_pass_rate": float(baseline_rate) if baseline_rate is not None else None,
            "regression_detected": regression,
        },
        "policy": {"descriptive_only": True, "no_network_export": True,
                   "does_not_override_admission": True,
                   "insufficient_corpus_is_not_pass": True},
    }


def run_corpus(fixtures: Path, command: list[str], *, timeout: int,
               base_sha: str, head_sha: str, min_cases: int = 20,
               configuration: Any = None,
               baseline: dict[str, Any] | None = None) -> dict[str, Any]:
    if not SHA_RE.fullmatch(base_sha) or not SHA_RE.fullmatch(head_sha):
        raise ValueError("base_sha and head_sha must be full hexadecimal SHAs")
    if not command:
        raise ValueError("worker command is required")
    meta_report = meta_test.run_suite(fixtures, command, timeout, base_sha, head_sha)
    report = summarize(meta_report, min_cases=min_cases, baseline=baseline)
    report["base_sha"] = base_sha
    report["head_sha"] = head_sha
    report["configuration_digest"] = configuration_digest(command, configuration)
    report["cases"] = meta_report.get("cases", [])
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixtures", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--base-sha", required=True)
    parser.add_argument("--head-sha", required=True)
    parser.add_argument("--timeout", type=int, default=900)
    parser.add_argument("--min-cases", type=int, default=20)
    parser.add_argument("--configuration", type=Path)
    parser.add_argument("--baseline", type=Path)
    parser.add_argument("--command", nargs=argparse.REMAINDER, required=True)
    args = parser.parse_args()
    command = list(args.command)
    if command[:1] == ["--"]:
        command = command[1:]
    try:
        configuration = json.loads(args.configuration.read_text(encoding="utf-8")) if args.configuration else None
        baseline = json.loads(args.baseline.read_text(encoding="utf-8")) if args.baseline else None
        report = run_corpus(args.fixtures.resolve(), command, timeout=args.timeout,
                            base_sha=args.base_sha, head_sha=args.head_sha,
                            min_cases=args.min_cases, configuration=configuration,
                            baseline=baseline)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    except (OSError, TypeError, ValueError, UnicodeError, json.JSONDecodeError) as exc:
        print(f"ERROR: agent eval corpus failed: {type(exc).__name__}")
        return 2
    print(f"agent_eval_corpus: {report['status']} "
          f"{report['metrics']['cases_passed']}/{report['metrics']['cases_total']} "
          f"ready={report['metrics']['corpus_ready']}")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
