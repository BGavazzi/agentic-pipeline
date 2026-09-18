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
STATE_SCHEMA_VERSION = 1
FULL_SHA = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")
DEFAULT_COMMAND = (sys.executable, "-m", "pytest", "tests", "-q")
ACUTE_SURFACES = {"security/identity", "data/schema", "infrastructure", "CI/workflow", "harness/policy"}
SECRET_ENV = re.compile(r"(?:TOKEN|SECRET|PASSWORD|PASSWD|CREDENTIAL|PRIVATE_KEY|API_KEY|ACCESS_KEY)", re.I)
CONTROL_ENV = re.compile(
    r"^(?:GIT_(?:DIR|WORK_TREE|INDEX_FILE|OBJECT_DIRECTORY|ALTERNATE_OBJECT_DIRECTORIES|CONFIG_.*|SSH_COMMAND)|"
    r"SSH_AUTH_SOCK|DOCKER_HOST|KUBECONFIG|GOOGLE_APPLICATION_CREDENTIALS|"
    r"CLOUDSDK_AUTH_CREDENTIAL_FILE_OVERRIDE|AZURE_CONFIG_DIR)$", re.I)


@dataclass(frozen=True)
class Candidate:
    number: int
    title: str
    ref: str
    head_sha: str | None = None
    url: str | None = None
    base_ref: str | None = None
    is_cross_repository: bool = False
    head_repository: str | None = None
    head_owner: str | None = None


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


def _branch_name(ref: str) -> str:
    """Normalize common local/remote branch spellings for identity checks."""
    if ref.startswith("refs/heads/"):
        ref = ref.removeprefix("refs/heads/")
    return ref.removeprefix("origin/")


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
    cross_repository = value.get("is_cross_repository", value.get("isCrossRepository", False))
    if type(cross_repository) is not bool:
        raise ValueError("candidate cross-repository flag is invalid")
    base_ref = value.get("base_ref")
    if base_ref is not None and (not isinstance(base_ref, str) or not base_ref
                                 or any(c in base_ref for c in "\r\n\x00")):
        raise ValueError("candidate base_ref is invalid")
    return Candidate(number, title, ref, head_sha, value.get("url"), base_ref,
                     cross_repository, value.get("head_repository"), value.get("head_owner"))


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


def load_state(path: Path | None) -> dict[str, Any]:
    """Load loop state; a missing state file means no candidates were seen."""
    if path is None or not path.exists():
        return {"schema_version": STATE_SCHEMA_VERSION, "processed": {}}
    value = json.loads(path.read_text(encoding="utf-8"))
    if (not isinstance(value, dict) or value.get("schema_version") != STATE_SCHEMA_VERSION
            or not isinstance(value.get("processed"), dict)):
        raise ValueError("integration loop state has an unsupported schema")
    return value


def save_state(path: Path | None, state: dict[str, Any]) -> None:
    """Atomically persist local state; this never writes to a remote."""
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def pending_candidates(candidates: Iterable[Candidate], state: dict[str, Any]) -> tuple[list[Candidate], int]:
    """Skip only candidates whose immutable head survived local integration.

    A held candidate is intentionally *not* terminal: unresolved human review
    must remain visible on the next bounded round.
    """
    pending: list[Candidate] = []
    skipped = 0
    processed = state.get("processed", {})
    for candidate in candidates:
        entry = processed.get(str(candidate.number))
        candidate_identity = candidate.head_sha
        if candidate_identity is None and FULL_SHA.fullmatch(candidate.ref):
            candidate_identity = candidate.ref
        if (entry and candidate_identity and entry.get("head_sha") == candidate_identity
                and entry.get("status") == "included"):
            skipped += 1
            continue
        pending.append(candidate)
    return pending, skipped


