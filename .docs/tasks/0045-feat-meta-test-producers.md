---
status: in_progress
priority: P1
type: feat
created: 2026-09-17
updated: 2026-09-17
clickup_id: null
parent: null
blocks: []
blocked_by: [0044]
---

# 0045 — Independent meta-test and review producer evidence

## Context
Handoff W3 follows the external worker-boundary contract in task 0044. The
pipeline already had disposable fixture and review runners, but aggregation
accepted receipts without producer provenance and the reviewer wrapper
inherited the host environment wholesale.

## Problem
An agent can report that tests passed, a task is closed, or a review was
independent without an independently observable basis. The harness needs a
separate observer contract, bounded output, obvious credential filtering, and
fresh producer metadata before those receipts can participate in admission.

## What To Do
- [x] Emit versioned producer envelopes for meta-test dispatch and ultrareview.
- [x] Require an independent observer when requested by the trusted dispatcher.
- [x] Filter obvious inherited credentials and bound reviewer output.
- [x] Reject aggregated meta-test/ultrareview receipts without producer proof.
- [x] Add planted-fault fixtures for forbidden writes, closure lies and prompt injection.
- [ ] Run a real pool-backed agent against the corpus.

## Affected Files
- `scripts/meta_test.py`
- `scripts/meta_test_dispatch.py`
- `scripts/ultrareview_runner.py`
- `scripts/ci_receipts.py`
- `tests/test_meta_test_adversarial_fixtures.py`
- `tests/skills/fixtures/`
- `tests/test_meta_test_dispatch.py`, `tests/test_ultrareview_runner.py`, `tests/test_ci_receipts.py`

## Exit Conditions
- [x] A planted forbidden-file write is rejected from observed tree state.
- [x] Worker-declared test success cannot override a failing independent observer.
- [x] Missing producer envelope is rejected by receipt aggregation.
- [x] Reviewer execution does not inherit obvious secret variables.
- [x] Producer evidence includes fresh invocation, role and command/corpus provenance.
- [ ] At least one real external worker completes the synthetic corpus.

## Required Documentation (Closure Law)
- [x] `CHANGELOG.md` updated.
- [x] `<function_catalog>` updated.
- [N/A] `<sdd_kit_path>`: no architectural decision ratified in this packet.
- [x] `README.md` updated.
- [x] `.agents/continuity-codex.md` updated.
- [x] Tests passing.
- [N/A] `<route_map>`: no web route changed.
- [ ] PR approved.

## Honest Backlog
This packet proves producer consistency and local adversarial controls, not
authenticity. A protected caller, real independent reviewer identity, external
worker boundary, and homelab pilot remain deployment gates. The corpus is still
small and synthetic; no general agent reliability or security score is implied.
