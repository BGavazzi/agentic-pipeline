---
status: in_progress
priority: P1
type: feat
created: 2026-09-16
updated: 2026-09-16
clickup_id: null
parent: 0010
blocks: []
blocked_by: []
---

# 0015 — feat: conservative test-impact analysis

## Context
Agentic coding increases CI volume. State-of-the-art pipelines use test-impact
analysis to reduce redundant execution, but an under-approximation can create
false green. This task adds a conservative report that selects impacted Python
tests only when direct import/path evidence is reliable and otherwise requests
the full suite.

## Problem
The harness currently runs the full test suite for every integration attempt,
with no machine-readable explanation of selection cost or fallback behavior.
There is no safe way to optimize until unknown file types, dynamic imports,
unresolved modules, and empty selections are explicitly treated as full-suite
conditions.

## What To Do
- [x] Add `scripts/test_impact.py` with git-diff discovery, Python AST import
      edges, conventional test matching, conservative fallback, and schema-v1
      metrics.
- [x] Emit changed/available/selected counts, selection ratio, fallback
      reasons, exact base/head refs, and an explicit optimization-only policy.
- [x] Add tests for direct impact, non-Python fallback, and unknown-module
      fallback.
- [ ] Integrate the report into the clean-room runner without allowing an
      impact report to replace full execution until precision/recall is measured.

## Affected Files
- `scripts/test_impact.py`
- `tests/test_test_impact.py`
- `.docs/tasks/0015-feat-conservative-test-impact-analysis.md`
- `README.md`
- `CHANGELOG.md`
- `.agents/continuity-codex.md`

## Exit Conditions
- [x] Directly impacted Python tests can be selected from committed diff/import
      evidence.
- [x] Unknown/non-Python/no-selection cases fall back to the full suite.
- [x] Metrics and provenance are emitted as versioned JSON.
- [x] Tests and validators pass.
- [ ] Selection is wired into execution only after a precision/recall benchmark
      demonstrates it does not under-select relevant tests.
- [ ] PR approved — remains `in_progress` until review, per Closure Law.

## Required Documentation (Closure Law)
- [x] `CHANGELOG.md` updated
- [x] `<function_catalog>` updated (signature change)
- [N/A] `<sdd_kit_path>` — no SDD_KIT.md in this repo
- [x] `README.md` updated
- [x] `.agents/continuity-codex.md` updated
- [x] Tests passing
- [N/A] `<route_map>` — no web routes in this repo
- [ ] PR approved

## Honest Backlog
- Python AST imports do not model dynamic imports, generated code, service
  boundaries, or non-Python ecosystems. Those cases deliberately fall back to
  full execution.
- No historical precision/recall dataset exists yet. The report is therefore
  advisory and optimization-only, not an admission gate.
- Integration CI still runs the full clean-room suite; wiring the subset must
  wait for a benchmark proving no relevant test is silently omitted.
