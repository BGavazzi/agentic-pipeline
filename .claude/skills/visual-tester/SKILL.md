---
name: visual-tester
description: Drives a real, already-logged-in Chrome instance via the Chrome DevTools Protocol (CDP) to screenshot a running app (or a Storybook story) and diff it against a reference image — either an exported Figma frame or a previous baseline screenshot. Used by tester's fe_real mode to assert "looks right", not just "builds". Requires a Chrome instance launched with --remote-debugging-port and CDP endpoint reachable; figma-mode also requires FIGMA_API_KEY. Never touches the user's own tabs — opens a fresh tab per capture. STATUS - reference skill for CDP capture + diff scripts; wire the scripts into your repo (not bundled here as a running service).
tools: Bash, Read, Write, Glob
---

# Visual Tester

Closes the "build green ≠ looks right" gap. Screenshots a real, rendered
page via CDP and diffs it pixel-by-pixel against a reference — without
touching whatever tabs the human already has open in that Chrome instance.

**Do NOT confuse with [[codebase-audit]] or [[clickup-audit]]** — this
doesn't audit anything against declared rules; it compares two images.

---

## Precondition

A Chrome instance reachable via CDP (`--remote-debugging-port=<port>`,
already logged into whatever the app under test requires). If unreachable:

```
degrade — do NOT invent a pass. tester's fe_real mode falls back to
build+lint only and marks the visual axis as skipped, not green.
```

`figma-mode` diffing additionally requires `FIGMA_API_KEY` (see [[figma-api]]).

---

## Components (BYO — write these into your repo, adapt paths freely)

| Script | Purpose |
|---|---|
| `live_shot.mjs --cdp <endpoint> --navigate <url>` | Opens a **new tab** in the target Chrome (via CDP), navigates to `<url>`, waits for network-idle, screenshots, closes the tab. Detects a logged-out state (`looksLogin: true` in its output) so callers don't diff a login screen against a reference and call it a fail for the wrong reason. |
| `figma_export.mjs --node <figma_node_id> --out <path>` | Wraps [[figma-api]]'s image export endpoint; downloads the reference PNG locally. |
| `diff.mjs --a <path_a> --out <diff_path>` --b <path_b> | Pixel diff (e.g. via `pixelmatch` or `resemblejs`) between two PNGs of matching dimensions; writes a diff-highlight image + a numeric `%` mismatch. |

These are thin wrappers, not a bundled framework — the specific diff
library and CDP client are a repo choice (Playwright's CDP-connect API is
one straightforward option: `chromium.connectOverCDP(endpoint)`).

---

## Modes

### 1. Baseline mode (no Figma — screenshot vs. previous screenshot)

Use when there's no design reference, only "did this change unexpectedly."

```bash
node live_shot.mjs --cdp $CDP_ENDPOINT --navigate <url> --out current.png
node diff.mjs --a <baseline_path> --b current.png --out diff.png
```

- No prior baseline exists → this run's screenshot **becomes** the baseline; report "baseline captured", not a diff.
- Baseline exists → report `%` mismatch + `diff.png`.

### 2. Figma mode (screenshot vs. exported design frame)

Use when the task carries a Figma brief ([[figma-frontend-context]] output).

```bash
node figma_export.mjs --node <figma_node_id> --out reference.png
node live_shot.mjs --cdp $CDP_ENDPOINT --navigate <url> --out current.png
node diff.mjs --a reference.png --b current.png --out diff.png
```

**Directional, not a hard gate**: a raster diff between a vector design tool
export and a real browser render will never be 0% (font rendering,
anti-aliasing, subpixel layout differ even on a pixel-perfect implementation).
Treat the `%` as a signal to eyeball `diff.png`, not a pass/fail threshold on
its own — this mirrors [[tester]]'s note ("don't reject solely on %").

### 3. Storybook mode

If the repo's convention is story-per-component (see
`.docs/conventions/engineering-defaults.md` if present), point `live_shot.mjs`
at the story's isolated URL instead of the full app — smaller surface,
faster, and matches what design/QA actually reviews.

---

## Login-state guard

`live_shot.mjs` must detect a logged-out render (redirect to a login route,
or a login form's marker selector present) and set `looksLogin: true` in its
output. Callers (Tester) treat this as a **fail with a distinct reason**
("session logged out"), never as a silent 0%-match "pass" against a login
screen that happens to resemble nothing.

---

## Output (per invocation)

```
Visual Tester — <mode: baseline | figma | storybook>
Target: <url>
CDP: <reachable | unreachable — degraded>
Login state: <ok | looksLogin:true>
Reference: <baseline.png | figma node <id> | story <name>>
Diff: <%.N mismatch> — <diff_path>
Verdict: <pass | needs-review | fail>
```

`Verdict` mapping:
- `pass` — mismatch below the repo's own tolerance (baseline mode only; figma mode never auto-passes on %, see §2).
- `needs-review` — figma mode always lands here plus the diff image, for a human/[[tester]] to eyeball.
- `fail` — `looksLogin: true`, CDP unreachable and no fallback taken, or (baseline mode) mismatch far above tolerance with no code explanation.

---

## Hard rules

- **Never touches the user's existing tabs** — always a fresh tab via CDP, closed after capture.
- **Never invents a pass** — CDP unreachable → degrade and say so; don't fabricate a diff.
- **Figma-mode % is directional** — never gate purely on a numeric threshold; a human or [[tester]] looks at `diff.png`.
- **Detect logged-out renders** — a blank/login screenshot must never register as a low-mismatch "pass."

## Failure modes

| Error | What to do |
|---|---|
| CDP endpoint unreachable | Degrade to build+lint only (caller's responsibility per [[tester]] §5 step 4); report `unreachable`, don't retry indefinitely |
| `looksLogin: true` | Fail with that reason; do not diff further |
| Dimension mismatch between `a` and `b` | Fail the diff step explicitly — don't silently resize (resizing hides real layout bugs) |
| Figma export fails (network/auth) | Fall back to baseline mode if a prior screenshot exists; else report the figma-mode axis as skipped |
| Story/route doesn't exist at given URL | Fail with the literal HTTP status / navigation error |

## Anti-patterns

- ❌ Treating a `%` mismatch threshold as pass/fail in figma-mode.
- ❌ Diffing without checking for a logged-out redirect first.
- ❌ Reusing the user's active Chrome tab instead of opening a new one.
- ❌ Silently resizing one image to match the other before diffing.
- ❌ Calling this a "test suite" — it's one axis ([[tester]]'s `fe_real` opt-in), not a replacement for functional tests.

## Skills consumed / produced

- Reuses: [[figma-api]] (figma-mode export).
- Invoked by: [[tester]] (`fe_real: true` — see tester §5 step 4), [[implement-figma-task]] (optional sanity pass before handoff).
- Upstream: [[figma-frontend-context]] (supplies the `figma_node_id` when in figma-mode).

## V2 backlog

- Multi-viewport capture (mobile/tablet/desktop in one run)
- Baseline auto-approval workflow (human clicks "accept new baseline" instead of editing files)
- Perceptual diff tuned for anti-aliasing tolerance (SSIM-based, not raw pixelmatch) to reduce figma-mode noise
