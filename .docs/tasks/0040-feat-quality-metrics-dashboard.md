---
status: todo
priority: P2
type: feat
created: 2026-09-16
updated: 2026-09-16
clickup_id: null
parent: 0037
blocks: []
blocked_by: []
---

# 0040 — Feature: denominator-first quality metrics dashboard

## Context
PR intelligence now exposes risk, contact surfaces, gate evidence and test
impact per change. Operational calibration needs an aggregate view with
denominators, sample-size warnings and explicit limitations.

## Problem
Individual PR comments do not show whether the framework is improving, whether
HITL is being triggered too late, or whether test-impact evidence is present.
Raw counts and weighted quality scores would be misleading on a small sample.

## What To Do
- [ ] Aggregate schema-v1 PR intelligence receipts from files/directories.
- [ ] Report risk, evidence, HITL, churn, test/source and impact metrics with denominators.
- [ ] Mark cohorts below 30 valid receipts as calibration-only.
- [ ] Preserve invalid-input counts and limitations instead of dropping them.
- [ ] Add JSON/Markdown output and unit coverage.

## Affected Files
- `scripts/quality_metrics_dashboard.py`
- `scripts/pr_intelligence.py`
- `tests/test_quality_metrics_dashboard.py`
- `README.md`, `CHANGELOG.md`

## Exit Conditions
- [ ] Dashboard is descriptive only and cannot override admission.
- [ ] Rates include denominators and small-sample warnings.
- [ ] Invalid receipts remain visible as an error count.
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
This first version is file-based and local to one repository. A durable event
journal, signatures and cross-repository aggregation remain separate work.
