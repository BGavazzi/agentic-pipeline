---
name: whatsapp-clickup
description: Turns an inbound WhatsApp message (text, or transcribed voice note) into a ClickUp task — parses intent (create task / update status / add comment), resolves assignee and due-date hints, creates/updates via clickup-api, and replies on WhatsApp via zap-comms confirming what happened. Trigger when wiring a "message the bot, it makes a task" workflow, or when an inbound message has already been received and needs to be turned into ClickUp action. Requires both zap-comms and clickup-api's env vars.
tools: Bash, WebFetch, Read
---

# WhatsApp → ClickUp

Composes [[zap-comms]] (WhatsApp transport) and [[clickup-api]] (task CRUD)
into one flow: a person sends a message, a ClickUp task gets
created/updated, and they get a WhatsApp reply confirming it. This skill
owns the **intent parsing and composition**; it doesn't reimplement either
transport.

---

## Precondition

Both [[zap-comms]]'s env vars (`EVOLUTION_API_URL`, `EVOLUTION_API_KEY`,
`EVOLUTION_INSTANCE_NAME`) and [[clickup-api]]'s (`CLICKUP_API_KEY`,
`CLICKUP_LIST_ID` at minimum) must be set. Either missing → print setup
instructions for the missing half, exit.

---

## Input

An inbound message event (however it arrives — webhook payload, or a
transcript already produced upstream if the message was a voice note):

```json
{
  "from": "<E.164 number or JID>",
  "text": "string — already transcribed if it was voice",
  "message_id": "string",
  "received_at": "ISO8601"
}
```

Voice-note transcription itself is out of scope for this skill — assume
`text` is already plain language by the time it reaches here (wire a
transcription step, e.g. Whisper, upstream if the source is audio).

---

## Workflow

### Step 1 — Classify intent

From `text`, determine one of:
- `create_task` — default when nothing else matches; most inbound messages are "make a note of this"
- `update_status` — text references an existing task by name/number and a target status ("mark X as done", "move Y to review")
- `add_comment` — text references an existing task and reads as a note/update rather than a new item or a status change
- `unclear` — can't confidently classify

`unclear` → reply on WhatsApp asking for clarification (§Step 5), don't guess.

### Step 2 — Extract fields

For `create_task`:
- `title` — the core ask, cleaned of filler words
- `assignee_hint` — a name mentioned, or none (defaults to the sender if the workspace maps phone numbers to ClickUp users — that mapping is a caller-supplied table, not invented here)
- `due_date_hint` — a natural-language date expression, if present
- `priority_hint` — urgency language ("urgent", "when you get a chance") mapped to ClickUp's 1-4 scale; default `3` (normal) if nothing suggests otherwise

For `update_status` / `add_comment`:
- `target_task_hint` — name/number fragment to search for via [[clickup-api]]'s search endpoint
- `target_status` (update_status only) or `comment_text` (add_comment only)

### Step 3 — Resolve against ClickUp

- `create_task`: resolve `assignee_hint` via [[clickup-api]]'s fuzzy-match pattern; parse `due_date_hint` via its due-date parsing pattern; then `POST /list/{list_id}/task`.
- `update_status` / `add_comment`: search via `GET /team/{workspace_id}/task?query=<target_task_hint>`. Zero matches → §Step 5 asks for clarification. Multiple matches → reply listing the candidates, ask which one (don't guess the first result).

### Step 4 — Write back to the sender's context

If the sender's phone number maps to a known ClickUp user (a table the
deploying team maintains, not invented by this skill), set them as
`assignees` on a newly created task by default — unless `assignee_hint`
named someone else. Absent a mapping, leave `assignees` empty and note it
in the WhatsApp reply.

### Step 5 — Reply on WhatsApp

Via [[zap-comms]] `sendText`, confirm what happened:

```
✅ Created: "<title>"
<clickup task URL>
Assignee: <resolved name | unassigned>
Due: <resolved date | none>
```

Or for `unclear`/ambiguous matches:

```
Not sure what you meant — could you clarify?
(Did you want to create a task, or update "<best-guess existing task>"?)
```

---

## Hard rules

- **Never guess an ambiguous match** — multiple candidate tasks or unclear intent always gets a clarifying reply, never a best-effort pick.
- **Never invent a phone→ClickUp-user mapping** — that table is the deploying team's to build and maintain; this skill consumes it if present, doesn't fabricate entries.
- **Confirm every write on WhatsApp** — a task created/updated with no reply back leaves the sender unsure it worked.
- **Rate limit hygiene** — inherits [[clickup-api]]'s 90 req/min ceiling; a single inbound message is 2-4 calls, not a concern at normal volume, but don't batch-process a backlog of messages without pacing.

## Failure modes

| Error | What to do |
|---|---|
| Both env halves absent | Print setup instructions for whichever is missing, exit |
| Intent `unclear` | Reply asking for clarification, don't create a task speculatively |
| `target_task_hint` matches 0 tasks | Reply "couldn't find a task matching that — could you give me more to go on?" |
| `target_task_hint` matches 2+ tasks | Reply listing candidates, ask which one |
| ClickUp create/update call fails (4xx/5xx) | Reply on WhatsApp that it failed — don't leave the sender thinking it worked when it didn't |
| Phone number has no ClickUp user mapping | Create unassigned, note it in the reply, don't block the task creation on it |

## Anti-patterns

- ❌ Creating a task on `unclear` intent "just in case."
- ❌ Picking the first search result silently when multiple tasks match.
- ❌ Silent failure — any ClickUp-side error must produce a WhatsApp reply saying so.
- ❌ Reimplementing WhatsApp send/receive here instead of calling [[zap-comms]].
- ❌ Reimplementing ClickUp auth/discovery here instead of calling [[clickup-api]].

## Skills consumed / produced

- Reuses: [[zap-comms]] (transport), [[clickup-api]] (task CRUD, assignee/due-date resolution).
- Upstream: whatever receives the inbound WhatsApp webhook and (if voice) transcribes it — outside this skill's scope.
- Downstream: none — this is a leaf flow, not part of the Builder/Tester pipeline.
