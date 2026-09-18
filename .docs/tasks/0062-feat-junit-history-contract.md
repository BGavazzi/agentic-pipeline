---
status: in_progress
priority: P1
type: feat
created: 2026-09-18
updated: 2026-09-18
clickup_id: null
parent: 0061
blocks: []
blocked_by: []
---

# 0062 — Feature: normalize JUnit into per-test history evidence

## Context
The harness can evaluate flake policy and record per-test history, but CI only
produced an opaque JUnit artifact. Agents therefore could not consume test
identity, status and duration through a versioned contract.

## Problem
Without a deterministic adapter, each consumer would parse vendor-specific XML,
with inconsistent failure semantics and no protection against duplicate or
unsafe test records.

## What To Do
- [x] Normalize common nested JUnit testcase elements into a schema-versioned
      per-test JSON report.
- [x] Preserve pass/fail/error/skip and duration metrics with exact commit/run
      identity and report digest.
- [x] Reject malformed, duplicate, unsafe or ambiguous input fail-closed.
- [x] Emit normalized evidence from the CI unit job without changing admission.
- [ ] Add durable cross-run history storage and a separately approved
      test-impact promotion policy; this slice must not skip tests.

## Affected Files
- `scripts/junit_history.py`
- `tests/test_junit_history.py`
- `.github/workflows/ci.yml`, `scripts/sota_audit.py`
- `README.md`, `CHANGELOG.md`, `.docs/function-catalog.md`

## Exit Conditions
- [x] Parser behavior is deterministic and tested for statuses, duration,
      duplicates, malformed identity and unsafe XML declarations.
- [x] CI uploads normalized per-test evidence on success and failure.
- [x] Full suite, scanners and closure validators pass.
- [ ] PR approved.

## Required Documentation (Closure Law)
- [x] `CHANGELOG.md` updated
- [x] `<function_catalog>` updated
- [N/A] `<sdd_kit_path>`: no new architectural decision record
- [x] `README.md` updated
- [x] `.agents/continuity-codex.md` updated
- [x] Tests passing
- [N/A] `<route_map>`: no route changed
- [ ] PR approved

## Honest Backlog
This adapter emits one-run evidence. It does not persist history across CI
runs, authorize test selection, retry failures, or turn quarantine into green.
