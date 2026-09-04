---
status: todo
priority: P2
type: fix
created: 2026-09-04
updated: 2026-09-04
clickup_id: null
parent: null
blocks: []
blocked_by: []
---

# 0007 — fix: trivy "unparseable output" on scan_gate.py's first live CI run

## Context
PR #6 (task 0005, CI gates wiring) was this repo's first time `scan_gate.py`
ran against a real Docker daemon in CI, rather than degrading locally (no
environment it was built in had one — task 0001's Honest Backlog). trivy
errored ("unparseable output: Expecting value: line 1 column 1 (char 0)")
on that first run; semgrep and gitleaks ran clean. Noted in commit `c62678b`
as a known follow-up rather than fixed inline, to avoid scope-creeping a
shell-injection fix into a scanner-reliability bug. This is item 5 of the
user-ordered remediation list from the portfolio completeness benchmark.

**Update since that note**: PR #6's retry (after the shell-injection fix)
re-ran the same `gates` job and trivy passed. That's evidence for the
diagnosis below, not proof against fixing it — a flake that self-resolves on
retry is still worth fixing, it just means it's not a hard blocker.

## Problem
`json.loads(raw)` raising `Expecting value: line 1 column 1 (char 0)` means
`raw` (trivy's captured stdout) was an **empty string** — this is the exact
error Python's json module gives for `json.loads("")`. Two compounding
issues in `scripts/scan_gate.py`:

1. **Likely root cause**: `run_trivy()` (`scripts/scan_gate.py:155`) invokes
   `docker run aquasec/trivy fs --scanners vuln,secret,misconfig --format
   json ...` with no persistent volume for trivy's vulnerability DB. On a
   GitHub-hosted runner, each job gets a fresh container — trivy must
   download its DB from `ghcr.io/aquasecurity/trivy-db` on every single
   invocation. If that download is slow, rate-limited, or transiently fails,
   trivy can exit having written nothing to stdout (error/progress goes to
   stderr) — exactly the failure the retry's success is consistent with.
2. **Observability gap**: `_docker_run()` (`scripts/scan_gate.py:132`)
   captures `result.stdout` and discards `result.stderr` entirely — even on
   the error path (`scripts/scan_gate.py:304`,
   `ToolRun(tool=name, status="error", reason=f"unparseable output: {e}")`).
   The `e` is a `JSONDecodeError` from the *parser*, which has no way to
   know trivy's actual failure reason lives in the stderr that was thrown
   away. This is why diagnosing PR #6's failure required downloading the CI
   artifact and reading the scan-report JSON rather than being obvious from
   the error message itself.

## What To Do
- [ ] Fix #2 first (it's what makes #1 diagnosable without guessing): thread
      `result.stderr` through `_docker_run()`'s return (or a small
      `DockerResult(stdout, stderr, returncode)` instead of a bare `str`),
      and include a truncated stderr tail in the `ToolRun.reason` when
      `raw` fails to parse or is empty.
- [ ] Confirm/refute the DB-download hypothesis: re-run `scan_gate.py`
      against this repo in CI a few times (or locally against a reachable
      Docker daemon) and check whether trivy's stderr on a bare/empty-stdout
      run actually shows a DB pull failure. Update this task with what's
      found before deciding on a fix beyond better error surfacing.
- [ ] If confirmed: consider a `--skip-db-update` + pre-warmed DB volume
      (cached across CI runs via `actions/cache` keyed on trivy DB version),
      or a `docker run` retry with backoff specifically for trivy — whichever
      is cheaper given what's actually happening in stderr.
- [ ] Add a regression test to `tests/test_scan_gate.py`: empty-stdout input
      to `parse_trivy`/the run-and-parse path produces a `ToolRun` whose
      `reason` includes actionable stderr content, not just the bare
      `JSONDecodeError` message.

## Affected Files
- `scripts/scan_gate.py` (`_docker_run`, `run_trivy`, the parse/degrade loop
  around line 304)
- `tests/test_scan_gate.py`

## Exit Conditions
- [ ] Root cause confirmed (not just hypothesized) via stderr captured from
      a real failing run
- [ ] A trivy invocation failure surfaces an actionable reason in
      `.docs/scan-reports/<NNNN>.json`, not just "unparseable output: ..."
- [ ] Regression test passing
- [ ] If root cause is DB-download flakiness: either fixed (caching/retry)
      or explicitly accepted as a known transient-failure mode with the
      gate's existing degrade-honestly behavior judged sufficient — either
      outcome is a valid close, but it has to be a decision, not a shrug

## Required Documentation (Closure Law)
- [ ] `CHANGELOG.md` updated
- [N/A] `<function_catalog>` — doesn't exist yet in this repo
- [N/A] `<sdd_kit_path>` — no SDD_KIT.md in this repo
- [ ] `README.md` updated, if the fix changes BYO requirements (e.g. a
      cache step) — [N/A] if the fix is error-surfacing only
- [N/A] `.agents/continuity-<agent>.md` — not in use this session
- [ ] Tests passing
- [N/A] `<route_map>` — no web routes in this repo
- [ ] PR approved

## Honest Backlog
- Root cause is a hypothesis backed by one data point (fail-then-pass-on-retry
  across two different CI runs, which is consistent with but not proof of a
  DB-download flake — could also be an unrelated transient Docker Hub/ghcr.io
  hiccup). Filed as `todo`, not `in_progress`, precisely because the next
  step is confirming this before spending effort on a specific fix.
