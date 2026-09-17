---
status: in_progress
priority: P1
type: feat
created: 2026-09-17
updated: 2026-09-17
clickup_id: null
parent: null
blocks: []
blocked_by: [0049]
---

# 0050 — Deterministic receipt-mutation benchmark

## Context
Admission has unit-level malformed-receipt tests, but a compact mutation
benchmark makes the fail-closed property measurable and visible in CI.

## What To Do
- [x] Generate nine deterministic stale, malformed, downgraded, duplicate,
  unknown and non-pass receipt mutations from a complete high-risk fixture.
- [x] Report blocked/unsafe counts and fail-closed rate.
- [x] Fail the benchmark if any mutation still admits.
- [x] Run and upload the benchmark in CI.
- [ ] Add property/fuzz generation and authenticated platform fixtures in a
  separate packet.

## Affected Files
- `scripts/receipt_mutation_benchmark.py`
- `tests/test_receipt_mutation_benchmark.py`
- `.github/workflows/ci.yml`

## Exit Conditions
- [x] Every current mutation is rejected or returns `admitted=false`.
- [x] The benchmark emits explicit unsafe survivors and a fail-closed rate.
- [x] Existing admission and scanner suites remain green.
- [ ] Property/fuzz corpus and independent producer authenticity are added.

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
Nine hand-authored mutations are a regression contract, not fuzzing or a
formal proof. They do not establish authenticity of the producer inputs or
cover every parser/runtime boundary. Those require separate, trusted fixtures.
