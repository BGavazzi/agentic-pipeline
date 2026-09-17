---
status: todo
priority: P1
type: feat
created: 2026-09-16
updated: 2026-09-16
clickup_id: null
parent: 0018
blocks: []
blocked_by: []
---

# 0019 — feat: benchmark test-impact precision and recall

## Context
Task 0018 runs test-impact selection in shadow mode but needs evidence before
the optimization can influence correctness admission. A versioned fixture corpus
provides repeatable before/after git histories and a declared relevant-test set.

## Problem
Selection ratio alone is not a quality metric. A fast subset with low recall is
unsafe, especially for transitive dependencies. The pipeline needs precision,
recall, fallback, and promotion-readiness metrics that can be tracked over time.

## What To Do
- [x] Add before/after git fixture manifests for direct, transitive, and
  non-Python changes.
- [x] Materialize fixtures and run the real `test_impact.analyze` implementation.
- [x] Emit per-case and aggregate precision/recall metrics.
- [x] Keep `promotion_ready` separate from successful benchmark execution.
- [ ] Improve transitive dependency recall before promoting selection.

## Affected Files
- `scripts/impact_benchmark.py`
- `tests/impact/fixtures/*.json`
- `tests/test_impact_benchmark.py`
- `.github/workflows/ci.yml`

## Exit Conditions
- [x] Benchmark runs from a clean checkout without external services.
- [x] Direct-import case reaches precision=1 and recall=1.
- [x] Known transitive-import limitation is visible in the report.
- [x] Non-Python changes prove full-suite fallback.
- [ ] `promotion_ready` becomes true for the supported impacted-mode class.
- [ ] PR approved and merged.

## Required Documentation (Closure Law)
- [ ] `CHANGELOG.md` updated
- [x] `function-catalog.md` updated
- [ ] `SDD_KIT.md` updated — no new ratified decision
- [x] `README.md` updated
- [ ] `.agents/continuity-<agent>.md` updated
- [x] Tests passing
- [ ] `route_map` updated — no route/handler/model change
- [ ] PR approved

## Honest Backlog
- The benchmark is intentionally not a merge-blocking admission criterion beyond
  requiring that the corpus executes. Its `promotion_ready: false` result is the
  correct current state, not a hidden failure.
