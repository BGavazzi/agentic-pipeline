---
name: grill-me
description: Interview the user (or a task author) relentlessly about a plan or design until reaching shared understanding, resolving each branch of the decision tree. Picks a Product/Design variant or a Developer variant depending on who's being grilled. Mode 1 (interactive) works out of the box. Modes 2/3 (per-task, poll) require CLICKUP_API_KEY + CLICKUP_SPACE_ID. Use when user mentions "grill me", wants to stress-test a plan, or asks Claude to interrogate a new task.
tools: Bash, Read, Glob, Grep, WebFetch
---

# /grill-me — Relentless Plan & Design Interview

Interview the target relentlessly about every aspect of a plan, design, or
new ClickUp task until shared understanding is reached. Walk down each
branch of the decision tree, resolving dependencies between decisions one
at a time.

**Two variants:**
- **PO/Designer variant** — product, UX, user value, scope, acceptance.
- **Developer variant** — architecture, data, integration, failure, ops.

**Hard rule on wall-of-text:** **max 5 questions per variant per turn.**
For single-variant authors that's a flat 5; for dual-role authors
(`dev` + `po`/`designer`) it's 5 + 5 = 10 in one comment, split into
two clearly labelled sections. Hold the rest in your head, surface
them only after the target answers. Each question must include your
recommended answer.

---

## Modes

The skill operates in three modes. Pick based on the invocation.

### 1. Interactive mode — `/grill-me` (no args)

The classic mode. The current Claude Code user wants to be grilled on
the current plan/design under discussion. Behave as follows:

1. Read the conversation context — what is the plan being stress-tested?
2. If unclear, ask once: "What plan should I grill you on?"
3. Pick the variant:
   - Default to **Developer** if the conversation involves code, files,
     APIs, schemas, infra.
   - Use **PO/Designer** if it's about a feature concept, user flow,
     scope, prioritisation, KPI.
   - If genuinely mixed, ask: "Grill you as PO/designer or dev?"
4. Produce **5 questions** following the variant's framework, each with
   your recommended answer.
5. Wait for the user to respond before producing the next 5.
6. If a question can be answered by exploring the codebase, **explore
   the codebase instead** — don't ask what you can verify.

### 2. Per-task mode — `/grill-me <clickup_task_id>`

**Preconditions:** `CLICKUP_API_KEY` and `CLICKUP_SPACE_ID` must be set. If absent, print setup instructions and exit — don't attempt API calls.

Grill the author of a specific ClickUp task by posting comments on it.

1. `GET /task/{task_id}` — fetch task name, description, author (`creator`).
2. Look up the author's `roles` array in `member-roles.json` (next to this file):
   - contains `skip` → **STOP** — author is opted out, no grill
   - contains `dev` **AND** (`po` or `designer`) → **Both variants** (5 PO + 5 dev questions in one comment)
   - contains `po` or `designer` (no `dev`) → **PO/Designer variant** (5 questions)
   - contains `dev` only → **Developer variant** (5 questions)
   - missing entirely → don't post, tell the maintainer locally
3. If `creator.id == CLICKUP_BOT_USER_ID` (the bot) → **STOP**. The
   bot does not grill itself. Print "Skipping — bot-authored task" and
   exit.
4. Generate the right number of questions per the variant rule:
   - single variant → **5 questions**
   - dual-role (dev + po/designer) → **5 PO + 5 dev = 10 questions**,
     each question with recommended answer.
5. **Auto-post** as a single ClickUp comment on the task (per user
   decision in design 2026-05-11). Format depends on variant count.

   **Single-variant format:**

   ```
   🔍 Grilled by Claude (variant: <po-designer|dev>)

   Read your task, here are the 5 things I'd nail down before this moves to in-progress. Each comes with my recommended answer — push back if you disagree.

   **1. <question>**
   Recommended: <answer>

   ... etc through 5 ...

   Reply on this thread when you've thought through these — I'll come back with the next branch if needed.
   ```

   **Dual-variant format (dev + po/designer):**

   ```
   🔍 Grilled by Claude (dual-variant: dev + po/designer)

   Read your task, here are 10 things I'd nail down — five from the product/design lens, five from the engineering lens. Each comes with my recommended answer; push back if you disagree.

   ## Product / Design lens

   **P1. <question>**
   Recommended: <answer>

   ... etc through P5 ...

   ## Engineering lens

   **E1. <question>**
   Recommended: <answer>

   ... etc through E5 ...

   Reply on this thread when you've thought through these — I'll come back with the next branch if needed.
   ```

