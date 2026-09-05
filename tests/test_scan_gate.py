"""
Unit tests for scripts/scan_gate.py.

Same rationale as test_blast_radius.py: scan_gate.py's OWN logic (severity
normalization, introduced-vs-pre-existing classification, SARIF assembly,
degrade-when-unavailable behavior) is deterministic and has no LLM reasoning
in it, so it gets a direct pytest unit test rather than a meta-test fixture.

What this suite does NOT cover, and why: it cannot invoke a real Semgrep/
Trivy/gitleaks/OWASP-Dependency-Check Docker container, because no CI
runner or dev sandbox this was written against had a reachable Docker daemon
at the time (see .agents/continuity-claude-code.md, 2026-07-11 entry, and
task 0001's Honest Backlog). Every parser is tested against a canned,
hand-written sample of that tool's real JSON output shape instead — this
proves the NORMALIZATION logic is correct, not that the live `docker run`
invocation string is. That remains open until someone runs this against a
real Docker host; tracked, not silently assumed away.

Run: pytest tests/test_scan_gate.py -v
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT_PATH = Path(__file__).resolve().parent.parent / "scripts" / "scan_gate.py"

spec = importlib.util.spec_from_file_location("scan_gate", SCRIPT_PATH)
scan_gate = importlib.util.module_from_spec(spec)
sys.modules["scan_gate"] = scan_gate
spec.loader.exec_module(scan_gate)


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-c", "user.email=test@test.local", "-c", "user.name=test",
         "-C", str(repo), *args],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    assert result.returncode == 0, f"git {args} failed: {result.stderr}"
    return result.stdout


def write(repo: Path, relpath: str, content: str) -> None:
    p = repo / relpath
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


@pytest.fixture
def sandbox(tmp_path: Path) -> Path:
    repo = tmp_path / "sandbox"
    repo.mkdir()
    git(repo, "init", "-q", "-b", "master")
    write(repo, "README.md", "seed\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "seed")
    return repo


# ---------------------------------------------------------------------------
# Parsers — canned real-shaped tool output
# ---------------------------------------------------------------------------

SEMGREP_SAMPLE = json.dumps({
    "results": [
        {
            "check_id": "python.lang.security.subprocess-shell-true",
            "path": "app/run.py",
            "start": {"line": 12},
            "extra": {"severity": "ERROR", "message": "subprocess with shell=True"},
        },
        {
            "check_id": "python.lang.best-practice.unused-import",
            "path": "app/util.py",
            "start": {"line": 1},
            "extra": {"severity": "INFO", "message": "unused import"},
        },
    ]
})


def test_parse_semgrep_normalizes_severity():
    findings = scan_gate.parse_semgrep(SEMGREP_SAMPLE)
    assert len(findings) == 2
    assert findings[0].severity == "high"
    assert findings[0].file == "app/run.py"
    assert findings[0].line == 12
    assert findings[1].severity == "low"


TRIVY_SAMPLE = json.dumps({
    "Results": [
        {
            "Target": "requirements.txt",
            "Vulnerabilities": [
                {"VulnerabilityID": "CVE-2024-0001", "Severity": "CRITICAL", "Title": "outdated pkg"},
            ],
            "Secrets": [
                {"RuleID": "aws-access-key", "Severity": "HIGH", "StartLine": 4, "Title": "AWS key"},
            ],
            "Misconfigurations": [
                {"ID": "AVD-DS-0002", "Severity": "MEDIUM", "Title": "root user in Dockerfile"},
            ],
        }
    ]
})


def test_parse_trivy_covers_vuln_secret_and_misconfig():
    findings = scan_gate.parse_trivy(TRIVY_SAMPLE)
    by_rule = {f.rule_id: f for f in findings}
    assert by_rule["CVE-2024-0001"].severity == "critical"
    assert by_rule["aws-access-key"].severity == "high"
    assert by_rule["aws-access-key"].line == 4
    assert by_rule["AVD-DS-0002"].severity == "medium"


def test_parse_gitleaks_empty_stdout_returns_no_findings():
    assert scan_gate.parse_gitleaks("") == []
    assert scan_gate.parse_gitleaks("   \n") == []


def test_parse_gitleaks_findings_are_always_critical():
    raw = json.dumps([{"RuleID": "generic-api-key", "File": "config.py", "StartLine": 8,
                        "Description": "possible API key"}])
    findings = scan_gate.parse_gitleaks(raw)
    assert len(findings) == 1
    assert findings[0].severity == "critical"
    assert findings[0].file == "config.py"


DEPENDENCY_CHECK_SAMPLE = json.dumps({
    "dependencies": [
        {
            "fileName": "package-lock.json",
            "vulnerabilities": [
                {"name": "CVE-2023-9999", "severity": "HIGH", "description": "known-vuln package"},
            ],
        }
    ]
})


def test_parse_dependency_check_normalizes_severity():
    findings = scan_gate.parse_dependency_check(DEPENDENCY_CHECK_SAMPLE)
    assert len(findings) == 1
    assert findings[0].severity == "high"
    assert findings[0].file == "package-lock.json"


# ---------------------------------------------------------------------------
# classify_gate — introduced vs. pre-existing, severity threshold
# ---------------------------------------------------------------------------

def _finding(**kwargs) -> "scan_gate.ScanFinding":
    defaults = dict(tool="semgrep", rule_id="r1", severity="high", file="app/x.py", line=1, message="m")
    defaults.update(kwargs)
    return scan_gate.ScanFinding(**defaults)


def _dr(stdout: str, stderr: str = "", returncode: int = 0) -> "scan_gate.DockerResult":
    return scan_gate.DockerResult(stdout=stdout, stderr=stderr, returncode=returncode)


def test_classify_gate_blocks_on_introduced_high_severity():
    runs = [scan_gate.ToolRun(tool="semgrep", status="ok", findings=[_finding(file="app/x.py")])]
    result = scan_gate.classify_gate(runs, changed=["app/x.py"])
    assert result["verdict"] == "block"
    assert result["findings_introduced_blocking"] == 1


def test_classify_gate_passes_when_finding_is_pre_existing():
    runs = [scan_gate.ToolRun(tool="semgrep", status="ok", findings=[_finding(file="app/other.py")])]
    result = scan_gate.classify_gate(runs, changed=["app/x.py"])
    assert result["verdict"] == "pass"
    assert result["findings_introduced_blocking"] == 0


def test_classify_gate_medium_introduced_does_not_block():
    runs = [scan_gate.ToolRun(tool="semgrep", status="ok",
                               findings=[_finding(file="app/x.py", severity="medium")])]
    result = scan_gate.classify_gate(runs, changed=["app/x.py"])
    assert result["verdict"] == "pass"
    assert result["findings_introduced"] == 1


def test_classify_gate_degraded_when_all_tools_skipped():
    runs = [
        scan_gate.ToolRun(tool="semgrep", status="skipped", reason="docker unavailable"),
        scan_gate.ToolRun(tool="trivy", status="skipped", reason="docker unavailable"),
    ]
    result = scan_gate.classify_gate(runs, changed=["app/x.py"])
    assert result["verdict"] == "degraded"
    assert result["degraded"] is True
    assert result["ran_any_scanner"] is False


# ---------------------------------------------------------------------------
# _docker_run — extra_mounts (task 0007: trivy DB cache persistence)
# ---------------------------------------------------------------------------

def test_docker_run_bind_mounts_extra_paths_and_creates_them(sandbox: Path, tmp_path: Path, monkeypatch):
    captured_cmd = {}

    def fake_run(cmd, **kwargs):
        captured_cmd["cmd"] = cmd
        return subprocess.CompletedProcess(cmd, returncode=0, stdout="{}", stderr="")

    monkeypatch.setattr(scan_gate.subprocess, "run", fake_run)
    cache_dir = tmp_path / "not-yet-created" / "trivy-cache"
    assert not cache_dir.exists()

    scan_gate._docker_run("some/image", ["scan"], sandbox, extra_mounts=[(cache_dir, "/root/.cache/trivy")])

    assert cache_dir.exists()  # created before the mount, not left for docker to fail on
    cmd = captured_cmd["cmd"]
    assert f"{cache_dir}:/root/.cache/trivy" in cmd
    assert f"{sandbox}:/src" in cmd


def test_run_trivy_mounts_a_cache_dir_by_default(sandbox: Path, monkeypatch):
    captured = {}
    monkeypatch.setattr(
        scan_gate, "_docker_run",
        lambda image, args, repo, extra_mounts=None: captured.update(
            image=image, args=args, extra_mounts=extra_mounts
        ) or scan_gate.DockerResult(stdout="{}", stderr="", returncode=0),
    )
    monkeypatch.delenv("TRIVY_CACHE_DIR", raising=False)

    scan_gate.run_trivy(sandbox, [])

    assert "--cache-dir" in captured["args"]
    assert captured["extra_mounts"][0][1] == "/root/.cache/trivy"
    assert captured["extra_mounts"][0][0] == sandbox / ".trivy-cache"


def test_run_trivy_honors_trivy_cache_dir_env_override(sandbox: Path, tmp_path: Path, monkeypatch):
    captured = {}
    monkeypatch.setattr(
        scan_gate, "_docker_run",
        lambda image, args, repo, extra_mounts=None: captured.update(extra_mounts=extra_mounts)
        or scan_gate.DockerResult(stdout="{}", stderr="", returncode=0),
    )
    override = tmp_path / "shared-trivy-cache"
    monkeypatch.setenv("TRIVY_CACHE_DIR", str(override))

    scan_gate.run_trivy(sandbox, [])

    assert captured["extra_mounts"][0][0] == override


# ---------------------------------------------------------------------------
# run_all_scanners — degrade path + per-tool error isolation
# ---------------------------------------------------------------------------

def test_run_all_scanners_degrades_when_docker_unavailable(sandbox: Path):
    runs = scan_gate.run_all_scanners(sandbox, changed=[], docker_available=False,
                                       enable_dependency_check=False)
    assert len(runs) == 3  # semgrep, trivy, gitleaks (dependency-check opt-in only)
    assert all(r.status == "skipped" for r in runs)
    assert all(r.reason == "docker unavailable" for r in runs)
    assert all(r.findings == [] for r in runs)


def test_run_all_scanners_isolates_one_tool_erroring(sandbox: Path, monkeypatch):
    monkeypatch.setattr(scan_gate, "run_semgrep", lambda repo, targets: _dr("not json"))
    monkeypatch.setattr(scan_gate, "run_trivy", lambda repo, targets: _dr(TRIVY_SAMPLE))
    monkeypatch.setattr(scan_gate, "run_gitleaks", lambda repo, targets: _dr(""))

    runs = scan_gate.run_all_scanners(sandbox, changed=["requirements.txt"], docker_available=True,
                                       enable_dependency_check=False)
    by_tool = {r.tool: r for r in runs}
    assert by_tool["semgrep"].status == "error"
    assert by_tool["trivy"].status == "ok"
    assert len(by_tool["trivy"].findings) == 3
    assert by_tool["gitleaks"].status == "ok"
    assert by_tool["gitleaks"].findings == []


def test_run_all_scanners_surfaces_stderr_on_unparseable_output(sandbox: Path, monkeypatch):
    """Task 0007: empty/unparseable stdout must carry the *why* from stderr,
    not just the bare JSONDecodeError — this is what made PR #6's live trivy
    failure require pulling the CI artifact to diagnose instead of being
    readable from the gate's own error message."""
    monkeypatch.setattr(
        scan_gate, "run_trivy",
        lambda repo, targets: _dr("", stderr="FATAL: unable to update vulnerability DB: "
                                              "context deadline exceeded", returncode=1),
    )
    monkeypatch.setattr(scan_gate, "run_semgrep", lambda repo, targets: _dr(json.dumps({"results": []})))
    monkeypatch.setattr(scan_gate, "run_gitleaks", lambda repo, targets: _dr(""))

    runs = scan_gate.run_all_scanners(sandbox, changed=[], docker_available=True,
                                       enable_dependency_check=False)
    trivy_run = {r.tool: r for r in runs}["trivy"]
    assert trivy_run.status == "error"
    assert "unparseable output" in trivy_run.reason
    assert "unable to update vulnerability DB" in trivy_run.reason


