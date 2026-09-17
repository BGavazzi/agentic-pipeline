---
status: in_progress
priority: P0
type: feat
created: 2026-09-16
updated: 2026-09-16
clickup_id: null
parent: 0011
blocks: []
blocked_by: []
---

# 0012 — feat: isolated ultrareview worker runner

## Context
Task 0011 defined a safe receipt contract but left the reviewer invocation
outside the harness. The user wants agent-generated work to survive automated
integration and adversarial review before staging review, with homelab workers
used where the event is trusted. This task supplies the portable worker-side
execution boundary; runner routing and credential policy remain deployment
concerns.

## Problem
An ultrareview receipt is only meaningful if the reviewer ran independently
against the committed candidate. A wrapper that runs a command in the builder's
checkout, accepts prose, or treats an unavailable worker as PASS defeats the
entire admission model.

## What To Do
- [x] Add `scripts/ultrareview_runner.py` to archive committed HEAD, write a
      base/head diff context, execute an explicit reviewer argv in a temporary
      workspace, and pass stdout through the task 0011 validator.
- [x] Emit explicit error receipts for worker timeout, non-zero exit, malformed
      JSON, workspace failure, and missing command; never downgrade them to
      PASS.
- [x] Add tests for successful worker output, non-zero/malformed/timeout
      failures, CLI output, and clean-workspace context.
- [x] Include the runner in core sync and high-risk gate-script classification.
- [ ] Add protected homelab-worker routing and credential isolation as a
      deployment task; this runner has no credentials and does not contact an
      LLM service itself.

## Affected Files
- `scripts/ultrareview_runner.py`
- `scripts/ultrareview_receipt.py`
- `scripts/core_sync.py`
- `scripts/blast_radius.py`
- `tests/test_ultrareview_runner.py`
- `.docs/function-catalog.md`
- `README.md`
- `CHANGELOG.md`
- `.agents/continuity-codex.md`

## Exit Conditions
- [x] Reviewer runs in a temporary committed-HEAD workspace with a separate
      diff context and no shell interpolation.
- [x] Valid PASS/BLOCK reports normalize through the task 0011 contract.
- [x] Worker unavailable, timeout, malformed output, or non-zero exit produces
      `status=error` and a non-zero process exit.
- [x] Focused tests pass and gate-surface changes are high-risk classified.
- [ ] Homelab routing/credential isolation is implemented — separate task.
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
- The runner is an execution adapter, not an LLM client. A deployment must
  provide a reviewer command, isolate its credentials, and authenticate the
  resulting evidence before using it as a security boundary.
- The temporary workspace is a host-process boundary. Container/VM sandboxing,
  network policy, and ephemeral homelab workers are the next hardening layer.
- The diff context is a file path in the temporary workspace and is cited by
  the reviewer; future validation can check that cited paths/lines exist.
