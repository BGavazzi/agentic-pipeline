# Convention — Engineering Defaults (org-wide)

Architecture and stack decisions that apply as **defaults** across all repos. Not absolute laws (👇 they have justifiable exceptions), but the burden of diverging falls on whoever diverges.

> Promoted from personal memory to the constitution because these describe *how this org builds software*, not one person's preference.

---

## 1. Business rules live in the backend that owns the data

Validation, invariant enforcement, 3rd-party integration (keys/secrets), and auto-derivation **go in the backend that owns the data** — never in the frontend. The front is **UX**: surfacing backend errors, affordance, optimistic disabling. Never enforcement.

- Validation rule ("X required to publish", "Y ∈ Z"): use-case in the backend + DB constraint where applicable. Front shows the 4xx/422.
- 3rd-party integration with secrets (image-gen, OpenAI, payments): endpoint in the backend. Front does POST and reads the response.
- Auto-derivation ("derive X from Y on write"): backend re-derives authoritatively. Front can pre-fill for UX.
- Cross-record invariant: transaction in the backend.

**Why:** if the rule lives only in the front, any other caller (scraper, webhook, future microservice, manual `curl`) bypasses it. Lived with `news_items.source_id` (ADR-002). If a front ticket says "enforce X" / "prevent Y", rewrite it as a backend ticket + a thin UI follow-up.

---

## 2. No technical plumbing exposed in the UI

Do not expose backend plumbing (FK selectors derivable from context) as a form choice in editor screens. **Prefer silent auto-derivation.**

When a fix requires populating a relational FK in a form, first ask whether the FK can be **derived** from another field the user already cares about (host from URL, category name, slug). If so, derive it in a watch/effect and hide the FK. Only fall back to a picker when derivation is genuinely ambiguous and the user **must** disambiguate. Document the derivation logic in an ADR — silent untracked inference becomes a ghost.

**Why:** the editor thinks "the original article's URL", not the curated taxonomy table. A picker adds a click that the user's mental model doesn't justify.

---

## 3. AI-generated images: never photorealistic

AI-generated images (Imagen or any provider) for public-facing products (news portals, etc.) **must never be photorealistic** — always illustration / non-photo style.

- The shared image tool **does not expose `"photo"` mode** — do not pass `style: "photo"`.
- Pair with a visible "AI-generated" label.

**Why:** a photorealistic image of a real event/person = misinformation + likeness risk; illustration clearly signals it's editorial/AI, not a photo of the event. Applies to cluster-synthesis, cover generation, and similar tools.

---

## 4. UI Component ⇄ Storybook (mandatory, frontend)

In any frontend repo with Storybook, **component and story are a single package**:

- **No new component without a story.** Creating a UI component (atom, molecule, any reusable in `Components/`) **requires** delivering, in the same PR, what Storybook needs: the `*.stories.jsx` with representative variants (relevant states/colors/sizes) rendering with the real theme (decorator `ChakraProvider` + theme tokens). PR for a component without a story = incomplete, doesn't merge.
- **If it already exists in Storybook, use and respect it.** Before writing a component, **search the Storybook/catalog** to see if there's already a canonical one for that intent. If so, **reuse it** (extend via props/composition) — **cloning an `XCustom`/`XV2`/domain-copy that does the same thing is forbidden**. Diverging from the canonical requires explicit justification in the PR (and ideally becomes a variant of the canonical, not a new component).
- **Tokens, not hardcode.** Component in a story uses theme tokens (color/spacing/typography) — zero hardcoded hex. This is what makes the story faithful to Figma and whitelabeling possible.
- **Pixel-perfect verifiable.** The story is the artifact against which design/QA checks Figma fidelity (and where the factory's `visual-tester` runs perceptual diff). Without a story, "matches Figma" is unverifiable.

**Why:** the `<front-repo>` accumulated ~21 Button implementations, 17 Input, 8 Avatar — each screen built on non-consolidated atoms, so the same intent appears visually different across screens. Story-per-component + "reuse the canonical" is what prevents the next generation of clones and gives the designer a single source of truth. 2026-06-09.
