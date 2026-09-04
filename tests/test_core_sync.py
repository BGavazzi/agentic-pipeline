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
    result = core_sync.sync_skills(source, target, allowlist=None, dry_run=False)

    assert sorted(result.synced) == [
        ".claude/skills/builder/SKILL.md",
        ".claude/skills/tester/SKILL.md",
    ]
    assert result.drifted == []
    assert (target / ".claude/skills/builder/SKILL.md").read_text() == "builder skill\n"
    assert (target / ".claude/skills/tester/SKILL.md").read_text() == "tester skill\n"


def test_sync_skills_excludes_pycache(source: Path, target: Path):
    core_sync.sync_skills(source, target, allowlist=None, dry_run=False)

    assert not (target / ".claude/skills/builder/__pycache__").exists()


def test_sync_skills_respects_allowlist(source: Path, target: Path):
    result = core_sync.sync_skills(source, target, allowlist={"tester"}, dry_run=False)

    assert result.synced == [".claude/skills/tester/SKILL.md"]
    assert not (target / ".claude/skills/builder").exists()
    assert (target / ".claude/skills/tester/SKILL.md").exists()


def test_sync_skills_dry_run_makes_no_changes(source: Path, target: Path):
    result = core_sync.sync_skills(source, target, allowlist=None, dry_run=True)

    assert sorted(result.synced) == [
        ".claude/skills/builder/SKILL.md",
        ".claude/skills/tester/SKILL.md",
    ]
    assert not (target / ".claude").exists()


def test_sync_skills_overwrites_existing_by_name(source: Path, target: Path):
    # No manifest entry for this file yet, so it's a pre-existing file, not a
    # tracked-and-then-drifted one — first sync always wins (see module docstring).
    write(target, ".claude/skills/builder/SKILL.md", "stale local edit\n")

    core_sync.sync_skills(source, target, allowlist=None, dry_run=False)

    assert (target / ".claude/skills/builder/SKILL.md").read_text() == "builder skill\n"


# --- sync_skills: drift detection ------------------------------------------

def test_sync_skills_skips_drifted_skill_and_records_new_manifest_hashes(source: Path, target: Path):
    manifest = {}
    core_sync.sync_skills(source, target, allowlist=None, dry_run=False, manifest=manifest)
    assert manifest[".claude/skills/builder/SKILL.md"] == core_sync._sha256(
        source / ".claude/skills/builder/SKILL.md"
    )

    # Someone hand-edits the vendored copy after the first sync.
    write(target, ".claude/skills/builder/SKILL.md", "hand-edited after sync\n")

    result = core_sync.sync_skills(source, target, allowlist=None, dry_run=False, manifest=manifest)

    assert result.drifted == [".claude/skills/builder/SKILL.md"]
    assert result.synced == [".claude/skills/tester/SKILL.md"]  # unaffected skill still syncs
    assert (target / ".claude/skills/builder/SKILL.md").read_text() == "hand-edited after sync\n"


def test_sync_skills_force_overwrites_drifted_skill(source: Path, target: Path):
    manifest = {}
    core_sync.sync_skills(source, target, allowlist=None, dry_run=False, manifest=manifest)
    write(target, ".claude/skills/builder/SKILL.md", "hand-edited after sync\n")

    result = core_sync.sync_skills(
        source, target, allowlist=None, dry_run=False, manifest=manifest, force=True,
    )

    assert result.drifted == []
    assert ".claude/skills/builder/SKILL.md" in result.synced
    assert (target / ".claude/skills/builder/SKILL.md").read_text() == "builder skill\n"


def test_sync_skills_one_drifted_file_blocks_the_whole_skill_directory(source: Path, target: Path):
    write(source, ".claude/skills/builder/notes.md", "extra file\n")
    manifest = {}
    core_sync.sync_skills(source, target, allowlist=None, dry_run=False, manifest=manifest)
    write(target, ".claude/skills/builder/SKILL.md", "hand-edited after sync\n")

    result = core_sync.sync_skills(source, target, allowlist=None, dry_run=False, manifest=manifest)

    # notes.md itself didn't drift, but it's in the same directory as the
    # file that did — the whole skill is gated, not just the touched file.
    assert ".claude/skills/builder/notes.md" not in result.synced
    assert (target / ".claude/skills/builder/notes.md").read_text() == "extra file\n"  # untouched, from first sync


# --- sync_gate_scripts -----------------------------------------------------

def test_sync_gate_scripts_whitelist_only(source: Path, target: Path):
    result = core_sync.sync_gate_scripts(source, target, dry_run=False)

    assert sorted(result.synced) == ["scripts/blast_radius.py", "scripts/validate_task.py"]
    assert (target / "scripts/validate_task.py").exists()
    assert not (target / "scripts/some_unrelated_helper.py").exists()


def test_sync_gate_scripts_skips_missing_source_file(source: Path, target: Path):
    # scan_gate.py and quota_gate.py aren't in the fixture source tree at all.
    result = core_sync.sync_gate_scripts(source, target, dry_run=False)

    assert "scripts/scan_gate.py" not in result.synced
    assert "scripts/quota_gate.py" not in result.synced


def test_sync_gate_scripts_dry_run_makes_no_changes(source: Path, target: Path):
    core_sync.sync_gate_scripts(source, target, dry_run=True)

    assert not (target / "scripts").exists()


