---
status: in_progress
priority: P1
type: fix
created: 2026-09-16
updated: 2026-09-16
clickup_id: null
parent: 0019
blocks: []
blocked_by: []
---

# 0028 — fix: close the transitive test-impact gap

## Context
The versioned impact benchmark intentionally exposed a transitive-import gap:
when `test_service` imported `service`, and `service` imported changed
`shared`, the conservative selector only selected `test_shared`. The benchmark
reported recall `0.5` and correctly kept `promotion_ready=false`.

## Problem
Direct-import matching is useful evidence but is not enough for agentic code
throughput. The selector needs a bounded reverse dependency closure while
remaining optimization-only and falling back to the full suite for unknown
files/modules.

## What To Do
- [x] Build a reverse Python import graph over tracked files.
- [x] Traverse the transitive reverse-import closure from changed modules.
- [x] Correct absolute `ImportFrom` parsing so package names are not doubled.
- [x] Add closure-size metrics to per-case benchmark output.
- [x] Version the benchmark contract to `0.2` and require recall 1.0 in the
      transitive fixture.
- [x] Keep full-suite fallback and shadow-only policy unchanged.

## Affected Files
- `scripts/test_impact.py`
- `scripts/impact_benchmark.py`
- `tests/test_test_impact.py`
- `tests/test_impact_benchmark.py`
- `tests/impact/fixtures/002-transitive-import.json`

## Exit Conditions
- [x] The transitive fixture selects both relevant tests with recall 1.0.
- [x] Benchmark reports `promotion_ready=true` with mean recall 1.0.
- [x] Unknown/non-Python changes still fall back to the full suite.
- [x] Full test suite and repository validators pass.

## Required Documentation (Closure Law)
- [x] `CHANGELOG.md` updated
- [N/A] `function-catalog.md` — no function catalog exists
- [N/A] `SDD_KIT.md` — no new product decision
- [x] `README.md` updated
- [N/A] `.agents/continuity-<agent>.md` — no continuity file in this checkout
- [x] Tests passing
- [N/A] `ROUTE_BEHAVIOR_MAP.md` — no route/handler/model change
- [ ] PR approved

## Honest Backlog
- Dynamic imports, generated code, and non-Python dependency graphs remain
  fallback cases. This change does not authorize skipping the full suite.
- Benchmark promotion readiness is a metric, not permission to remove the
  authoritative integration gate.
