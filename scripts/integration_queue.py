#!/usr/bin/env python3
"""Run the local integration policy across a stacked open-PR queue.

The queue is grouped by each candidate's declared base branch. Every group is
then delegated to ``local_integration_loop`` in a disposable worktree. This
preserves stacked-PR identity instead of flattening dependent candidates onto
``master``. The command is read-only with respect to GitHub: it may discover
PRs and fetch immutable heads, but never creates, approves, merges, pushes, or
deploys anything.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

try:
    from . import local_integration_loop as loop
except ImportError:  # pragma: no cover
    import local_integration_loop as loop  # type: ignore


SCHEMA_VERSION = 1
QUEUE_VERSION = 1


def discover_all_open(repo_slug: str) -> list[loop.Candidate]:
    """Discover all open PRs once, retaining exact head/base identity."""
    result = subprocess.run(
        ["gh", "pr", "list", "--repo", repo_slug, "--state", "open",
         "--limit", "100", "--json",
         ("number,title,headRefName,headRefOid,url,baseRefName,isCrossRepository,"
          "isDraft,headRepository,headRepositoryOwner")],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    if result.returncode != 0:
        raise RuntimeError("gh could not discover open PRs")
    value = json.loads(result.stdout or "[]")
    if not isinstance(value, list):
        raise ValueError("gh PR list was not a JSON list")
    return [loop._candidate({
        "number": item["number"], "title": item["title"],
        "ref": f"origin/{item['headRefName']}", "head_sha": item["headRefOid"],
        "url": item.get("url"), "base_ref": item.get("baseRefName"),
        "is_cross_repository": item.get("isCrossRepository", False),
        "is_draft": item.get("isDraft", False),
        "head_repository": item.get("headRepository"),
        "head_owner": item.get("headRepositoryOwner"),
    }) for item in value if isinstance(item, dict)]


def group_by_base(candidates: Iterable[loop.Candidate]) -> dict[str, list[loop.Candidate]]:
    groups: dict[str, list[loop.Candidate]] = defaultdict(list)
    for candidate in candidates:
        groups[candidate.base_ref or "master"].append(candidate)
    return {base: sorted(items, key=lambda item: item.number)
            for base, items in sorted(groups.items())}


def local_base_ref(base: str) -> str:
    return base if base.startswith("origin/") else f"origin/{base}"


def unresolved_base_report(base: str, candidates: list[loop.Candidate], exc: Exception) -> dict[str, Any]:
    """Fail closed for one broken base without discarding other base groups."""
    items = [{
        "pr": candidate.number, "title": candidate.title, "url": candidate.url,
        "ref": candidate.ref, "base_ref": candidate.base_ref,
        "fork_pr": candidate.is_cross_repository, "draft": candidate.is_draft,
        "classification": "acute", "risk_level": "high",
        "risk_triggers": ["base-ref-unresolved"],
        "required_gates": loop.blast_radius.required_gates_for("high", ["base-ref-unresolved"]),
        "contact_surfaces": {"harness/policy": ["queue base identity"]},
        "human_review_required": True, "status": "held_for_human",
        "reason": "base_ref_unresolved",
    } for candidate in candidates]
    return {
        "schema_version": loop.SCHEMA_VERSION,
        "local_integration_version": loop.SCHEMA_VERSION,
        "base_ref": local_base_ref(base), "base_sha": None,
        "status": "review_required", "included_prs": [],
        "held_prs": [candidate.number for candidate in candidates],
        "human_review_required": True, "remote_write": False,
        "metrics": {"candidates_total": len(candidates), "included_count": 0,
                     "held_count": len(candidates), "acute_count": len(candidates)},
        "error": type(exc).__name__, "candidates": items,
        "policy": {"local_merge_only": True, "no_remote_merge": True,
                   "credential_env_scrubbed": True, "acute_risk_surfaces_human": True},
    }


def run_queue(repo: Path, candidates: Iterable[loop.Candidate], *, command: tuple[str, ...],
              timeout: int = 900, fetch_missing: bool = False) -> dict[str, Any]:
    groups = group_by_base(candidates)
    reports: list[dict[str, Any]] = []
    for base, items in groups.items():
        try:
            reports.append(loop.integrate(repo, local_base_ref(base), items, command,
                                          timeout, fetch_missing=fetch_missing))
        except (OSError, RuntimeError, TypeError, ValueError) as exc:
            reports.append(unresolved_base_report(base, items, exc))

    all_items = [item for report in reports for item in report.get("candidates", [])]
    included = [item["pr"] for item in all_items if item.get("status") == "included"]
    held = [item["pr"] for item in all_items if item.get("status") == "held_for_human"]
    not_ready = [item["pr"] for item in all_items if item.get("classification") == "not_ready"]
    acute = [item["pr"] for item in all_items if item.get("classification") == "acute"]
    return {
        "schema_version": SCHEMA_VERSION, "integration_queue_version": QUEUE_VERSION,
        "status": "review_required" if held else "routine_survivors_ready",
        "staging_handoff": {"status": "ready_for_staging_gate" if included else "blocked",
                             "reason": "routine survivors available" if included else
                             "no routine survivor passed local integration"},
        "included_prs": included, "held_prs": held,
        "human_review_required": bool(held), "remote_write": False,
        "metrics": {"base_groups": len(reports), "candidates_total": len(all_items),
                    "included_count": len(included), "held_count": len(held),
                    "not_ready_count": len(not_ready), "acute_count": len(acute),
                    "routine_survivor_rate": round(len(included) / len(all_items), 4)
                    if all_items else 0.0,
                    "human_review_rate": round(len(held) / len(all_items), 4)
                    if all_items else 0.0},
        "command": list(command), "base_reports": reports, "candidates": all_items,
        "policy": {"local_merge_only": True, "no_remote_merge": True,
                   "credential_env_scrubbed": True, "acute_risk_surfaces_human": True,
                   "staging_pr_created": False},
    }


def render_markdown(report: dict[str, Any]) -> str:
    metrics = report["metrics"]
    lines = ["# Integration queue → staging handoff", "",
             f"Status: **{report['status']}**; staging: **{report['staging_handoff']['status']}**", "",
             "| Metric | Value |", "|---|---:|"]
    for key in ("base_groups", "candidates_total", "included_count", "held_count",
                "not_ready_count", "acute_count", "routine_survivor_rate", "human_review_rate"):
        lines.append(f"| {key} | {metrics[key]} |")
    lines += ["", "| PR | Base | Classification | Status | Risk | Reason |",
              "|---:|---|---|---|---|---|"]
    for item in report["candidates"]:
        lines.append(f"| {item['pr']} | {item.get('base_ref', '')} | "
                     f"{item.get('classification', '')} | {item['status']} | "
                     f"{item.get('risk_level', '')} | {item.get('reason', '')} |")
    lines += ["", "No remote merge, approval, push, deploy, or staging PR creation is performed by this command.", ""]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--repo-slug")
    source.add_argument("--manifest", type=Path)
    parser.add_argument("--fetch-missing", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, required=True)
    parser.add_argument("--timeout", type=int, default=900)
    parser.add_argument("--command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    try:
        candidates = (loop.load_manifest(args.manifest) if args.manifest
                      else discover_all_open(args.repo_slug))
        report = run_queue(args.repo.resolve(), candidates,
                           command=tuple(args.command or loop.DEFAULT_COMMAND),
                           timeout=args.timeout, fetch_missing=args.fetch_missing)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        args.markdown_output.write_text(render_markdown(report), encoding="utf-8")
    except (OSError, RuntimeError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: integration queue failed: {type(exc).__name__}")
        return 2
    print(f"integration_queue: status={report['status']} included={len(report['included_prs'])} held={len(report['held_prs'])}")
    return 0 if not report["human_review_required"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
