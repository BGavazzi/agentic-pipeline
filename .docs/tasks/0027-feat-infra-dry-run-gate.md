---
status: in_progress
priority: P0
type: feat
created: 2026-09-16
updated: 2026-09-16
clickup_id: null
parent: 0002
blocks: []
blocked_by: []
---

# 0027 — feat: implement the infrastructure dry-run gate

## Context
The blast-radius classifier has required `infra-dry-run` for Terraform,
Ansible, Helm, Fleet, Rancher, and Nexus-shaped changes since task 0002, but
the producer was only an honest backlog item. This left high-risk
infrastructure candidates permanently unable to satisfy admission.

## Problem
Infrastructure validation is provider- and repository-specific, so the core
must not guess a cloud command or run shell text. It needs to detect the
obligation, require an explicit argv profile, execute that profile against the
committed candidate in isolation, and make missing tooling/profile evidence
non-admissible.

## What To Do
- [x] Add `infra_dry_run.py` with infrastructure-path detection and exact
      base/head identity.
- [x] Run explicit dry-run profiles without a shell in a clean git-archive
      workspace with timeout and bounded metrics.
- [x] Emit `not_applicable` for ordinary code and fail closed for infra changes
      without a profile.
- [x] Aggregate applicable receipts into `infra-dry-run` admission evidence.
- [x] Wire the producer into CI artifacts and the canonical high-risk sync
      surface.
- [x] Add deterministic tests for no-op, missing profile, pass, fail, and
      stale/invalid input behavior.

## Affected Files
- `scripts/infra_dry_run.py`
- `scripts/ci_receipts.py`
- `scripts/core_sync.py`
- `scripts/blast_radius.py`
- `scripts/policy_integrity.py`
- `.github/workflows/ci.yml`
- `tests/test_infra_dry_run.py`
- `tests/test_ci_receipts.py`

## Exit Conditions
- [x] Infrastructure changes cannot become admitted without a passing dry-run
      profile.
- [x] Ordinary code changes do not gain a false infra blocker.
- [x] Candidate code is not executed from the dirty checkout.
- [x] Receipt identity is bound to exact base/head SHAs.
- [x] Tests, workflow parsing, and repository validators pass.

## Required Documentation (Closure Law)
- [x] `CHANGELOG.md` updated
- [N/A] `function-catalog.md` — no function catalog exists
- [N/A] `SDD_KIT.md` — no new product decision
- [x] `README.md` updated
- [N/A] `.agents/continuity-<agent>.md` — no continuity file in this checkout
- [x] Tests passing
- [N/A] `ROUTE_BEHAVIOR_MAP.md` — no route/handler/model change
- [ ] PR approved

## Honest Backlog
- The core does not ship provider-specific Terraform/Helm/Ansible profiles.
  Each infrastructure consumer must provide a reviewed argv profile and
  pinned tool/container image.
- A future task should add a profile manifest with tool-version metrics and
  homelab execution policy; this gate intentionally refuses to invent one.
