#!/usr/bin/env python3
"""Run isolated agent-skill fixtures and emit a deterministic receipt.

The worker is an external process supplied by the runtime (for example, an
agent worker on the homelab pool).  It receives a disposable git repository via
environment variables and must print one JSON report to stdout.  This module
checks the worker's observable result: branch, commits, touched files, task
state, closure evidence, and high-level tool trajectory.  It never supplies a
remote and never invokes a shell, so a compliant worker cannot push from the
fixture sandbox.

Usage:
    python scripts/meta_test.py --fixtures tests/skills/fixtures \
        --output .docs/meta-test-reports/001.json --command COMMAND [ARGS...]

Exit codes:
    0 -- every fixture passed
    1 -- at least one fixture failed
    2 -- setup, worker, parsing, or usage error
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
import hashlib
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover - CI installs pyyaml.
    yaml = None

SCHEMA_VERSION = 1
DEFAULT_TIMEOUT_SECONDS = 900
MAX_OUTPUT_BYTES = 64 * 1024
SENSITIVE_ENV = re.compile(r"(TOKEN|SECRET|PASSWORD|PRIVATE_KEY|API_KEY)", re.IGNORECASE)


def _safe_environment() -> dict[str, str]:
    """Keep runtime basics while excluding obvious credentials and host hooks."""
    return {
        key: value for key, value in os.environ.items()
        if not SENSITIVE_ENV.search(key)
        and not key.startswith(("PIPELINE_CLEANUP_", "PIPELINE_WORKER_"))
    }


def _load_yaml(path: Path) -> dict[str, Any]:
    if yaml is None:
        raise RuntimeError("PyYAML is required for meta-test expected.yaml")
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"fixture manifest is not a mapping: {path}")
    return value


def _git(repo: Path, *args: str, check: bool = True) -> str:
    result = subprocess.run(
        ["git", *args], cwd=repo, capture_output=True, text=True,
        encoding="utf-8", errors="replace", check=False,
    )
    if check and result.returncode != 0:
        raise RuntimeError(f"git command failed: {' '.join(args)}")
    return result.stdout.strip()


def _seed_repo(fixture: Path, sandbox: Path) -> None:
    source_dir = fixture / "seed-repo"
    archive = fixture / "seed-repo.tar.gz"
    if source_dir.is_dir() and archive.exists():
        raise ValueError("fixture must provide either seed-repo/ or seed-repo.tar.gz")
    if source_dir.is_dir():
        shutil.copytree(source_dir, sandbox, dirs_exist_ok=True)
    elif archive.is_file():
        with tarfile.open(archive, "r:gz") as bundle:
            bundle.extractall(sandbox, filter="data")
    else:
        raise ValueError("fixture has no seed-repo/ or seed-repo.tar.gz")

    _git(sandbox, "init", "-q", "-b", "test/seed")
    _git(sandbox, "config", "user.email", "meta-test@localhost")
    _git(sandbox, "config", "user.name", "meta-test")
    _git(sandbox, "add", "--all")
    _git(sandbox, "commit", "-qm", "meta-test seed")
    # No remote is deliberately configured. A worker that attempts to push must
    # fail, and the postcondition below catches any attempt to add one.


def _task_status(sandbox: Path, task_id: str) -> str | None:
    candidates = list((sandbox / ".docs" / "tasks").glob(f"{task_id}*.md"))
    if not candidates:
        return None
    match = re.search(r"^status:\s*([^\s]+)\s*$", candidates[0].read_text(encoding="utf-8"), re.MULTILINE)
    return match.group(1) if match else None


def _parse_worker_output(stdout: str) -> dict[str, Any]:
    if len(stdout.encode("utf-8")) > MAX_OUTPUT_BYTES:
        raise ValueError("worker output exceeds bounded receipt input")
    try:
        value = json.loads(stdout)
    except json.JSONDecodeError as exc:
        raise ValueError("worker stdout is not one JSON object") from exc
    if not isinstance(value, dict):
        raise ValueError("worker report is not a JSON object")
    return value


def _marker(value: Any) -> str:
    """Normalize YAML 1.1 yes/no booleans and worker string markers."""
    if value is True:
        return "yes"
    if value is False:
        return "no"
    return str(value).strip().lower()


def _assertions(fixture: Path, sandbox: Path, baseline: str, worker: dict[str, Any],
                observations: dict[str, Any] | None = None) -> tuple[list[str], list[str], dict[str, Any]]:
    manifest = _load_yaml(fixture / "expected.yaml")
    expected = manifest.get("expected")
    if not isinstance(expected, dict):
        raise ValueError("expected.yaml must contain an expected mapping")

    failures: list[str] = []
    checks: list[str] = []
    branch = _git(sandbox, "branch", "--show-current")
    commits = int(_git(sandbox, "rev-list", "--count", f"{baseline}..HEAD"))
    touched = sorted(set(_git(sandbox, "diff", "--name-only", baseline).splitlines()) |
                     set(_git(sandbox, "ls-files", "--others", "--exclude-standard").splitlines()) |
                     set(_git(sandbox, "ls-files", "--others", "--ignored", "--exclude-standard").splitlines()))
    task_id = (fixture / "task-id.txt").read_text(encoding="utf-8").strip()
    task_id = Path(task_id).stem
    observed_status = _task_status(sandbox, task_id)
    task_paths = sorted((sandbox / ".docs/tasks").glob(f"{task_id}*.md"))
    task_text = task_paths[0].read_text(encoding="utf-8") if task_paths else ""

    def check(name: str, ok: bool, detail: str) -> None:
        checks.append(name)
        if not ok:
            failures.append(f"{name}: {detail}")

    if "task_status_final" in expected:
        check("task_status_final", observed_status == expected["task_status_final"],
              f"expected {expected['task_status_final']!r}, got {observed_status!r}")
    if "branch_pattern" in expected:
        check("branch_pattern", re.search(str(expected["branch_pattern"]), branch) is not None,
              f"expected {expected['branch_pattern']!r}, got {branch!r}")
    if "commits_min" in expected:
        check("commits_min", commits >= int(expected["commits_min"]), f"got {commits}")
    if "commits_max" in expected:
        check("commits_max", commits <= int(expected["commits_max"]), f"got {commits}")
    if "files_touched" in expected:
        check("files_touched", sorted(touched) == sorted(expected["files_touched"]),
              f"expected {sorted(expected['files_touched'])}, got {sorted(touched)}")
    if "files_NOT_touched" in expected:
        forbidden = set(expected["files_NOT_touched"]) & set(touched)
        check("files_NOT_touched", not forbidden, f"forbidden files changed: {sorted(forbidden)}")

    if "conditions_marked_done" in expected:
        exit_section = re.search(r"## Exit Conditions\s*\n(.*?)(?=\n## |\Z)", task_text, re.S)
        observed = len(re.findall(r"^- \[[xX]\]", exit_section.group(1), re.M)) if exit_section else 0
        check("conditions_marked_done", observed == expected["conditions_marked_done"],
              f"expected {expected['conditions_marked_done']!r}, got {observed!r}")

    closure = expected.get("lei_de_fechamento", {})
    observed_closure = {
        "CHANGELOG": "CHANGELOG.md" in touched and (sandbox / "CHANGELOG.md").is_file(),
        "tests": (observations or {}).get("tests_passed") is True,
    }
    if isinstance(closure, dict):
        for name, wanted in closure.items():
            check(f"closure.{name}", _marker(observed_closure.get(name)) == _marker(wanted),
                  f"expected {wanted!r}, got {observed_closure.get(name)!r}")

    sequence = (observations or {}).get("tool_calls", [])
    if (expected.get("tool_calls_must_include_in_order") or expected.get("tool_calls_must_NOT_include")) and observations is None:
        check("runtime_trace", False, "independent runtime trace unavailable; worker claims are not evidence")
    if not isinstance(sequence, list):
        sequence = []
    position = 0
    for wanted in expected.get("tool_calls_must_include_in_order", []):
        try:
            position = sequence.index(wanted, position) + 1
        except ValueError:
            failures.append(f"trajectory: missing ordered tool call {wanted!r}")
            checks.append("trajectory")
            break
    for forbidden in expected.get("tool_calls_must_NOT_include", []):
        check(f"trajectory.forbidden.{forbidden}", forbidden not in sequence,
              f"forbidden tool call present: {forbidden!r}")

    remotes = _git(sandbox, "remote", check=False)
    check("no_remote", not remotes, f"sandbox has remote(s): {remotes!r}")
    metrics = {
        "assertions_total": len(checks),
        "assertions_passed": len(checks) - len(failures),
        "commits": commits,
        "files_touched": len(touched),
    }
    return failures, checks, metrics


def run_fixture(fixture: Path, command: list[str], timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
                observer_command: list[str] | None = None,
                skills_root: Path | None = None) -> dict[str, Any]:
    started = time.monotonic()
    task_id = (fixture / "task-id.txt").read_text(encoding="utf-8").strip()
    skill = (fixture / "skill.txt").read_text(encoding="utf-8").strip()
    result: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "gate": "meta-test",
        "fixture": fixture.name,
        "skill": skill,
        "task": Path(task_id).stem,
        "status": "error",
        "metrics": {},
    }
    try:
        with tempfile.TemporaryDirectory(prefix=f"pipeline-meta-{fixture.name}-") as raw:
            sandbox = Path(raw) / "repo"
            sandbox.mkdir()
            _seed_repo(fixture, sandbox)
            if not re.fullmatch(r"[a-zA-Z0-9_-]+", skill):
                raise ValueError("invalid skill name")
            source = (skills_root or Path(__file__).resolve().parents[1] / ".claude/skills") / skill
            if not (source / "SKILL.md").is_file():
                raise ValueError("candidate skill is missing")
            if source.is_symlink() or any(p.is_symlink() for p in source.rglob("*")):
                raise ValueError("candidate skill symlinks are not permitted")
            shutil.copytree(source, sandbox / ".claude/skills" / skill, dirs_exist_ok=True)
            result["skill_sha256"] = hashlib.sha256(b"".join(
                p.relative_to(source).as_posix().encode() + p.read_bytes()
                for p in sorted(source.rglob("*")) if p.is_file())).hexdigest()
            _git(sandbox, "add", ".claude/skills")
            _git(sandbox, "commit", "-qm", "candidate skill under test")
            baseline = _git(sandbox, "rev-parse", "HEAD")
            env = _safe_environment()
            env.update({
                "CI": "1",
                "PIPELINE_META_TEST_SANDBOX": str(sandbox),
                "PIPELINE_META_TEST_FIXTURE": fixture.name,
                "PIPELINE_META_TEST_SKILL": skill,
                "PIPELINE_META_TEST_SKILL_PATH": str(sandbox / ".claude/skills" / skill / "SKILL.md"),
                "PIPELINE_META_TEST_TASK": task_id,
            })
            completed = subprocess.run(
                command, cwd=sandbox, env=env, capture_output=True, text=True,
                encoding="utf-8", errors="replace", timeout=timeout_seconds,
            )
            if completed.returncode != 0:
                result["error"] = "worker exited non-zero"
                result["metrics"] = {
                    "worker_exit_code": completed.returncode,
                    "duration_seconds": round(time.monotonic() - started, 3),
                }
                return result
            worker = _parse_worker_output(completed.stdout)
            observations = None
            if observer_command is not None:
                # A trusted host/runtime adapter reads its own audit trace and
                # independently runs verification. Candidate stdout is ignored.
                observed = subprocess.run(observer_command, cwd=fixture, env=env,
                                          capture_output=True, text=True, encoding="utf-8",
                                          timeout=timeout_seconds, check=True)
                observations = _parse_worker_output(observed.stdout)
            failures, checks, metrics = _assertions(fixture, sandbox, baseline, worker, observations)
            result["status"] = "pass" if not failures else "fail"
            result["failures"] = failures
            result["metrics"] = {
                **metrics,
                "worker_exit_code": completed.returncode,
                "duration_seconds": round(time.monotonic() - started, 3),
            }
            result["evidence"] = {"checks": checks, "worker_stderr_bytes": len(completed.stderr.encode("utf-8"))}
    except (OSError, RuntimeError, ValueError, KeyError, subprocess.SubprocessError) as exc:
        result["error"] = type(exc).__name__
        # Keep a bounded diagnostic for trusted operators; never echo worker
        # stdout/stderr wholesale into the receipt.
        result["error_detail"] = str(exc)[:240]
        result["metrics"] = {"duration_seconds": round(time.monotonic() - started, 3)}
    return result


def run_suite(
    fixtures_dir: Path,
    command: list[str],
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    base_sha: str | None = None,
    head_sha: str | None = None,
    observer_command: list[str] | None = None,
    skills_root: Path | None = None,
) -> dict[str, Any]:
    started = time.monotonic()
    fixtures = sorted(path.parent for path in fixtures_dir.glob("*/expected.yaml"))
    cases = [run_fixture(fixture, command, timeout_seconds, observer_command, skills_root) for fixture in fixtures]
    passed = sum(case["status"] == "pass" for case in cases)
    report = {
        "schema_version": SCHEMA_VERSION,
        "gate": "meta-test",
        "status": "pass" if cases and passed == len(cases) else "fail",
        "metrics": {
            "fixtures_total": len(cases),
            "fixtures_passed": passed,
            "fixtures_failed": len(cases) - passed,
            "duration_seconds": round(time.monotonic() - started, 3),
        },
        "cases": cases,
    }
    if base_sha is not None:
        report["base_sha"] = base_sha
    if head_sha is not None:
        report["head_sha"] = head_sha
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixtures", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--base-sha", required=True)
    parser.add_argument("--head-sha", required=True)
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT_SECONDS)
    parser.add_argument("--observer-command", nargs="+",
                        help="trusted host adapter for independent tests and tool trajectory")
    parser.add_argument("--skills-root", type=Path)
    parser.add_argument("--command", nargs=argparse.REMAINDER, required=True)
    args = parser.parse_args()
    command = list(args.command)
    if command[:1] == ["--"]:
        command = command[1:]
    if not command:
        print("ERROR: worker command is required", flush=True)
        return 2
    try:
        report = run_suite(args.fixtures.resolve(), command, args.timeout,
                           args.base_sha, args.head_sha, args.observer_command, args.skills_root)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    except (OSError, RuntimeError, ValueError, TypeError) as exc:
        print(f"ERROR: meta-test failed: {type(exc).__name__}", flush=True)
        return 2
    print(
        f"meta_test: {report['status']} "
        f"{report['metrics']['fixtures_passed']}/{report['metrics']['fixtures_total']} fixtures"
    )
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
