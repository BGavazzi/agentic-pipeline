"""
Unit tests for scripts/blast_radius.py.

Plain pytest against a throwaway local git sandbox — deliberately NOT a
meta-test fixture (meta-test spawns an Agent subagent to exercise a SKILL.md's
LLM-driven behavior; blast_radius.py is a deterministic script with no LLM
reasoning involved, so a direct unit test is the right-sized tool here, same
as validate_task.py/validate_closure.py which also have no meta-test fixture).

Run: pytest tests/test_blast_radius.py -v
"""
from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT_PATH = Path(__file__).resolve().parent.parent / "scripts" / "blast_radius.py"

spec = importlib.util.spec_from_file_location("blast_radius", SCRIPT_PATH)
blast_radius = importlib.util.module_from_spec(spec)
sys.modules["blast_radius"] = blast_radius
spec.loader.exec_module(blast_radius)


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


def test_low_risk_isolated_change(sandbox: Path):
    write(sandbox, "docs/isolated.md", "leaf doc, no consumers\n")
    git(sandbox, "add", "-A")
    git(sandbox, "commit", "-q", "-m", "add isolated doc")
    git(sandbox, "checkout", "-q", "-b", "feat/x")
    write(sandbox, "docs/isolated.md", "changed\n")
    git(sandbox, "commit", "-q", "-am", "edit isolated doc")

    result = blast_radius.classify(sandbox, "0099", base="master", branch="feat/x")

    assert result["changed_files"] == ["docs/isolated.md"]
    assert result["risk_level"] == "low"
    assert result["required_gates"] == ["unit"]


def test_medium_risk_via_ownership_map(sandbox: Path):
    write(
        sandbox,
        ".docs/module-owners.md",
        "| Path prefix | Owner tag | Consumers (path prefixes) |\n"
        "|---|---|---|\n"
        "| lib/shared.py | shared-lib | app/service_a.py, app/service_b.py |\n",
    )
    write(sandbox, "lib/shared.py", "def f(): pass\n")
    git(sandbox, "add", "-A")
    git(sandbox, "commit", "-q", "-m", "seed shared lib + ownership map")
    git(sandbox, "checkout", "-q", "-b", "feat/y")
    write(sandbox, "lib/shared.py", "def f(): return 1\n")
    git(sandbox, "commit", "-q", "-am", "change shared lib")

    result = blast_radius.classify(sandbox, "0100", base="master", branch="feat/y")

    assert "app/service_a.py" in result["affected_modules"]
    assert "app/service_b.py" in result["affected_modules"]
    assert result["risk_level"] == "medium"
    assert "sast" in result["required_gates"]


def test_high_risk_infra_path(sandbox: Path):
    write(sandbox, "ansible/playbook.yml", "- hosts: all\n")
    git(sandbox, "add", "-A")
    git(sandbox, "commit", "-q", "-m", "seed playbook")
    git(sandbox, "checkout", "-q", "-b", "feat/z")
    write(sandbox, "ansible/playbook.yml", "- hosts: all\n  tasks: []\n")
    git(sandbox, "commit", "-q", "-am", "edit playbook")

    result = blast_radius.classify(sandbox, "0101", base="master", branch="feat/z")

    assert result["risk_level"] == "high"
    assert "ansible" in result["risk_triggers"]
    assert "infra-dry-run" in result["required_gates"]
    assert "ultrareview" in result["required_gates"]


def test_high_risk_auth_path(sandbox: Path):
    write(sandbox, "src/auth/login.py", "def login(): pass\n")
    git(sandbox, "add", "-A")
    git(sandbox, "commit", "-q", "-m", "seed auth")
    git(sandbox, "checkout", "-q", "-b", "feat/w")
    write(sandbox, "src/auth/login.py", "def login(): return True\n")
    git(sandbox, "commit", "-q", "-am", "change auth")

    result = blast_radius.classify(sandbox, "0102", base="master", branch="feat/w")

    assert result["risk_level"] == "high"
    assert "auth" in result["risk_triggers"]
    # No infra pattern matched -> infra-dry-run should not be required
    assert "infra-dry-run" not in result["required_gates"]


