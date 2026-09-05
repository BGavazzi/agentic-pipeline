#!/usr/bin/env python3
"""
scan_gate.py — deterministic SAST/SCA/secret-scan gate (task 0001)

Purpose: the deterministic half of the "replace paid CodeRabbit/SonarQube"
plan (see .docs/tasks/0001-feat-oss-static-analysis-gate.md). tester (build/
lint/unit tests) and ultrareview (semantic/adversarial review) can both pass
while a diff introduces a known-vulnerable dependency, a hardcoded secret, or
an unsafe pattern (SQL string concat, unsafe deserialization) — none of which
either of those checks for. This script closes that gap with four scanners,
run as Docker images (BYO footprint = "has Docker," not four separate
package-manager installs — verified via a real smoke test, see task 0001's
Context):

    - Semgrep      (semgrep/semgrep)            — SAST
    - Trivy        (aquasec/trivy)               — SCA + secrets + misconfig
    - gitleaks     (ghcr.io/gitleaks/gitleaks)   — dedicated secret scan
    - OWASP Dependency-Check (owasp/dependency-check) — SCA fallback/complement,
      OPT-IN ONLY (--enable-dependency-check): its NVD database needs an API
      key to sync at a usable speed, and this repo hasn't done that sync yet
      (task 0001's Context) — never auto-run something that slow/rate-limited
      without the caller explicitly asking for it.

Same anti-fake-green principle as validate_task.py / blast_radius.py /
validate_closure.py: gate on an artifact, never on a model's self-report.
A missing scanner (no Docker, image not pulled) DEGRADES the run (skip +
record why) rather than fabricating a pass — mirrors tester's fe_real
"prerequisite absent -> degrade to build+lint + warn" rule exactly.

Severity policy (V1, deliberately simple — see Honest Backlog in task 0001):
a `critical`/`high` finding whose file appears in the diff's changed-file set
counts as INTRODUCED and fails the gate. A finding whose file is NOT in the
changed-file set is treated as PRE-EXISTING and never fails the gate on its
own — this is an approximation (the file could have been already-vulnerable
before this branch touched it, and a comment-only edit still counts the whole
file as "changed"), not a true base-vs-branch differential scan. A true
differential would re-run every scanner against the base ref too; that's V2
(see this script's module docstring in the repo's CHANGELOG/task 0001 for
the exact tradeoff). `medium`/`low` findings are warnings only in V1,
regardless of introduced/pre-existing.

Usage:
    python scripts/scan_gate.py <task_id> [--base REF] [--branch REF]
                                [--repo PATH] [--enable-dependency-check]

Output:
    .docs/scan-reports/<task_id>.sarif  — normalized SARIF 2.1.0, all tools' runs
    .docs/scan-reports/<task_id>.json   — verdict + per-tool status + counts
                                           (this is what tester/dispatcher gate on)

Exit codes:
    0 -- pass (no introduced critical/high finding) — includes "degraded" runs
         where every scanner was skipped (never claims a positive pass in that
         case; the JSON artifact's "degraded": true is the tell)
    1 -- BLOCK: at least one introduced critical/high finding
    2 -- usage error (bad --repo path) or a scanner produced unparseable
         output that isn't itself a "scanner unavailable" case (a real bug in
         the invocation, not a missing prerequisite)

Part of the agentic-pipeline core scripts (sibling of blast_radius.py, whose
git-diff helpers this script reuses rather than re-deriving them).
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

# Reuse blast_radius.py's git-diff helpers (detect_base/detect_branch/
# changed_files/run) instead of re-deriving them — same repo state, same
# base/branch auto-detection rules. Loaded by path (not `import blast_radius`)
# so this script works whether or not scripts/ is on sys.path — same pattern
# tests/test_blast_radius.py already uses to load its own target module.
_BLAST_RADIUS_PATH = Path(__file__).resolve().parent / "blast_radius.py"
_spec = importlib.util.spec_from_file_location("blast_radius", _BLAST_RADIUS_PATH)
blast_radius = importlib.util.module_from_spec(_spec)
sys.modules.setdefault("blast_radius", blast_radius)  # dataclass() needs this registered first
_spec.loader.exec_module(blast_radius)  # type: ignore[union-attr]

DOCKER_TIMEOUT_SECONDS = 300  # per-tool cap; a hung scanner shouldn't hang the gate forever

SEVERITY_ORDER = ["critical", "high", "medium", "low", "unknown"]
SARIF_LEVEL = {"critical": "error", "high": "error", "medium": "warning", "low": "note", "unknown": "note"}


@dataclass
class ScanFinding:
    tool: str
    rule_id: str
    severity: str  # normalized: critical | high | medium | low | unknown
    file: str
    line: int | None
    message: str


@dataclass
class ToolRun:
    tool: str
    status: str  # "ok" | "skipped" | "error"
    reason: str | None = None
    findings: list[ScanFinding] = field(default_factory=list)


@dataclass
class DockerResult:
    stdout: str
    stderr: str
    returncode: int


def _stderr_tail(stderr: str, max_chars: int = 500) -> str:
    """Last `max_chars` of stderr, stripped — enough to see a real scanner
    error (DB pull failure, auth, OOM) without dumping a whole crash log into
    a ToolRun.reason that's meant to be read at a glance."""
    stderr = stderr.strip()
    if not stderr:
        return ""
    return stderr[-max_chars:]


