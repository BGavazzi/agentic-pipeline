---
status: todo
priority: P1
type: feat
created: 2026-09-18
updated: 2026-09-18
clickup_id: null
parent: 0079
blocks: []
blocked_by: []
---

# 0080 — [Feat]: Productize multi-base integration queue processing

## Context
The integration-to-staging dogfood run had to be driven by an operator-side
wrapper because the open PR queue is a dependency stack with many declared base
branches. A flat run against `master` would hold every dependent PR as a base
mismatch and would not test the actual stack topology.

## Problem
The reusable producer handled one base at a time, but there was no versioned
queue adapter that discovered the queue once, grouped candidates by declared
base, ran each group with the same local-only policy, and aggregated metrics for
the staging handoff.

## What To Do
- [x] Discover the open queue once with immutable head/base metadata.
- [x] Group candidates deterministically by declared base ref.
- [x] Delegate each group to the disposable local integration producer.
- [x] Isolate unresolved base refs as fail-closed human holds.
- [x] Emit aggregate JSON/Markdown metrics and staging-handoff status.
- [x] Add multi-base, discovery, and aggregation tests.

## Affected Files
- `scripts/integration_queue.py` (new queue adapter)
- `tests/test_integration_queue.py` (contract tests)
- `README.md` (usage)
- `.docs/function-catalog.md` (contract inventory)
- `.agents/continuity-codex.md` (continuity record)

## Exit Conditions
- [x] A stacked queue is processed without flattening dependent bases.
- [x] The adapter never creates, approves, merges, pushes, or deploys remotely.
- [x] No routine survivor is presented as staging-authorized; staging gate remains separate.
- [x] Tests and repository validators pass.
- [ ] PR receives independent review and approval.

## Required Documentation (Closure Law)
- [x] `CHANGELOG.md` updated
- [x] `.docs/function-catalog.md` updated
- [ ] `<sdd_kit_path>` updated (no new decision record)
- [x] `README.md` updated
- [x] `.agents/continuity-codex.md` updated
- [x] Tests passing
- [x] `<route_map>` unchanged
- [ ] PR approved (task only closes once review is APPROVED — see git-pr-workflow.md §4)

## Honest Backlog
Worker-pool scheduling and external staging PR creation remain separate
adapters. This command only produces local evidence for the existing admission
and staging gates.