def discover_open(repo_slug: str, base: str) -> list[Candidate]:
    # Git callers commonly use ``origin/branch`` while GitHub's API expects
    # the branch name itself.  Normalizing here prevents a valid base ref from
    # becoming a silently empty candidate set.
    gh_base = base.removeprefix("origin/")
    result = subprocess.run(
        ["gh", "pr", "list", "--repo", repo_slug, "--base", gh_base, "--state", "open",
         "--limit", "100", "--json",
         "number,title,headRefName,headRefOid,url,baseRefName,isCrossRepository,headRepository,headRepositoryOwner"],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    if result.returncode != 0:
        raise RuntimeError("gh could not discover open PRs")
    value = json.loads(result.stdout or "[]")
    if not isinstance(value, list):
        raise ValueError("gh PR list was not a JSON list")
    return [_candidate({"number": item["number"], "title": item["title"],
                        "ref": item["headRefName"], "head_sha": item["headRefOid"],
                        "url": item.get("url"), "base_ref": item.get("baseRefName"),
                        "is_cross_repository": item.get("isCrossRepository", False),
                        "head_repository": item.get("headRepository"),
                        "head_owner": item.get("headRepositoryOwner")})
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
    return {key: value for key, value in os.environ.items()
            if not SECRET_ENV.search(key) and not CONTROL_ENV.fullmatch(key)}


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
    commit = subprocess.run(["git", "-c", "core.hooksPath=",
                             "-c", "user.name=agentic-pipeline-local",
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
                                        "url": candidate.url, "ref": candidate.ref,
                                        "base_ref": candidate.base_ref,
                                        "fork_pr": candidate.is_cross_repository,
                                        "head_repository": candidate.head_repository,
                                        "head_owner": candidate.head_owner}
                previous_head = ""
                try:
                    if (candidate.base_ref is not None
                            and _branch_name(candidate.base_ref) != _branch_name(base_ref)):
                        item.update({"classification": "acute", "risk_level": "high",
                                     "risk_triggers": ["base-ref-mismatch"],
                                     "required_gates": blast_radius.required_gates_for(
                                         "high", ["base-ref-mismatch"]),
                                     "contact_surfaces": {"harness/policy": ["candidate base identity"]},
                                     "human_review_required": True,
                                     "status": "held_for_human",
                                     "reason": "candidate_base_ref_mismatch"})
                        held.append(candidate.number)
                        results.append(item)
                        continue
                    # Fork code is untrusted until a human explicitly routes
                    # it through the GitHub-hosted lane. Never fetch, merge or
                    # execute a cross-repository head in this local loop.
                    if candidate.is_cross_repository:
                        item.update({"classification": "acute", "risk_level": "high",
                                     "risk_triggers": ["fork-pr"],
                                     "required_gates": blast_radius.required_gates_for(
                                         "high", ["fork-pr"]),
                                     "contact_surfaces": {"security/identity": ["cross-repository PR head"]},
                                     "human_review_required": True,
                                     "status": "held_for_human",
                                     "reason": "fork_pr_requires_human_review"})
                        held.append(candidate.number)
                        results.append(item)
                        continue
                    previous_head = _git(worktree, "rev-parse", "HEAD")
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
                    if FULL_SHA.fullmatch(previous_head):
                        _git(worktree, "reset", "--hard", previous_head, check=False)
                        _git(worktree, "clean", "-fdx", check=False)
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


def run_loop(repo: Path, base_ref: str, candidates: Iterable[Candidate],
             command: tuple[str, ...] = DEFAULT_COMMAND, timeout: int = 900,
             work_root: Path | None = None, fetch_missing: bool = False,
             state_path: Path | None = None, max_rounds: int = 1,
             refresh: Any = None) -> dict[str, Any]:
    """Run bounded rounds and accumulate a human-review bundle.

    ``refresh`` is an optional zero-argument callable used by the CLI to
    rediscover open PRs between rounds. A candidate is skipped only when its
    manifest/discovery metadata includes the same immutable head SHA that a
    prior round processed. This makes re-invocation safe while allowing a new
    push to the same PR to be considered again.
    """
    if max_rounds < 1:
        raise ValueError("max_rounds must be positive")
    if max_rounds > 1 and state_path is None:
        raise ValueError("--state is required when max_rounds is greater than one")
    state = load_state(state_path)
    source = list(candidates)
    reports: list[dict[str, Any]] = []
    skipped_total = 0
    for round_number in range(1, max_rounds + 1):
        if round_number > 1 and refresh is not None:
            source = list(refresh())
        pending, skipped = pending_candidates(source, state)
        skipped_total += skipped
        if not pending:
            break
        report = integrate(repo, base_ref, pending, command, timeout, work_root, fetch_missing)
        report["round"] = round_number
        reports.append(report)
        for item in report["candidates"]:
            if item.get("head_sha") and item.get("status") == "included":
                state["processed"][str(item["pr"])] = {
                    "head_sha": item["head_sha"], "status": item["status"]}
        save_state(state_path, state)
    if reports:
        base_sha = reports[0]["base_sha"]
    else:
        base_sha = _sha(repo, base_ref)
    all_items = [item for report in reports for item in report["candidates"]]
    # Keep exposure metrics in ``rounds``/candidates_total, but present one
    # current decision per PR in the human bundle. If a PR head changes, the
    # latest round replaces the stale prior decision.
    latest_by_pr: dict[int, dict[str, Any]] = {}
    for item in all_items:
        latest_by_pr[int(item["pr"])] = item
    bundle_items = list(latest_by_pr.values())
    included = [item["pr"] for item in bundle_items if item["status"] == "included"]
    held = [item["pr"] for item in bundle_items if item["status"] == "held_for_human"]
    return {"schema_version": SCHEMA_VERSION, "local_integration_version": 1,
            "base_ref": base_ref, "base_sha": base_sha,
            "status": "review_required" if held else "routine_survivors_ready",
            "included_prs": included, "held_prs": held,
            "human_review_required": bool(held), "remote_write": False,
            "metrics": {"rounds_completed": len(reports),
                        "candidates_total": len(all_items),
                        "bundle_unique_count": len(bundle_items),
                        "included_count": len(included), "held_count": len(held),
                        "skipped_processed_count": skipped_total,
                        "acute_count": sum(item.get("classification") == "acute" for item in all_items)},
            "command": list(command), "rounds": reports,
            "candidates": bundle_items, "state_path": str(state_path) if state_path else None,
            "policy": {"local_merge_only": True, "no_remote_merge": True,
                       "credential_env_scrubbed": True,
                       "acute_risk_surfaces_human": True,
                       "bounded_rounds": True}}


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
    parser.add_argument("--state", type=Path,
                        help="local JSON state for idempotent multi-round processing")
    parser.add_argument("--max-rounds", type=int, default=1,
                        help="bounded discovery rounds; requires --state when greater than one")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, required=True)
    parser.add_argument("--timeout", type=int, default=900)
    parser.add_argument("--command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    try:
        if not args.manifest and not args.repo_slug:
            raise ValueError("--repo-slug is required when --manifest is omitted")
        repo = args.repo.resolve()
        candidates = load_manifest(args.manifest) if args.manifest else discover_open(args.repo_slug, args.base)
        refresh = None if args.manifest else lambda: discover_open(args.repo_slug, args.base)
        report = run_loop(repo, args.base, candidates,
                          tuple(args.command or DEFAULT_COMMAND), args.timeout,
                          fetch_missing=args.fetch_missing, state_path=args.state,
                          max_rounds=args.max_rounds, refresh=refresh)
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
