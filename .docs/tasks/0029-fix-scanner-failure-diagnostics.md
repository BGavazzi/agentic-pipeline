---
status: in_progress
priority: P1
type: fix
created: 2026-09-16
updated: 2026-09-16
clickup_id: null
parent: 0007
blocks: []
blocked_by: []
---

# 0029 — fix: add safe structured scanner failure diagnostics

## Context
The current scan gate already captures scanner stderr internally, but its
receipt only reported a generic JSON parse failure. The original Trivy incident
was therefore difficult to diagnose without downloading artifacts and could
not be reproduced from the local environment until Docker was opened.

## Problem
Publishing raw stderr into a PR artifact can leak paths, URLs, or accidental
secrets; publishing nothing makes a transient scanner failure opaque. The gate
needs a bounded diagnostic category plus a correlation digest, while keeping
the actual scanner failure non-admissible.

## What To Do
- [x] Classify stderr into safe categories such as Trivy DB download, network,
      rate-limited, permission, resource-exhausted, or generic present.
- [x] Include a short SHA-256 digest of stderr for correlation without raw log
      publication.
- [x] Add tests for Trivy DB diagnostics, empty stderr, and redaction.
- [x] Run the live Docker contract against pinned Semgrep, Trivy, and Gitleaks
      images and record the result.
- [x] Update user-facing scanner documentation with the current evidence.

## Affected Files
- `scripts/scan_gate.py`
- `tests/test_scan_gate.py`
- `README.md`

## Exit Conditions
- [x] Parse failures remain blocking errors.
- [x] Receipts contain a safe diagnostic category and no raw stderr.
- [x] Live synthetic scanner contract passes for all required scanners.
- [x] Full test suite passes.

## Required Documentation (Closure Law)
- [x] `CHANGELOG.md` updated
- [N/A] `function-catalog.md` — no function catalog exists
- [N/A] `SDD_KIT.md` — no new product decision
- [x] `README.md` updated
- [N/A] `.agents/continuity-<agent>.md` — no continuity file in this checkout
- [x] Tests passing
- [N/A] `ROUTE_BEHAVIOR_MAP.md` — no route/handler/model change
- [ ] PR approved

## Honest Backlog
- Task 0007 remains `in_progress`: the original transient Trivy failure was not
  reproduced, so this task does not claim to prove whether the vulnerability DB
  download caused it. The current invocation/cache path is live-validated and
  future failures will carry a safe diagnostic category and digest.
