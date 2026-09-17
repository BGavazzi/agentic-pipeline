---
status: in_progress
priority: P1
type: feat
created: 2026-09-17
updated: 2026-09-17
clickup_id: null
parent: null
blocks: []
blocked_by: [0050]
---

# 0051 — Core release compatibility matrix

## Context
The release contract identifies the installed core, but a consumer still needs
an explicit check for minimum core versions and required receipt contracts.

## What To Do
- [x] Define a versioned compatibility matrix format.
- [x] Validate minimum semantic version and contract inventory per consumer.
- [x] Fail closed for unsupported matrix/schema/contract inputs.
- [x] Add a self-consumer matrix and CI report path.
- [ ] Mass-sync a real consumer only after protected release/rollout approval.

## Affected Files
- `scripts/core_compatibility.py`
- `.docs/compatibility/core-matrix.json`
- `tests/test_core_compatibility.py`
- `.github/workflows/ci.yml`

## Exit Conditions
- [x] Compatible and incompatible consumer cases are tested.
- [x] Current core release is checked against the committed self matrix.
- [x] Existing full suite and scanner gates remain authoritative.
- [ ] A real consumer compatibility rollout is approved and executed.

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
The matrix is a local compatibility contract, not signed distribution, a
consumer migration or a dependency/action pinning policy. The self consumer is
deliberately synthetic until a protected rollout is authorized.
