---
status: in_progress
priority: P0
type: feat
created: 2026-09-18
updated: 2026-09-18
clickup_id: null
parent: 0057-audit-sota-agentic-harness-capabilities
blocks: []
blocked_by: []
---

# 0074 — Feature: require verified worker network policy

## Context
The worker preflight already requires ephemeral lifecycle, clean workspace,
zero mounted secrets, and an explicit pool label. Agent-generated code can still
be dangerous if a self-hosted worker has unrestricted egress.

## Problem
Docker reachability and secret absence do not prove that a homelab worker's
network policy is constrained or observed.

## What To Do
- [x] Add a required `network_policy_verified` self-hosted fact.
- [x] Block self-hosted workers when the fact is absent or false.
- [x] Propagate the fact through the supervisor and runbook.
- [x] Add adversarial preflight and supervisor fixtures.
- [ ] Implement host-level network policy attestation in the homelab adapter.

## Affected Files
- `scripts/worker_preflight.py`
- `scripts/worker_supervisor.py`
- `tests/test_worker_preflight.py`
- `tests/test_worker_supervisor.py`
- `.docs/runbooks/homelab-runner-pool.md`

## Exit Conditions
- [x] Unverified self-hosted network policy is fail-closed.
- [x] GitHub-hosted and fork routing behavior is unchanged.
- [x] Focused tests pass.
- [ ] Host adapter emits independently verified network facts.

## Required Documentation (Closure Law)
- [x] `CHANGELOG.md` updated
- [x] `function-catalog` updated
- [N/A] `SDD_KIT` — no new architecture decision required
- [x] `README.md` updated (runbook is the relevant operator documentation)
- [x] `.agents/continuity-codex.md` updated
- [x] Tests passing
- [N/A] `ROUTE_BEHAVIOR_MAP` — no HTTP routes
- [ ] PR approved (task remains in progress until review)

## Honest Backlog
The boolean is a contract boundary, not proof by itself. The homelab host
adapter must produce it from an independently trusted network observation.