# ---------------------------------------------------------------------------
# Availability checks (kept as standalone functions so tests can monkeypatch
# them directly, instead of mocking subprocess calls all the way down).
# ---------------------------------------------------------------------------

def check_docker_available() -> bool:
    if shutil.which("docker") is None:
        return False
    try:
        result = subprocess.run(
            ["docker", "info"], capture_output=True, text=True, timeout=10,
        )
    except (subprocess.TimeoutExpired, OSError):
        return False
    return result.returncode == 0


# ---------------------------------------------------------------------------
# Per-tool invocation. Each returns raw stdout (str) or raises RuntimeError on
# a genuine invocation failure (docker present but the run itself errored in
# a way that isn't just "found findings" — see note below on exit codes).
# ---------------------------------------------------------------------------

def _docker_run(
    image: str, args: list[str], repo: Path,
    extra_mounts: list[tuple[Path, str]] | None = None,
) -> DockerResult:
    """Run `docker run --rm -v <repo>:/src <image> <args>`, capturing both
    stdout and stderr.

    Scanners commonly exit non-zero when they FOUND something (that's not an
    invocation error) — so this only raises when docker itself couldn't be
    invoked at all; a non-zero exit is still returned as a DockerResult for
    the caller to parse (or fail to parse, with stderr available to explain
    why — see run_all_scanners).

    `extra_mounts` bind-mounts additional host dirs (created if missing) —
    used by run_trivy() to make its vulnerability DB cache persistent across
    invocations instead of re-downloading it fresh every `docker run --rm`
    (task 0007: the leading hypothesis for a trivy run that produced empty
    stdout on its first-ever live CI invocation).
    """
    cmd = ["docker", "run", "--rm", "-v", f"{repo}:/src"]
    for host_path, container_path in extra_mounts or []:
        host_path.mkdir(parents=True, exist_ok=True)
        cmd += ["-v", f"{host_path}:{container_path}"]
    cmd += [image, *args]
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=DOCKER_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as e:
        raise RuntimeError(f"timed out after {DOCKER_TIMEOUT_SECONDS}s: {' '.join(cmd)}") from e
    except OSError as e:
        raise RuntimeError(f"failed to invoke docker: {e}") from e
    return DockerResult(stdout=result.stdout, stderr=result.stderr, returncode=result.returncode)


