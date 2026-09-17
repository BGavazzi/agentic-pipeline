---
status: in_progress
priority: P0
type: feat
created: 2026-09-16
updated: 2026-09-16
clickup_id: null
parent: 0024
blocks: []
blocked_by: []
---

# 0031 — feat: open staging-review PRs from eligible receipts

## Context
Task 0024 established the autonomous-to-staging eligibility receipt, but the
final handoff still required a bespoke agent or shell sequence. The intended
workflow is now explicit: autonomous tests and gates produce evidence, then a
human receives a staging PR without the system merging it.

## Problem
A naive PR adapter could open a PR for stale, blocked, or already-submitted
evidence, or invoke `gh` through shell text. The handoff must validate exact
candidate identity, be idempotent, and keep the human-review boundary intact.

## What To Do
- [x] Add `staging_pr.py` to validate eligible schema-v1 receipts and exact
      candidate SHA.
- [x] Detect an existing open PR for the candidate head before creating one.
- [x] Invoke `gh pr create` with an argv list only; never merge or approve.
- [x] Add dry-run support and tests for blocked, duplicate, and planned paths.
- [x] Add the adapter to canonical sync, high-risk, and policy surfaces.
- [x] Document the staging handoff contract and human-review boundary.

## Affected Files
- `scripts/staging_pr.py`
- `tests/test_staging_pr.py`
- `scripts/core_sync.py`
- `scripts/blast_radius.py`
- `scripts/policy_integrity.py`

## Exit Conditions
- [x] Blocked/stale receipts cannot reach `gh`.
- [x] Existing open staging PRs are not duplicated.
- [x] Dry-run returns the exact planned argv without external mutation.
- [x] Successful creation remains a PR-only action; no merge/approval path
      exists in the adapter.
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
- This adapter is intentionally opt-in; a repository-specific dispatcher still
  decides when an eligible receipt should request a staging PR.
- The GitHub account/token and branch protection remain external trust inputs.
