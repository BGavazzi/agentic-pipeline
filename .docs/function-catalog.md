# Public CLI function catalog

Initial catalog, 2026-09-15. Core script APIs are internal Python interfaces;
CLI output/exit changes must still be documented and regression-tested.

## Task 0042 contract revisions (supersede earlier signatures below)

| API | Current contract |
|---|---|
| `ci_receipts.test_status(path, base_sha, head_sha)` | Requires versioned JSON exit evidence for the exact pair; bare exit-code text is rejected. |
| `integration_gate.staged_workspace(repo, head_sha=None, base_sha=None)` | Archives an exact commit or clean base/head merge tree; `run_integration` emits executed-tree provenance. |
| `infra_dry_run._clean_workspace(repo, head_sha)` | Archives the exact candidate, not checkout HEAD. |
| `policy_integrity.build_report(repo, base, head, policy_ref=None, review_evidence=None)` | Protects the complete script/workflow/skill surface; only a protected caller can supply API-verified independent review evidence. |
| `visual_receipt.validate_report(report, base_sha, head_sha, artifact_root=None, threshold=0.0)` | Requires an artifact root; verifies hashes, containment and consistent counts against a trusted threshold. |
| `worker_supervisor.supervise(..., cleanup_command=None)` | Blocks without a trusted host teardown argv. Fresh callback JSON, never child-written files, supplies postconditions on every exit path. |
| `meta_test.run_fixture(..., observer_command=None, skills_root=None)` | Observes disk state; independent observer supplies tests/trace; records installed candidate skill hash. `run_suite` forwards the same options. |
| `meta_test_dispatch.dispatch(..., cleanup_command=None, observer_command=None, source_repo=None)` | Requires candidate checkout identity, clean skills, fresh outputs, host teardown, and fixture/skill provenance. |
| `staging_gate.evaluate(..., repository=None)` | Requires merge-tree integration proof. CLI requires `--repository`. |
| `staging_pr.verify_remote` / `verify_pr` | Validate actual GitHub repository/head/base before and after draft creation; races block promotion. |
| `receipt_journal.append_event` | Atomic concurrent insert-or-verify; schema checked; timezone normalized; metadata conflicts rejected. |
| `receipt_journal.append_test_result` / `summarize_test_history` | Append-only per-test result history and explicit-reference freshness/flakiness/duration metrics; descriptive only and never an admission override. |

All these validators check consistency. Authenticity depends on protected
callers and host isolation; see `runbooks/review-remediation.md`.

