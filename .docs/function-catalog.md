# Public CLI function catalog

Initial catalog, 2026-09-15. Core script APIs are internal Python interfaces;
CLI output/exit changes must still be documented and regression-tested.

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
| `impact_benchmark.py` | `run_benchmark(fixtures_dir)` materializes versioned before/after git fixtures, measures test-impact precision/recall and fallback behavior, and reports whether impacted-mode promotion is safe; it never changes admission. |
| `visual_receipt.py` | `validate_report(report, base_sha, head_sha)` validates screenshot, baseline, viewport, pixel-diff threshold, and exact identity before normalizing a visual PASS/FAIL receipt; it does not launch Playwright. |
| `scan_gate.py` | `scan(repo, task_id, base, branch, enable_dependency_check)` returns summary/SARIF; `classify_gate(runs, changed, required_tools=REQUIRED_TOOLS)` checks required coverage and findings; `main()` returns 0 pass, 1 finding block, 2 incomplete/error. |
| `blast_radius.py` | `classify(repo, task_id, base, branch)` produces risk and obligations; `required_gates_for(risk_level, triggered)` supplies the gate minimum. |
| `core_sync.py` | `main()` vendors whitelisted scripts/skills/conventions and fingerprints them; drift handling is documented in README. |
| `validate_task.py` | `main()` validates task schema; does not execute acceptance conditions. |
| `validate_closure.py` | `main()` validates documentation structure; does not certify human approval or runtime correctness. |
| `quota_gate.py` | `main()` evaluates local quota state for STOP/CONTINUE; not a worker scheduler. |
