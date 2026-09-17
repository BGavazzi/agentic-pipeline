#!/usr/bin/env python3
"""Check a core release against a versioned consumer compatibility matrix."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

try:
    from .core_version import validate as validate_metadata
except ImportError:  # pragma: no cover - exercised by the CLI entry point.
    from core_version import validate as validate_metadata

SCHEMA_VERSION = 1
VERSION = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")


def _version(value: Any) -> tuple[int, int, int]:
    if not isinstance(value, str) or not (match := VERSION.fullmatch(value)):
        raise ValueError("invalid semantic version")
    return tuple(int(part) for part in match.groups())


def evaluate(metadata: dict[str, Any], matrix: dict[str, Any]) -> dict[str, Any]:
    validate_metadata(metadata)
    if matrix.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("unsupported compatibility matrix schema")
    consumers = matrix.get("consumers")
    if not isinstance(consumers, list) or not consumers:
        raise ValueError("compatibility matrix needs consumers")
    current = _version(metadata["core_release_version"])
    supported = metadata.get("supported_contracts", {})
    results: list[dict[str, Any]] = []
    for consumer in consumers:
        if not isinstance(consumer, dict) or not isinstance(consumer.get("name"), str):
            raise ValueError("invalid consumer entry")
        minimum = _version(consumer.get("minimum_core_release"))
        required = consumer.get("required_contracts")
        if not isinstance(required, dict) or any(not isinstance(key, str) or type(value) is not int
                                                  for key, value in required.items()):
            raise ValueError("invalid required contract inventory")
        missing = sorted(key for key, value in required.items() if supported.get(key) != value)
        compatible = current >= minimum and not missing
        results.append({
            "name": consumer["name"],
            "compatible": compatible,
            "minimum_core_release": consumer["minimum_core_release"],
            "missing_or_mismatched_contracts": missing,
        })
    compatible_count = sum(item["compatible"] for item in results)
    return {
        "schema_version": SCHEMA_VERSION,
        "matrix_version": matrix.get("matrix_version", "unversioned"),
        "core_release_version": metadata["core_release_version"],
        "status": "pass" if compatible_count == len(results) else "fail",
        "metrics": {
            "consumers_total": len(results),
            "consumers_compatible": compatible_count,
            "consumers_incompatible": len(results) - compatible_count,
            "compatibility_rate": compatible_count / len(results),
        },
        "consumers": results,
        "policy": {"unsupported_contracts_fail_closed": True},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--matrix", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        report = evaluate(
            json.loads(args.metadata.read_text(encoding="utf-8")),
            json.loads(args.matrix.read_text(encoding="utf-8")),
        )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    except (OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print("ERROR: core compatibility failed: " + type(exc).__name__, file=sys.stderr)
        return 2
    print(f"core_compatibility: {report['status']} rate={report['metrics']['compatibility_rate']:.3f}")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