def run_semgrep(repo: Path, targets: list[str]) -> DockerResult:
    return _docker_run("semgrep/semgrep", ["semgrep", "--config", "auto", "--json", *targets], repo)


def run_trivy(repo: Path, targets: list[str]) -> DockerResult:
    scan_targets = targets or ["."]
    # Trivy's own default cache dir inside the image is /root/.cache/trivy.
    # Bind-mounting a host dir there (TRIVY_CACHE_DIR, defaulting to a repo-
    # local .trivy-cache/ so it's easy to .gitignore and to key an
    # actions/cache step on in CI) means the vulnerability DB survives across
    # `docker run --rm` invocations instead of being pulled from scratch
    # every time — see task 0007.
    cache_dir = Path(os.environ.get("TRIVY_CACHE_DIR", repo / ".trivy-cache"))
    return _docker_run(
        "aquasec/trivy",
        ["fs", "--scanners", "vuln,secret,misconfig", "--format", "json",
         "--cache-dir", "/root/.cache/trivy", *scan_targets],
        repo,
        extra_mounts=[(cache_dir, "/root/.cache/trivy")],
    )


def run_gitleaks(repo: Path, targets: list[str]) -> DockerResult:
    # gitleaks scans a source tree, not individual files — point it at /src
    # regardless of `targets`; findings are filtered to changed files later
    # via the same introduced/pre-existing logic as every other tool.
    return _docker_run(
        "ghcr.io/gitleaks/gitleaks",
        ["detect", "--source", "/src", "--no-git", "--report-format", "json", "--report-path", "/dev/stdout"],
        repo,
    )


def run_dependency_check(repo: Path, task_id: str) -> DockerResult:
    return _docker_run(
        "owasp/dependency-check",
        ["--scan", "/src", "--format", "JSON", "--out", "/src", "--project", task_id],
        repo,
    )


# ---------------------------------------------------------------------------
# Parsers — pure functions, each takes raw tool JSON and returns normalized
# findings. Kept separate from invocation so tests exercise them with canned
# fixture strings instead of needing a live scanner.
# ---------------------------------------------------------------------------

def parse_semgrep(raw: str) -> list[ScanFinding]:
    data = json.loads(raw)
    sev_map = {"ERROR": "high", "WARNING": "medium", "INFO": "low"}
    findings = []
    for r in data.get("results", []):
        extra = r.get("extra", {})
        findings.append(ScanFinding(
            tool="semgrep",
            rule_id=r.get("check_id", "unknown"),
            severity=sev_map.get(extra.get("severity", ""), "unknown"),
            file=r.get("path", "unknown"),
            line=(r.get("start", {}) or {}).get("line"),
            message=extra.get("message", ""),
        ))
    return findings


def parse_trivy(raw: str) -> list[ScanFinding]:
    data = json.loads(raw)
    sev_map = {"CRITICAL": "critical", "HIGH": "high", "MEDIUM": "medium", "LOW": "low"}
    findings = []
    for result in data.get("Results", []) or []:
        target = result.get("Target", "unknown")
        for v in result.get("Vulnerabilities", []) or []:
            findings.append(ScanFinding(
                tool="trivy", rule_id=v.get("VulnerabilityID", "unknown"),
                severity=sev_map.get(v.get("Severity", ""), "unknown"),
                file=target, line=None,
                message=v.get("Title") or v.get("Description", ""),
            ))
        for s in result.get("Secrets", []) or []:
            findings.append(ScanFinding(
                tool="trivy", rule_id=s.get("RuleID", "unknown"),
                severity=sev_map.get(s.get("Severity", ""), "critical"),
                file=target, line=s.get("StartLine"),
                message=s.get("Title", "secret detected"),
            ))
        for m in result.get("Misconfigurations", []) or []:
            findings.append(ScanFinding(
                tool="trivy", rule_id=m.get("ID", "unknown"),
                severity=sev_map.get(m.get("Severity", ""), "unknown"),
                file=target, line=None,
                message=m.get("Title", ""),
            ))
    return findings


