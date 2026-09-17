#!/usr/bin/env python3
"""Decide whether an agent-produced candidate is eligible for staging review.

This is the handoff between autonomous integration and human review. It does
not create or merge a pull request. It validates that the candidate's quality
scorecard is admitted, that the candidate survived the isolated integration
producer, and that every report names the exact same base/head commit pair.
The result is a versioned, machine-readable receipt that a repository adapter
may use to open a staging PR.

Usage:
    python scripts/staging_gate.py --scorecard scorecard.json \
        --integration-report integration.json --base-sha SHA --head-sha SHA \
        --output .docs/staging-reports/task.json

Exit codes:
    0 -- eligible for staging review
    1 -- valid evidence, but candidate is blocked
    2 -- invalid or stale evidence
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

SCHEMA_VERSION = 1
STAGING_GATE_VERSION = 1


def read_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("report must be a JSON object")
    return value


def _validate_sha(value: str, label: str) -> None:
    if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", value):
        raise ValueError(f"{label} must be a full hexadecimal commit SHA")


def evaluate(scorecard: dict, integration: dict, base_sha: str, head_sha: str,
             repository: str | None = None) -> dict:
    """Return a fail-closed staging eligibility decision."""
    _validate_sha(base_sha, "base_sha")
    _validate_sha(head_sha, "head_sha")
    for label, report in (("scorecard", scorecard), ("integration", integration)):
        if report.get("base_sha") != base_sha or report.get("head_sha") != head_sha:
            raise ValueError(f"{label} report is for a different commit pair")
    if scorecard.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("unsupported scorecard schema version")
    if scorecard.get("scorecard_version") != 1:
        raise ValueError("unsupported scorecard version")
    if integration.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("unsupported integration schema version")

    blockers: dict[str, str] = {}
    if scorecard.get("admitted") is not True:
        blockers["admission"] = "scorecard_not_admitted"
    if scorecard.get("quality_band") != "green":
        blockers["quality_band"] = str(scorecard.get("quality_band", "missing"))
    if integration.get("status") != "pass":
        blockers["integration"] = str(integration.get("status", "missing"))
    if integration.get("isolated") is not True:
        blockers["integration_isolation"] = "not_isolated"
    if integration.get("integration_mode") != "base-head-merge":
        blockers["integration_mode"] = "exact base/head merge was not tested"
    if not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", str(integration.get("executed_tree", ""))):
        blockers["executed_tree"] = "missing"

    score_metrics = scorecard.get("metrics")
    if not isinstance(score_metrics, dict):
        raise ValueError("scorecard metrics are missing")
    completeness = score_metrics.get("evidence_completeness")
    if not isinstance(completeness, (int, float)) or not 0 <= completeness <= 1:
        raise ValueError("invalid evidence completeness metric")
    if completeness < 1:
        blockers["evidence_completeness"] = f"{completeness:.3f}"

    integration_metrics = integration.get("metrics")
    if not isinstance(integration_metrics, dict):
        raise ValueError("integration metrics are missing")
    duration = integration_metrics.get("duration_seconds")
    if not isinstance(duration, (int, float)) or duration < 0:
        raise ValueError("invalid integration duration metric")

    return {
        "schema_version": SCHEMA_VERSION,
        "staging_gate_version": STAGING_GATE_VERSION,
        "base_sha": base_sha,
        "head_sha": head_sha,
        "eligible": not blockers,
        "target": "staging-review",
        "repository": repository,
        "blockers": blockers,
        "metrics": {
            "evidence_completeness": completeness,
            "integration_duration_seconds": duration,
            "integration_isolated": integration.get("isolated") is True,
            "risk_level": scorecard.get("risk_level"),
        },
        "provenance": {
            "scorecard": "scorecard",
            "integration": "integration",
            "human_review_required": True,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scorecard", type=Path, required=True)
    parser.add_argument("--integration-report", type=Path, required=True)
    parser.add_argument("--base-sha", required=True)
    parser.add_argument("--head-sha", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repository", required=True)
    args = parser.parse_args()
    try:
        result = evaluate(
            read_json(args.scorecard), read_json(args.integration_report),
            args.base_sha, args.head_sha, args.repository,
        )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    except (OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps({
            "schema_version": SCHEMA_VERSION,
            "staging_gate_version": STAGING_GATE_VERSION,
            "eligible": False,
            "target": "staging-review",
            "error": "invalid_input",
            "error_type": type(exc).__name__,
        }, indent=2) + "\n", encoding="utf-8")
        print("ERROR: invalid staging evidence: " + type(exc).__name__, flush=True)
        return 2
    print(f"staging_gate: eligible={str(result['eligible']).lower()} target=staging-review")
    return 0 if result["eligible"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
