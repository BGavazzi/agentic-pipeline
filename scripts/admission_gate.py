#!/usr/bin/env python3
"""Validate v1 gate receipts against a trusted risk report and exact commit pair.

Usage: admission_gate.py --risk PATH --receipts PATH --base-sha SHA --head-sha SHA
Exit: 0 admitted, 1 unmet obligations, 2 invalid input. JSON decision on stdout.
Caller MUST supply protected risk/receipt inputs from independent execution.
This checks consistency, NOT authenticity; signatures/CI adapters are pending.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from blast_radius import required_gates_for

SCHEMA_VERSION = 1
KNOWN_GATES = {"unit", "integration", "sast", "sca", "ultrareview", "infra-dry-run", "secrets"}
STATUSES = {"pass", "fail", "error", "skipped", "not_applicable"}


def evaluate(risk: dict, receipts: dict, base_sha: str, head_sha: str) -> dict:
    """Fail closed on invalid identity, missing gates, duplicate or unknown receipts."""
    for sha in (base_sha, head_sha):
        if not isinstance(sha, str) or not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", sha):
            raise ValueError("expected full commit SHA")
    for doc in (risk, receipts):
        if not isinstance(doc, dict) or type(doc.get("schema_version")) is not int or doc["schema_version"] != SCHEMA_VERSION:
            raise ValueError("unsupported schema version")
        if doc.get("base_sha") != base_sha or doc.get("head_sha") != head_sha:
            raise ValueError("stale or mismatched commit identity")
    level = risk.get("risk_level")
    triggers = risk.get("risk_triggers")
    required = risk.get("required_gates")
    if level not in ("low", "medium", "high"):
        raise ValueError("unknown risk level")
    if not isinstance(triggers, list) or any(not isinstance(t, str) for t in triggers):
        raise ValueError("invalid risk triggers")
    if not isinstance(required, list) or not required or any(not isinstance(g, str) for g in required):
        raise ValueError("missing required gates")
    if len(required) != len(set(required)) or set(required) - KNOWN_GATES:
        raise ValueError("duplicate or unknown required gate")
    if not set(required_gates_for(level, triggers)) <= set(required):
        raise ValueError("risk obligations were removed")
    # Scanners remain mandatory even for low risk, matching existing CI policy.
    obligations = set(required) | {"sast", "sca", "secrets"}
    items = receipts.get("gates")
    if not isinstance(items, list):
        raise ValueError("missing gate receipts")
    by_gate = {}
    for item in items:
        if not isinstance(item, dict):
            raise ValueError("invalid receipt")
        name, status = item.get("gate"), item.get("status")
        if not isinstance(name, str) or name not in KNOWN_GATES or name in by_gate:
            raise ValueError("unknown or duplicate receipt")
        if not isinstance(status, str) or status not in STATUSES:
            raise ValueError("invalid receipt status")
        by_gate[name] = status
    blockers = {gate: by_gate.get(gate, "missing") for gate in sorted(obligations)
                if by_gate.get(gate) != "pass"}
    # Extra failed evidence cannot be discarded just because selection missed it.
    blockers.update({gate: status for gate, status in by_gate.items() if status != "pass"})
    passed = sum(by_gate.get(gate) == "pass" for gate in obligations)
    return {"schema_version": SCHEMA_VERSION, "admitted": not blockers,
            "base_sha": base_sha, "head_sha": head_sha,
            "required_gates": sorted(obligations), "blockers": blockers,
            "metrics": {"required_count": len(obligations), "passed_count": passed,
                        "evidence_completeness": passed / len(obligations)}}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for option in ("risk", "receipts", "base-sha", "head-sha"):
        parser.add_argument("--" + option, required=True)
    args = parser.parse_args()
    try:
        result = evaluate(json.loads(Path(args.risk).read_text(encoding="utf-8")),
                          json.loads(Path(args.receipts).read_text(encoding="utf-8")),
                          args.base_sha, args.head_sha)
    except (OSError, ValueError, TypeError) as exc:
        # Do not echo arbitrary source/report content into logs.
        print(json.dumps({"schema_version": SCHEMA_VERSION, "admitted": False,
                          "error": "invalid input", "error_type": type(exc).__name__}))
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0 if result["admitted"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
