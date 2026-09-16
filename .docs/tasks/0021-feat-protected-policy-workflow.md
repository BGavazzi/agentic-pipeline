---
status: todo
priority: P0
type: feat
created: 2026-09-16
updated: 2026-09-16
clickup_id: null
parent: 0020
blocks: []
blocked_by: []
---

# 0021 — feat: execute policy integrity from a protected reusable workflow

## Context
Task 0020 makes policy changes visible and blocking, but a candidate-controlled
workflow is not a final trust anchor. GitHub reusable workflows allow consuming
repositories to pin policy execution to a reviewed immutable core commit.

## Problem
An agent that can edit its own CI could otherwise remove or weaken the local
policy job. The framework needs a rollout mechanism where branch protection
requires a job whose implementation is loaded from a protected SHA outside the
candidate diff.

## What To Do
- [x] Add a `workflow_call` reusable policy gate with required immutable inputs.
- [x] Check out the candidate and pinned core separately.
- [x] Route all caller inputs through environment variables before shell use.
- [x] Document branch-protection rollout and no-secret posture.
- [ ] Migrate each consuming repository to a reviewed immutable core SHA.

## Affected Files
- `.github/workflows/policy-gate-reusable.yml`
- `.docs/runbooks/protected-policy-workflow.md`
- `tests/test_protected_policy_workflow.py`

## Exit Conditions
- [x] Workflow requires `core_ref`, `base_sha`, `head_sha`, and `task_id`.
- [x] Workflow has read-only permissions and no inherited secrets.
- [x] Candidate policy changes remain non-admissible.
- [ ] Agentic-pipeline branch protection requires the protected check.
- [ ] Portfolio consumers migrated and smoke-tested.
- [ ] PR approved and merged.

## Required Documentation (Closure Law)
- [x] `CHANGELOG.md` updated
- [ ] `function-catalog.md` updated — no Python API changed
- [ ] `SDD_KIT.md` updated — pending human ratification
- [x] `README.md` updated
- [ ] `.agents/continuity-<agent>.md` updated
- [x] Tests added
- [ ] `route_map` updated — no route/handler/model change
- [ ] PR approved

## Honest Backlog
- This PR cannot activate branch protection or migrate portfolio repositories
  automatically; those are deployment/administrative actions requiring the
  immutable commit after merge.
