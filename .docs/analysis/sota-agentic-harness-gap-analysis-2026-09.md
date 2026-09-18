# SOTA agentic harness gap analysis — 2026-09

## Executive result

The repository has an unusually strong deterministic evidence core for an
agentic coding harness: diff risk, static scanners, exact-tree integration,
receipt identity, conservative test-impact analysis, worker-boundary contracts,
and explicit human checkpoints. The missing pieces are mostly at the boundary
between “a contract exists” and “an independent system enforces and measures
it.”

The new `scripts/sota_audit.py` turns this distinction into a repeatable local
and CI benchmark. Its score is a maturity signal, not a merge decision.

## Ranked gaps

| Rank | Gap | Why it matters | Suggested next bounded task |
|---:|---|---|---|
| P0 | Protected policy and independent producer activation | Candidate-authored receipts are consistency evidence until an independently protected caller, policy pin and reviewer identity exist. | Activate only after platform settings and protected identities are available; negative-test deletion, stale review, forged check and pin removal. |
| P0 | Cryptographic provenance and SBOM | SHA-bound JSON is not SLSA/in-toto provenance and scanner output is not an SBOM or release attestation. | Generate an SPDX/CycloneDX SBOM and attest a release artifact; verify subject digest, workflow, source SHA and builder identity. |
| P1 | Hermeticity and environment parity | Archive-based clean-room execution still inherits host assumptions and installs unpinned dependencies. | Pin dependencies/toolchain image, constrain network, emit environment fingerprints and compare hosted/Windows/disposable-worker runs. |
| P1 | Flaky-test governance | A single pytest run has no historical flake rate, quarantine owner/expiry, or “quarantined is not green” policy. | Add deterministic test IDs/seeds, bounded diagnostic reruns, quarantine metadata, expiry gate and recovery metrics. |
| P1 | Production-grade TIA history | The selector and holdout benchmark are conservative, but there is no per-test result listener/selector history, freshness SLO or lag alert. | Extend the local journal with per-test result events, staleness metrics and replayable selector inputs before any promotion. |
| P1 | Operational observability | Local reports are useful but there is no durable export, queue-age alerting or correlation of flakes, worker leaks, policy failures and escaped defects. | Define versioned events and OpenTelemetry-compatible export; add queue, lag, failure and worker SLOs. |
| P1 | Visual consumer activation | The receipt contract is present; protected browser image, baseline storage and a real CI consumer remain external. | Approve one private consumer, pin browser/OS/font image and run a protected baseline workflow. |
| P1 | Merge/deploy safety | There is no merge-group check, post-deploy health gate, last-known-good artifact or rollback drill in this coordination repo. | Add consumer-side merge-group/health/rollback contract and a dry-run rollback evidence producer. |

## What is already ahead of common public practice

- A deterministic closure law and CI-blocking evidence model instead of only
  agent self-reported “done” checklists.
- Risk classification that treats edits to the gate definitions themselves as
  high risk.
- Exact base/head identity through scanners, receipts, integration and impact
  evidence.
- A conservative TIA policy that falls back to the full suite and measures
  precision/recall before promotion.
- Explicit separation between candidate evidence, trusted admission and human
  review, including a checkpoint before staging for high-impact changes.

## SOTA signals used

- Anthropic's September 2026 report describes a deterministic listener/selector
  architecture, stale-history risk and the need to design for large increases
  in CI volume: https://claude.com/blog/agentic-coding-is-straining-ci-heres-how-we-scaled-test-impact-analysis-at-anthropic
- SLSA defines provenance completeness, authenticity, unforgeability and
  ephemeral build isolation as separate properties:
  https://slsa.dev/spec/v1.0/requirements
- GitHub artifact attestations bind artifacts to workflow, repository, commit,
  environment and event, and can carry SBOM attestations:
  https://docs.github.com/en/actions/concepts/security/artifact-attestations
- GitHub merge queues require `merge_group` checks to be reported, otherwise
  required status checks can block the queue:
  https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/managing-a-merge-queue
- OpenTelemetry publishes CI/CD semantic conventions for spans, metrics and
  logs, giving the operational layer a standard vocabulary:
  https://opentelemetry.io/docs/specs/semconv/cicd/
- Bazel's hermeticity guidance treats host isolation, source identity and
  reproducibility as prerequisites for safe caching and remote execution:
  https://bazel.build/concepts/hermeticity

## Boundary

No static audit can prove GitHub ruleset state, signing-key protection,
reviewer independence, homelab network isolation, or successful teardown on a
real host. Those require separately captured operational evidence and must
remain blocked until the evidence exists.
