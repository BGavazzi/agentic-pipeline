#!/usr/bin/env python3
"""Build a schema-v1 receipt bundle from independent CI job artifacts.

This adapter only aggregates observed exit/status artifacts. It does not sign
them or make candidate-authored artifacts trustworthy; the final job and its
policy source need protected ownership before this is a security boundary.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

SCHEMA_VERSION = 1


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_status(path: Path, base_sha: str, head_sha: str) -> str:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        if (not isinstance(value, dict) or value.get("schema_version") != 1 or
                value.get("base_sha") != base_sha or value.get("head_sha") != head_sha or
                type(value.get("exit_code")) is not int):
            return "error"
    except (OSError, ValueError, TypeError):
        return "error"
    return "pass" if value["exit_code"] == 0 else "fail"


def build_receipts(risk_path: Path, scan_path: Path, unit_exit_path: Path,
                   base_sha: str, head_sha: str,
                   integration_path: Path | None = None,
                   ultrareview_path: Path | None = None,
                   policy_path: Path | None = None,
                   infra_path: Path | None = None,
                   visual_path: Path | None = None,
                   meta_test_path: Path | None = None,
                   intent_path: Path | None = None) -> dict:
    risk = read_json(risk_path)
    scan = read_json(scan_path)
    if risk.get("base_sha") != base_sha or risk.get("head_sha") != head_sha:
        raise ValueError("risk report is for a different commit pair")
    if scan.get("base_sha") != base_sha or scan.get("head_sha") != head_sha:
        raise ValueError("scan report is for a different commit pair")

    integration = None
    if integration_path is not None:
        integration = read_json(integration_path)
        if integration.get("base_sha") != base_sha or integration.get("head_sha") != head_sha:
            raise ValueError("integration report is for a different commit pair")

    ultrareview = None
    if ultrareview_path is not None:
        ultrareview = read_json(ultrareview_path)
        if ultrareview.get("schema_version") != 1 \
                or ultrareview.get("gate") != "ultrareview":
            raise ValueError("invalid ultrareview receipt")
        if ultrareview.get("base_sha") != base_sha or ultrareview.get("head_sha") != head_sha:
            raise ValueError("ultrareview report is for a different commit pair")

    policy = None
    if policy_path is not None:
        policy = read_json(policy_path)
        if policy.get("schema_version") != 1 or policy.get("gate") != "policy":
            raise ValueError("invalid policy integrity receipt")
        if policy.get("base_sha") != base_sha or policy.get("head_sha") != head_sha:
            raise ValueError("policy report is for a different commit pair")

    infra = None
    if infra_path is not None:
        infra = read_json(infra_path)
        if infra.get("schema_version") != 1 or infra.get("gate") != "infra-dry-run":
            raise ValueError("invalid infra dry-run receipt")
        if infra.get("base_sha") != base_sha or infra.get("head_sha") != head_sha:
            raise ValueError("infra report is for a different commit pair")

    visual = None
    if visual_path is not None:
        visual = read_json(visual_path)
        if visual.get("schema_version") != 1 or visual.get("gate") != "visual":
            raise ValueError("invalid visual receipt")
        _require_producer(visual, "visual-producer")
        if visual.get("base_sha") != base_sha or visual.get("head_sha") != head_sha:
            raise ValueError("visual report is for a different commit pair")

    meta_test = None
    if meta_test_path is not None:
        meta_test = read_json(meta_test_path)
        if meta_test.get("schema_version") != 1 or meta_test.get("gate") != "meta-test":
            raise ValueError("invalid meta-test receipt")
        if meta_test.get("base_sha") != base_sha or meta_test.get("head_sha") != head_sha:
            raise ValueError("meta-test report is for a different commit pair")

    intent = None
    if intent_path is not None:
        intent = read_json(intent_path)
        if (intent.get("schema_version") != 1 or
                intent.get("intent_version") != 1 or
                intent.get("base_sha") != base_sha or intent.get("head_sha") != head_sha or
                type(intent.get("eligible")) is not bool or
                not isinstance(intent.get("blockers"), list)):
            raise ValueError("invalid intent report")

    statuses = {
        "unit": test_status(unit_exit_path, base_sha, head_sha),
        "sast": scan.get("tool_status", {}).get("semgrep", {}).get("status", "error"),
        "sca": scan.get("tool_status", {}).get("trivy", {}).get("status", "error"),
        "secrets": scan.get("tool_status", {}).get("gitleaks", {}).get("status", "error"),
    }
    statuses = {name: ("pass" if status == "ok" else status)
                for name, status in statuses.items()}
    # Execution success is not a security verdict. Unknown/contradictory
    # aggregate evidence must veto every scanner receipt conservatively.
    verdict = scan.get("verdict")
    findings = scan.get("blocking_findings")
    if verdict != "pass" or not isinstance(findings, list) or findings:
        status = "fail" if verdict == "block" or findings else "error"
        for name in ("sast", "sca", "secrets"):
            statuses[name] = status
    if integration is not None:
        statuses["integration"] = integration.get("status", "error")
        if statuses["integration"] not in {"pass", "fail", "error"}:
            statuses["integration"] = "error"
    if ultrareview is not None:
        statuses["ultrareview"] = ultrareview.get("status", "error")
        if statuses["ultrareview"] not in {"pass", "fail", "error"}:
            statuses["ultrareview"] = "error"
    statuses["policy"] = policy.get("status", "error") if policy is not None else "error"
    if statuses["policy"] == "review_required":
        statuses["policy"] = "fail"
    if infra is not None and infra.get("status") != "not_applicable":
        statuses["infra-dry-run"] = infra.get("status", "error")
        if statuses["infra-dry-run"] not in {"pass", "fail", "error"}:
            statuses["infra-dry-run"] = "error"
    if visual is not None:
        statuses["visual"] = visual.get("status", "error")
        if statuses["visual"] not in {"pass", "fail", "error"}:
            statuses["visual"] = "error"
    if meta_test is not None:
        statuses["meta-test"] = meta_test.get("status", "error")
        if statuses["meta-test"] not in {"pass", "fail", "error"}:
            statuses["meta-test"] = "error"
    if intent is not None:
        statuses["intent"] = "pass" if intent["eligible"] and not intent["blockers"] else "fail"
    elif "intent" in risk.get("required_gates", []):
        # Preserve an explicit fail-closed receipt when a consequential risk
        # report requires intent but the producer did not emit an artifact.
        statuses["intent"] = "error"
    evidence = {"risk_report": str(risk_path), "scan_report": str(scan_path),
                "unit_exit": str(unit_exit_path)}
    if integration_path is not None:
        evidence["integration_report"] = str(integration_path)
    if ultrareview_path is not None:
        evidence["ultrareview_report"] = str(ultrareview_path)
    if policy_path is not None:
        evidence["policy_report"] = str(policy_path)
    if infra_path is not None:
        evidence["infra_report"] = str(infra_path)
    if visual_path is not None:
        evidence["visual_report"] = str(visual_path)
    if meta_test_path is not None:
        evidence["meta_test_report"] = str(meta_test_path)
    if intent_path is not None:
        evidence["intent_report"] = str(intent_path)
    elif "intent" in risk.get("required_gates", []):
        evidence["intent_report"] = None
    return {"schema_version": SCHEMA_VERSION, "base_sha": base_sha,
            "head_sha": head_sha,
            "gates": [{"gate": name, "status": status} for name, status in sorted(statuses.items())],
            "evidence": evidence}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--risk", type=Path, required=True)
    parser.add_argument("--scan", type=Path, required=True)
    parser.add_argument("--unit-exit", type=Path, required=True)
    parser.add_argument("--integration-report", type=Path)
    parser.add_argument("--ultrareview-report", type=Path)
    parser.add_argument("--policy-report", type=Path, required=True)
    parser.add_argument("--infra-report", type=Path)
    parser.add_argument("--visual-report", type=Path)
    parser.add_argument("--meta-test-report", type=Path)
    parser.add_argument("--intent-report", type=Path)
    parser.add_argument("--base-sha", required=True)
    parser.add_argument("--head-sha", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = build_receipts(args.risk, args.scan, args.unit_exit,
                                args.base_sha, args.head_sha,
                                args.integration_report, args.ultrareview_report,
                                args.policy_report, args.infra_report, args.visual_report,
                                args.meta_test_report, args.intent_report)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        print("ERROR: could not build receipt bundle", flush=True)
        return 2
    print(f"receipt bundle: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
