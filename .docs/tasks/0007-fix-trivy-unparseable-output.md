---
status: in_progress
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
- [x] Fix #2 first (it's what makes #1 diagnosable without guessing): thread
      `result.stderr` through `_docker_run()`'s return (a small
      `DockerResult(stdout, stderr, returncode)` instead of a bare `str`),
      and include a truncated stderr tail in the `ToolRun.reason` when
      `raw` fails to parse or is empty. Also handles the empty-stdout-AND-
      empty-stderr case explicitly (e.g. an OOM-killed container) instead of
      leaving the reader to guess why no stderr came through.
- [x] Confirm/refute the DB-download hypothesis — **could not confirm**, same
      limitation as task 0001's Honest Backlog: no environment this fix was
      built in has a reachable Docker daemon, so trivy's actual stderr on the
      next real failure is still unobserved. Not fabricating a confirmation
      — see Honest Backlog below for what this means for closing the task.
- [x] Given the hypothesis is plausible but unconfirmed, implemented the
      cheap mitigation regardless of exact cause: `run_trivy()` now bind-
      mounts a persistent cache dir (`TRIVY_CACHE_DIR`, default
      `<repo>/.trivy-cache`) at trivy's own default DB path
      (`/root/.cache/trivy`) instead of letting each `docker run --rm`
      start cold. `ci.yml`'s `gates` job caches that dir with
      `actions/cache` (keyed on `run_id`, falling back to the most recent
      prior entry) so the DB persists across CI runs too. This is correct
      to do whether or not a DB pull was actually this failure's cause —
      it removes a real network dependency from every gate run either way.
- [x] Regression tests added to `tests/test_scan_gate.py`: empty-stdout
      input to the run-and-parse path produces a `ToolRun.reason` carrying
      the actual stderr content (`test_run_all_scanners_surfaces_stderr_on_unparseable_output`),
      an explicit "empty stderr too" note when stderr is also empty
      (`test_run_all_scanners_notes_empty_stderr_too_when_stdout_is_empty`),
      and the new `_docker_run`/`run_trivy` mount-building logic itself
      (`test_docker_run_bind_mounts_extra_paths_and_creates_them`,
      `test_run_trivy_mounts_a_cache_dir_by_default`,
      `test_run_trivy_honors_trivy_cache_dir_env_override`).

## Affected Files
- `scripts/scan_gate.py` (`DockerResult`, `_stderr_tail`, `_docker_run`,
  `run_trivy`, `run_all_scanners`)
- `tests/test_scan_gate.py`
- `.github/workflows/ci.yml` (`gates` job — trivy DB cache step)
- `.gitignore` (`.trivy-cache/`)

## Exit Conditions
- [ ] Root cause confirmed via stderr captured from a real failing run —
      **not met**; see Honest Backlog. Left unchecked deliberately rather
      than marked N/A, since it's the one exit condition this pass could
      not close.
- [x] A trivy invocation failure surfaces an actionable reason in
      `.docs/scan-reports/<NNNN>.json`, not just "unparseable output: ..."
- [x] Regression tests passing (22/22 in `tests/test_scan_gate.py`)
- [x] DB-download flakiness mitigated regardless of confirmed root cause
      (persistent cache dir, locally and in CI) — a deliberate decision to
      de-risk the plausible cause cheaply rather than block on confirming it

## Required Documentation (Closure Law)
- [x] `CHANGELOG.md` updated
- [N/A] `<function_catalog>` — doesn't exist yet in this repo
- [N/A] `<sdd_kit_path>` — no SDD_KIT.md in this repo
- [ ] `README.md` — not updated; the cache step is CI-internal, not a new
      BYO requirement for a consuming repo (nothing outside `ci.yml` and
      `scan_gate.py` itself needs to know it exists)
- [N/A] `.agents/continuity-<agent>.md` — not in use this session
- [x] Tests passing
- [N/A] `<route_map>` — no web routes in this repo
- [ ] PR approved — stays `in_progress` until PR review lands

## Honest Backlog
- **Root cause still unconfirmed.** The DB-download hypothesis is backed by
  one data point (fail-then-pass-on-retry across two CI runs — consistent
  with, not proof of, a DB-download flake; could also be an unrelated
  transient Docker Hub/ghcr.io hiccup) and this fix's own dev environment
  had no reachable Docker daemon either, so it couldn't be tested against a
  real trivy invocation. The error-surfacing fix means the *next* live
  failure (if the cache mitigation doesn't fully absorb it) will show real
  stderr in `.docs/scan-reports/<NNNN>.json` instead of a bare
  `JSONDecodeError` — closing that gap was the actual precondition for ever
  confirming this. Filed as `in_progress`, not `done`: the mitigation and
  observability fix are real and tested, but "confirmed root cause" — one
  of this task's own Exit Conditions — is honestly still open until a live
  CI failure (or a session with real Docker access) produces stderr to read.
- The `--cache-dir` flag and `/root/.cache/trivy` default path are asserted
  from trivy's documented behavior, not verified against a live `docker run
  aquasec/trivy` invocation (no Docker here) — if a future run shows trivy
  actually caches elsewhere inside the image, the mount target needs
  correcting.
