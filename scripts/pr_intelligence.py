#!/usr/bin/env python3
"""Build a deterministic, commit-bound human-review summary for a change.

This is an observability and routing artifact, not a replacement admission
policy.  It combines the already-issued risk report with diff shape and any
available gate/impact receipts, then emits JSON plus Markdown suitable for a
GitHub job summary or an idempotent PR comment.

The summary deliberately separates:

* hard evidence (risk report, gate statuses, exact SHA pair),
* derived measurements (churn, contact surfaces, test ratios), and
* advisory HITL signals (when a human should inspect the change earlier).

No advisory score can turn a blocked admission green, and missing optional
evidence is reported as missing rather than inferred to be successful.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1

# Ordered from most specific to broadest.  A file can contribute to several
# surfaces: a workflow that also changes a policy script should show both.
SURFACE_RULES: tuple[tuple[str, str], ...] = (
    (r"^\.github/workflows/", "CI/workflow"),
    (r"^scripts/(?:.*(?:gate|receipt|policy|preflight|supervisor|impact|meta|scan|blast|staging).*)\.py$", "harness/policy"),
    (r"^\.claude/skills/", "agent behavior"),
    (r"(?:^|/)(?:auth|rbac|permission|security|secrets?)(?:/|[_.-])", "security/identity"),
    (r"(?:^|/)(?:migrations?|schema|.*\.sql$)", "data/schema"),
    (r"(?:^|/)(?:terraform|ansible|playbooks?|helm|charts?|fleet|rancher|infra)(?:/|[_.-])", "infrastructure"),
    (r"(?:package-lock\.json|pnpm-lock\.yaml|yarn\.lock|poetry\.lock|uv\.lock|requirements[^/]*\.txt|go\.sum|Cargo\.lock)$", "dependencies"),
    (r"(?:^|/)(?:api|openapi|graphql|routes?|handlers?)(?:/|[_.-])", "API/contracts"),
    (r"(?:^|/)(?:components?|pages?|stories?|storybook|frontend|ui|web|playwright)(?:/|[_.-])", "UI/visual"),
    (r"(?:^|/)(?:tests?|__tests__|specs?)(?:/|[_.-])|(?:^|/)test_[^/]+|\.test\.[^.]+$|\.spec\.[^.]+$", "tests"),
    (r"^(?:\.docs/|\.agents/)|(?:^|/)(?:docs?|README|CHANGELOG|AGENTS)(?:/|$|\.)", "documentation/governance"),
)


def read_json(path: Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=repo, capture_output=True, text=True,
        encoding="utf-8", errors="replace",
    )
    if result.returncode != 0:
        raise ValueError(f"git command failed: {' '.join(args)}")
    return result.stdout


def diff_stats(repo: Path, base_sha: str, head_sha: str) -> dict[str, Any]:
    raw = git(repo, "diff", "--numstat", f"{base_sha}...{head_sha}")
    additions = deletions = 0
    binary_files = 0
    file_stats: list[dict[str, Any]] = []
    for line in raw.splitlines():
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        added_raw, deleted_raw, path = parts[0], parts[1], "\t".join(parts[2:])
        if added_raw == "-" or deleted_raw == "-":
            binary_files += 1
            added = deleted = 0
        else:
            added, deleted = int(added_raw), int(deleted_raw)
            additions += added
            deletions += deleted
        file_stats.append({"path": path, "additions": added, "deletions": deleted})
    return {
        "additions": additions,
        "deletions": deletions,
        "churn": additions + deletions,
        "changed_file_count": len(file_stats),
        "binary_file_count": binary_files,
        "file_stats": file_stats,
    }


def changed_paths(risk: dict[str, Any]) -> list[str]:
    paths = risk.get("changed_files", [])
    if not isinstance(paths, list) or any(not isinstance(p, str) for p in paths):
        raise ValueError("risk report has invalid changed_files")
    return sorted(set(paths))


def surfaces(paths: list[str]) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for path in paths:
        matched = [label for pattern, label in SURFACE_RULES
                   if re.search(pattern, path, re.IGNORECASE)]
        if not matched:
            matched = ["application/source"]
        for label in matched:
            result.setdefault(label, []).append(path)
    return {label: sorted(files) for label, files in sorted(result.items())}


def gate_metrics(receipts: dict[str, Any] | None, risk: dict[str, Any]) -> dict[str, Any]:
    if receipts is None:
        return {"status": "missing", "observed_count": 0, "passed_count": 0,
                "failed_or_nonpass": [], "missing_required": list(risk.get("required_gates", []))}
    items = receipts.get("gates", [])
    if not isinstance(items, list):
        return {"status": "invalid", "observed_count": 0, "passed_count": 0,
                "failed_or_nonpass": [], "missing_required": list(risk.get("required_gates", []))}
    statuses = {item.get("gate"): item.get("status") for item in items
                if isinstance(item, dict) and isinstance(item.get("gate"), str)}
    required = set(risk.get("required_gates", [])) | {"sast", "sca", "secrets", "policy"}
    nonpass = sorted(f"{name}:{statuses.get(name, 'missing')}" for name in required
                     if statuses.get(name) != "pass")
    return {
        "status": "complete" if not nonpass else "blocked",
        "observed_count": len(statuses),
        "passed_count": sum(value == "pass" for value in statuses.values()),
        "failed_or_nonpass": nonpass,
        "missing_required": sorted(name for name in required if name not in statuses),
        "statuses": dict(sorted(statuses.items())),
    }


def impact_metrics(impact: dict[str, Any] | None, promotion: dict[str, Any] | None) -> dict[str, Any]:
    source = promotion or impact
    if source is None:
        return {"status": "missing"}
    metrics = source.get("metrics", {}) if isinstance(source.get("metrics", {}), dict) else {}
    result = {"status": source.get("status", "unknown")}
    for key in ("available_test_count", "selected_test_count", "selection_ratio",
                "tests_avoided", "precision", "recall", "duration_savings_seconds",
                "duration_savings_ratio"):
        if key in metrics:
            result[key] = metrics[key]
    result["mode"] = source.get("mode", source.get("promotion_mode", "unknown"))
    return result


def human_review(paths: list[str], risk: dict[str, Any], stats: dict[str, Any],
                 gate: dict[str, Any], surfaces_map: dict[str, list[str]],
                 impact: dict[str, Any]) -> dict[str, Any]:
    triggers: list[dict[str, str]] = []
    level = risk.get("risk_level", "unknown")
    if level == "high":
        triggers.append({"severity": "required", "reason": "risk classifier returned high"})
    elif level == "medium":
        triggers.append({"severity": "recommended", "reason": "risk classifier returned medium"})
    for trigger in risk.get("risk_triggers", []):
        if trigger in {"ci-workflow", "gate-script", "pre-commit-config", "agent-skill", "policy"}:
            triggers.append({"severity": "required", "reason": f"protected harness surface changed: {trigger}"})
    if gate.get("failed_or_nonpass"):
        triggers.append({"severity": "required", "reason": "one or more required evidence gates are not pass"})
    if "application/source" in surfaces_map and "tests" not in surfaces_map:
        triggers.append({"severity": "recommended", "reason": "application code changed without a test-file change"})
    if "UI/visual" in surfaces_map and "visual" not in gate.get("statuses", {}):
        triggers.append({"severity": "recommended", "reason": "UI/visual surface changed without visual evidence"})
    if "dependencies" in surfaces_map:
        triggers.append({"severity": "recommended", "reason": "dependency or lockfile surface changed"})
    if "infrastructure" in surfaces_map or "data/schema" in surfaces_map:
        triggers.append({"severity": "required", "reason": "infrastructure or data/schema compatibility needs human inspection"})
    if stats["churn"] >= 400:
        triggers.append({"severity": "recommended", "reason": f"large diff churn ({stats['churn']} lines)"})
    if impact.get("status") in {"missing", "error", "not_applicable"} and "application/source" in surfaces_map:
        triggers.append({"severity": "recommended", "reason": "test-impact evidence is unavailable or not applicable"})

    # Preserve the strongest reason once; duplicate triggers add noise to PRs.
    unique: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in triggers:
        if item["reason"] not in seen:
            unique.append(item)
            seen.add(item["reason"])
    required = any(item["severity"] == "required" for item in unique)
    return {
        "checkpoint": "before integration" if required else ("before staging" if unique else "staging review"),
        "decision": "required_before_staging" if required else ("recommended" if unique else "standard"),
        "triggers": unique,
    }


def build_intelligence(repo: Path, risk_path: Path, base_sha: str, head_sha: str,
                       receipts_path: Path | None = None,
                       impact_path: Path | None = None,
                       promotion_path: Path | None = None) -> dict[str, Any]:
    risk = read_json(risk_path)
    if risk is None or risk.get("base_sha") != base_sha or risk.get("head_sha") != head_sha:
        raise ValueError("risk report is stale or mismatched")
    paths = changed_paths(risk)
    stats = diff_stats(repo, base_sha, head_sha)
    surfaces_map = surfaces(paths)
    test_file_count = len(surfaces_map.get("tests", []))
    source_file_count = len(paths) - test_file_count - len(surfaces_map.get("documentation/governance", []))
    stats["test_file_count"] = test_file_count
    stats["source_file_count"] = max(0, source_file_count)
    stats["test_to_source_file_ratio"] = (test_file_count / source_file_count
                                           if source_file_count else None)
    gate = gate_metrics(read_json(receipts_path), risk)
    impact = impact_metrics(read_json(impact_path), read_json(promotion_path))
    review = human_review(paths, risk, stats, gate, surfaces_map, impact)
    return {
        "schema_version": SCHEMA_VERSION,
        "intelligence_version": 1,
        "base_sha": base_sha,
        "head_sha": head_sha,
        "risk": {
            "level": risk.get("risk_level"),
            "triggers": risk.get("risk_triggers", []),
            "affected_module_count": len(risk.get("affected_modules", [])),
            "required_gate_count": len(risk.get("required_gates", [])),
        },
        "diff": {key: value for key, value in stats.items() if key != "file_stats"},
        "contact_surfaces": {label: {"file_count": len(files), "files": files}
                             for label, files in surfaces_map.items()},
        "gates": gate,
        "test_impact": impact,
        "human_review": review,
        "provenance": {"risk_report": str(risk_path),
                       "receipts": str(receipts_path) if receipts_path else None,
                       "impact_report": str(impact_path) if impact_path else None,
                       "promotion_report": str(promotion_path) if promotion_path else None},
    }


def markdown(report: dict[str, Any]) -> str:
    risk = report["risk"]
    diff = report["diff"]
    gate = report["gates"]
    hitl = report["human_review"]
    impact = report["test_impact"]
    lines = [
        "<!-- agentic-pipeline-pr-intelligence -->",
        "## Agentic quality intelligence",
        "",
        f"**HITL checkpoint:** `{hitl['checkpoint']}`  ",
        f"**Review decision:** `{hitl['decision']}`  ",
        f"**Risk:** `{risk['level']}` ({len(risk['triggers'])} classifier trigger(s))",
        "",
        "| Measurement | Value |",
        "|---|---:|",
        f"| Changed files | {diff['changed_file_count'] if 'changed_file_count' in diff else 'n/a'} |",
        f"| Diff churn | {diff['churn']} lines (+{diff['additions']} / -{diff['deletions']}) |",
        f"| Affected modules | {risk['affected_module_count']} |",
        f"| Required gates | {risk['required_gate_count']} |",
        f"| Gate evidence | {gate['passed_count']}/{gate['observed_count']} observed pass; `{gate['status']}` |",
        f"| Test/source file ratio | {diff.get('test_to_source_file_ratio', 'n/a')} |",
        f"| Test-impact evidence | `{impact.get('status', 'missing')}` |",
        "",
        "### Why a human may need to look now",
    ]
    triggers = hitl["triggers"]
    lines.extend([f"- **{item['severity']}** — {item['reason']}" for item in triggers] or ["- No elevated deterministic HITL signal."])
    lines += ["", "### Contact surfaces"]
    for label, details in report["contact_surfaces"].items():
        lines.append(f"- **{label}** ({details['file_count']}): " + ", ".join(f"`{path}`" for path in details["files"][:8]) + (" …" if details["file_count"] > 8 else ""))
    if gate.get("failed_or_nonpass"):
        lines += ["", "### Non-pass evidence", ""]
        lines.extend(f"- `{item}`" for item in gate["failed_or_nonpass"])
    lines += ["", f"_Evidence identity: `{report['base_sha'][:12]}...` → `{report['head_sha'][:12]}...`; this summary is advisory and cannot override admission._", ""]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path("."))
    parser.add_argument("--risk", type=Path, required=True)
    parser.add_argument("--receipts", type=Path)
    parser.add_argument("--impact-report", type=Path)
    parser.add_argument("--promotion-report", type=Path)
    parser.add_argument("--base-sha", required=True)
    parser.add_argument("--head-sha", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, required=True)
    args = parser.parse_args()
    try:
        report = build_intelligence(args.repo.resolve(), args.risk, args.base_sha, args.head_sha,
                                    args.receipts, args.impact_report, args.promotion_report)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        args.markdown_output.write_text(markdown(report), encoding="utf-8")
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
        print(f"ERROR: invalid PR intelligence input: {type(exc).__name__}", file=sys.stderr)
        return 2
    print(f"pr-intelligence: decision={report['human_review']['decision']} risk={report['risk']['level']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
