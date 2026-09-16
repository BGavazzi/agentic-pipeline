---
status: in_progress
priority: P0
type: infra
created: 2026-09-16
updated: 2026-09-16
clickup_id: null
parent: 0025
blocks: []
blocked_by: []
---

# 0026 — infra: wire worker preflight into CI execution lanes

## Context
Task 0025 defined a deterministic worker trust receipt, but a contract that is
never called cannot protect the homelab pool. The integration, unit, and
scanner lanes must execute preflight before candidate-controlled commands and
upload the evidence with their job artifacts.

## Problem
The route decision happens before a job is assigned, while worker facts such as
ephemeral state, prior-job age, cleanup, and mounted secrets are known only to
the worker supervisor. CI needs a fail-closed bridge between those facts and
the job's first execution step.

## What To Do
- [x] Add a JSON facts-file input to `worker_preflight.py` for runner
      supervisors; missing facts fail closed for self-hosted jobs.
- [x] Invoke preflight before tests, clean-room integration, and deterministic
      scanner gates.
- [x] Keep fork PRs on the hosted path and make the preflight receipt prove
      zero fork-to-pool routing.
- [x] Upload preflight evidence with each relevant job artifact.
- [x] Document the facts-file contract for homelab worker supervisors.

## Affected Files
- `.github/workflows/ci.yml`
- `scripts/worker_preflight.py`
- `tests/test_worker_preflight.py`
- `.docs/runbooks/homelab-runner-pool.md`

## Exit Conditions
- [x] A self-hosted lane cannot proceed without a supervisor facts file.
- [x] A hosted/fork lane produces an eligible preflight receipt without
      requiring homelab facts.
- [x] Preflight executes before candidate tests/scanners and its receipt is
      uploaded even when later steps fail.
- [x] Tests, workflow parsing, and repository validators pass.

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
- The facts file is supplied by the worker supervisor and cannot prove a
  malicious host is honest. Protected reusable workflow ownership and a
  disposable VM remain the stronger trust boundary.
- The live homelab supervisor still requires host-side registration and one
  real observed job.
