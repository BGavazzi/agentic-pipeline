# Changelog

Format: newest entry on top. Never delete or rewrite past entries (typos excepted).

## [2026-09-18] - Add deterministic intent and authorization evidence (task 0081)
### Added
- `intent_gate.py` validates declared path scope, forbidden paths/effects,
  allowed data classes, sensitive negative tests, and exact base/head identity.
- The SOTA capability audit now reports intent authorization separately as
  partial until protected producer and admission wiring exist.
### Safety
- Intent reports are evidence-only and explicitly untrusted until a protected
  producer and admission integration consume them.
**Author**: Codex (agent); pending independent review.

## [2026-09-18] - Productize multi-base integration queue processing (task 0080)
### Added
- `integration_queue.py` discovers the open PR queue once, groups candidates by
  their declared base, delegates each group to the disposable local producer,
  and emits aggregate JSON/Markdown evidence for the staging gate.
### Safety
- Unresolved bases become explicit human-review holds; the adapter performs no
  remote merge, approval, push, deploy, or staging PR creation.
**Author**: Codex (agent); pending independent review.

## [2026-09-18] - Harden integration queue identity and draft readiness (task 0079)
### Changed
- Local PR discovery now prefers remote-tracking heads and refreshes a moved
  head once through the read-only pull-ref API before identity validation.
- Draft PRs are carried through manifests and GitHub discovery, then held as
  `not_ready` before ref resolution or candidate execution.
### Safety
- The change preserves fail-closed identity checks and adds no remote write,
  merge, approval, deploy, or secret-forwarding capability.
**Author**: Codex (agent); pending independent review.

## [2026-09-18] - Refresh SOTA report with implementation delta (task 0078)
### Changed
- The SOTA report now records the shipped eval, selector, trust, visual,
  worker, KPI, mutation, and PR-summary contracts while preserving explicit
  external activation gaps.
**Author**: Codex (agent); pending independent review.

## [2026-09-18] - Surface deterministic quality metrics on PRs (task 0077)
### Changed
- Trusted PR summaries now show candidate/base identity, changed-file count,
  churn, deterministic HITL status, and contact surfaces above the diagnostics
  link, without checking out or executing candidate code.
**Author**: Codex (agent); pending independent review.

## [2026-09-18] - Add admission mutation benchmark (task 0076)
### Added
- A deterministic mutation score exercises missing, failed, stale, unknown,
  and removed-obligation admission evidence; the CI unit job now runs it.
### Safety
- Mutation output is descriptive correctness evidence and cannot authorize
  admission or skipped tests.
**Author**: Codex (agent); pending independent review.

## [2026-09-18] - Add versioned KPI vector history (task 0075)
### Added
- `kpi_history.py` stores compact numeric KPI vectors with input hashes and
  exact commit/run identity, then reports long-run variance, p95, freshness,
  and bounded-window statistics.
### Safety
- KPI vectors are descriptive telemetry only; raw logs are not retained by this
  layer and the vector cannot authorize admission or skipped tests.
**Author**: Codex (agent); pending independent review.

## [2026-09-18] - Require verified worker network policy (task 0074)
### Changed
- Self-hosted worker preflight now blocks unless host facts explicitly report
  a verified network policy; Docker reachability is not treated as isolation.
**Author**: Codex (agent); pending independent review.

## [2026-09-18] - Bind visual receipts to protected baselines (task 0073)
### Added
- Visual receipts can now require an independently supplied baseline policy
  binding the baseline ref, digest, threshold, and browser image provenance.
### Safety
- The core still does not launch Playwright; protected frontend production and
  baseline storage remain external prerequisites.
**Author**: Codex (agent); pending independent review.

## [2026-09-18] - Dogfood task and closure validator contracts (task 0072)
### Added
- Adversarial unit coverage for valid/invalid task schemas and advisory versus
  strict Task Closure Law behavior.
**Author**: Codex (agent); pending independent review.

## [2026-09-18] - Add tamper-evident receipt history (task 0071)
### Added
- Receipt journal events now carry chained digests over immutable identity and
  receipt payloads; summaries expose chain validity and break counts.
### Safety
- The chain is descriptive evidence only. It does not authorize skipped tests
  or replace protected archival and independent verification.
**Author**: Codex (agent); pending independent review.

## [2026-09-18] - Add fail-closed trusted-policy verification (task 0070)
### Added
- `scripts/trusted_policy.py` binds policy receipts, exact-head reviewer
  evidence, immutable policy pins, and protected producer attestations.
- Missing, stale, mismatched, or unprotected trust evidence is blocked rather
  than inferred as trusted.
### Safety
- The verifier is an adapter, not a trust oracle; protected workflow identity
  and deployment-owned immutable pins remain external prerequisites.
**Author**: Codex (agent); pending independent review.

## [2026-09-18] - Measure test-impact selector regret and bounded load (task 0069)
### Added
- `impact_benchmark.py` now reports per-case selection regret, selection ratio,
  duration, fallback rate, p95 case latency, and repeated-corpus throughput.
- The benchmark supports bounded `--iterations` runs for load calibration.
### Safety
- Benchmark identity is versioned and promotion rejects stale version `0.4`
  receipts; metrics remain observational and never authorize skipped tests.
**Author**: Codex (agent); pending independent review.

## [2026-09-18] - Add versioned agent-eval corpus metrics (task 0068)
### Added
- `scripts/agent_eval_corpus.py` summarizes meta-test cases with pass rate,
  corpus readiness, baseline regression, p50/p95 duration, token/cost totals,
  and a configuration digest without storing worker command contents.
- `meta_test.py` now removes secret and Git/SSH/Docker/Kubernetes control
  variables before launching agent workers.
### Safety
- Fewer than the configured minimum number of cases is
  `insufficient_corpus`, never `pass`; eval output is descriptive and cannot
  override admission.
**Author**: Codex (agent); pending independent review.

## [2026-09-18] - Document agentic SDLC testing SOTA and next queue (task 0067)
### Added
- `.docs/analysis/agentic-sdlc-testing-sota-2026-09.md` compares primary
  sources on scalable test-impact analysis, continuous agent evals, benchmark
  integrity, hermeticity, visual environments, telemetry, and human review.
- A metric-driven implementation queue separates local eval/test work from
  protected worker, policy, telemetry, and deployment activation.
**Author**: Codex (agent); pending independent review.

