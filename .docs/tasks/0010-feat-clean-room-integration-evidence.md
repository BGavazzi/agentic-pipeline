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

# 0010 — feat: clean-room integration evidence

## Context
Task 0009 made admission fail closed on high-risk changes, but the first
honest receipt showed that the pipeline had no independent integration
producer. Unit tests ran in the checkout and scanner jobs produced evidence,
while the documented V2 idea of a clean sandbox remained prose. This task is
the first executable slice of the agentic quality-admission framework: an
agent-generated change must survive a fresh workspace before it can progress
to staging review.

## Problem
"Tests passed" is not enough if the test command ran against checkout-local
residue, untracked files, or a state different from the committed candidate.
Admission must receive a machine-readable integration result with exact
base/head identity, an explicit pass/fail/error status, and useful metrics.
The producer must not use a shell string or publish arbitrary test output into
the receipt.

## What To Do
- [x] Add `scripts/integration_gate.py` with a git-archive clean-room
      workspace, argv-only command execution, timeout handling, and schema-v1
      evidence containing identity, status, isolation mode, exit code, and
      duration/output-size metrics.
- [x] Add unit tests for clean staging, success, failure, timeout, CLI output,
      and invalid commit identity.
- [x] Add a PR-only CI `integration` job on the same safe runner-routing
      policy as the existing test/gates jobs; upload evidence even on failure.
- [x] Extend `ci_receipts.py` to include the integration artifact when present
      and reject stale integration identity.
- [x] Make the integration producer a core gate script and classify edits to
      it as high risk.
- [x] Document the new evidence path and update the function catalog,
      changelog, and continuity ledger.
- [ ] Add an independent ultrareview receipt producer in a follow-up task;
      this task deliberately does not fabricate that obligation.

## Affected Files
- `scripts/integration_gate.py`
- `scripts/ci_receipts.py`
- `scripts/core_sync.py`
- `scripts/blast_radius.py`
- `.github/workflows/ci.yml`
- `tests/test_integration_gate.py`
- `tests/test_ci_receipts.py`
- `.docs/function-catalog.md`
- `README.md`
- `CHANGELOG.md`
- `.agents/continuity-codex.md`

## Exit Conditions
- [x] A committed candidate can be tested in a temporary clean workspace
      without shell interpolation or checkout-local residue.
- [x] Pass, non-zero failure, timeout, and staging errors are distinguishable;
      no missing/error integration run becomes pass.
- [x] Receipt identity binds to exact full base/head SHAs and is consumed by
      the admission aggregator.
- [x] CI uploads integration evidence on both pass and failure paths.
- [x] Focused tests, task validation, workflow YAML parsing, and diff checks
      pass; a real local clean-room run passes.
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
- The clean-room runner uses the host's installed dependencies and does not
  yet provision a container image or service topology. A later task should add
  pinned worker images, database/service fixtures, and homelab pool execution
  policy for trusted events.
- Evidence is structurally validated but not cryptographically signed; task
  0009 already records that protected workflow ownership and signed policy are
  still required before this is a trust boundary.
- The integration command is intentionally explicit and argv-based. A future
  repo manifest can declare language-specific integration profiles without
  reintroducing shell interpolation.
