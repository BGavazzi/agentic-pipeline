#!/usr/bin/env python3
"""Produce/consume policy envelopes using read-only GitHub API observations.

Run this implementation from an externally approved immutable checkout. API
verification here does NOT protect a caller allowed to replace this code/pin.
No candidate checkout, imports, subprocess execution or archive extraction.
Only the fixed gh executable is invoked, for authenticated GET requests.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
import zipfile
from urllib.parse import quote

try:
    from .policy_integrity import POLICY_PATHS
except ImportError:
    from policy_integrity import POLICY_PATHS

WORKFLOW = ".github/workflows/trusted-policy.yml"
MAX_BYTES = 2_000_000
SHA = re.compile(r"[0-9a-f]{40}")
SENSITIVE = re.compile(r"(^scripts/|^\.github/|^\.claude/skills/|(^|/)(auth|security|infra|terraform|migrations|schema)(/|\.)|\.tf$)", re.I)


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise ValueError(reason)


def positive(value: object) -> bool:
    return type(value) is int and value > 0


def digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                    allow_nan=False).encode()).hexdigest()


def identity(repository: str, number: int, base: str, head: str, pin: str) -> dict:
    require(bool(re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository)), "invalid repository")
    require(positive(number), "invalid PR number")
    require(all(isinstance(s, str) and SHA.fullmatch(s) for s in (base, head, pin)), "full SHAs required")
    return dict(repository=repository, pull_request=number, base_sha=base, head_sha=head, policy_sha=pin)


def title(subject: dict) -> str:
    return f"policy-pr-{subject['pull_request']}-{subject['base_sha']}-{subject['head_sha']}"


def artifact_name(subject: dict, attempt: int) -> str:
    return f"trusted-policy-{subject['pull_request']}-{subject['head_sha']}-{attempt}"


class GitHub:
    """GET-only adapter. Paths originate here, never from artifact-provided URLs."""
    def __init__(self, repository: str):
        require(bool(re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository)), "invalid repository")
        self.root = f"repos/{repository}"

    def raw(self, suffix: str) -> bytes:
        result = subprocess.run(["gh", "api", "--method", "GET", f"{self.root}/{suffix}"],
                                capture_output=True, timeout=60)
        require(result.returncode == 0, "GitHub API request failed")
        require(len(result.stdout) <= MAX_BYTES, "API response too large")
        return result.stdout

    def get(self, suffix: str):
        return json.loads(self.raw(suffix))

    def pages(self, suffix: str, key: str | None = None) -> list:
        items = []
        for page in range(1, 32):
            data = self.get(f"{suffix}{'&' if '?' in suffix else '?'}per_page=100&page={page}")
            batch = data[key] if key else data
            require(isinstance(batch, list), "invalid API list")
            items.extend(batch)
            if len(batch) < 100:
                return items
        raise ValueError("API pagination limit exceeded")


def evaluate_review(pr: dict, files: list, reviews: list, permissions: dict) -> dict:
    """Current API state, not candidate claims. All substantive reviews count."""
    require(pr.get("state") == "open", "PR is not open")
    require(type(pr.get("changed_files")) is int and len(files) == pr["changed_files"], "incomplete diff inventory")
    paths = set()
    for item in files:
        require(isinstance(item.get("filename"), str), "invalid diff file")
        paths.add(item["filename"])
        if item.get("previous_filename"):
            paths.add(item["previous_filename"])
    changed_policy = sorted(p for p in paths if p in POLICY_PATHS or p.startswith(("scripts/", ".github/", ".claude/skills/")))
    require(all(type(pr.get(k)) is int and pr[k] >= 0 for k in ("additions", "deletions")), "invalid churn")
    impactful = bool(changed_policy or any(SENSITIVE.search(p) for p in paths) or pr["additions"] + pr["deletions"] >= 400)
    latest = {}
    for review in sorted(reviews, key=lambda r: r["id"]):
        require(positive(review.get("id")), "invalid review id")
        if review["state"] in {"APPROVED", "CHANGES_REQUESTED", "DISMISSED"}:
            latest[review["user"]["login"]] = review
    approvals, objections, state = [], [], []
    for login, review in sorted(latest.items()):
        permission = permissions.get(login)
        authorized = permission in {"admin", "maintain", "write"} and review["user"]["type"] == "User" and login != pr["user"]["login"]
        state.append([login, review["id"], review["state"], review.get("commit_id"), permission, authorized])
        if authorized and review["state"] == "CHANGES_REQUESTED":
            objections.append(review["id"])
        if authorized and review["state"] == "APPROVED" and review.get("commit_id") == pr["head"]["sha"]:
            approvals.append(review["id"])
    allowed = not objections and (not impactful or bool(approvals))
    return dict(allowed=allowed, impactful=impactful, approval_ids=approvals, objection_ids=objections,
                changed_policy_files=changed_policy, review_state_sha256=digest(state),
                reason="allowed" if allowed else "independent exact-head review required")


def snapshot(api: GitHub, subject: dict) -> tuple[dict, dict]:
    number = subject["pull_request"]
    pr = api.get(f"pulls/{number}")
    require(pr["base"]["repo"]["full_name"] == subject["repository"] and pr["number"] == number, "wrong PR repository")
    require(pr["base"]["sha"] == subject["base_sha"] and pr["head"]["sha"] == subject["head_sha"], "PR/base moved")
    files = api.pages(f"pulls/{number}/files")
    reviews = api.pages(f"pulls/{number}/reviews")
    permissions = {login: api.get(f"collaborators/{quote(login, safe='')}/permission")["permission"]
                   for login in sorted({r["user"]["login"] for r in reviews if r["user"]["type"] == "User"})}
    decision = evaluate_review(pr, files, reviews, permissions)
    current = api.get(f"pulls/{number}")
    require(current["state"] == "open" and current["base"]["sha"] == subject["base_sha"] and current["head"]["sha"] == subject["head_sha"], "PR moved during observation")
    return pr, decision


def validate_run(run: dict, subject: dict, workflow_id: int, *, completed: bool) -> None:
    require(isinstance(run, dict), "invalid run metadata")
    require(positive(workflow_id) and positive(run.get("workflow_id")) and run.get("workflow_id") == workflow_id, "wrong workflow id")
    require(run.get("repository", {}).get("full_name") == subject["repository"], "wrong run repository")
    require(run.get("path") == WORKFLOW and run.get("event") == "workflow_dispatch", "wrong workflow/event")
    require(run.get("head_sha") == subject["policy_sha"] and run.get("display_title") == title(subject), "unapproved producer or subject")
    require(positive(run.get("id")) and positive(run.get("run_attempt")), "invalid run identity")
    if completed:
        require(run.get("status") == "completed" and run.get("conclusion") == "success", "latest producer is not successful")


def produce(api: GitHub, subject: dict, run_id: int, attempt: int) -> dict:
    workflow_id = api.get("actions/workflows/trusted-policy.yml")["id"]
    run = api.get(f"actions/runs/{run_id}")
    validate_run(run, subject, workflow_id, completed=False)
    require(run["id"] == run_id and run["run_attempt"] == attempt, "wrong producer attempt")
    _, decision = snapshot(api, subject)
    tree = api.get(f"git/commits/{subject['head_sha']}")["tree"]["sha"]
    require(bool(SHA.fullmatch(tree)), "invalid subject tree")
    receipt = dict(schema_version=1, gate="policy", base_sha=subject["base_sha"], head_sha=subject["head_sha"],
                   status="pass" if decision["allowed"] else "review_required", policy_version=subject["policy_sha"],
                   changed_policy_files=decision["changed_policy_files"], early_review=decision)
    return dict(envelope_version=1, **subject, subject_tree=tree, executed_tree=None,
                execution_kind="metadata-only-policy", workflow_path=WORKFLOW, workflow_id=workflow_id,
                run_id=run_id, run_attempt=attempt, producer=f"github-actions:{subject['repository']}:{workflow_id}:{subject['policy_sha']}",
                artifact_name=artifact_name(subject, attempt), payload_sha256=digest(receipt), receipt=receipt)


def verify_archive(raw: bytes, artifact: dict, run: dict, subject: dict, workflow_id: int) -> dict:
    validate_run(run, subject, workflow_id, completed=True)
    require(len(raw) <= MAX_BYTES and artifact.get("size_in_bytes") == len(raw), "artifact size mismatch")
    require(artifact.get("expired") is False and artifact.get("workflow_run", {}).get("id") == run["id"], "expired or wrong-run artifact")
    require(artifact.get("digest") == "sha256:" + hashlib.sha256(raw).hexdigest(), "artifact digest mismatch")
    require(artifact.get("name") == artifact_name(subject, run["run_attempt"]), "wrong artifact attempt/name")
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        require(archive.namelist() == ["envelope.json"], "unexpected archive entries")
        require(archive.getinfo("envelope.json").file_size <= MAX_BYTES, "payload too large")
        envelope = json.loads(archive.read("envelope.json"))
    require(isinstance(envelope, dict), "invalid envelope object")
    require(type(envelope.get("envelope_version")) is int and envelope["envelope_version"] == 1, "unknown envelope version")
    require(all(positive(envelope.get(k)) for k in ("pull_request", "workflow_id", "run_id", "run_attempt")), "invalid envelope ids")
    require(all(envelope.get(k) == v for k, v in subject.items()), "wrong envelope subject")
    expected = dict(workflow_path=WORKFLOW, workflow_id=workflow_id, run_id=run["id"], run_attempt=run["run_attempt"],
                    producer=f"github-actions:{subject['repository']}:{workflow_id}:{subject['policy_sha']}",
                    artifact_name=artifact["name"], execution_kind="metadata-only-policy", executed_tree=None)
    require(all(envelope.get(k) == v for k, v in expected.items()), "wrong producer envelope")
    receipt = envelope["receipt"]
    require(isinstance(receipt, dict), "invalid policy payload object")
    require(digest(receipt) == envelope.get("payload_sha256"), "payload digest mismatch")
    require(type(receipt.get("schema_version")) is int and receipt["schema_version"] == 1 and receipt.get("gate") == "policy" and
            receipt.get("base_sha") == subject["base_sha"] and receipt.get("head_sha") == subject["head_sha"] and
            receipt.get("policy_version") == subject["policy_sha"] and receipt.get("status") in {"pass", "review_required"}, "invalid policy payload")
    return envelope


def consume(api: GitHub, subject: dict) -> dict:
    workflow_id = api.get("actions/workflows/trusted-policy.yml")["id"]
    runs = api.pages("actions/workflows/trusted-policy.yml/runs?event=workflow_dispatch", "workflow_runs")
    matching = [r for r in runs if r.get("display_title") == title(subject)]
    require(bool(matching), "no protected producer for this PR/base/head")
    # Never fall back to an old successful run when a new attempt failed/queued.
    run = api.get(f"actions/runs/{max(matching, key=lambda r: r['id'])['id']}")
    validate_run(run, subject, workflow_id, completed=True)
    artifacts = api.pages(f"actions/runs/{run['id']}/artifacts", "artifacts")
    matches = [a for a in artifacts if a.get("name") == artifact_name(subject, run["run_attempt"])]
    require(len(matches) == 1, "missing or duplicate producer artifact")
    artifact = matches[0]
    require(positive(artifact.get("id")) and type(artifact.get("size_in_bytes")) is int and 0 < artifact["size_in_bytes"] <= MAX_BYTES, "invalid artifact metadata")
    envelope = verify_archive(api.raw(f"actions/artifacts/{artifact['id']}/zip"), artifact, run, subject, workflow_id)
    tree = api.get(f"git/commits/{subject['head_sha']}")["tree"]["sha"]
    require(envelope["subject_tree"] == tree, "subject tree mismatch")
    _, current = snapshot(api, subject)
    require(current == envelope["receipt"].get("early_review"), "review changed; refresh protected producer")
    require((envelope["receipt"]["status"] == "pass") == current["allowed"], "policy contradicts current review")
    latest = api.get(f"actions/runs/{run['id']}")
    require(latest == run, "producer changed during verification")
    newest = [r for r in api.pages("actions/workflows/trusted-policy.yml/runs?event=workflow_dispatch", "workflow_runs") if r.get("display_title") == title(subject)]
    require(bool(newest) and max(r["id"] for r in newest) == run["id"], "new producer superseded evidence")
    return dict(envelope["receipt"], provenance=dict(verified_via="github-api", **subject,
                workflow_id=workflow_id, run_id=run["id"], run_attempt=run["run_attempt"],
                artifact_id=artifact["id"], artifact_digest=artifact["digest"], subject_tree=tree))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("produce", "consume"))
    parser.add_argument("--repository", required=True)
    parser.add_argument("--pr", type=int, required=True)
    parser.add_argument("--base-sha", required=True)
    parser.add_argument("--head-sha", required=True)
    parser.add_argument("--policy-sha", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    # Invalidate prior output BEFORE network/parse work or interruption.
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(dict(schema_version=1, gate="policy", status="error",
        base_sha=args.base_sha, head_sha=args.head_sha, error="trusted policy verification incomplete")) + "\n", encoding="utf-8")
    try:
        subject = identity(args.repository, args.pr, args.base_sha, args.head_sha, args.policy_sha)
        api = GitHub(args.repository)
        if args.mode == "produce":
            require(os.environ.get("GITHUB_SHA") == subject["policy_sha"], "producer code not at approved pin")
            result = produce(api, subject, int(os.environ["GITHUB_RUN_ID"]), int(os.environ["GITHUB_RUN_ATTEMPT"]))
        else:
            result = consume(api, subject)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        # A valid review_required receipt is evidence too; gate evaluation vetoes it.
        return 0
    except (OSError, ValueError, KeyError, TypeError, AttributeError, RuntimeError, subprocess.SubprocessError, zipfile.BadZipFile):
        # Replace stale output explicitly; never preserve a prior PASS on failure.
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(dict(schema_version=1, gate="policy", status="error",
            base_sha=args.base_sha, head_sha=args.head_sha, error="trusted policy verification failed")) + "\n", encoding="utf-8")
        print("BLOCK: trusted policy evidence unavailable or invalid; no fallback to local approval")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
