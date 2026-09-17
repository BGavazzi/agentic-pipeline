---
status: in_progress
priority: P1
type: feat
created: 2026-09-17
updated: 2026-09-17
clickup_id: null
parent: null
blocks: []
blocked_by: [0046]
---

# 0047 — Top-of-PR risk and contact intelligence panel

## Context
The pipeline already computed risk, contact surfaces and gate evidence, but the
workflow publisher posted only a generic link to the CI run. Humans and agents
could not see the earliest HITL checkpoint without opening artifacts.

## Problem
High-impact changes need early, bounded signals: risk triggers, blast radius,
surfaces of contact, sensitive areas, gate completeness and missing evidence.
The panel must remain advisory, exact-head bound and explicit about unknowns;
it cannot become a candidate-controlled admission bypass.

## What To Do
- [x] Add blast-radius and sensitive-surface metrics to PR intelligence.
- [x] Render exact base/head, required/passed/missing gates and HITL checkpoint.
- [x] Publish a bounded completed-run diagnostic artifact at the top of the PR.
- [x] Escape comment controls and suppress accidental mentions from artifact text.
- [x] Add regression tests for panel fields and backward-compatible rendering.
- [ ] Calibrate false positives/negatives against a labeled PR corpus.

## Affected Files
- `scripts/pr_intelligence.py`
- `.github/workflows/pr-summary.yml`
- `tests/test_pr_intelligence.py`

## Exit Conditions
- [x] High-risk/harness changes request HITL before integration.
- [x] Panel distinguishes missing/failed evidence from passed evidence.
- [x] Panel binds to the completed run head SHA and is updated idempotently.
- [x] Candidate artifact text is bounded and cannot inject a comment marker or mention.
- [x] Existing tests, scanners and workflow YAML remain green.
- [ ] Trusted metric calibration is complete.

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
The panel is diagnostic, not a trust boundary. It does not authenticate
candidate-produced risk artifacts, prove metric accuracy, or replace required
checks. Calibration needs labeled non-sensitive changes and observed outcomes;
no hours-saved or correctness score is inferred here.
