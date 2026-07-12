---
status: in_progress
priority: P1
type: feat
created: 2026-07-04
updated: 2026-07-11
clickup_id: null
parent: null
blocks: []
blocked_by: []
---

# 0001 — Feat: OSS static-analysis / SCA / secret-scan gate (SonarQube + CodeRabbit deterministic half)

## Context
Discussion (2026-07-04) on replacing paid tools (CodeRabbit, SonarQube) with
free/OSS equivalents split by capability: a deterministic half (SAST, SCA,
secret scanning) and an LLM-judgment half. The LLM half is already covered by
[[ultrareview]] (independent adversarial review, gates on artifact + re-run).
This task covers the deterministic half, which `ultrareview` and `tester` do
not currently provide: no SAST, no dependency/CVE scanning, no secret
scanning runs anywhere in the pipeline today.

## Problem
A task can pass `tester` (build/lint/unit tests) and `ultrareview` (semantic/
adversarial review) while still introducing a known-vulnerable dependency, a
hardcoded secret, or a common insecure pattern (e.g. SQL string
concatenation, unsafe deserialization) — none of which the current pipeline
checks for deterministically.

**Implementation note (2026-07-04):** verified via a real smoke test (Trivy
caught 5 CVEs in a deliberately outdated `requirements.txt`; Semgrep caught
`subprocess.call(shell=True)`) that these scanners run cleanly as Docker
images (`aquasec/trivy`, `semgrep/semgrep`, `owasp/dependency-check`,
`ghcr.io/gitleaks/gitleaks`) rather than needing native binaries on PATH.
`scan_gate.py` should shell out via `docker run --rm -v <repo>:/src <image>
<args>` — this keeps the BYO footprint to "has Docker," not four separate
package-manager installs, which fits this repo's portability goals better.

## What To Do
- [x] Infra dependency resolved (2026-07-04): the four scanner images —
  `aquasec/trivy`, `semgrep/semgrep`, `owasp/dependency-check`,
  `ghcr.io/gitleaks/gitleaks` — are pulled and smoke-tested working on a
  real Docker host (Trivy caught 5 CVEs in a deliberately outdated
  `requirements.txt`; Semgrep caught `subprocess.call(shell=True)`).
  `owasp/dependency-check`'s NVD database has NOT been synced yet — that
  needs an NVD API key to avoid a very slow/rate-limited first run; ask
  before kicking that off. This item was the "needs infrastructure" blocker
  that previously separated this task from 0002/0003; it's no longer a
  blocker for whoever implements `scan_gate.py` next.
- [x] Add `scripts/scan_gate.py`: runs, per changed-file set in the branch diff:
  - Semgrep (Community rules, `--config auto`) for SAST
  - Trivy (`trivy fs --scanners vuln,secret,misconfig`) for SCA + IaC + secrets
  - OWASP Dependency-Check as a fallback/complement — implemented but
    **opt-in only** (`--enable-dependency-check`), per this task's own note
    that its NVD database hasn't been synced (needs an API key); never
    auto-run something that slow/rate-limited without being asked
  - gitleaks as a dedicated secret-scan pass (belt-and-suspenders with Trivy)
- [x] Normalize all four tools' output into a single SARIF file at
  `.docs/scan-reports/<NNNN>.sarif` (same artifact-gate pattern as
  `.docs/test-reports/<NNNN>.json` — gate on the file, not on prose)
- [x] Wire `scan_gate.py` into [[tester]]'s SKILL.md as a required step
  (§1 note + new step 4b), producing a pass/fail/degraded verdict alongside
  the existing test report; degrades honestly (never fabricates a pass) when
  Docker/scanners are unavailable, same rule as the `fe_real` axis
- [x] Define severity policy (V1, deliberately simple — see Honest Backlog):
  a `critical`/`high` finding whose file is in the diff's changed-file set
  fails the gate; `medium`/`low` are warnings only. This is a
  changed-file-membership approximation of "introduced," not a true
  base-vs-branch differential re-scan (that would need every scanner to run
  twice, once per ref) — same class of deliberate imprecision as
  `blast_radius.py`'s own three cheap signals.
