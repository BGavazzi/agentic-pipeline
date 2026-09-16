---
status: in_progress
priority: P0
type: feat
created: 2026-09-16
updated: 2026-09-16
clickup_id: null
parent: 0009
blocks: []
blocked_by: []
---

# 0011 — feat: ultrareview receipt contract

## Context
Task 0009 intentionally required an ultrareview gate for high-risk changes,
and task 0010 supplied the independent clean-room integration producer. The
remaining gap is the interface between an independent adversarial agent and
the deterministic admission layer. The existing `ultrareview` skill defines
the behavior—re-execute, cite evidence, default to BLOCK when proof is weak—
but had no machine-checked receipt contract.

## Problem
Admission cannot safely consume prose such as "review passed." It needs a
canonical PASS/BLOCK/invalid distinction, exact commit identity, proof that
the reviewer invocation was independent, and citations for the verdict. A
deterministic adapter must validate those claims without pretending to be the
LLM reviewer or authenticating candidate-controlled JSON.

## What To Do
- [x] Add `scripts/ultrareview_receipt.py` to validate an independent review
      report and normalize it into a schema-v1 `ultrareview` receipt.
- [x] Require exact base/head SHAs, an independence marker, reviewer kind and
      invocation id, at least one evidence citation, metrics, and findings for
      BLOCK verdicts.
- [x] Reject PASS without evidence, BLOCK without findings, stale identity,
      malformed metrics, and unsupported schema.
- [x] Extend `ci_receipts.py` and core-sync/high-risk classification to consume
      the canonical ultrareview receipt when a producer supplies it.
- [x] Add adversarial contract tests; keep the actual LLM review separate.
- [ ] Add a protected independent-agent producer in the next orchestration
      slice; this task only makes its output safe to consume.

## Affected Files
- `scripts/ultrareview_receipt.py`
- `scripts/ci_receipts.py`
- `scripts/core_sync.py`
- `scripts/blast_radius.py`
- `tests/test_ultrareview_receipt.py`
- `tests/test_ci_receipts.py`
- `.docs/function-catalog.md`
- `README.md`
- `CHANGELOG.md`
- `.agents/continuity-codex.md`

## Exit Conditions
- [x] Canonical PASS and BLOCK receipts are emitted only from reports that
      satisfy identity, independence, evidence, and metrics requirements.
- [x] Invalid or stale reports fail with exit code 2; BLOCK exits 1; PASS exits
      0; no malformed report can become a pass.
- [x] Receipt aggregation carries ultrareview status and rejects stale reports.
- [x] Focused tests pass and gate-script changes are classified high risk.
- [ ] Protected independent reviewer invocation exists — separate task.
- [ ] PR approved — remains `in_progress` until review, per Closure Law.

## Required Documentation (Closure Law)
- [x] `CHANGELOG.md` updated
- [x] `.docs/function-catalog.md` updated (new public script signature)
- [N/A] `<sdd_kit_path>` — no SDD_KIT.md in this repo
- [x] `README.md` updated
- [x] `.agents/continuity-codex.md` updated
- [x] Tests passing
- [N/A] `<route_map>` — no web routes in this repo
- [ ] PR approved

## Honest Backlog
- The adapter validates structure and identity but cannot authenticate who
  produced the report. Protected workflow ownership, signed evidence, and
  reviewer isolation remain required before this becomes a trust boundary.
- The repo's Claude/agent runtime is not callable from ordinary GitHub Actions
  without an explicit credential and policy integration. No fake CI PASS is
  emitted; missing ultrareview evidence still blocks high-risk admission.
- Evidence citations are structured strings, not yet verified against the
  checkout. A later producer can add path/line/artifact existence checks.
