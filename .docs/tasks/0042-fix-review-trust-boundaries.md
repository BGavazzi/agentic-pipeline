---
status: in_progress
priority: P0
type: fix
created: 2026-09-16
updated: 2026-09-16
clickup_id: null
parent: null
blocks: []
blocked_by: []
---

# 0042 — Fix reviewed harness trust and evidence boundaries

## Context
The user requested fixes for the review of PRs #14–#44. Fourteen findings
identified false-pass evidence, unsafe worker attestations, staging identity
gaps, inaccurate telemetry, and ineffective workflow trust assumptions.
This is a corrective replacement for that interdependent stack, not another
feature expansion. Existing branches/worktrees remain preserved.

## Problem
Passing unit tests did not establish that the gates reject adversarial inputs.
Several adapters erased upstream failures or accepted claims without observing
the underlying code, artifacts, or lifecycle. GitHub master was also found to
have no branch protection; code changes alone cannot activate that protection.

## What To Do
- [x] Preserve scanner vetoes and bind unit receipts to the exact commit pair.
- [x] Execute exact candidate trees and test the merge with the staging base.
- [x] Strictly validate worker facts and use a separate fresh host teardown callback.
- [x] Observe task state and all file changes independently of agent claims.
- [x] Verify visual artifacts, protected thresholds, counts, and hashes.
- [x] Verify remote staging identity and create draft-only handoffs with race checks.
- [x] Protect new policy files; separate publisher permissions from candidate execution.
- [x] Fix test-impact deletion/import handling and selector/corpus/subset binding.
- [x] Fix projected inventories, dashboard validation/deduplication, and concurrent journaling.
- [x] Add counterexample regressions and run live scanner contracts.
- [ ] Complete final committed-tree verification and open corrective PR.

## Affected Files
- `scripts/` — reviewed gate, worker, staging, sync and telemetry implementations.
- `.github/workflows/` — read-only candidate jobs and trusted metadata workflows.
- `tests/test_review_regressions.py` and existing contract tests.
- `.docs/runbooks/review-remediation.md` — compatibility and activation requirements.

## Exit Conditions
- [x] Reviewed false-pass inputs fail deterministically.
- [x] Candidate execution cannot receive the PR-comment write token.
- [x] Missing host teardown/trace/artifact evidence is not considered success.
- [ ] Exact committed-tree suite and CI diagnostics verified.
- [ ] Platform activation independently verified before claiming mandatory enforcement.

## Required Documentation (Closure Law)
- [x] `CHANGELOG.md` updated.
- [x] `.docs/function-catalog.md` updated for changed signatures.
- [N/A] SDD kit: decisions recorded in the remediation runbook; no SDD kit exists.
- [x] `README.md` updated for user-visible contract changes.
- [x] `.agents/continuity-codex.md` updated.
- [ ] Tests passing on the final committed candidate.
- [N/A] Route map: CLI tooling only.
- [ ] PR approved; task remains in progress until independent approval.

## Honest Backlog
- Platform activation requires reviewed default-branch workflows, an approved
  immutable policy pin and mandatory GitHub protections. These are not yet
  active and must not be simulated by candidate-side code.
- Homelab remains quarantined until an actual isolated launcher, trusted trace
  observer and host teardown adapter are demonstrated. Local subprocesses and
  contract-test stubs are not OS isolation.
- Actual frontend Playwright production remains consumer-repository work.
- Final committed-tree tests and PR checks are recorded after commit; required
  human/policy/worker evidence is not bypassed to turn admission green.