## [2026-09-18] - Add bounded local integration and human-review bundling (task 0066)
### Added
- `scripts/local_integration_loop.py` for disposable, one-candidate-at-a-time
  local merges, argv-only integration tests, risk/contact-surface routing, and
  JSON/Markdown bundles of routine survivors and acute-risk holds.
- Explicit credential-environment scrubbing, optional read-only PR-head fetch,
  GitHub base-branch normalization, worktree cleanup between candidates, and a
  no-remote-write policy receipt.
- Optional stateful, bounded rediscovery rounds skip only immutable heads that
  survived local integration; unresolved human-review holds remain visible and
  round metrics accumulate.
- Cross-repository/fork candidates are held before ref resolution, local fetch,
  merge, or execution, preventing untrusted fork code from entering the
  homelab/local lane.
- Candidate base-ref mismatches are held before resolution, and unexpected
  worker-launch exceptions restore the prior disposable merge state.
- Local synthetic commits disable repository hooks, and integration processes
  drop Git/SSH/Docker/Kubernetes control variables in addition to secrets.
### Safety
- High-risk, infrastructure, CI/workflow, harness-policy, schema and
  security/identity changes remain human-review holds before execution.
- Conflicts and failed integration commands are reverted in the disposable
  worktree; the tool cannot approve, push, merge remotely or deploy.
### Tests
- Added focused coverage for acute classification, routine inclusion, failed
  merge rollback, and deterministic candidate manifests.
**Author**: Codex (agent); pending independent review.

## [2026-09-18] - Add versioned SOTA harness capability audit (task 0057)
### Added
- `scripts/sota_audit.py` and CI evidence output for a deterministic,
  denominator-first capability benchmark covering correctness, security,
  agent evaluation, supply chain and operations.
- Explicit separation between repository evidence and external activation
  obligations; missing signatures, protected identities, ephemeral workers and
  rollback controls are never inferred from prose or placeholder files.
### Tests
- Added conservative classification and deterministic JSON/Markdown CLI tests.
**Author**: Codex (agent); pending independent review.

## [2026-09-18] - Add release health and rollback evidence contract (task 0065)
### Added
- `scripts/release_health_gate.py` for fail-closed health/check identity and
  distinct rollback-plan validation.
- Explicit evidence flags showing no trusted producer, command execution or
  admission authority.
### Safety
- The adapter never polls services or executes rollback commands; deployment
  provider integration remains a separately protected operational task.
**Author**: Codex (agent); pending independent review.

## [2026-09-18] - Add merge-group identity contract (task 0064)
### Added
- Explicit `merge_group` CI trigger and a fail-closed event identity contract
  for merge-queue base/head SHAs and refs.
- Non-authoritative contract artifact listing expected merge-group checks.
### Safety
- The contract never claims check completion, merge authorization, deployment
  health or rollback; protected control-plane activation remains external.
**Author**: Codex (agent); pending independent review.

## [2026-09-18] - Add provider-neutral CI telemetry evidence (task 0063)
### Added
- `scripts/ci_telemetry.py` and CI evidence output for file-only OTLP-shaped
  numeric metrics derived from scorecard and PR-intelligence reports.
- Commit/run identity, report labels and explicit network-export-disabled policy.
### Safety
- Telemetry is descriptive and cannot compensate for failed admission evidence;
  collectors, queue SLOs and external export remain protected deployment work.
**Author**: Codex (agent); pending independent review.

## [2026-09-18] - Normalize JUnit into per-test history evidence (task 0062)
### Added
- `scripts/junit_history.py` with fail-closed parsing for common JUnit XML,
  exact candidate identity, per-test statuses, durations and report digest.
- CI upload of normalized unit-test evidence on both passing and failing runs.
### Safety
- The adapter is descriptive only. It cannot retry, skip, select or authorize
  tests; durable cross-run history and TIA promotion remain separate controls.
**Author**: Codex (agent); pending independent review.

## [2026-09-18] - Add pinned CI environment evidence (task 0060)
### Added
- `requirements-ci.txt` with exact pytest, PyYAML and Pillow pins.
- `scripts/environment_fingerprint.py` and CI evidence for dependency/runtime
  drift, with no secret or credential values captured.
### Safety
- This is a parity contract, not a claim of full hermeticity; OS images,
  network policy, browser/font stacks and homelab isolation remain separate.
**Author**: Codex (agent); pending independent review.

## [2026-09-18] - Add explicit flaky-test governance (task 0061)
### Added
- `scripts/flake_gate.py` and tests for owner/expiry quarantine evaluation
  over per-test history.
- `degraded` state for active quarantines; expired and unowned flakes block.
### Safety
- Quarantine never becomes a green admission result, and the gate does not
  silently retry tests or mutate the manifest.
**Author**: Codex (agent); pending independent review.

## [2026-09-18] - Add tag-only release provenance and SBOM (task 0059)
### Added
- `scripts/provenance_verify.py` to bind a release archive and SPDX/CycloneDX
  SBOM to source, workflow, event and semantic-version tag identity.
- `.github/workflows/release-provenance.yml` for pinned, tag-only GitHub
  artifact/SBOM attestations.
### Safety
- The local contract fails closed on identity or digest mismatch. Routine PR
  runs do not create release attestations.
**Author**: Codex (agent); pending independent review.

## [2026-09-18] - Add per-test history metrics for TIA (task 0058)
### Added
- Extended the append-only journal with idempotent per-test result events and
  explicit `test-result-append` / `test-result-summary` CLI contracts.
- Added denominator-first freshness, stale-test, flaky-test, latest-status and
  duration metrics with an explicit reference timestamp.
### Safety
- History remains descriptive telemetry. It cannot replace the full suite or
  authorize test skipping before a separately validated promotion policy exists.
**Author**: Codex (agent); pending independent review.

## [2026-09-16] - Repair reviewed evidence and trust boundaries (task 0042)
### Fixed
- Preserve scanner vetoes; require commit-bound unit receipts and execute exact
  candidate/base merge trees instead of labeling arbitrary HEAD execution.
- Strict worker facts, fresh host teardown and independent meta-test observations;
  quarantine unverified homelab routing and separate PR publisher permissions.
- Remote staging identity, draft-only handoff, visual artifact/hash consistency,
  complete policy surfaces and exact-head protected review.
- Conservative TIA deletion/import handling and benchmark/subset binding;
  truthful sync inventories, deduplicated metrics and atomic journal retries.
### Added
- Adversarial review regressions and a platform activation runbook. Actual branch
  protection, independent approval and homelab isolation remain deployment gates,
  not claims inferred from unit tests.
**Author**: Codex (agent); pending independent review.

