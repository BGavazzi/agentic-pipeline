---
status: in_progress
priority: P0
type: feat
created: 2026-09-17
updated: 2026-09-17
clickup_id: null
parent: null
blocks: []
blocked_by: []
---

# 0043 — Trusted policy evidence and review lifecycle (handoff W1)

## Context
The maintainer authorized the next handoff packet after merging the corrected
stack in PR #45. This is one bounded PR, not an autonomous expansion into W2–W7.

## Problem
CI inferred early approval from workflow-run PR associations, never consumed a
protected policy producer, and could retain approval after review dismissal.
Candidate-local policy diagnostics could not represent an independently approved
policy change. No producer had an artifact/run/attempt verification envelope.

## What To Do
- [x] Implement v1 metadata-only policy envelope with GitHub API verification.
- [x] Bind PR/base/head/tree, policy SHA, workflow, run/attempt and artifact digest.
- [x] Reject stale approval, self/bot approval, objections and old successful runs.
- [x] Add read-only pinned producer with explicit controlled refresh after review.
- [x] Consume verified policy in routing and recheck immediately before aggregation.
- [x] Keep candidate inventory diagnostic only; never substitute it for approval.
- [x] Test Python adapter and actual early-review JavaScript with offline events.
- [ ] Verify committed candidate and hosted PR diagnostics.

## Affected Files
- scripts/trusted_policy.py and scripts/blast_radius.py
- .github/workflows/{ci,early-review,trusted-policy}.yml
- tests/test_trusted_policy.py
- .docs/runbooks/protected-policy-workflow.md

## Exit Conditions
- [x] Wrong/replayed/tampered evidence blocks; no stale-success fallback.
- [x] Ordinary change can proceed without human approval in offline fixtures.
- [x] Elevated change requires current independent authorized exact-head review.
- [x] Review dismissal and base/head movement invalidate producer evidence.
- [ ] Final committed tests and CI diagnostics recorded.
- [ ] Independent review and real pinned-producer pilot before activation claims.

## Required Documentation (Closure Law)
- [x] CHANGELOG updated.
- [x] FUNCTION_CATALOG updated for public CLI/contracts.
- [N/A] SDD_KIT: activation decision recorded in existing policy runbook.
- [x] README updated with the producer/consumer path.
- [x] CONTINUITY updated.
- [ ] Tests passing on final committed candidate.
- [N/A] ROUTE_BEHAVIOR_MAP: no web routes.
- [ ] PR approved.

## Honest Backlog
- No repository variables, required rules, reviewer identities or homelab state
  were changed. The producer is dormant until an approved full-SHA pin exists.
- Final required admission must run protected code outside candidate ownership.
  This PR verifies the policy producer and improves diagnostic orchestration; it
  does not authenticate the other candidate-produced test/scanner receipts.
- Controlled refresh is manual, not a review-event privileged workflow. Live
  GitHub envelope/artifact/rerun behavior remains a pilot acceptance condition.
- Metadata-only policy observes the candidate tree, never claims execution.
  Integration/reviewer/worker provenance is W2/W3 work, not fabricated here.
- Shared human/agent GitHub credentials cannot prove human approval. A genuinely
  independent identity/surface and effective required controls remain decisions.