6. After posting: print the task URL and the questions to the local
   session so the human user can audit what went out.
7. **Update the local cache** at
   `~/.claude/skills/grill-me/state/grilled-tasks.json`. Append:
   ```json
   "<task_id>": {
     "task_name": "<name>",
     "task_url": "https://app.clickup.com/t/<task_id>",
     "creator_id": "<creator_id>",
     "creator_name": "<creator_username>",
     "variant": "<dev|po-designer|dual>",
     "grilled_at_ms": <now_ms>,
     "comment_id": "<posted_comment_id>",
     "last_reply_seen_ms": <now_ms>
   }
   ```
   **This file is a cache, not source of truth.** ClickUp comments are
   the authoritative record of what was grilled and what was replied.
   The JSON exists only to make Phase B cheaper (skip ClickUp re-query
   for tasks we already know about) and to remember
   `last_reply_seen_ms` between ticks. **Deletable any time without
   data loss** — Phase B's next tick will re-derive active grills
   from ClickUp's `date_updated_gt` scan.

### 3. Poll mode — `/grill-me poll` (or wired to a cron)

**Preconditions:** `CLICKUP_API_KEY`, `CLICKUP_SPACE_ID`, and `CLICKUP_BOT_USER_ID` must be set. If absent, print setup instructions and exit.

Scan the configured space (`$CLICKUP_SPACE_ID`) for newly created tasks **and** surface new replies on previously-grilled tasks. Two phases per tick.

#### Phase A — scan new tasks

1. Compute window: tasks created in the last N minutes (default 15,
   override with `/grill-me poll <minutes>`).
2. `GET /team/$CLICKUP_WORKSPACE_ID/task?space_ids[]=$CLICKUP_SPACE_ID&date_created_gt=<unix_ms>&order_by=created&reverse=true&include_closed=false`
3. For each task in the response:
   - Skip if `creator.id == CLICKUP_BOT_USER_ID`.
   - Skip if the bot has already commented on it
     (`GET /task/{id}/comment` → look for `user.id == CLICKUP_BOT_USER_ID`).
   - Otherwise run **per-task mode** on the task (which also writes
     state via step 7 of that mode).
4. Pace yourself: `sleep 0.7s` between API calls (rate limit hygiene).
5. Print a one-line summary per task: `<task_id> | <author_name> | grilled | <variant>` or `skipped (<reason>)`.

#### Phase B — scan replies on grilled tasks