## [2026-09-16] - Add append-only local quality receipt journal (task 0041)
### Added
- `scripts/receipt_journal.py` stores immutable receipt events in SQLite WAL,
  making identical retries idempotent and conflicting event IDs an error.
- Replayable summaries expose event counts, candidate pairs, statuses and time
  range without turning telemetry into an admission decision.
**Author**: Codex (agent); pending human review.

## [2026-09-16] - Add denominator-first quality metrics dashboard (task 0040)
### Added
- `scripts/quality_metrics_dashboard.py` aggregates PR-intelligence receipts
  into JSON and Markdown risk, HITL, evidence, churn and test-impact metrics.
- Small cohorts are labeled calibration-only, invalid receipts remain counted,
  and limitations are explicit; the dashboard cannot override admission.
### Changed
- PR intelligence now exposes required-gate count and evidence completeness
  so aggregate measurements retain their denominators.
**Author**: Codex (agent); pending human review.

## [2026-09-16] - Add safe survivor-to-staging dispatcher (task 0039)
### Added
- `scripts/staging_dispatch.py` verifies the current base/head refs against the
  staging eligibility receipt, composes the review body with PR intelligence,
  and defaults to a no-write dry run.
- `--create` is the explicit human-review handoff; the adapter never merges,
  approves, deploys, or pushes.
**Author**: Codex (agent); pending human review.

## [2026-09-16] - Add trusted meta-test dispatcher boundary (task 0038)
### Added
- `scripts/meta_test_dispatch.py` composes the disposable agent-skill fixture
  suite with the one-shot worker supervisor and emits one exact-SHA-bound
  `meta-test` receipt carrying lifecycle evidence.
- Missing worker output, unsafe facts, failed cleanup or failed deregistration
  remain non-pass; the adapter never fabricates agent or teardown evidence.
### Changed
- The runtime handoff is now explicit: a protected homelab dispatcher can
  upload the combined receipt without the core selecting a model or opening a
  remote connection.
**Author**: Codex (agent); pending human review.

## [2026-09-16] - Add commit-bound PR intelligence for early HITL routing (task 0037)
### Added
- `scripts/pr_intelligence.py` emits JSON and Markdown with deterministic risk,
  diff-churn, contact-surface, gate-evidence and test-impact measurements.
- The summary derives explicit human-review checkpoints without changing the
  fail-closed admission policy, and is published to the CI job summary plus an
  idempotent PR comment when GitHub permits comment writes.
### Changed
- The admission job now exposes the evidence reviewers need before staging;
  fork PRs still retain the job-summary/artifact fallback when comment writes
  are permission-restricted.
**Author**: Codex (agent); pending human review.

## [2026-09-16] - Implement the read-only debt ledger runner (task 0036)
### Added
- `scripts/debt_ledger.py` emits deterministic Markdown and JSON ledgers for
  TODO/FIXME/HACK/XXX/ponytail markers, prioritizing no-trigger debt and
  reporting scan errors and marker metrics.
- Generated/dependency/archive directories are skipped by default; docs are
  opt-in through `--include-docs`.
### Changed
- The `debt-ledger` skill now points at the executable runner instead of an
  unimplemented `runner.py` placeholder.
**Author**: Codex (agent); pending human review.

## [2026-09-16] - Migrate reusable pipeline skills (task 0035)
### Added
- Portable `integration-pilot`, `frontend-refactor-pr`, and `debt-ledger`
  skills are now canonical, scrubbed of company-specific structure.
- The migration preserves reversible integration-only merge/revert rules,
  per-location visual proof, and the no-trigger debt distinction.
### Changed
- The application-specific speaker-to-ClickUp skill remains explicitly
  excluded rather than introducing FIS entities or company workflow into the
  generic pipeline.
**Author**: Codex (agent); pending human review.

## [2026-09-16] - Add test-impact promotion eligibility receipt (task 0034)
### Added
- `scripts/impact_promotion.py` combines versioned benchmark, candidate
  selection, shadow execution, and authoritative full-suite evidence into a
  commit-bound eligibility decision.
- The receipt measures benchmark precision/recall, selection ratio, tests
  avoided, shadow/full durations, and observed duration savings while keeping
  full-suite authority explicit.
**Author**: Codex (agent); pending human review.

## [2026-09-16] - Enforce one-shot homelab worker lifecycle (task 0033)
### Added
- `scripts/worker_supervisor.py` now blocks unsafe self-hosted facts before
  launch, runs one bounded argv-only worker, scrubs obvious credential
  variables, and requires post-run cleanup/deregistration facts.
- Lifecycle receipts expose queue wait, worker age, mounted-secret count,
  cleanup, deregistration, duration, and exit metrics; failures remain
  non-pass.
### Changed
- The supervisor is included in canonical sync and the high-risk policy
  surface; the homelab runbook now documents the pre/post facts contract.
**Author**: Codex (agent); pending human review.

## [2026-09-16] - Add the agent-skill meta-test integration gate (task 0032)
### Added
- `scripts/meta_test.py` runs runtime-supplied agent workers against disposable
  fixture repositories and emits a schema-v1 receipt with deterministic checks
  for branch/commit discipline, task state, file scope, Closure Law markers,
  trajectory, and bounded timing/count metrics.
- A committed builder happy-path fixture is now executable under
  `tests/skills/fixtures/001-trivial-readme-edit/`.
- Skill changes are classified as `agent-skill` and require `meta-test` in the
  high-risk gate set; receipts are carried into admission and scorecard metrics
  only when bound to the exact candidate commit pair.
### Changed
- The `meta-test` skill and README now describe an implemented worker contract,
  not a design-only feature.
**Author**: Codex (agent); pending human review.

## [2026-09-16] - Add staging-review PR handoff adapter (task 0031)
### Added
- `scripts/staging_pr.py` validates eligible receipts, exact candidate SHA,
  open-PR idempotency, and emits a dry-run plan before invoking `gh pr create`.
- The adapter is synced/classified as a high-risk policy surface and cannot
  merge or approve a PR.
**Author**: Codex (agent); pending human review.

## [2026-09-16] - Carry visual receipts through admission (task 0030)
### Added
- Admission and scorecard adapters now recognize optional `visual` receipts,
  bind them to exact base/head SHAs, and expose diff/comparison metrics.
- CI discovers visual receipts when a consumer workflow supplies them without
  forcing browser dependencies on the core repository.
**Author**: Codex (agent); pending human review.

