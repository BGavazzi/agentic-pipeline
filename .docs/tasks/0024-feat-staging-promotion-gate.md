---
status: in_progress
priority: P0
type: feat
created: 2026-09-16
updated: 2026-09-16
clickup_id: null
parent: 0010
blocks: []
blocked_by: []
---

# 0024 — feat: add the autonomous-to-staging promotion gate

## Context
The pipeline now has clean-room integration, deterministic admission, and a
quality scorecard. It still lacks an explicit handoff artifact for the desired
agentic workflow: an agent can test a candidate without a human, but only a
candidate that survives those checks should become eligible for a staging PR.

## Problem
Without a separate promotion decision, adapters would have to infer staging
eligibility from several reports and could accidentally open a review PR for a
candidate with incomplete or non-isolated evidence. The handoff must be
fail-closed, versioned, metric-bearing, and independent of PR creation.

## What To Do
- [x] Add `scripts/staging_gate.py` with exact commit-pair validation.
- [x] Require an admitted green scorecard and a passing isolated integration
  receipt.
- [x] Emit staging eligibility, blockers, provenance, and metrics in a
  schema-v1 receipt.
- [x] Add deterministic tests for pass, failure, isolation, stale identity,
  incomplete evidence, and invalid input.
- [x] Run the staging decision in the admission workflow and upload its receipt.
- [x] Add the gate to core sync and high-risk blast-radius classification.

## Affected Files
- `scripts/staging_gate.py`
- `scripts/core_sync.py`
- `scripts/blast_radius.py`
- `.github/workflows/ci.yml`
- `tests/test_staging_gate.py`

## Exit Conditions
- [x] A candidate with admitted scorecard plus isolated integration is eligible
  for `staging-review`.
- [x] Missing, stale, failed, or non-isolated evidence cannot become eligible.
- [x] The workflow uploads a machine-readable staging receipt even when the
  decision is blocked.
- [x] Human review remains explicitly required after eligibility; no PR is
  created or merged by this gate.
- [x] Tests and repository validators pass.

## Required Documentation (Closure Law)
- [x] `CHANGELOG.md` updated
- [N/A] `function-catalog.md` — repository has no function catalog
- [N/A] `SDD_KIT.md` — no new product decision
- [x] `README.md` updated
- [N/A] `.agents/continuity-<agent>.md` — no continuity file in this checkout
- [x] Tests passing
- [N/A] `ROUTE_BEHAVIOR_MAP.md` — no route/handler/model change
- [ ] PR approved

## Honest Backlog
- This task emits eligibility only. A future repository-specific adapter may
  create the staging PR after receiving an eligible receipt, but PR creation is
  intentionally outside the core trust decision.
- Human review, branch protection, and protected workflow ownership remain
  required before merge.
