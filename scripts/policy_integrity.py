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
    "scripts/integration_gate.py",
    "scripts/infra_dry_run.py",
    "scripts/meta_test.py",
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


def build_report(repo: Path, base: str, head: str, policy_ref: str | None = None) -> dict:
    """Report whether the candidate changes a file that defines policy."""
    policy_ref = policy_ref or base
    changed = [
        line for line in _git(repo, "diff", "--name-only", f"{base}..{head}").splitlines()
        if line
    ]
    changed_policy = sorted(set(changed) & set(POLICY_PATHS))
    trusted_hashes = {
        relative: digest
        for relative in POLICY_PATHS
        if (digest := _hash_at(repo, policy_ref, relative)) is not None
    }
    candidate_hashes = {
        relative: digest
        for relative in POLICY_PATHS
        if (digest := _hash_at(repo, head, relative)) is not None
    }
    version_material = "\n".join(
        f"{relative}:{trusted_hashes.get(relative, '<missing')}"
        for relative in sorted(trusted_hashes)
    ).encode("utf-8")
    return {
        "schema_version": SCHEMA_VERSION,
        "gate": "policy",
        "base_sha": base,
        "head_sha": head,
        "trusted_policy_ref": policy_ref,
        "policy_version": hashlib.sha256(version_material).hexdigest(),
        "changed_policy_files": changed_policy,
        "candidate_hashes": candidate_hashes,
        "status": "pass" if not changed_policy else "review_required",
        "metrics": {
            "policy_file_count": len(POLICY_PATHS),
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
    args = parser.parse_args()
    try:
        report = build_report(args.repo.resolve(), args.base, args.head, args.policy_ref)
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
