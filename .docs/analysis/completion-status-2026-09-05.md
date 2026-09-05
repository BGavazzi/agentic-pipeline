# Completion status — agentic-pipeline conformance initiative (2026-09-05)

Cross-repo handoff document. Written so a fresh model/session can pick up
this initiative without re-deriving context from chat history. Covers
everything opened since `completeness-benchmark-2026-09.md` (2026-09-03) —
read that file first for the original 28-repo scoring and the 6-item
user-ordered remediation list this all traces back to.

Every item below is either **DONE**, **OPEN (blocked on X)**, or
**NOT STARTED** — read the status word before assuming something is finished.

---

## 1. agentic-pipeline — open PRs (all green, none merged yet)

| PR | Branch | Task | Status |
|---|---|---|---|
| [#6](https://github.com/BGavazzi/agentic-pipeline/pull/6) | `feat/0005-ci-gates-homelab-pool` | 0005 (part 1) | **DONE** — CI green, needs merge |
| [#7](https://github.com/BGavazzi/agentic-pipeline/pull/7) | `docs/0006-fill-in-own-agents-md` | — | **DONE** — CI green, needs merge |
| [#8](https://github.com/BGavazzi/agentic-pipeline/pull/8) | `feat/0005-core-sync-script` | 0005 (part 2) | **DONE** — CI green, needs merge |
| [#9](https://github.com/BGavazzi/agentic-pipeline/pull/9) | `docs/0006-migrate-guidelines-ia` | 0006 | **DONE** — CI green, needs merge |
| [#10](https://github.com/BGavazzi/agentic-pipeline/pull/10) | `fix/0007-trivy-unparseable-output` | 0007 | **DONE** — CI green, needs merge |
| [#11](https://github.com/BGavazzi/agentic-pipeline/pull/11) | `feat/0008-core-sync-drift-detection` | 0008 | **DONE** — CI green, needs merge |

**Merge order matters less than it looks** — every one of these has already
hit at least one CHANGELOG.md merge conflict against master as sibling PRs
merged (trivial "both added an entry at the top" collisions, always resolved
the same way: keep both entries, newest-dated on top). Expect this to
recur — merging any one PR will very likely re-conflict the others; each
needs `git merge origin/master`, re-resolve CHANGELOG.md the same way,
re-run `pytest tests/ && python scripts/validate_task.py .docs/tasks &&
python scripts/validate_closure.py .docs/tasks`, then push before merging
the next. This is expected, not a sign something is wrong.

**Nobody has actually clicked "merge"** on any of these six yet — that's
the single biggest concrete next action for this whole initiative.

---

## 2. Task 0007 — trivy stderr surfacing + DB cache (PR #10)

**Status: DONE, but the task file itself stays `in_progress`, not `done`.**

Fixed: `_docker_run()` now returns a `DockerResult(stdout, stderr,
returncode)`; an unparseable scanner output surfaces actual stderr in
`ToolRun.reason` instead of a bare `JSONDecodeError`. `run_trivy()` now
bind-mounts a persistent cache dir at trivy's DB path, and `ci.yml`'s
`gates` job caches it via `actions/cache`.

**Not resolved, on purpose**: the original root cause (trivy DB download
flakiness) was never confirmed with real stderr — no environment this fix
was built in had a reachable Docker daemon (same limitation as task 0001).
The mitigation (caching) was applied regardless, since it's correct either
way, but task 0007's own Exit Conditions correctly leave "root cause
confirmed" unchecked. **If a live CI run ever hits this failure again**, its
`.docs/scan-reports/<NNNN>.json` will now carry real stderr — read that
before doing anything else; it may finally confirm or refute the DB-pull
hypothesis. Full detail in `.docs/tasks/0007-fix-trivy-unparseable-output.md`.

---

## 3. Task 0008 — core_sync.py drift detection (PR #11)

**Status: DONE for the mechanism; NOT STARTED for its actual motivating use case.**

`core_sync.py` now fingerprints every synced file in
`<target>/.claude/.core-sync-manifest.json` and refuses to silently
overwrite a file that's drifted (hand-edited locally) since the last sync —
skills gated per-directory, gate scripts/conventions per-file, `--force` to
override. 34 tests, all passing.

**What this was actually for is still undone**: `bluemagic-front` is the
repo that motivated this (stuck on the older `.agentic-core/sync-core.sh`
mechanism). See §5 below — the migration itself hasn't happened, only a
dry-run.

---

## 4. clawdinha-do-rh — WIP features shipped

**Status: DONE.** PR [#183](https://github.com/BGavazzi/clawdinha-do-rh/pull/183)
merged. The `wip/uncommitted-work-safety-net-2026-09-03` branch's real
unshipped work (geekhunter.py scraper, gupy.py expansion, link_ingest.py's
`log_unscrapable`/`queue_scraper_task` — the mechanism this repo's own
`CLAUDE.md` handoff step depends on — plus browser-extension gaps) was
merged onto current master (25+ commits ahead of the stale branch's base),
one docstring conflict resolved, full suite re-verified (2213 passed, 1
pre-existing unrelated flake confirmed present on plain master too).

**Loose end found along the way, not yet acted on**: two scraper-task
requests have sat `queued` in `scraper_task_requests` since 2026-07-25
(`jobs.micro1.ai`, `vertigo.inhire.app` — both "couldn't extract real
content" failures). `clawdinha_do_rh`'s own `CLAUDE.md` says an incoming
session should convert these to real tracked tasks and mark them
`converted`; this session had no `TaskCreate` tool available, so they're
still sitting there. **NOT STARTED** — next session with task-creation
tooling should run the query in that `CLAUDE.md` and action them.

---

## 5. bluemagic-front migration to core_sync.py (FIS repo)

**Status: NOT STARTED — dry-run only, deliberately.**

`bluemagic-front`'s remote is `github.com/iniciativafis/bluemagic-front` —
flagged in this user's own standing notes as a past org, never to push to.
It's also a live production repo (real deploy pipeline, Sentry,
`Dockerfile.ci`) that coworkers touch. Given that, this session stopped at:

```
python scripts/core_sync.py /d/VIBES/FIS/bluemagic-front --dry-run
```
— confirmed clean (would add 19-20 skills, 5 gate scripts, 6 conventions;
`AGENTS.md` correctly left untouched; no drift, since it has no manifest
yet). **No files have been written, nothing committed, nothing pushed.**

Explicit next steps, in order, each needing a human decision before
proceeding to the next:
1. Run the real sync (drop `--dry-run`) — writes files locally only.
2. Review the diff in that checkout.
3. Decide whether to also remove the old `.agentic-core/` dir and
   `sync-core.sh` (core_sync.py does NOT do this automatically — additive
   only, by design).
4. Commit and push **only with explicit fresh confirmation each time** —
   this is FIS company code on an org flagged "never use" for pushes;
   the standing instruction is to re-confirm scope for this specific
   action, not treat one past approval as blanket permission.

---

## 6. guidelines_IA's 4 unmigrated skills

**Status: NOT STARTED.** A cross-portfolio harness survey (this session,
2026-09-04) found `guidelines_IA` (the deprecated predecessor repo) still
has 4 skills that were never migrated into `agentic-pipeline`:
`integration-pilot`, `frontend-refactor-pr`, `debt-ledger`,
`bluemagic-speakers-to-clickup`. Task 0006's migration passes (both of
them) only ever checked top-level files/dirs against `agentic-pipeline`,
never diffed the actual skill inventory — this gap was found by the survey,
not by task 0006's own process, so it's worth treating as a distinct
follow-up rather than assuming task 0006 covers it.

Each needs the same KEEP-AS-IS / SCRUB-THEN-KEEP / EXCLUDE triage the
second-pass guidelines_IA migration (task 0006) used — not yet done for
any of these four. `bluemagic-speakers-to-clickup` in particular sounds
FIS-specific by name and may be an EXCLUDE on inspection; the other three
sound more likely portable. Unverified either way — nobody has opened
these four `SKILL.md` files yet in this initiative.

---

## 7. Portfolio-wide harness inventory (context, not a task)

From the same survey — useful background for anyone deciding what to do
next, not itself an action item:

| Repo | Harness | Real visual-regression | CI gates wired |
|---|---|---|---|
| agentic-pipeline (canonical) | full skill set, source of truth | No — `visual-tester` is docs-only | Yes |
| guidelines_IA (superseded) | 23 skills (4 unmigrated, see §6) | No | No |
| bluemagic-front | 8 skills, OLD `.agentic-core/sync-core.sh` mechanism | No | No |
| bluemagic-events, clickup_bot_CM_WA, newshub-collector, teste_refactor_whitelabel | none vendored | No | No |
| PortalApp | Storybook helpers, not the pipeline skill set | **Yes — real** (Playwright + Chromatic) | No |

Real Playwright visual-regression exists in exactly one place in the whole
portfolio (PortalApp, via Chromatic) — a completely different mechanism
from what `visual-tester`'s `SKILL.md` documents (CDP + pixelmatch), which
has never been implemented as actual code anywhere, including in
`guidelines_IA` where the idea originated.

---

## 8. sao-bernardino-brain encryption

**Status: OPEN — VeraCrypt now installed, container not yet created.**

User's explicit request: keep this repo local-only (already true — no
remote, confirmed earlier), encrypted, choosing a VeraCrypt container over
Windows EFS. VeraCrypt was blocked for a while on a UAC prompt a headless
shell can't approve; **as of 2026-09-05 it is installed**
(`C:\Program Files\VeraCrypt\VeraCrypt.exe` confirmed present).

**Not done, and shouldn't be automated**: creating the actual encrypted
volume needs a passphrase, which must never pass through a shell command,
process list, or this chat transcript — that's the whole point of
encrypting something this sensitive (a confidential legal/valuation vault).
This has to be done by the user directly, either via the VeraCrypt GUI
(Volumes → Create New Volume → standard/hidden, size, encryption
algorithm, then type the passphrase interactively) or the CLI with the
passphrase typed at an interactive prompt, never passed as an argument.
Once a volume exists and is mounted, moving `sao-bernardino-brain`'s content
into it is a plain file move — that part an agent can do.

---

## 9. Older housekeeping items, still open (pre-date this document)

- **Homelab runner pool** (`.docs/runbooks/homelab-runner-pool.md`,
  merged via PR #6): registration steps are written but the
  `USE_HOMELAB_POOL` repo variable is confirmed **not set**
  (`gh api repos/BGavazzi/agentic-pipeline/actions/variables` → empty) as
  of 2026-09-05. All CI on `agentic-pipeline` is still running on
  GitHub-hosted runners, not the homelab pool. **NOT STARTED.**
- **`overpowers`/`zeroclaw` orphaned nested git repos** inside
  `clawdinha_do_rh` — confirmed still present as of 2026-09-05 (`.git/` in
  each, no `.gitmodules` entry — `git submodule status` errors on both).
  Flagged in an earlier pass, never actioned. Needs a decision: register
  as real submodules, or `git rm --cached` + `.gitignore` them, or convert
  to plain non-git dirs if the nested `.git/` was accidental.

---

## How to resume

Merging PRs #6–#11 (§1) is the one action that unblocks the most — every
other open item here is independent of that. §5 (bluemagic-front) and §8
(VeraCrypt volume) both need the user directly, not an agent, for their
next step. §6 (guidelines_IA's 4 skills) and §9 (homelab pool,
overpowers/zeroclaw) are both fully agent-actionable whenever picked up —
they're just not yet started, not blocked on anything external.
