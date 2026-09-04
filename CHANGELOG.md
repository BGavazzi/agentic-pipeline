# Changelog

Format: newest entry on top. Never delete or rewrite past entries (typos excepted).

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
