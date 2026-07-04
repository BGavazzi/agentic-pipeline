# agentic-pipeline

Minimal, company-agnostic agentic task-processing pipeline for Claude Code.

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
  meta-test/             ← fixture-based tests of the pipeline skills themselves

scripts/
  quota_gate.py          ← daily/weekly token budget enforcement for /loop
  validate_task.py       ← validates .docs/tasks/*.md schema before dispatch
  validate_closure.py    ← validates Closure Law §3 compliance post-librarian

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

### 1. Copy constitution
Edit `AGENTS.md` — fill in your repo name, stack, and any project-specific rules.

### 2. Create a task
```
cp .docs/tasks/000-template.md .docs/tasks/0001-my-first-task.md
# edit it, fill in §O Que Fazer and §Condições de Saída
```

### 3. Run the pipeline
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
| `notifier` | GitHub token (`GITHUB_TOKEN`) for PR comments; ClickUp token optional |
| `grill-me` | ClickUp API key (`CLICKUP_API_KEY`) for poll/per-task modes; interactive mode works without |
| `quota_gate.py` | No external deps — reads/writes `.claude/quota-state.json` |

## Skills not included

These require platform-specific credentials or infra and are not part of this core repo:

- `clickup-api`, `clickup-grounding`, `clickup-audit` — ClickUp-coupled
- `figma-api`, `figma-frontend-context`, `implement-figma-task` — Figma-coupled
- `visual-tester` — Playwright CDP + screenshot infra required
- `whatsapp-clickup`, `zap-comms` — WhatsApp / Evolution API

## License

MIT
