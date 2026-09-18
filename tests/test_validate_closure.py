from pathlib import Path

from scripts.validate_closure import validate_closure


def test_non_done_task_is_advisory_when_closure_is_incomplete(tmp_path: Path):
    path = tmp_path / "0001-feat-example.md"
    path.write_text("""---
status: in_progress
priority: P1
type: feat
created: 2026-09-18
updated: 2026-09-18
---

## Required Documentation
- [ ] Tests passing
""", encoding="utf-8")
    report = validate_closure(path)
    assert report.passed is True
    assert report.warnings


def test_done_task_requires_every_closure_obligation(tmp_path: Path):
    path = tmp_path / "0001-feat-example.md"
    path.write_text("""---
status: done
priority: P1
type: feat
created: 2026-09-18
updated: 2026-09-18
---

## Required Documentation (Closure Law)
- [x] CHANGELOG.md updated
- [x] function-catalog.md updated
- [N/A] SDD_KIT.md — no architecture decision required
- [x] README.md updated
- [x] .agents/continuity-codex.md updated
- [x] Tests passing
- [N/A] ROUTE_BEHAVIOR_MAP.md — no HTTP routes
""", encoding="utf-8")
    report = validate_closure(path)
    assert report.passed is True
    assert len(report.items_seen) == 7