def parse_gitleaks(raw: str) -> list[ScanFinding]:
    raw = raw.strip()
    if not raw:
        return []  # gitleaks emits nothing on stdout when no leaks are found
    data = json.loads(raw)
    findings = []
    for item in data:
        findings.append(ScanFinding(
            tool="gitleaks", rule_id=item.get("RuleID", "unknown"),
            severity="critical",  # a leaked secret is never "low" (see module docstring)
            file=item.get("File", "unknown"), line=item.get("StartLine"),
            message=item.get("Description", "secret detected"),
        ))
    return findings


def parse_dependency_check(raw: str) -> list[ScanFinding]:
    data = json.loads(raw)
    sev_map = {"CRITICAL": "critical", "HIGH": "high", "MEDIUM": "medium", "LOW": "low"}
    findings = []
    for dep in data.get("dependencies", []) or []:
        file_name = dep.get("fileName", "unknown")
        for v in dep.get("vulnerabilities", []) or []:
            severity = v.get("severity", "")
            findings.append(ScanFinding(
                tool="dependency-check", rule_id=v.get("name", "unknown"),
                severity=sev_map.get(severity.upper(), "unknown"), file=file_name, line=None,
                message=v.get("description", ""),
            ))
    return findings


PARSERS = {
    "semgrep": parse_semgrep,
    "trivy": parse_trivy,
    "gitleaks": parse_gitleaks,
    "dependency-check": parse_dependency_check,
}


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def run_all_scanners(
    repo: Path, changed: list[str], docker_available: bool, enable_dependency_check: bool,
    task_id: str = "adhoc",
) -> list[ToolRun]:
    runs: list[ToolRun] = []
    tools: list[tuple[str, object]] = [
        ("semgrep", lambda: run_semgrep(repo, changed)),
        ("trivy", lambda: run_trivy(repo, changed)),
        ("gitleaks", lambda: run_gitleaks(repo, changed)),
    ]
    if enable_dependency_check:
        tools.append(("dependency-check", lambda: run_dependency_check(repo, task_id)))

    for name, invoke in tools:
        if not docker_available:
            runs.append(ToolRun(tool=name, status="skipped", reason="docker unavailable"))
            continue
        try:
            docker_result = invoke()
        except RuntimeError as e:
            runs.append(ToolRun(tool=name, status="error", reason=str(e)))
            continue
        try:
            findings = PARSERS[name](docker_result.stdout)
        except json.JSONDecodeError as e:
            reason = f"unparseable output: {e}"
            tail = _stderr_tail(docker_result.stderr)
            if tail:
                reason += f" — stderr: {tail}"
            elif not docker_result.stdout.strip():
                reason += " (empty stdout, empty stderr too — exit code " \
                    f"{docker_result.returncode})"
            runs.append(ToolRun(tool=name, status="error", reason=reason))
            continue
        runs.append(ToolRun(tool=name, status="ok", findings=findings))
    return runs


def classify_gate(runs: list[ToolRun], changed: list[str]) -> dict:
    changed_set = set(changed)
    all_findings = [f for r in runs for f in r.findings]

    introduced = [f for f in all_findings if f.file in changed_set or f.file == "unknown"]
    introduced_blocking = [f for f in introduced if f.severity in ("critical", "high")]

    ran_ok = any(r.status == "ok" for r in runs)
    all_skipped = all(r.status == "skipped" for r in runs)

    if all_skipped:
        verdict = "degraded"
    elif introduced_blocking:
        verdict = "block"
    else:
        verdict = "pass"

    by_severity: dict[str, int] = {}
    for f in all_findings:
        by_severity[f.severity] = by_severity.get(f.severity, 0) + 1

    return {
        "verdict": verdict,
        "degraded": all_skipped,
        "ran_any_scanner": ran_ok,
        "findings_total": len(all_findings),
        "findings_introduced": len(introduced),
        "findings_introduced_blocking": len(introduced_blocking),
        "findings_by_severity": by_severity,
        "blocking_findings": [
            {"tool": f.tool, "rule_id": f.rule_id, "severity": f.severity, "file": f.file, "line": f.line,
             "message": f.message}
            for f in introduced_blocking
        ],
    }


