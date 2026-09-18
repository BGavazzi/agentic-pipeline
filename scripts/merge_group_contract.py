#!/usr/bin/env python3
"""Validate the structural identity of a GitHub merge-group event.

This contract proves only that a merge-queue event carries the commit/ref
identity needed to run checks. It does not claim branch-protection settings,
check completion, deployment health or rollback authority.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
SHA_RE = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")


def validate_event(event: dict[str, Any], event_name: str,
                   required_checks: list[str]) -> dict[str, Any]:
    if event_name != "merge_group":
        raise ValueError("event_name must be merge_group")
    group = event.get("merge_group")
    if not isinstance(group, dict):
        raise ValueError("merge_group payload is missing")
    base_sha, head_sha = group.get("base_sha"), group.get("head_sha")
    if not isinstance(base_sha, str) or not SHA_RE.fullmatch(base_sha):
        raise ValueError("merge_group.base_sha is invalid")
    if not isinstance(head_sha, str) or not SHA_RE.fullmatch(head_sha):
        raise ValueError("merge_group.head_sha is invalid")
    base_ref, head_ref = group.get("base_ref"), group.get("head_ref")
    if not isinstance(base_ref, str) or not base_ref.startswith("refs/heads/"):
        raise ValueError("merge_group.base_ref is invalid")
    if not isinstance(head_ref, str) or not head_ref.startswith("refs/heads/"):
        raise ValueError("merge_group.head_ref is invalid")
    checks = sorted({item.strip() for item in required_checks if item.strip()})
    if not checks:
        raise ValueError("at least one required check is needed")
    return {"schema_version": SCHEMA_VERSION, "merge_group_contract_version": 1,
            "status": "pass", "action": event.get("action", "unknown"),
            "base_sha": base_sha, "head_sha": head_sha,
            "base_ref": base_ref, "head_ref": head_ref,
            "required_checks": checks,
            "checks_observed": False, "deployment_observed": False,
            "admission_authority": False}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--event", type=Path, required=True)
    parser.add_argument("--event-name", required=True)
    parser.add_argument("--required-check", action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        event = json.loads(args.event.read_text(encoding="utf-8"))
        if not isinstance(event, dict):
            raise ValueError("event must be a JSON object")
        report = validate_event(event, args.event_name, args.required_check)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    except (OSError, TypeError, ValueError, UnicodeError, json.JSONDecodeError) as exc:
        print(f"ERROR: merge-group contract failed: {type(exc).__name__}")
        return 2
    print(f"merge_group_contract: status={report['status']} checks={len(report['required_checks'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