## [2026-09-16] - Add safe scanner failure diagnostics (task 0029)
### Added
- Scanner parse failures now emit a bounded diagnostic category and short
  stderr digest instead of raw tool logs, preserving actionable telemetry
  without publishing paths or accidental secrets.
- Live Docker smoke evidence: Semgrep, Trivy, and Gitleaks passed clean and
  planted synthetic contracts (`3 passed`); task 0007 remains open because the
  original transient Trivy root cause was not reproduced.
**Author**: Codex (agent); pending human review.

## [2026-09-16] - Close transitive test-impact gap (task 0028)
### Changed
- Test-impact analysis now traverses a conservative reverse Python import
  closure and correctly handles absolute `ImportFrom` statements.
- The versioned benchmark moved to `0.2`; transitive recall is now `1.000`,
  mean recall is `1.000`, and the benchmark reports `promotion_ready=true`.
**Author**: Codex (agent); pending human review.

## [2026-09-16] - Implement infrastructure dry-run gate (task 0027)
### Added
- `scripts/infra_dry_run.py` detects infrastructure changes and runs an
  explicit argv-only dry-run profile in a clean committed candidate archive.
- CI now produces and aggregates the infrastructure receipt; absent profiles
  fail closed while ordinary code changes remain explicitly not applicable.
### Changed
- The infrastructure gate is part of the canonical sync and high-risk policy
  surface.
**Author**: Codex (agent); pending human review.

## [2026-09-16] - Wire worker preflight into CI execution lanes (task 0026)
### Added
- CI runs the worker trust preflight before unit, clean-room integration, and
  deterministic gate commands, and uploads the resulting receipts.
- Self-hosted jobs now require a supervisor-provided facts file; hosted/fork
  jobs use an explicit safe default.
**Author**: Codex (agent); pending human review.

## [2026-09-16] - Add machine-checkable homelab worker preflight (task 0025)
### Added
- `scripts/worker_preflight.py` emits a fail-closed worker trust receipt with
  ephemeral, cleanup, worker-age, mounted-secret, Docker, and fork-routing
  metrics.
- The homelab runbook now documents the preflight invocation and its limits.
### Changed
- Worker preflight is part of the canonical synced/high-risk gate surface.
**Author**: Codex (agent); pending human review.

## [2026-09-16] - Add autonomous-to-staging promotion gate (task 0024)
### Added
- `scripts/staging_gate.py` converts an admitted quality scorecard plus a
  passing isolated integration receipt into a versioned staging-review
  eligibility receipt with blockers and metrics.
- CI now uploads staging eligibility evidence; missing or failed evidence stays
  blocked instead of becoming a green result.
### Changed
- The staging gate is part of the canonical synced/high-risk gate surface.
  It never creates or merges a PR; human review remains the next stage.
**Author**: Codex (agent); pending human review.

## [2026-09-16] - Make core sync provenance canonical and self-describing (task 0023)
### Added
- `core_sync.py` now generates `.claude/skills/VENDORED.md` with the canonical
  source URL plus the complete skill and gate inventory.
- Provenance metadata participates in the existing manifest/drift contract and
  has tests for clean sync, dry-run, drift detection, and forced repair.
### Changed
- Consumer Quick Start documentation now explains that stale
  `guidelines_IA` provenance is retired and should be replaced by the generated
  canonical receipt.
**Author**: Codex (agent); pending human review.

## [2026-09-16] - Add protected reusable policy workflow (task 0021)
### Added
- Added a reusable policy-integrity workflow that checks out a pinned core
  implementation and emits a policy receipt without inheriting secrets.
- Added a rollout runbook requiring immutable SHA pinning and branch protection.
**Author**: Codex (agent); pending human review.

## [2026-09-16] - Add policy-integrity admission receipt (task 0020)
### Added
- `scripts/policy_integrity.py` fingerprints the trusted base policy surface and
  reports workflow/gate-script changes as `review_required`.
### Changed
- Admission now requires a policy receipt in addition to unit, scanner, and
  risk-selected gates; policy changes cannot be silently auto-admitted.
**Author**: Codex (agent); pending human review.

## [2026-09-16] - Add versioned test-impact benchmark (task 0019)
### Added
- `scripts/impact_benchmark.py` materializes before/after git fixtures and
  reports precision, recall, fallback behavior, and `promotion_ready`.
### Changed
- CI now runs the benchmark as a deterministic harness metric. The corpus keeps
  test-impact shadow-only and makes the known transitive-import gap explicit.
**Author**: Codex (agent); pending human review.

## [2026-09-16] - Add test-impact shadow execution (task 0018)
### Added
- `scripts/impact_runner.py` executes conservative impacted-test selections in
  the clean-room boundary and emits non-authoritative selection/execution
  metrics.
### Changed
- CI now publishes test-impact shadow evidence while full-suite integration
  remains the correctness authority; task-derived shell arguments are routed via
  environment variables.
**Author**: Codex (agent); pending human review.

## [2026-09-16] - Add visual-regression receipt contract (task 0016)
### Added
- `scripts/visual_receipt.py` validates screenshot/viewport evidence, baseline
  provenance, pixel metrics, thresholds, and exact candidate identity before
  normalizing a visual PASS/FAIL receipt.
### Changed
- Visual receipt validation is now part of the synced/high-risk gate surface.
  The core remains honest: consuming frontend repos provide the Playwright
  producer; missing browser evidence is not a pass.
**Author**: Codex (agent); pending human review.

## [2026-09-16] - Add conservative test-impact analysis (task 0015)
### Added
- `scripts/test_impact.py` emits schema-v1 changed-file, selected-test,
  fallback-reason, and selection-ratio metrics using Python AST/path evidence.
### Changed
- Unknown/non-Python/unresolved changes explicitly fall back to the full test
  suite. Test-impact output is advisory until precision/recall benchmarking
  proves it safe to replace full clean-room execution.
**Author**: Codex (agent); pending human review.

## [2026-09-16] - Add deterministic quality scorecard (task 0014)
### Added
- `scripts/quality_scorecard.py` emits provenance-bound metrics for risk,
  evidence completeness, gate pass rate, change fan-out, integration duration,
  isolation, and reviewer independence.
- PR admission CI uploads the scorecard alongside the receipt. The scorecard
  mirrors the admission result and cannot create a green result from incomplete
  evidence.
**Author**: Codex (agent); pending human review.

## [2026-09-16] - Define ephemeral homelab worker boundary (task 0013)
### Changed
- Expanded the homelab runbook with a trust matrix, ephemeral/JIT lifecycle,
  credential and workspace isolation rules, revocation procedure, preflight,
  and measurable pool acceptance metrics.
