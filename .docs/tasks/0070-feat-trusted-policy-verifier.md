---
status: in_progress
priority: P0
type: feat
created: 2026-09-18
updated: 2026-09-18
clickup_id: null
parent: 0067-docs-agentic-sdlc-testing-sota
blocks: []
blocked_by: []
---

# 0070 — Feature: add a fail-closed trusted-policy verifier

## Context
The repository has protected workflow material and policy-integrity receipts,
but no small deterministic contract that binds the policy receipt, exact-head
review, immutable policy pin, and protected producer attestation together.

## Problem
Without this adapter, downstream admission code must infer trust from several
independent artifacts. That creates a dangerous gap between “evidence exists”
and “evidence was produced by the protected control plane for this exact code.”

## What To Do
- [x] Verify exact base/head identity and a full immutable policy reference.
- [x] Require independent exact-head review evidence.
- [x] Require a protected producer attestation with workflow and run identity.
- [x] Fail closed for absent, stale, mismatched, or unprotected evidence.
- [x] Add unit coverage and inventory the verifier as a high-risk policy script.
- [ ] Wire the verifier into the protected external producer after deployment of
      the immutable policy pin (external activation, not simulated locally).

## Affected Files
- `scripts/trusted_policy.py`
- `tests/test_trusted_policy.py`
- `scripts/policy_integrity.py`
- `scripts/core_sync.py`
- `scripts/blast_radius.py`

## Exit Conditions
- [x] Valid protected evidence passes only for the exact commit pair.
- [x] Missing or mismatched trust evidence is blocked.
- [x] Focused and full test suites pass.
- [ ] Protected workflow invokes the verifier with an externally authenticated
      attestation.

## Required Documentation (Closure Law)
- [x] `CHANGELOG.md` updated
- [x] `README.md` updated (no end-user CLI contract change)
- [x] `function-catalog` updated
- [x] `.agents/continuity-codex.md` updated
- [x] Tests passing
- [ ] PR approved (task only closes once review is APPROVED — see git-pr-workflow.md §4)

## Honest Backlog
The verifier cannot create trust. Protected branch configuration, immutable
policy pinning, and producer identity remain deployment-owned controls.
