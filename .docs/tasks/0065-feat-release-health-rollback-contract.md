---
status: in_progress
priority: P1
type: feat
created: 2026-09-18
updated: 2026-09-18
clickup_id: null
parent: 0064
blocks: []
blocked_by: []
---

# 0065 — Feature: post-deploy health and rollback evidence contract

## Context
The SOTA audit identified deployment verification and rollback as the remaining
merge/release safety gap. This repository has no single deploy target, so the
safe reusable slice is an evidence contract rather than an invented executor.

## Problem
A deployment surface needs commit/environment-bound health evidence and a
verified rollback plan, while candidate-controlled JSON must not be mistaken for
trusted production observation or cause arbitrary command execution.

## What To Do
- [x] Validate health status, named check coverage and candidate identity.
- [x] Validate a distinct rollback target, owner, runbook and dry-run marker.
- [x] Fail closed on stale identity, failed checks or unverified rollback.
- [x] Explicitly report no trusted producer, no command execution and no
      admission authority.
- [ ] Integrate a protected deploy provider, health producer and rollback
      executor for a specific application as a separate operational task.

## Affected Files
- `scripts/release_health_gate.py`
- `tests/test_release_health_gate.py`
- `scripts/sota_audit.py`, `scripts/blast_radius.py`, `scripts/core_sync.py`
- `README.md`, `CHANGELOG.md`, `.docs/function-catalog.md`

## Exit Conditions
- [x] Healthy evidence plus a valid rollback plan produces a descriptive pass.
- [x] Failed health and stale/unverified evidence block.
- [x] No command execution or trusted-producer claim is possible.
- [x] Tests and closure validators pass.
- [ ] Deploy provider, health source and rollback are activated.
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
This validates evidence only. It does not know a deployment provider, poll a
service, run a health check, execute rollback, or establish production authority.
