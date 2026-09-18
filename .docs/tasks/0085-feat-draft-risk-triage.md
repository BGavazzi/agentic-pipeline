---
status: in_progress
priority: P1
type: feat
created: 2026-09-18
updated: 2026-09-18
clickup_id: null
parent: 0080
blocks: []
blocked_by: []
---

# 0085 — [Feat]: Risk-first triage for draft PRs

## Context
The multi-base local integration queue correctly held draft PRs before any
fetch, merge or execution. That protected the worker boundary, but it made all
drafts equally opaque (`risk=unknown`), preventing the human bundle from
prioritizing a dangerous draft over a routine one.

## Problem
Readiness and execution are separate decisions. A same-repository draft head
can be inspected read-only for changed-file, blast-radius and contact-surface
metrics without running its code. Fork drafts and unresolved identities must
remain fully fail-closed.

## What To Do
- [x] Classify same-repository draft heads read-only when identity resolves.
- [x] Preserve draft holds and never merge or execute draft candidates.
- [x] Keep fork, base-mismatch and unresolved-head holds fail-closed.
- [x] Add metrics coverage for risk, changed files and draft provenance.
- [ ] Wire the resulting bundle into a protected staging-review handoff.

## Affected Files
- `scripts/local_integration_loop.py`
- `tests/test_local_integration_loop.py`
- `README.md`
- `.docs/function-catalog.md`
- `CHANGELOG.md`
- `.agents/continuity-codex.md`

## Exit Conditions
- [x] Same-repository drafts carry risk/contact evidence when their immutable
  head is available.
- [x] Drafts remain `held_for_human` and cannot reach the execution worker.
- [x] Fork and unresolved-head cases retain fail-closed behavior.
- [x] Focused tests pass.
- [ ] Full suite and repository gates pass.
- [ ] PR receives independent review and approval.

## Required Documentation (Closure Law)
- [x] `CHANGELOG.md` updated
- [x] `.docs/function-catalog.md` updated
- [ ] `<sdd_kit_path>` updated (no new decision record)
- [x] `README.md` updated
- [x] `.agents/continuity-codex.md` updated
- [x] Tests passing
- [x] `<route_map>` unchanged
- [ ] PR approved

## Honest Backlog
Risk triage is evidence only. Draft readiness, protected policy, integration
execution and human review remain independent conditions for staging.