- [x] Document BYO install requirements (Docker; no native scanner binaries
  needed) in README.md's "BYO dependencies" table

## Affected Files
- `scripts/scan_gate.py` (new)
- `tests/test_scan_gate.py` (new)
- `.claude/skills/tester/SKILL.md` (wire the new step)
- `README.md` (BYO dependencies table + gates section)
- `.gitignore` (`.docs/scan-reports/` — same treatment as test-reports)

## Exit Conditions
- [x] `scan_gate.py` runs standalone against a diff and emits a valid SARIF
  file + exit code (0 = pass, 1 = new critical/high finding, 2 = tool error)
  — verified both via `tests/test_scan_gate.py` (17/17 green) and a live
  invocation against this repo's own branch (correctly detected the diff,
  degraded honestly since no Docker daemon was reachable in this
  environment, wrote both artifacts, exit 0)
- [x] `tester` SKILL.md references the new step (§1 + new step 4b) and
  documents the degrade path if Docker/a scanner is missing (warn via
  §Honest Backlog, don't invent a pass)
- [ ] At least one fixture in `meta-test` exercises `scan_gate.py` against a
  sandbox repo with a deliberately planted secret/vuln and confirms it's
  caught — **not done**; `meta-test` itself has zero fixtures and its
  fixture-runner scripts (`tests/skills/lib/{setup,assert,teardown}.sh`)
  don't exist yet (see `meta-test/SKILL.md`'s own "design spec, not yet
  implemented" status). Building that infra is bigger than this task's
  scope; tracked honestly below instead of silently marked done.

## Required Documentation (Closure Law)
- [x] `CHANGELOG.md` updated
- [ ] `<function_catalog>` — [N/A] this repo has no function-catalog.md (core/tooling repo, not an app)
- [ ] `<sdd_kit_path>` — [N/A] no SDD_KIT.md in this repo yet
- [x] `README.md` updated (BYO table + gates section)
- [x] `.agents/continuity-<agent>.md` updated (ledger now exists —
  `.agents/continuity-claude-code.md`, bootstrapped 2026-07-11)
- [x] Tests passing (`pytest tests/test_scan_gate.py` — 17/17 green; full
  suite `pytest tests/` — 24/24 green). Live-scanner coverage against a real
  Docker daemon is NOT part of this — see Exit Conditions and Honest Backlog.
- [ ] `<route_map>` — [N/A] no HTTP routes in this repo
- [ ] PR approved — pending human review; task stays `in_progress` until
  then per `git-pr-workflow.md` §4

## Honest Backlog
- No environment this was developed/tested in had a reachable Docker daemon
  (`docker info` fails here — client installed, engine not running) or any
  of the four scanner binaries on PATH. `scan_gate.py`'s normalization,
  severity-policy, and degrade-path logic are genuinely unit-tested
  (`tests/test_scan_gate.py`, 17/17 green, against canned real-shaped tool
  output); the actual `docker run` invocation strings for Semgrep/Trivy/
  gitleaks/OWASP-DC have NOT been exercised against a live daemon. Whoever
  picks this up next with real Docker access should run it once against a
  repo with a deliberately planted secret/CVE and confirm the images pull
  and the output parses as expected — that's also exactly what the missing
  `meta-test` fixture below would formalize.
- The `meta-test` fixture this task's own Exit Conditions call for doesn't
  exist — `meta-test` has zero fixtures built at all yet (its
  `tests/skills/lib/{setup,assert,teardown}.sh` scripts aren't written),
  so adding one fixture here would mean building that shared infra first.
  Scoped out of this task; worth its own follow-up once `meta-test`'s first
  fixture (`001-trivial-readme-edit`, already on its roadmap for `builder`)
  proves the harness out.
- `scan_gate.py`'s introduced-vs-pre-existing check is changed-file
  membership, not a true differential scan against the base ref (see the
  script's own docstring) — a V2 pass could scan both refs and diff finding
  sets for precision. Flagged, not blocking — same tradeoff class as
  `blast_radius.py`'s three cheap unioned signals.
