---
status: in_progress
priority: P1
type: feat
created: 2026-09-18
updated: 2026-09-18
clickup_id: null
parent: 0067-docs-agentic-sdlc-testing-sota
blocks: []
blocked_by: []
---

# 0069 — Feature: measure test-impact selector regret and bounded load

## Context
The harness already benchmarks test-impact precision and recall, but a single
mean can hide missed-test regret, fallback frequency, and selector behavior under
repeat load. Those are required before any future optimization can be considered
for promotion.

## Problem
The benchmark did not expose a stable regret metric, fallback rate, p95 case
latency, or bounded throughput. Operators therefore could not distinguish a
selector that is conservative because it is slow from one that is safely precise.

## What To Do
- [x] Add per-case selection regret, selection ratio, and duration metrics.
- [x] Add repeated-corpus iterations with fallback-rate, p95-latency, regret,
      and throughput summaries.
- [x] Bump the benchmark identity and keep promotion fail-closed on the new
      version.
- [x] Add deterministic tests for metrics and repeated execution.
- [ ] Collect a larger representative portfolio corpus before changing the
      full-suite authority (the current fixtures remain calibration-only).

## Affected Files
- `scripts/impact_benchmark.py`
- `scripts/impact_promotion.py`
- `tests/test_impact_benchmark.py`

## Exit Conditions
- [x] The benchmark reports selector regret and bounded load metrics.
- [x] A promotion receipt rejects stale benchmark identity.
- [x] Existing impact fixtures and the full test suite pass.
- [ ] A representative corpus demonstrates acceptable regret and latency.

## Required Documentation (Closure Law)
- [x] `CHANGELOG.md` updated
- [x] `README.md` updated (not a user-facing CLI contract change)
- [x] `.agents/continuity-codex.md` updated
- [x] Tests passing
- [ ] PR approved (task only closes once review is APPROVED — see git-pr-workflow.md §4)

## Honest Backlog
Promotion remains blocked until the corpus includes representative repositories
and the result is reviewed in the protected promotion context.
