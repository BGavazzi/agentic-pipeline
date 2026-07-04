---
status: todo
priority: P2
type: chore
created: YYYY-MM-DD
updated: YYYY-MM-DD
clickup_id: null
parent: null
blocks: []
blocked_by: []
---

# NNNN — [Type]: [Descriptive Title]

## Context
Why this task exists. What problem it solves. References to related tasks,
SDD_KIT decisions, or the discussion that produced it.

## Problem
Precise technical description of what is wrong or missing.

## What To Do
- [ ] Subtask 1 (actionable, verifiable)
- [ ] Subtask 2
- [ ] Subtask N

## Affected Files
- `path/to/file` (main)
- `path/to/test` (tests)

## Exit Conditions
- [ ] Behavior X implemented and functional
- [ ] Test suite passes 100%

## Required Documentation (Closure Law)
- [ ] `CHANGELOG.md` updated
- [ ] `<function_catalog>` updated (signature change)
- [ ] `<sdd_kit_path>` updated (new Dxx decision)
- [ ] `README.md` updated (user-visible change)
- [ ] `.agents/continuity-<agent>.md` updated
- [ ] Tests passing
- [ ] `<route_map>` updated (route/handler/model changed)
- [ ] PR approved (task only closes once review is APPROVED — see git-pr-workflow.md §4)

## Honest Backlog
(Optional — anything left open, with a one-line reason. Referenced items here
are tolerated as unresolved by validate_task.py F12 / validate_closure.py.)
