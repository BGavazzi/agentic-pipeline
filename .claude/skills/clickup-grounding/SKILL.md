---
name: clickup-grounding
description: Enriches a brief (a ClickUp task ID, or a JSON/markdown brief that references one) with ClickUp-specific context — the list's schema (statuses, custom fields, members), the task's own frontmatter-equivalent fields, comment history, and any linked/blocking tasks — before the brief reaches codebase-grounding or builder. Trigger when the user gives a ClickUp task ID/URL and wants it turned into actionable local context, or says "ground this ClickUp task", "pull the ClickUp context first". Requires CLICKUP_API_KEY (+ CLICKUP_WORKSPACE_ID). Output is the input unchanged, with a clickup_context block appended.
tools: Bash, WebFetch, Read
---

# ClickUp Grounding

**Do NOT confuse with [[codebase-grounding]]** (repo context) or
[[clickup-audit]] (workspace-wide health check). This grounds **one task**
against **ClickUp's own state** — it doesn't touch a target repo at all.

**Output contract:** the input unchanged, with a new top-level key
`clickup_context`.

---

## Precondition

`CLICKUP_API_KEY` must be set (and `CLICKUP_WORKSPACE_ID` for cross-list
lookups). If absent → print setup instructions and exit; don't attempt API
calls. Auth/rate-limit/discovery patterns: [[clickup-api]].

---

## Input

Either:
- a bare `task_id` (or a `https://app.clickup.com/t/<id>` URL — extract the ID), or
- a JSON/markdown brief that contains a `clickup_id` field somewhere.

---

## Workflow

### Step 1 — Fetch the task

```bash
GET /task/{task_id}?include_subtasks=true
```

Capture: `name`, `description`, `status`, `priority`, `assignees`, `creator`,
`due_date`, `custom_fields`, `list_id`, `linked_tasks`, `dependencies`
(blocks/blocked_by).

### Step 2 — Fetch the list's schema

```bash
GET /list/{list_id}          # → available statuses (exact strings, order)
GET /list/{list_id}/field    # → custom field defs (id, name, type, options)
GET /list/{list_id}/member   # → who can be assigned
```

This is what lets a downstream skill (builder, grill-me) map local frontmatter
concepts (`status: todo`) to ClickUp's actual status vocabulary, which is
per-list and never assumed.

### Step 3 — Fetch comment history

```bash
GET /task/{task_id}/comment
```

Capture chronologically: `user.username`, `date`, `comment_text` (first
500 chars each — full history can be long; note truncation if it happens).
This is what lets grill-me's poll mode (or a human) see prior back-and-forth
without re-reading the whole thread.

### Step 4 — Resolve dependencies

For each ID in `linked_tasks` / `dependencies`:

```bash
GET /task/{linked_id}   # name + status only, not full context
```

Flag any `blocked_by` task whose status isn't in a "done"-equivalent state —
this is a hard blocker for downstream work.

### Step 5 — Assemble output

```json
{
  "...": "(input unchanged)",
  "clickup_context": {
    "task_id": "string",
    "name": "string",
    "status": "string (exact, per list vocabulary)",
    "priority": 1,
    "assignees": [{"id": "...", "username": "..."}],
    "creator": {"id": "...", "username": "..."},
    "due_date": "unix_ms | null",
    "custom_fields": [{"name": "...", "id": "...", "value": "..."}],
    "list_schema": {
      "statuses": ["to do", "in progress", "review", "done"],
      "members": [{"id": "...", "username": "..."}]
    },
    "comments": [{"user": "...", "date": "...", "text": "..."}],
    "blockers": [{"task_id": "...", "name": "...", "status": "...", "resolved": false}],
    "discovery_notes": ["any ambiguity — e.g. custom field with no obvious mapping"]
  }
}
```

---

## When to stop and ask

- `task_id` not resolvable (404) → tell the user, don't guess a different ID.
- `CLICKUP_API_KEY` absent → print setup instructions, exit (§Precondition).
- Task has an unresolved `blocked_by` → surface it prominently; don't silently continue as if the task were ready.
- Custom field value looks like it encodes structured data (JSON-in-a-string) the caller likely needs parsed → parse it, but flag the assumption in `discovery_notes`.

---

## What this skill does NOT do

- Does not modify the ClickUp task (read-only, same spirit as [[codebase-audit]]).
- Does not touch a target repo — pair with [[codebase-grounding]] for that.
- Does not decide task readiness/priority — surfaces facts, the caller (builder/dispatcher/human) decides.

## Hard rules

- **Read-only.** No `PUT`/`POST` calls in this skill.
- **Never invent a status string** — always the exact string from `GET /list/{list_id}`.
- **Rate limit hygiene** — same 90 req/min ceiling as [[clickup-api]]; this skill makes ~4-6 calls per invocation, well within budget for single-task use.

## Failure modes

| Error | What to do |
|---|---|
| `task_id` 404 | Tell the user; don't guess a nearby ID |
| `CLICKUP_API_KEY` absent | Print setup instructions, exit — no partial output |
| List has 0 custom fields | `custom_fields: []`, not an error |
| Comment history > 50 entries | Truncate to most recent 20 + oldest 5, note truncation in `discovery_notes` |
| Circular `linked_tasks` reference | Resolve each ID once, don't recurse |

## Skills consumed / produced

- Reuses: [[clickup-api]] for auth/discovery/rate-limit patterns.
- Downstream: [[codebase-grounding]] (repo context, if the task also targets code), [[builder]], [[grill-me]] (per-task mode already does its own lighter fetch; this skill is for when full context — comments + blockers + schema — is needed upfront).
