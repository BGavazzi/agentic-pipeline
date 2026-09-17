#!/usr/bin/env python3
"""Benchmark conservative test-impact selection against versioned git fixtures.

The benchmark is observational: it reports precision/recall and whether the
current policy is promotion-ready, but it does not weaken the full-suite gate.
Each fixture contains a before/after tree and a declared relevant-test set.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
import time
import hashlib
from pathlib import Path

try:  # Package import for pytest; direct import for the CLI entry point.
    from .test_impact import analyze
except ImportError:  # pragma: no cover - exercised by `python scripts/...`.
    from test_impact import analyze


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=repo, capture_output=True, text=True, encoding="utf-8"
    )
    if result.returncode != 0:
        raise RuntimeError("fixture git operation failed")
    return result.stdout.strip()


def _write_tree(root: Path, files: dict[str, str]) -> None:
    for relative, content in files.items():
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")


def _commit(repo: Path, message: str) -> str:
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", message)
    return _git(repo, "rev-parse", "HEAD")


def run_case(path: Path) -> dict:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory(prefix="pipeline-impact-fixture-") as raw:
        repo = Path(raw)
        _git(repo, "init", "-q")
        _git(repo, "config", "user.email", "harness@example.invalid")
        _git(repo, "config", "user.name", "Harness Fixture")
        _write_tree(repo, manifest["before"])
        base_sha = _commit(repo, "fixture base")
        for relative in set(manifest["before"]) - set(manifest["after"]):
            (repo / relative).unlink()
        _write_tree(repo, manifest["after"])
        head_sha = _commit(repo, "fixture candidate")
        result = analyze(repo, base_sha, head_sha)

    selected = set(result["selected_tests"])
    relevant = set(manifest["relevant_tests"])
    intersection = selected & relevant
    precision = len(intersection) / len(selected) if selected else (1.0 if not relevant else 0.0)
    recall = len(intersection) / len(relevant) if relevant else 1.0
    minimum_precision = manifest.get("minimum_precision", 1.0)
    minimum_recall = manifest.get("minimum_recall", 1.0)
    contract_ok = (
        result["mode"] == manifest["expected_mode"]
        and precision >= minimum_precision
        and recall >= minimum_recall
    )
    return {
        "name": path.stem,
        "status": "pass" if contract_ok else "fail",
        "mode": result["mode"],
        "expected_mode": manifest["expected_mode"],
        "selected_tests": sorted(selected),
        "relevant_tests": sorted(relevant),
        "metrics": {
            "precision": precision,
            "recall": recall,
            "selected_count": len(selected),
            "relevant_count": len(relevant),
            "minimum_precision": minimum_precision,
            "minimum_recall": minimum_recall,
            "dependency_closure_count": result["metrics"].get(
                "dependency_closure_count", 0
            ),
        },
        "promotion_safe": result["mode"] == "impacted" and recall == 1.0,
    }


def run_benchmark(fixtures_dir: Path) -> dict:
    started = time.monotonic()
    cases = [run_case(path) for path in sorted(fixtures_dir.glob("*.json"))]
    passed = sum(case["status"] == "pass" for case in cases)
    impacted = [case for case in cases if case["mode"] == "impacted"]
    return {
        "schema_version": 1,
        "benchmark_version": "0.3",
        "selector_sha256": hashlib.sha256(Path(__file__).with_name("test_impact.py").read_bytes()).hexdigest(),
        "corpus_sha256": hashlib.sha256(b"".join(path.name.encode() + path.read_bytes()
                                      for path in sorted(fixtures_dir.glob("*.json")))).hexdigest(),
        "status": "pass" if cases and passed == len(cases) else "fail",
        "promotion_ready": bool(impacted) and all(
            case["promotion_safe"] for case in impacted
        ),
        "metrics": {
            "cases_total": len(cases),
            "cases_passed": passed,
            "cases_failed": len(cases) - passed,
            "impacted_cases": len(impacted),
            "mean_precision": (
                sum(case["metrics"]["precision"] for case in cases) / len(cases)
                if cases else 0.0
            ),
            "mean_recall": (
                sum(case["metrics"]["recall"] for case in cases) / len(cases)
                if cases else 0.0
            ),
            "duration_seconds": round(time.monotonic() - started, 3),
        },
        "cases": cases,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixtures", type=Path, default=Path("tests/impact/fixtures"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        report = run_benchmark(args.fixtures.resolve())
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    except (OSError, RuntimeError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print("ERROR: impact benchmark failed: " + type(exc).__name__, flush=True)
        return 2
    print(
        f"impact_benchmark: {report['status']} "
        f"recall={report['metrics']['mean_recall']:.3f} "
        f"promotion_ready={report['promotion_ready']}"
    )
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
