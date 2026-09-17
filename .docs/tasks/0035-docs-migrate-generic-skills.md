---
status: in_progress
priority: P1
type: docs
created: 2026-09-16
updated: 2026-09-16
clickup_id: null
parent: 0006
blocks: []
blocked_by: []
---

# 0035 — docs: migrate reusable pipeline skills from guidelines_IA

## Context
The portfolio audit found four skills present in `guidelines_IA` but absent from
the canonical agentic pipeline. Three contain portable agentic engineering
methodology; the fourth is an application/company-specific ClickUp integration
and must remain excluded under the no-FIS/company-structure rule.

## Problem
Leaving portable skills in the superseded repository creates drift and makes
the completeness benchmark understate the canonical harness. Migration must
preserve the valuable method while removing real organization names, repo
identifiers, credentials, and operational structures.

## What To Do
- [x] Migrate a generic integration-pilot skill with reversible-branch,
      dependency-order, validation, quota, and auto-revert rules.
- [x] Migrate a generic frontend-refactor PR skill with reachability, clean
      build, per-location visual proof, and human visual-review rules.
- [x] Migrate the read-only debt-ledger skill and its no-trigger insight.
- [x] Keep the FIS-specific speaker-to-ClickUp skill excluded and document the
      exclusion rationale.
- [x] Update canonical README and changelog.

## Affected Files
- `.claude/skills/integration-pilot/SKILL.md`
- `.claude/skills/frontend-refactor-pr/SKILL.md`
- `.claude/skills/debt-ledger/SKILL.md`
- `README.md`
- `CHANGELOG.md`

## Exit Conditions
- [x] All three migrated skills contain no FIS/company-specific names,
      identifiers, or credential paths.
- [x] The integration skill preserves the reversible integration-only merge and
      automatic-revert safety boundary.
- [x] The frontend skill preserves per-location visual proof and human review
      for intentional changes.
- [x] The debt skill remains read-only and distinguishes no-trigger debt.
- [x] Task and closure validators pass.

## Required Documentation (Closure Law)
- [x] `CHANGELOG.md` updated
- [N/A] `function-catalog.md` — no function catalog exists
- [N/A] `SDD_KIT.md` — no new product decision
- [x] `README.md` updated
- [N/A] `.agents/continuity-<agent>.md` — no continuity file in this checkout
- [x] Tests passing / validators pass
- [N/A] `ROUTE_BEHAVIOR_MAP.md` — no route/handler/model change
- [ ] PR approved

## Honest Backlog
- `bluemagic-speakers-to-clickup` remains excluded because its entity names,
  status enum, and ClickUp behavior are inseparable from a specific product
  and company workflow; extracting a generic event-to-task pattern is a
  separate design task, not a safe copy.
- The debt-ledger skill still describes the output contract; its standalone
  runner is not yet implemented in the canonical repo.
