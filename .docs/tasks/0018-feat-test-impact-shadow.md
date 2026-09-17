---
status: todo
priority: P1
type: feat
created: 2026-09-16
updated: 2026-09-16
clickup_id: null
parent: null
blocks: []
blocked_by: []
---

# 0018 — feat: measure test-impact analysis in clean room without reducing authority

## Context
Task 0015 added conservative test selection, but left execution deliberately
disabled until there was precision/recall evidence. This task adds a shadow
worker that executes the selection in the same clean-room boundary as the
integration gate and publishes metrics, while the full suite remains the only
correctness evidence used for admission.

## Problem
An impact optimization that replaces the full suite too early can create a
false-green on indirect changes. The pipeline must measure subset failures and
speedup without turning a heuristic into authority.

## What To Do
- [x] Execute `test_impact.py` selection through `integration_gate.py`.
- [x] Emit mode, policy, selection, status, and execution metrics.
- [x] Run the shadow job on PRs with artifacts even when the shadow fails.
- [x] Mark `impact_runner.py` as a high-risk, synchronizable gate script.
- [ ] Accumulate a precision/recall benchmark before promoting selection to
  replace any required suite.

## Affected Files
- `scripts/impact_runner.py`
- `tests/test_impact_runner.py`
- `scripts/core_sync.py`
- `scripts/blast_radius.py`
- `.github/workflows/ci.yml`

## Exit Conditions
- [x] Reliable Python changes execute only selected tests in shadow mode.
- [x] Unknown changes fall back to the full suite.
- [x] Reports keep `authoritative: false` and full identity.
- [ ] PR approved and merged; real CI benchmark accumulated.

## Required Documentation (Closure Law)
- [ ] `CHANGELOG.md` updated
- [x] `function-catalog.md` updated
- [ ] `SDD_KIT.md` updated — no new ratified decision; existing policy remains.
- [x] `README.md` updated
- [ ] `.agents/continuity-<agent>.md` updated
- [x] Tests passing
- [ ] `route_map` updated — no route/handler/model change
- [ ] PR approved

## Honest Backlog
- Shadow status is intentionally not part of `admission_gate.py`. Promotion
  requires a benchmark measuring false negatives against full-suite results.
