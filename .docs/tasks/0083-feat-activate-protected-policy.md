---
status: todo
priority: P0
type: feat
created: 2026-09-18
updated: 2026-09-18
clickup_id: null
parent: 0021
blocks: []
blocked_by: []
---

# 0083 — [Feat]: Activate protected policy admission

## Context
The repository already contains a reusable workflow that runs policy
integrity from an immutable core revision, but no default-branch-owned caller
activated it. That left policy diagnostics and policy authority too easy to
confuse.

## Problem
Candidate code must not be able to remove admission obligations by changing
`admission_gate.py`, `blast_radius.py`, or the caller workflow. Admission must
be evaluated by a pull-request-target workflow whose caller and implementation
are outside the candidate diff. Candidate-local CI remains diagnostic; the
protected check must be required by branch protection.

## What To Do
- [x] Add a default-branch-owned `pull_request_target` caller.
- [x] Pin the reusable workflow and `core_ref` to the same immutable SHA.
- [x] Pass exact base/head SHAs and a deterministic PR-scoped task identifier.
- [x] Add workflow regression coverage for no candidate-local fallback.
- [ ] Configure branch protection to require the protected check.
- [ ] Maintain/rotate the immutable policy SHA after reviewed policy releases.

## Affected Files
- `.github/workflows/protected-policy.yml`
- `.github/workflows/policy-gate-reusable.yml`
- `tests/test_protected_policy_workflow.py`
- `.docs/runbooks/protected-policy-workflow.md`

## Exit Conditions
- [x] Pull requests trigger a protected-policy check from the default branch.
- [x] Candidate-local policy receipts remain diagnostic only.
- [x] Missing protected policy evidence is represented by a failing required check.
- [x] Workflow regression tests pass.
- [ ] GitHub branch protection requires `Protected policy integrity`.
- [ ] PR receives independent review and approval.

## Required Documentation (Closure Law)
- [x] `CHANGELOG.md` updated
- [x] `README.md` updated
- [x] `.agents/continuity-codex.md` updated
- [x] Tests passing
- [ ] `function-catalog.md` updated (workflow-only change)
- [ ] PR approved (task only closes once review is APPROVED — see git-pr-workflow.md §4)

## Honest Backlog
The workflow cannot mutate repository branch protection. Until the protected
check is required in GitHub settings, this is an enforced CI dependency but
not yet an immutable merge-control boundary.
