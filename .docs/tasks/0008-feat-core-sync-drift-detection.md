---
status: in_progress
priority: P2
type: feat
created: 2026-09-04
updated: 2026-09-04
clickup_id: null
parent: 0005
blocks: []
blocked_by: []
---

# 0008 — feat: core_sync.py drift detection

## Context
Task 0005's own Honest Backlog flagged this explicitly: "if someone hand-edits
a vendored skill or gate script in a target repo (violating 'core is
read-only'), core_sync silently overwrites it on next sync rather than
warning first." A follow-up cross-portfolio harness survey confirmed this is
not hypothetical — `bluemagic-front` is still on the OLDER `.agentic-core/
sync-core.sh` vendoring mechanism specifically because nobody has migrated it
to `core_sync.py` yet, and a repo left on manual/ad-hoc vendoring for a long
stretch is exactly the shape of repo where a "quick local fix" to a vendored
skill is most likely to happen and then get silently destroyed by the next
sync. This is item 6 of that survey's battle-ready punch list.

## Problem
`core_sync.py`'s `sync_skills`/`sync_gate_scripts`/`sync_conventions` always
overwrite by name with no comparison against what was there before. There was
no way to tell "this differs from source because it's a stale copy" from
"this differs from source because someone deliberately hand-edited it" —
every sync run's answer was "overwrite it anyway," even for the second case.

## What To Do
- [x] Fingerprint every synced file in `<target>/.claude/.core-sync-manifest.json`
      (`{relpath: sha256}`) at sync time.
- [x] Before overwriting a file, compare its current content against the
      manifest's recorded hash for that relpath — if they differ, it drifted
      (hand-edited locally since the last sync). A relpath with no manifest
      entry is never "drifted" (first sync, or a pre-existing file with
      nothing to compare against) — first sync still always wins, matching
      pre-existing behavior exactly.
- [x] Skills are gated per-directory (any drifted file in a skill blocks
      syncing that whole directory this run, not a partial per-file merge);
      gate scripts and convention docs are gated per-file, since each is a
      single standalone file.
- [x] `--force` flag overwrites drifted files anyway and re-fingerprints them.
- [x] `main()` reports drifted files distinctly from synced ones and returns
      exit code `1` (not `0`) when anything was skipped due to drift, so a
      caller/CI step can tell "clean sync" from "needs a human decision"
      without parsing stdout.
- [x] Unit tests: `_is_drifted` directly, drift-skip + force-override for all
      three sync functions, the one-drifted-file-blocks-the-whole-skill-dir
      behavior, manifest load/save (including a corrupt-manifest fallback to
      "nothing tracked"), and `main()`-level exit-code coverage.
- [x] `README.md` Quick Start — note that the manifest should be committed in
      the target repo (not gitignored), since an uncommitted manifest only
      protects edits made in the same clone that ran the last sync.

## Affected Files
- `scripts/core_sync.py` (`SyncResult`, `_sha256`, `load_manifest`,
  `save_manifest`, `_is_drifted`, `sync_skills`, `sync_gate_scripts`,
  `sync_conventions`, `main`)
- `tests/test_core_sync.py`
- `README.md` (Quick Start §1)

## Exit Conditions
- [x] A hand-edited vendored file is never silently overwritten by a normal
      (non-`--force`) sync
- [x] `--force` still allows a deliberate full re-vendor
- [x] `main()` distinguishes "clean sync" (exit 0) from "drift skipped, needs
      a decision" (exit 1) from "usage error" (exit 2)
- [x] Test suite passes 100%
- [ ] Actually used to migrate `bluemagic-front` off the old `sync-core.sh`
      mechanism — not this task's scope (separate item on the same punch
      list), but the reason this exists; noted here so it doesn't get lost.

## Required Documentation (Closure Law)
- [x] `CHANGELOG.md` updated
- [N/A] `<function_catalog>` — doesn't exist yet in this repo
- [N/A] `<sdd_kit_path>` — no SDD_KIT.md in this repo
- [x] `README.md` updated
- [N/A] `.agents/continuity-<agent>.md` — not in use this session
- [x] Tests passing
- [N/A] `<route_map>` — no web routes in this repo
- [ ] PR approved — stays `in_progress` until PR review lands

## Honest Backlog
- The manifest is a flat `{relpath: sha256}` map with no timestamp or
  "synced by/from which commit" metadata — enough to answer "did this
  drift," not enough to answer "when, or against which version of the
  source." Adding that is cheap if it turns out to matter; left out for now
  as speculative scope.
- No merge/reconcile helper — when a file has drifted, the operator's only
  paths are "keep the local edit forever (leave it drifted, it just keeps
  getting skipped)" or "`--force` and lose it." A three-way diff/merge
  workflow would be nicer but is meaningfully more machinery for a problem
  that, in the one motivating case (`bluemagic-front`), is currently zero
  drifted files — there's nothing yet to prove the simple version is
  insufficient.
- Not validated against a real drifted vendored skill in an actual target
  repo (`bluemagic-front` or otherwise) — only against the fixture trees in
  `tests/test_core_sync.py` and this repo's own real source tree via the
  `main_*` integration-style tests. First real-world run is still open.
