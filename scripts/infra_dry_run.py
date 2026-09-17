#!/usr/bin/env python3
"""Run an explicit infrastructure dry-run profile in a clean candidate tree.

Infrastructure changes are classified as requiring ``infra-dry-run``. This
producer makes that obligation executable without inventing a cloud provider:
it detects infrastructure paths, archives the committed candidate, and runs a
caller-supplied argv profile without a shell. Non-infrastructure candidates
emit ``not_applicable`` and do not create a receipt gate obligation.

Exit codes: 0 pass/not_applicable, 1 failed or unavailable dry-run, 2 invalid input.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import tarfile
import tempfile
import time
from io import BytesIO
from pathlib import Path

SCHEMA_VERSION = 1
FULL_SHA = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")
INFRA_PATTERNS = (
    re.compile(r"(^|/)(infra|terraform|helm|charts|ansible|playbooks|fleet|rancher|nexus)(/|$)", re.I),
    re.compile(r"\.(tf|tfvars)$", re.I),
)


def _validate_sha(value: str, label: str) -> None:
    if not FULL_SHA.fullmatch(value):
        raise ValueError(f"{label} must be a full hexadecimal commit SHA")


def changed_files(repo: Path, base_sha: str, head_sha: str) -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--name-only", f"{base_sha}..{head_sha}"],
        cwd=repo, capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    if result.returncode != 0:
        raise RuntimeError("could not inspect candidate diff")
    return sorted(line for line in result.stdout.splitlines() if line)


def infra_files(paths: list[str]) -> list[str]:
    return sorted(path for path in paths if any(pattern.search(path) for pattern in INFRA_PATTERNS))


def _clean_workspace(repo: Path, head_sha: str) -> Path:
    raw = tempfile.mkdtemp(prefix="pipeline-infra-")
    workspace = Path(raw)
    archive = subprocess.run(
        ["git", "archive", "--format=tar", head_sha],
        cwd=repo, capture_output=True, timeout=60,
    )
    if archive.returncode != 0:
        raise RuntimeError("could not archive candidate HEAD")
    with tarfile.open(fileobj=BytesIO(archive.stdout), mode="r:") as bundle:
        bundle.extractall(workspace, filter="data")
    return workspace


def run_dry_run(repo: Path, task_id: str, base_sha: str, head_sha: str,
                command: list[str] | None = None, timeout_seconds: int = 900) -> dict:
    _validate_sha(base_sha, "base_sha")
    _validate_sha(head_sha, "head_sha")
    paths = changed_files(repo, base_sha, head_sha)
    infra = infra_files(paths)
    report = {
        "schema_version": SCHEMA_VERSION,
        "gate": "infra-dry-run",
        "task": task_id,
        "base_sha": base_sha,
        "head_sha": head_sha,
        "status": "not_applicable" if not infra else "error",
        "changed_infra_files": infra,
        "isolated": bool(infra),
        "command": list(command or []),
        "metrics": {"changed_infra_file_count": len(infra)},
    }
    if not infra:
        return report
    if not command:
        report["error"] = "infra changes require an explicit dry-run command profile"
        return report
    started = time.monotonic()
    workspace = None
    try:
        workspace = _clean_workspace(repo, head_sha)
        env = dict(os.environ)
        env.update({"CI": "1", "TF_IN_AUTOMATION": "1"})
        result = subprocess.run(
            command, cwd=workspace, env=env, capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=timeout_seconds,
        )
        report["status"] = "pass" if result.returncode == 0 else "fail"
        report["metrics"].update({
            "exit_code": result.returncode,
            "duration_seconds": round(time.monotonic() - started, 3),
            "stdout_bytes": len(result.stdout.encode("utf-8")),
            "stderr_bytes": len(result.stderr.encode("utf-8")),
        })
    except subprocess.TimeoutExpired:
        report["status"] = "error"
        report["error"] = "dry-run timed out"
        report["metrics"]["duration_seconds"] = round(time.monotonic() - started, 3)
    except (OSError, RuntimeError, tarfile.TarError) as exc:
        report["status"] = "error"
        report["error"] = "dry-run workspace failed: " + type(exc).__name__
    finally:
        if workspace is not None:
            import shutil
            shutil.rmtree(workspace, ignore_errors=True)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("task_id")
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--base-sha", required=True)
    parser.add_argument("--head-sha", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--timeout", type=int, default=900)
    parser.add_argument("--command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    try:
        report = run_dry_run(args.repo.resolve(), args.task_id, args.base_sha,
                             args.head_sha, args.command or None, args.timeout)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    except (OSError, RuntimeError, TypeError, ValueError):
        print("ERROR: infra dry-run could not run", flush=True)
        return 2
    print(f"infra_dry_run: status={report['status']}")
    return 0 if report["status"] in {"pass", "not_applicable"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
