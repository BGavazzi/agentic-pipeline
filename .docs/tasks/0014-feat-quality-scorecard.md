---
status: in_progress
priority: P1
type: feat
created: 2026-09-16
updated: 2026-09-16
clickup_id: null
parent: 0009
blocks: []
blocked_by: []
---

# 0014 — feat: deterministic quality scorecard

## Context
The admission framework now has risk, unit, scanner, clean-room integration,
and ultrareview receipt contracts. The next framework requirement is to measure
quality and completeness across changes without collapsing all dimensions into
an opaque model score. This task makes the metrics durable and comparable.

## Problem
Gate results alone answer "admit or block" but not "why," "how complete was
the evidence," or "did integration fan-out/cost change over time?" Without a
versioned scorecard, the portfolio cannot benchmark harness completeness or
detect queue/worker regressions.

## What To Do
- [x] Add schema/versioned `quality_scorecard.py` derived only from validated
      risk and receipt artifacts.
- [x] Emit evidence completeness, observed gate pass rate, risk triggers,
      changed/affected counts, integration duration/isolation, and reviewer
      independence when those artifacts exist.
- [x] Mirror admission as `green`/`blocked` without changing admission policy
      or treating partial evidence as pass.
- [x] Upload the scorecard from PR admission CI and add tests for complete,
      blocked, optional metrics, and stale identity.
- [x] Include the scorecard in core sync and high-risk gate-surface review.

## Affected Files
- `scripts/quality_scorecard.py`
- `.github/workflows/ci.yml`
- `scripts/core_sync.py`
- `scripts/blast_radius.py`
- `tests/test_quality_scorecard.py`
- `.docs/function-catalog.md`
- `.gitignore`
- `README.md`
- `CHANGELOG.md`
- `.agents/continuity-codex.md`

## Exit Conditions
- [x] Scorecard has schema/provenance and exact base/head identity.
- [x] Metrics are deterministic and derived from gate evidence, not model prose.
- [x] Blocked admission produces a `blocked` scorecard; incomplete evidence is
      never reported as green.
- [x] CI uploads the scorecard even when admission blocks.
- [x] Tests, validators, workflow YAML parse, and diff checks pass.
- [ ] PR approved — remains `in_progress` until review, per Closure Law.

## Required Documentation (Closure Law)
- [x] `CHANGELOG.md` updated
- [x] `.docs/function-catalog.md` updated (new public script signature)
- [N/A] `<sdd_kit_path>` — no SDD_KIT.md in this repo
- [x] `README.md` updated
- [x] `.agents/continuity-codex.md` updated
- [x] Tests passing
- [N/A] `<route_map>` — no web routes in this repo
- [ ] PR approved

## Honest Backlog
- The scorecard is a measurement artifact, not a learned quality model and
  does not claim that a green result means production safety.
- Historical time-series storage and portfolio dashboards are not included;
  CI artifacts are the current source of evidence.
- Cost/quota metrics and true base-vs-head differential findings remain future
  dimensions.
