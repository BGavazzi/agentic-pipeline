---
status: in_progress
priority: P1
type: feat
created: 2026-09-16
updated: 2026-09-16
clickup_id: null
parent: 0019
blocks: []
blocked_by: []
---

# 0034 — feat: add test-impact promotion eligibility receipt

## Context
The harness already benchmarks conservative transitive test-impact analysis and
runs the selected tests in shadow mode, while the full integration suite stays
authoritative. It lacked a single receipt that quantified the potential saving
and stated whether the evidence was strong enough for a future dispatcher to
use the impacted subset.

## Problem
Test-impact selection must not become an implicit correctness shortcut. A
dispatcher needs an explicit, versioned, commit-bound decision that combines
benchmark recall/precision, candidate selection, shadow success, and full-suite
success. Unknown, stale, or fallback evidence must remain blocked or explicitly
not applicable.

## What To Do
- [x] Add `scripts/impact_promotion.py` with exact identity validation and
      fail-closed eligibility logic.
- [x] Report precision/recall, selection ratio, tests avoided, shadow/full
      durations, and observed duration savings.
- [x] Preserve full-suite authority and explicit full-fallback semantics.
- [x] Add tests for eligible, blocked, not-applicable, and stale evidence.
- [x] Add the receipt producer to canonical sync and policy/risk surfaces.

## Affected Files
- `scripts/impact_promotion.py`
- `tests/test_impact_promotion.py`
- `scripts/core_sync.py`
- `scripts/blast_radius.py`
- `scripts/policy_integrity.py`
- `README.md`
- `CHANGELOG.md`

## Exit Conditions
- [x] A valid impacted selection with green benchmark, shadow, and full
      integration evidence produces `eligible: true`.
- [x] Any stale or failed evidence blocks promotion.
- [x] Full-suite fallback is reported as `not_applicable`, never as eligible.
- [x] Metrics make test avoidance and observed time savings measurable.
- [x] Tests and validators pass.

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
- This receipt does not yet replace the full CI suite. A later dispatcher can
  consume `eligible: true` for optimization only after repository-specific
  policy review and longer-running benchmark evidence.
