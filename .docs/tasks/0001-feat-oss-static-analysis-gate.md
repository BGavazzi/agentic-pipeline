---
status: todo
priority: P1
type: feat
created: 2026-07-04
updated: 2026-07-04
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
- [ ] Add `scripts/scan_gate.py`: runs, per changed-file set in the branch diff:
  - Semgrep (Community rules, `--config auto` or a pinned ruleset) for SAST
  - Trivy (`trivy fs --scanners vuln,secret,misconfig`) for SCA + IaC + secrets
  - OWASP Dependency-Check as a fallback/complement where Trivy's DB doesn't
    cover the ecosystem
  - gitleaks as a dedicated secret-scan pass (belt-and-suspenders with Trivy)
- [ ] Normalize all four tools' output into a single SARIF file at
  `.docs/scan-reports/<NNNN>.sarif` (same artifact-gate pattern as
  `.docs/test-reports/<NNNN>.json` — gate on the file, not on prose)
- [ ] Wire `scan_gate.py` into [[tester]]'s SKILL.md as a required step,
  producing a pass/fail verdict alongside the existing test report
- [ ] Define severity policy: any `critical`/`high` finding introduced by the
  diff (not pre-existing in the base branch) fails the gate; `medium`/`low`
  are warnings only in V1
- [ ] Document BYO install requirements (Semgrep, Trivy, Dependency-Check,
  gitleaks binaries) in README.md's "BYO dependencies" table

## Affected Files
- `scripts/scan_gate.py` (new)
- `.claude/skills/tester/SKILL.md` (wire the new step)
- `README.md` (BYO dependencies table)
- `.gitignore` (`.docs/scan-reports/` — same treatment as test-reports)

## Exit Conditions
- [ ] `scan_gate.py` runs standalone against a diff and emits a valid SARIF
  file + exit code (0 = pass, 1 = new critical/high finding, 2 = tool error)
- [ ] `tester` SKILL.md references the new step and documents the degrade
  path if a scanner binary is missing (warn, don't invent a pass)
- [ ] At least one fixture in `meta-test` exercises `scan_gate.py` against a
  sandbox repo with a deliberately planted secret/vuln and confirms it's
  caught

## Required Documentation (Closure Law)
- [ ] `CHANGELOG.md` updated
- [ ] `<function_catalog>` — [N/A] this repo has no function-catalog.md (core/tooling repo, not an app)
- [ ] `<sdd_kit_path>` — [N/A] no SDD_KIT.md in this repo yet
- [ ] `README.md` updated (BYO table)
- [ ] `.agents/continuity-<agent>.md` — [N/A] no multi-agent continuity ledger in use yet
- [ ] Tests passing (meta-test fixture)
- [ ] `<route_map>` — [N/A] no HTTP routes in this repo
- [ ] PR approved
