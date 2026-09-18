---
status: in_progress
priority: P1
type: feat
created: 2026-09-18
updated: 2026-09-18
clickup_id: null
parent: 0065
blocks: []
blocked_by: []
---

# 0066 — Feature: bounded local integration loop and review bundles

## Context
Agentic development produces more candidate PRs than a human can inspect
serially. The harness needs an integration layer that eats its own output:
routine candidates should be tested together locally, while acute-risk work
should surface early with evidence for human review.

## Problem
The existing clean-room gate proves one exact tree at a time and the staging
path validates handoff evidence, but neither composes multiple candidate PRs
into a disposable local sequence. A model must not decide that a risky change
is routine, and a failed local merge or test must not leak into the next
candidate.

## What To Do
- [x] Accept deterministic candidate manifests and optionally discover open PRs.
- [x] Resolve immutable head identities, with an explicit read-only fetch path
      for missing same-repository PR refs.
- [x] Classify risk and contact surfaces; hold acute candidates before merge.
- [x] Merge routine candidates one at a time in a disposable worktree.
- [x] Execute the integration command through argv-only subprocesses with
      obvious credential variables removed.
- [x] Revert failed candidates and clean the worktree before the next candidate.
- [x] Emit versioned JSON and Markdown metrics/review bundles with an explicit
      no-remote-write policy.
- [x] Support bounded rediscovery rounds with local state keyed by immutable
      candidate head SHA; new pushes are considered again and unresolved holds
      remain visible until human disposition.
- [x] Hold cross-repository/fork candidates before fetching or executing their
      head code; route them to the untrusted hosted lane for explicit review.
- [ ] Add a protected scheduler/worker consumer and notification channel as a
      separate deployment task; this local producer must remain bounded.

## Affected Files
- `scripts/local_integration_loop.py`
- `tests/test_local_integration_loop.py`
- `scripts/blast_radius.py`
- `scripts/core_sync.py`
- `scripts/sota_audit.py`
- `README.md`, `CHANGELOG.md`, `.docs/function-catalog.md`

## Exit Conditions
- [x] Routine passing candidates are included in a local disposable bundle.
- [x] Acute, conflicting, unresolved, and failing candidates are held.
- [x] No remote merge, push, approval, deployment, shell command, or secret
      forwarding is possible through the integration path.
- [x] Focused tests and repository gates pass.
- [ ] A host-level loop scheduler and protected human notification are activated.
- [ ] PR approved.

## Required Documentation (Closure Law)
- [x] `CHANGELOG.md` updated
- [x] `.docs/function-catalog.md` updated
- [N/A] `<sdd_kit_path>`: no new architectural decision record
- [x] `README.md` updated
- [x] `.agents/continuity-codex.md` updated
- [x] Tests passing
- [N/A] `<route_map>`: no route changed
- [ ] PR approved

## Honest Backlog
This task provides a local bounded producer and stateful round primitive. It
does not provision homelab workers, create an unbounded daemon, authenticate
GitHub policy, send external notifications, merge/push remotely, approve a PR,
or deploy an application.
