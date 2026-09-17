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

# 0025 — infra: add machine-checkable worker preflight contract

## Context
The homelab runbook defines an ephemeral/JIT lifecycle, but a worker can still
start a job without proving that it is single-use, clean, secret-free, and
correctly labelled. This is the operational gap left after task 0013's policy
and SLO documentation.

## Problem
Routing is a string decision; worker trust is a runtime fact. A persistent
self-hosted runner or a fork PR accidentally routed to the pool must fail
before checkout, with evidence that explains why. The check must be
deterministic and safe to call from a worker wrapper.

## What To Do
- [x] Add `worker_preflight.py` with a fail-closed worker trust contract.
- [x] Block fork/self-hosted combinations, persistent workers, stale worker
      age, dirty workspaces, mounted secrets, missing pool labels, and missing
      Docker when required.
- [x] Emit schema-v1 metrics for worker age, cleanup, secrets, Docker, and
      fork-to-pool routing.
- [x] Add unit tests covering safe and unsafe worker states.
- [x] Document invocation and operational limits in the homelab runbook.
- [x] Add the preflight to core sync and high-risk gate classification.

## Affected Files
- `scripts/worker_preflight.py`
- `tests/test_worker_preflight.py`
- `scripts/core_sync.py`
- `scripts/blast_radius.py`
- `.docs/runbooks/homelab-runner-pool.md`

## Exit Conditions
- [x] A clean ephemeral homelab worker produces an eligible receipt.
- [x] Unsafe worker states are blocked deterministically.
- [x] Fork PRs remain eligible only on GitHub-hosted workers.
- [x] No secrets or host-specific credentials are stored in the repository.
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
- The contract cannot inspect a host's kernel, hypervisor, or process table by
  itself. The wrapper must supply truthful measurements, and the stronger
  isolation tier remains a disposable VM/container.
- Registration and one real homelab job remain host-side operator actions.
