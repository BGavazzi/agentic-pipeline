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

# 0063 — Feature: provider-neutral CI telemetry evidence

## Context
The harness emits local scorecards and PR-intelligence measurements, but no
provider-neutral metric payload. That makes queue, gate and worker SLO export a
future rewrite instead of a bounded adapter.

## Problem
Operational telemetry must preserve denominators and commit/run identity while
avoiding accidental network or secret export. It must not become a quality score
that compensates for a failed gate.

## What To Do
- [x] Convert numeric fields from validated local reports into an OTLP-shaped
      JSON metric payload with resource identity and report labels.
- [x] Keep the adapter file-only and explicitly mark network export disabled.
- [x] Emit the payload from the admission evidence job as an artifact.
- [x] Test deterministic metrics, identity validation and secret-free fields.
- [ ] Add a protected collector/exporter and queue-age/worker SLO source as a
      separately authorized operational deployment task.

## Affected Files
- `scripts/ci_telemetry.py`
- `tests/test_ci_telemetry.py`
- `.github/workflows/ci.yml`, `scripts/sota_audit.py`
- `README.md`, `CHANGELOG.md`, `.docs/function-catalog.md`

## Exit Conditions
- [x] Numeric metrics retain a report denominator label and exact run identity.
- [x] No network call or credential value is emitted by the adapter.
- [x] CI produces the payload without changing admission semantics.
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
This is a local OTLP-shaped evidence adapter, not an exporter, collector, queue
monitor or alerting system. It does not infer worker health, delivery success or
quality from a metric count.
