---
status: todo
priority: P1
type: feat
created: 2026-09-18
updated: 2026-09-18
clickup_id: null
parent: null
blocks: []
blocked_by: []
---

# 0079 — [Feat]: Harden integration queue identity and readiness handling

## Context
The first real queue pass over the open PR stack used the local integration
producer and found that the operational wrapper had to rewrite discovered head
refs to `origin/<branch>` manually. The repository can have stale same-named
local branches, so discovery must bind directly to the remote-tracking ref and
refresh once when the immutable GitHub head SHA has moved. Draft PRs also need a
readiness hold before any ref resolution or candidate execution.

## Problem
`local_integration_loop.py` previously discovered a plain head branch name and
could false-hold a current PR when a stale local branch shadowed it. It also did
not carry `isDraft`, so a draft could reach risk classification and execution
instead of remaining explicitly not ready for staging.

## What To Do
- [x] Prefer `origin/<headRefName>` during read-only PR discovery.
- [x] Refresh a stale remote-tracking head once through `refs/pull/N/head`.
- [x] Represent draft status in manifests and GitHub discovery.
- [x] Hold drafts before ref resolution with an explicit readiness reason.
- [x] Add focused tests for draft holds and remote-ref discovery.
- [ ] Integrate the queue producer with a reusable multi-base orchestration CLI.

## Affected Files
- `scripts/local_integration_loop.py` (candidate identity and readiness)
- `tests/test_local_integration_loop.py` (adversarial contract tests)
- `README.md` (behavior and usage)
- `.docs/function-catalog.md` (contract inventory)
- `.agents/continuity-codex.md` (continuity record)

## Exit Conditions
- [x] Draft candidates never fetch, merge, or execute locally.
- [x] Discovered same-repository candidates bind to the immutable GitHub head.
- [x] A moved head is refreshed once before fail-closed rejection.
- [x] Focused integration-loop tests pass.
- [ ] Full suite and repository gates pass.
- [ ] PR receives independent review and approval.

## Required Documentation (Closure Law)
- [x] `CHANGELOG.md` updated
- [x] `.docs/function-catalog.md` updated
- [ ] `<sdd_kit_path>` updated (no new decision record)
- [x] `README.md` updated
- [x] `.agents/continuity-codex.md` updated
- [ ] Full tests passing
- [x] `<route_map>` unchanged (no route/handler/model changed)
- [ ] PR approved (task only closes once review is APPROVED — see git-pr-workflow.md §4)

## Honest Backlog
The multi-base queue orchestration remains a follow-up. This patch hardens the
single-base producer and the queue wrapper can continue to fail closed until
that orchestration is implemented and tested.
