---
status: in_progress
priority: P1
type: feat
created: 2026-09-18
updated: 2026-09-18
clickup_id: null
parent: 0066-feat-local-integration-loop
blocks: []
blocked_by: []
---

# 0077 — Feature: surface deterministic quality metrics on PRs

## Context
The trusted PR summary publisher linked to diagnostics but made humans open the
workflow before seeing the basic risk-routing signals.

## Problem
Risk-aware review is slower when changed-file count, churn, candidate/base
identity, contact surfaces, and the deterministic HITL checkpoint are hidden in
logs or artifacts.

## What To Do
- [x] Add exact candidate and base SHA to the trusted summary.
- [x] Surface changed files, churn, deterministic HITL status, and contact
      surfaces in a compact table.
- [x] Keep the publisher metadata-only: no checkout or candidate execution.
- [x] Add workflow contract coverage.
- [ ] Add artifact-derived gate/impact metrics after a safe validated artifact
      reader is deployed.

## Affected Files
- `.github/workflows/pr-summary.yml`
- `tests/test_pr_summary_workflow.py`

## Exit Conditions
- [x] Acute changes are visibly marked before staging.
- [x] Routine changes still show standard review instead of false green.
- [x] Candidate code is not checked out or executed by the publisher.
- [x] Tests pass.
- [ ] Artifact-derived metrics are added without trusting candidate content.

## Required Documentation (Closure Law)
- [x] `CHANGELOG.md` updated
- [N/A] `function-catalog` — no production Python signature changed
- [N/A] `SDD_KIT` — no new architecture decision required
- [x] `README.md` updated (PR summary behavior is documented by the task)
- [x] `.agents/continuity-codex.md` updated
- [x] Tests passing
- [N/A] `ROUTE_BEHAVIOR_MAP` — no HTTP routes
- [ ] PR approved (task remains in progress until review)

## Honest Backlog
The publisher intentionally shows only metadata-derived metrics. It does not
parse or execute candidate artifacts; a future artifact reader needs its own
schema and trust boundary.
