---
status: in_progress
priority: P0
type: feat
created: 2026-09-18
updated: 2026-09-18
clickup_id: null
parent: 0057
blocks: []
blocked_by: []
---

# 0059 — Feature: tag-only release provenance and SBOM

## Context
The harness has commit-bound receipts and pinned scanner images, but these are
not cryptographic artifact provenance. SLSA and GitHub artifact attestations
separate release artifacts from routine test runs and bind the artifact to the
workflow, source commit and builder.

## Problem
Consumers cannot currently verify that a published harness archive came from a
tagged source commit or inspect its dependency inventory. Attesting every PR
test output would add noise and would not establish a release boundary.

## What To Do
- [x] Add a deterministic local provenance contract binding archive, SBOM,
      source SHA, workflow ref, event and semantic-version tag.
- [x] Add fail-closed artifact/SBOM digest verification tests.
- [x] Add a tag-only GitHub workflow using pinned official actions/SHAs,
      SPDX SBOM generation and `actions/attest`.
- [x] Keep permissions scoped to contents read, OIDC, attestations and artifact
      metadata; do not expose credentials to build steps beyond GitHub's action.
- [ ] Verify one real tag attestation with `gh attestation verify` after PR
      approval; the workflow is not a release claim until that happens.

## Affected Files
- `scripts/provenance_verify.py`
- `tests/test_provenance_verify.py`
- `scripts/core_sync.py`, `scripts/blast_radius.py`
- `.github/workflows/release-provenance.yml`
- `README.md`, `CHANGELOG.md`, `.docs/function-catalog.md`

## Exit Conditions
- [x] Local contract rejects wrong event, tag, source SHA, SBOM format or
      artifact/SBOM tampering.
- [x] Tag-only workflow is fail-closed before attestation and uses pinned action
      revisions.
- [x] No routine PR workflow emits a release attestation.
- [x] Tests and closure validators pass.
- [ ] A real release attestation is verified after human approval.
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
This adds a release boundary but does not make a consumer verify attestations,
does not sign ordinary CI receipts, and does not prove the homelab is a trusted
builder. `gh attestation verify` must be exercised on a real tag before this
task can be considered operationally complete.
