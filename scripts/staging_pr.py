#!/usr/bin/env python3
"""Open a staging-review PR only after a valid staging eligibility receipt.

This is the external handoff adapter, not an admission gate and not a merge
bot. It validates exact candidate identity, refuses blocked receipts, checks
for an existing open PR for the same head branch, and invokes ``gh`` with an
argv list. ``--dry-run`` prints the planned operation without any external
write.

Exit codes: 0 created/already-existing/dry-run, 1 blocked or duplicate policy
failure, 2 invalid input or GitHub CLI failure.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from urllib.parse import quote
from pathlib import Path

FULL_SHA = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")


def read_eligibility(path: Path, expected_head: str) -> dict:
    report = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(report, dict) or report.get("schema_version") != 1:
        raise ValueError("unsupported eligibility schema")
    if report.get("target") != "staging-review":
        raise ValueError("eligibility target is not staging-review")
    if report.get("head_sha") != expected_head:
        raise ValueError("eligibility is for a different head SHA")
    if report.get("eligible") is not True or report.get("blockers"):
        raise PermissionError("candidate is not eligible for staging review")
    if report.get("provenance", {}).get("human_review_required") is not True:
        raise ValueError("human-review handoff marker is missing")
    return report


def git_sha(repo_path: Path, ref: str) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "--verify", "--end-of-options", ref + "^{commit}"], cwd=repo_path, capture_output=True,
        text=True, encoding="utf-8", errors="replace",
    )
    if result.returncode != 0:
        raise RuntimeError("could not resolve candidate ref")
    value = result.stdout.strip()
    if not FULL_SHA.fullmatch(value):
        raise ValueError("resolved candidate is not a full commit SHA")
    return value


def gh_json(args: list[str]) -> list | dict:
    result = subprocess.run(["gh", *args], capture_output=True, text=True,
                            encoding="utf-8", errors="replace")
    if result.returncode != 0:
        raise RuntimeError("gh query failed")
    value = json.loads(result.stdout or "[]")
    if not isinstance(value, (list, dict)):
        raise ValueError("gh returned an invalid JSON value")
    return value


def staging_pr_command(repo: str, head: str, base: str, title: str,
                       body_file: Path) -> list[str]:
    return ["gh", "pr", "create", "--repo", repo, "--head", head,
            "--base", base, "--title", title, "--body-file", str(body_file), "--draft"]


def verify_remote(repo_path: Path, repo: str, head: str, base: str,
                  expected_head: str, expected_base: str) -> None:
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo):
        raise ValueError("invalid GitHub repository")
    origin = subprocess.run(["git", "remote", "get-url", "origin"], cwd=repo_path,
                            capture_output=True, text=True, check=True).stdout.strip()
    allowed = {f"https://github.com/{repo}", f"https://github.com/{repo}.git",
               f"git@github.com:{repo}.git", f"git@github.com:{repo}"}
    if origin.lower() not in {x.lower() for x in allowed}:
        raise ValueError("local origin does not match eligibility repository")
    for branch, expected in ((head, expected_head), (base, expected_base)):
        value = gh_json(["api", f"repos/{repo}/git/ref/heads/{quote(branch, safe='')}"])
        if not isinstance(value, dict) or value.get("object", {}).get("sha") != expected:
            raise ValueError("remote branch moved; fresh integration evidence required")


def verify_pr(value: dict, head_sha: str, base_sha: str, base: str) -> None:
    if value.get("headRefOid") != head_sha or value.get("baseRefOid") != base_sha or value.get("baseRefName") != base:
        raise ValueError("PR identity changed; do not promote, rerun integration")


def create_staging_pr(
    eligibility_path: Path, repo_path: Path, repo: str, head: str, base: str,
    title: str, body_file: Path, dry_run: bool = False,
) -> dict:
    expected_head = git_sha(repo_path, head)
    eligibility = read_eligibility(eligibility_path, expected_head)
    expected_base = git_sha(repo_path, base)
    if eligibility.get("base_sha") != expected_base or eligibility.get("repository") != repo:
        raise ValueError("eligibility base/repository does not match target")
    verify_remote(repo_path, repo, head, base, expected_head, expected_base)
    existing = gh_json(["pr", "list", "--repo", repo, "--head", head,
                        "--base", base, "--state", "open", "--json",
                        "number,url,headRefOid,baseRefOid,baseRefName"])
    if not isinstance(existing, list):
        raise ValueError("unexpected open-PR response")
    command = staging_pr_command(repo, head, base, title, body_file)
    if existing:
        verify_pr(existing[0], expected_head, expected_base, base)
        return {"status": "already_exists", "head_sha": expected_head,
                "url": existing[0].get("url"), "command": command}
    if dry_run:
        return {"status": "dry_run", "head_sha": expected_head,
                "command": command, "metrics": eligibility.get("metrics", {})}
    # GitHub has no compare-and-swap PR-create API. Create a DRAFT, then
    # revalidate its refs; even a racing update cannot surface as ready review.
    result = subprocess.run(command, capture_output=True, text=True,
                            encoding="utf-8", errors="replace")
    if result.returncode != 0:
        raise RuntimeError("gh could not create staging PR")
    url = result.stdout.strip()
    created = gh_json(["pr", "view", url, "--repo", repo, "--json",
                       "headRefOid,baseRefOid,baseRefName"])
    verify_pr(created, expected_head, expected_base, base)
    verify_remote(repo_path, repo, head, base, expected_head, expected_base)
    return {"status": "draft_created", "head_sha": expected_head,
            "url": result.stdout.strip(), "command": command,
            "metrics": eligibility.get("metrics", {})}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--eligibility", type=Path, required=True)
    parser.add_argument("--repo-path", type=Path, default=Path.cwd())
    parser.add_argument("--repo", required=True, help="owner/name GitHub slug")
    parser.add_argument("--head", required=True, help="candidate branch")
    parser.add_argument("--base", required=True, help="staging base branch")
    parser.add_argument("--title", required=True)
    parser.add_argument("--body-file", type=Path, required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    try:
        result = create_staging_pr(
            args.eligibility, args.repo_path.resolve(), args.repo, args.head,
            args.base, args.title, args.body_file, args.dry_run,
        )
    except PermissionError as exc:
        print(json.dumps({"status": "blocked", "reason": str(exc)}))
        return 1
    except (OSError, RuntimeError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "error", "error_type": type(exc).__name__}))
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
