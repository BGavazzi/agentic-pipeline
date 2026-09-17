---
status: in_progress
priority: P0
type: infra
created: 2026-09-17
updated: 2026-09-17
clickup_id: null
parent: null
blocks: []
blocked_by: []
---

# 0044 — External worker sandbox and observation contract (handoff W2)

## Context
W1's trusted policy path is in PR #46. The next bounded slice makes the worker
boundary explicit without registering a homelab runner or touching host state.

## Problem
The supervisor checked lifecycle facts but did not require a concrete external
sandbox contract. A self-hosted adapter could report ephemeral status while
retaining host mounts, Docker socket access, broad network, credentials, weak
resource limits, or candidate-owned observations.

## What To Do
- [x] Validate container/VM isolation, no host mounts/socket/privilege.
- [x] Require explicit deny/allowlist network and single-job registration scope.
- [x] Require trusted-host ownership for launcher/observer/cleanup and host API receipt.
- [x] Require resource limits, disposable workspace and destroy/revoke on every outcome.
- [x] Block the supervisor before launch when required attestation is absent/invalid.
- [x] Bind the optional boundary contract into meta-test dispatch interfaces.
- [ ] Run final suite, exact integration and scanner verification.
- [ ] Demonstrate a real disposable worker pilot; this is operator work, not this PR.

## Affected Files
- `scripts/worker_boundary.py`, `scripts/worker_supervisor.py`, `scripts/meta_test_dispatch.py`
- `scripts/{core_sync,policy_integrity,blast_radius}.py`
- `tests/test_worker_boundary.py`
- `.docs/runbooks/homelab-runner-pool.md`

## Exit Conditions
- [x] Unsafe attestation and absent required boundary block before candidate launch.
- [x] Valid synthetic attestation records bounded metrics and lifecycle evidence.
- [x] Existing compatibility paths remain available unless boundary is explicitly required.
- [ ] Final committed tests and CI diagnostics recorded.
- [ ] Real host adapter independently verified before enabling homelab routing.

## Required Documentation (Closure Law)
- [x] CHANGELOG updated.
- [x] FUNCTION_CATALOG updated.
- [N/A] SDD_KIT: no architectural decision file; boundary rationale is in runbook.
- [x] README updated.
- [x] CONTINUITY updated.
- [ ] Tests passing on final committed candidate.
- [N/A] ROUTE_BEHAVIOR_MAP: no web routes.
- [ ] PR approved.

## Honest Backlog
- This contract validates external attestations; it cannot inspect or secure a host
  when the adapter itself is compromised. The adapter must be independently owned.
- No runner registration, token minting, Docker socket access, SSH, homelab mutation,
  secrets, or confidential repository access occurred.
- A container without a trusted runtime boundary is not automatically safe. Verify
  rootless/VM mode, filesystem/network policy and credential revocation in a pilot.
- W3 still needs independently observed builder/reviewer producers and receipt wiring.
