#!/usr/bin/env python3
"""Validate a versioned intent/authorization contract against a Git diff.

This gate checks whether the changed tree stays inside the agent's declared
scope and whether its declared effects/data classes have the required negative
evidence. It does not infer business authorization, inspect runtime traffic,
or treat a candidate-authored intent as trusted approval; the resulting report
is evidence for the existing admission and human-review layers.
"""
from __future__ import annotations

import argparse
import fnmatch
import json
import re
import subprocess
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
INTENT_VERSION = 1
TASK_ID = re.compile(r"^[0-9]{4}$")
SHA = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")
SENSITIVE_DATA_CLASSES = {"credentials", "personal-data", "financial-data", "health-data", "production-data"}
SENSITIVE_EFFECTS = {"authz-change", "data-access", "external-write", "secret-use", "deploy"}


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(["git", *args], cwd=repo, capture_output=True,
                            text=True, encoding="utf-8", errors="replace")
    if result.returncode != 0:
        raise RuntimeError(f"git command failed: {' '.join(args)}")
    return result.stdout.strip()


def _sha(repo: Path, ref: str) -> str:
    value = _git(repo, "rev-parse", "--verify", "--end-of-options", ref + "^{commit}")
    if not SHA.fullmatch(value):
        raise ValueError("resolved ref is not a full commit SHA")
    return value


def changed_files(repo: Path, base: str, head: str) -> list[str]:
    return sorted(path for path in _git(repo, "diff", "--name-only", f"{base}...{head}").splitlines() if path)


def _list(value: Any, name: str) -> list[str]:
    if not isinstance(value, list) or not value or any(not isinstance(item, str) or not item for item in value):
        raise ValueError(f"{name} must be a non-empty string list")
    return value


def _optional_list(value: Any, name: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list) or any(not isinstance(item, str) or not item for item in value):
        raise ValueError(f"{name} must be a string list")
    return value


def _matches(path: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatchcase(path, pattern) for pattern in patterns)


def _negative_tests(intent: dict[str, Any]) -> list[dict[str, Any]]:
    raw = intent.get("negative_tests", [])
    if not isinstance(raw, list):
        raise ValueError("negative_tests must be a list")
    result: list[dict[str, Any]] = []
    for item in raw:
        if not isinstance(item, dict) or not isinstance(item.get("name"), str):
            raise ValueError("negative_tests entries require a name")
        result.append(item)
    return result


def evaluate(intent: dict[str, Any], repo: Path, base: str, head: str) -> dict[str, Any]:
    if intent.get("schema_version") != SCHEMA_VERSION or intent.get("intent_version") != INTENT_VERSION:
        raise ValueError("unsupported intent schema/version")
    task_id = intent.get("task_id")
    if not isinstance(task_id, str) or not TASK_ID.fullmatch(task_id):
        raise ValueError("task_id must be a four-digit string")
    allowed_paths = _list(intent.get("allowed_paths"), "allowed_paths")
    forbidden_paths = _optional_list(intent.get("forbidden_paths"), "forbidden_paths")
    allowed_effects = _list(intent.get("allowed_effects"), "allowed_effects")
    declared_effects = _optional_list(intent.get("declared_effects"), "declared_effects")
    allowed_data_classes = _list(intent.get("allowed_data_classes"), "allowed_data_classes")
    data_classes = _optional_list(intent.get("data_classes"), "data_classes")
    forbidden_effects = _optional_list(intent.get("forbidden_effects"), "forbidden_effects")
    negative_tests = _negative_tests(intent)
    observed_effects = _optional_list(intent.get("observed_effects"), "observed_effects")
    base_sha, head_sha = _sha(repo, base), _sha(repo, head)
    changed = changed_files(repo, base_sha, head_sha)
    blockers: list[dict[str, str]] = []

    outside_scope = [path for path in changed if not _matches(path, allowed_paths)]
    if outside_scope:
        blockers.append({"code": "path-outside-scope", "detail": ", ".join(outside_scope)})
    forbidden = [path for path in changed if _matches(path, forbidden_paths)]
    if forbidden:
        blockers.append({"code": "forbidden-path", "detail": ", ".join(forbidden)})
    undeclared = sorted(set(declared_effects) - set(allowed_effects))
    if undeclared:
        blockers.append({"code": "effect-not-allowed", "detail": ", ".join(undeclared)})
    observed_not_allowed = sorted(set(observed_effects) - set(allowed_effects))
    if observed_not_allowed:
        blockers.append({"code": "observed-effect-not-allowed", "detail": ", ".join(observed_not_allowed)})
    observed_forbidden = sorted(set(observed_effects) & set(forbidden_effects))
    if observed_forbidden:
        blockers.append({"code": "forbidden-effect-observed", "detail": ", ".join(observed_forbidden)})
    unapproved_data = sorted(set(data_classes) - set(allowed_data_classes))
    if unapproved_data:
        blockers.append({"code": "data-class-not-allowed", "detail": ", ".join(unapproved_data)})

    sensitive = set(data_classes) & SENSITIVE_DATA_CLASSES or set(declared_effects) & SENSITIVE_EFFECTS
    if sensitive:
        if not negative_tests:
            blockers.append({"code": "negative-tests-missing", "detail": "sensitive intent requires negative tests"})
        elif any(item.get("status") != "pass" for item in negative_tests):
            blockers.append({"code": "negative-test-failed", "detail": "all negative tests must pass"})

    return {
        "schema_version": SCHEMA_VERSION, "intent_version": INTENT_VERSION,
        "task_id": task_id, "base_sha": base_sha, "head_sha": head_sha,
        "changed_files": changed, "metrics": {
            "changed_file_count": len(changed), "outside_scope_count": len(outside_scope),
            "forbidden_path_count": len(forbidden), "declared_effect_count": len(declared_effects),
            "data_class_count": len(data_classes), "negative_test_count": len(negative_tests),
        },
        "blockers": blockers, "eligible": not blockers,
        "human_review_required": True,
        "policy": {"candidate_authored_claim_is_untrusted": True,
                   "evidence_only": True, "no_remote_write": True},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--intent", type=Path, required=True)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--base", required=True)
    parser.add_argument("--head", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        intent = json.loads(args.intent.read_text(encoding="utf-8"))
        if not isinstance(intent, dict):
            raise ValueError("intent must be a JSON object")
        report = evaluate(intent, args.repo.resolve(), args.base, args.head)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    except (OSError, RuntimeError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: intent gate failed: {type(exc).__name__}")
        return 2
    print(f"intent_gate: eligible={report['eligible']} blockers={len(report['blockers'])}")
    return 0 if report["eligible"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