def test_run_all_scanners_notes_empty_stderr_too_when_stdout_is_empty(sandbox: Path, monkeypatch):
    """No stderr either (e.g. the container was OOM-killed) — still say so
    explicitly rather than leaving the reader to guess why stderr is absent
    from the message."""
    monkeypatch.setattr(scan_gate, "run_trivy", lambda repo, targets: _dr("", stderr="", returncode=137))
    monkeypatch.setattr(scan_gate, "run_semgrep", lambda repo, targets: _dr(json.dumps({"results": []})))
    monkeypatch.setattr(scan_gate, "run_gitleaks", lambda repo, targets: _dr(""))

    runs = scan_gate.run_all_scanners(sandbox, changed=[], docker_available=True,
                                       enable_dependency_check=False)
    trivy_run = {r.tool: r for r in runs}["trivy"]
    assert trivy_run.status == "error"
    assert "empty stderr" in trivy_run.reason
    assert "137" in trivy_run.reason


def test_run_all_scanners_skips_dependency_check_by_default(sandbox: Path):
    runs = scan_gate.run_all_scanners(sandbox, changed=[], docker_available=True,
                                       enable_dependency_check=False)
    assert "dependency-check" not in {r.tool for r in runs}


def test_run_all_scanners_includes_dependency_check_when_enabled(sandbox: Path, monkeypatch):
    monkeypatch.setattr(scan_gate, "run_semgrep", lambda repo, targets: _dr(json.dumps({"results": []})))
    monkeypatch.setattr(scan_gate, "run_trivy", lambda repo, targets: _dr(json.dumps({"Results": []})))
    monkeypatch.setattr(scan_gate, "run_gitleaks", lambda repo, targets: _dr(""))
    monkeypatch.setattr(scan_gate, "run_dependency_check", lambda repo, task_id: _dr(DEPENDENCY_CHECK_SAMPLE))

    runs = scan_gate.run_all_scanners(sandbox, changed=[], docker_available=True,
                                       enable_dependency_check=True, task_id="0001")
    by_tool = {r.tool: r for r in runs}
    assert "dependency-check" in by_tool
    assert by_tool["dependency-check"].status == "ok"
    assert len(by_tool["dependency-check"].findings) == 1


