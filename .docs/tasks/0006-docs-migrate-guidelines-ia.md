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

**Second pass (2026-09-04, same day):** after seeing what got left out, the
user overrode the original scope call — "We should make sure all the bits
from there are here without fis or company structure." The first pass's
exclusion list (`.docs/analysis/`, `.docs/strategy/`, `.template/`, the
5 extra `.docs/conventions/*.md` files, etc.) was re-reviewed file-by-file:
genuinely portable methodology got migrated with FIS/company specifics
scrubbed out; genuinely FIS-specific operational history (real names, real
incidents, real GCP project IDs, real client-project codenames) stayed
excluded, because scrubbing those wouldn't leave anything left worth having.

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
- [x] **Second pass**: migrate the remaining portable content, scrubbed of
      FIS/company specifics — `.docs/strategy/double-diamond-prototype-pipeline.md`
      (the actual Triple-Diamond definition this repo's README says doesn't
      exist anywhere), `.docs/analysis/factory-testing-gaps-2026-06-09.md`,
      `.docs/analysis/pattern-rationale.md` (from `02-padroes-identificados.md`),
      `.docs/analysis/meta-constitution.md` (from `05-A`),
      `.docs/analysis/agentic-pipeline-target-architecture.md` (from `07-playbook`),
      `.docs/conventions/clickup-task-schema.md` (from `06-template-tarefa-clickup.md`),
      `.docs/conventions/scope-intake.md`, `.docs/conventions/clickup-comment-style.md`,
      `.docs/conventions/frontend-screen-flow.md`, and the full `.template/`
      scaffold kit (rewired from guidelines_IA's `git subtree`/`dist/core`
      flow to reference `core_sync.py` instead)
- [ ] Translate to English — explicitly deferred for the Portuguese-authored
      `.docs/analysis/`/`.docs/strategy/` docs and the 6 files from the first
      pass; the second pass's `.docs/conventions/*.md` additions ARE in
      English (to match the other 6 files already in that directory) — see
      Honest Backlog

## Affected Files
- `MODEL-SELECTION.guidelines.md`, `AGENTS.balanced.md`, `AGENTS.minimal.md`,
  `AGENTS.opus48.balanced.md`, `AGENTS.assessment.md`,
  `AGENTS.usage-guidelines.md` (new, migrated, first pass)
- `.docs/strategy/double-diamond-prototype-pipeline.md`,
  `.docs/analysis/factory-testing-gaps-2026-06-09.md`,
  `.docs/analysis/pattern-rationale.md`, `.docs/analysis/meta-constitution.md`,
  `.docs/analysis/agentic-pipeline-target-architecture.md`,
  `.docs/conventions/clickup-task-schema.md`,
  `.docs/conventions/scope-intake.md`,
  `.docs/conventions/clickup-comment-style.md`,
  `.docs/conventions/frontend-screen-flow.md`,
  `.template/README.md`, `.template/AGENTS.md`, `.template/CHANGELOG.md`,
  `.template/.docs/PRD.md`, `.template/.gitignore` (new, migrated, second pass)
- `README.md` (new sections)

## Exit Conditions
- [x] All 6 first-pass files present in `agentic-pipeline`
- [x] `MODEL-SELECTION.guidelines.md` and `AGENTS.usage-guidelines.md` name
      current models, not a superseded generation
- [x] `README.md` links all 6 with enough context to know which to open
- [x] Every second-pass file reviewed line-by-line for FIS names, company
      structure, real people, or org-specific IDs before migrating —
      documented per-file in the migration work itself, not just asserted

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
- **Still not migrated, even after the second pass** (checked, not skipped):
  `.docs/analysis/INDEX.md` (contains a real credential-incident note),
  `00-RELATORIO-EXECUTIVO.md`, `01-mapa-cross-repo.md`,
  `03-gaps-e-redundancias.md` (same credential incident), `08-roadmap-adocao.md`,
  `09-ciclo-1-retrospectiva-e-gaps.md` (real names + PR#/ticket IDs),
  `10-status-vs-plano-original.md` (real names + org roles),
  `.docs/admin/pending-actions.md` (real repo/person-specific admin list),
  all 28 files under `.docs/tasks/` (FIS's own execution history — GCE
  provisioning, a specific ClickUp bot's build-out — superseded in substance
  by what's actually built now: `validate_task.py`/`validate_closure.py`/
  `blast_radius.py`/`scan_gate.py` all exist and are better-specified than
  these speculative task files were), `.docs/conventions/daemon-shell.md`
  (a GCP deployment runbook naming real GCP projects and real bot repos —
  infra-specific, not doctrine), `.docs/conventions/validation-pipeline.md`
  (the *pattern* — ClickUp as state machine, routed validation, one-way
  digest — is reusable, but real names/IDs are threaded through nearly every
  section; rewriting clean was judged too large for this pass, flagged as a
  candidate for a from-scratch doc later rather than a scrub), `.docs/skills/*.md`
  (stale vs. this repo's real `.claude/skills/*/SKILL.md`, confirmed via diff
  in the first pass — migrating would be a regression), `infra/observability/*`
  (real GCP project IDs, a real production incident with real service names),
  `.template/.docs/tasks/000-template.md` (pure duplicate of this repo's own
  `.docs/tasks/000-template.md`, just in Portuguese with different field
  names — would create two competing task formats), `publish-core.sh` (a
  `git subtree split` mechanism for `guidelines_IA`'s old source→consumer
  topology, superseded by `core_sync.py` which fits this repo's actual
  topology — this repo directly IS the source).
- Translation to English: the Portuguese-authored docs (both passes' `.docs/analysis/`
  and `.docs/strategy/` content, plus the first pass's `MODEL-SELECTION.guidelines.md`
  and `AGENTS.*.md` variants) are left as-is. Rewriting risks losing nuance
  the original author intended; better done on-demand by whoever first needs
  a non-Portuguese-speaking consumer to read one of these. The second pass's
  `.docs/conventions/*.md` additions (`clickup-task-schema.md`,
  `scope-intake.md`, `clickup-comment-style.md`, `frontend-screen-flow.md`)
  and the `.template/` files ARE in English/kept-as-authored — conventions
  matched the existing English convention in that directory; `.template/`'s
  `AGENTS.md`/`README.md`/`CHANGELOG.md`/`PRD.md` stayed Portuguese to match
  the still-Portuguese `AGENTS.balanced.md` they instantiate from.
