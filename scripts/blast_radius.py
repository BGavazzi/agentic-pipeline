#!/usr/bin/env python3
"""
blast_radius.py — diff-scoped blast-radius + risk-tier classifier

Purpose: deterministic gate between Builder and Tester/Ultrareview. Computes,
from a git diff, which modules are plausibly affected and what risk tier the
change falls into, then emits which downstream gates are required —
tester/ultrareview read this artifact instead of guessing scope themselves
(same anti-fake-green principle as validate_task.py / validate_closure.py:
gate on an artifact, not on the model's self-report of what it considered).

This is deliberately IMPRECISE — it unions three cheap heuristics rather than
building a real dependency graph (see .docs/tasks/0002-feat-blast-radius-risk-
classifier.md for the rationale). Each signal is individually sloppy; the
union converges to something usable without maintaining a graph tool.

Usage:
    python scripts/blast_radius.py <task_id> [--base REF] [--branch REF] [--repo PATH]
    python scripts/blast_radius.py 0021 --base main --branch feat/0021-x

    --base/--branch default to auto-detect (branch = current HEAD; base =
    first of integration/main/master that exists on origin).

Signals unioned into affected_modules:
    1. Ownership map (.docs/module-owners.md) — hand-maintained path-prefix ->
       owner tag + consumer prefixes. Missing/absent file = signal skipped,
       not an error (V1 default: repo hasn't authored one yet).
    2. Import/grep heuristic — literal "what references this changed file's
       name" across tracked files (no AST, no dependency graph).
    3. Historical co-change — files that have previously changed in the same
       commit as one of the diff's files (last COCHANGE_HISTORY_LIMIT commits
       touching those files), above a minimum co-occurrence count.

Risk tier (single source of truth — ultrareview/dispatcher should read
`risk_level` from this artifact rather than recomputing it inline):
    - high:   diff touches a high-risk path pattern (auth/RBAC, migrations,
              payments/billing, infra manifests: Ansible/Helm/Fleet/Terraform/
              Rancher/Nexus) OR affected_modules spans more than
              WIDE_BLAST_RADIUS_THRESHOLD entries
    - medium: affected_modules non-empty (touches shared code) but no
              high-risk pattern and under the wide-blast-radius threshold
    - low:    no consumers found, no high-risk pattern (isolated/leaf change)

Output: .docs/blast-reports/<task_id>.json
Exit codes: 0 = classified OK, 2 = usage/git error. This script does not
pass/fail a change — required_gates is what downstream skills act on.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

WIDE_BLAST_RADIUS_THRESHOLD = 8
COCHANGE_HISTORY_LIMIT = 200  # commits scanned per changed file, perf cap
COCHANGE_MIN_COUNT = 2  # min co-occurrences before a file counts as coupled
BASE_CANDIDATES = ["integration", "main", "master"]

HIGH_RISK_PATH_PATTERNS = [
    (r"(^|/)auth[/_.-]", "auth"),
    (r"(^|/)rbac[/_.-]", "rbac"),
    (r"(^|/)permission", "permissions"),
    (r"(^|/)migrat", "migration"),
    (r"\.sql$", "sql-migration"),
    (r"(^|/)(payment|billing)[/_.-]", "payments"),
    (r"(^|/)(ansible|playbooks?)[/_.-].*\.ya?ml$", "ansible"),
    (r"(^|/)(helm|charts?)[/_.-].*\.ya?ml$", "helm"),
    (r"(^|/)fleet[/_.-].*\.ya?ml$", "fleet"),
    (r"(^|/)(terraform|\.tf)$", "terraform"),
    (r"(^|/)(rancher|nexus)[/_.-]", "rancher-or-nexus"),
]


def run(args: list[str], cwd: Path) -> str:
    result = subprocess.run(
        args, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    if result.returncode != 0:
        raise RuntimeError(f"git command failed: {' '.join(args)}\n{result.stderr}")
    return result.stdout


def detect_base(repo: Path, explicit: str | None) -> str:
    if explicit:
        return explicit
    for candidate in BASE_CANDIDATES:
        try:
            out = run(["git", "ls-remote", "--heads", "origin", candidate], cwd=repo)
        except RuntimeError:
            continue  # no origin remote (e.g. local sandbox) — try next candidate
        if out.strip():
            return candidate
    # No remote, or none of the candidates exist there — fall back to whatever
    # local branches actually exist (sandbox/offline case).
    local_branches = run(["git", "branch", "--format=%(refname:short)"], cwd=repo).split()
    for candidate in BASE_CANDIDATES:
        if candidate in local_branches:
            return candidate
    return "master"


def detect_branch(repo: Path, explicit: str | None) -> str:
    if explicit:
        return explicit
    return run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=repo).strip()


def changed_files(repo: Path, base: str, branch: str) -> list[str]:
    merge_base_ref = f"origin/{base}" if base not in ("HEAD",) else base
    try:
        out = run(["git", "diff", "--name-only", f"{merge_base_ref}...{branch}"], cwd=repo)
    except RuntimeError:
        # Fall back to local base ref (no origin remote / not fetched)
        out = run(["git", "diff", "--name-only", f"{base}...{branch}"], cwd=repo)
    return [line.strip() for line in out.splitlines() if line.strip()]


@dataclass
class OwnerRule:
    prefix: str
    owner: str
    consumers: list[str] = field(default_factory=list)


def load_ownership_map(repo: Path) -> list[OwnerRule]:
    """Parse .docs/module-owners.md — a markdown table:
    | Path prefix | Owner tag | Consumers (comma-separated path prefixes) |
    Missing file → empty list (signal skipped, not an error).
    """
    path = repo / ".docs" / "module-owners.md"
    if not path.exists():
        return []
    rules: list[OwnerRule] = []
    row_pat = re.compile(r"^\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.*?)\s*\|\s*$")
    for line in path.read_text(encoding="utf-8").splitlines():
        m = row_pat.match(line)
        if not m:
            continue
        prefix, owner, consumers_raw = m.groups()
        if prefix.lower() in ("path prefix", "---") or set(prefix) <= {"-", " "}:
            continue
        consumers = [c.strip() for c in consumers_raw.split(",") if c.strip()]
        rules.append(OwnerRule(prefix=prefix, owner=owner, consumers=consumers))
    return rules


def ownership_signal(changed: list[str], rules: list[OwnerRule]) -> set[str]:
    hits: set[str] = set()
    for f in changed:
        for rule in rules:
            if f.startswith(rule.prefix):
                hits.add(rule.owner)
                hits.update(rule.consumers)
    return hits


def import_grep_signal(repo: Path, changed: list[str]) -> set[str]:
    """Cheap 'what references this changed file's name' — literal grep on the
    file's stem across tracked files, no AST/dependency graph."""
    hits: set[str] = set()
    try:
        tracked = run(["git", "ls-files"], cwd=repo).splitlines()
    except RuntimeError:
        return hits
    changed_set = set(changed)
    for f in changed:
        stem = Path(f).stem
        if len(stem) < 3:
            continue  # too short, would match noise
        pattern = re.compile(re.escape(stem))
        for candidate in tracked:
            if candidate in changed_set or candidate == f:
                continue
            fp = repo / candidate
            if not fp.is_file():
                continue
            try:
                text = fp.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            if pattern.search(text):
                hits.add(candidate)
    return hits


