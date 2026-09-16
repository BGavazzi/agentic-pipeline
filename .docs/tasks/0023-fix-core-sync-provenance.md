---
status: in_progress
priority: P1
type: fix
created: 2026-09-16
updated: 2026-09-16
clickup_id: null
parent: null
blocks: []
blocked_by: []
---

# 0023 — fix: make core sync provenance canonical and self-describing

## Context
Task 0022 migrated `bluemagic-front` from the legacy `guidelines_IA` subtree
projection to the canonical agentic-pipeline gates. That migration exposed a
second-order defect: the generated `VENDORED.md` still named the retired source
of truth, so a future agent could edit the wrong repository or believe that the
consumer only received the original eight skills.

## Problem
`core_sync.py` copied the right files but did not generate provenance metadata.
Consumers with an existing legacy projection therefore kept stale instructions
even after a successful canonical sync. Provenance must be deterministic,
versioned through the same manifest, and drift-protected like the other synced
files.

## What To Do
- [x] Generate `.claude/skills/VENDORED.md` from the canonical source tree.
- [x] Include the complete skill and gate inventory in that generated file.
- [x] Include the generated file in manifest hashing and drift detection.
- [x] Add unit tests for canonical provenance, dry-run, drift, and `--force`.
- [x] Update the consumer-facing Quick Start documentation.

## Affected Files
- `scripts/core_sync.py`
- `tests/test_core_sync.py`
- `README.md`

## Exit Conditions
- [x] A clean sync points to `BGavazzi/agentic-pipeline` and never
  `guidelines_IA`.
- [x] The generated inventory contains all current skills and whitelisted gates.
- [x] Provenance drift returns the same non-zero sync status as other vendored
  files, while `--force` repairs it.
- [x] Existing target `AGENTS.md` remains untouched.
- [x] Tests pass.

## Required Documentation (Closure Law)
- [x] `CHANGELOG.md` updated
- [N/A] `function-catalog.md` — no public application function catalog exists
- [N/A] `SDD_KIT.md` — no new product decision
- [x] `README.md` updated
- [N/A] `.agents/continuity-<agent>.md` — this repository has no continuity file
- [x] Tests passing
- [N/A] `ROUTE_BEHAVIOR_MAP.md` — no route/handler/model change
- [ ] PR approved

## Honest Backlog
- Existing consumers may still carry a legacy `.agentic-core/README.md`; the
  generated canonical `VENDORED.md` is the authoritative migration notice, and
  consumer-specific legacy docs should be retired in their own migration PR.
