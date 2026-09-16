---
status: todo
priority: P1
type: feat
created: 2026-09-16
updated: 2026-09-16
clickup_id: null
parent: 0031
blocks: []
blocked_by: []
---

# 0039 — Feature: safe survivor-to-staging dispatcher

## Context
The pipeline already emits `staging_gate.py` eligibility and has a tested
`staging_pr.py` adapter. The missing last-mile boundary was a single command
that verifies the current refs, attaches the quality evidence, and remains
dry-run unless an explicitly trusted caller authorizes the PR write.

## Problem
An autonomous lane should be able to hand a surviving candidate to humans
without guessing whether the staging base moved or silently dropping the
evidence that made the candidate reviewable. Opening a PR is acceptable at the
human-review boundary; merge and deployment are not autonomous outcomes.

## What To Do
- [ ] Verify eligibility, current base SHA, and current candidate head SHA.
- [ ] Compose the staging body with the PR intelligence evidence.
- [ ] Default to dry-run; require `--create` for the external PR write.
- [ ] Preserve duplicate detection and human-review-required marker.
- [ ] Test stale-base and no-write behavior.

## Affected Files
- `scripts/staging_dispatch.py`
- `tests/test_staging_dispatch.py`
- `README.md`, `CHANGELOG.md`

## Exit Conditions
- [ ] A valid survivor produces a dry-run plan with evidence attached.
- [ ] A stale base or head is rejected before any GitHub query/write.
- [ ] No path merges, approves, deploys, or pushes autonomously.
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
The `--create` flag still needs a separately protected dispatcher identity and
repository branch policy in production. This task only makes the boundary
explicit and safe; it does not grant a candidate worker any GitHub write token.
