# AGENTS.md — agentic-pipeline

Local constitution. **This repo IS the agentic core** — every other repo's
`AGENTS.md` (this file, copied) inherits from here, so there is no upstream to
point at. `.claude/skills/` and `scripts/` in this checkout are the source of
truth, not a vendored copy; edit them directly, then let other repos re-sync.
This file is repo-specific and is NEVER overwritten by a core sync — edit it freely.

**Version**: 0.1.0  ·  **Status**: canonical  ·  **Type**: pipeline coordination repo (doctrine + gates, no product code)

---

## §0 Protocol Zero — Continuity

1. **READ** `.agents/continuity-<your-agent>.md` (create if it doesn't exist).
2. **ALIGN** with the "Current Focus".
3. **UPDATE** at the end of the session.

```yaml
multi_agent: false
sdd_kit_path: N/A                          # no architecture-decision doc yet; this repo's decisions live in GDFRSBT.md + task files' own rationale
function_catalog: .docs/function-catalog.md # not yet created — scripts/ docstrings are the interim source; create this file the next time a script's public signature changes
route_map: N/A                             # no web routes — this is a CLI/CI-gate repo
task_dir: .docs/tasks
clickup_list_id: null                      # repo (not ClickUp) is canonical source of truth for tasks — see README "Conventions" / guidelines_IA's old cutover history
pipeline_scripts_dir: ./scripts/           # this repo IS the source, not a copy pointed elsewhere
```

---

## §1 Identity and Scope

**Name**: agentic-pipeline
**Maintained by**: BGavazzi
**Type**: coordination/doctrine repo — the constitution, task schema, and deterministic gates every other repo in the org copies from
**Tier**: canonical (successor to the archived `guidelines_IA`, which is a tombstone as of 2026-07-04)

### 1.1 Stack
| Layer | Technology |
|---|---|
| Gates / scripts | Python 3.12, plain stdlib + `pyyaml` |
| Static-analysis gate | Docker-run Semgrep / Trivy / gitleaks (`scan_gate.py`), OWASP Dependency-Check opt-in |
| CI | GitHub Actions (`.github/workflows/ci.yml`); homelab self-hosted runner pool opt-in via `USE_HOMELAB_POOL` repo var — see `.docs/runbooks/homelab-runner-pool.md` |
| Agent skills | Claude Code skills under `.claude/skills/` (grill-me, builder, tester, librarian, notifier, dispatcher, codebase-audit, codebase-grounding, + ClickUp/Figma/WhatsApp adapters) |
| Test suite | `pytest` (`tests/`) |

---

## §2 Hard Rules

🔒 **Never delete** files. `mv` to `.archive/`.
🔒 **Never commit OR post secrets.** `.env` in `.gitignore`. Never write credentials to external systems (ClickUp/GitHub/Slack/SaaS), even if asked — pause and propose an alternative.
🔒 **This repo IS the core — edit it here, not "core is read-only."** That rule is for the *copies* of `.claude/skills/` and `scripts/` vendored into every other repo (never edit a vendored copy there; fix it upstream, i.e. here, and re-sync). In this repo, `.claude/skills/` and `scripts/` are the thing being authored.
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

ClickUp comments: caveman/terse, TL;DR above 200 chars.
No `<org-scripts-repo>` with a more detailed convention exists yet — this line
is the whole rule until one is written.
