#!/usr/bin/env python3
"""Validate screenshot/Playwright visual-regression evidence.

This adapter does not launch a browser. A consuming frontend repo runs its
Playwright adapter and supplies screenshots plus pixel metrics; this script
checks provenance, evidence, and threshold semantics before the result can be
carried as a visual gate receipt. A missing screenshot or baseline is an error,
never a pass.
"""
from __future__ import annotations

import argparse
import json
import re
import math
import hashlib
from pathlib import Path

SCHEMA_VERSION = 1
FULL_SHA = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")


def _text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_report(report: dict, base_sha: str, head_sha: str,
                    artifact_root: Path | None = None, threshold: float = 0.0) -> dict:
    if not isinstance(report, dict) or report.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("unsupported schema version")
    if not FULL_SHA.fullmatch(base_sha) or not FULL_SHA.fullmatch(head_sha):
        raise ValueError("expected full commit SHAs")
    if report.get("base_sha") != base_sha or report.get("head_sha") != head_sha:
        raise ValueError("stale or mismatched commit identity")
    if not _text(report.get("task")):
        raise ValueError("missing task identity")
    if artifact_root is None:
        raise ValueError("artifact root is required to verify visual evidence")
    root = artifact_root.resolve()
    def artifact(item: dict) -> None:
        path = (root / str(item.get("path", ""))).resolve()
        if not path.is_relative_to(root) or not path.is_file() or path.stat().st_size == 0:
            raise ValueError("missing or escaping visual artifact")
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if item.get("sha256") != digest:
            raise ValueError("visual artifact digest mismatch")
    evidence = report.get("evidence")
    if not isinstance(evidence, list) or not evidence:
        raise ValueError("visual evidence is required")
    for item in evidence:
        if not isinstance(item, dict) or item.get("kind") != "screenshot" \
                or not _text(item.get("path")) or not _text(item.get("viewport")):
            raise ValueError("each screenshot needs path and viewport")
        artifact(item)
    baseline = report.get("baseline")
    if not isinstance(baseline, dict) or not _text(baseline.get("ref")):
        raise ValueError("baseline provenance is required")
    artifact(baseline)
    metrics = report.get("metrics")
    if not isinstance(metrics, dict):
        raise ValueError("visual metrics are required")
    diff_ratio = metrics.get("diff_ratio")
    if type(threshold) not in (int, float) or not math.isfinite(threshold) or not 0 <= threshold <= 1:
        raise ValueError("invalid protected threshold")
    if metrics.get("threshold") != threshold:
        raise ValueError("candidate threshold differs from protected policy")
    for name, value in (("diff_ratio", diff_ratio), ("threshold", threshold)):
        if type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= 1:
            raise ValueError(f"metrics.{name} must be between 0 and 1")
    for name in ("pages", "comparisons", "changed_pixels", "total_pixels"):
        value = metrics.get(name)
        if type(value) is not int or value < 0:
            raise ValueError(f"metrics.{name} must be a non-negative integer")
    if metrics["comparisons"] != len(evidence):
        raise ValueError("comparisons must equal screenshot evidence count")
    if not 0 < metrics["pages"] <= metrics["comparisons"] or metrics["total_pixels"] <= 0:
        raise ValueError("visual evidence must contain pages and pixels")
    if metrics["changed_pixels"] > metrics["total_pixels"] or not math.isclose(
            diff_ratio, metrics["changed_pixels"] / metrics["total_pixels"], abs_tol=1e-9):
        raise ValueError("pixel counts contradict diff ratio")
    status = "pass" if diff_ratio <= threshold else "fail"
    return {
        "schema_version": SCHEMA_VERSION,
        "gate": "visual",
        "task": report["task"],
        "base_sha": base_sha,
        "head_sha": head_sha,
        "status": status,
        "baseline": baseline,
        "evidence": evidence,
        "metrics": metrics,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--base-sha", required=True)
    parser.add_argument("--head-sha", required=True)
    parser.add_argument("--artifact-root", type=Path, required=True)
    parser.add_argument("--threshold", type=float, required=True,
                        help="trusted policy threshold, not supplied by the candidate report")
    args = parser.parse_args()
    try:
        report = validate_report(json.loads(args.input.read_text(encoding="utf-8")),
                                 args.base_sha, args.head_sha, args.artifact_root, args.threshold)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    except (OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print("ERROR: invalid visual evidence: " + type(exc).__name__, flush=True)
        return 2
    print(f"visual_receipt: status={report['status']} diff_ratio="
          f"{report['metrics']['diff_ratio']:.6f}")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
