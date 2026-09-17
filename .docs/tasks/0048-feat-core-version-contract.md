---
status: in_progress
priority: P1
type: feat
created: 2026-09-17
updated: 2026-09-17
clickup_id: null
parent: null
blocks: []
blocked_by: [0047]
---

# 0048 — Versioned core release and compatibility metadata

## Context
The pipeline had many schema constants and a drift manifest, but a consumer
could not answer which core release it installed or which contract inventory it
was expected to support.

## Problem
Silent core drift and unreviewed receipt/schema changes make portfolio-wide
syncs hard to audit. Release identity, producer-envelope compatibility and
manifest schema must be explicit while local edits remain protected.

## What To Do
- [x] Define a documented core release version separate from receipt schemas.
- [x] Emit source repository, exact source commit and supported contract metadata during sync.
- [x] Add a validator CLI for installed metadata.
- [x] Include release metadata in drift protection and core sync inventory.
- [x] Add fresh-sync, validation and invalid-metadata tests.
- [ ] Publish an immutable signed release and migrate a consumer repo.

## Affected Files
- `scripts/core_version.py`
- `scripts/core_sync.py`
- `tests/test_core_version.py`, `tests/test_core_sync.py`

## Exit Conditions
- [x] A synced target records core release and source commit.
- [x] Unsupported or malformed metadata fails closed.
- [x] Local edits to release metadata are detected and preserved by default.
- [x] Existing drift/skill/receipt behavior remains green.
- [ ] A real consumer compatibility matrix and signed release are published.

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
This is a version/provenance contract, not a signature or supply-chain proof.
Release signing, immutable tags, dependency/action pinning and consumer rollout
remain separate activation work. No target repository was mass-synced here.
