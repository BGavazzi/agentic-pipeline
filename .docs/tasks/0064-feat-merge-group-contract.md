---
status: in_progress
priority: P1
type: feat
created: 2026-09-18
updated: 2026-09-18
clickup_id: null
parent: 0057
blocks: []
blocked_by: []
---

# 0064 — Feature: merge-group compatibility contract

## Context
Merge queues dispatch `merge_group` events rather than ordinary pull-request
events. A workflow that omits that trigger can leave required checks absent or
stale at the exact point a queued merge is assembled.

## Problem
The harness had no machine-readable contract for merge-group commit/ref
identity and no explicit evidence boundary distinguishing event validity from
actual check completion or deployment safety.

## What To Do
- [x] Declare the `merge_group` CI trigger.
- [x] Add a deterministic, fail-closed merge-group identity contract and tests.
- [x] Emit an explicit contract artifact listing expected checks without
      pretending they were observed or admitted.
- [ ] Configure protected branch rules/merge queue and verify required checks
      in the GitHub control plane as a separate operator action.
- [ ] Add post-deploy health and rollback evidence for a real deploy target.

## Affected Files
- `scripts/merge_group_contract.py`
- `tests/test_merge_group_contract.py`, `tests/test_merge_group_workflow.py`
- `.github/workflows/ci.yml`, `scripts/sota_audit.py`
- `README.md`, `CHANGELOG.md`, `.docs/function-catalog.md`

## Exit Conditions
- [x] Valid merge-group identity is normalized with base/head commit and refs.
- [x] Missing identity, wrong event and missing checks fail closed.
- [x] CI emits the contract artifact on merge-group events.
- [x] Tests and closure validators pass.
- [ ] Protected merge queue and rollback are activated.
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
This proves event identity only. It does not inspect branch-protection settings,
observe required check conclusions, authorize merge, verify deployment health,
or perform rollback.
