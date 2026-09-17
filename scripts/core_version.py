#!/usr/bin/env python3
"""Describe and validate the installed agentic core contract.

The core release version is separate from individual receipt schema versions.
Consumers can use this small CLI after ``core_sync.py`` to prove which core
release and source revision were installed without guessing from file contents.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

CORE_RELEASE_VERSION = "0.1.0"
METADATA_SCHEMA_VERSION = 1
FULL_SHA = re.compile(r"^[0-9a-f]{40}$")
SUPPORTED_CONTRACTS = {
    "receipt_schema": 1,
    "core_sync_manifest": 1,
    "producer_envelope": 1,
}


def metadata(source_commit: str | None = None) -> dict[str, Any]:
    return {
        "metadata_schema_version": METADATA_SCHEMA_VERSION,
        "core_release_version": CORE_RELEASE_VERSION,
        "source_repository": "BGavazzi/agentic-pipeline",
        "source_commit": source_commit,
        "supported_contracts": dict(SUPPORTED_CONTRACTS),
    }


def validate(value: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(value, dict) or value.get("metadata_schema_version") != METADATA_SCHEMA_VERSION:
        raise ValueError("unsupported core metadata schema")
    version = value.get("core_release_version")
    if not isinstance(version, str) or not re.fullmatch(r"\d+\.\d+\.\d+", version):
        raise ValueError("invalid core release version")
    source = value.get("source_repository")
    if source != "BGavazzi/agentic-pipeline":
        raise ValueError("unexpected core source repository")
    commit = value.get("source_commit")
    if commit is not None and (not isinstance(commit, str) or not FULL_SHA.fullmatch(commit)):
        raise ValueError("invalid source commit")
    contracts = value.get("supported_contracts")
    if not isinstance(contracts, dict) or contracts.get("receipt_schema") != 1:
        raise ValueError("unsupported contract inventory")
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        result = validate(json.loads(args.metadata.read_text(encoding="utf-8")))
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    except (OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print("ERROR: invalid core metadata: " + type(exc).__name__, file=sys.stderr)
        return 2
    print(f"core_version: {result['core_release_version']} ({result.get('source_commit') or 'unbound'})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
