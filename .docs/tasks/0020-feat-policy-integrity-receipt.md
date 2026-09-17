---
status: todo
priority: P0
type: feat
created: 2026-09-16
updated: 2026-09-16
clickup_id: null
parent: null
blocks: []
blocked_by: []
---

# 0020 — feat: bind admission to a trusted policy-integrity receipt

## Context
The gate jobs already detect edits to workflows and gate scripts as high risk,
but receipt aggregation did not independently record whether the policy surface
changed. A candidate could therefore be described as green without a distinct
machine-readable policy-review obligation.

## Problem
Agent-authored CI configuration is part of the attack surface. Policy changes
must be visible, versioned, and non-admissible until the protected review path
handles them. The receipt must not imply that a PR-controlled workflow is a
cryptographic trust boundary.

## What To Do
- [x] Hash the policy surface from the protected base reference.
- [x] Emit exact base/head identity and changed policy file list.
- [x] Require a policy receipt in receipt aggregation and admission.
- [x] Mark workflow/gate-script changes `review_required` → blocking `fail`.
- [ ] Move the final policy loader to a protected reusable workflow outside the
  candidate repository.

## Affected Files
- `scripts/policy_integrity.py`
- `scripts/ci_receipts.py`
- `scripts/admission_gate.py`
- `.github/workflows/ci.yml`
- `tests/test_policy_integrity.py`

## Exit Conditions
- [x] Product-only changes produce policy PASS.
- [x] Workflow changes produce policy review-required evidence.
- [x] Missing/stale policy evidence cannot admit.
- [x] Full test suite and fixture corpus pass.
- [ ] Protected reusable workflow owns final policy execution.
- [ ] PR approved and merged.

## Required Documentation (Closure Law)
- [x] `CHANGELOG.md` updated
- [x] `function-catalog.md` updated
- [ ] `SDD_KIT.md` updated — decision remains pending human ratification
- [x] `README.md` updated
- [ ] `.agents/continuity-<agent>.md` updated
- [x] Tests passing
- [ ] `route_map` updated — no route/handler/model change
- [ ] PR approved

## Honest Backlog
- This receipt improves detection and admission semantics but cannot protect a
  workflow that has already been replaced by an attacker. A protected reusable
  workflow or organization-level branch policy remains necessary for that final
  trust boundary.
