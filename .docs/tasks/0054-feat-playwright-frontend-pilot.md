---
status: in_progress
priority: P1
type: feat
created: 2026-09-17
updated: 2026-09-17
clickup_id: null
parent: null
blocks: []
blocked_by: [0046]
---

# 0054 — Feature: approved Storybook/Playwright visual pilot

## Context
Task 0046 supplied the core pixel-evidence producer but deliberately stopped
short of choosing a frontend, browser, or baseline policy. This task adds a
small reusable Storybook adapter and exercises it against an approved private
frontend locally, without uploading screenshots or invoking a hosted visual
service.

## Problem
The harness can validate a real browser receipt, but there was no documented
capture adapter or evidence that a real Storybook view set can pass through the
producer. A pilot must keep the view set protected, use deterministic viewport
metadata, fail on missing stories or page errors, and preserve the local-only
boundary for private frontend content.

## What To Do
- [x] Add a generic Storybook capture adapter that emits the producer manifest.
- [x] Validate exact protected story IDs, bounded viewports and PNG output paths.
- [x] Add Node syntax/CLI contract coverage to the Python test suite.
- [x] Run a real Playwright Chromium capture against the approved private
      Storybook consumer and compare it with a locally protected baseline.
- [ ] Decide the long-term browser image, baseline storage and CI worker policy.

## Affected Files
- `examples/playwright/storybook_capture.mjs` (generic consumer adapter)
- `tests/test_storybook_capture_contract.py` (CLI/syntax contract)
- `.docs/analysis/playwright-visual-pilot-2026-09.md` (local metrics and limits)
- `README.md` (usage and trust boundary)
- `CHANGELOG.md` (shipped capability)
- `.docs/function-catalog.md` (public adapter contract)

## Exit Conditions
- [x] The adapter captures only the protected manifest's exact view IDs.
- [x] Missing Storybook entries, invalid viewports, page errors and timeouts fail.
- [x] The adapter emits only bounded JSON on stdout and writes PNGs locally.
- [x] A real browser run produces a zero-diff receipt against a local baseline.
- [ ] A protected CI worker and durable baseline store are approved and deployed.

## Required Documentation (Closure Law)
- [x] `CHANGELOG.md` updated
- [x] `<function_catalog>` updated
- [N/A] `<sdd_kit_path>`: no architectural decision ratified in this packet
- [x] `README.md` updated
- [x] `.agents/continuity-codex.md` updated
- [x] Tests passing
- [N/A] `<route_map>`: no web route changed
- [ ] PR approved

## Honest Backlog
The pilot intentionally does not commit private screenshots, baseline images,
frontend source, credentials, Chromatic tokens or a claim of CI authenticity.
The protected caller still owns the baseline manifest, browser image, worker
isolation and artifact upload policy.