def cochange_signal(repo: Path, changed: list[str]) -> set[str]:
    """Files that historically changed together with one of the diff's files,
    above COCHANGE_MIN_COUNT co-occurrences, over the last COCHANGE_HISTORY_LIMIT
    commits touching each file.

    Two-step on purpose: `git log -- <path> --name-only` restricts the file
    list to that same pathspec (it won't show co-changed files at all), so we
    first collect the commit SHAs that touched each changed file, then ask
    each commit for its FULL file list via `diff-tree` (no pathspec).
    """
    changed_set = set(changed)
    commit_shas: set[str] = set()
    for f in changed:
        try:
            out = run(
                ["git", "log", f"-{COCHANGE_HISTORY_LIMIT}", "--format=%H", "--", f],
                cwd=repo,
            )
        except RuntimeError:
            continue
        commit_shas.update(sha.strip() for sha in out.splitlines() if sha.strip())

    counter: Counter[str] = Counter()
    for sha in commit_shas:
        try:
            out = run(["git", "diff-tree", "--no-commit-id", "--name-only", "-r", sha], cwd=repo)
        except RuntimeError:
            continue
        for other in (l.strip() for l in out.splitlines() if l.strip()):
            if other not in changed_set:
                counter[other] += 1
    return {f for f, count in counter.items() if count >= COCHANGE_MIN_COUNT}


