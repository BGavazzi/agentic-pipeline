---
status: in_progress
priority: P1
type: test
created: 2026-09-18
updated: 2026-09-18
clickup_id: null
parent: 0067-docs-agentic-sdlc-testing-sota
blocks: []
blocked_by: []
---

# 0072 — Test: dogfood task and closure validator contracts

## Context
The harness audit identified the task-schema and closure-law scripts as
implemented but under-tested. Since these scripts define the work intake and
completion boundary, regressions here can silently weaken every downstream gate.

## Problem
The validators had no direct adversarial tests for missing required sections,
advisory in-progress tasks, and strict seven-obligation completion.

## What To Do
- [x] Add valid and invalid task-schema fixtures in unit tests.
- [x] Add advisory and strict closure-law contract tests.
- [x] Keep the tests temporary-file based and deterministic.

## Affected Files
- `tests/test_validate_task.py`
- `tests/test_validate_closure.py`

## Exit Conditions
- [x] Valid task schema passes and missing context fails.
- [x] In-progress closure remains advisory.
- [x] Done closure requires all seven obligations to be resolved.
- [x] Full test suite passes.

## Required Documentation (Closure Law)
- [x] `CHANGELOG.md` updated
- [x] `function-catalog` updated (no new production signature)
- [N/A] `SDD_KIT` — no architecture decision required
- [N/A] `README.md` — no user-facing behavior change
- [x] `.agents/continuity-codex.md` updated
- [x] Tests passing
- [N/A] `ROUTE_BEHAVIOR_MAP` — no HTTP routes
- [ ] PR approved (task remains in progress until review)

## Honest Backlog
The tests validate local contracts; they do not prove protected branch settings
or external workflow installation.