After Phase A completes, find tasks with new replies (non-bot comments
since the bot's last reaction). ClickUp is the source of truth; the
JSON cache is only used to remember `last_reply_seen_ms` between ticks.

1. **Hydrate active-grills set from ClickUp.**
   - Load `~/.claude/skills/grill-me/state/grilled-tasks.json` (may
     be missing/empty — fine, treat as `{}`).
   - Run `GET /team/$CLICKUP_WORKSPACE_ID/task?space_ids[]=$CLICKUP_SPACE_ID&date_updated_gt=<now - N min>&include_closed=false`
     to discover tasks with activity in the window.
   - For each task in the response **not already in cache**: fetch
     `GET /task/{id}/comment`; if any comment has
     `user.id == CLICKUP_BOT_USER_ID`, treat as a grilled task and
     hydrate a cache entry with `last_reply_seen_ms = max(bot_comment_dates)`.
2. **For each task in the (now hydrated) cache:**
   - `GET /task/{task_id}/comment` (sleep 0.7s before next).
   - Filter: comments where `user.id != CLICKUP_BOT_USER_ID` AND
     `int(date) > cache[task_id].last_reply_seen_ms`.
   - For each new reply, print to local session:
     ```
     🗨️  Reply on <task_id> | <user.username> @ <HH:MM>
     > "<comment_text first 200 chars, single-line>"
        <task_url>
     ```
   - **Post a follow-up on the ClickUp thread** (don't be silent —
     surfacing locally is not enough; the author posted publicly and
     expects a public response). **Default is next-branch grill** —
     the skill is `grill relentlessly`, not `agree and close`. Decide:
     - **Next-branch grill (DEFAULT)** — drill into what the reply
       opened. Up to 5 fresh questions per variant (5+5 for dual),
       scoped to the new ground the reply exposed. Don't restart the
       framework from scratch; pick the branches the human's answers
       made load-bearing. This is the bot's normal continuation
       behavior on reply.
     - **Close-out** ONLY if the human explicitly signals "stop" /
       "deu", "fechei", "chega", "passa". Vague convergence like
       "passou no 1o teste" is NOT a close signal — it's an invitation
       to round 2. When in doubt, next-branch.
     - **Apology/correction** if the bot's previous comment was wrong
       (per safety rule #5 — no DELETE, post correction instead).
     Why default to next-branch: premature close-out after the user's
     first reply felt like the bot wasn't actually engaging. The
     original /grill-me prompt commits to `interview me relentlessly`;
     honor that until told to stop.
     The follow-up itself counts as a bot comment, so it bumps
     `last_reply_seen_ms` correctly on the next state save.
   - Update `cache[task_id].last_reply_seen_ms` to the max `date` seen
     across **all** comments on that task — including the bot's own
     follow-up just posted. Prevents re-surfacing on the next tick.
3. **Garbage-collect** the cache: drop entries for tasks ClickUp says
   are closed/archived, or where no activity has happened for >30
   days. Cache stays small.
4. Save the JSON cache. Print one-line summary:
   `replies: <N_new> across <M_active> grilled tasks (<H> newly hydrated)`.

If the JSON cache is wiped, the next tick re-discovers grilled tasks
via the bot-commented filter in step 1 — `last_reply_seen_ms` resets
to the bot's most recent comment date, so previously-surfaced replies
will re-surface once. Acceptable; no data corruption.

#### State file lifecycle

| Field | Set when | Used by |
|---|---|---|
| `task_name`, `task_url`, `creator_*`, `variant`, `comment_id` | per-task mode step 7 (right after POST) | audit / display only |
| `grilled_at_ms` | per-task mode step 7 | initial value for `last_reply_seen_ms` |
| `last_reply_seen_ms` | Phase B end of each tick | filters which replies are "new" |

The state file is **never** committed to guidelines_IA — it lives
only in `~/.claude/skills/grill-me/state/` (user-global). Delete it
to reset the reply scan to "everything is new again".

#### Why no explicit watcher add?

ClickUp auto-adds the bot as a watcher on any task where it comments.
No separate `POST /watcher` call needed. The bot's ClickUp inbox
aggregates activity on all grilled tasks "for free" — maintainers can
also monitor via web (log in as the bot account) instead of only the terminal.

---

## PO / Designer Variant — Question Framework

When grilling a PO or designer, draw from these branches. Pick the 5
most load-bearing for the specific task; don't ask all of them.

### A. User & Value
- Who exactly is the user of this? (role, context, frequency of use)
- What's the user's current workaround? Why is *that* not enough?
- What measurable thing improves when we ship this? (KPI, north-star metric, qualitative signal)
- What does "done" look like from the user's POV — not from a code/PR perspective?
- If we don't build this, who notices and what do they do?

### B. Scope & Boundaries
- What's explicitly **out of scope** for this iteration?
- What's the smallest thing we could ship that still moves the metric?
- Which existing flow does this replace, augment, or sit beside?
- What does the "v2" of this look like — and why is it not v1?

### C. Acceptance & Edge Cases
- What's the acceptance test a non-engineer can run? (click X, see Y)
- What happens on the unhappy path: empty state, error, slow network, offline, permission denied?
- What's the worst plausible user input you've imagined for this?
- What changes for power users vs. first-time users?

### D. Dependencies & Cross-team
- Who else needs to know this is shipping? (CM, dev, design, ops, legal, CEO)
- Is there a content/copy dependency? Translation? Asset?
- Is there a data dependency — does this need data that doesn't exist yet?
- Does shipping this affect ongoing work in another epic?

### E. Prioritisation
- Why is this the next thing, not <other-thing-in-backlog>?
- What's the deadline and what drives it? (external event, board, demo)
- If we have to cut, what's the first thing to drop?

---

## Developer Variant — Question Framework

When grilling a developer, draw from these branches. Pick the 5 most
load-bearing for the specific task; don't ask all of them.

### A. Architecture & Boundaries
- What module/bounded context owns this? Why there and not elsewhere?
- What's the public contract (HTTP route, event, function signature) and what's internal?
- Does this introduce a new `Dxx` decision in `SDD_KIT.md`? Which?
- What pattern in the codebase are you mirroring? (point to file:line)

### B. Data & State
- What's the data model — fields, types, nullability, indexes?
- Where is this data stored? Migrations? Backfill needed?
- What's the invariant this code must preserve? What enforces it?
- Read-after-write consistency: does this need it? How will you guarantee it?

### C. Integration & Failure
- What external systems does this call? (DB, ClickUp, backend API, GCS, …)
- What's the timeout, retry, and backoff policy? Idempotency key?
- What happens if the external call fails halfway? Rollback or replay?
- What's the blast radius if this misbehaves in prod?

### D. Performance & Cost
- What's the expected request volume / size / latency?
- What's the most expensive line in this code path?
- Cache strategy: what's cacheable, TTL, invalidation trigger?
- LLM cost (if relevant): which model, how many tokens/call, batchable?

### E. Testing, Observability, Rollback
- What's the test pyramid for this — unit / integration / e2e?
- What logs/metrics will let you debug this at 2am?
- How do you roll this back if it breaks prod? Feature flag? Migration reversible?
- What's the smallest deployable slice — can it ship behind a flag dark first?

### F. Security & Compliance
- What user input touches this? Sanitisation? Authorisation check?
- Any secrets involved? Where do they live? Rotated how?
- PII / privacy-regulation-sensitive fields touched (GDPR, LGPD, CCPA, etc.)? Logged? Where?

---

## How to phrase the recommended answer

For each question, give a **single concrete recommendation**, not a menu.
A grill answer like "could be X or Y, depends" is worthless — it just
pushes the work back. Pattern:

> **Q:** What's the data model for the new "tag" field?
> **Recommended:** `tag: { id: uuid, name: string (≤32), createdAt: timestamp }`, stored on `events.tags[]` as an embedded array (not a separate table) since cardinality is low (<10 per event). Index on `events.tags.name` for filtering.

The author can push back ("no, we need a separate table because…") — and
that pushback is where the design gets sharper.

---

## Determining role from author ID

Read `member-roles.json` (sibling of this file). Schema:

```json
{
  "<user-id>":  { "name": "PO Name",    "roles": ["po"] },
  "<user-id>":  { "name": "Designer",   "roles": ["po", "designer"] },
  "<bot-id>":   { "name": "Bot Name",   "roles": ["skip"] }
}
```

Allowed values inside `roles[]`: `po`, `designer`, `dev`, `skip`.

Variant selection:
1. If `roles` contains `skip` → **don't grill**, exit silently.
2. Else if `roles` contains `dev` AND (`po` or `designer`) → **Both
   variants** (5 PO/designer + 5 dev questions in one comment, two sections).
3. Else if `roles` contains `po` or `designer` → **PO/Designer variant**.
4. Else if `roles` contains `dev` → **Developer variant**.
5. Else (unknown roles or empty array) → ask the maintainer.

If an author isn't in the map at all, **don't post**. Print to local
session: "author <id> <name> not in role map — please update
member-roles.json".

---

## ClickUp adapter (modes 2 and 3 only)

Required env vars:

| Var | Purpose |
|---|---|
| `CLICKUP_API_KEY` | Personal or bot token — gate for modes 2/3 |
| `CLICKUP_WORKSPACE_ID` | Team ID (numeric); find via `GET /v2/team` |
| `CLICKUP_SPACE_ID` | Space to poll for new tasks |
| `CLICKUP_BOT_USER_ID` | Bot's ClickUp user ID — **never grill the bot** |

Auth, rate limit, and comment endpoint patterns: see `../clickup-api/SKILL.md` if the skill is present. The 0.7s poll pacing enforces ClickUp's 100 req/min limit.

**Mode 1 (interactive) does not need any of these.**

---

## Language & tone

**Match the language of the task/plan being grilled.** Default: English.

- Task written in English → respond in English.
- Task written in another language → match it.
- Mixed or unclear → use English.

Configure a default with the `GRILL_LANGUAGE` env var (e.g. `pt-BR`, `en`, `es`). If set, use it as the default when language is ambiguous.

Register: **direct and casual, not slangy.** Contractions OK. One emoji max (the `🔍` header). No memes, no excessive punctuation.

**PT-BR style reference** (for teams that use Brazilian Portuguese):

| Avoid (EU-PT) | Use (BR-PT) |
|---|---|
| `tu` / `tuas` | `você` / `suas` |
| `fora de scope` | `fora de escopo` |
| `actual` / `actualizar` | `atual` / `atualizar` |
| `tens / és / fazes` | `tem / é / faz` |

---

## Safety rules

These hold even though the user opted in to auto-posting:

1. **Never grill the bot itself** — `creator.id == $CLICKUP_BOT_USER_ID` is a hard skip.
2. **Never post twice on the same task** — check existing comments for any from `CLICKUP_BOT_USER_ID` first.
3. **Never post if the role map is missing the author** — log locally and skip.
4. **Never post a question whose recommended answer is "it depends"** — refine until you have a concrete recommendation.
5. **Always print the posted content back to local session** so the maintainer can audit. **No DELETE in unattended mode** — if the bot writes something wrong, post a *correction/apology comment* on the same task instead of silently deleting. The bot's DELETE/PUT token authority is reserved for maintainer-supervised manual fixes, not for autonomous self-correction. Why: public apology > silent rewrite — silently deleting destroys the thread context and trust.
6. **Respect closed/archived tasks** — `include_closed=false` in poll queries; skip tasks already in done states.

---

## Example: invocation walkthrough

```bash
# User is in Claude Code, mentions a half-baked plan:
> /grill-me
Claude: [picks dev variant, asks 5 architecture/data/failure questions
         with recommendations]

# Cron tick fires, calls /grill-me poll (requires CLICKUP_* env vars):
> /grill-me poll 15
Claude: [scans $CLICKUP_SPACE_ID, finds task abc123 by <team-member>, looks up roles=[po],
         generates 5 product questions, posts comment, prints URL]
Claude: abc123 | Product Owner | grilled | po-designer
Claude: def456 | Bot User    | skipped (bot author)
Claude: ghi789 | <team-member> | skipped (role=skip)
Claude: jkl012 | <team-member> | skipped (already grilled)
```

---

## Wiring it on a schedule

### v1 — local /loop (current)

Run inside a long-lived Claude Code session:

```
/loop 15m /grill-me poll 15
```

The session must stay open for the loop to keep firing. Pause with the
loop skill's stop control. This is the v1 cadence — try it on real
tasks for a week before promoting to a remote routine.

### v2 — remote /schedule routine (when local proves out)

When ready to lift off the local Claude Code window:

1. Use the `schedule` skill to create a routine on cron (e.g. `*/15 * * * *`).
2. The routine prompt should be a self-contained version of the **Poll
   mode** logic above — embed `$CLICKUP_SPACE_ID`, `$CLICKUP_BOT_USER_ID`,
   and the role map inline (since the remote agent won't read this file from disk).
3. Wire `CLICKUP_API_KEY` into the routine's environment — never inline
   the value in the prompt.
4. **Audit log: deferred for v1.** Local stdout (Claude Code terminal)
   is sufficient audit until v2 is wired. When wiring v2, decide then
   whether to add an audit task in All Blue / Documentação or a
   different channel — don't pre-build it.
5. Keep this local skill file as the **canonical grill prompt** — the
   remote routine reads from it (via raw GitHub URL) on each tick so
   variant frameworks don't drift.

Both paths share the same skill body, role map, and safety rules. The
only divergence is the *trigger*: local `/loop` vs. remote cron.

---

## Pointers

- `member-roles.json` — sibling of this file, role map. Edit when team changes. Keys are ClickUp user IDs (modes 2/3 only; mode 1 ignores this file).
- `state/grilled-tasks.json` — runtime state for Phase B reply scan. Lives **only** in `~/.claude/skills/grill-me/state/` (user-global, gitignored). Schema documented in mode 3 Phase B.
- `../clickup-api/SKILL.md` — ClickUp API reference (optional; only needed for modes 2/3).
- Required env vars for modes 2/3: `CLICKUP_API_KEY`, `CLICKUP_WORKSPACE_ID`, `CLICKUP_SPACE_ID`, `CLICKUP_BOT_USER_ID`.
- Optional: `GRILL_LANGUAGE` — default language when task language is ambiguous (e.g. `en`, `pt-BR`).
