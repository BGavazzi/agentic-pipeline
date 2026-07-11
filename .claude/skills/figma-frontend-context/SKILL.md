---
name: figma-frontend-context
description: Turns a Figma design reference (a frame URL, or a "sticky note" comment marking a frame as ready-to-build) into a structured JSON brief — target frame's children/components, summary of intent, and a first-pass implementation hint. Trigger when the user pastes a Figma URL/sticky and wants it turned into something codebase-grounding or a builder can act on, or says "turn this Figma frame into a brief". Requires FIGMA_API_KEY. Output feeds codebase-grounding.
tools: Bash, WebFetch, Read, Write
---

# Figma Frontend Context

Reads a Figma frame (directly, or via a "sticky note" comment that marks a
frame as ready-to-build) and produces a structured JSON brief describing
what needs to be built — without touching a target repo. Pair with
[[codebase-grounding]] next to map the brief onto actual code.

**Output contract:**

```json
{
  "meta": { "file_key": "string", "node_id": "string", "figma_url": "string", "fetched_at": "ISO8601" },
  "source": { "kind": "frame | sticky", "sticky_id": "string | null", "sticky_text": "string | null" },
  "summary": "1-3 sentence plain-language description of what the frame shows",
  "target_children": [
    { "name": "string", "type": "FRAME | INSTANCE | TEXT | ...", "figma_id": "string" }
  ],
  "implementation": { "what_to_build": "string", "notes": "string | null" }
}
```

Auth/discovery/export patterns: [[figma-api]].

---

## Precondition

`FIGMA_API_KEY` must be set. Absent → print setup instructions, exit.

---

## Modes

### 1. Direct frame mode

Input: a Figma URL with a `node-id`.

```
1. Parse file_key + node_id from the URL (see figma-api §Parsing a Figma URL).
2. GET /files/{file_key}/nodes?ids={node_id} → full node tree.
3. Proceed to §Workflow.
```

### 2. Sticky mode

Input: a Figma comment ("sticky") marking a frame as ready — the comment's
`client_meta` anchors it to a node, or its text names a frame.

```
1. GET /files/{file_key}/comments → find the sticky by ID or by matching text.
2. Resolve the anchored node_id from client_meta.node_id (if present);
   else treat the sticky's text as a search hint and locate the nearest
   named frame ancestor (walk up client_meta position → containing frame).
3. GET /files/{file_key}/nodes?ids={resolved_node_id} → full node tree.
4. Carry sticky_id + sticky_text into `source` for traceability.
5. Proceed to §Workflow.
```

If a sticky can't be resolved to a node with reasonable confidence → ask the
user for the direct frame URL instead of guessing.

---

## Workflow

### Step 1 — Extract target children

Walk the node tree; for each direct child of the target frame (and any
nested `INSTANCE` of a shared component), record `name`, `type`, `figma_id`.
Strip cosmetic version suffixes when they're clearly not semantic (e.g. a
name like `Button v2` still maps to a `Button` concept — leave the raw
`name` in the record; let `codebase-grounding` do the fuzzy match against
real code).

### Step 2 — Summarize intent

Produce a 1-3 sentence plain-language `summary` of what the frame
represents (a page, a modal, a component variant) — enough for a human or
`codebase-grounding` to orient without opening Figma.

### Step 3 — Extract copy/text content

Collect all `TEXT` node contents verbatim (for later i18n-key matching in
`codebase-grounding` Step 4). Include under `implementation.notes` if
non-trivial (e.g. more than a couple of short labels).

### Step 4 — Draft `what_to_build`

One paragraph: what a builder should implement, in terms of the target
children identified in Step 1 — not code, just intent ("a segmented control
above a list of cards, each card showing title + status badge").

### Step 5 — Export a reference image (optional but recommended)

```bash
GET /images/{file_key}?ids={node_id}&format=png&scale=2
```

Download it to `<cwd>/.docs/figma-refs/<node_id>.png` — this is what
[[visual-tester]] later diffs the built UI against. Note the path in
`implementation.notes` if exported.

### Step 6 — Write output

Write the JSON to `<cwd>/.docs/figma-briefs/<node_id>-<slug>.json` and print
it to the caller. This is the brief that feeds [[codebase-grounding]].

---

## When to stop and ask

- URL has no `node-id` and mode isn't sticky → ask for a frame-scoped link, don't operate on the whole file.
- Sticky can't be confidently resolved to a node → ask for the direct frame URL.
- Target frame has 0 children (empty frame) → tell the user, don't fabricate a brief.
- Frame is enormous (50+ direct children, e.g. a whole page of unrelated content) → ask the user to scope down to the actual component/section, rather than producing an unusably broad brief.

---

## What this skill does NOT do

- Does not read the target codebase — that's [[codebase-grounding]], invoked next.
- Does not write implementation code — that's [[implement-figma-task]] / [[builder]].
- Does not decide component naming in code — surfaces Figma names as-is.

## Hard rules

- **Read-only against Figma** — no comment posted, no node modified, unless the caller explicitly asks for a comment reply (out of scope for this skill; see [[figma-api]] directly).
- **Never fabricate `target_children`** — only what's actually in the node tree.
- **Image export is best-effort** — a failed export doesn't block producing the JSON brief; note the failure in `implementation.notes`.

## Failure modes

| Error | What to do |
|---|---|
| `FIGMA_API_KEY` absent | Print setup instructions, exit |
| URL unparseable | Ask the user for a valid Figma frame URL |
| Sticky text ambiguous (matches 2+ frames) | Ask which one |
| Node tree fetch 404 | Node was deleted/renamed — tell the user |
| Image export fails | Continue without it; note in `implementation.notes` |

## Skills consumed / produced

- Reuses: [[figma-api]] for auth/fetch/export.
- Downstream: [[codebase-grounding]] (repo context), then [[implement-figma-task]] or [[builder]].
- Produces reference images consumed by: [[visual-tester]] (figma-mode diff).
