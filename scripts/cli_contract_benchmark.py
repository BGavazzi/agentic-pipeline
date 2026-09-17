#!/usr/bin/env python3
"""Run a bounded subprocess contract benchmark for the core gate CLIs.

The benchmark deliberately exercises only parser/help and missing-input paths.
Those paths must finish before any scanner, git mutation, network access, or
credential lookup can occur.  The gate-script registry is read from
``core_sync.py`` without importing or executing it, so the benchmark follows
the same allowlist used when the core is vendored.

Exit codes:
    0 -- every contract case passed
    1 -- at least one case failed or timed out
    2 -- benchmark usage/configuration error
"""
from __future__ import annotations

import argparse
import ast
import json
import os
import platform
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


BENCHMARK_VERSION = "1.0"
DEFAULT_TIMEOUT_SECONDS = 5.0
MAX_TIMEOUT_SECONDS = 30.0

# These two validators predate argparse and print their usage docstring when
# called without a path.  They are still part of the canonical gate registry,
# but ``--help`` is not a supported contract for them.
NO_ARGPARSE_HELP = frozenset({"validate_task.py", "validate_closure.py"})
SENSITIVE_ENV_MARKERS = (
    "API_KEY",
    "AUTH_TOKEN",
    "CREDENTIAL",
    "PASSWORD",
    "PRIVATE_KEY",
    "SECRET",
    "TOKEN",
)


@dataclass(frozen=True)
class ContractCase:
    name: str
    category: str
    script: str
    args: tuple[str, ...]
    expected_exit: int


def _positive_timeout(value: str) -> float:
    try:
        parsed = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("timeout must be a number") from exc
    if not 0 < parsed <= MAX_TIMEOUT_SECONDS:
        raise argparse.ArgumentTypeError(
            f"timeout must be > 0 and <= {MAX_TIMEOUT_SECONDS:g} seconds"
        )
    return parsed


def _gate_script_names(repo: Path) -> tuple[str, ...]:
    """Read ``core_sync.GATE_SCRIPTS`` as data, without importing the module."""
    source = repo / "scripts" / "core_sync.py"
    try:
        tree = ast.parse(source.read_text(encoding="utf-8"), filename=str(source))
    except (OSError, SyntaxError) as exc:
        raise ValueError(f"cannot read gate registry: {source} ({exc})") from exc

    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if not any(isinstance(target, ast.Name) and target.id == "GATE_SCRIPTS"
                   for target in node.targets):
            continue
        try:
            value = ast.literal_eval(node.value)
        except (ValueError, SyntaxError) as exc:
            raise ValueError("GATE_SCRIPTS must be a literal list") from exc
        if not isinstance(value, list) or not value or not all(
            isinstance(item, str) and item.endswith(".py") for item in value
        ):
            raise ValueError("GATE_SCRIPTS must be a non-empty list of .py names")
        if len(set(value)) != len(value):
            raise ValueError("GATE_SCRIPTS contains duplicate names")
        return tuple(value)

    raise ValueError("GATE_SCRIPTS assignment not found in core_sync.py")


def build_cases(repo: Path) -> tuple[ContractCase, ...]:
    """Build deterministic help and invalid-input cases for the core registry."""
    cases: list[ContractCase] = []
    for script in _gate_script_names(repo):
        script_path = repo / "scripts" / script
        if not script_path.is_file():
            raise ValueError(f"registered gate script is missing: {script_path}")
        if script not in NO_ARGPARSE_HELP:
            cases.append(ContractCase(
                name=f"{script}:help",
                category="help",
                script=script,
                args=("--help",),
                expected_exit=0,
            ))
        cases.append(ContractCase(
            name=f"{script}:missing-input",
            category="invalid-input",
            script=script,
            args=(),
            expected_exit=2,
        ))
    return tuple(cases)


