# Public CLI function catalog

Initial catalog, 2026-09-15. Core script APIs are internal Python interfaces;
CLI output/exit changes must still be documented and regression-tested.

| Script | Entry points / responsibility |
|---|---|
| `admission_gate.py` | `evaluate(risk, receipts, base_sha, head_sha)` validates schema v1, identities and obligations; `main()` returns 0 admitted, 1 unmet gate, 2 invalid input. Input authenticity is a caller obligation. |
| `ci_receipts.py` | `build_receipts(risk_path, scan_path, unit_exit_path, base_sha, head_sha, integration_path=None)` maps observed CI artifacts to schema-v1 gate statuses; missing evidence becomes error. It does not sign or authenticate evidence. |
| `integration_gate.py` | `run_integration(repo, task_id, base_sha, head_sha, command, timeout_seconds)` runs a command in a temporary git-archive workspace and emits schema-v1 pass/fail/error evidence without trusting prose. |
| `scan_gate.py` | `scan(repo, task_id, base, branch, enable_dependency_check)` returns summary/SARIF; `classify_gate(runs, changed, required_tools=REQUIRED_TOOLS)` checks required coverage and findings; `main()` returns 0 pass, 1 finding block, 2 incomplete/error. |
| `blast_radius.py` | `classify(repo, task_id, base, branch)` produces risk and obligations; `required_gates_for(risk_level, triggered)` supplies the gate minimum. |
| `core_sync.py` | `main()` vendors whitelisted scripts/skills/conventions and fingerprints them; drift handling is documented in README. |
| `validate_task.py` | `main()` validates task schema; does not execute acceptance conditions. |
| `validate_closure.py` | `main()` validates documentation structure; does not certify human approval or runtime correctness. |
| `quota_gate.py` | `main()` evaluates local quota state for STOP/CONTINUE; not a worker scheduler. |
