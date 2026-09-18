---
status: in_progress
priority: P1
type: fix
created: 2026-09-17
updated: 2026-09-17
clickup_id: null
parent: null
blocks: []
blocked_by: []
---

# 0056 — Fix Docker scanner execution for Windows worktrees

## Context
The BlueMagic consumer migration exposed a real platform failure: Semgrep
received a mounted Windows worktree whose `.git` file pointed to a host-only
`D:/.../.git/worktrees/...` path. It failed while configuring Git safe-directory
before scanning any source.

## Problem
The scanner gate mounted the consumer checkout directly into `/src`. Git
worktree metadata is not portable across the Docker boundary, so a scanner
failure was caused by the host path rather than source findings. The gate must
preserve fail-closed semantics while making the input tree portable.

## What To Do
- [x] Detect a worktree `.git` pointer before Docker scanner invocation.
- [x] Stage a source-only tree without `.git`, dependency caches or build output.
- [x] Keep ordinary checkout behavior and the Trivy cache contract unchanged.
- [x] Add regression tests for a host-only Windows worktree pointer and the
      ordinary-checkout fast path.
- [ ] Run the live scanner contract from a real Windows worktree after review.

## Affected Files
- `scripts/scan_gate.py`
- `tests/test_scan_gate.py`
- `.docs/tasks/0056-fix-windows-worktree-scanner-boundary.md`

## Exit Conditions
- [x] A worktree scanner input never exposes its host-only `.git` pointer.
- [x] Missing/failed scanner output still produces an error, never a pass.
- [x] Existing parser, cache and ordinary-checkout tests remain green.
- [ ] Live Semgrep/Trivy/Gitleaks run passes on the Windows worktree path.

## Required Documentation (Closure Law)
- [ ] `CHANGELOG.md` updated
- [x] `<function_catalog>`: internal helper only; no public CLI change
- [N/A] `<sdd_kit_path>`: no architectural decision ratified in this packet
- [ ] `README.md` updated if the platform contract changes
- [ ] `.agents/continuity-<agent>.md` updated
- [x] Tests added
- [N/A] `<route_map>`: no route changed
- [ ] PR approved

## Honest Backlog
This patch addresses the observed worktree metadata failure only. The live
scanner must still be exercised on the actual Windows path, and CI remains the
authoritative check until that run completes.
