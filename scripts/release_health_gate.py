#!/usr/bin/env python3
"""Validate post-deploy health and rollback-plan evidence.

The gate validates evidence shape, identity and coverage only. It never runs a
rollback command, treats a candidate-supplied report as trusted by itself, or
claims that a deployment is healthy without a protected producer.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
SHA_RE = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")
NAME_RE = re.compile(r"^\S{1,120}$")


def _sha(value: Any, label: str) -> None:
    if not isinstance(value, str) or not SHA_RE.fullmatch(value):
        raise ValueError(f"{label} must be a full hexadecimal commit SHA")


def _health(value: dict[str, Any], candidate_sha: str, environment: str) -> list[str]:
    if value.get("schema_version") != SCHEMA_VERSION or value.get("health_version") != 1:
        raise ValueError("unsupported health evidence schema")
    _sha(value.get("commit_sha"), "health commit_sha")
    if value["commit_sha"] != candidate_sha:
        raise ValueError("health evidence is for a different commit")
    if value.get("environment") != environment:
        raise ValueError("health evidence is for a different environment")
    checks = value.get("checks")
    if not isinstance(checks, list) or not checks:
        raise ValueError("health checks are required")
    names: set[str] = set()
    failures: list[str] = []
    for check in checks:
        if not isinstance(check, dict) or not isinstance(check.get("name"), str) \
                or not NAME_RE.fullmatch(check["name"]):
            raise ValueError("health check name is invalid")
        if check["name"] in names:
            raise ValueError("duplicate health check")
        names.add(check["name"])
        if check.get("status") != "pass":
            failures.append(check["name"])
    if value.get("status") not in {"pass", "fail"}:
        raise ValueError("health status is invalid")
    if value["status"] == "fail":
        failures.append("health-status")
    return sorted(set(failures))


def _rollback(value: dict[str, Any], candidate_sha: str, environment: str) -> None:
    if value.get("schema_version") != SCHEMA_VERSION or value.get("rollback_version") != 1:
        raise ValueError("unsupported rollback schema")
    _sha(value.get("target_sha"), "rollback target_sha")
    if value["target_sha"] == candidate_sha:
        raise ValueError("rollback target must differ from candidate")
    if value.get("environment") != environment:
        raise ValueError("rollback plan is for a different environment")
    for field in ("owner", "runbook"):
        if not isinstance(value.get(field), str) or not value[field].strip() or len(value[field]) > 500:
            raise ValueError(f"rollback {field} is required")
    if value.get("dry_run_verified") is not True:
        raise ValueError("rollback dry_run_verified must be true")


def evaluate(health: dict[str, Any], rollback: dict[str, Any], candidate_sha: str,
             environment: str) -> dict[str, Any]:
    _sha(candidate_sha, "candidate_sha")
    if not isinstance(environment, str) or not environment or not NAME_RE.fullmatch(environment):
        raise ValueError("environment is invalid")
    failures = _health(health, candidate_sha, environment)
    _rollback(rollback, candidate_sha, environment)
    return {"schema_version": SCHEMA_VERSION, "release_health_gate_version": 1,
            "status": "pass" if not failures else "block",
            "candidate_sha": candidate_sha, "environment": environment,
            "health_failures": failures, "rollback_plan_valid": True,
            "trusted_producer_observed": False, "command_execution": False,
            "admission_authority": False}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--health", type=Path, required=True)
    parser.add_argument("--rollback", type=Path, required=True)
    parser.add_argument("--candidate-sha", required=True)
    parser.add_argument("--environment", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        health = json.loads(args.health.read_text(encoding="utf-8"))
        rollback = json.loads(args.rollback.read_text(encoding="utf-8"))
        if not isinstance(health, dict) or not isinstance(rollback, dict):
            raise ValueError("evidence must be JSON objects")
        report = evaluate(health, rollback, args.candidate_sha, args.environment)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    except (OSError, TypeError, ValueError, UnicodeError, json.JSONDecodeError) as exc:
        print(f"ERROR: release health gate failed: {type(exc).__name__}")
        return 2
    print(f"release_health_gate: status={report['status']} command_execution=false")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