def classify_risk(changed: list[str], affected_modules: set[str]) -> tuple[str, list[str]]:
    triggered: list[str] = []
    for pattern, label in HIGH_RISK_PATH_PATTERNS:
        rx = re.compile(pattern, re.IGNORECASE)
        if any(rx.search(f) for f in changed):
            triggered.append(label)

    if triggered:
        return "high", triggered
    if len(affected_modules) > WIDE_BLAST_RADIUS_THRESHOLD:
        return "high", ["wide-blast-radius"]
    if affected_modules:
        return "medium", []
    return "low", []


def required_gates_for(risk_level: str, triggered: list[str]) -> list[str]:
    if risk_level == "low":
        return ["unit"]
    if risk_level == "medium":
        return ["unit", "integration", "sast", "sca"]
    # high
    gates = ["unit", "integration", "sast", "sca", "ultrareview"]
    infra_labels = {"ansible", "helm", "fleet", "terraform", "rancher-or-nexus"}
    if infra_labels & set(triggered):
        gates.append("infra-dry-run")
    return gates


def classify(repo: Path, task_id: str, base: str | None, branch: str | None) -> dict:
    resolved_branch = detect_branch(repo, branch)
    resolved_base = detect_base(repo, base)
    changed = changed_files(repo, resolved_base, resolved_branch)

    rules = load_ownership_map(repo)
    affected = set()
    affected |= ownership_signal(changed, rules)
    affected |= import_grep_signal(repo, changed)
    affected |= cochange_signal(repo, changed)
    # Don't count the changed files themselves as "affected consumers"
    affected -= set(changed)

    risk_level, triggered = classify_risk(changed, affected)
    gates = required_gates_for(risk_level, triggered)

    return {
        "task": task_id,
        "base": resolved_base,
        "branch": resolved_branch,
        "changed_files": sorted(changed),
        "affected_modules": sorted(affected),
        "risk_level": risk_level,
        "risk_triggers": triggered,
        "required_gates": gates,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("task_id", help="Task NNNN id, used to name the output artifact")
    parser.add_argument("--base", default=None, help="Base ref (default: auto-detect)")
    parser.add_argument("--branch", default=None, help="Branch ref (default: current HEAD)")
    parser.add_argument("--repo", default=".", help="Repo path (default: cwd)")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    if not (repo / ".git").exists():
        print(f"ERROR: {repo} is not a git repo root", file=sys.stderr)
        return 2

    try:
        result = classify(repo, args.task_id, args.base, args.branch)
    except RuntimeError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2

    out_dir = repo / ".docs" / "blast-reports"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{args.task_id}.json"
    out_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")

    print(f"blast_radius: task {args.task_id} -> risk={result['risk_level']} "
          f"gates={result['required_gates']}")
    print(f"  changed_files: {len(result['changed_files'])}")
    print(f"  affected_modules: {len(result['affected_modules'])}")
    if result["risk_triggers"]:
        print(f"  triggers: {', '.join(result['risk_triggers'])}")
    print(f"  artifact: {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
