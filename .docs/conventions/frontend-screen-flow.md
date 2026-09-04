# Convention — frontend screen creation flow

> **Provenance note (migrated 2026-09).** Migrated from this repo's
> predecessor (`guidelines_IA`, tombstoned). Translated to English for
> consistency with this repo's other convention files. Scrubbed of one
> client-project codename and one specific screen name from the original
> incident story — the underlying lessons (§6 especially, real debugging
> gotchas) are kept verbatim since they're technical, not organizational.

How a frontend **screen** is born, from spec/Figma to PR, without shipping wrong. This is the **screen**-level layer above two conventions that already exist and are **not** repeated here:

- **Component level:** [`engineering-defaults.md` §4](engineering-defaults.md) — Storybook mandatory, reuse the canonical component, tokens-not-hardcode, verifiable pixel-perfect.
- **Branch/build/deploy level:** [`git-pr-workflow.md` §3 and §6](git-pr-workflow.md) — PR base = `integration`, local build before CI.

> Origin: a real frontend project, observed over several weeks. Screens shipped wrong for three recurring reasons — they diverged from Figma with nobody noticing until the PO looked; every screen reinvented its own structure; and nobody knew which component was canonical (21 Buttons, 17 Inputs, 8 Avatars, all across the same codebase). This convention attacks all three in the flow itself, not in review.

---

## 1. The three pains (and where each is solved)

| Pain | Symptom | Solved by |
|---|---|---|
| **Diverges from Figma** | screen compiles green, but layout/color/filters don't match; only discovered when the PO looks | **visual proof in the flow** (§4 below, `visual-tester` skill) |
| **Reinvents everything** | structure/data-fetch/state redone from scratch on every screen | **screen recipe / golden path** (§3 below) |
| **Which component?** | picks the wrong version, clones it, hardcodes a color | **reuse the canonical** (`engineering-defaults` §4) + a canonical-components table |

The core rule: **the pipeline has to see the divergence before the human does.** A screen that compiles ≠ a correct screen. What put the team in the line of fire (a visually wrong screen the PO sees) was exactly what CI didn't check — `build`+`lint` pass and the screen is still crooked.

---

## 2. The flow, end to end

For **every new or reworked screen**:

```
1. Brief        → spec + Figma frame (link, fileKey, nodeId)
2. Grounding    → what already exists in the repo for this? which is the canonical component?
3. Scaffold     → copy the screen mold (§3), do NOT invent a new structure
4. Implement    → reuse canonicals (eng-defaults §4); tokens, never hex
5. Local build  → build passes + click through the screen (git-pr-workflow §6)
6. Visual proof → screenshot of the screen vs. Figma → diff attached (§4 below)
7. PR           → targets `integration` (git-pr-workflow §3)
```

Step 6 is what this convention adds to the loop. Without it, step 5 ("build passes") gives a false sense of done.

---

## 3. Screen recipe (golden path)

