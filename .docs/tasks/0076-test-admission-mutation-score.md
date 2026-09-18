---
status: in_progress
priority: P1
type: test
created: 2026-09-18
updated: 2026-09-18
clickup_id: null
parent: 0067-docs-agentic-sdlc-testing-sota
blocks: []
blocked_by: []
---

# 0076 — Test: benchmark admission mutation score

## Context
Fixture self-tests prove named scenarios, but mutation testing measures whether
small adversarial changes to risk, identity, obligations, and gate statuses are
actually rejected.

## Problem
The harness had no explicit mutation score or CI signal for fail-closed
admission soundness.

## What To Do
- [x] Add deterministic mutations to the admitted harness fixture.
- [x] Report killed/survived mutations and mutation score.
- [x] Wire the benchmark into the unit job without changing admission policy.
- [x] Add unit coverage and high-risk inventory entries.
- [ ] Expand the mutation corpus across all receipt adapters.

## Affected Files
- `scripts/admission_mutation_benchmark.py`
- `tests/test_admission_mutation_benchmark.py`
- `.github/workflows/ci.yml`

## Exit Conditions
- [x] All current mutations are killed.
- [x] Mutation score is versioned and emitted as CI evidence.
- [x] A mutation benchmark failure fails the unit job.
- [ ] A broader adapter corpus is maintained.

## Required Documentation (Closure Law)
- [x] `CHANGELOG.md` updated
- [x] `function-catalog` updated
- [N/A] `SDD_KIT` — no new architecture decision required
- [x] `README.md` updated (CI evidence is the user-visible change)
- [x] `.agents/continuity-codex.md` updated
- [x] Tests passing
- [ ] `ROUTE_BEHAVIOR_MAP` — no HTTP routes
- [ ] PR approved (task remains in progress until review)

## Honest Backlog
The initial corpus targets admission mutations only; receipt adapters and
worker/visual contracts need their own mutation families later.
