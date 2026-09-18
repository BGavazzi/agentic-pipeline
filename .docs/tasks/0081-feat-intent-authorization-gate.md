---
status: todo
priority: P0
type: feat
created: 2026-09-18
updated: 2026-09-18
clickup_id: null
parent: null
blocks: []
blocked_by: []
---

# 0081 — [Feat]: Add deterministic intent and authorization evidence

## Context
AI-generated code can be technically correct while violating the intended
data, permission, or workflow boundary. The existing harness validates the
resulting tree and execution evidence, but it did not have a machine-readable
contract for what the agent was authorized to change or what sensitive failure
cases had to be rejected.

## Problem
Without an intent contract, a passing implementation can silently expand its
path scope, data classes, or external effects. Human review then discovers
intent drift late, after the candidate has already consumed integration and
scanner capacity.

## What To Do
- [x] Define a versioned JSON intent contract.
- [x] Compare changed files against allowed and forbidden path globs.
- [x] Check declared/observed effects and allowed data classes.
- [x] Require passing negative tests for sensitive data/effect declarations.
- [x] Bind the evidence report to exact base/head SHAs.
- [x] Add adversarial unit coverage and a CLI.
- [x] Add the capability to the deterministic SOTA audit.
- [ ] Carry the intent receipt into CI admission as a mandatory obligation for
  agent-generated changes.

## Affected Files
- `scripts/intent_gate.py` (new deterministic gate)
- `tests/test_intent_gate.py` (contract and negative tests)
- `README.md` (operator contract)
- `.docs/function-catalog.md` (function inventory)
- `.docs/analysis/agentic-sdlc-testing-sota-2026-09.md` (SOTA delta)
- `.agents/continuity-codex.md` (continuity record)

## Exit Conditions
- [x] Scope drift, forbidden paths/effects, and unapproved data classes block.
- [x] Sensitive intent without passing negative evidence blocks.
- [x] Reports carry exact base/head identity and remain evidence-only.
- [x] Focused tests pass.
- [ ] Intent evidence is required by admission for agent-generated work.
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
The gate deliberately does not infer business authorization, inspect runtime
traffic, or authenticate candidate-authored claims. Protected producer identity
and admission wiring are the next task.
