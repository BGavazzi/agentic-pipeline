---
status: in_progress
priority: P1
type: feat
created: 2026-09-16
updated: 2026-09-16
clickup_id: null
parent: 0016
blocks: []
blocked_by: []
---

# 0030 — feat: carry visual receipts through admission

## Context
Task 0016 established a strict visual receipt contract, and PortalApp now has
the first real local Playwright producer. The core admission adapter still did
not recognize the `visual` gate, so a consumer could validate a screenshot but
could not carry that evidence into the same scorecard/admission path.

## Problem
Visual evidence must be optional at the core level because not every consumer
has a browser surface, but when a frontend supplies a visual receipt it must be
schema-checked, identity-bound, measured, and fail-closed like every other
gate. Unknown visual evidence must not be silently discarded.

## What To Do
- [x] Add `visual` to the known admission gate set.
- [x] Aggregate optional visual receipts with exact base/head identity checks.
- [x] Carry visual status and diff metrics into the quality scorecard.
- [x] Wire optional visual artifact discovery into CI admission/scorecard jobs.
- [x] Add tests for pass and stale visual evidence.
- [x] Document that consumers provide the browser producer while core owns the
      admission contract.

## Affected Files
- `scripts/admission_gate.py`
- `scripts/ci_receipts.py`
- `scripts/quality_scorecard.py`
- `.github/workflows/ci.yml`
- `tests/test_ci_receipts.py`
- `tests/test_quality_scorecard.py`

## Exit Conditions
- [x] A valid visual receipt is carried as a `visual` gate.
- [x] A stale/malformed visual receipt is rejected.
- [x] Visual diff ratio and comparison count appear in scorecard metrics.
- [x] A visual failure remains a blocker when the receipt is supplied.
- [x] Tests and workflow parsing pass.

## Required Documentation (Closure Law)
- [x] `CHANGELOG.md` updated
- [N/A] `function-catalog.md` — no function catalog exists
- [N/A] `SDD_KIT.md` — no new product decision
- [x] `README.md` updated
- [N/A] `.agents/continuity-<agent>.md` — no continuity file in this checkout
- [x] Tests passing
- [N/A] `ROUTE_BEHAVIOR_MAP.md` — no route/handler/model change
- [ ] PR approved

## Honest Backlog
- The core still does not install Playwright or launch a browser. PortalApp is
  the first local producer; each frontend consumer must provide its own
  deterministic producer and baseline review policy.