def test_cochange_signal_surfaces_coupled_file(sandbox: Path):
    # Couple config.py and worker.py across 2 prior commits (meets
    # COCHANGE_MIN_COUNT) on master, before any feature branch exists.
    for i in range(2):
        write(sandbox, "app/config.py", f"VALUE = {i}\n")
        write(sandbox, "app/worker.py", f"# rev {i}\n")
        git(sandbox, "add", "-A")
        git(sandbox, "commit", "-q", "-m", f"co-change round {i}")

    git(sandbox, "checkout", "-q", "-b", "feat/v")
    write(sandbox, "app/config.py", "VALUE = 99\n")
    git(sandbox, "commit", "-q", "-am", "change config only")

    result = blast_radius.classify(sandbox, "0103", base="master", branch="feat/v")

    assert result["changed_files"] == ["app/config.py"]
    assert "app/worker.py" in result["affected_modules"]


def test_import_grep_ignores_generic_stems(sandbox: Path):
    # "SKILL" is the stem of every .claude/skills/*/SKILL.md in the real
    # pipeline repo — a literal-name grep on it would match nearly everything.
    # Regression guard for that over-matching.
    write(sandbox, "pkg/one/SKILL.md", "some skill doc\n")
    write(sandbox, "pkg/two/SKILL.md", "mentions SKILL in prose\n")
    git(sandbox, "add", "-A")
    git(sandbox, "commit", "-q", "-m", "seed two skill docs")
    git(sandbox, "checkout", "-q", "-b", "feat/u")
    write(sandbox, "pkg/one/SKILL.md", "some skill doc, edited\n")
    git(sandbox, "commit", "-q", "-am", "edit one SKILL.md")

    result = blast_radius.classify(sandbox, "0105", base="master", branch="feat/u")

    assert "pkg/two/SKILL.md" not in result["affected_modules"]


def test_no_origin_remote_does_not_crash(sandbox: Path):
    # Regression guard: detect_base must not blow up when there's no origin
    # remote configured (plain local sandbox, no push yet).
    result = blast_radius.classify(sandbox, "0104", base=None, branch="master")
    assert result["base"] in ("integration", "main", "master")


def test_high_risk_ci_workflow_path(sandbox: Path):
    """A diff touching the CI workflow can disable every other gate, so it must
    classify high — otherwise a PR that deletes its own gates rides through on
    unit tests alone."""
    write(sandbox, ".github/workflows/ci.yml", "name: CI\non: [push]\n")
    git(sandbox, "add", "-A")
    git(sandbox, "commit", "-q", "-m", "seed ci")
    git(sandbox, "checkout", "-q", "-b", "feat/ci")
    write(sandbox, ".github/workflows/ci.yml", "name: CI\non: [push]\njobs: {}\n")
    git(sandbox, "commit", "-q", "-am", "edit ci")

    result = blast_radius.classify(sandbox, "0103", base="master", branch="feat/ci")

    assert result["risk_level"] == "high"
    assert "ci-workflow" in result["risk_triggers"]
    assert "ultrareview" in result["required_gates"]


def test_high_risk_gate_script_path(sandbox: Path):
    """Same reasoning for the gate scripts themselves."""
    write(sandbox, "scripts/validate_closure.py", "def main(): pass\n")
    git(sandbox, "add", "-A")
    git(sandbox, "commit", "-q", "-m", "seed gate")
    git(sandbox, "checkout", "-q", "-b", "feat/gate")
    write(sandbox, "scripts/validate_closure.py", "def main(): return 0\n")
    git(sandbox, "commit", "-q", "-am", "edit gate")

    result = blast_radius.classify(sandbox, "0104", base="master", branch="feat/gate")

    assert result["risk_level"] == "high"
    assert "gate-script" in result["risk_triggers"]


def test_ordinary_source_change_not_flagged_as_gate(sandbox: Path):
    """Guard against the new patterns over-matching: a normal script outside the
    gate set must not inherit gate-script risk."""
    write(sandbox, "scripts/helper.py", "def helper(): pass\n")
    git(sandbox, "add", "-A")
    git(sandbox, "commit", "-q", "-m", "seed helper")
    git(sandbox, "checkout", "-q", "-b", "feat/helper")
    write(sandbox, "scripts/helper.py", "def helper(): return 1\n")
    git(sandbox, "commit", "-q", "-am", "edit helper")

    result = blast_radius.classify(sandbox, "0105", base="master", branch="feat/helper")

    assert "gate-script" not in result["risk_triggers"]
    assert "ci-workflow" not in result["risk_triggers"]
