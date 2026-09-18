#!/usr/bin/env python3
"""Measure agentic CI/CD capability coverage from repository evidence.

This deterministic maturity report is descriptive telemetry, not an admission
controller. Repository files can prove that a contract exists, but cannot prove
that GitHub rules, signing keys, reviewer identities, runner teardown, or
deployment systems are configured safely.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
AUDIT_VERSION = 1


def _capability(capability_id: str, title: str, tier: str, *, implementation=(),
                tests=(), ci=(), docs=(), external=(), note="") -> dict[str, Any]:
    return {"id": capability_id, "title": title, "tier": tier,
            "implementation": list(implementation), "tests": list(tests),
            "ci": list(ci), "docs": list(docs), "external": list(external),
            "note": note}


CAPABILITIES: tuple[dict[str, Any], ...] = (
    _capability("doctrine-closure", "Constitution, task schema and closure law", "foundation",
                implementation=("AGENTS.md", "scripts/validate_task.py", "scripts/validate_closure.py"),
                tests=("tests/test_validate_task.py", "tests/test_validate_closure.py"),
                docs=(".docs/tasks/000-template.md",)),
    _capability("risk-blast-radius", "Deterministic risk and blast-radius classification", "correctness",
                implementation=("scripts/blast_radius.py",), tests=("tests/test_blast_radius.py",),
                ci=(".github/workflows/ci.yml",)),
    _capability("static-security-scans", "SAST, SCA and secret scanning", "security",
                implementation=("scripts/scan_gate.py",),
                tests=("tests/test_scan_gate.py", "tests/test_live_scanners.py"),
                ci=(".github/workflows/ci.yml",)),
    _capability("receipt-admission", "Versioned receipts and deterministic admission", "trust",
                implementation=("scripts/ci_receipts.py", "scripts/admission_gate.py", "scripts/quality_scorecard.py"),
                tests=("tests/test_ci_receipts.py", "tests/test_admission_gate.py"),
                ci=(".github/workflows/ci.yml",)),
    _capability("clean-room-integration", "Exact-tree integration execution", "correctness",
                implementation=("scripts/integration_gate.py",), tests=("tests/test_integration_gate.py",),
                ci=(".github/workflows/ci.yml",),
                note="The contract exists; trusted activation is external."),
    _capability("test-impact-analysis", "Conservative test-impact selection", "scale",
                implementation=("scripts/test_impact.py", "scripts/impact_runner.py", "scripts/impact_promotion.py"),
                tests=("tests/test_test_impact.py", "tests/test_impact_runner.py"),
                ci=(".github/workflows/ci.yml", "scripts/impact_benchmark.py"),
                note="A production listener/selector history service is not inferred."),
    _capability("agent-behavior-evals", "Fixture-based agent/skill evaluation", "agentic",
                implementation=("scripts/meta_test.py", "scripts/meta_test_dispatch.py", "scripts/harness_selftest.py"),
                tests=("tests/test_meta_test.py", "tests/test_meta_test_dispatch.py", "tests/test_harness_selftest.py"),
                ci=(".github/workflows/ci.yml",), docs=("tests/skills",)),
    _capability("worker-boundary", "Disposable worker boundary and lifecycle evidence", "security",
                implementation=("scripts/worker_boundary.py", "scripts/worker_preflight.py", "scripts/worker_supervisor.py"),
                tests=("tests/test_worker_boundary.py", "tests/test_worker_preflight.py", "tests/test_worker_supervisor.py"),
                ci=(".github/workflows/ci.yml",), docs=(".docs/runbooks/homelab-runner-pool.md",),
                external=("live ephemeral/JIT worker observation", "host-level teardown observer"),
                note="Static evidence cannot prove the homelab was provisioned safely."),
    _capability("independent-review", "Independent review and trusted policy evidence", "trust",
                implementation=("scripts/ultrareview_receipt.py", "scripts/ultrareview_runner.py", "scripts/trusted_policy.py"),
                tests=("tests/test_ultrareview_receipt.py", "tests/test_ultrareview_runner.py", "tests/test_trusted_policy.py"),
                ci=(".github/workflows/early-review.yml", ".github/workflows/trusted-policy.yml"),
                external=("protected producer identity", "independent reviewer identity", "immutable policy pin"),
                note="The repository deliberately blocks until these facts exist."),
    _capability("visual-regression", "Browser/visual evidence with protected baselines", "ux",
                implementation=("scripts/visual_receipt.py",), tests=("tests/test_visual_receipt.py",),
                docs=(".docs/tasks/0016-feat-visual-regression-receipt.md",),
                external=("protected Playwright producer", "durable baseline store", "browser image pin"),
                note="The core receipt contract is present; a protected consumer is external."),
    _capability("test-result-history", "Scalable result listener and selector history", "scale",
                implementation=("scripts/receipt_journal.py",), tests=("tests/test_receipt_journal.py",),
                docs=(".docs/tasks/0041-feat-receipt-journal.md",),
                external=("per-test result history", "staleness/lag SLO", "horizontally scalable listener"),
                note="Receipt journaling is not yet a per-test impact-history service."),
    _capability("artifact-provenance-sbom", "Signed artifact provenance and SBOM verification", "supply-chain",
                external=("SLSA-compatible provenance", "artifact attestation", "SBOM generation and verification"),
                note="Scanner reports are not release provenance."),
    _capability("hermetic-reproducible-builds", "Pinned, hermetic and reproducible execution", "correctness",
                implementation=("scripts/integration_gate.py",),
                external=("pinned dependency lock/constraints", "reproducible toolchain image", "network policy"),
                note="Archive isolation does not make installs or tools hermetic."),
    _capability("flaky-test-governance", "Flake detection, quarantine and recovery", "correctness",
                external=("flake history", "quarantine policy", "re-enable/remediation workflow"),
                note="Retries without a quarantine ledger would hide regressions."),
    _capability("ci-observability", "CI/CD telemetry, queue and SLO visibility", "operations",
                implementation=("scripts/quality_metrics_dashboard.py", "scripts/receipt_journal.py"),
                tests=("tests/test_quality_metrics_dashboard.py", "tests/test_receipt_journal.py"),
                docs=(".docs/tasks/0041-feat-receipt-journal.md",),
                external=("OpenTelemetry CI/CD export", "queue-age/lag alerts", "worker-pool SLO dashboard"),
                note="Local reports exist; external telemetry and alerting are not assumed."),
    _capability("merge-release-safety", "Merge queue, deployment verification and rollback", "operations",
                external=("merge_group checks", "post-deploy health gate", "automated rollback"),
                note="Consumer deployment boundaries still need an explicit integration."),
)


def _exists(repo: Path, relative: str) -> bool:
    return (repo / relative).exists()


def _evidence(repo: Path, values: list[str]) -> dict[str, bool]:
    evidence: dict[str, bool] = {}
    for value in values:
        if "::" not in value:
            evidence[value] = _exists(repo, value)
            continue
        relative, pattern = value.split("::", 1)
        path = repo / relative
        try:
            evidence[value] = path.is_file() and re.search(
                pattern, path.read_text(encoding="utf-8"), re.MULTILINE) is not None
        except (OSError, UnicodeError, re.error):
            evidence[value] = False
    return evidence


def _status(capability: dict[str, Any], evidence: dict[str, Any]) -> str:
    impl = capability["implementation"]
    tests = capability["tests"]
    ci = capability["ci"]
    docs = capability["docs"]
    impl_ok = bool(impl) and all(evidence["implementation"].values())
    tests_ok = bool(tests) and all(evidence["tests"].values())
    ci_ok = bool(ci) and all(evidence["ci"].values())
    docs_ok = bool(docs) and all(evidence["docs"].values())
    if impl_ok and tests_ok and ci_ok and not capability["external"]:
        return "pass"
    if impl_ok and tests_ok and (ci_ok or docs_ok or capability["external"]):
        return "partial" if capability["external"] else "pass"
    if impl_ok or tests_ok or ci_ok or docs_ok:
        return "partial"
    return "missing"


def audit(repo: Path) -> dict[str, Any]:
    repo = repo.resolve()
    rows = []
    for capability in CAPABILITIES:
        evidence = {"implementation": _evidence(repo, capability["implementation"]),
                    "tests": _evidence(repo, capability["tests"]),
                    "ci": _evidence(repo, capability["ci"]),
                    "docs": _evidence(repo, capability["docs"]),
                    "external": list(capability["external"])}
        status = _status(capability, evidence)
        rows.append({"id": capability["id"], "title": capability["title"],
                     "tier": capability["tier"], "status": status,
                     "score": {"pass": 2, "partial": 1, "missing": 0}[status],
                     "evidence": evidence, "note": capability["note"]})
    counts = {status: sum(row["status"] == status for row in rows)
              for status in ("pass", "partial", "missing")}
    maximum = len(rows) * 2
    achieved = sum(row["score"] for row in rows)
    critical_missing = [row["id"] for row in rows if row["status"] == "missing"
                       and row["tier"] in {"security", "trust", "supply-chain"}]
    return {"schema_version": SCHEMA_VERSION, "audit_version": AUDIT_VERSION,
            "audit": "sota-agentic-harness", "repository": str(repo),
            "scope": "static repository evidence; external activation is never inferred",
            "metrics": {"capabilities_total": len(rows), "pass_count": counts["pass"],
                        "partial_count": counts["partial"], "missing_count": counts["missing"],
                        "score_points": achieved, "max_score_points": maximum,
                        "coverage_ratio": round(achieved / maximum, 4) if maximum else 0.0,
                        "critical_missing_count": len(critical_missing)},
            "capabilities": rows,
            "limitations": ["A passing static audit does not prove runtime authenticity or security.",
                            "External controls are obligations, not simulated passes.",
                            "This report must not replace admission_gate.py."]}


def markdown(report: dict[str, Any]) -> str:
    metrics = report["metrics"]
    lines = ["# SOTA agentic harness capability audit", "",
             "Static, deterministic evidence report. This is not an admission decision.", "",
             f"**Coverage:** {metrics['score_points']}/{metrics['max_score_points']} points "
             f"({metrics['coverage_ratio']:.1%})  ",
             f"**Pass:** {metrics['pass_count']} · **Partial:** {metrics['partial_count']} · "
             f"**Missing:** {metrics['missing_count']}", "",
             "| Capability | Tier | Status | Score |", "|---|---|---|---:|"]
    for row in report["capabilities"]:
        lines.append(f"| {row['title']} (`{row['id']}`) | {row['tier']} | "
                     f"{row['status']} | {row['score']}/2 |")
    lines.extend(["", "## Boundary", "",
                  "No credit is given for signed provenance, protected reviewer "
                  "identity, ephemeral worker teardown, merge-queue activation, "
                  "or deployment rollback without repository evidence. Runtime "
                  "activation still needs independent operational evidence."])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path)
    args = parser.parse_args()
    try:
        report = audit(args.repo)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        if args.markdown_output:
            args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
            args.markdown_output.write_text(markdown(report), encoding="utf-8")
    except (OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: SOTA audit failed: {type(exc).__name__}")
        return 2
    print(f"sota_audit: {report['metrics']['score_points']}/{report['metrics']['max_score_points']} "
          f"coverage={report['metrics']['coverage_ratio']:.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
