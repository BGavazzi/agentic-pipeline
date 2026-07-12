---
status: in_progress
priority: P2
type: feat
created: 2026-07-11
updated: 2026-07-11
clickup_id: null
parent: null
blocks: []
blocked_by: []
---

# 0004 — Feat: generic ClickUp/Figma/WhatsApp adapter skills + README deepening

## Context
The README's "Skills not included" section listed nine platform-coupled
skills (`clickup-api`, `clickup-grounding`, `clickup-audit`, `figma-api`,
`figma-frontend-context`, `implement-figma-task`, `visual-tester`,
`whatsapp-clickup`, `zap-comms`) as excluded from this core repo because the
only existing versions of some of them (`clickup-api` in particular) were
written against a specific org's bot account, org-specific task schema, and
Portuguese-language conventions — not because the *capability* was actually
out of scope for a generic pipeline.

Separately, the README itself had drifted to a bare one-liner-per-skill list
and a BYO table with no explanation of the terms used throughout every
`SKILL.md` (Closure Law, blast radius, proof-of-execution artifact,
fake-green, Diamond/stage numbering) — someone reading it cold had no way to
connect the pieces.

**Retroactive note (2026-07-11):** this task file is being created *after*
the work already merged as PR #4, not before — the work itself predates this
repo's own convention of tracking every substantive change as a
`.docs/tasks/NNNN-*.md` file (established by task 0003, also 2026-07-04).
Filed now specifically so the CHANGELOG/Closure-Law gap doesn't get
perpetuated: a repo whose whole purpose is enforcing "always update the
docs when you close a task" shouldn't have an ungrounded exception for
changes to itself.

## Problem
1. Nine real, generic capabilities (ClickUp task CRUD, Figma frame → brief,
   CDP visual diffing, WhatsApp messaging) had no generic implementation in
   this repo — only a company-specific one existed elsewhere, and it wasn't
   vendored here.
2. The README explained *what* each skill does in one line but not *why* the
   pipeline is shaped the way it is, nor what its own recurring jargon means
   — a new reader had to reverse-engineer Closure Law/blast-radius/fake-green
   from individual `SKILL.md` files instead of getting them defined once.

## What To Do
- [x] Write 9 new `SKILL.md` files under `.claude/skills/`, each BYO-credential-gated
  (env var precondition check, no hardcoded org/workspace/bot persona),
  cross-linked (`[[skill]]`) with the existing skills that already
  referenced them (`builder`, `tester`, `notifier`, `grill-me`,
  `codebase-grounding`, `codebase-audit`)
- [x] Update `README.md`: remove "Skills not included", list the 9 under
  "What's here", add their credential requirements to the BYO table
- [x] Deepen `README.md` further: add a pipeline-flow diagram, a concepts
  glossary (Closure Law §3, Dxx decisions, blast radius, proof-of-execution
  artifact, fake-green, grounding-vs-audit, prototype-vs-production mode,
  loop mode, quota gate, BYO pattern), per-group skill tables, a gates
  section, and a conventions section
- [x] Flag two real doc/repo inconsistencies found while writing the above
  instead of silently ignoring them: `tester` references
  `.docs/conventions/repo-tiering.md`, which didn't exist (see task's
  Honest Backlog — now being closed by a follow-up in this same session);
  the old README pointed to `migration-timestamp-ms.md` when the actual
  file is `migration-timestamp.md` (fixed the README reference)
- [x] File this task retroactively + add a CHANGELOG entry (closing the gap
  described in §Context)

## Affected Files
- `.claude/skills/clickup-api/SKILL.md` (new)
- `.claude/skills/clickup-grounding/SKILL.md` (new)
- `.claude/skills/clickup-audit/SKILL.md` (new)
- `.claude/skills/figma-api/SKILL.md` (new)
- `.claude/skills/figma-frontend-context/SKILL.md` (new)
- `.claude/skills/implement-figma-task/SKILL.md` (new)
- `.claude/skills/visual-tester/SKILL.md` (new)
- `.claude/skills/zap-comms/SKILL.md` (new)
- `.claude/skills/whatsapp-clickup/SKILL.md` (new)
- `README.md`
- `CHANGELOG.md` (new — see task 0003, which already created it)

## Exit Conditions
- [x] All 9 `SKILL.md` files pass a manual grep for company/persona-specific
  strings (`FIS`, `iniciativa`, `CM_WA`) with zero matches
- [x] README's "What's here", BYO table, and new glossary/flow sections are
  internally consistent with the actual skill files (no skill mentioned that
  doesn't exist, no env var named that a skill doesn't actually check)
- [ ] PR #4 approved and merged (opened 2026-07-11, https://github.com/BGavazzi/agentic-pipeline/pull/4)

## Required Documentation (Closure Law)
- [x] `CHANGELOG.md` updated (this task's own entry)
- [ ] `<function_catalog>` — [N/A] core/tooling repo, no function-catalog.md
- [ ] `<sdd_kit_path>` — [N/A] no SDD_KIT.md in this repo yet
- [x] `README.md` updated (this task's primary deliverable)
- [x] `.agents/continuity-<agent>.md` updated (ledger initialized this same
  session — see task tracking the `.agents/` bootstrap)
- [ ] Tests passing — [N/A] no code/scripts changed, only `SKILL.md`
  markdown + `README.md`; nothing for `pytest tests/` to exercise
- [ ] `<route_map>` — [N/A] no HTTP routes in this repo
- [ ] PR approved — pending human review; task stays `in_progress` until
  then per `git-pr-workflow.md` §4

## Honest Backlog
- No automated coverage exists (or is planned) for "does this SKILL.md
  actually behave as documented" — that's exactly the gap `meta-test`
  describes but hasn't built fixtures for yet. A future `meta-test` fixture
  per adapter skill (e.g. mock ClickUp/Figma API responses) would close it,
  but is out of scope for this task.
