#!/usr/bin/env python3
"""Build deterministic quality metrics from risk and gate evidence.

This is a measurement artifact, not a second admission policy. It reports
evidence completeness, risk/fan-out, observed gate pass rate, integration
duration, and reviewer independence with schema/provenance fields. It never
turns a blocked admission into a green result.

Exit codes:
    0 -- valid scorecard and admission was admitted
    1 -- valid scorecard but admission was blocked
    2 -- invalid or stale inputs
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from admission_gate import SCHEMA_VERSION, evaluate


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def build_scorecard(risk_path: Path, receipts_path: Path, base_sha: str,
                    head_sha: str, integration_path: Path | None = None,
                    ultrareview_path: Path | None = None) -> dict:
    risk = read_json(risk_path)
    receipts = read_json(receipts_path)
    decision = evaluate(risk, receipts, base_sha, head_sha)
    items = receipts.get("gates", [])
    observed_passed = sum(item.get("status") == "pass" for item in items)
    metrics = {
        "required_gate_count": decision["metrics"]["required_count"],
        "passed_gate_count": decision["metrics"]["passed_count"],
        "evidence_completeness": decision["metrics"]["evidence_completeness"],
        "observed_gate_count": len(items),
        "observed_pass_rate": (observed_passed / len(items)) if items else 0.0,
        "risk_trigger_count": len(risk.get("risk_triggers", [])),
        "changed_file_count": len(risk.get("changed_files", [])),
        "affected_module_count": len(risk.get("affected_modules", [])),
    }
    if integration_path is not None:
        integration = read_json(integration_path)
        if integration.get("base_sha") != base_sha or integration.get("head_sha") != head_sha:
            raise ValueError("integration report is for a different commit pair")
        metrics["integration_duration_seconds"] = integration.get("metrics", {}).get(
            "duration_seconds")
        metrics["integration_isolated"] = integration.get("isolated") is True
    if ultrareview_path is not None:
        review = read_json(ultrareview_path)
        if review.get("base_sha") != base_sha or review.get("head_sha") != head_sha:
            raise ValueError("ultrareview report is for a different commit pair")
        metrics["review_independent"] = review.get("independent") is True
        metrics["review_evidence_count"] = len(review.get("evidence", [])) \
            if isinstance(review.get("evidence"), list) else 0
    return {
        "schema_version": SCHEMA_VERSION,
        "scorecard_version": 1,
        "base_sha": base_sha,
        "head_sha": head_sha,
        "admitted": decision["admitted"],
        "quality_band": "green" if decision["admitted"] else "blocked",
        "risk_level": risk.get("risk_level"),
        "blockers": decision["blockers"],
        "metrics": metrics,
        "provenance": {
            "risk_report": str(risk_path),
            "receipts": str(receipts_path),
            "integration_report": str(integration_path) if integration_path else None,
            "ultrareview_report": str(ultrareview_path) if ultrareview_path else None,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--risk", type=Path, required=True)
    parser.add_argument("--receipts", type=Path, required=True)
    parser.add_argument("--integration-report", type=Path)
    parser.add_argument("--ultrareview-report", type=Path)
    parser.add_argument("--base-sha", required=True)
    parser.add_argument("--head-sha", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = build_scorecard(args.risk, args.receipts, args.base_sha,
                                 args.head_sha, args.integration_report,
                                 args.ultrareview_report)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    except (OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print("ERROR: invalid scorecard input: " + type(exc).__name__, flush=True)
        return 2
    print(f"quality_scorecard: band={result['quality_band']} completeness="
          f"{result['metrics']['evidence_completeness']:.3f}")
    return 0 if result["admitted"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