- Explicitly retained fork-PR routing on GitHub-hosted workers and prohibited
  persistent workers for public PR validation. No credentials or confidential
  repository data are included.
**Author**: Codex (agent); pending human review and host-side execution.

## [2026-09-16] - Add isolated ultrareview worker runner (task 0012)
### Added
- `scripts/ultrareview_runner.py` executes an explicit reviewer argv in a
  temporary committed-HEAD workspace, supplies a base/head diff context, and
  normalizes JSON through the ultrareview receipt contract.
- Worker timeout, non-zero exit, malformed output, and unavailable execution
  produce explicit error evidence rather than a fabricated PASS.
### Changed
- Core sync and blast-radius gate-surface classification now include the
  worker runner. Homelab routing, network/credential isolation, and evidence
  authentication remain deployment follow-ups.
**Author**: Codex (agent); pending human review.

## [2026-09-16] - Add ultrareview receipt contract (task 0011)
### Added
- `scripts/ultrareview_receipt.py` validates independent reviewer reports and
  emits canonical schema-v1 PASS/BLOCK receipts with exact commit identity,
  invocation identity, evidence citations, findings, and metrics.
### Changed
- Receipt aggregation can now consume validated ultrareview evidence; malformed
  or stale review reports remain errors, and absent evidence still blocks
  high-risk admission. The adapter does not perform or impersonate the LLM
  review; protected reviewer execution remains a follow-up.
**Author**: Codex (agent); pending human review.

## [2026-09-16] - Add clean-room integration evidence (task 0010)
### Added
- `scripts/integration_gate.py` stages the committed HEAD into a temporary
  git-archive workspace and runs an explicit argv integration command without a
  shell. It emits schema-v1 identity, status, isolation, exit-code, duration,
  and output-size metrics; staging, timeout, and non-zero execution are never
  reported as pass.
- Independent PR `integration` job and artifact aggregation into the admission
  receipt. Core-sync and blast-radius now treat the integration producer as a
  gate script/high-risk surface.
### Changed
- Admission receipts now carry integration evidence when the producer emits
  it, while preserving missing-evidence fail-closed behavior for high-risk
  changes. Ultrareview evidence remains a separate follow-up.
**Author**: Codex (agent); pending human review.

## [2026-09-15] - Start fail-closed admission hardening (task 0009)
### Changed
- Live Docker verification fixed Semgrep auto-config/telemetry incompatibility
  and Gitleaks report capture; required scanner images are pinned by digest.
- Hosted CI exposed Gitleaks `detect --no-git` traversing checkout metadata and
  timing out; use its explicit directory scanner instead.
- A second hosted run showed whole-tree directory scanning still timed out;
  Gitleaks now receives an isolated temporary tree containing only changed files.
- Hosted run 35018028766 showed the Docker readiness probe was too short for a
  cold runner and that artifact download strips the `.docs/` prefix; readiness
  now allows 60 seconds, admission accepts either artifact layout, and the
  gates checkout the actual PR head SHA instead of GitHub's synthetic merge.
- Scanner absence, incomplete output and unexpected exit codes now return failure.
- Correct scan working directory and Trivy target, make source mount read-only,
  read Dependency-Check's report file, and avoid publishing raw stderr.
### Added
- Real clean/planted scanner contract fixtures and a GitHub-hosted CI job.
- Schema-v1 CI receipt aggregation for unit and scanner evidence, plus a final
  admission job bound to the pull request base/head SHAs. It intentionally does
  not claim authenticity until workflow/policy protection is configured.
- Schema-v1 admission consistency checker with required-gate/commit checks and
  completeness metrics, adversarial regression tests, and function catalog.
- Admission gate is included in core sync and classified high-risk when edited.
  Protected CI receipt production remains pending; this is not a deployed service.
**Author**: Codex (agent); pending human review.

## [2026-09-07] - Fix merge-artifact corruption in this file
### Fixed
- A stray, unmatched `=======` conflict marker had landed between the
  "File task 0007" and "Second pass: migrate guidelines_IA" entries — a
  leftover from resolving one of the several sibling-PR CHANGELOG.md
  conflicts noted in `completion-status-2026-09-05.md` §1. The same
  corruption had also eaten that entry's `**Author**` line, and the file's
  entries were no longer in the "newest entry on top" order this file's own
  header requires (the 2026-09-05 handoff-doc entry was buried at position 6
  instead of position 1). Removed the stray marker, restored the missing
  Author line, and reordered every entry from the 2026-09-03 gates-in-CI
  entry through the 2026-09-05 handoff doc back into newest-first order.
  No entry's actual text content changed — this is a structural fix to a
  merge artifact, not a rewrite of past entries.
**Author**: Claude (agent), reviewed by Bernardo Gavazzi

## [2026-09-05] - Cross-repo completion-status handoff doc
### Added
- `.docs/analysis/completion-status-2026-09-05.md` — status of every open
  thread from this initiative (PRs #6-#11, task 0007/0008 honest state,
  the clawdinha-do-rh WIP ship, the bluemagic-front migration decision,
  guidelines_IA's 4 still-unmigrated skills, sao-bernardino-brain's
  VeraCrypt encryption, and older housekeeping: the homelab runner pool
  registration and the `overpowers`/`zeroclaw` orphaned nested-git-repos in
  clawdinha-do-rh) — written so a fresh session/model can resume without
  re-deriving context from chat history.
**Author**: Claude (agent), reviewed by Bernardo Gavazzi

## [2026-09-04] - core_sync.py: drift detection for hand-edited vendored files (task 0008)
### Added
- `scripts/core_sync.py` — every synced file is now fingerprinted in
  `<target>/.claude/.core-sync-manifest.json`. If a vendored file's content
  no longer matches its recorded hash on the next sync (hand-edited locally,
  violating "core is read-only"), that file — or, for a skill, its whole
  directory — is skipped instead of silently overwritten, and `main()`
  returns exit code `1` to flag it distinctly from a clean sync (`0`) or a
  usage error (`2`). `--force` overwrites a drifted file anyway.
- `.docs/tasks/0008-feat-core-sync-drift-detection.md`.
- 21 new tests in `tests/test_core_sync.py` covering `_is_drifted`,
  manifest load/save (including a corrupt-manifest fallback), drift-skip +
  `--force` override for all three sync functions, and `main()`-level exit
  codes.