A screen is **not invented** — it copies the mold. For a Next.js Pages Router app, the canonical skeleton follows a strict layer: `pages/ → Components/ → queries/ → services/` (see that repo's own `CLAUDE.md`):

1. **`pages/<route>/index.js`** — route only: guards it (`ProtectRoute`), renders the feature component. Zero logic.
2. **`Components/<Domain>/<Screen>/`** — the feature. Composes **existing canonical components** (§4 eng-defaults), never new ad-hoc atoms.
3. **Data via a hook** — `queries/` (React Query) → `services/` (Axios). **A component never calls the API client directly.** Backend choice is explicit via env var, never implicit.
4. **Four required states, always**: `loading` (skeleton), `error` (toast from the backend's 4xx — don't invent a rule client-side, see §1 eng-defaults), `empty` (empty-state), `data`.
5. **Layout via theme tokens** — zero hardcoded hex. This is what keeps fidelity to Figma and enables whitelabeling.
6. **Visible text in the product's language; code identifiers in English.**

**Why:** when every screen picks its own structure, data-fetch, and state handling, review turns into archaeology and inconsistency between screens explodes. One shared mold makes a screen born reviewable.

---

## 4. Mandatory visual proof before the PR

Every screen with a Figma reference **closes with a visual proof attached to the PR** — not "I think it looks right."

- **Tool:** the [`visual-tester`](../../.claude/skills/visual-tester/SKILL.md) skill. Invoke it with the screen + the Figma `{fileKey, nodeId}`; the underlying scripts (export/capture/diff) run via shared Playwright+pixelmatch.
- **What it produces:** a screenshot of the rendered screen (frame's viewport) + an export of the Figma frame + a **perceptual diff** (numeric % + diff image) → attached to the PR as evidence. Report under `.docs/visual-reports/`.
- **Two modes:**
  - **vs-Figma (directional):** catches structural divergence — a truncated label, a missing filter, off spacing. Noisy when the mock has placeholder data and the screen has real data; good for finding what's missing, not for pinning down an exact %.
  - **baseline (regression):** the first run captures the baseline and **stops for human approval**; subsequent runs compare against that approved baseline. Controlled state → the % is trustworthy.
- **Anti-hallucination:** the diff image is the evidence. "Matches Figma" with no diff attached **doesn't count** — same law as `engineering-defaults` §4, applied at the screen level.

**Why:** visual divergence is the pain that reaches the PO/boss and never shows up in `build`+`lint`. Moving that check inside the flow (before the PR) is what takes the team out of the line of fire.

---

## 5. Long tail — consolidating primitives

The canonical-components table is a stopgap; the cure is **consolidating duplicated primitives** (Button/Input/Avatar/Badge) into a single set with a story (`engineering-defaults` §4). That's a multi-session initiative with human gates to confirm each set's canonical form. While it's running, the flow's rule is: **when in doubt about which component to use, stop and ask — don't clone.**

**Regression gate (consolidation without Figma).** Swapping a clone for the canonical rarely has a Figma reference to check against — so **today's rendered screen is the spec**. The criterion is zero-regression: swap the component, capture every screen that consumes it (found via the actual import/reachability graph, **not** grep) across two targets, compare pixel-by-pixel — **unchanged visual = WIN; changed = either the canonical's variant doesn't cover that case, or the swap wasn't safe → revert.** This is the `visual-tester` (§4) baseline mode applied cross-environment:

- **candidate** = a local **production** build of the branch with the swap;
- **baseline** = deployed staging **or** the same branch without the swap. The second isolates the delta completely (no data/version noise); the first is the human sanity check.
- The canonical component has to be a **superset**: it must reproduce every existing look via a variant/prop, chosen by the consumer. If two clones look genuinely different, "nothing changed" only closes that way.
- **Authenticated screens:** attach via CDP to an already-logged-in Chrome instance and reuse the session. **Never** handle a user's credential/token without explicit OK. SSO doesn't log in unattended — there's no such thing as an unassisted login; without a session, the authenticated gate stays pending a human's 30-second login.

---

## 6. Verification gotchas — when the green check lies

A gate's value is proportional to its honesty: it only counts if **a broken process would actually turn it red**. Every trap below already made a "✅" lie on a real frontend gate.

- **A story parsing/rendering in isolation ≠ the app build passing.** A smoke test that only imports/renders a story in Storybook does **not** catch `react-hooks/rules-of-hooks`: a hook called inside a lowercase `render: () => {...}` function (not a Capitalized component) is a **lint error** and breaks the actual app build. Fix: extract the body into a proper Capitalized component (`render: (a) => <Demo {...a}/>`). Only a clean build **with lint** catches this — Storybook alone won't.
- **A stale eslint cache masks the error.** A build tool reusing its lint cache can pass **locally** while breaking in a fresh CI/deploy. To validate a build "from zero," clear the build cache first.
- **The build cache bakes env values in.** Public env vars get inlined at build time. Swapping env values **without** clearing the build cache serves the app's old, baked-in values (one real incident: shipped a candidate build silently pointing at production data). Always clear the build cache when changing env.
- **`cmd | tail` swallows the exit code.** `build | tail -5` returns `tail`'s exit status (always 0), hiding a build that actually failed. Capture the real exit code from the command that matters, without piping through something that discards it.
- **`networkidle` never fires** in an app with HMR/websocket/polling (dev servers, Storybook dev) → every screenshot times out and the gate reports a false 0/N. Use `domcontentloaded` + wait for a content selector instead.
- **Focus state / antialiasing = noise.** A focus ring present in one capture and not the other, or a gradient border, produces a false diff. Neutralize focus (`activeElement.blur()`), disable animation/transition/caret, and calibrate the pixelmatch threshold (too strict flags identical screens; too loose misses real diffs).

**Why:** before trusting a gate, ask *if this were actually broken right now, would this check catch it?* Several of the above answered "no" — and so they lied. A gate that can't fail isn't a gate.

---

## 7. Screen closure checklist

Before opening a screen's PR:

- [ ] Structure follows the §3 mold (thin route → feature → hook → 4 states).
- [ ] Zero new atom without checking the canonical (§4 eng-defaults); zero hardcoded hex.
- [ ] Local build passes (git-pr-workflow §6) — ideally **from a clean cache**, to avoid masking lint/env issues (§6).
- [ ] Visual proof attached (§4) — diff vs. Figma **or** vs. baseline. Consolidation without Figma: zero-regression gate (§5).
- [ ] PR targets `integration` (git-pr-workflow §3), no default reviewer.
- [ ] UI text is in the product's language.