def _safe_environment() -> dict[str, str]:
    """Return only ordinary process settings; never forward credentials."""
    keep = {"LANG", "LC_ALL", "PATH", "PATHEXT", "SYSTEMROOT", "TEMP", "TMP",
            "WINDIR"}
    environment = {
        key: value for key, value in os.environ.items()
        if key.upper() in keep
        and not any(marker in key.upper() for marker in SENSITIVE_ENV_MARKERS)
    }
    environment.update({"PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"})
    return environment


def run_case(repo: Path, case: ContractCase, timeout: float) -> dict[str, Any]:
    """Run one case without a shell and record only bounded output previews."""
    command = [sys.executable, "-X", "utf8", str(repo / "scripts" / case.script), *case.args]
    started = time.monotonic()
    timed_out = False
    try:
        completed = subprocess.run(
            command,
            cwd=str(repo),
            env=_safe_environment(),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            shell=False,
            timeout=timeout,
            check=False,
        )
        actual_exit = completed.returncode
        stdout = completed.stdout
        stderr = completed.stderr
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        actual_exit = None
        stdout = exc.stdout or ""
        stderr = exc.stderr or ""

    duration = time.monotonic() - started
    passed = not timed_out and actual_exit == case.expected_exit
    return {
        **asdict(case),
        "args": list(case.args),
        "actual_exit": actual_exit,
        "timed_out": timed_out,
        "passed": passed,
        "duration_seconds": round(duration, 4),
        "stdout_preview": str(stdout)[-500:],
        "stderr_preview": str(stderr)[-500:],
    }


def run_benchmark(repo: Path, timeout: float = DEFAULT_TIMEOUT_SECONDS) -> dict[str, Any]:
    """Run every case and return a stable, JSON-serializable metrics report."""
    repo = repo.resolve()
    cases = build_cases(repo)
    started = time.monotonic()
    results = [run_case(repo, case, timeout) for case in cases]
    duration = time.monotonic() - started
    help_count = sum(case.category == "help" for case in cases)
    invalid_count = sum(case.category == "invalid-input" for case in cases)
    passed = sum(result["passed"] for result in results)
    timed_out = sum(result["timed_out"] for result in results)
    return {
        "schema_version": 1,
        "benchmark": "core-cli-contract",
        "benchmark_version": BENCHMARK_VERSION,
        "status": "pass" if passed == len(results) else "fail",
        "repository": str(repo),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "execution": {
            "transport": "subprocess",
            "shell": False,
            "network": False,
            "credentials_forwarded": False,
            "timeout_seconds": timeout,
        },
        "metrics": {
            "scripts_total": len(_gate_script_names(repo)),
            "help_cases": help_count,
            "invalid_input_cases": invalid_count,
            "cases_total": len(results),
            "cases_passed": passed,
            "cases_failed": len(results) - passed,
            "timeouts": timed_out,
            "duration_seconds": round(duration, 4),
        },
        "cases": results,
    }


def _write_report(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo", type=Path, default=Path(__file__).resolve().parent.parent,
        help="repository root containing scripts/ (default: this repository)",
    )
    parser.add_argument(
        "--timeout", type=_positive_timeout, default=DEFAULT_TIMEOUT_SECONDS,
        help=f"per-case timeout in seconds (default: {DEFAULT_TIMEOUT_SECONDS:g}; max: {MAX_TIMEOUT_SECONDS:g})",
    )
    parser.add_argument("--output", type=Path, help="optional JSON report path")
    parser.add_argument("--json", action="store_true", help="emit the full JSON report")
    args = parser.parse_args()

    try:
        report = run_benchmark(args.repo, args.timeout)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if args.output:
        _write_report(args.output, report)

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        metrics = report["metrics"]
        print(
            f"core-cli-contract: {report['status']} "
            f"{metrics['cases_passed']}/{metrics['cases_total']} cases "
            f"({metrics['scripts_total']} scripts, "
            f"{metrics['duration_seconds']:.3f}s)"
        )
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
