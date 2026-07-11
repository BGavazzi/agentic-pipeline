---
name: clickup-api
description: Generic ClickUp API v2 integration — auth, rate limiting, dynamic discovery (never hardcode IDs), assignee resolution, and task CRUD. Use when the user wants to create/read/update/close ClickUp tasks, map a `.docs/tasks/NNNN-*.md` file to a ClickUp task, resolve assignees by name, or read task state for pipeline decisions. BYO credentials — no org/workspace baked in. STATUS - reference skill (auth + endpoints), consumed by grill-me/notifier/clickup-grounding/clickup-audit.
tools: Bash, WebFetch, Read, Glob
---

# ClickUp API

Generic ClickUp API v2 reference. No workspace, space, or bot identity is
hardcoded here — every ID is discovered at runtime or supplied via env var.
Other skills (`grill-me`, `notifier`, `clickup-grounding`, `clickup-audit`,
`whatsapp-clickup`) treat this file as the shared auth/rate-limit/discovery
reference rather than re-deriving it.

---

## When to Use

- Create a task from technical work or planning
- Read a task for pipeline context (status, assignees, custom fields)
- Update status, comments, or due dates
- Map a `.docs/tasks/NNNN-*.md` file to the board
- Resolve a person's name → user ID before creating/updating a task
- Any operation where the user says "ClickUp", "task", "board", "sprint"

---

## Auth & Setup

### Environment variables