### Changed
- `sync_skills`/`sync_gate_scripts`/`sync_conventions` now return a
  `SyncResult(synced, drifted)` dataclass instead of a bare `list[str]` —
  existing tests updated to match; `sync_skills`'s reporting granularity
  changed from per-directory (`.claude/skills/tester/`) to per-file
  (`.claude/skills/tester/SKILL.md`), matching how the other two functions
  already reported.
- `README.md` Quick Start §1 — notes the manifest should be committed in the
  target repo, not gitignored (an uncommitted manifest only protects edits
  made in the same clone that ran the last sync).
### Not yet done
- Not validated against a real drifted vendored skill in an actual target
  repo — only against fixture trees and this repo's own source tree. First
  real-world case (likely `bluemagic-front`, still on the older
  `.agentic-core/sync-core.sh` mechanism) is still open.
**Author**: Claude (agent), reviewed by Bernardo Gavazzi

## [2026-09-04] - Surface scanner stderr + cache trivy's DB across runs (task 0007)
### Added
- `scripts/scan_gate.py` — `DockerResult(stdout, stderr, returncode)`
  replaces the bare `str` `_docker_run()` used to return; on an unparseable
  scanner output, `ToolRun.reason` now includes a truncated stderr tail (or
  an explicit "empty stderr too" note) instead of just the bare
  `JSONDecodeError` message that made PR #6's live trivy failure require
  pulling the CI artifact to diagnose.
- `run_trivy()` bind-mounts a persistent cache dir (`TRIVY_CACHE_DIR`,
  default `<repo>/.trivy-cache`) at trivy's default DB path
  (`/root/.cache/trivy`) so the vulnerability DB survives across
  `docker run --rm` invocations. `.github/workflows/ci.yml`'s `gates` job
  caches that dir via `actions/cache` (keyed on `run_id`, falling back to
  the most recent prior entry).
- 7 new tests in `tests/test_scan_gate.py` covering the stderr-surfacing
  behavior and the new mount-building logic.
### Not resolved
- The DB-download hypothesis for trivy's original failure is still
  unconfirmed — no environment this fix was built in has a reachable Docker
  daemon (same limitation noted in task 0001). The cache mitigation is
  applied regardless, since it's correct either way; task 0007 stays
  `in_progress` until a live failure (or real Docker access) actually
  confirms or refutes the cause. Full reasoning in the task's Honest
  Backlog.
**Author**: Claude (agent), reviewed by Bernardo Gavazzi

## [2026-09-04] - File task 0007: trivy "unparseable output" on scan_gate.py's first live run
### Added
- `.docs/tasks/0007-fix-trivy-unparseable-output.md` — backlog task for the
  trivy scanner error PR #6 surfaced on `scan_gate.py`'s first invocation
  against a real Docker daemon in CI (noted in commit `c62678b` as a
  follow-up rather than fixed inline). Diagnosis: `json.loads("")` on empty
  stdout is the exact error text seen, and `_docker_run()` currently
  discards `stderr` even on the error path — so the likely root cause (no
  persistent volume for trivy's vulnerability DB, downloaded fresh on every
  CI job) can't be confirmed from the gate's own error message today. Filed
  as `todo`, not fixed — item 5 of the user-ordered remediation list was
  "file a task," not "fix it."
**Author**: Claude (agent), reviewed by Bernardo Gavazzi

## [2026-09-04] - Second pass: migrate the rest of guidelines_IA's portable content, scrubbed (task 0006)
### Added
- `.docs/strategy/double-diamond-prototype-pipeline.md` — the actual
  Triple-Diamond/Diamante-2 definition this repo's own README references
  but says isn't written down anywhere; now it is.
- `.docs/analysis/pattern-rationale.md`, `.docs/analysis/meta-constitution.md`,
  `.docs/analysis/agentic-pipeline-target-architecture.md`,
  `.docs/analysis/factory-testing-gaps-2026-06-09.md` — design rationale for
  why this repo's doctrine and gate scripts look the way they do.
- `.docs/conventions/clickup-task-schema.md`, `.docs/conventions/scope-intake.md`,
  `.docs/conventions/clickup-comment-style.md`,
  `.docs/conventions/frontend-screen-flow.md` — three more shared
  conventions in the vein of the existing 6, plus the ClickUp-side task
  schema design spec.
- `.template/` — a minimal from-scratch prototype scaffold kit
  (README/AGENTS.md/CHANGELOG/PRD/`.gitignore`), rewired from
  `guidelines_IA`'s old `git subtree`/`dist/core` bootstrap flow to
  reference `core_sync.py` instead.
### Changed
- `README.md` — new section linking all of the above.
- `.docs/tasks/0006-docs-migrate-guidelines-ia.md` — scope note + updated
  Honest Backlog reflecting the second pass.
