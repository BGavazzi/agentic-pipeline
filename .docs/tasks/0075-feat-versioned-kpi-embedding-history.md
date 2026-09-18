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

# 0075 — Feature: retain versioned KPI vectors and long-run variance

## Context
Agentic CI produces many receipts and logs. Long-term analysis needs signal
variance and drift without retaining sensitive raw logs in every analytics
system.

## Problem
Existing telemetry emits provider-neutral metrics but has no compact, versioned
feature-vector store or deterministic rolling statistics for KPI behavior.

## What To Do
- [x] Extract finite numeric KPIs into a sorted, schema-versioned vector.
- [x] Retain input hashes and commit/run identity instead of raw report bodies.
- [x] Add append-only SQLite storage with idempotent run handling.
- [x] Report mean, variance, standard deviation, min/max, p95, freshness and
      bounded windows.
- [x] Mark the vector descriptive-only and non-authoritative for admission.
- [ ] Add protected long-term archival/retention and an external dashboard.

## Affected Files
- `scripts/kpi_history.py`
- `tests/test_kpi_history.py`

## Exit Conditions
- [x] KPI vectors are deterministic and versioned.
- [x] Long-run variance is queryable without raw-log retention.
- [x] Duplicate and conflicting run IDs are handled deterministically.
- [x] Tests pass.
- [ ] Protected archival and dashboard deployment exist.

## Required Documentation (Closure Law)
- [x] `CHANGELOG.md` updated
- [x] `function-catalog` updated
- [N/A] `SDD_KIT` — no new architecture decision required
- [x] `README.md` updated (feature is documented in the task)
- [x] `.agents/continuity-codex.md` updated
- [x] Tests passing
- [N/A] `ROUTE_BEHAVIOR_MAP` — no HTTP routes
- [ ] PR approved (task remains in progress until review)

## Honest Backlog
This is a deterministic numeric feature vector, not a semantic-model embedding.
It must not become a hidden admission score; protected retention and visualization
remain deployment work.
