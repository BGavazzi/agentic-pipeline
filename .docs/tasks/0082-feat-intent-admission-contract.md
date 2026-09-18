---
status: todo
priority: P0
type: feat
created: 2026-09-18
updated: 2026-09-18
clickup_id: null
parent: 0081
blocks: []
blocked_by: []
---

# 0082 — [Feat]: Carry intent evidence into risk and admission

## Context
Task 0081 established a deterministic, evidence-only intent contract. This
task makes that evidence operational for consequential changes: medium- and
high-risk diffs must provide a report bound to the exact candidate tree before
the existing admission and staging surfaces can treat them as eligible.

## Problem
An intent report that exists only as a local CLI is easy to omit from CI. The
risk classifier, receipt adapter, and admission gate therefore need one
versioned path for missing, stale, malformed, or failed intent evidence. The
candidate's contract remains untrusted; protected policy and human review are
still authoritative.

## What To Do
- [x] Add `intent` to medium/high deterministic risk obligations.
- [x] Emit explicit fail-closed evidence when the contract is missing.
- [x] Carry intent status and provenance through `ci_receipts.py`.
- [x] Run the intent gate in CI for medium/high-risk changes and opt-in low-risk changes.
- [x] Add adversarial receipt and admission coverage.
- [ ] Move intent-policy production to a protected producer outside candidate code.

## Affected Files
- `scripts/blast_radius.py`
- `scripts/intent_gate.py`
- `scripts/ci_receipts.py`
- `scripts/admission_gate.py`
- `.github/workflows/ci.yml`
- `tests/test_ci_receipts.py`
- `tests/test_admission_gate.py`
- `tests/harness/fixtures/002-admission-missing-integration.json`
- `.docs/intent/0082.json`

## Exit Conditions
- [x] Medium/high risk reports require `intent` in their gate obligations.
- [x] Missing, failed, stale, or malformed intent evidence cannot admit.
- [x] Low-risk legacy changes remain compatible when no intent contract is supplied.
- [x] Tests and the full local harness pass.
- [ ] Protected producer and independent policy authority are deployed.
- [ ] PR receives independent review and approval.

## Required Documentation (Closure Law)
- [x] `CHANGELOG.md` updated
- [x] `.docs/function-catalog.md` updated
- [ ] `<sdd_kit_path>` updated (no new decision record)
- [x] `README.md` updated
- [x] `.agents/continuity-codex.md` updated
- [x] Tests passing
- [x] `<route_map>` unchanged
- [ ] PR approved (task only closes once review is APPROVED — see git-pr-workflow.md §4)

## Honest Backlog
The CI job executes candidate-tree code, so intent reports are consistency
evidence rather than authorization. A protected producer and policy source
outside the candidate checkout are required before this becomes a security
boundary.
