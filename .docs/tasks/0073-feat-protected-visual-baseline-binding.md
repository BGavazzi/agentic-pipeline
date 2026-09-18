---
status: in_progress
priority: P1
type: feat
created: 2026-09-18
updated: 2026-09-18
clickup_id: null
parent: 0016-feat-visual-regression-receipt
blocks: []
blocked_by: []
---

# 0073 — Feature: bind visual receipts to protected baselines

## Context
The visual receipt contract validates screenshot artifacts and threshold
semantics, but a candidate could still select a different baseline unless a
trusted caller supplied a protected baseline policy.

## Problem
Visual regression evidence is only meaningful when the baseline reference,
digest, and browser image are independently selected and exact-bound.

## What To Do
- [x] Accept an optional protected baseline policy from the trusted caller.
- [x] Bind baseline ref and digest to the policy manifest.
- [x] Bind the protected threshold and record browser image provenance.
- [x] Add adversarial tests for valid and candidate-replaced baselines.
- [ ] Wire a real Playwright producer and protected baseline store in a
      consuming frontend repository.

## Affected Files
- `scripts/visual_receipt.py`
- `tests/test_visual_receipt.py`

## Exit Conditions
- [x] Protected baseline mismatch blocks the receipt.
- [x] Valid baseline policy remains exact-head and artifact-bound.
- [x] Existing visual receipt tests pass.
- [ ] A protected frontend producer generates the evidence.

## Required Documentation (Closure Law)
- [x] `CHANGELOG.md` updated
- [x] `function-catalog` updated
- [N/A] `SDD_KIT` — no new architecture decision required
- [x] `README.md` updated (visual contract docs already describe the adapter)
- [x] `.agents/continuity-codex.md` updated
- [x] Tests passing
- [N/A] `ROUTE_BEHAVIOR_MAP` — no HTTP routes
- [ ] PR approved (task remains in progress until review)

## Honest Backlog
This does not launch Playwright or create a baseline repository. It prevents
untrusted candidate evidence from choosing its own baseline when a protected
caller supplies the manifest.
