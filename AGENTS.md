# AGENTS.md — <project_name>

Local constitution. **Inherits the agentic core** vendored from
[BGavazzi/agentic-pipeline](https://github.com/BGavazzi/agentic-pipeline)
(`.claude/skills/` + `scripts/` copied in directly, or pointed at via
`PIPELINE_SCRIPTS_DIR` — see that repo's README Quick Start).
This file is repo-specific and is NEVER overwritten by a core sync — edit it freely.

**Version**: 0.1.0  ·  **Status**: <tier>  ·  **Type**: <one-line type>

---

## §0 Protocol Zero — Continuity

1. **READ** `.agents/continuity-<your-agent>.md` (create if it doesn't exist).
2. **ALIGN** with the "Current Focus".
3. **UPDATE** at the end of the session.

```yaml
multi_agent: false
sdd_kit_path: docs/SDD_KIT.md
function_catalog: .docs/function-catalog.md
route_map: .docs/ROUTE_BEHAVIOR_MAP.md
task_dir: .docs/tasks
clickup_list_id: <optional, if synced>
pipeline_scripts_dir: <optional, defaults to ./scripts/>   # see PIPELINE_SCRIPTS_DIR in agentic-pipeline's README
```

---

## §1 Identity and Scope

**Name**: <project_name>
**Maintained by**: <maintainer>
**Type**: <type>
**Tier**: <prototype | active | canonical>

### 1.1 Stack
| Layer | Technology |
|---|---|
| <e.g.: Runtime> | <e.g.: FastAPI + Docker> |

---

## §2 Hard Rules

🔒 **Never delete** files. `mv` to `.archive/`.
🔒 **Never commit OR post secrets.** `.env` in `.gitignore`. Never write credentials to external systems (ClickUp/GitHub/Slack/SaaS), even if asked — pause and propose an alternative.
🔒 **Core is read-only.** Skills under `.claude/skills/` vendored from agentic-pipeline are not edited here — fix upstream in the pipeline repo and re-copy. Local skills use a distinct name.
🔒 **PR is the clean merge unit.** Never recycle a wrong PR — new PR + close the old one. Conflict = rebase on base (`integration`/`main`).
🔒 **"Keep going" ≠ inventing scope.** In autonomous mode (dispatcher/loop), only explicit requests; do not derive from old backlog/specs without per-feature confirmation.

**Shared conventions** (in agentic-pipeline): [`git-pr-workflow.md`](https://github.com/BGavazzi/agentic-pipeline/blob/main/.docs/conventions/git-pr-workflow.md) · [`engineering-defaults.md`](https://github.com/BGavazzi/agentic-pipeline/blob/main/.docs/conventions/engineering-defaults.md) · [`agent-conduct.md`](https://github.com/BGavazzi/agentic-pipeline/blob/main/.docs/conventions/agent-conduct.md)

---

## §3 Task Closure Law

Before marking a task `done`, all of these must be updated (`validate_closure.py` checks):

| # | Artifact | When |
|---|---|---|
| 1 | `CHANGELOG.md` | Always |
| 2 | `<function_catalog>` | Signature change |
| 3 | `<sdd_kit_path>` | New Dxx decision |
| 4 | `README.md` | User-visible change |
| 5 | `.agents/continuity-<agent>.md` | Always |
| 6 | Tests passing | Always |
| 7 | `<route_map>` | Route/handler/model changed |
| 8 | **PR approved** | Task that produces code |

`[N/A]` with a 1-line justification if not applicable.
🔒 **Task only closes with an approved PR** — a task with code only becomes `done`/moves to `completed/` with an approved PR; an open PR is not enough (stays `in_progress` in review until human approval). The dispatcher does NOT close the task when opening the PR.

---

## §4 Tasks

### 4.1 Naming (shared convention)
`<task_dir>/NNNN-type-slug.md` — `NNNN` 4 digits; `type`: feat/fix/refactor/docs/chore/audit/proposal/infra/test.
`validate_task.py` validates the frontmatter (F1–F12).

### 4.2 Minimum frontmatter
```yaml
---
status: todo | in_progress | done
priority: P0 | P1 | P2
type: feat | fix | ...
created: YYYY-MM-DD
updated: YYYY-MM-DD
clickup_id: <id|null>
parent: null
blocks: []
blocked_by: []
---
```

### 4.3 State
- Open: `<task_dir>/NNNN-...md` · Completed: `<task_dir>/completed/NNNN-...md` (move on close) · Planning: `<task_dir>/planning/`

### 4.4 Skills inherited from core

| Skill | Purpose |
|---|---|
| `grill-me` | Interview the task author until the spec is actionable |
| `codebase-grounding` | Map the repo before touching anything |
| `builder` | Execute a task in code |
| `tester` | Validate §Exit Conditions (prototype mode) |
| `librarian` | Closure Law §3 |
| `notifier` | Post summary to ClickUp + GitHub |
| `dispatcher` | Orchestrate the `<task_dir>` queue (quota-aware; interactive sessions only) |
| `codebase-audit` | Read-only repo health checks |

---

## §5 Style

ClickUp comments: caveman/terse, TL;DR above 200 chars. See convention in <org-scripts-repo>.
