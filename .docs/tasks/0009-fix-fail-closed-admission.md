---
status: in_progress
priority: P0
type: fix
created: 2026-09-15
updated: 2026-09-15
clickup_id: null
parent: null
blocks: []
blocked_by: []
---

# 0009 — Fix: fail-closed scanner and admission contracts

## Context
User authorized the SOTA hardening sequence: truthful gates first, then durable
isolated execution, evaluations/observability, integration promotion and TIA.
Worktree created from origin/master 210cf86; the earlier RFC remains in the
original checkout, untouched.

## Problem
Skipped/error scanners could exit successfully. Required risk gates were emitted
but lacked a deterministic receipt evaluator. Scanner commands also lacked a
working directory, Trivy received multiple targets and Dependency-Check stdout
was treated as a JSON report although it writes a file.

## What To Do
- [x] Fail closed on missing, skipped, error and malformed scanner output.
- [x] Validate exit codes, scan tree from /src, protect source mount read-only.
- [x] Add versioned receipt evaluator and completeness measurement.
- [x] Reject missing/duplicate/unknown/stale receipts and removed obligations.
- [x] Add adversarial tests and preserve raw diagnostic output privacy.
- [x] Verify required scanner commands with real Docker images (clean + planted).
- [x] Wire receipt aggregation and admission check into CI; protection/authenticity
      remains explicitly open until branch/ruleset protection is configured.

## Affected Files
- `scripts/scan_gate.py`
- `scripts/admission_gate.py`
- `scripts/blast_radius.py`
- `scripts/core_sync.py`
- `tests/test_scan_gate.py`
- `tests/test_admission_gate.py`
- `tests/test_live_scanners.py`
- `tests/test_ci_receipts.py`
- `.github/workflows/ci.yml`
- `README.md`
- `.docs/function-catalog.md`

## Exit Conditions
- [x] No Docker and partial scanner failure return nonzero.
- [x] Admission cannot pass with a missing mandatory gate or stale identity.
- [x] Existing and new unit tests pass.
- [x] Real scanner execution verified and receipt aggregation/admission run in CI.
- [ ] Human review approved.

## Required Documentation (Closure Law)
- [x] `CHANGELOG.md` updated
- [x] `<function_catalog>` created at `.docs/function-catalog.md`
- [N/A] `<sdd_kit_path>` — no separate SDD kit; decisions recorded here
- [x] `README.md` updated
- [x] `.agents/continuity-codex.md` updated
- [x] Tests passing
- [N/A] `<route_map>` — CLI only
- [ ] PR approved — no PR created yet

## Honest Backlog
- Admission CLI validates consistency, not authenticity. Inputs must come from
  trusted execution. The CI job now aggregates unit/scanner evidence and runs
  admission, but workflow/policy ownership is still candidate-editable until
  branch/ruleset protection is configured.
- Live Docker contracts passed for Semgrep, Trivy and Gitleaks. Optional
  Dependency-Check remains unverified (opt-in DB setup not requested).
- Required scanner image digests are pinned; remote Semgrep rules and Trivy
  databases remain mutable. Base/head differential scanning,
  candidate-config isolation, coverage-of-scan proofs and signed evidence remain.
- Schema v1 does not yet bind policy/toolchain versions or wall-clock expiry.
  Commit matching does not protect against forged, candidate-written receipts.
- Durable orchestration, worker isolation, telemetry, visual adapter and TIA
  remain subsequent implementation slices; no infrastructure changed here.
- High-risk changes correctly fail admission when integration or ultrareview
  receipts are absent. Those producers are not fabricated by the aggregator;
  the failure is an honest signal for the next implementation slice.

## Live verification (2026-09-15)
- Full suite including live fixtures: 108 passed in 25.34s; task/closure
  validators and git diff --check passed. Reports are in the gitignored
  `.docs/test-reports/full-suite.xml` and `live-scanners.xml`.
- Docker Engine 29.1.2; required scanner fixtures: 3 passed in 14.26s.
- Live tests exposed Semgrep auto-config/metrics incompatibility; changed to
  explicit `p/security-audit` with metrics disabled (not silently enabling telemetry).
- Gitleaks detected a fixture but `/dev/stdout` did not deliver JSON to the
  caller. Changed to a dedicated writable report mount and require the file.
- Hosted PR run 35013562997 then exposed a second live issue: Gitleaks
  `detect --no-git` timed out after 300s on the checkout. Switched to the
  explicit `dir /src` scanner so repository metadata is not treated as a
  working-tree scan. Hosted run 35015951189 showed that scanning the whole
  working tree still timed out; changed Gitleaks to stage only the changed
  files. Local live suite passed after the fix.
- Hosted run 35018028766 showed a cold runner's Docker daemon exceeded the
  previous 10-second readiness probe and that `download-artifact` flattened
  the uploaded `.docs/` prefix. Increased the readiness budget to 60 seconds,
  made admission accept either artifact layout, and pinned the gates checkout
  to the actual pull-request head SHA so receipts cannot bind to a synthetic
  merge commit.
- Synthetic fixtures use never-issued values with valid format, constructed
  at runtime; public EXAMPLE values are allowlisted by Gitleaks.
- Added GitHub-hosted live-scanner CI job. This workflow change is local and
  unpushed; it is regression testing, not trusted admission receipt production.
