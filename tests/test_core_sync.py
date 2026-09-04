"""
Unit tests for scripts/core_sync.py.

Plain pytest against throwaway local source/target trees under tmp_path —
same style as test_blast_radius.py (deterministic script, no LLM reasoning,
so a direct unit test is the right-sized tool; no meta-test fixture needed).

Run: pytest tests/test_core_sync.py -v
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

SCRIPT_PATH = Path(__file__).resolve().parent.parent / "scripts" / "core_sync.py"

spec = importlib.util.spec_from_file_location("core_sync", SCRIPT_PATH)
core_sync = importlib.util.module_from_spec(spec)
sys.modules["core_sync"] = core_sync
spec.loader.exec_module(core_sync)


def write(root: Path, relpath: str, content: str = "x\n") -> Path:
    p = root / relpath
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return p


@pytest.fixture
def source(tmp_path: Path) -> Path:
    """A fake agentic-pipeline source tree — not the real repo, so tests
    don't depend on which skills/scripts happen to exist here today."""
    src = tmp_path / "source"
    write(src, ".claude/skills/builder/SKILL.md", "builder skill\n")
    write(src, ".claude/skills/builder/__pycache__/junk.pyc", "junk\n")
    write(src, ".claude/skills/tester/SKILL.md", "tester skill\n")
    write(src, "scripts/validate_task.py", "# validate_task\n")
    write(src, "scripts/blast_radius.py", "# blast_radius\n")
    write(src, "scripts/some_unrelated_helper.py", "# not a gate script\n")
    write(src, ".docs/conventions/git-pr-workflow.md", "# workflow\n")
    write(src, ".docs/conventions/engineering-defaults.md", "# defaults\n")
    write(src, ".docs/conventions/not-markdown.txt", "ignored\n")
    return src


@pytest.fixture
def target(tmp_path: Path) -> Path:
    dst = tmp_path / "target"
    dst.mkdir()
    return dst


# --- sync_skills ---------------------------------------------------------

def test_sync_skills_copies_all_by_default(source: Path, target: Path):
    synced = core_sync.sync_skills(source, target, allowlist=None, dry_run=False)

    assert sorted(synced) == [".claude/skills/builder/", ".claude/skills/tester/"]
    assert (target / ".claude/skills/builder/SKILL.md").read_text() == "builder skill\n"
    assert (target / ".claude/skills/tester/SKILL.md").read_text() == "tester skill\n"


def test_sync_skills_excludes_pycache(source: Path, target: Path):
    core_sync.sync_skills(source, target, allowlist=None, dry_run=False)

    assert not (target / ".claude/skills/builder/__pycache__").exists()


def test_sync_skills_respects_allowlist(source: Path, target: Path):
    synced = core_sync.sync_skills(source, target, allowlist={"tester"}, dry_run=False)

    assert synced == [".claude/skills/tester/"]
    assert not (target / ".claude/skills/builder").exists()
    assert (target / ".claude/skills/tester/SKILL.md").exists()


def test_sync_skills_dry_run_makes_no_changes(source: Path, target: Path):
    synced = core_sync.sync_skills(source, target, allowlist=None, dry_run=True)

    assert sorted(synced) == [".claude/skills/builder/", ".claude/skills/tester/"]
    assert not (target / ".claude").exists()


def test_sync_skills_overwrites_existing_by_name(source: Path, target: Path):
    write(target, ".claude/skills/builder/SKILL.md", "stale local edit\n")

    core_sync.sync_skills(source, target, allowlist=None, dry_run=False)

    assert (target / ".claude/skills/builder/SKILL.md").read_text() == "builder skill\n"


# --- sync_gate_scripts -----------------------------------------------------

def test_sync_gate_scripts_whitelist_only(source: Path, target: Path):
    synced = core_sync.sync_gate_scripts(source, target, dry_run=False)

    assert sorted(synced) == ["scripts/blast_radius.py", "scripts/validate_task.py"]
    assert (target / "scripts/validate_task.py").exists()
    assert not (target / "scripts/some_unrelated_helper.py").exists()


def test_sync_gate_scripts_skips_missing_source_file(source: Path, target: Path):
    # scan_gate.py and quota_gate.py aren't in the fixture source tree at all.
    synced = core_sync.sync_gate_scripts(source, target, dry_run=False)

    assert "scripts/scan_gate.py" not in synced
    assert "scripts/quota_gate.py" not in synced


def test_sync_gate_scripts_dry_run_makes_no_changes(source: Path, target: Path):
    core_sync.sync_gate_scripts(source, target, dry_run=True)

    assert not (target / "scripts").exists()


# --- sync_conventions -------------------------------------------------------

def test_sync_conventions_copies_only_markdown(source: Path, target: Path):
    synced = core_sync.sync_conventions(source, target, dry_run=False)

    assert sorted(synced) == [
        ".docs/conventions/engineering-defaults.md",
        ".docs/conventions/git-pr-workflow.md",
    ]
    assert not (target / ".docs/conventions/not-markdown.txt").exists()


# --- seed_agents_md ----------------------------------------------------------

def test_seed_agents_md_creates_when_absent(target: Path):
    result = core_sync.seed_agents_md(target, dry_run=False)

    assert result is not None
    assert (target / "AGENTS.md").exists()
    assert "<project_name>" in (target / "AGENTS.md").read_text()


def test_seed_agents_md_never_overwrites_existing(target: Path):
    write(target, "AGENTS.md", "my own hand-written constitution\n")

    result = core_sync.seed_agents_md(target, dry_run=False)

    assert result is None
    assert (target / "AGENTS.md").read_text() == "my own hand-written constitution\n"


def test_seed_agents_md_dry_run_makes_no_changes(target: Path):
    result = core_sync.seed_agents_md(target, dry_run=True)

    assert result is not None
    assert not (target / "AGENTS.md").exists()


# --- main() / CLI ------------------------------------------------------------

def test_main_rejects_nonexistent_target(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(sys, "argv", ["core_sync.py", str(tmp_path / "does-not-exist")])

    assert core_sync.main() == 2


def test_main_rejects_target_equal_to_source(monkeypatch):
    real_source = core_sync.find_repo_root()
    monkeypatch.setattr(sys, "argv", ["core_sync.py", str(real_source)])

    assert core_sync.main() == 2


def test_main_dry_run_against_real_source_leaves_target_untouched(monkeypatch, target: Path):
    """Integration-style: uses this repo's real source tree, but --dry-run
    means the throwaway target must come back empty."""
    monkeypatch.setattr(sys, "argv", ["core_sync.py", str(target), "--dry-run"])

    assert core_sync.main() == 0
    assert list(target.iterdir()) == []


def test_main_full_run_against_real_source_seeds_target(monkeypatch, target: Path):
    monkeypatch.setattr(sys, "argv", ["core_sync.py", str(target)])

    assert core_sync.main() == 0
    assert (target / "AGENTS.md").exists()
    assert (target / "scripts" / "validate_task.py").exists()
    assert (target / ".docs" / "conventions").is_dir()


def test_main_second_run_never_overwrites_target_agents_md(monkeypatch, target: Path):
    monkeypatch.setattr(sys, "argv", ["core_sync.py", str(target)])
    assert core_sync.main() == 0
    write(target, "AGENTS.md", "edited after first sync\n")

    monkeypatch.setattr(sys, "argv", ["core_sync.py", str(target)])
    assert core_sync.main() == 0

    assert (target / "AGENTS.md").read_text() == "edited after first sync\n"
