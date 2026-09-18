---
status: in_progress
priority: P1
type: feat
created: 2026-09-18
updated: 2026-09-18
clickup_id: null
parent: 0058
blocks: []
blocked_by: []
---

# 0060 — Feature: explicit flaky-test governance

## Context
Agentic CI needs to distinguish a real regression from a flaky test without
turning retries into false green evidence. The new per-test history can detect
pass/fail oscillation, but it needs an explicit owner/expiry policy.

## Problem
There is no quarantine manifest, expiry enforcement or machine-readable state
that tells an agent whether a flaky test is contained, overdue or unowned.

## What To Do
- [x] Add a schema-versioned quarantine manifest with owner, reason and expiry.
- [x] Add a deterministic flake gate consuming per-test history.
- [x] Emit flaky, active, expired, unquarantined and coverage metrics.
- [x] Make active quarantine `degraded`, never `pass`; expired/unowned flakes
      block.
- [ ] Wire real JUnit ingestion and expiry alerts in a later operational slice.

## Affected Files
- `scripts/flake_gate.py`
- `tests/test_flake_gate.py`
- `README.md`, `CHANGELOG.md`, `.docs/function-catalog.md`

## Exit Conditions
- [x] Policy is explicit, deterministic and fail-closed.
- [x] Quarantine cannot be mistaken for green admission.
- [x] Tests and closure validators pass.
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
This contract does not silently retry tests, ingest hosted JUnit history or
automatically create quarantine entries. The full suite remains authoritative.