def build_sarif(runs: list[ToolRun]) -> dict:
    sarif_runs = []
    for r in runs:
        results = []
        for f in r.findings:
            location = {"physicalLocation": {"artifactLocation": {"uri": f.file}}}
            if f.line is not None:
                location["physicalLocation"]["region"] = {"startLine": f.line}
            results.append({
                "ruleId": f.rule_id,
                "level": SARIF_LEVEL.get(f.severity, "note"),
                "message": {"text": f.message or f.rule_id},
                "locations": [location],
            })
        sarif_runs.append({
            "tool": {"driver": {"name": r.tool, "informationUri": "", "rules": []}},
            "invocations": [{
                "executionSuccessful": r.status != "error",
                **({"exitCodeDescription": r.reason} if r.reason else {}),
            }],
            "results": results,
        })
    return {
        "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
        "version": "2.1.0",
        "runs": sarif_runs,
    }


def scan(
    repo: Path, task_id: str, base: str | None, branch: str | None, enable_dependency_check: bool,
) -> tuple[dict, dict]:
    resolved_branch = blast_radius.detect_branch(repo, branch)
    resolved_base = blast_radius.detect_base(repo, base)
    changed = blast_radius.changed_files(repo, resolved_base, resolved_branch)

    docker_available = check_docker_available()
    runs = run_all_scanners(repo, changed, docker_available, enable_dependency_check, task_id)
    verdict_info = classify_gate(runs, changed)
    sarif = build_sarif(runs)

    summary = {
        "task": task_id,
        "base": resolved_base,
        "branch": resolved_branch,
        "changed_files": sorted(changed),
        "tool_status": {r.tool: {"status": r.status, "reason": r.reason} for r in runs},
        **verdict_info,
    }
    return summary, sarif


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("task_id", help="Task NNNN id, used to name the output artifact")
    parser.add_argument("--base", default=None, help="Base ref (default: auto-detect)")
    parser.add_argument("--branch", default=None, help="Branch ref (default: current HEAD)")
    parser.add_argument("--repo", default=".", help="Repo path (default: cwd)")
    parser.add_argument(
        "--enable-dependency-check", action="store_true",
        help="Also run OWASP Dependency-Check (opt-in: needs a synced NVD DB to be useful/fast)",
    )
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    if not (repo / ".git").exists():
        print(f"ERROR: {repo} is not a git repo root", file=sys.stderr)
        return 2

    try:
        summary, sarif = scan(repo, args.task_id, args.base, args.branch, args.enable_dependency_check)
    except RuntimeError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2

    out_dir = repo / ".docs" / "scan-reports"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"{args.task_id}.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    (out_dir / f"{args.task_id}.sarif").write_text(json.dumps(sarif, indent=2) + "\n", encoding="utf-8")

    print(f"scan_gate: task {args.task_id} -> verdict={summary['verdict']}"
          f"{' (DEGRADED - no scanner ran)' if summary['degraded'] else ''}")
    for tool, st in summary["tool_status"].items():
        line = f"  {tool}: {st['status']}"
        if st["reason"]:
            line += f" ({st['reason']})"
        print(line)
    print(f"  findings: {summary['findings_total']} total, "
          f"{summary['findings_introduced']} introduced, "
          f"{summary['findings_introduced_blocking']} blocking")
    print(f"  artifacts: {out_dir / f'{args.task_id}.json'}, {out_dir / f'{args.task_id}.sarif'}")

    if summary["verdict"] == "block":
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