| Variable | Purpose |
|---|---|
| `CLICKUP_API_KEY` | Personal or bot token (`pk_...`). Header: `Authorization: <token>` — **no** `Bearer` prefix |
| `CLICKUP_LIST_ID` | Default target list (e.g. active sprint) |
| `CLICKUP_WORKSPACE_ID` | Team ID, used in `/team/{id}/...` |
| `CLICKUP_DEFAULT_ASSIGNEE_ID` | Fallback assignee (e.g. the bot's own user ID) — optional |

Read these from the process environment only (`$CLICKUP_API_KEY` or
equivalent). **Never** read credentials from a file and echo the value into
code, logs, or a committed file — that's how tokens leak.

### Required header

```
Authorization: <CLICKUP_API_KEY>
Content-Type: application/json
```

The ClickUp API v2 does **not** use a `Bearer` prefix.

---

## Rate Limiting

- Official cap: **100 req/min** per token
- Safe margin: **90 req/min** (~1.5 req/s) — add `sleep 0.7s` between calls in loops/batches
- On `429`: honor the `Retry-After` header, or exponential backoff (max 3 retries)

---

## Base URL

```
https://api.clickup.com/api/v2
```

---

## Discovery pattern (never hardcode IDs)

Always discover structure at runtime; cache in-session, don't repeat the same
discovery call within one invocation.

```bash
# 1. Workspace → Spaces → Folders → Lists
GET /team/{workspace_id}/space
GET /space/{space_id}/folder
GET /folder/{folder_id}/list

# 2. Custom fields of the target list
GET /list/{list_id}/field
# → cache {field_name_lower: field_id}, 1h TTL

# 3. Members of the target list (for assignee resolution)
GET /list/{list_id}/member
# → cache, 1h TTL
```

---

## Core operations

### Create task

```bash
POST /list/{list_id}/task
{
  "name": "<title>",
  "description": "<description — schema is caller-defined, see §Task schema>",
  "status": "<status discovered via GET /list/{list_id} — never assume 'todo' exists>",
  "assignees": [<user_id>],        # optional
  "due_date": <unix_ms>,           # optional
  "due_date_time": true,
  "priority": <1-4>,               # 1=urgent 2=high 3=normal 4=low
  "custom_fields": [
    {"id": "<field_id>", "value": "<value>"}
  ]
}
```

### Read task

```bash
GET /task/{task_id}
GET /task/{task_id}?include_subtasks=true
```

### Update task

```bash
PUT /task/{task_id}
{ "status": "<exact status name>", "description": "<new description>", ... }
```

### Comment

```bash
POST /task/{task_id}/comment
{"comment_text": "<text>"}
```

For non-ASCII/emoji text posted from a Windows shell, use the Write-tool +
`--data-binary` method documented in `../notifier/SKILL.md` §3 — inline
`curl -d` corrupts UTF-8 on that platform.

### Search

```bash
GET /team/{workspace_id}/task?query=<term>&statuses[]=<status>
```

---

## Task schema (caller-defined, adapt to your project)

This skill does not mandate a specific description schema — that's a
project convention, not an API concern. If your repo's task convention is
the one in `.docs/tasks/000-template.md` (§Context / §What To Do / §Affected
Files / §Exit Conditions / §Documentação Obrigatória), mirror those section
headers verbatim in the ClickUp `description` field so a task can be read
from either source with the same fields. If your project uses a different
schema, use that instead — don't invent one here.

Suggested custom-field mapping (discover actual `field_id`s via
`GET /list/{list_id}/field`):

| ClickUp field | Local task mapping |
|---|---|
| `status` (native) | frontmatter `status` |
| `priority` (native) | frontmatter `priority` |
| `assignees` (native) | frontmatter `author` / assignee hint |
| `due_date` (native) | frontmatter `due_date` |
| `clickup_id` (custom, if you add one) | auto-filled after creation |

---

## Assignee resolution (fuzzy match)

Never assume a user ID from a name string — always resolve against the
list's actual members:

```python
members = GET /list/{list_id}/member   # cache 1h
for member in members:
    score = SequenceMatcher(hint.lower(), member["username"].lower()).ratio()
    if score >= 0.6:                    # threshold, tune per team
        return member["id"]
# fallback: CLICKUP_DEFAULT_ASSIGNEE_ID, or ask
```

Implement the equivalent in Bash/Python/JS depending on the calling context.

---

## Due-date parsing (natural language, locale-agnostic)

```python
import dateparser
parsed = dateparser.parse(
    hint,                              # e.g. "tomorrow", "next week", "friday"
    languages=["en"],                  # swap/add locales as needed, e.g. ["pt", "en"]
    settings={
        "TIMEZONE": "<IANA tz, e.g. America/Sao_Paulo>",
        "PREFER_DATES_FROM": "future",
        "TO_TIMEZONE": "UTC",
    },
)
due_ms = int(parsed.timestamp() * 1000)   # ClickUp expects Unix ms
```

No `dateparser` available → convert manually or omit `due_date` rather than
guessing.

---

## Mapping `.docs/tasks/` ↔ ClickUp

Creating a ClickUp task from a local `.docs/tasks/NNNN-*.md`:

1. Read the file's YAML frontmatter.
2. Map `status`, `priority`, `type`, `author` to ClickUp fields.
3. Use the file's body as the task `description` (§Task schema).
4. After creation: write `clickup_id: <id>` back into the file's frontmatter.

Reading a ClickUp task back into the local file:

1. `GET /task/{task_id}`.
2. Extract `status`, `assignees`, `due_date`, comments.
3. Update frontmatter and matching sections in the `.md` file.

---

## Error handling

| Code | Meaning | Action |
|---|---|---|
| `400` | Invalid payload | Check required fields and IDs |
| `401` | Invalid/expired token | Check `CLICKUP_API_KEY`; never commit a new value |
| `403` | No permission on list | Confirm the token's account has access |
| `404` | Task/List/Space doesn't exist | Re-run discovery — the ID may have changed |
| `429` | Rate limit hit | Honor `Retry-After`; backoff |
| `500` | ClickUp-side error | Retry with exponential backoff (max 3x) |

---

## Example: create a task from a local doc

```bash
# 1. Discover the active sprint list
GET /team/$CLICKUP_WORKSPACE_ID/space → pick the relevant space
GET /space/{space_id}/folder → pick the relevant folder
GET /folder/{folder_id}/list → pick the most recent list

# 2. Discover custom fields
GET /list/{list_id}/field → cache {field_name: field_id}

# 3. Discover available statuses
GET /list/{list_id} → read the "statuses" array

# 4. Resolve assignee (if a name was mentioned)
GET /list/{list_id}/member → fuzzy match

# 5. Create
POST /list/{list_id}/task
{
  "name": "<title>",
  "description": "<body>",
  "status": "<name discovered in #3>",
  "assignees": [<id resolved in #4>],
  "priority": 3
}
# → store the returned task_id in the local file's frontmatter
```

---

## Hard rules

- **Never hardcode** workspace/space/list/user IDs in this file or in callers — discover or read from env.
- **`CLICKUP_API_KEY` never committed.** Check before `git add`.
- **No `Bearer` prefix** on the `Authorization` header.
- **Rate limit is real** — 90 req/min ceiling in batch/loop contexts.
- Suspected token exposure → rotate it in ClickUp's integration settings; don't just remove it from the file.

## Skills consumed / produced

- Consumed by: [[grill-me]] (modes 2/3), [[notifier]] (ClickUp channel), [[clickup-grounding]], [[clickup-audit]], [[whatsapp-clickup]].
- Upstream: none — this is the base adapter.
