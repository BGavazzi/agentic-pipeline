---
status: in_progress
priority: P1
type: feat
created: 2026-09-16
updated: 2026-09-16
clickup_id: null
parent: 0004
blocks: []
blocked_by: []
---

# 0016 — feat: visual-regression receipt contract

## Context
The portfolio survey found no runnable visual-regression adapter in the core,
guidelines_IA, or bluemagic-front; only PortalApp has real Playwright/Chromatic
execution. The harness needs a generic evidence contract before each frontend
repo grows a bespoke and unauditable screenshot policy.

## Problem
"Looks right" is not a gate. A visual result must identify the candidate and
baseline, cite screenshots and viewports, report pixel-diff metrics, and apply a
deterministic threshold. Missing screenshots or baselines must be non-admitted.

## What To Do
- [x] Add `scripts/visual_receipt.py` to validate screenshot evidence,
      baseline provenance, viewport, pixel counts, diff ratio, threshold, and
      exact base/head identity.
- [x] Normalize deterministic PASS/FAIL results; reject missing or malformed
      evidence rather than treating browser absence as pass.
- [x] Add adversarial contract tests and classify the adapter as a gate surface.
- [x] Document that consuming frontend repos provide the Playwright/browser
      runner; this core does not pretend to launch one universally.
- [ ] Add a Playwright producer in the first frontend repo selected for
      migration, then feed its artifact into this contract.

## Affected Files
- `scripts/visual_receipt.py`
- `tests/test_visual_receipt.py`
- `scripts/core_sync.py`
- `scripts/blast_radius.py`
- `.docs/function-catalog.md`
- `README.md`
- `CHANGELOG.md`
- `.agents/continuity-codex.md`

## Exit Conditions
- [x] Under-threshold evidence is PASS; over-threshold evidence is FAIL.
- [x] Missing screenshots, baseline, metrics, or stale identity returns error.
- [x] Contract is tested and synced/classified as a high-risk gate surface.
- [ ] A real Playwright producer is wired in a consuming frontend repo.
- [ ] PR approved — remains `in_progress` until review, per Closure Law.

## Required Documentation (Closure Law)
- [x] `CHANGELOG.md` updated
- [x] `.docs/function-catalog.md` updated (new public script signature)
- [N/A] `<sdd_kit_path>` — no SDD_KIT.md in this repo
- [x] `README.md` updated
- [x] `.agents/continuity-codex.md` updated
- [x] Tests passing
- [N/A] `<route_map>` — no web routes in this repo
- [ ] PR approved

## Honest Backlog
- This task is intentionally a contract, not a browser runtime. Playwright,
  browser binaries, visual baselines, and app-specific login/state belong in a
  consuming frontend repository or dedicated worker image.
- Pixel thresholds do not understand semantic layout correctness; add DOM and
  accessibility assertions alongside screenshots.
- Baseline storage and review of intentional visual changes need a protected
  artifact policy before visual PASS can be trusted for release.
