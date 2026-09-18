---
status: in_progress
priority: P1
type: feat
created: 2026-09-18
updated: 2026-09-18
clickup_id: null
parent: 0057
blocks: []
blocked_by: []
---

# 0060 — Feature: pinned CI environment contract

## Context
The harness runs the same logical tests on hosted and future disposable
workers, but CI installed Python dependencies without exact pins and emitted
no environment identity. That makes drift and cross-worker failures harder to
explain.

## Problem
Archive isolation is not hermeticity. We need a small, secret-free evidence
contract that fails when required Python packages differ from the reviewed
versions and records the runner/platform identity for later parity analysis.

## What To Do
- [x] Add exact CI dependency pins in `requirements-ci.txt`.
- [x] Replace unpinned CI installs with the requirements file.
- [x] Emit a versioned environment fingerprint into test evidence.
- [x] Fail the fingerprint on missing or mismatched pinned packages.
- [x] Add deterministic unit tests with injected observations.
- [ ] Add a pinned OCI toolchain and network/offline enforcement as a later
      deployment task; this slice does not claim full hermetic execution.

## Affected Files
- `requirements-ci.txt`
- `scripts/environment_fingerprint.py`
- `tests/test_environment_fingerprint.py`
- `.github/workflows/ci.yml`, `scripts/sota_audit.py`
- `README.md`, `CHANGELOG.md`

## Exit Conditions
- [x] CI dependency installation is exact-version, not floating.
- [x] Test artifacts include a secret-free environment fingerprint.
- [x] Mismatch and malformed-pin behavior is tested.
- [x] Full suite, scanners and closure validators pass.
- [ ] PR approved.

## Required Documentation (Closure Law)
- [x] `CHANGELOG.md` updated
- [x] `<function_catalog>` updated
- [N/A] `<sdd_kit_path>`: no new architectural decision record
- [x] `README.md` updated
- [x] `.agents/continuity-codex.md` updated
- [x] Tests passing
- [N/A] `<route_map>`: no route changed
- [ ] PR approved

## Honest Backlog
This is a dependency/fingerprint contract, not proof of a hermetic build. It
does not pin the OS image, Docker daemon, browser/font stack, network policy or
homelab worker. Those remain explicit SOTA gaps.
