---
name: frontend-refactor-pr
description: Open a reviewable frontend refactor PR with reachability grounding, zero-regression classification, clean builds, per-location visual evidence, and explicit human review for intentional pixel changes. Triggers - consolidating components, tokenizing hardcoded values, converging on a design system, or retiring a legacy atom.
metadata:
  type: skill
---

# frontend-refactor-pr

Frontend refactor means structural or token convergence, not behavior change.
The proof is not merely “it compiles”: it is that the rendered result stayed
the same, or that every intended visual change is explicit and reviewable.

## Grounding before editing

- Use an import/reachability graph when finding consumers; never use grep as a
  substitute for reachability.
- Read representative callers. Counts and old audit reports age; the most-used
  component is not automatically the canonical one.
- Do not sweep idiomatic framework components into custom wrappers merely
  because they are common. Consolidate real clones and the intended canonical
  surface.

## Classify the refactor

| Class | Example | Required proof |
|---|---|---|
| Zero-regression by construction | same-value tokenization, alias collapse, dead-key rename | clean build plus pixel-identical confirmation |
| Intentional pixel change | legacy atom → design-system atom with different defaults | the visual diff is the proposal; human review is mandatory |

Resolve design tokens in the component's supported prop/CSS context. Verify
icon props and casing rather than assuming a token string will resolve in every
renderer.

## Build and visual gates

1. Build from a clean cache. A stale lint/build cache can hide hooks errors or
   bake the wrong public environment values.
2. Preserve exit codes; do not pipe the decisive command through a formatter
   that masks failure.
3. Map changed components to affected screens through reachability.
4. Compare at least one representative location from every affected usage
   stratum. One screenshot can miss the only caller that actually changes.
5. Prefer a deterministic browser/Storybook producer that emits a versioned
   visual receipt. Keep binary evidence on a dedicated non-code evidence branch
   or artifact store, never in the feature branch.
6. The PR body leads with an “Impacto visual”/“Visual impact” section stating
   which locations changed, which are pixel-identical, and linking each proof.

Authentication is an explicit precondition. Never capture or manipulate a
user's session/token without permission; a missing authenticated surface is a
blocked visual gate, not fabricated evidence.

## PR mechanics and hard rules

- One PR per coherent refactor decision; stacked branches are allowed when the
  dependency is explicit.
- Behavior changes leave this workflow and become feature work.
- A zero-pixel result is still evidence and must be reported.
- Intentional visual changes cannot be auto-approved.
- State what was not sampled as a follow-up; never imply whole-app coverage
  from one location.
