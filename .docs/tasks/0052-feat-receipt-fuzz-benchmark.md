---
status: in_progress
priority: P1
type: feat
created: 2026-09-17
updated: 2026-09-17
clickup_id: null
parent: null
blocks: []
blocked_by: [0051]
---

# 0052 — Bounded receipt fuzz benchmark for malformed nested evidence

## Context
The W9 receipt-mutation benchmark covers nine hand-authored mutations. This
packet adds a bounded property-style corpus that generates deterministic JSON
noise for authoritative nested admission fields and measures whether the
evaluator rejects or blocks every case.

The benchmark is synthetic regression evidence. It does not authenticate the
producer, runner, CI platform, or source of any receipt, and it does not prove
universal parser safety.

## What To Do
- [x] Add a seeded generator with default 128 cases, maximum 512 cases, and a
  maximum generated payload depth of 3 (hard depth limit 6).
- [x] Cover malformed schema, identity, risk, required-gate, receipt-list,
  gate-name and gate-status fields consumed by admission.
- [x] Report rejected, blocked, unsafe-admitted, path-coverage and fail-closed
  metrics in a deterministic JSON artifact.
- [x] Run the benchmark in CI beside the W9 mutation benchmark.
- [ ] Use authenticated platform-produced fixtures or claim authenticity.

## Affected Files
- `scripts/receipt_fuzz_benchmark.py`
- `tests/test_receipt_fuzz_benchmark.py`
- `.docs/tasks/0052-feat-receipt-fuzz-benchmark.md`
- `.docs/analysis/receipt-fuzz-benchmark-2026-09.md`
- `.github/workflows/ci.yml` (one benchmark step and artifact path)

## Exit Conditions
- [x] The default corpus is deterministic and bounded.
- [x] Every generated malformed authoritative case is rejected or returns
  `admitted=false`; any unsafe survivor fails the benchmark.
- [x] Unit, clean-room integration, task/closure, blast-radius and scanner
  gates are run and their limitations are recorded.
- [x] The output explicitly distinguishes synthetic fuzz evidence from
  authenticity proof.
- [ ] An independently protected producer and authenticated platform fixture
  exist.
- [ ] PR approved.

## Required Documentation (Closure Law)
- [x] `CHANGELOG.md` updated.
- [x] `function-catalog.md` updated.
- [N/A] `SDD_KIT.md` — no architectural decision ratified in this packet.
- [x] `README.md` updated.
- [x] `.agents/continuity-codex.md` updated.
- [x] Tests passing.
- [N/A] `ROUTE_BEHAVIOR_MAP.md` — this repository has no HTTP routes.
- [ ] PR approved.

## Honest Backlog
This bounded corpus exercises the current Python evaluator with generated
in-memory values. It is not a security proof, does not cover arbitrary parser
implementations or all runtime boundaries, and cannot establish authenticity.
The full suite and protected external producers remain authoritative.
