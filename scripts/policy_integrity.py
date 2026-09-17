#!/usr/bin/env python3
"""Emit a provenance-bound receipt for changes to the policy surface.

The report does not pretend to make a PR workflow immutable. It makes policy
changes explicit and non-admissible until a protected review path handles them.
The trusted reference is normally the protected base commit.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

SCHEMA_VERSION = 1
POLICY_PATHS = (
    ".pre-commit-config.yaml",
    ".pre-commit-config.yml",
    ".github/workflows/ci.yml",
    "scripts/admission_gate.py",
    "scripts/blast_radius.py",
    "scripts/ci_receipts.py",
    "scripts/core_sync.py",
    "scripts/harness_selftest.py",
    "scripts/impact_benchmark.py",
    "scripts/impact_runner.py",
    "scripts/impact_promotion.py",
    "scripts/integration_gate.py",
    "scripts/infra_dry_run.py",
    "scripts/meta_test.py",
    "scripts/meta_test_dispatch.py",
    "scripts/worker_supervisor.py",
    "scripts/worker_boundary.py",
    "scripts/policy_integrity.py",
    "scripts/quality_scorecard.py",
    "scripts/quota_gate.py",
    "scripts/scan_gate.py",
    "scripts/staging_gate.py",
    "scripts/staging_pr.py",
    "scripts/test_impact.py",
    "scripts/ultrareview_receipt.py",
    "scripts/ultrareview_runner.py",
    "scripts/validate_closure.py",
    "scripts/validate_task.py",
    "scripts/visual_receipt.py",
)


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=repo, capture_output=True, text=True, encoding="utf-8"
    )
    if result.returncode != 0:
        raise RuntimeError("git policy query failed")
    return result.stdout


def _hash_at(repo: Path, ref: str, relative: str) -> str | None:
    result = subprocess.run(
        ["git", "show", f"{ref}:{relative}"],
        cwd=repo,
        capture_output=True,
    )
    if result.returncode != 0:
        return None
    return hashlib.sha256(result.stdout).hexdigest()


def build_report(repo: Path, base: str, head: str, policy_ref: str | None = None,
                 review_evidence: dict | None = None) -> dict:
    """Report whether the candidate changes a file that defines policy."""
    policy_ref = policy_ref or base
    changed = [
        line for line in _git(repo, "diff", "--name-only", f"{base}..{head}").splitlines()
        if line
    ]
    # Protect the whole executable policy surface, including newly added
    # modules/workflows. A hand-maintained list silently misses new adapters.
    def protected(path: str) -> bool:
        return path in POLICY_PATHS or path.startswith(("scripts/", ".github/", ".claude/skills/"))
    inventory = set(POLICY_PATHS)
    for ref in (policy_ref, head):
        inventory.update(path for path in _git(repo, "ls-tree", "-r", "--name-only", ref).splitlines()
                         if protected(path))
    changed_policy = sorted(path for path in changed if protected(path))
    trusted_hashes = {
        relative: digest
        for relative in sorted(inventory)
        if (digest := _hash_at(repo, policy_ref, relative)) is not None
    }
    candidate_hashes = {
        relative: digest
        for relative in sorted(inventory)
        if (digest := _hash_at(repo, head, relative)) is not None
    }
    version_material = "\n".join(
        f"{relative}:{trusted_hashes.get(relative, '<missing')}"
        for relative in sorted(trusted_hashes)
    ).encode("utf-8")
    approved = bool(review_evidence and review_evidence.get("base_sha") == base
                    and review_evidence.get("head_sha") == head
                    and review_evidence.get("approved") is True
                    and review_evidence.get("reviewer") and review_evidence.get("review_id"))
    return {
        "schema_version": SCHEMA_VERSION,
        "gate": "policy",
        "base_sha": base,
        "head_sha": head,
        "trusted_policy_ref": policy_ref,
        "policy_version": hashlib.sha256(version_material).hexdigest(),
        "changed_policy_files": changed_policy,
        "candidate_hashes": candidate_hashes,
        "status": "pass" if not changed_policy or approved else "review_required",
        "trusted_review": review_evidence if approved else None,
        "metrics": {
            "policy_file_count": len(inventory),
            "changed_policy_file_count": len(changed_policy),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--base", required=True)
    parser.add_argument("--head", required=True)
    parser.add_argument("--policy-ref")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--trusted-review", type=Path,
                        help="ONLY a protected caller may supply independently fetched review evidence")
    args = parser.parse_args()
    try:
        review = json.loads(args.trusted_review.read_text(encoding="utf-8")) if args.trusted_review else None
        if review is not None and not isinstance(review, dict):
            raise ValueError("review evidence must be an object")
        report = build_report(args.repo.resolve(), args.base, args.head, args.policy_ref, review)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    except (OSError, RuntimeError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print("ERROR: policy integrity failed: " + type(exc).__name__, flush=True)
        return 2
    print(
        f"policy_integrity: status={report['status']} "
        f"changed={report['metrics']['changed_policy_file_count']}"
    )
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
