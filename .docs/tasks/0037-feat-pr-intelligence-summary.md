---
status: todo
priority: P1
type: feat
created: 2026-09-16
updated: 2026-09-16
clickup_id: null
parent: null
blocks: []
blocked_by: []
---

# 0037 — Feature: commit-bound PR intelligence and early HITL routing

## Context
Agents need a compact, deterministic way to expose impact before a human spends
time reviewing a patch. Existing risk, receipt, integration, visual and
test-impact artifacts contain the evidence, but they are distributed across job
logs and artifacts. This task adds a derived view for PRs without replacing the
fail-closed admission controller.

## Problem
Reviewers cannot quickly see the change's blast radius, contact surfaces,
evidence completeness, test-impact state, or why a human checkpoint is needed.
A single scalar quality score would be unsafe because strong evidence in one
dimension cannot compensate for a failed security or policy gate.

## What To Do
- [ ] Emit a schema-versioned JSON intelligence receipt bound to base/head SHAs.
- [ ] Emit Markdown with risk, diff, surfaces, gate and test-impact metrics.
- [ ] Derive deterministic HITL checkpoint reasons; never use them to override admission.
- [ ] Publish the summary to the GitHub job summary and update one idempotent PR comment.
- [ ] Add unit tests for surface classification, identity binding, metrics and wording.

## Affected Files
- `scripts/pr_intelligence.py`
- `tests/test_pr_intelligence.py`
- `.github/workflows/ci.yml`
- `README.md`, `CHANGELOG.md`

## Exit Conditions
- [ ] JSON and Markdown are commit-bound and fail closed on stale risk evidence.
- [ ] High-impact and non-pass evidence produces an explicit pre-staging HITL signal.
- [ ] Existing admission semantics are unchanged.
- [ ] Test suite and repository closure validators pass.

## Required Documentation (Closure Law)
- [ ] `CHANGELOG.md` updated
- [ ] `README.md` updated
- [ ] `function-catalog` unchanged (no public function catalog is maintained)
- [ ] `SDD_KIT` unchanged (no new decision record is needed)
- [ ] Tests passing
- [ ] `.agents/continuity-<agent>.md` unchanged (continuity handoff is not part of this feature)
- [ ] `ROUTE_BEHAVIOR_MAP` unchanged (no route or handler changed)
- [ ] PR opened for human review

## Honest Backlog
The comment publisher is best-effort on fork PRs because GitHub downgrades token
write permissions for untrusted contributors; the job summary and artifact remain
the authoritative display surfaces. A cryptographically signed controller-issued
receipt remains a later trust-boundary upgrade.
