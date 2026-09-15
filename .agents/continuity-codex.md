# Continuity — Codex

## 2026-09-15 — Task 0009, first implementation slice

- User authorized SOTA hardening. Isolated worktree from freshly fetched
  origin/master 210cf86; branch fix/0009-fail-closed-admission.
- Scanner fail-closed semantics, report-shape/exit checks, source read-only,
  normalized source paths and corrected invocations implemented.
- Admission schema v1 / evaluator implemented with completeness metrics and
  adversarial tests. It is NOT trusted CI enforcement yet: protected receipt
  producers, policy loading and authentication remain explicitly pending.
- Existing scanner CI step needs no YAML change to inherit new failure exits.
- Docker became available after the user opened it. Required live-image
  clean/planted contracts pass (3 tests); optional Dependency-Check not run.
  Fixed Semgrep explicit rules/telemetry setting and Gitleaks report-file capture.
  Pinned required image digests; CI contract job added locally, not pushed.
- Added `ci_receipts.py`, schema-bound risk/scan reports and a final CI admission
  job. It is explicitly a consistency check until workflow/policy protection
  and signed evidence exist; absent high-risk integration/ultrareview receipts
  block as designed.
- PR #14 hosted run exposed Gitleaks `detect --no-git` timing out on checkout
  metadata after 300s. Switched to `gitleaks dir /src`; focused live suite then
  passed 67 tests locally. Follow-up is uncommitted until pushed.
- Hosted rerun 35015951189 showed whole-tree `dir` scanning also timed out.
  Gitleaks now stages only changed files in a temporary tree; focused live
  scanner tests pass locally. Follow-up remains uncommitted until pushed.
- Hosted run 35018028766 showed Docker readiness timing out at 10 seconds and
  admission not finding artifact directories after GitHub flattened the
  `.docs/` prefix. Increased readiness to 60 seconds, accepted both artifact
  layouts, and pinned the gates checkout to the real PR head SHA. Gates still
  fail closed when Docker is unavailable; admission still reports the missing
  evidence rather than fabricating a receipt.
- No push, PR, deployment, worker provisioning or private/company-repo change.
- Final verification with PIPELINE_LIVE_SCANNERS=1: 111 tests passed in
  102.08s;
  task/closure structural validators
  passed; git diff --check passed with Windows line-ending warnings only.
- Next: trusted CI receipt producers, then durable
  isolated execution. Keep task in_progress until verification and review.
