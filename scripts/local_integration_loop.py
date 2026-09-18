#!/usr/bin/env python3
"""Integrate routine PRs locally and bundle only the acute risks for a human.

The loop is intentionally local and bounded:

* candidate PR metadata is read from a manifest or ``gh pr list``;
* refs are resolved into the local object database, never pushed or merged on
  GitHub;
* blast-radius/contact-surface evidence decides whether a candidate is acute;
* routine candidates are merged one at a time in a disposable worktree;
* the supplied argv is executed after each merge without a shell and with
  obvious credential variables removed;
* acute, conflicting and test-failing candidates remain in a review bundle.

This is an integration producer, not an admission override. A survivor bundle
still needs the existing staging/admission/human-review path.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

try:
    from . import blast_radius
    from .pr_intelligence import surfaces
except ImportError:  # pragma: no cover
    import blast_radius  # type: ignore
    from pr_intelligence import surfaces  # type: ignore

SCHEMA_VERSION = 1
FULL_SHA = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")
DEFAULT_COMMAND = (sys.executable, "-m", "pytest", "tests", "-q")
ACUTE_SURFACES = {"security/identity", "data/schema", "infrastructure", "CI/workflow", "harness/policy"}
SECRET_ENV = re.compile(r"(?:TOKEN|SECRET|PASSWORD|PASSWD|CREDENTIAL|PRIVATE_KEY|API_KEY|ACCESS_KEY)", re.I)


@dataclass(frozen=True)
class Candidate:
    number: int
    title: str
    ref: str
    head_sha: str | None = None
    url: str | None = None
    base_ref: str | None = None


def _git(repo: Path, *args: str, check: bool = True) -> str:
    result = subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True,
                            encoding="utf-8", errors="replace")
    if check and result.returncode != 0:
        raise RuntimeError(f"git command failed: {' '.join(args)}: {result.stderr.strip()}")
    return result.stdout.strip()


def _sha(repo: Path, ref: str) -> str:
    value = _git(repo, "rev-parse", "--verify", "--end-of-options", ref + "^{commit}")
    if not FULL_SHA.fullmatch(value):
        raise ValueError(f"ref does not resolve to a full commit: {ref}")
    return value


def _candidate(value: dict[str, Any]) -> Candidate:
    try:
        number = int(value["number"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("candidate number is required") from exc
    if number <= 0:
        raise ValueError("candidate number must be positive")
    title, ref = value.get("title", f"PR #{number}"), value.get("ref") or value.get("head_ref_name")
    if not isinstance(title, str) or not title or len(title) > 500:
        raise ValueError("candidate title is invalid")
    if not isinstance(ref, str) or not ref or any(c in ref for c in "\r\n\x00"):
        raise ValueError("candidate ref is invalid")
    head_sha = value.get("head_sha") or value.get("head_ref_oid")
    if head_sha is not None and (not isinstance(head_sha, str) or not FULL_SHA.fullmatch(head_sha)):
        raise ValueError("candidate head_sha is invalid")
    return Candidate(number, title, ref, head_sha, value.get("url"), value.get("base_ref"))


def load_manifest(path: Path) -> list[Candidate]:
    value = json.loads(path.read_text(encoding="utf-8"))
    raw = value.get("candidates") if isinstance(value, dict) else value
    if not isinstance(raw, list):
        raise ValueError("candidate manifest must be a list or {candidates: list}")
    candidates = [_candidate(item) for item in raw if isinstance(item, dict)]
    if len(candidates) != len(raw):
        raise ValueError("candidate manifest contains a non-object")
    if len({item.number for item in candidates}) != len(candidates):
        raise ValueError("candidate numbers must be unique")
    return sorted(candidates, key=lambda item: item.number)


def discover_open(repo_slug: str, base: str) -> list[Candidate]:
    # Git callers commonly use ``origin/branch`` while GitHub's API expects
    # the branch name itself.  Normalizing here prevents a valid base ref from
    # becoming a silently empty candidate set.
    gh_base = base.removeprefix("origin/")
    result = subprocess.run(
        ["gh", "pr", "list", "--repo", repo_slug, "--base", gh_base, "--state", "open",
         "--limit", "100", "--json", "number,title,headRefName,headRefOid,url,baseRefName"],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    if result.returncode != 0:
        raise RuntimeError("gh could not discover open PRs")
    value = json.loads(result.stdout or "[]")
    if not isinstance(value, list):
        raise ValueError("gh PR list was not a JSON list")
    return [_candidate({"number": item["number"], "title": item["title"],
                        "ref": item["headRefName"], "head_sha": item["headRefOid"],
                        "url": item.get("url"), "base_ref": item.get("baseRefName")})
            for item in value if isinstance(item, dict)]


def resolve_candidate(repo: Path, candidate: Candidate, *, fetch_missing: bool = False) -> str:
    """Resolve a candidate ref without creating a local branch or pushing.

    A manifest normally supplies refs already present in the local object
    database.  Discovery through ``gh`` commonly supplies only a remote PR
    head name, so ``fetch_missing`` may read ``refs/pull/N/head`` from
    ``origin`` into ``FETCH_HEAD``.  This is deliberately opt-in and read-only
    with respect to the remote: it never creates a remote branch, pushes, or
    changes GitHub state.
    """
    try:
        resolved = _sha(repo, candidate.ref)
    except RuntimeError:
        if not fetch_missing:
            raise
        _git(repo, "fetch", "--no-tags", "origin", f"refs/pull/{candidate.number}/head")
        resolved = _sha(repo, "FETCH_HEAD")
    if candidate.head_sha and resolved != candidate.head_sha:
        raise ValueError(f"candidate #{candidate.number} ref moved")
    return resolved


def classify_candidate(repo: Path, base_sha: str, candidate: Candidate,
                       head_sha: str) -> dict[str, Any]:
    changed = [line for line in _git(repo, "diff", "--name-only", f"{base_sha}...{head_sha}").splitlines() if line]
    rules = blast_radius.load_ownership_map(repo)
    affected = blast_radius.ownership_signal(changed, rules)
    affected |= blast_radius.import_grep_signal(repo, changed)
    affected |= blast_radius.cochange_signal(repo, changed)
    affected -= set(changed)
    risk, triggers = blast_radius.classify_risk(changed, affected)
    required = blast_radius.required_gates_for(risk, triggers)
    contact = surfaces(changed)
    acute = risk == "high" or bool(ACUTE_SURFACES & set(contact))
    return {"risk_level": risk, "risk_triggers": sorted(set(triggers)),
            "required_gates": required, "changed_files": sorted(changed),
            "affected_modules": sorted(affected), "contact_surfaces": contact,
            "classification": "acute" if acute else "routine",
            "human_review_required": acute}


def _safe_env() -> dict[str, str]:
    return {key: value for key, value in os.environ.items() if not SECRET_ENV.search(key)}


def _run_command(worktree: Path, command: tuple[str, ...], timeout: int) -> dict[str, Any]:
    started = time.monotonic()
    try:
        result = subprocess.run(list(command), cwd=worktree, env={**_safe_env(), "CI": "1",
                               "PYTHONDONTWRITEBYTECODE": "1", "PYTHONPATH": ""},
                               capture_output=True, text=True, encoding="utf-8",
                               errors="replace", timeout=timeout)
        return {"status": "pass" if result.returncode == 0 else "fail",
                "exit_code": result.returncode,
                "duration_seconds": round(time.monotonic() - started, 3),
                "stdout_bytes": len(result.stdout.encode("utf-8")),
                "stderr_bytes": len(result.stderr.encode("utf-8"))}
    except subprocess.TimeoutExpired:
        return {"status": "error", "exit_code": None,
                "duration_seconds": round(time.monotonic() - started, 3),
                "error": "integration command timed out"}


def _merge_one(worktree: Path, head_sha: str) -> tuple[bool, str | None]:
    result = subprocess.run(["git", "merge", "--no-commit", "--no-ff", head_sha],
                            cwd=worktree, capture_output=True, text=True,
                            encoding="utf-8", errors="replace")
    if result.returncode != 0:
        subprocess.run(["git", "merge", "--abort"], cwd=worktree,
                       capture_output=True, text=True)
        return False, "merge_conflict"
    commit = subprocess.run(["git", "-c", "user.name=agentic-pipeline-local",
                             "-c", "user.email=local@invalid", "commit", "--no-edit",
                             "-m", f"local integration of {head_sha[:12]}"],
                            cwd=worktree, capture_output=True, text=True,
                            encoding="utf-8", errors="replace")
    if commit.returncode != 0:
        return False, "local_commit_failed"
    return True, None


def _clean_worktree(worktree: Path) -> None:
    """Restore the disposable worktree to its current committed tree."""
    _git(worktree, "reset", "--hard", "HEAD")
    _git(worktree, "clean", "-fdx")


def integrate(repo: Path, base_ref: str, candidates: Iterable[Candidate],
              command: tuple[str, ...] = DEFAULT_COMMAND, timeout: int = 900,
              work_root: Path | None = None, fetch_missing: bool = False) -> dict[str, Any]:
    base_sha = _sha(repo, base_ref)
    ordered = list(candidates)
    results: list[dict[str, Any]] = []
    included: list[int] = []
    held: list[int] = []
    with tempfile.TemporaryDirectory(prefix="pipeline-local-integration-",
                                     dir=str(work_root) if work_root else None) as raw:
        worktree = Path(raw)
        _git(repo, "worktree", "add", "--detach", str(worktree), base_sha)
        try:
            for candidate in ordered:
                item: dict[str, Any] = {"pr": candidate.number, "title": candidate.title,
                                        "url": candidate.url, "ref": candidate.ref}
                try:
                    head_sha = resolve_candidate(repo, candidate, fetch_missing=fetch_missing)
                    item["head_sha"] = head_sha
                    item.update(classify_candidate(repo, base_sha, candidate, head_sha))
                    if item["classification"] == "acute":
                        item["status"] = "held_for_human"
                        held.append(candidate.number)
                        results.append(item)
                        continue
                    merged, error = _merge_one(worktree, head_sha)
                    if not merged:
                        _clean_worktree(worktree)
                        item.update({"status": "held_for_human", "reason": error})
                        held.append(candidate.number)
                        results.append(item)
                        continue
                    test = _run_command(worktree, command, timeout)
                    item["test"] = test
                    if test["status"] == "pass":
                        item["status"] = "included"
                        included.append(candidate.number)
                    else:
                        # Revert only the disposable local merge; never touch
                        # a user branch or remote ref.
                        _git(worktree, "reset", "--hard", "HEAD^", check=True)
                        _git(worktree, "clean", "-fdx", check=True)
                        item.update({"status": "held_for_human", "reason": "integration_failed"})
                        held.append(candidate.number)
                    results.append(item)
                except (OSError, RuntimeError, TypeError, ValueError) as exc:
                    item.update({"status": "held_for_human", "reason": type(exc).__name__})
                    held.append(candidate.number)
                    results.append(item)
        finally:
            subprocess.run(["git", "worktree", "remove", "--force", str(worktree)],
                           cwd=repo, capture_output=True, text=True)
    return {"schema_version": SCHEMA_VERSION, "local_integration_version": 1,
            "base_ref": base_ref, "base_sha": base_sha,
            "status": "review_required" if held else "routine_survivors_ready",
            "included_prs": included, "held_prs": held,
            "human_review_required": bool(held), "remote_write": False,
            "metrics": {"candidates_total": len(ordered), "included_count": len(included),
                        "held_count": len(held), "acute_count": sum(
                            item.get("classification") == "acute" for item in results)},
            "command": list(command), "fetch_missing": fetch_missing,
            "candidates": results,
            "policy": {"local_merge_only": True, "no_remote_merge": True,
                       "credential_env_scrubbed": True,
                       "acute_risk_surfaces_human": True}}


def markdown(report: dict[str, Any]) -> str:
    lines = ["# Local integration bundle", "",
             f"Status: **{report['status']}**; base: `{report['base_sha'][:12]}...`",
             f"Included routine PRs: **{report['included_prs']}**; held for human: **{report['held_prs']}**", "",
             "| PR | Classification | Status | Risk | Reason |", "|---:|---|---|---|---|"]
    for item in report["candidates"]:
        lines.append(f"| {item['pr']} | {item.get('classification', 'unknown')} | {item['status']} | "
                     f"{item.get('risk_level', 'unknown')} | {item.get('reason', '')} |")
    lines += ["", "This bundle was produced by disposable local merges. It never merges, pushes, approves or deploys remotely.", ""]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--base", required=True)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--repo-slug", help="use gh pr list when --manifest is omitted")
    parser.add_argument("--fetch-missing", action="store_true",
                        help="read missing same-repository PR heads via origin refs/pull/N/head")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, required=True)
    parser.add_argument("--timeout", type=int, default=900)
    parser.add_argument("--command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    try:
        if not args.manifest and not args.repo_slug:
            raise ValueError("--repo-slug is required when --manifest is omitted")
        candidates = load_manifest(args.manifest) if args.manifest else discover_open(args.repo_slug, args.base)
        report = integrate(args.repo.resolve(), args.base, candidates,
                           tuple(args.command or DEFAULT_COMMAND), args.timeout,
                           fetch_missing=args.fetch_missing)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        args.markdown_output.write_text(markdown(report), encoding="utf-8")
    except (OSError, RuntimeError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: local integration loop failed: {type(exc).__name__}")
        return 2
    print(f"local_integration_loop: status={report['status']} included={len(report['included_prs'])} held={len(report['held_prs'])}")
    return 0 if not report["human_review_required"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
