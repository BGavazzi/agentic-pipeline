# agentic-pipeline

[![CI](https://github.com/BGavazzi/agentic-pipeline/actions/workflows/ci.yml/badge.svg)](https://github.com/BGavazzi/agentic-pipeline/actions/workflows/ci.yml)

Minimal agentic task-processing pipeline for Claude Code — skills, task lifecycle, and deterministic gates you can drop into any repo.

Pick up tasks from `.docs/tasks/`, run them through the Triple-Diamond pipeline (grounding → build → test → adversarial review → closure), and ship PRs — unattended or interactively.

## What's here

```
.claude/skills/          ← pipeline skills (invoke via Claude Code Skill tool)
  dispatcher/            ← orchestrator: reads task queue, chains all stages
  codebase-grounding/    ← enriches brief with repo context before building
  builder/               ← codegen: implements the task, runs tests
  tester/                ← validates §Exit Conditions, emits proof artifact
  ultrareview/           ← adversarial independent review (fake-green scanner)
  librarian/             ← Closure Law §3: updates CHANGELOG, SDD_KIT, README
  notifier/              ← posts structured comments to GitHub PR + ClickUp
  grill-me/              ← relentless plan/design interview (gate before build)
  codebase-audit/        ← read-only audit of repo against its own rules
  meta-test/             ← design spec for fixture-based skill tests (not yet implemented — see SKILL.md)
  clickup-api/           ← generic ClickUp API v2 reference (auth, rate limit, discovery) — BYO credentials
  clickup-grounding/     ← enriches a single ClickUp task with its own list/comment/blocker context
  clickup-audit/         ← read-only audit of a ClickUp workspace against its own conventions
  figma-api/             ← generic Figma REST API reference (auth, node fetch, image export) — BYO credentials
  figma-frontend-context/← turns a Figma frame/sticky into a structured implementation brief
  implement-figma-task/  ← builder specialization: writes the diff for a Figma-sourced brief
  visual-tester/         ← CDP screenshot + pixel diff vs. a reference image (design or baseline)
  zap-comms/             ← generic WhatsApp messaging over a self-hosted Evolution API instance — BYO instance
  whatsapp-clickup/      ← inbound WhatsApp message → ClickUp task, composed from zap-comms + clickup-api

scripts/
  quota_gate.py          ← daily/weekly token budget enforcement for /loop
  validate_task.py       ← validates .docs/tasks/*.md schema before dispatch
  validate_closure.py    ← validates Closure Law §3 compliance post-librarian
  blast_radius.py        ← diff-scoped blast-radius + risk-tier classifier

tests/
  test_blast_radius.py   ← real pytest unit tests for blast_radius.py (run in CI)

.docs/
  tasks/
    000-template.md      ← template for new task files
  conventions/
    agent-conduct.md     ← how an agent must behave (scope, boards, grilling)
    git-pr-workflow.md   ← branch/PR lifecycle rules
    engineering-defaults.md ← coding defaults (backend, frontend, DB)
    notify-on-stop.md    ← agent must notify human before stopping unattended
    migration-timestamp-ms.md ← DB migration naming convention

AGENTS.md                ← repo constitution (loaded by every Claude Code session)
GDFRSBT.md               ← task lifecycle: states, transitions, Closure Law §3
```

## Quick start

### 1. Copy the core into your target repo
`.claude/skills/`, `scripts/`, and `.docs/conventions/` are meant to be
vendored into the repo you're actually building — this repo is the source,
not the workspace. Either copy `scripts/` in directly, or set
`PIPELINE_SCRIPTS_DIR` to point at wherever you placed it (`dispatcher` and
`librarian` both read this env var; default is `<repo>/scripts/`).

### 2. Copy constitution
Edit `AGENTS.md` — fill in your repo name, stack, and any project-specific rules.

### 3. Create a task
```
cp .docs/tasks/000-template.md .docs/tasks/0001-my-first-task.md
# edit it, fill in §What To Do and §Exit Conditions
```

### 4. Run the pipeline
```
# Interactive (single task):
/codebase-grounding
/builder
/tester
/ultrareview
/librarian

# Unattended (full queue, bounded by quota):
/dispatcher
# or: /loop
```

## BYO dependencies

| Skill | What you need |
|---|---|
| `dispatcher`, `librarian` | `gh` CLI, authenticated — both open/edit PRs via `gh pr create` / `gh pr edit` |
| `dispatcher`, `librarian` | `scripts/` (this repo's) copied into your target repo, or `PIPELINE_SCRIPTS_DIR` set |
| `validate_task.py`, `validate_closure.py` | Python 3 + `pyyaml` (`pip install pyyaml`) |
| `dispatcher` (`/loop` unattended mode only) | `.claude/statusline_quota.py` writing `.claude/quota-state.json` from Claude Code's `rate_limits` injection (Pro/Max only), wired via `.claude/settings.json`'s `statusLine`. **Not bundled in this repo — you write it.** Without it, `quota_gate.py` fails safe (STOP) and `/loop` can't run unattended; interactive single-task use (step 4, top block) doesn't need this at all. |
| `notifier` | GitHub token (`GITHUB_TOKEN`) for PR comments; ClickUp token optional |
| `grill-me` | ClickUp API key (`CLICKUP_API_KEY`) for poll/per-task modes; interactive mode works without |
| `quota_gate.py` | No external deps — reads/writes `.claude/quota-state.json` (see `/loop` row above for how that file gets populated) |
| `clickup-api`, `clickup-grounding`, `clickup-audit` | `CLICKUP_API_KEY` (+ `CLICKUP_WORKSPACE_ID`/`CLICKUP_SPACE_ID` for grounding/audit) — no org, workspace, or bot persona baked in |
| `figma-api`, `figma-frontend-context`, `implement-figma-task` | `FIGMA_API_KEY` — no team/project/file baked in |
| `visual-tester` | A Chrome instance reachable via CDP (`--remote-debugging-port`), already logged into whatever the app under test requires; the CDP-attach + diff scripts (`live_shot.mjs`/`figma_export.mjs`/`diff.mjs`) are BYO, wired per repo |
| `zap-comms`, `whatsapp-clickup` | A self-hosted [Evolution API](https://github.com/EvolutionAPI/evolution-api) instance (`EVOLUTION_API_URL`, `EVOLUTION_API_KEY`, `EVOLUTION_INSTANCE_NAME`); `whatsapp-clickup` additionally needs `clickup-api`'s vars |

All nine live in **this repo**, under the same `.claude/skills/` as every
other skill above — they are not a separate package or a vendored external
repo, and there's nothing extra to clone or sync to use them. They're
generic reference/adapter skills: no company, team, or bot persona is
encoded in them, and they sit idle (and cost nothing) until their env vars
are set. Each `SKILL.md` documents its own precondition check and prints
setup instructions rather than guessing when a credential is missing.

## License

MIT
