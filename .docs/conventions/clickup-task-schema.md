# ClickUp task schema — same shape whether an agent reads it from the repo or the API

> **Provenance note (migrated 2026-09).** Migrated from this repo's
> predecessor (`guidelines_IA`, tombstoned). This is a design proposal, not
> yet implemented as code here — `clickup-api`/`clickup-grounding`/
> `clickup-audit` exist as skills, but no `validate_task.py`-equivalent for
> ClickUp-side schema validation has been built. Kept as the spec for that
> future work. Scrubbed of one company-specific example value and a
> real task count.

The key piece for ClickUp automation: a **task description schema** that holds whether read from `.docs/tasks/NNNN-*.md` or via the ClickUp API — so an agent reading a task via the API has exactly the same fields as reading the local file.

This doc covers:

1. **Canonical schema** (structured markdown + ClickUp field mapping)
2. **JSON contract** (expected shape of `GET /v2/task/{id}` as parsed by an agent)
3. **Recommended custom fields** in ClickUp

---

## 1. Canonical schema

Every task, on either medium (markdown or ClickUp), has **8 sections**, fixed order:

| # | Section | Required | Content |
|---|---|:-:|---|
| 1 | **Frontmatter / Meta** | ✅ | YAML in the file, or custom fields in ClickUp |
| 2 | **Context** | ✅ | Why this task exists. References to other tasks, SDD, route map |
| 3 | **Problem** | ✅ | Precise technical description of what's wrong/missing |
| 4 | **What To Do** | ✅ | Actionable subtasks as `[ ]` checkboxes |
| 5 | **Affected Files** | ✅ | List of paths with role (main/test/doc) |
| 6 | **Exit Conditions** | ✅ | Verifiable criteria as `[ ]` (BDD given/when/then if useful) |
| 7 | **Implementation Notes** | ❌ | Hints, references to existing functions, links |
| 8 | **Required Documentation (Closure Law)** | ✅ | The Closure Law checklist |

**Golden rule**: if a field lives in one section, don't duplicate it in another. ClickUp `priority` is a native field — don't also write `Priority: P1` in the description.

This matches `.docs/tasks/000-template.md`'s structure in this repo already (§Context/§Problem/§What To Do/§Affected Files/§Exit Conditions/§Required Documentation) — this doc's contribution is the **ClickUp side** of the mapping, not a new task format.

---

## 2. JSON contract — what an agent expects to consume

When an agent reads a task via `GET /v2/task/{task_id}`:

```json
{
  "id": "86ahxxxxx",
  "name": "0123 — fix: short description",
  "status": { "status": "in progress", "color": "..." },
  "priority": { "priority": "high", "color": "..." },
  "tags": [
    { "name": "type:fix" },
    { "name": "AI: ready to start!" },
    { "name": "blocks:0145" }
  ],
  "custom_fields": [
    { "name": "agent_owner", "value": "claude-code" },
    { "name": "blocked_by", "value": "0120" },
    { "name": "estimated_blocks", "value": 2 }
  ],
  "markdown_description": "## Context\n...\n## Problem\n...\n## What To Do\n- [ ] ...",
  "url": "https://app.clickup.com/t/86ahxxxxx"
}
```

The agent's **parser** should produce this internal structure:

```python
@dataclass
class AgentReadableTask:
    id: str
    title: str
    type: str           # extracted from title OR from `type:*` tags
    priority: str        # from native field
    status: str          # from native field
    context: str         # extracted from markdown ## Context
    problem: str         # ## Problem
    todo: list[str]      # ## What To Do (bullets)
    files_affected: list[FileRef]  # ## Affected Files (path + role)
    exit_criteria: list[str]       # ## Exit Conditions
    notes: str           # ## Implementation Notes
    closure_checklist: list[ChecklistItem]  # ## Required Documentation
    blocked_by: list[str]   # from custom field
    blocks: list[str]       # from custom field
    agent_owner: str        # from custom field
    source_of_truth: Literal["clickup", "repo"]
    repo_path: str | None   # if source_of_truth == "repo"
```

This contract is what makes a task **predictable** for an agent instead of something it has to guess at via regex.

---

## 3. Recommended custom fields in ClickUp

Custom fields do what frontmatter does in the `.md` file. Configure once per Space, replicate to every relevant list:

| Custom field | Type | Purpose | `.md` equivalent |
|---|---|---|---|
| `type` | dropdown (feat/fix/refactor/docs/chore/audit/proposal) | Task type | frontmatter `type:` |
| `agent_owner` | text | Assigned agent | frontmatter `author:` (once picked up) |
| `parent_task` | task relationship | Parent (epic/story) | frontmatter `parent:` |
| `blocked_by` | task relationship (multi) | Blockers | frontmatter `blocked_by:` |
| `blocks` | task relationship (multi) | Blocked tasks | frontmatter `blocks:` |
| `estimated_blocks` | number | Effort estimate | n/a — metadata |
| `repo` | dropdown (one option per target repo) | Target repo | frontmatter `repo:` (not currently a field — suggested) |
| `clickup_id_local` | text (auto via API) | Mirrors the local task ID | frontmatter `clickup_id:` (the other side) |
| `last_synced_at` | date | Last repo↔ClickUp sync | n/a — sync log |

**Tags** stay useful for fast signaling without competing with custom fields:

| Tag | Use |
|---|---|
| `AI: ready to start!` | Task is structured and ready for an agent to pick up |
| `AI: more info needed` | Missing info for an agent — a human needs to fill it in |
| `AI: human only` | Not automatable (e.g. design, product decision) |
| `AI: in-progress:<agent>` | Agent is working on it (redundant with `agent_owner` field, but more visible) |
| `lei-fechamento:incomplete` | Task closed but the Closure Law checklist wasn't complete — flag for review |

---

## 4. Task validator (not yet built)

To make the schema enforced, a `validate_task.py`-equivalent for the ClickUp side should check:

1. ✅ Frontmatter/custom-fields contain: `status`, `priority`, `type`, `author`, `created`.
2. ✅ Body contains all required sections, in order.
3. ✅ "What To Do" has ≥1 checkbox bullet.
4. ✅ "Affected Files" has ≥1 path (do the paths exist? warn if not).
5. ✅ "Exit Conditions" has ≥1 bullet.
6. ✅ "Required Documentation" has all canonical items (even if `[N/A]`).
7. ✅ If `clickup_id` is set, `GET /v2/task/{id}` returns 200.
8. ⚠ Warn if "Implementation Notes" is >500 words (probably should be a separate design doc).

Structured JSON output with `pass | warn | fail` per criterion. Runs as a pre-commit hook or in CI — same pattern as this repo's `validate_task.py` for the file side.

---

## 5. Why this schema is what unlocks a real agentic pipeline

Without a predictable schema: an agent has to infer via regex/LLM what each part of a task means. Slow, error-prone, expensive in tokens.

With a predictable schema: the parser (`AgentReadableTask`) is a small, predictable struct. The agent can focus entirely on execution — not on figuring out what the task even is. That's the gap between "an agent that helps devs write tickets" and "a pipeline where tickets become PRs."
