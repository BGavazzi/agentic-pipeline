from pathlib import Path

from scripts.validate_task import validate


VALID = """---
status: todo
priority: P1
type: feat
created: 2026-09-18
updated: 2026-09-18
---

# 0001 — feat: example

## Context
An executable task contract.

## What To Do
- [ ] Implement the behavior.

## Exit Conditions
- [ ] Tests pass.
"""


def test_valid_task_schema_passes(tmp_path: Path):
    path = tmp_path / "0001-feat-example.md"
    path.write_text(VALID, encoding="utf-8")
    report = validate(path)
    assert report.passed is True


def test_missing_required_section_is_rejected(tmp_path: Path):
    path = tmp_path / "0001-feat-example.md"
    path.write_text(VALID.replace("## Context", "## Missing"), encoding="utf-8")
    report = validate(path)
    assert report.passed is False
    assert any("F7" in error for error in report.errors)
