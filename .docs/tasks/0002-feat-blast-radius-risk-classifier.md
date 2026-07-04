---
status: in_progress
priority: P1
type: feat
created: 2026-07-04
updated: 2026-07-04
clickup_id: null
parent: null
blocks: []
blocked_by: []
---

# 0002 — Feat: diff-scoped blast-radius + risk-tier classifier gate

## Context
Discussion (2026-07-04) on scaling test scope to the size/risk of a change
instead of either "always run everything" or "trust the LLM to pick tests."
`ultrareview` already computes `risk_level: high` for tasks touching
schema/RBAC/migration/contract (see its SKILL.md), but nothing today computes
*blast radius* (which modules/tests a diff plausibly affects) or extends risk
classification to infra changes (Ansible/Rancher/Nexus-shaped tasks). This
task adds a single deterministic script that both `tester` and `ultrareview`
can consume, rather than each guessing scope independently.

## Problem
Today, `tester` and `ultrareview` either run a fixed test scope or rely on
the model's judgment about what's "relevant" to re-run — which is exactly the
kind of self-reported claim the pipeline's anti-fake-green philosophy
(gate on artifacts, not prose) already refuses to trust elsewhere.

## What To Do
- [x] Add `scripts/blast_radius.py`, run right after [[builder]] and before
  [[tester]]:
  - Input: `git diff <base>...<branch>` (changed files) — base/branch
    auto-detect (integration/main/master, falls back to local branches when
    no `origin` remote exists, e.g. a fresh sandbox)
  - Signal 1 — ownership map: cheap per-module "who depends on me" list
    (`.docs/module-owners.md`; missing file = signal skipped, not an error)
  - Signal 2 — import/grep heuristic: literal grep for each changed file's
    stem across tracked files (no AST, no dependency-graph build)
  - Signal 3 — historical co-change: files that changed together with the
    diff's files in prior commits, above a min co-occurrence count. Note:
    implemented as commit-SHA collection + `git diff-tree` per SHA, NOT
    `git log -- <path> --name-only` — the latter silently restricts the
    file list to the same pathspec and never surfaces co-changed files
  - Union the three signals into `affected_modules`
- [x] Risk classification with path/diff triggers for: auth/RBAC,
  migrations, payment/billing, and — per the Ansible/Rancher/Nexus
  discussion — Ansible/Helm/Fleet/Terraform manifests and Rancher/Nexus
  paths. `ultrareview` did not have a separate risk_level computation of its
  own to "reuse" (it received risk_level as a plain input, assigned inline
  by dispatcher's prose) — this task makes `blast_radius.py` the single
  source of truth and dispatcher/ultrareview now read from it instead
- [x] Emit `.docs/blast-reports/<NNNN>.json`:
  `{task, base, branch, changed_files, affected_modules, risk_level,
  risk_triggers, required_gates}`; `required_gates` drawn from
  `["unit","integration","sast","sca","ultrareview","infra-dry-run"]` based
  on risk tier (low/medium/high)
- [x] Wired `tester` and `ultrareview` SKILL.md to read `required_gates`/
  `risk_level` from this artifact; `dispatcher` SKILL.md §4 gains step 5b
  invoking the script between builder and tester
- [x] `risk_level: high` + an infra trigger (ansible/helm/fleet/terraform/
  rancher-or-nexus) → `required_gates` includes `infra-dry-run`. Note: this
  task implements the CLASSIFIER flagging the requirement; it does not
  implement the dry-run mechanics themselves (`ansible-playbook --check`,
  `helm template`+`kubeconform`, Fleet dry-run) — that remains follow-up work
  once an actual infra repo exists to exercise it against (see Honest
  Backlog)

## Affected Files
- `scripts/blast_radius.py` (new)
- `.claude/skills/tester/SKILL.md` (consume `required_gates`)
- `.claude/skills/ultrareview/SKILL.md` (consume `required_gates`; extend
  risk-trigger list)
- `.gitignore` (`.docs/blast-reports/`)

## Exit Conditions
- [x] `blast_radius.py` runs standalone against a diff and emits a valid
  JSON artifact with `changed_files`/`affected_modules`/`risk_level`/
  `required_gates` populated
- [x] Risk-tier trigger list is a single shared source: `ultrareview` and
  `dispatcher` SKILL.md now point at the artifact/script instead of
  embedding their own copy of the trigger list
- [x] Test coverage confirms a change under a high-risk path (auth/, an
  Ansible playbook) produces `risk_level: high` + the expected
  `required_gates`, a medium-risk change (via ownership map) produces
  `risk_level: medium`, and an isolated low-risk change produces
  `risk_level: low` with `required_gates: ["unit"]` only. Implemented as a
  plain `pytest` unit test (`tests/test_blast_radius.py`, 6 cases, all
  green) against a throwaway git sandbox, NOT an Agent-spawned `meta-test`
  fixture — `meta-test` exercises a SKILL.md's LLM-driven behavior via a
  subagent, and `blast_radius.py` has no LLM reasoning in it (same
  reasoning as why `validate_task.py`/`validate_closure.py` have no
  meta-test fixture either). See Honest Backlog for what a future
  `meta-test` fixture covering the *dispatcher wiring* would still add.

## Required Documentation (Closure Law)
- [x] `CHANGELOG.md` updated
- [ ] `<function_catalog>` — [N/A] core/tooling repo, no function-catalog.md
- [ ] `<sdd_kit_path>` — [N/A] no SDD_KIT.md in this repo yet
- [ ] `README.md` — [N/A] script is used internally by the dispatcher; no
  user-facing quick-start change needed for this increment (BYO dependency
  table already covers `scripts/` generally)
- [ ] `.agents/continuity-<agent>.md` — [N/A] no continuity ledger in use yet
- [x] Tests passing (`pytest tests/test_blast_radius.py` — 6/6 green)
- [ ] `<route_map>` — [N/A] no HTTP routes in this repo
- [ ] PR approved — pending human review; stays `in_progress` until then

## Honest Backlog
- Historical co-change mining (signal 3) needs a minimum commit-history depth
  to be useful; on a fresh/shallow-cloned repo it degrades to signals 1+2
  only — acceptable for V1, flagged here rather than blocking the task.
- `infra-dry-run` is flagged by the classifier as a required gate but its
  actual mechanics (`ansible-playbook --check`, `helm template`+
  `kubeconform`, Fleet dry-run) are not implemented — there's no infra repo
  in this pipeline yet to exercise it against. Follow-up task once one exists.
- No `meta-test` fixture covers the *dispatcher wiring* end-to-end (step 5b
  actually firing between builder and tester in a live dispatcher run) —
  today's test coverage is a direct unit test of the classifier itself, not
  of the orchestration. Worth a fixture once `006-tester-prototype-mode` (see
  meta-test's own roadmap) exists to build on.
- `import_grep_signal` reads every tracked file's full contents on each run
  (no caching, no size cap) — fine at this repo's current size, would need
  revisiting before pointing this at a large monorepo.
- Dogfooding this against the repo's own real diff (task 0002's own PR)
  caught a precision bug: the grep stem "SKILL" (from every `SKILL.md`)
  matched almost everything. Fixed with a generic-stem stoplist + word-
  boundary matching (see CHANGELOG). `affected_modules` also mixes owner
  TAGS (e.g. `pipeline-scripts`) with file PATHS in the same list per the
  original spec — works, but is a minor API wart; a future pass could
  separate them into `affected_owners` vs `affected_files` if it starts
  causing confusion downstream.
