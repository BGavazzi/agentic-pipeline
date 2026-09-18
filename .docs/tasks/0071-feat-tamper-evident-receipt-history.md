---
status: in_progress
priority: P1
type: feat
created: 2026-09-18
updated: 2026-09-18
clickup_id: null
parent: 0058-feat-test-result-history
blocks: []
blocked_by: []
---

# 0071 — Feature: make receipt history tamper-evident

## Context
The receipt journal is append-only and replayable, but append-only storage alone
does not expose whether a privileged process altered historical evidence outside
the normal API. SOTA quality systems need verifiable evidence provenance before
using history for trend, flake, or test-impact decisions.

## Problem
Operators could inspect a valid-looking SQLite journal without a deterministic
answer about whether its event sequence and receipt payload digests still match
the original append order.

## What To Do
- [x] Add a chained digest over immutable event identity and receipt digest.
- [x] Verify the chain without network access or mutation.
- [x] Expose chain validity and break counts in journal summaries.
- [x] Add replay tests for multi-event ordering and identity.
- [ ] Add protected archival/export and cross-run storage in deployment.

## Affected Files
- `scripts/receipt_journal.py`
- `tests/test_receipt_journal.py`

## Exit Conditions
- [x] New events carry a previous-event and event digest.
- [x] Summary reports invalid or incomplete chains as non-valid.
- [x] Existing append-only/idempotency behavior remains green.
- [ ] A protected external archive verifies the chain independently.

## Required Documentation (Closure Law)
- [x] `CHANGELOG.md` updated
- [x] `function-catalog` updated
- [x] `.agents/continuity-codex.md` updated
- [x] Tests passing
- [ ] PR approved (task only closes once review is APPROVED — see git-pr-workflow.md §4)

## Honest Backlog
The local chain detects mutation and replay inconsistencies but is not a remote
notary. Deployment still needs protected retention and an independent verifier.
