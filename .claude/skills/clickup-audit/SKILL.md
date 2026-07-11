---
name: clickup-audit
description: Audits a ClickUp workspace/space (read-only) against its own declared conventions — naming pattern drift, tasks missing required custom fields, orphaned custom fields (defined but unused), stale tasks stuck in a status too long, tasks with no assignee past a grace period, and drift between .docs/tasks/ files and their linked ClickUp counterparts. Triggers - "audit the ClickUp space", "ClickUp drift scan", "monthly board housekeeping". Requires CLICKUP_API_KEY + CLICKUP_WORKSPACE_ID (+ CLICKUP_SPACE_ID). STATUS - V1 = 4 core checks; rest is backlog.
tools: Bash, WebFetch, Read, Glob, Write
---

# ClickUp Audit

**Do NOT confuse with [[codebase-audit]]** (a git repo). This audits a
**ClickUp workspace/space** against conventions you define for your team —
it never touches a git repo.

V1 implements 4 core checks:
1. `naming_pattern_drift`
2. `stale_status`
3. `local_clickup_drift` (`.docs/tasks/*.md` ↔ linked ClickUp task out of sync)
4. `unassigned_past_grace`

V2 backlog: `orphan_custom_field`, `duplicate_task_title`, `missing_priority`.

---

## Precondition

`CLICKUP_API_KEY` and `CLICKUP_WORKSPACE_ID` required; `CLICKUP_SPACE_ID`
required to scope the scan (auditing an entire workspace across spaces is
expensive and rarely what's wanted). Absent → print setup instructions, exit.
Auth/discovery/rate-limit patterns: [[clickup-api]].

---

## Inputs

- `space_id`: defaults to `$CLICKUP_SPACE_ID`
- `checks`: optional subset (default: all V1)
- `naming_pattern`: optional regex or example, if the team has one (default: none — check is a no-op without it)
- `stale_after_days`: default `14` — days in the same non-terminal status before flagging
- `grace_days`: default `2` — days a new task may stay unassigned before flagging
- `repo_paths`: optional list of local repos to cross-check against (for `local_clickup_drift`)

---

## Main loop

```
1. Discover space schema:
   GET /space/{space_id}/folder → GET /folder/{id}/list  (per list)
   For each list: GET /list/{id} (statuses) + GET /list/{id}/field (custom fields)

2. Fetch tasks:
   GET /team/{workspace_id}/task?space_ids[]=<space_id>&include_closed=true
   (paginate; sleep 0.7s between pages per rate-limit hygiene)

3. For each check in `checks`:
   a. Apply rule (§Checks below)
   b. List violations [(task_id, task_name, list, reason, severity)]

4. Write report:
   - Markdown: <cwd>/.docs/audit-reports/<YYYY-MM-DD>-clickup-audit.md
   - JSON:     <cwd>/.docs/audit-reports/<YYYY-MM-DD>-clickup-audit.json

5. Output summary (§Output below).

6. Do NOT edit tasks, do NOT post comments. Human triage decides.
```

---

## Checks — implementation

### naming_pattern_drift

Only runs if `naming_pattern` was supplied. Match every task `name` in scope
against the pattern; list mismatches.

Severity: `warn` (a convention, not an API constraint).

### stale_status

```
for task in tasks where status not in {terminal statuses}:
    days_in_status = (now - task.status_last_changed) / 86400
    if days_in_status > stale_after_days:
        flag(task, f"stuck in '{task.status}' for {days_in_status}d")
```

`status_last_changed` — ClickUp doesn't expose this directly on the task
object; derive it from the task's history (`GET /task/{id}` includes
`date_updated`, which is a reasonable proxy when the field itself changed
recently, but isn't exact for status specifically — note the approximation
in the report rather than presenting it as precise).

Severity: `warn`.

### local_clickup_drift

For each `repo_paths` entry, glob `.docs/tasks/*.md` (+ `completed/`), read
frontmatter `clickup_id` + `status`. For each non-null `clickup_id`, fetch
the ClickUp task and compare `status`. Mismatch → flag both sides.

Severity: `error` (this is a caller-facing correctness bug, not a style nit) — since it means someone will act on stale information in one of the two places.

### unassigned_past_grace

```
for task in tasks where assignees == [] and status not in {terminal statuses}:
    days_open = (now - task.date_created) / 86400
    if days_open > grace_days:
        flag(task, f"unassigned for {days_open}d")
```

Severity: `info`.

---

## Output

```
✅ ClickUp Audit — space <space_id>
Lists scanned: <N>
Tasks scanned: <M>
Checks: 4/4 V1

Violations:
  error: <N>
  warn:  <M>
  info:  <K>

Top 3:
  1. local_clickup_drift — task <id> "<name>": local=done, ClickUp=in progress
  2. stale_status — task <id> "<name>": stuck in "review" ~21d
  3. unassigned_past_grace — task <id> "<name>": unassigned ~5d

Report: <cwd>/.docs/audit-reports/<date>-clickup-audit.md
JSON:   <cwd>/.docs/audit-reports/<date>-clickup-audit.json

Next: human triage — resolve drift, reassign, or accept as-is.
```

---

## Hard rules

- **Read-only.** No `PUT`/`POST`/`DELETE` call against ClickUp in this skill.
- **Does not create tasks or comments** for violations found — human triage decides, same rationale as [[codebase-audit]].
- **Does not invent conventions** — `naming_pattern_drift` is a no-op without an explicit pattern; doesn't guess one from observed data.
- **Rate limit hygiene** — paginate with `sleep 0.7s`; a large space can be hundreds of tasks.

## Failure modes

| Error | What to do |
|---|---|
| `CLICKUP_SPACE_ID` absent | Print setup instructions, exit — refuse to scan "everything" by default |
| Space has 0 lists | No-op, report "empty space" |
| `local_clickup_drift` repo has no `.docs/tasks/` | Skip that repo for this check, note in report |
| Pagination exceeds ~2000 tasks | Warn, cap scan, note in report as `"partial": true` |
| Specific check crashes | Skip, log, continue others |

## Anti-patterns

- ❌ Auto-fixing drift (e.g. silently overwriting local status from ClickUp) — surfaces it, doesn't decide which side is right.
- ❌ Scanning the entire workspace without a `space_id` scope "to be thorough."
- ❌ Treating `date_updated` as an exact status-change timestamp — it's a proxy, say so.
- ❌ Running this on every dispatcher tick — like [[codebase-audit]], this is a periodic housekeeping job, not a pipeline gate.

## Skills consumed / produced

- Reuses: [[clickup-api]] for auth/discovery/rate-limit patterns.
- Related: [[codebase-audit]] — repo scope, this is workspace scope. Complementary, not overlapping.
- Related: [[clickup-grounding]] — single-task scope; this is aggregate scope.