### Why a second pass
The first pass (below) excluded everything under `.docs/analysis/`,
`.docs/strategy/`, `.template/`, and 5 of `guidelines_IA`'s 11 conventions
files as "FIS-specific project history." After seeing the exclusion list,
the user overrode it: "make sure all the bits from there are here without
fis or company structure." Re-reviewed every excluded file individually —
files with real names/incidents/GCP-project-IDs/client-codenames threaded
through them stayed excluded (scrubbing wouldn't leave much); files that
were generic methodology with only incidental FIS mentions got migrated
with those mentions scrubbed. Full per-file disposition in task 0006's
Honest Backlog.
**Author**: Claude (agent), reviewed by Bernardo Gavazzi

## [2026-09-04] - Finish the guidelines_IA migration: model-selection + AGENTS variants (task 0006)
### Added
- `MODEL-SELECTION.guidelines.md`, `AGENTS.balanced.md`, `AGENTS.minimal.md`,
  `AGENTS.opus48.balanced.md`, `AGENTS.assessment.md`,
  `AGENTS.usage-guidelines.md` — migrated from `guidelines_IA`, the repo this
  one superseded. Flagged by the portfolio completeness benchmark as content
  a tombstoned repo was still load-bearing for. Model references updated to
  the current generation in the two live-reference docs
  (`MODEL-SELECTION.guidelines.md`, `AGENTS.usage-guidelines.md`); the two
  explicitly historical/versioned files (`AGENTS.opus48.balanced.md`,
  `AGENTS.assessment.md`) got a provenance note instead of a rewrite.
- `.docs/tasks/0006-docs-migrate-guidelines-ia.md`.
### Changed
- `README.md` — new "Choosing a model and an AGENTS.md variant" section
  linking all 6 migrated files.
### Not migrated (see task 0006's Honest Backlog for why)
- `.docs/analysis/`, `.docs/strategy/`, `.docs/admin/`, `.docs/tasks/`
  (FIS-specific project history, not portfolio-wide doctrine).
- `.docs/skills/*.md` (stale — missing 8 skills this repo already
  implements; migrating would be a regression).
- `infra/`, `.template/`, `publish-core.sh` (FIS-specific infra, a
  superseded scaffold kit, and a publish mechanism superseded by
  `core_sync.py` respectively).
**Author**: Claude (agent), reviewed by Bernardo Gavazzi

## [2026-09-04] - core_sync.py: automate vendoring the core into satellite repos (task 0005)
### Added
- `scripts/core_sync.py` — vendors `.claude/skills/` (optionally filtered via
  `--skills`), the whitelisted gate scripts, and `.docs/conventions/*.md`
  into a target repo, and seeds `AGENTS.md` from a generic template only
  when the target has none yet (never overwrites an existing one).
  `--dry-run` previews with zero filesystem changes. Directly targets the
  root cause found by the portfolio completeness benchmark
  (`.docs/analysis/completeness-benchmark-2026-09.md`): the doctrine's
  median score was 20/24 on the repos it was built for and 6/24 everywhere
  else, because adoption was manual copy-paste nobody actually did.
- `tests/test_core_sync.py` — 17 unit tests against fixture source/target
  trees plus integration-style tests against this repo's own real source
  tree (dry-run no-op, full sync, second-run never overwrites `AGENTS.md`).
- `.docs/tasks/0005-feat-core-sync-script.md`.
### Changed
- `README.md` Quick Start §1 — replaced the manual "copy `scripts/` in
  directly" instructions with `python scripts/core_sync.py <target>`.
**Author**: Claude (agent), reviewed by Bernardo Gavazzi

## [2026-09-03] - Enforce the gates in CI; benchmark the portfolio (task 0005)
### Added
- `.github/workflows/ci.yml` gains a `gates` job (PRs only, `fetch-depth: 0`)
  running `blast_radius.py` and `scan_gate.py` against the PR diff, uploading
  `.docs/blast-reports/` + `.docs/scan-reports/` and feeding scan_gate's SARIF
  to GitHub code scanning. Both scripts shipped with tests in July but were
  never actually invoked by CI — they were artifacts, not enforcement.
- `route` job selecting the runner per event. Fork PRs are pinned to
  GitHub-hosted runners: this repo is public and a self-hosted runner would
  execute untrusted fork code on the homelab box, which also holds the
  Evolution/WhatsApp credentials and the clawdinha stack. Pool routing is
  opt-in behind the `USE_HOMELAB_POOL` repo variable, because a job pinned to
  a label with no registered runner queues until timeout rather than failing.
- `.docs/runbooks/homelab-runner-pool.md` — registration steps, the
  User-vs-Organization constraint (user accounts cannot have org-level runner
  groups, so the pool is emulated with a uniform `homelab-pool` label), and
  the fork-PR security posture.
- `.docs/analysis/COMPLETENESS-RUBRIC.md` + `completeness-benchmark-2026-09.md`
  — 12-criterion conformance rubric and a scored benchmark of all 28 first-party
  repos, worktree-collapsed (30 dirs -> 6 canonical repos).

### Fixed
- `blast_radius.py` classified changes to the gate definitions themselves as
  `risk=low, gates=['unit']`. A PR deleting the entire `gates` job would have
  been waved through on unit tests alone. Adds `ci-workflow`, `gate-script`
  and `pre-commit-config` high-risk patterns, with an over-match guard test.
  Verified on this branch's own diff: now `risk=high`, requiring
  `sast`/`sca`/`ultrareview`.

### Notes
- Least-privilege `permissions:` and job timeouts added to all jobs.
- Test suite: 24 -> 27 passing.

## [2026-07-11] - Implement scan_gate.py: SAST/SCA/secret-scan gate (task 0001)
### Added
- `scripts/scan_gate.py` — runs Semgrep, Trivy, and gitleaks as Docker
  images against a diff's changed files, normalizes findings to SARIF +
  a verdict JSON (`.docs/scan-reports/<NNNN>.{sarif,json}`). OWASP
  Dependency-Check is wired but opt-in only (`--enable-dependency-check`),
  per this repo's own note that its NVD database isn't synced yet.
  Severity policy: a `critical`/`high` finding on a changed file blocks
  (exit 1); missing Docker/scanners degrades honestly (no fabricated pass).
- `tests/test_scan_gate.py` — 17 unit tests against canned real-shaped tool
  output (Semgrep/Trivy/gitleaks/OWASP-DC JSON), the classify/degrade logic,
  and SARIF assembly. Does NOT cover a live `docker run` invocation — no
  environment this was built in had a reachable Docker daemon; see the
  test file's own module docstring and task 0001's Honest Backlog.
- `.claude/skills/tester/SKILL.md` — new step 4b wiring `scan_gate.py` in as
  a required step when `blast_radius.py` marks a diff `sast`/`sca`, with the
  same degrade-don't-fabricate rule already used for the `fe_real` axis.
### Changed
- `README.md` — added `scan_gate.py` to the gates section and BYO table.
- `.gitignore` — added `.docs/scan-reports/` (same treatment as
  test-reports/blast-reports).
**Author**: Claude (agent), reviewed by Bernardo Gavazzi

## [2026-07-11] - Backlog closure pass: task 0004 tracking, repo-tiering.md, continuity ledger
### Added
- `.docs/tasks/0004-feat-generic-clickup-figma-whatsapp-skills.md` — filed
  retroactively for the previous entry's PR #4, closing the gap between
  "this repo enforces Closure Law on every task" and that PR having shipped
  without one.
- `.docs/conventions/repo-tiering.md` — the `prototype`/`active`/`canonical`
  vocabulary `tester`'s `SKILL.md` has referenced since it was first
  specified, but which never actually existed; every vendoring repo was
  silently falling back to `tester`'s conservative `prototype` default.
- `.agents/continuity-claude-code.md` — bootstrapped the continuity ledger
  `AGENTS.md` §0 has mandated since this repo's constitution was written;
  no prior agent pass (including this same agent's earlier work on tasks
  0001-0003) had actually initialized it.
### Fixed
- Task 0003's last open exit condition (validator spot-check) closed: re-ran
  `validate_task.py`/`validate_closure.py` against every task file,
  file-by-file and in CI's directory-mode invocation — all PASS.
**Author**: Claude (agent), reviewed by Bernardo Gavazzi

## [2026-07-11] - Generic ClickUp/Figma/WhatsApp skills + README deepening (task 0004)
### Added
- 9 new skills under `.claude/skills/`: `clickup-api`, `clickup-grounding`,
  `clickup-audit`, `figma-api`, `figma-frontend-context`,
  `implement-figma-task`, `visual-tester`, `zap-comms`, `whatsapp-clickup`.
  All BYO-credential-gated (env var precondition, no hardcoded org/workspace/
  bot persona), replacing the previous "Skills not included" README section.
### Changed
- `README.md` rewritten: pipeline-flow diagram, a concepts glossary (Closure
  Law §3, Dxx decisions, blast radius, proof-of-execution artifact,
  fake-green, grounding-vs-audit, prototype-vs-production mode, loop mode,
  quota gate, BYO pattern), per-group skill tables, a gates section, and a
  conventions section, replacing the previous one-liner-per-skill list.
### Fixed
- README referenced `migration-timestamp-ms.md`; the actual file is
  `migration-timestamp.md` — corrected the reference.
**Author**: Claude (agent), reviewed by Bernardo Gavazzi

## [2026-07-04] - Resolve task 0001's infra blocker (scanner images verified working)
### Changed
- `.docs/tasks/0001-feat-oss-static-analysis-gate.md` — the four scanners
  (Trivy, Semgrep, OWASP Dependency-Check, gitleaks) are confirmed running
  as Docker images with real smoke tests (Trivy: 5 CVEs found in a
  deliberately outdated `requirements.txt`; Semgrep: caught
  `subprocess.call(shell=True)`). Documents that `scan_gate.py` should shell
  out via `docker run`, not assume native binaries on PATH — smaller BYO
  footprint (needs Docker, not four package-manager installs). OWASP
  Dependency-Check's NVD database sync intentionally not run yet (needs an
  NVD API key to avoid a very slow first sync).
