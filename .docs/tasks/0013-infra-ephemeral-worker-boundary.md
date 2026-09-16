---
status: in_progress
priority: P0
type: infra
created: 2026-09-16
updated: 2026-09-16
clickup_id: null
parent: 0012
blocks: []
blocked_by: []
---

# 0013 — infra: ephemeral worker and credential boundary

## Context
Tasks 0010–0012 make integration and ultrareview execution evidence-carrying,
but the worker is still a deployment responsibility. The homelab is valuable
because it has Docker and can run the scanners and isolated agent workers, yet
it also hosts confidential automation credentials. Persistent self-hosted
runners are therefore not an acceptable default for public-repository code.

## Problem
Routing trusted events to a shared homelab label is only safe if each worker is
single-use, has no host application credentials, cleans its workspace, and
cannot be selected for fork-controlled code. The current runbook identifies
these requirements but does not provide an explicit trust matrix, preflight,
rotation procedure, or operational acceptance checklist.

## What To Do
- [x] Define the event/repository trust matrix: fork PRs stay GitHub-hosted;
      trusted same-repo validation may use the pool; protected deployment jobs
      require a separate environment policy.
- [x] Define the ephemeral worker lifecycle, registration-token handling,
      cleanup, isolation, and failure/revocation procedure without storing
      secrets in the repository.
- [x] Define measurable pool SLOs and evidence fields: queue wait, worker age,
      single-job exit, cleanup result, host capacity, and mounted secret count.
- [x] Update the homelab runbook with a preflight checklist and an explicit
      "do not enable" condition for persistent workers on public PR jobs.
- [ ] Execute the homelab registration/migration commands and verify one
      real ephemeral job; requires the host-side operator step.

## Affected Files
- `.docs/runbooks/homelab-runner-pool.md`
- `.docs/tasks/0013-infra-ephemeral-worker-boundary.md`
- `README.md`
- `CHANGELOG.md`
- `.agents/continuity-codex.md`

## Exit Conditions
- [x] Fork PRs cannot route to the homelab pool in the workflow policy.
- [x] Runbook documents ephemeral/JIT lifecycle, credential boundary, cleanup,
      revocation, and measurable acceptance criteria.
- [x] No credentials or confidential repository content are added to the repo.
- [ ] At least one ephemeral worker is registered and observed completing a
      clean-room job on the homelab.
- [ ] PR approved — remains `in_progress` until review, per Closure Law.

## Required Documentation (Closure Law)
- [x] `CHANGELOG.md` updated
- [N/A] `<function_catalog>` — documentation-only task
- [N/A] `<sdd_kit_path>` — no SDD_KIT.md in this repo
- [x] `README.md` updated
- [x] `.agents/continuity-codex.md` updated
- [x] Tests passing / workflow YAML parse
- [N/A] `<route_map>` — no web routes in this repo
- [ ] PR approved

## Honest Backlog
- GitHub User accounts do not have organization runner groups; the current
  uniform-label pool remains per-repository registration until an organization
  migration is chosen.
- The host-side commands are intentionally not automated from this repo: they
  require a short-lived registration token and access to a machine with
  confidential services. Execute them manually after reviewing the checklist.
- Ephemeral process cleanup is necessary but not sufficient for hostile code;
  a dedicated VM or stronger container policy is the next isolation tier.
