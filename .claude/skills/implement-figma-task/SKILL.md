---
name: implement-figma-task
description: Implements a frontend task whose spec is a grounded Figma brief (figma-frontend-context + codebase-grounding output) rather than plain prose — maps target_children to actual components (creating new ones only when codebase_context.component_mapping found no match), writes the diff, and iterates against the exported reference image. Trigger when builder detects a task is frontend AND has a Figma brief/sticky attached, or user says "implement this Figma frame". Runs inside the normal Builder loop — same Closure Law obligations.
tools: Read, Edit, Write, Bash, Glob, Grep
---

# Implement Figma Task

A specialization of [[builder]] for tasks whose spec originates from Figma.
Everything [[builder]] requires (Closure Law §3, surgical §Affected Files,
tests passing) still applies — this skill only changes **how the diff gets
written**, not the closure obligations around it.

**Do NOT invoke this standalone** without a grounded brief — it consumes the
output of [[figma-frontend-context]] → [[codebase-grounding]], it doesn't
fetch Figma or scan the repo itself.

---

## Inputs

- `brief`: the JSON produced by `figma-frontend-context` and enriched by
  `codebase-grounding` (has `target_children`, `implementation`,
  `codebase_context.component_mapping`, `codebase_context.conventions`,
  `codebase_context.constitution`)
- `task_path`: `.docs/tasks/NNNN-*.md` (if invoked from the normal task
  queue rather than ad hoc)
- `reference_image`: path to the exported PNG (from `figma-frontend-context`
  §Step 5), if present

---

## Workflow

```
1. Read codebase_context.constitution (hard_rules, design_decisions) —
   same non-negotiable precedence as builder §2 step 2.

2. For each entry in brief.target_children, cross-reference
   codebase_context.component_mapping:
   a. Matched, in_design_system: true → import and use it. Do NOT clone it
      into a local variant "to be safe" (see engineering-defaults.md's
      canonical-component rule if the repo has one).
   b. Matched, in_design_system: false (app-level component) → reuse if the
      match is solid; ambiguous match → read the candidate file before
      deciding, don't guess from the name alone.
   c. No match (ambiguous: null) → this child needs to be built. Check
      codebase_context.conventions for file naming / export style / props
      typing, and mirror the nearest analogous existing component.

3. Implement using Edit/Write, following brief.implementation.what_to_build
   and any TEXT content captured in figma-frontend-context's output
   (use as literal copy, or map to i18n keys per codebase_context.i18n_keys
   if the repo has i18n).

4. Use design tokens, not hardcoded values, for color/spacing/typography —
   read codebase_context.tech_stack.styling to know where those tokens live
   (Tailwind config, CSS variables, a theme object). A pixel value lifted
   directly from the Figma inspector instead of the nearest token is the
   most common way this kind of task drifts from the design system.

5. If reference_image is present and a dev server is reachable, do a quick
   visual sanity pass yourself (screenshot the rendered output, eyeball
   against reference_image) before declaring done — this is a cheap check,
   not a substitute for [[visual-tester]]'s pixel diff, which runs later in
   Tester's fe_real mode.

6. Continue the normal builder loop from here: type-check, test, commit,
   Closure Law §3 (see [[builder]] §2 steps 4d onward). If the repo has a
   Storybook convention requiring a story per new component, that's part of
   §Affected Files / Closure Law, not optional because the source was Figma.
```

---

## Divergence handling

If the built result diverges from the Figma frame (a target child doesn't
exist in code and building it faithfully would require a larger change than
the task scope allows, or the design uses a pattern the design system
doesn't support yet):

- Record it in the PR body's §Divergences (same as [[builder]] §2 step 4g) —
  Dxx candidate if it implies a new design-system primitive.
- Do NOT silently approximate ("close enough") without flagging it — the
  whole point of a Figma-sourced task is that fidelity is verifiable
  ([[visual-tester]] will catch an unflagged divergence anyway, just later
  and without context on why).

---

## Hard rules

- **Constitution wins over the Figma brief** — same rule as [[codebase-grounding]]: if `constitution.hard_rules` contradicts what the brief implies, surface the conflict rather than silently following Figma.
- **Reuse the canonical component** — don't create `ButtonV2`/`ButtonCustom` when `codebase_context.component_mapping` found a match, even if the Figma instance is named differently.
- **Tokens, not hardcoded values** — any hex/px lifted directly from the Figma inspector instead of the nearest design token is a defect, not a shortcut.
- **All of [[builder]]'s hard rules apply** — this skill doesn't relax Closure Law, testing, or the surgical-diff contract.

## Failure modes

| Error | What to do |
|---|---|
| `component_mapping` empty (no design system detected) | Build inline, following `codebase_context.conventions`; note in PR that no design system was found |
| `target_children` references a component type not expressible in the stack (e.g. a native-only pattern in a web repo) | STOP, ask — don't force a bad translation |
| `reference_image` missing | Continue without the visual sanity pass; rely on [[visual-tester]] downstream |
| Ambiguous match in `component_mapping` (`ambiguous: true`) | Read both candidates before choosing; if still unclear, ask |

## Anti-patterns

- ❌ Cloning a design-system component into a one-off variant instead of extending it via props.
- ❌ Hardcoded hex/px values copied straight from the Figma inspector.
- ❌ Silently approximating a Figma detail that doesn't fit the current design system, without a §Divergences note.
- ❌ Treating this as a separate closure flow from [[builder]] — it's the same obligations, different diff-writing strategy.

## Skills consumed / produced

- Upstream: [[figma-frontend-context]] → [[codebase-grounding]] (brief must already be grounded).
- Invoked by: [[builder]], when a task is frontend and carries a Figma brief.
- Downstream: [[tester]] (`fe_real: true` + [[visual-tester]] for the pixel-fidelity check), then [[librarian]] as normal.