**Author**: Claude (agent), reviewed by Bernardo Gavazzi

## [2026-07-04] - Tighten blast_radius.py import/grep signal (found via dogfooding)
### Fixed
- `import_grep_signal` matched on generic filename stems (e.g. `SKILL`, from
  every `.claude/skills/*/SKILL.md`) as plain substrings — caught by running
  the classifier against this very PR's own diff, which flagged ~15 files as
  "affected" mostly through that one over-broad match. Added a stoplist of
  generic stems (`skill`, `index`, `readme`, `template`, `config`, `test`,
  etc.), raised the minimum stem length to 4, and switched to word-boundary
  matching (`\bstem\b`) instead of a bare substring search.
**Author**: Claude (agent), reviewed by Bernardo Gavazzi

## [2026-07-04] - Implement blast-radius + risk-tier classifier (task 0002)
### Added
- `scripts/blast_radius.py` — deterministic diff-scoped blast-radius +
  risk-tier classifier, run between `builder` and `tester`/`ultrareview`.
  Unions three cheap heuristics (ownership map, import/grep, historical
  co-change) into `affected_modules`; classifies `risk_level` (low/medium/
  high) from path/diff triggers (auth/RBAC, migrations, payments, Ansible/
  Helm/Fleet/Terraform/Rancher/Nexus paths, or unusually wide blast radius);
  emits `.docs/blast-reports/<NNNN>.json` with `required_gates`.
- `.docs/module-owners.md` — this repo's own (illustrative) ownership map,
  the hand-maintained input to signal 1.
- `tests/test_blast_radius.py` — 6 unit tests against a throwaway git
  sandbox (plain pytest, not a `meta-test` fixture — see task 0002's Exit
  Conditions for why).
### Changed
- `dispatcher` SKILL.md §4 gains step 5b invoking `blast_radius.py`;
  `risk_level` for `ultrareview` is no longer assigned inline by dispatcher's
  own prose judgment — both `tester` and `ultrareview` SKILL.md now read
  `risk_level`/`required_gates` from the artifact as the single source of
  truth.
### Fixed (found while implementing, not pre-existing repo bugs)
- `detect_base()` no longer crashes when a repo has no `origin` remote
  (e.g. a fresh local sandbox) — falls through to local branches, then
  `master`.
- Co-change mining (signal 3) originally used `git log -- <path>
  --name-only`, which silently restricts the file list to that same
  pathspec and can never surface a co-changed file. Rewritten as: collect
  commit SHAs touching the file, then `git diff-tree --no-commit-id
  --name-only -r <sha>` per commit (no pathspec) for the full file list.
- git's `--format=<literal>` treats a literal string with no `%` codes as a
  named pretty-format alias lookup and errors ("invalid --pretty format")
  unless prefixed `format:` — affected the co-change commit-boundary
  delimiter; fixed to `--format=format:<delimiter>`.
**Author**: Claude (agent), reviewed by Bernardo Gavazzi

## [2026-07-04] - Backlog: OSS scanning gate + blast-radius/risk-tier classifier; fix validator language drift
### Added
- `.docs/tasks/0001-feat-oss-static-analysis-gate.md` — backlog task for a
  deterministic SAST/SCA/secret-scan gate (Semgrep + Trivy + OWASP
  Dependency-Check + gitleaks → SARIF), the free/OSS half of what
  SonarQube/CodeRabbit provide.
- `.docs/tasks/0002-feat-blast-radius-risk-classifier.md` — backlog task for
  a diff-scoped blast-radius + risk-tier classifier gate feeding `tester`
  and `ultrareview`, extending risk triggers to infra (Ansible/Rancher/Nexus)
  changes.
- `.docs/tasks/000-template.md` — was referenced by README's quick-start but
  never actually existed in the repo (see Fixed, below).
### Fixed
- `scripts/validate_task.py` and `scripts/validate_closure.py` still checked
  Portuguese section titles (`Contexto`, `O Que Fazer`, `Condições de
  Saída`, `Pendências Honestas`, `Lei de Fechamento`) after the prior
  "translate all content to English" commit updated every doc to English
  headers (`Context`, `What To Do`, `Exit Conditions`, `Honest Backlog`,
  `Closure Law`). Any task written per current docs would have failed
  validation. See `.docs/tasks/0003-fix-validator-english-section-titles.md`.
- `.gitignore`'s `.docs/tasks/[0-9]*.md` rule also matched `000-template.md`
  (leading digit), silently preventing this repo from ever committing its
  own template or dogfood backlog. Removed the blanket ignore.
**Author**: Claude (agent), reviewed by Bernardo Gavazzi