def test_sync_gate_scripts_skips_drifted_file(source: Path, target: Path):
    manifest = {}
    core_sync.sync_gate_scripts(source, target, dry_run=False, manifest=manifest)
    write(target, "scripts/validate_task.py", "# hand-patched locally\n")

    result = core_sync.sync_gate_scripts(source, target, dry_run=False, manifest=manifest)

    assert result.drifted == ["scripts/validate_task.py"]
    assert result.synced == ["scripts/blast_radius.py"]
    assert (target / "scripts/validate_task.py").read_text() == "# hand-patched locally\n"


def test_sync_gate_scripts_force_overwrites_drifted_file(source: Path, target: Path):
    manifest = {}
    core_sync.sync_gate_scripts(source, target, dry_run=False, manifest=manifest)
    write(target, "scripts/validate_task.py", "# hand-patched locally\n")

    result = core_sync.sync_gate_scripts(source, target, dry_run=False, manifest=manifest, force=True)

    assert result.drifted == []
    assert (target / "scripts/validate_task.py").read_text() == "# validate_task\n"


# --- sync_conventions -------------------------------------------------------

def test_sync_conventions_copies_only_markdown(source: Path, target: Path):
    result = core_sync.sync_conventions(source, target, dry_run=False)

    assert sorted(result.synced) == [
        ".docs/conventions/engineering-defaults.md",
        ".docs/conventions/git-pr-workflow.md",
    ]
    assert not (target / ".docs/conventions/not-markdown.txt").exists()


def test_sync_conventions_skips_drifted_file(source: Path, target: Path):
    manifest = {}
    core_sync.sync_conventions(source, target, dry_run=False, manifest=manifest)
    write(target, ".docs/conventions/git-pr-workflow.md", "hand-edited\n")

    result = core_sync.sync_conventions(source, target, dry_run=False, manifest=manifest)

    assert result.drifted == [".docs/conventions/git-pr-workflow.md"]
    assert (target / ".docs/conventions/git-pr-workflow.md").read_text() == "hand-edited\n"


# --- manifest persistence + _is_drifted -------------------------------------

def test_load_manifest_returns_empty_dict_when_absent(target: Path):
    assert core_sync.load_manifest(target) == {}


def test_load_manifest_returns_empty_dict_when_corrupt(target: Path):
    write(target, ".claude/.core-sync-manifest.json", "{not valid json")
    assert core_sync.load_manifest(target) == {}


def test_save_and_load_manifest_roundtrips(target: Path):
    core_sync.save_manifest(target, {"scripts/foo.py": "abc123"}, dry_run=False)
    assert core_sync.load_manifest(target) == {"scripts/foo.py": "abc123"}


def test_save_manifest_dry_run_writes_nothing(target: Path):
    core_sync.save_manifest(target, {"scripts/foo.py": "abc123"}, dry_run=True)
    assert not (target / ".claude" / ".core-sync-manifest.json").exists()


def test_is_drifted_false_when_no_manifest_entry(target: Path):
    write(target, "scripts/foo.py", "content\n")
    assert core_sync._is_drifted(target, {}, "scripts/foo.py") is False


def test_is_drifted_false_when_file_missing(target: Path):
    manifest = {"scripts/foo.py": "somehash"}
    assert core_sync._is_drifted(target, manifest, "scripts/foo.py") is False


def test_is_drifted_true_when_content_no_longer_matches(target: Path):
    write(target, "scripts/foo.py", "content\n")
    manifest = {"scripts/foo.py": core_sync._sha256(target / "scripts/foo.py")}
    write(target, "scripts/foo.py", "different content\n")
    assert core_sync._is_drifted(target, manifest, "scripts/foo.py") is True


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


def test_main_writes_a_manifest_after_a_real_run(monkeypatch, target: Path):
    monkeypatch.setattr(sys, "argv", ["core_sync.py", str(target)])
    assert core_sync.main() == 0

    manifest_path = target / ".claude" / ".core-sync-manifest.json"
    assert manifest_path.exists()
    manifest = core_sync.load_manifest(target)
    assert "scripts/validate_task.py" in manifest


def test_main_dry_run_writes_no_manifest(monkeypatch, target: Path):
    monkeypatch.setattr(sys, "argv", ["core_sync.py", str(target), "--dry-run"])
    assert core_sync.main() == 0
    assert not (target / ".claude" / ".core-sync-manifest.json").exists()


def test_main_returns_1_and_skips_a_hand_edited_gate_script(monkeypatch, target: Path):
    monkeypatch.setattr(sys, "argv", ["core_sync.py", str(target)])
    assert core_sync.main() == 0
    write(target, "scripts/validate_task.py", "# hand-patched after the first sync\n")

    monkeypatch.setattr(sys, "argv", ["core_sync.py", str(target)])
    assert core_sync.main() == 1  # drift detected, not a clean sync

    assert (target / "scripts/validate_task.py").read_text() == "# hand-patched after the first sync\n"


def test_main_force_overwrites_the_hand_edited_gate_script(monkeypatch, target: Path):
    monkeypatch.setattr(sys, "argv", ["core_sync.py", str(target)])
    assert core_sync.main() == 0
    write(target, "scripts/validate_task.py", "# hand-patched after the first sync\n")

    monkeypatch.setattr(sys, "argv", ["core_sync.py", str(target), "--force"])
    assert core_sync.main() == 0  # forced, so it's a clean sync again

    real_source = core_sync.find_repo_root()
    assert (target / "scripts/validate_task.py").read_text() == \
        (real_source / "scripts/validate_task.py").read_text()
