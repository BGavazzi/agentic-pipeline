---
status: in_progress
priority: P1
type: feat
created: 2026-09-04
updated: 2026-09-04
clickup_id: null
parent: null
blocks: []
blocked_by: []
---

# 0005 — feat: core-sync script (automate core vendoring into satellite repos)

## Context
The portfolio completeness benchmark (`.docs/analysis/completeness-benchmark-2026-09.md`)
found the doctrine followed almost perfectly by the repos it was written for
(FIS repos, median 20/24) and almost not at all by the rest of the portfolio
(median 6/24). The gap isn't that the doctrine is wrong for those repos — it's
that adopting it meant manually copying `.claude/skills/`, gate scripts, and
`.docs/conventions/*.md` into every target repo and hand-editing a template
`AGENTS.md`, and nobody actually did that consistently. This is item 3 of the
user-ordered remediation list from that benchmark ("build a core-sync script
— this is the actual lever behind the 6/24-vs-20/24 gap").

## Problem
`README.md`'s Quick Start told every satellite repo to "copy `scripts/` in
directly, or set `PIPELINE_SCRIPTS_DIR`" and "Edit `AGENTS.md`" by hand — a
manual, undocumented, drift-prone process with no re-sync story once the core
itself changes.

## What To Do
- [x] `scripts/core_sync.py`: copy `.claude/skills/` (optionally filtered by
      `--skills` allowlist) into a target repo
- [x] Copy a whitelisted set of gate scripts (`GATE_SCRIPTS`) into
      `<target>/scripts/` — not the whole directory, so a target's own
      unrelated scripts are never at risk
- [x] Copy `.docs/conventions/*.md` into the target
- [x] Seed `<target>/AGENTS.md` from a generic template, but only when the
      target has none yet — never overwrite repo-specific content
- [x] `--dry-run` flag that makes zero filesystem changes
- [x] Unit tests (`tests/test_core_sync.py`) against fixture source/target
      trees, plus integration-style tests against this repo's own real
      source tree
- [x] Update `README.md` Quick Start to reference the script instead of the
      manual copy instructions

## Affected Files
- `scripts/core_sync.py` (main)
- `tests/test_core_sync.py` (tests)
- `README.md` (Quick Start section)

## Exit Conditions
- [x] `python scripts/core_sync.py <target>` vendors skills/gate
      scripts/conventions/AGENTS.md into a target repo with zero manual
      copy-paste
- [x] Re-running against a repo that already has an `AGENTS.md` never
      touches it
- [x] Test suite passes 100%

## Required Documentation (Closure Law)
- [x] `CHANGELOG.md` updated
- [N/A] `<function_catalog>` — doesn't exist yet in this repo (noted in
      AGENTS.md §0 as not-yet-created); nothing to update
- [N/A] `<sdd_kit_path>` — no SDD_KIT.md in this repo; no Dxx decision log
- [x] `README.md` updated (Quick Start now points at the script)
- [N/A] `.agents/continuity-<agent>.md` — not in use this session
- [x] Tests passing
- [N/A] `<route_map>` — no web routes in this repo
- [ ] PR approved — stays `in_progress` until PR review lands

## Honest Backlog
- No drift detection: if someone hand-edits a vendored skill or gate script
  in a target repo (violating "core is read-only"), core_sync silently
  overwrites it on next sync rather than warning first. Acceptable for V1 —
  the whole point of "core is read-only" is that target-local edits to
  vendored files shouldn't happen in the first place.
- Doesn't touch git in the target repo (no commit/branch) — caller reviews
  and commits the diff themselves, consistent with every other gate script
  in this repo.
- Doesn't seed `.docs/tasks/`, `CHANGELOG.md`, or `.agents/continuity-*.md`
  in the target — those are project-specific content, not core, and seeding
  them blindly would be worse than leaving them for the target repo's own
  first task.
