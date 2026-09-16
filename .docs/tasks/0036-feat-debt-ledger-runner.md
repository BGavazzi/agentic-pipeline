---
status: in_progress
priority: P2
type: feat
created: 2026-09-16
updated: 2026-09-16
clickup_id: null
parent: 0035
blocks: []
blocked_by: []
---

# 0036 — feat: implement the read-only debt-ledger runner

## Context
The migrated `debt-ledger` skill captured a useful governance rule — a
shortcut without a revisit task is the most likely to become permanent — but
its referenced runner did not exist in the canonical pipeline.

## Problem
Agents and humans need a deterministic, repeatable ledger rather than prose or
grep output. The scanner must be read-only, skip generated/dependency outputs,
separate tracked from no-trigger debt, and expose machine-readable metrics.

## What To Do
- [x] Implement `scripts/debt_ledger.py` with code-only default scanning and
      opt-in documentation scanning.
- [x] Emit stable JSON and Markdown ledgers with schema/version/totals/entries.
- [x] Skip generated, dependency, archive, and VCS directories.
- [x] Add tests for classification, ordering, docs opt-in, and ignore policy.
- [x] Update the skill, README, and changelog.

## Affected Files
- `scripts/debt_ledger.py`
- `tests/test_debt_ledger.py`
- `.claude/skills/debt-ledger/SKILL.md`
- `README.md`
- `CHANGELOG.md`

## Exit Conditions
- [x] The runner never mutates source files or task state.
- [x] No-trigger entries are listed before tracked entries.
- [x] JSON contains versioned totals, marker counts, entries, and scan errors.
- [x] Tests and validators pass.

## Required Documentation (Closure Law)
- [x] `CHANGELOG.md` updated
- [N/A] `function-catalog.md` — no function catalog exists
- [N/A] `SDD_KIT.md` — no new product decision
- [x] `README.md` updated
- [N/A] `.agents/continuity-<agent>.md` — no continuity file in this checkout
- [x] Tests passing
- [N/A] `ROUTE_BEHAVIOR_MAP.md` — no route/handler/model change
- [ ] PR approved

## Honest Backlog
- The runner reports debt but does not automatically create tasks; task creation
  remains an explicit builder/dispatcher decision.
