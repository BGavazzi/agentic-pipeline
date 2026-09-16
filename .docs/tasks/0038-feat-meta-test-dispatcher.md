---
status: todo
priority: P1
type: feat
created: 2026-09-16
updated: 2026-09-16
clickup_id: null
parent: 0032
blocks: []
blocked_by: []
---

# 0038 — Feature: trusted meta-test dispatcher adapter

## Context
Task 0032 established deterministic fixtures and a runtime-supplied worker
command, while task 0033 established the one-shot homelab lifecycle contract.
The missing integration layer was an explicit adapter that composes both
contracts into one receipt a protected dispatcher can upload to CI.

## Problem
Without an adapter, a worker can pass meta-test fixtures locally but the
system has no single receipt proving that the worker was ephemeral, cleaned up,
and deregistered. Conversely, lifecycle evidence alone says nothing about the
agent's observable code change.

## What To Do
- [ ] Compose `meta_test.py` and `worker_supervisor.py` with argv-only execution.
- [ ] Bind the resulting receipt to the exact candidate base/head SHAs.
- [ ] Refuse missing worker output or lifecycle cleanup proof; never synthesize pass.
- [ ] Add end-to-end tests for pass and blocked worker paths.
- [ ] Document the operator boundary and CI upload handoff.

## Affected Files
- `scripts/meta_test_dispatch.py`
- `tests/test_meta_test_dispatch.py`
- `README.md`, `CHANGELOG.md`

## Exit Conditions
- [ ] A compliant ephemeral worker produces one combined meta-test receipt.
- [ ] Unsafe worker facts produce an error/blocked result with zero fixture pass.
- [ ] Exact base/head identity is preserved.
- [ ] Tests and closure validators pass.

## Required Documentation (Closure Law)
- [ ] `CHANGELOG.md` updated
- [ ] `README.md` updated
- [ ] `function-catalog` unchanged (no public function catalog is maintained)
- [ ] `SDD_KIT` unchanged (no new decision record is needed)
- [ ] `.agents/continuity-<agent>.md` unchanged (no continuity handoff is part of this feature)
- [ ] `ROUTE_BEHAVIOR_MAP` unchanged (no route or handler changed)
- [ ] Tests passing
- [ ] PR opened for human review

## Honest Backlog
The actual GitHub runner registration, short-lived token minting, and post-facts
production remain host/operator responsibilities. This adapter does not claim
that a homelab worker exists or that a receipt is trusted merely because it is
JSON; protected workflow ownership and artifact provenance remain required.