# ---------------------------------------------------------------------------
# SARIF assembly
# ---------------------------------------------------------------------------

def test_build_sarif_maps_severity_to_sarif_level():
    runs = [scan_gate.ToolRun(tool="semgrep", status="ok", findings=[
        _finding(severity="critical"), _finding(severity="medium"), _finding(severity="low"),
    ])]
    sarif = scan_gate.build_sarif(runs)
    assert sarif["version"] == "2.1.0"
    levels = [r["level"] for r in sarif["runs"][0]["results"]]
    assert levels == ["error", "warning", "note"]


def test_build_sarif_records_tool_error_as_unsuccessful_invocation():
    runs = [scan_gate.ToolRun(tool="semgrep", status="error", reason="unparseable output: boom")]
    sarif = scan_gate.build_sarif(runs)
    assert sarif["runs"][0]["invocations"][0]["executionSuccessful"] is False


# ---------------------------------------------------------------------------
# End-to-end scan() — real git sandbox + monkeypatched tool invocations
# ---------------------------------------------------------------------------

def test_scan_end_to_end_blocks_on_introduced_secret(sandbox: Path, monkeypatch):
    write(sandbox, "config.py", "SAFE = 1\n")
    git(sandbox, "add", "-A")
    git(sandbox, "commit", "-q", "-m", "seed config")
    git(sandbox, "checkout", "-q", "-b", "feat/leak")
    write(sandbox, "config.py", "API_KEY = 'sk-fake-example-not-a-real-secret'\n")
    git(sandbox, "commit", "-q", "-am", "accidentally add a key")

    monkeypatch.setattr(scan_gate, "check_docker_available", lambda: True)
    monkeypatch.setattr(scan_gate, "run_semgrep", lambda repo, targets: _dr(json.dumps({"results": []})))
    monkeypatch.setattr(scan_gate, "run_trivy", lambda repo, targets: _dr(json.dumps({"Results": []})))
    monkeypatch.setattr(
        scan_gate, "run_gitleaks",
        lambda repo, targets: _dr(json.dumps([
            {"RuleID": "generic-api-key", "File": "config.py", "StartLine": 1, "Description": "key"}
        ])),
    )

    summary, sarif = scan_gate.scan(sandbox, "0001", base="master", branch="feat/leak",
                                     enable_dependency_check=False)

    assert summary["verdict"] == "block"
    assert summary["changed_files"] == ["config.py"]
    assert summary["findings_introduced_blocking"] == 1
    assert sarif["runs"][2]["tool"]["driver"]["name"] == "gitleaks"


def test_scan_degrades_cleanly_without_fabricating_a_pass(sandbox: Path, monkeypatch):
    monkeypatch.setattr(scan_gate, "check_docker_available", lambda: False)
    summary, _ = scan_gate.scan(sandbox, "0002", base=None, branch="master", enable_dependency_check=False)
    assert summary["degraded"] is True
    assert summary["verdict"] == "degraded"
    assert summary["findings_total"] == 0
