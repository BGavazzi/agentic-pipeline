---
status: in_progress
priority: P1
type: feat
created: 2026-09-17
updated: 2026-09-18
clickup_id: null
parent: null
blocks: []
blocked_by: [0045]
---

# 0046 — Real Playwright visual-regression producer

## Context
The visual receipt validator checked hashes and internally consistent metrics,
but no core component actually decoded screenshots or computed pixel changes.
W4 supplies a protected-runtime adapter that can run a frontend repository's
Playwright command without making the generic pipeline depend on a frontend.

## Problem
Candidate-provided numeric diff claims are not proof of a visual change. A
visual gate needs protected baseline provenance, exact view coverage, decoded
baseline/candidate images, measured changed pixels, and durable diff artifacts.

## What To Do
- [x] Run a runtime-supplied Playwright-style argv in an exact candidate tree.
- [x] Require a protected baseline manifest and exact view-set match.
- [x] Decode PNGs, compare dimensions/pixels, and emit diff artifacts.
- [x] Bind receipt to base/head, baseline manifest, invocation and command digest.
- [x] Add identical-render, changed-render and mismatched-view tests.
- [x] Require a protected command policy, allowlisted environment, exact
  merge-tree execution, bounded image inputs, safe view IDs and digest-checked
  baseline/diff artifacts.
- [x] Preserve multi-view baseline evidence and make the producer receipt
  re-validate through the generic visual validator.
- [ ] Pilot against a scoped frontend repository with approved baseline storage.

## Affected Files
- `scripts/playwright_visual_producer.py`
- `scripts/visual_receipt.py`, `scripts/ci_receipts.py`
- `tests/test_playwright_visual_producer.py`, `tests/test_ci_receipts.py`
- `.github/workflows/ci.yml`

## Exit Conditions
- [x] Identical decoded render passes at zero threshold.
- [x] Changed decoded pixels fail a zero threshold and report exact counts.
- [x] Missing/mismatched views fail before admission.
- [x] Baseline/candidate/diff artifacts are copied under a bounded artifact root.
- [x] Command identity, clean-room tree, per-view metrics and artifact digests
  are recorded and adversarial path/duplicate/pixel-limit tests pass.
- [x] Reviewer/scanner gates remain green after the producer is added.
- [ ] A real Playwright browser run and protected baseline update are reviewed.

## Required Documentation (Closure Law)
- [x] `CHANGELOG.md` updated.
- [x] `<function_catalog>` updated.
- [N/A] `<sdd_kit_path>`: no architectural decision ratified in this packet.
- [x] `README.md` updated.
- [x] `.agents/continuity-codex.md` updated.
- [x] Tests passing.
- [N/A] `<route_map>`: no web route changed.
- [ ] PR approved.

## Honest Backlog
The protected caller must supply the command policy, browser version, OS/font
image, baseline storage and frontend scope. The adapter proves decoded pixels
and provenance consistency; it does not make a candidate-supplied policy or
baseline cryptographically trusted. No frontend repository or customer data was
used in this packet.
