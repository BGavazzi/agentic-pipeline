---
name: codebase-grounding
description: >
  Use this skill when you have a brief (typically a JSON from another skill like figma-frontend-context,
  or a manual spec, bug report, or screenshot description) and need to enrich it with codebase context —
  what already exists in the target repo, the repo's rules-of-the-house (CLAUDE.md / AGENTS.md /
  SDD_KIT.md — loaded as a hard-enforced "constitution"), available design system primitives, file
  locations, repo conventions, and i18n keys. Trigger when the user references a brief AND a repo path together, or
  says things like "ground this brief in our repo", "check the codebase before implementing X", "find
  what we already have for this". Output is the input JSON unchanged, with a codebase_context block
  appended.
---

# Codebase Grounding Skill

Takes a JSON brief (typically from another skill — e.g. `figma-frontend-context`) and a repo path. Enriches the brief with a `codebase_context` block describing what exists in the repo and how the work should integrate.

**Output contract:** the input JSON, unchanged, with a new top-level key `codebase_context`.

---

## Input

```json
{
  "meta": { "...": "..." },
  "source": { "...": "..." },
  "summary": "string",
  "target_children": [
    { "name": "SegmentedControl", "type": "INSTANCE", "...": "..." }
  ],
  "implementation": { "what_to_build": "...", "...": "..." }
}
```

Plus a `repo_path` (passed as an argument or asked from the user if missing).

Only `target_children[].name` and `implementation.what_to_build` are strictly required — everything else is optional context.

---

## Workflow

### Step 0 — Load the Repo Constitution (do this FIRST)

Before fingerprinting the stack, read the repo's **rules-of-the-house** documents. These are hard contracts the implementing agent MUST obey — not soft conventions inferred from sample files. Skipping this step is how silent violations ship (real example: a repo's `CLAUDE.md` mandated a Bruno `.bru` doc per new endpoint; grounding never read it, the Builder never created the docs, and the violation reached review undetected — cycle 1, gap G-02).

Read each of these if present, at the repo root and one level down:

| File | Authority |
|---|---|
| `CLAUDE.md` | Repo-specific hard rules for any agent. **Highest authority.** |
| `AGENTS.md` / `AGENTS.balanced.md` / `AGENTS.minimal.md` | Org + repo agent constitution (Lei de Fechamento, naming, doc obligations). |
| `SDD_KIT.md` | Formal design decisions (`Dxx` flags). Constrains what the implementation may change. |
| `ROUTE_BEHAVIOR_MAP.md` | Per-endpoint behavioral contracts (if the work touches routes). |
| `CONTRIBUTING.md` | Human-facing contribution rules, sometimes stricter than CLAUDE.md. |

Capture **verbatim** (do not paraphrase — the Builder needs the literal rule text), plus a distilled checklist of any rule phrased as "always / never / must / sempre / nunca / obrigatório":

```json
{
  "constitution": {
    "sources": ["CLAUDE.md", "AGENTS.balanced.md", "SDD_KIT.md"],
    "raw": {
      "CLAUDE.md": "<full text>",
      "AGENTS.balanced.md": "<full text>",
      "SDD_KIT.md": "<full text>"
    },
    "hard_rules": [
      {
        "rule": "Every new HTTP endpoint requires a .bru file under docs/api/Blue Events API/",
        "source": "CLAUDE.md §1",
        "applies_when": "the work adds or modifies an HTTP route"
      }
    ],
    "design_decisions": [
      { "id": "D02", "summary": "notification_dispatches is immutable — no updated_at/deleted_at", "source": "SDD_KIT.md" }
    ]
  }
}
```

**Filtering**: include in `hard_rules` only the rules that plausibly apply to *this* brief (an endpoint rule is irrelevant to a CSS-only change). But always capture the full `raw` text so the Builder can re-check edge cases.

If none of these files exist, record `"constitution": { "sources": [], "note": "No constitution docs found — fall back to inferred conventions (Step 5) only" }` and flag it in `discovery_notes` — a repo with no rules doc is itself worth noting.

---

### Step 1 — Detect Tech Stack

Read these files (if they exist) to fingerprint the project:

| File | What it tells you |
|---|---|
| `package.json` | Framework (`react`, `vue`, `svelte`), styling (`tailwindcss`, `styled-components`, `@emotion/*`), state (`zustand`, `redux`, `@tanstack/react-query`), i18n (`i18next`, `react-intl`, `vue-i18n`), routing |
| `tsconfig.json` / `jsconfig.json` | TypeScript? Path aliases (`@/components/*`)? |
| `tailwind.config.*` | Tailwind in use, theme tokens defined here |
| `next.config.*` / `vite.config.*` / `astro.config.*` | Meta-framework |
| `.eslintrc.*` / `biome.json` | Code style enforcement |
| `README.md` | Project conventions stated by humans |

Capture:

```json
{
  "framework": "react | vue | svelte | next | etc.",
  "language": "typescript | javascript",
  "styling": "tailwind | css-modules | styled-components | etc.",
  "state_management": "zustand | redux | context | tanstack-query | local",
  "i18n": { "library": "i18next | react-intl | none", "locale_files_path": "string | null" },
  "path_aliases": { "@/": "src/" }
}
```

---

### Step 2 — Locate the Design System

Look for a folder that contains shared UI primitives. Common patterns:

- `src/components/ui/`
- `src/components/design-system/`
- `src/ds/`
- `packages/ui/` (in monorepos)
- A package referenced in `package.json` like `@company/design-system`

Inside it, list the primitive components (button, input, select, tabs, etc.). Capture their file paths and exported names — this is what the implementation will import from.

```json
{
  "design_system_path": "src/components/design-system",
  "available_primitives": [
    { "name": "Button", "path": "src/components/design-system/Button.tsx" },
    { "name": "SegmentedControl", "path": "src/components/design-system/SegmentedControl.tsx" },
    { "name": "InputTextField", "path": "src/components/design-system/InputTextField.tsx" }
  ]
}
```

If no design system folder is found, scan `src/components/` for anything that looks like a primitive and note that the project doesn't have a formal DS.

---

### Step 3 — Match Figma Components to Codebase Components

For each name in `target_children[]`, search the repo for a matching component:

```bash
# locate which files export the design-system primitives
rg -l "export.*(SegmentedControl|Button v2|InputTextField)" --type ts --type tsx
```

Strip suffixes like "v2", "v3" — `Button v2` in Figma probably matches a `Button` component in code.

For each match, record:

- The Figma name (as it appeared in the brief)
- The codebase name (cleaned)
- The file path
- Whether it's in the design system or app code
- Whether multiple matches exist (ambiguity to flag)

```json
{
  "component_mapping": [
    {
      "figma_name": "Button v2",
      "codebase_name": "Button",
      "path": "src/components/design-system/Button.tsx",
      "in_design_system": true,
      "ambiguous": false
    },
    {
      "figma_name": "SegmentedControl",
      "codebase_name": null,
      "path": null,
      "in_design_system": false,
      "ambiguous": false,
      "note": "No match in repo — needs to be built or imported"
    }
  ]
}
```

---

### Step 4 — Find the Affected Area in the App

If the brief implies refactoring existing code (words like "off-model", "fix", "update", "current"), find where the existing code lives:

- Search for distinctive text strings from the design (Portuguese copy, labels, placeholders) — these often exist verbatim in the codebase or in locale files
- Search for route names or page names referenced in the ClickUp task
- Search for component names that match the target frame's name (`tabs-search` → look for `TabsSearch`, `tabs-search.tsx`, `SearchTabs`, etc.)

```bash
rg "Publicadas|Agendadas|Rascunhos" --type-add 'web:*.{ts,tsx,vue,svelte,js,jsx}' -t web
rg "tabs.search|TabsSearch" --type-add 'web:*.{ts,tsx,vue,svelte,js,jsx}' -t web
```

Capture:

```json
{
  "candidate_files": [
    {
      "path": "src/features/content/pages/MyContentPage.tsx",
      "reason": "Contains 'Publicadas' and 'Agendadas' literals",
      "action": "modify | create | replace"
    }
  ],
  "i18n_keys": [
    { "key": "content.tabs.published", "value": "Publicadas", "file": "locales/pt-BR.json" }
  ]
}
```

If i18n was detected in Step 1, also look up whether the copy already exists as keys.

---

### Step 5 — Detect Patterns the Agent Should Follow

Scan a few representative files in the same area to learn conventions:

- How are props typed? (`interface Props` vs `type Props`)
- Are components default exports or named?
- Is there a test file convention? (`*.test.tsx` next to component, or in `__tests__/`?)
- Storybook stories present?
- File naming: `PascalCase.tsx`, `kebab-case.tsx`, or `lowercase.tsx`?

```json
{
  "conventions": {
    "file_naming": "PascalCase",
    "export_style": "named",
    "props_typing": "interface",
    "test_location": "colocated",
    "has_storybook": true
  }
}
```

Keep this lightweight — read 2-3 nearby files, don't audit the whole codebase.

---

### Step 6 — Assemble Output

Append everything to the input JSON under `codebase_context`:

```json
{
  "...": "(input JSON unchanged)",
  "codebase_context": {
    "repo_path": "string",
    "constitution": { "...": "(from Step 0 — hard rules + design decisions)" },
    "tech_stack": { "...": "..." },
    "design_system": { "...": "..." },
    "component_mapping": [ "..." ],
    "candidate_files": [ "..." ],
    "i18n_keys": [ "..." ],
    "conventions": { "...": "(soft, inferred — distinct from constitution.hard_rules)" },
    "discovery_notes": [
      "Any ambiguities, missing matches, or warnings the next agent should know about"
    ]
  }
}
```

---

## When to Stop and Ask

- Repo path not given → ask the user
- Repo path doesn't exist or isn't readable → tell the user, don't guess
- No design system found AND multiple component matches across the repo → ask which area is canonical
- Brief is missing both `target_children` and `implementation.what_to_build` → ask the user what to search for
- **A `constitution.hard_rules` entry directly contradicts the brief** (e.g. brief says "skip API docs to move fast", CLAUDE.md says docs are mandatory) → surface the conflict to the user; do not silently let the brief override the constitution. The constitution wins unless the user explicitly overrides it.

---

## Performance Notes

- Cap scans at the first 2-3 directory levels unless something interesting is found
- For very large monorepos, ask the user which package/app to scope to

---

## What This Skill Does NOT Do

- It does not generate code — only context for code generation
- It does not modify any files in the repo
- It does not run the project, tests, or builds
- It does not validate that the suggested mappings are correct — it surfaces candidates for the next agent to verify
