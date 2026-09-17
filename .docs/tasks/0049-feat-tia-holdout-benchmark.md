---
status: in_progress
priority: P1
type: feat
created: 2026-09-17
updated: 2026-09-17
clickup_id: null
parent: null
blocks: []
blocked_by: [0048]
---

# 0049 — Held-out seeded-fault benchmark for test-impact analysis

## Context
The selector and shadow runner already measure a development fixture corpus,
but a selector can overfit the fixtures used while it is being changed. A
separate held-out corpus is needed before any future dispatcher can consider
using impacted tests as an optimization.

## What To Do
- [x] Add a versioned held-out benchmark runner with corpus identity hashes.
- [x] Add seeded-fault metadata and three independent holdout cases.
- [x] Report mean and worst-case precision/recall, fault types and corpus size.
- [x] Require a minimum independent corpus and worst-case recall of 1.0 for
  `promotion_ready`.
- [x] Run the holdout benchmark in CI and publish its bounded artifact.
- [ ] Wire promotion into a production dispatcher after real repository data
  and an approved trust policy exist.

## Affected Files
- `scripts/impact_holdout.py`
- `tests/impact/holdout/*.json`
- `tests/test_impact_holdout.py`
- `.github/workflows/ci.yml`

## Exit Conditions
- [x] Training and held-out corpus identity is recorded.
- [x] A seeded-fault miss or insufficient corpus cannot report promotion-ready.
- [x] Full-suite execution remains authoritative.
- [x] Existing impact benchmark and promotion contracts remain green.
- [ ] Production test dispatch consumes this evidence.

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
This is benchmark evidence, not proof of universal test-impact correctness.
The holdout is synthetic and deliberately small; production promotion still
requires a larger repository-derived corpus, authenticated evidence, and an
explicit rollback policy. No test gate is weakened by this packet.
