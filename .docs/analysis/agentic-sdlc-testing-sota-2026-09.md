# Agentic SDLC testing SOTA — 2026-09-18

## Executive finding

The state of the art is no longer “run the unit suite after an agent edits
code.” The strongest public and first-party systems combine four properties:

1. **Continuous feedback** inside the agent loop, before human review.
2. **Deterministic, hermetic execution** with exact source/environment
   identity and reproducible artifacts.
3. **Independent evaluation** of both the code and the agent configuration
   that produced it.
4. **Risk-weighted human accountability**: routine work can be automated, but
   security, invariants, policy, and uncertain evidence escalate early.

Our current harness has the right evidence-first shape and now has a local
merge/bundle loop, but it is still a local producer rather than a horizontally
scaled evaluation service or a protected admission system.

## Primary-source signals

### 1. CI must scale as agent throughput scales

Anthropic reports a 25x increase in CI job volume over six months and describes
rebuilding test-impact analysis as a horizontally scalable service rather than
continuing to patch a bottleneck. The implication is architectural: test
selection needs durable history, bounded latency, clear fallback behavior, and
capacity metrics—not only a static changed-file heuristic.

Source: [Anthropic — scaling test impact analysis](https://claude.com/blog/agentic-coding-is-straining-ci-heres-how-we-scaled-test-impact-analysis-at-anthropic)

### 2. Agent configuration is production code

Anthropic's AI-native SDLC guidance runs continuous evals when `CLAUDE.md`,
skills, or hooks change; recommends 20–50 representative tasks; and turns
production incidents into permanent regression cases. It also describes
independent agent reviews, proofs for findings, invariant-focused checks, and
risk-weighted human sampling.

Sources: [AI-native SDLC playbook](https://claude.com/blog/the-ai-native-sdlc-playbook),
[secure AI-native SDLC](https://claude.com/blog/how-anthropic-secures-its-ai-native-software-development-lifecycle),
[skill evals](https://claude.com/blog/improving-skill-creator-test-measure-and-refine-agent-skills)

### 3. Evaluation must be reproducible and multi-dimensional

OpenHands' public benchmark repository covers issue resolution, long-horizon
software engineering, greenfield implementation, safety, and program
reconstruction. It pins the Agent SDK as a git submodule and publishes
evaluation infrastructure rather than only leaderboard numbers. The OpenHands
Index additionally reports traces and cost/quality dimensions.

Sources: [OpenHands Benchmarks](https://github.com/OpenHands/benchmarks),
[OpenHands Index](https://openhands-openhands-index.hf.space/testing)

### 4. Correctness is an executable repository-level oracle

SWE-bench evaluates generated patches against repository tests and emphasizes
complete, re-derived execution artifacts. That is useful, but current research
also documents benchmark unreliability from reward hacking and broken or
mis-scoped tasks. A mature harness therefore audits its own benchmark cases,
tracks oracle quality, and does not equate test pass with semantic correctness.

Sources: [SWE-bench experiments](https://github.com/SWE-bench/experiments),
[SWE-Bench Pro reliability analysis](https://arxiv.org/abs/2609.08149)

### 5. Browser and visual behavior need first-class environments

BrowserGym provides reusable browser environments and benchmarks including
WebArena, VisualWebArena, WorkArena, and MiniWoB; AgentLab supplies a common
evaluation layer. This is materially different from storing screenshot prose:
the environment, task, browser version, viewport, seed, artifacts, and oracle
must be bound to the receipt.

Source: [ServiceNow BrowserGym](https://github.com/ServiceNow/BrowserGym)

### 6. Hermeticity is a correctness property, not just an optimization

Bazel's test specification requires tests to depend only on declared source,
declared products, and runner-guaranteed stable resources. Its hermeticity
guidance recommends isolation, pinned tools, strict sandboxing, and testing for
host-environment leakage. Our current environment fingerprint and disposable
archive are useful evidence, but they do not yet prove network/toolchain
hermeticity.

Sources: [Bazel hermeticity](https://bazel.build/concepts/hermeticity),
[Bazel test encyclopedia](https://bazel.build/reference/test-encyclopedia)

### 7. CI quality needs a standard telemetry vocabulary

OpenTelemetry's CI/CD semantic conventions define common spans, metrics, and
logs. Our local OTLP-shaped file is directionally compatible, but queue age,
worker saturation, selector latency, retry/flake rates, and human-review delay
still need a durable collector and SLOs.

Source: [OpenTelemetry CI/CD semantic conventions](https://opentelemetry.io/docs/specs/semconv/cicd/)

## Proposed agentic-quality framework

The novel part should be the **evidence graph**, not another autonomous merge
bot. Every candidate produces a versioned packet:

```text
intent/spec → diff → risk/contact surfaces → selected tests → exact tree
→ environment/worker identity → test + scan + visual + agent-eval receipts
→ independent review → admission decision → human bundle → post-merge outcome
```

Each edge must carry exact `base_sha`, `head_sha`, policy/config hash, runner
fingerprint, test-selection version, agent/model identity, duration, cost, and
artifact digests. Missing or stale edges are `blocked`, never inferred as
green.

### Gate families and measurements

| Family | Deterministic gates | Core measurements |
|---|---|---|
| Correctness | unit, integration, contracts, clean-room | pass rate, duration, changed-test regret, oracle coverage |
| Test selection | impact selector + full-suite sentinel | precision, recall, fallback rate, selector latency |
| Security | SAST, SCA, secrets, fork/credential boundary | findings, false-negative tests, secret exposure, forbidden-route count |
| Risk | blast radius, contact surfaces, policy-file detection | risk tier, affected modules, acute hold rate |
| Agent behavior | fixture evals, meta-tests, policy adherence | task pass rate, repair rate, tool violations, cost, tokens, intervention rate |
| UX | Playwright/Storybook/visual receipt | pixel diff, viewport/browser identity, baseline age, visual flake rate |
| Reproducibility | environment fingerprint, hermetic runner, provenance | replay success, cache variance, host-leak count, artifact digest match |
| Operations | queue, worker, telemetry, rollback | p50/p95 queue age, worker utilization, retry/flake rate, rollback readiness |
| Human accountability | independent review, risk-weighted sampling | review latency, sampled escape rate, disagreement rate, override reasons |

### Admission rules

- **Routine**: all required deterministic evidence is fresh and exact-tree
  integration passes; eligible for a local survivor bundle.
- **Uncertain**: missing, stale, degraded, flaky, or non-hermetic evidence;
  no automatic promotion.
- **Acute**: security/identity, data/schema, infrastructure, CI/policy,
  fork-origin, invariant, or wide-blast-radius change; surface to a human
  before execution where possible.
- **Post-merge sampling**: automatically sample low-risk automated decisions
  for human review. Automation must not lower the accountability denominator.

## Gap map against this repository

### Present or substantially present

- Deterministic task/closure, risk, scanner, receipt, admission, clean-room,
  worker preflight/supervision, visual receipt, provenance, flake, JUnit,
  telemetry, merge-group, and release-health contracts.
- Local disposable multi-candidate integration with risk/contact metrics,
  fork quarantine, stateful bounded rounds, and human-review bundles.
- Deterministic intent/authorization evidence now checks exact diff scope,
  forbidden effects, data classes, and sensitive negative tests; protected
  producer identity and admission consumption remain external.
- Versioned SOTA capability audit that separates repository evidence from
  external activation facts.

### Still behind SOTA

1. **Scaled test-impact service** — current selector is conservative and local;
   no durable per-test history service, shard scheduler, selector SLO, or
   large-volume load test.
2. **Agent-eval corpus** — meta-test fixtures exist, but there is no maintained
   20–50-task representative corpus, model/config matrix, cost tracking, or
   incident-to-eval promotion workflow.
3. **Mutation/invariant testing** — ordinary tests do not quantify whether
   changed behavior is actually discriminated; high-value invariants need
   executable negative tests and mutation score evidence.
4. **Protected visual producer** — the core receipt exists, but generic
   Playwright/Storybook execution, pinned browser images, baseline ownership,
   and baseline freshness are consumer-side gaps.
5. **Hermetic execution** — dependency pins and fingerprints exist, but network
   policy, declared inputs, toolchain image identity, and host-leak tests are
   not fully enforced.
6. **Trusted control plane** — protected policy identity, independent reviewer
   identity, merge-queue activation, JIT worker observation, telemetry
   collectors/SLO alerts, deploy health, and rollback remain external.
7. **Benchmark integrity** — add task-quality audits, contamination checks,
   reward-hacking fixtures, and oracle mutation tests before interpreting agent
   scores as quality.

## Recommended next implementation queue

1. Build a versioned agent-eval corpus runner with 20–50 local fixtures,
   config-change triggers, cost/token/latency metrics, and incident promotion.
2. Add selector-regret and load benchmarks: compare impacted mode with the full
   suite, measure precision/recall/latency, and block promotion on missed tests.
3. Add invariant/mutation fixtures for security, authorization, schema, and
   policy changes.
4. Add a local review-inbox/index adapter that preserves deduplicated bundles,
   acknowledgements, reviewer disposition, and risk-weighted sampling without
   sending confidential code off-machine.
5. Activate protected infrastructure separately: ephemeral homelab workers,
   immutable policy producer, OTel collector/SLOs, and deploy rollback.

The first four are implementable in this repository. The fifth requires
operator-controlled infrastructure and must not be simulated by a local script.

## Implementation delta after the initial research pass

The following local contracts are now implemented and dogfooded in the stacked
2026-09-18 work:

- the agent-eval corpus reports readiness, baseline regression, latency,
  tokens/cost, and configuration identity, while refusing to call an
  undersized corpus a pass;
- test-impact benchmarking reports selector regret, fallback rate, p95 case
  latency, and bounded repeated-corpus throughput;
- trusted policy verification binds exact base/head, immutable policy pin,
  exact-head independent review, and protected producer/run attestation;
- receipt history is hash-chained and replay-verifiable;
- visual evidence can bind to a protected baseline ref/digest, threshold, and
  browser image; the real producer remains a separate frontend/runtime concern;
- self-hosted worker preflight now requires explicit verified network-policy
  facts in addition to ephemeral, clean, secret-free lifecycle facts;
- KPI reports can be reduced to versioned deterministic numeric vectors and
  retained as append-only snapshots with long-run mean, variance, p95, and
  freshness metrics; the vector is not a semantic embedding and has no
  admission authority;
- admission mutation score and metadata-only PR topline metrics are now part of
  the local/CI evidence path.
- intent/authorization evidence now binds an agent-declared boundary to the
  exact changed tree; it remains explicitly untrusted until protected CI and
  admission consume it.

### Important visual-regression boundary

The generic core currently contains the receipt validator and protected-baseline
binding. The runnable Playwright-style producer is in the separate stacked
feature line [PR #49](https://github.com/BGavazzi/agentic-pipeline/pull/49), and
the only confirmed portfolio-native production consumer remains PortalApp's
Chromatic/Storybook setup. No claim of a protected browser fleet, baseline
ownership, or approved frontend pilot should be made until that external
activation is reviewed.

### Remaining SOTA gaps

The residual gaps are mostly deployment-owned: protected intent-policy
authority and admission wiring, a 20–50-case representative agent-eval
corpus, durable cross-run TIA history/sharding, protected/JIT homelab
observation, immutable policy producer identity, pinned browser and toolchain
images, OTel collection/SLO alerts, merge-queue activation, and post-deploy
rollback observation. These are intentionally represented as blocked/partial
evidence in `sota_audit.py`, not simulated as local passes.
