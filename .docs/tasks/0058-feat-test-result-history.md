---
status: in_progress
priority: P1
type: feat
created: 2026-09-18
updated: 2026-09-18
clickup_id: null
parent: 0057
blocks: []
blocked_by: []
---

# 0058 — Feature: per-test result history and freshness metrics

## Context
The harness has conservative static test-impact selection and a holdout
benchmark, but no replayable per-test history. SOTA impact-analysis systems
separate result ingestion from selection and measure lag before relying on the
optimization.

## Problem
Receipt-level telemetry cannot answer which tests are stale, flaky, slow or
recently failing. Adding retries without history would hide instability rather
than make agentic CI more reliable.

## What To Do
- [x] Add versioned per-test result events to the append-only local journal.
- [x] Make event replay idempotent and conflicting IDs fail closed.
- [x] Emit deterministic freshness, stale-test, flaky-test, duration and latest
      status metrics with an explicit reference time.
- [x] Add CLI contracts and focused tests.
- [ ] Keep selection promotion separate until a larger corpus and operational
      listener/lag SLO exist.

## Affected Files
- `scripts/receipt_journal.py`
- `tests/test_test_result_history.py`
- `README.md`, `CHANGELOG.md`, `.docs/function-catalog.md`

## Exit Conditions
- [x] Per-test history is append-only and replayable.
- [x] Freshness and flakiness are measured with denominators.
- [x] History cannot override admission or authorize skipped tests.
- [x] Tests and closure validators pass.
- [ ] PR approved.

## Required Documentation (Closure Law)
- [x] `CHANGELOG.md` updated
- [x] `<function_catalog>` updated
- [N/A] `<sdd_kit_path>`: no new architectural decision record
- [x] `README.md` updated
- [x] `.agents/continuity-codex.md` updated
- [x] Tests passing
- [N/A] `<route_map>`: no route changed
- [ ] PR approved

## Honest Backlog
This is a local journal extension, not a horizontally scaled listener, remote
event sink, OpenTelemetry exporter or TIA promotion policy. The full suite
remains authoritative.
