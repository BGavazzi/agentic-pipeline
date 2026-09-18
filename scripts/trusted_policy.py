#!/usr/bin/env python3
"""Verify protected policy evidence before it can participate in admission.

This is a verifier, not a trust oracle. The caller must obtain the policy
receipt, reviewer evidence, and producer attestation from a protected control
plane. Candidate code cannot manufacture trust merely by invoking this script.
The verifier binds every input to the exact base/head pair and an immutable
policy reference, then fails closed when an external attestation is absent.

Exit codes: 0 verified, 1 blocked, 2 malformed input.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
FULL_SHA = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")


def _sha(value: object) -> bool:
    return isinstance(value, str) and bool(FULL_SHA.fullmatch(value))


def _text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def evaluate(
    policy: dict[str, Any],
    attestation: dict[str, Any] | None,
    base_sha: str,
    head_sha: str,
    approved_policy_ref: str | None = None,
) -> dict[str, Any]:
    """Return a fail-closed trust receipt or raise for malformed evidence."""
    if not _sha(base_sha) or not _sha(head_sha):
        raise ValueError("base_sha and head_sha must be full commit SHAs")
    if not isinstance(policy, dict) or policy.get("schema_version") != 1:
        raise ValueError("unsupported policy receipt schema")
    if policy.get("gate") != "policy":
        raise ValueError("input is not a policy receipt")
    if policy.get("base_sha") != base_sha or policy.get("head_sha") != head_sha:
        raise ValueError("policy receipt has stale commit identity")
    policy_ref = policy.get("trusted_policy_ref")
    if not _sha(policy_ref):
        raise ValueError("policy receipt lacks an immutable policy reference")
    if approved_policy_ref is not None:
        if not _sha(approved_policy_ref):
            raise ValueError("approved policy reference must be a full SHA")
        if policy_ref != approved_policy_ref:
            raise ValueError("policy reference is not the approved immutable pin")

    review = policy.get("trusted_review")
    blockers: dict[str, str] = {}
    if policy.get("status") != "pass":
        blockers["policy"] = "policy_receipt_not_pass"
    if not isinstance(review, dict) or review.get("approved") is not True:
        blockers["review"] = "exact_head_independent_review_missing"
    elif (review.get("base_sha") != base_sha or review.get("head_sha") != head_sha
          or not _text(review.get("reviewer")) or not _text(review.get("review_id"))):
        blockers["review"] = "review_identity_mismatch_or_incomplete"

    if not isinstance(attestation, dict):
        blockers["producer"] = "protected_producer_attestation_missing"
    else:
        if attestation.get("schema_version") != 1:
            blockers["producer"] = "unsupported_producer_attestation"
        if (attestation.get("base_sha") != base_sha
                or attestation.get("head_sha") != head_sha):
            blockers["producer_identity"] = "producer_attestation_identity_mismatch"
        if attestation.get("policy_ref") != policy_ref:
            blockers["producer_policy_ref"] = "producer_attestation_policy_mismatch"
        if not _text(attestation.get("workflow_ref")):
            blockers["producer_workflow"] = "workflow_identity_missing"
        if not _text(attestation.get("run_id")):
            blockers["producer_run"] = "run_identity_missing"
        if attestation.get("protected") is not True:
            blockers["producer_protection"] = "protected_producer_not_asserted"

    return {
        "schema_version": SCHEMA_VERSION,
        "gate": "trusted-policy",
        "base_sha": base_sha,
        "head_sha": head_sha,
        "trusted_policy_ref": policy_ref,
        "status": "pass" if not blockers else "blocked",
        "verified": not blockers,
        "blockers": blockers,
        "metrics": {
            "review_present": isinstance(review, dict),
            "producer_attestation_present": isinstance(attestation, dict),
            "immutable_policy_pin": True,
        },
        "policy": {
            "fail_closed": True,
            "candidate_cannot_assert_trust": True,
            "external_producer_required": True,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--attestation", type=Path)
    parser.add_argument("--base-sha", required=True)
    parser.add_argument("--head-sha", required=True)
    parser.add_argument("--approved-policy-ref")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        policy = json.loads(args.policy.read_text(encoding="utf-8"))
        attestation = (json.loads(args.attestation.read_text(encoding="utf-8"))
                       if args.attestation else None)
        report = evaluate(policy, attestation, args.base_sha, args.head_sha,
                          args.approved_policy_ref)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    except (OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print("ERROR: trusted policy verification failed: " + type(exc).__name__, flush=True)
        return 2
    print(f"trusted_policy: status={report['status']}")
    return 0 if report["verified"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
