#!/usr/bin/env python3
"""Build a schema-v1 receipt bundle from independent CI job artifacts.

This adapter only aggregates observed exit/status artifacts. It does not sign
them or make candidate-authored artifacts trustworthy; the final job and its
policy source need protected ownership before this is a security boundary.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

SCHEMA_VERSION = 1


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_status(path: Path) -> str:
    try:
        value = path.read_text(encoding="utf-8").strip()
    except OSError:
        return "error"
    return "pass" if value == "0" else "fail"


def build_receipts(risk_path: Path, scan_path: Path, unit_exit_path: Path,
                   base_sha: str, head_sha: str) -> dict:
    risk = read_json(risk_path)
    scan = read_json(scan_path)
    if risk.get("base_sha") != base_sha or risk.get("head_sha") != head_sha:
        raise ValueError("risk report is for a different commit pair")
    if scan.get("base_sha") not in (None, base_sha) or scan.get("head_sha") not in (None, head_sha):
        raise ValueError("scan report is for a different commit pair")

    statuses = {
        "unit": test_status(unit_exit_path),
        "sast": scan.get("tool_status", {}).get("semgrep", {}).get("status", "error"),
        "sca": scan.get("tool_status", {}).get("trivy", {}).get("status", "error"),
        "secrets": scan.get("tool_status", {}).get("gitleaks", {}).get("status", "error"),
    }
    statuses = {name: ("pass" if status == "ok" else status)
                for name, status in statuses.items()}
    return {"schema_version": SCHEMA_VERSION, "base_sha": base_sha,
            "head_sha": head_sha,
            "gates": [{"gate": name, "status": status} for name, status in sorted(statuses.items())],
            "evidence": {"risk_report": str(risk_path), "scan_report": str(scan_path),
                         "unit_exit": str(unit_exit_path)}}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--risk", type=Path, required=True)
    parser.add_argument("--scan", type=Path, required=True)
    parser.add_argument("--unit-exit", type=Path, required=True)
    parser.add_argument("--base-sha", required=True)
    parser.add_argument("--head-sha", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = build_receipts(args.risk, args.scan, args.unit_exit,
                                args.base_sha, args.head_sha)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        print("ERROR: could not build receipt bundle", flush=True)
        return 2
    print(f"receipt bundle: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
