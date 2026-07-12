---
status: in_progress
priority: P0
type: fix
created: 2026-07-04
updated: 2026-07-11
clickup_id: null
parent: null
blocks: []
blocked_by: []
---

# 0003 — Fix: validators still check Portuguese section titles after English translation

## Context
Found while documenting tasks 0001/0002 in this repo (2026-07-04). Commit
`da457a4` ("translate all content to English") updated GDFRSBT.md, AGENTS.md,
and every SKILL.md to use English section headers (`## Context`,
`## What To Do`, `## Exit Conditions`, `§Honest Backlog`) and English closure
terminology (`Task Closure Law`), but did not update the two Python
validators, which still hardcoded the old Portuguese titles (`Contexto`,
`O Que Fazer`, `Condições de Saída`, `Pendências Honestas`, `Lei de
Fechamento`).

## Problem
Any task written per the repo's own current documentation would fail
`validate_task.py` (F7/F8/F9: "section missing") and `validate_closure.py`
("no closure section found") — the deterministic gates the whole dispatcher
pipeline depends on were silently broken for any new user following the
README/GDFRSBT.md as written. Separately, `.gitignore`'s
`.docs/tasks/[0-9]*.md` rule also matched `000-template.md` (leading digit
`0`), so the template file the README instructs users to `cp` could never
actually be committed, and this repo could never track its own
pipeline-improvement backlog.

## What To Do
- [x] `scripts/validate_task.py`: F7-F9 section lookups → `Context` /
  `What To Do` / `Exit Conditions`; F12 fallback → `Honest Backlog`;
  `arquivos_afetados` frontmatter warning key → `files_affected`
- [x] `scripts/validate_closure.py`: `CLOSURE_SECTION_TITLES` →
  `["Closure Law §3", "Closure Law", "Required Documentation (Closure Law)",
  "Required Documentation"]`; `Pendências Honestas`/`Pendências` fallback →
  `Honest Backlog`/`Backlog`; docstring and inline messages translated;
  `\btestes?\b` alias corrected to `\btests?\b` (the old regex only matched
  the Portuguese word, not English "test"/"tests")
- [x] `.gitignore`: removed the `.docs/tasks/[0-9]*.md` blanket ignore so
  this repo can track its own dogfood backlog and the template is no longer
  shadowed
- [x] `.docs/tasks/000-template.md` created (was referenced by README, never
  actually existed in the repo)

## Affected Files
- `scripts/validate_task.py`
- `scripts/validate_closure.py`
- `.gitignore`
- `.docs/tasks/000-template.md` (new)

## Exit Conditions
- [x] `python scripts/validate_task.py .docs/tasks/000-template.md` no longer
  reports F7/F8/F9 (template uses English headers by construction)
- [x] Manual spot-check (2026-07-11): ran both validators against
  `0001-*.md`, `0002-*.md`, `0003-*.md` (this file), `0004-*.md`, both
  file-by-file and in CI's directory-mode invocation
  (`python scripts/validate_task.py .docs/tasks` /
  `python scripts/validate_closure.py .docs/tasks`) — all PASS,
  `validate_closure.py` reports 7/7 items resolved on every task
- [ ] `pytest`/equivalent — [N/A] no automated test suite for these scripts
  yet; covered by manual invocation above (tracked as debt, not blocking)

## Required Documentation (Closure Law)
- [x] `CHANGELOG.md` updated (created — repo had none)
- [ ] `<function_catalog>` — [N/A] core/tooling repo, no function-catalog.md
- [ ] `<sdd_kit_path>` — [N/A] no SDD_KIT.md in this repo yet
- [ ] `README.md` — [N/A] no user-facing behavior change (bug fix restores
  documented behavior, doesn't change it)
- [ ] `.agents/continuity-<agent>.md` — [N/A] no continuity ledger in use yet
- [ ] Tests passing — see Exit Conditions above (manual validation, no
  automated suite exists for these scripts yet)
- [ ] `<route_map>` — [N/A] no HTTP routes in this repo
- [ ] PR approved — pending human review; task stays `in_progress` until
  then per git-pr-workflow.md §4 (opened ≠ accepted)

## Honest Backlog
- No automated test coverage for `validate_task.py`/`validate_closure.py`
  themselves (only manual invocation against real task files in this PR).
  Worth a `meta-test` fixture in a follow-up task rather than blocking this fix.