| Script | Entry points / responsibility |
|---|---|
| `admission_gate.py` | `evaluate(risk, receipts, base_sha, head_sha)` validates schema v1, identities and obligations; `main()` returns 0 admitted, 1 unmet gate, 2 invalid input. Input authenticity is a caller obligation. |
| `ci_receipts.py` | `build_receipts(risk_path, scan_path, unit_exit_path, base_sha, head_sha, integration_path=None, ultrareview_path=None)` maps observed CI artifacts to schema-v1 gate statuses; missing evidence becomes error. It does not sign or authenticate evidence. |
| `integration_gate.py` | `run_integration(repo, task_id, base_sha, head_sha, command, timeout_seconds)` runs a command in a temporary git-archive workspace and emits schema-v1 pass/fail/error evidence without trusting prose. |
| `ultrareview_receipt.py` | `validate_report(report, base_sha, head_sha)` rejects weak/stale independent-review claims and normalizes a cited PASS/BLOCK report into an ultrareview gate receipt. It does not perform the LLM review. |
| `ultrareview_runner.py` | `run_reviewer(repo, task_id, base_sha, head_sha, command, timeout_seconds)` runs an independent reviewer argv in a clean workspace, validates its JSON stdout through `ultrareview_receipt.py`, and fails closed on unavailable/malformed workers. |
| `quality_scorecard.py` | `build_scorecard(risk_path, receipts_path, base_sha, head_sha, integration_path=None, ultrareview_path=None)` computes provenance-bound completeness, pass-rate, risk/fan-out, duration, and independence metrics without changing admission policy. |
| `test_impact.py` | `analyze(repo, base, head)` emits a conservative schema-v1 impacted-test selection; unknown or non-Python changes fall back to the full suite and the report is optimization-only. |
| `impact_runner.py` | `run_shadow(repo, task_id, base_sha, head_sha, timeout_seconds)` executes the conservative selection in the clean-room integration boundary and emits non-authoritative execution plus selection metrics; it never replaces the full-suite admission gate. |
| `harness_selftest.py` | `run_suite(fixtures_dir)` executes the versioned deterministic admission-fixture corpus and reports case pass/fail and duration metrics; it fails closed on an empty or failing corpus. |
| `impact_benchmark.py` | `run_benchmark(fixtures_dir, iterations=1)` materializes versioned before/after git fixtures, measures precision/recall, selection regret, fallback behavior, p95 latency, and bounded throughput, and reports whether impacted-mode promotion is safe; it never changes admission. |
| `policy_integrity.py` | `build_report(repo, base, head, policy_ref)` hashes the trusted policy surface, identifies policy-file changes, and emits a provenance-bound PASS or review-required receipt; it does not claim workflow immutability. |
| `visual_receipt.py` | `validate_report(report, base_sha, head_sha)` validates screenshot, baseline, viewport, pixel-diff threshold, and exact identity before normalizing a visual PASS/FAIL receipt; it does not launch Playwright. |
| `scan_gate.py` | `scan(repo, task_id, base, branch, enable_dependency_check)` returns summary/SARIF; `classify_gate(runs, changed, required_tools=REQUIRED_TOOLS)` checks required coverage and findings; `main()` returns 0 pass, 1 finding block, 2 incomplete/error. |
| `blast_radius.py` | `classify(repo, task_id, base, branch)` produces risk and obligations; `required_gates_for(risk_level, triggered)` supplies the gate minimum. |
| `core_sync.py` | `main()` vendors whitelisted scripts/skills/conventions and fingerprints them; drift handling is documented in README. |
| `validate_task.py` | `main()` validates task schema; does not execute acceptance conditions. |
| `validate_closure.py` | `main()` validates documentation structure; does not certify human approval or runtime correctness. |
| `quota_gate.py` | `main()` evaluates local quota state for STOP/CONTINUE; not a worker scheduler. |
| `provenance_verify.py` | `build_manifest(...)` and `verify_manifest(...)` bind release archive/SBOM digests to tag, source SHA and workflow metadata; cryptographic verification remains GitHub `actions/attest`/`gh attestation verify`. |
| `flake_gate.py` | `evaluate(history, manifest_path, as_of)` classifies flake evidence as pass/degraded/block with owner/expiry and denominator-first metrics; it never overrides admission. |
| `environment_fingerprint.py` | `build_fingerprint(requirements, observed=None, platform_values=None)` verifies exact dependency pins and emits secret-free environment identity; it is parity evidence, not hermeticity proof. |
| `junit_history.py` | `build_history(report, base_sha, head_sha, run_id, occurred_at)` converts common JUnit XML into versioned per-test status/duration evidence; it does not select, retry or skip tests. |
| `ci_telemetry.py` | `build_payload(inputs, repository, commit, run_id, timestamp)` emits file-only OTLP-shaped numeric metrics with commit/run identity; it never sends data or overrides admission. |
| `merge_group_contract.py` | `validate_event(event, event_name, required_checks)` validates merge-queue commit/ref identity and records that check completion and admission were not observed. |
| `release_health_gate.py` | `evaluate(health, rollback, candidate_sha, environment)` validates post-deploy health/rollback evidence without executing commands or claiming a trusted producer. |
| `local_integration_loop.py` | `integrate(...)` performs one disposable local merge pass; `run_loop(..., state_path, max_rounds, refresh)` adds bounded rediscovery and immutable-head state so repeated rounds skip only locally included candidates while keeping unresolved holds visible. Cross-repository and base-ref-mismatched candidates are held before ref resolution; unexpected worker exceptions roll back the prior disposable state; synthetic commits bypass repository hooks and child environments drop control variables. Both emit versioned evidence and never push, merge remotely, approve, deploy, or receive secrets. |
| `agent_eval_corpus.py` | `summarize(meta_report, min_cases, baseline)` and `run_corpus(...)` report versioned agent-eval pass rate, corpus readiness, baseline regression, p50/p95 duration, tokens and cost; a green corpus below `min_cases` is `insufficient_corpus`, never pass. Worker/config contents are bound by digest and admission is never overridden. |
| `.github/workflows/release-provenance.yml` | Tag-only operational contract for source archive, CycloneDX SBOM and signed artifact attestation; it is not a candidate admission gate. |
| `sota_audit.py` | `audit(repo)` emits a versioned static capability report; `markdown(report)` renders denominator-first output; neither changes admission. |
