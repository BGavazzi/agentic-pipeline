---
status: in_progress
priority: P1
type: docs
created: 2026-09-04
updated: 2026-09-04
clickup_id: null
parent: null
blocks: []
blocked_by: []
---

# 0006 — docs: finish the `guidelines_IA` → `agentic-pipeline` migration

## Context
`guidelines_IA` is FIS's original repo for this doctrine; `agentic-pipeline`
is its generic, portfolio-wide successor. The portfolio completeness
benchmark (`.docs/analysis/completeness-benchmark-2026-09.md`, item 5 of its
findings) found `guidelines_IA` scoring 15/24 while declaring itself
superseded — a tombstone with content that never actually migrated, still
load-bearing for anyone who goes looking for the model-selection policy or
the `AGENTS.md` size variants. Item 4 of the user-ordered remediation list
from that benchmark.

## Problem
Six files existed only in `guidelines_IA` and nowhere in `agentic-pipeline`:
`MODEL-SELECTION.guidelines.md`, `AGENTS.balanced.md`, `AGENTS.minimal.md`,
`AGENTS.opus48.balanced.md`, `AGENTS.assessment.md`,
`AGENTS.usage-guidelines.md`. The benchmark called these out specifically as
"the two things another repo most needs when adopting the doctrine"
(model choice + which `AGENTS.md` size to use).

## What To Do
- [x] Copy the 6 files into `agentic-pipeline` root, matching `guidelines_IA`'s
      own flat layout
- [x] Update stale model references (`Opus 4.8`/`claude-opus-4-8`,
      `Sonnet 4.6`/`claude-sonnet-4-6`) to current model names/IDs in the two
      *live-reference* docs (`MODEL-SELECTION.guidelines.md`,
      `AGENTS.usage-guidelines.md`) — these actively tell a reader which
      model to pick today, so stale names would actively mislead
- [x] Leave `AGENTS.opus48.balanced.md` and `AGENTS.assessment.md` model
      references untouched — both are explicitly versioned/historical
      artifacts (same convention as `.archive/agents-variants-pre-opus48/`
      in the source repo); added a provenance note to each instead of
      rewriting history
- [x] Link all 6 from `README.md` in a new section, with a one-line note on
      why `core_sync.py` doesn't auto-vendor them (team/repo choices made
      once, not per-consumer core content)
- [ ] Translate to English — explicitly deferred, see Honest Backlog

## Affected Files
- `MODEL-SELECTION.guidelines.md`, `AGENTS.balanced.md`, `AGENTS.minimal.md`,
  `AGENTS.opus48.balanced.md`, `AGENTS.assessment.md`,
  `AGENTS.usage-guidelines.md` (new, migrated)
- `README.md` (new section)

## Exit Conditions
- [x] All 6 flagged files present in `agentic-pipeline`
- [x] `MODEL-SELECTION.guidelines.md` and `AGENTS.usage-guidelines.md` name
      current models, not a superseded generation
- [x] `README.md` links all 6 with enough context to know which to open

## Required Documentation (Closure Law)
- [x] `CHANGELOG.md` updated
- [N/A] `<function_catalog>` — doesn't exist yet in this repo; nothing to update
- [N/A] `<sdd_kit_path>` — no SDD_KIT.md in this repo
- [x] `README.md` updated
- [N/A] `.agents/continuity-<agent>.md` — not in use this session
- [N/A] Tests — pure docs migration, no code changed; nothing to test
- [N/A] `<route_map>` — no web routes in this repo
- [ ] PR approved — stays `in_progress` until PR review lands

## Honest Backlog
- **Not migrated, and deliberately so** (scope call, not an oversight):
  `.docs/analysis/`, `.docs/strategy/`, `.docs/admin/`, `.docs/tasks/`
  (the 23-task roadmap) — all FIS-project-specific operational history
  (cross-repo analysis reports, GCE provisioning, ClickUp bot tasks), not
  generic doctrine. Migrating them into the portfolio-wide core repo would
  make it a second FIS project archive, not a lean canonical core.
  `.docs/skills/*.md` — checked via diff against this repo's actual
  `.claude/skills/*/SKILL.md`: the `guidelines_IA` copy is a **stale**
  markdown mirror missing 8 skills this repo already has implemented
  (`codebase-grounding`, `debt-ledger`, `figma-frontend-context`,
  `frontend-refactor-pr`, `implement-figma-task`, `meta-test`, `ultrareview`,
  `visual-tester`) — migrating it would be a regression, not a gap-fill.
  `infra/` — FIS-specific GCP cost-observability Terraform, not portfolio-wide.
  `.template/` — an older, differently-scoped "new repo scaffold" kit
  (its own `AGENTS.md` variant, diverged from this repo's current template)
  that would introduce a second, conflicting notion of "the template"
  alongside `core_sync.py`'s `AGENTS_MD_TEMPLATE` (built in task 0005) —
  worth revisiting as its own task if a "scaffold a brand-new repo from
  scratch" flow is ever wanted, but not folded in here.
  `publish-core.sh` — a `git subtree split`-based publish mechanism for
  `guidelines_IA`'s old source→consumer topology; superseded by
  `core_sync.py` (task 0005), which fits `agentic-pipeline`'s actual
  topology (this repo directly IS the source, no `dist/core` split needed).
- Translation to English: left as-is in Portuguese. Rewriting ~750 lines
  risks losing nuance the original author intended; better done on-demand
  by whoever first needs a non-Portuguese-speaking consumer to read one of
  these, with that specific need to check the translation against.
