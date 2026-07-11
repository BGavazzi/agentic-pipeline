---
name: figma-api
description: Generic Figma REST API integration — auth, rate limiting, node/file fetching, image export, and comment posting. Use when the user gives a Figma file/frame URL and wants its structure read, an image exported, or a comment posted. BYO credentials — no team/project baked in. STATUS - reference skill (auth + endpoints), consumed by figma-frontend-context/implement-figma-task/visual-tester.
tools: Bash, WebFetch, Read
---

# Figma API

Generic Figma REST API reference. No team, project, or file is hardcoded —
every file/node key comes from the URL the user provides or from discovery
calls. `figma-frontend-context`, `implement-figma-task`, and `visual-tester`
treat this file as the shared auth/rate-limit/endpoint reference.

---

## When to Use

- User pastes a Figma URL (file, frame, or a sticky/comment) and wants its structure or content
- Need to export a frame/component as an image (PNG/SVG) for a visual diff
- Need to read/post a Figma comment (e.g. a design-review sticky note workflow)
- Any operation where the user says "Figma", "design", "frame", "sticky", "mockup"

---

## Auth & Setup

### Environment variables

| Variable | Purpose |
|---|---|
| `FIGMA_API_KEY` | Personal access token. Header: `X-Figma-Token: <token>` |

Read from the process environment only. Never echo the token into logs,
commits, or comments.

### Required header

```
X-Figma-Token: <FIGMA_API_KEY>
```

---

## Rate Limiting

Figma's limits are tiered by endpoint and not published as a single flat
number — treat any `429` as authoritative and back off (honor `Retry-After`
if present, else exponential backoff starting at 2s, max 3 retries). For
batch operations (e.g. exporting many nodes), pace calls at roughly 1/s
unless a tighter documented limit applies to that endpoint.

---

## Base URL

```
https://api.figma.com/v1
```

---

## Parsing a Figma URL

A shared Figma URL looks like:

```
https://www.figma.com/design/<file_key>/<file_name>?node-id=<node_id>
```

Extract:
- `file_key` — the path segment after `/design/` (or `/file/` on older URLs)
- `node_id` — the `node-id` query param, with `-` replaced by `:` for API calls (`12345-6789` → `12345:6789`)

---

## Core operations

### Fetch file structure

```bash
GET /files/{file_key}
# Full document tree — can be large; prefer the node-scoped call below when
# you already have a node_id.
```

### Fetch specific nodes

```bash
GET /files/{file_key}/nodes?ids=<node_id_1>,<node_id_2>
```

Returns each node's full tree (children, layout, styles, text content) —
this is the primary call for reading a frame/component's structure.

### Export an image

```bash
GET /images/{file_key}?ids=<node_id>&format=png&scale=2
# → { "images": { "<node_id>": "<temporary S3 URL>" } }
```

The returned URL is temporary (expires) — download it immediately if it
needs to persist:

```bash
curl -o <local_path>.png "<temporary S3 URL>"
```

`format` can be `png`, `svg`, `pdf`, `jpg`. Use `svg` for icons/vectors you
intend to re-implement as code, `png` for perceptual/visual diffing.

### Read comments (stickies)

```bash
GET /files/{file_key}/comments
```

Each comment has `message`, `client_meta` (position, often anchored to a
node), `user`, `created_at`. A "sticky note" design-review workflow treats
each top-level comment as one unit of work.

### Post a comment

```bash
POST /files/{file_key}/comments
{
  "message": "<text>",
  "client_meta": { "node_id": "<node_id>" }   # optional — anchors the reply
}
```

### File/team/project discovery (when file_key isn't known yet)

```bash
GET /teams/{team_id}/projects
GET /projects/{project_id}/files
```

Only needed when the user references a project/team by name rather than a
direct file URL.

---

## Error handling

| Code | Meaning | Action |
|---|---|---|
| `400` | Invalid node IDs / malformed request | Check the extracted `file_key`/`node_id` |
| `403` | Token lacks access to this file | Confirm the file is shared with the token's account |
| `404` | File/node doesn't exist | Re-check the URL; node may have been deleted/renamed |
| `429` | Rate limit hit | Honor `Retry-After`; backoff |
| `5xx` | Figma-side error | Retry with backoff (max 3x) |

---

## Hard rules

- **Never hardcode** `file_key`/`node_id`/`team_id` in this file — always derived from user input or discovery.
- **`FIGMA_API_KEY` never committed.** Check before `git add`.
- **Downloaded image URLs are temporary** — persist locally immediately if needed beyond the current step.
- **Large files**: prefer `nodes?ids=` over the full `/files/{key}` tree whenever a specific frame is already known — the full tree can be tens of MB on large design files.

## Skills consumed / produced

- Consumed by: [[figma-frontend-context]], [[implement-figma-task]], [[visual-tester]] (figma-mode diffing).
- Upstream: none — base adapter.
