---
status: in_progress
priority: P0
type: infra
created: 2026-09-16
updated: 2026-09-16
clickup_id: null
parent: 0013
blocks: []
blocked_by: []
---

# 0033 — infra: enforce one-shot worker lifecycle

## Context
Task 0013 documented the trust boundary and required ephemeral/JIT workers,
but the repository had no host-side supervisor contract to enforce the
single-use lifecycle. A label and a preflight receipt alone do not prove that a
worker deregistered or that its workspace was cleaned after candidate code ran.

## Problem
Persistent self-hosted runners accumulate state and credentials across jobs.
The pool needs a machine-checkable boundary: reject unsafe facts before launch,
run one argv-only process, then require post-run evidence for exactly one job,
zero mounted secrets, a clean workspace, and deregistration. Failure must be
visible and must never become a green receipt.

## What To Do
- [x] Add `scripts/worker_supervisor.py` with preflight, one-shot execution,
      timeout handling, postcondition checks, and versioned operational metrics.
- [x] Keep registration-token minting and runner registration outside the repo;
      the supervisor only consumes facts and a command.
- [x] Add tests for clean completion, persistent-worker rejection, and cleanup
      or deregistration failure.
- [x] Add the supervisor to canonical sync and policy/risk surfaces.
- [x] Document the host/operator integration contract in the runbook.

## Affected Files
- `scripts/worker_supervisor.py`
- `tests/test_worker_supervisor.py`
- `scripts/core_sync.py`
- `scripts/blast_radius.py`
- `scripts/policy_integrity.py`
- `.docs/runbooks/homelab-runner-pool.md`
- `README.md`
- `CHANGELOG.md`

## Exit Conditions
- [x] Unsafe self-hosted facts block before the worker command launches.
- [x] Worker execution uses an argv list, a scrubbed environment, and a
      bounded timeout.
- [x] Missing/dirty/unregistered post-run evidence fails closed.
- [x] Receipt metrics include queue wait, worker age, cleanup, deregistration,
      secrets, duration, and exit status.
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
- The host operator must still configure the GitHub runner in ephemeral/JIT
  mode and write the pre/post facts. This task does not mint tokens, register
  runners, or automate changes on the confidential homelab host.
- Stronger isolation such as a disposable VM/container boundary remains the
  next tier beyond process supervision.
