---
status: todo
priority: P2
type: feat
created: 2026-09-16
updated: 2026-09-16
clickup_id: null
parent: 0040
blocks: []
blocked_by: []
---

# 0041 — Feature: append-only local quality receipt journal

## Context
The framework now emits per-PR receipts and a denominator-first dashboard, but
file-based collection can lose duplicates or overwrite evidence when workers
run concurrently. SOTA test-impact systems separate result ingestion from
selection and preserve replayable history.

## Problem
Quality evidence needs durable, idempotent ingestion before it can support
cross-run metrics, lag measurement or worker-pool operations. A mutable JSON
summary is not enough to reconstruct what happened.

## What To Do
- [ ] Store immutable receipt events in a local SQLite WAL journal.
- [ ] Reject conflicting event IDs and make identical replays idempotent.
- [ ] Expose event, candidate-pair, status and time-range metrics.
- [ ] Reject updates/deletes through database triggers.
- [ ] Keep the journal local and receipt payloads credential-free.

## Affected Files
- `scripts/receipt_journal.py`
- `tests/test_receipt_journal.py`
- `README.md`, `CHANGELOG.md`

## Exit Conditions
- [ ] Concurrent-safe append path is transactional and replayable.
- [ ] Duplicate and conflicting evidence behavior is deterministic.
- [ ] Journal is descriptive and cannot override admission.
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
This is intentionally a single-host journal. Cross-host replication, signed
controller receipts, retention and privacy policy are later trust-boundary work.
