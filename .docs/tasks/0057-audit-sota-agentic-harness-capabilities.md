---
status: in_progress
priority: P1
type: audit
created: 2026-09-18
updated: 2026-09-18
clickup_id: null
parent: null
blocks: []
blocked_by: []
---

# 0057 — Audit SOTA agentic harness capabilities

## Context
The harness now has deterministic gates, receipts and bounded worker
contracts, but its maturity is difficult to benchmark. Current SOTA practice
also separates static implementation evidence from operational facts such as
signed provenance, ephemeral workers, test-history freshness and merge-queue
activation.

## Problem
Without a versioned capability inventory, a documented feature can be confused
with a working feature, and external trust controls can be accidentally
counted as active. The benchmark must be deterministic and report-only so it
cannot weaken admission.

## What To Do
- [x] Define a versioned capability rubric covering correctness, security,
      agent evaluation, scale, supply chain and operations.
- [x] Implement a static evidence auditor with pass/partial/missing states and
      denominator-first coverage metrics.
- [x] Keep externally activated controls explicit and uncredited by default.
- [x] Add unit coverage for conservative classification and deterministic JSON/
      Markdown output.
- [x] Run the audit in CI as an uploaded report without replacing admission.
- [ ] Turn missing/partial rows into separately scoped implementation tasks,
      starting with test-result history freshness and artifact provenance/SBOM.

## Affected Files
- `scripts/sota_audit.py`
- `tests/test_sota_audit.py`
- `.github/workflows/ci.yml`
- `.docs/analysis/sota-agentic-harness-gap-analysis-2026-09.md`
- `README.md`, `CHANGELOG.md`

## Exit Conditions
- [x] Report contains versioned metrics and an evidence row per capability.
- [x] Missing external activation cannot become a static PASS.
- [x] Report is descriptive and cannot override `admission_gate.py`.
- [x] Tests and closure validators pass.
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
This audit does not activate GitHub rulesets, merge queues, signing keys,
homelab workers, telemetry exporters, release deployment gates or private
consumer baselines. It measures repository-facing evidence and lists the
operational proof still required.
