# Completeness benchmark — all repos vs. agentic-pipeline doctrine

Date: 2026-09-03 · Rubric: [`COMPLETENESS-RUBRIC.md`](./COMPLETENESS-RUBRIC.md) (12 criteria, 2/1/0 each, max 24)

Scored mechanically from the filesystem and git metadata, not by eyeball. Third-party
checkouts (`ComfyUI`, `serena`, `FIS/reversa`, `sisvisa35*`) are excluded — they are
vendor code, not ours.

---

## Headline

| Cohort | n | median | mean |
|---|---|---|---|
| FIS / work repos | 7 | **20 / 24** | 17.9 |
| Personal (`BGavazzi`) repos | 21 | **6 / 24** | 7.9 |
| All | 28 | 7 / 24 | 10.4 |

**The doctrine was built at FIS and never propagated home.** The `guidelines_IA` →
`agentic-pipeline` constitution is followed almost perfectly by the repos it was
written for, and almost not at all by the personal portfolio — including the repos
that matter most for the job search (`clawdinha-do-rh`, `garimpo`, `baton`,
`worth-calculator-br`).

This is a *distribution* failure, not an authoring failure. The doctrine is good; it
has no delivery mechanism.

---

## Per-criterion breakdown (28 repos)

| Criterion | zero | partial | full | avg /2 |
|---|---:|---:|---:|---:|
| C1 AGENTS.md | 17 | 1 | 10 | 0.75 |
| C2 harness config (`.claude/`) | 17 | 0 | 11 | 0.79 |
| C3 continuity file | 21 | 0 | 7 | 0.50 |
| C4 task schema | 18 | 2 | 8 | 0.64 |
| C5 CHANGELOG | 19 | 1 | 8 | 0.61 |
| C6 README | 1 | 1 | 26 | 1.89 |
| C7 tests | 11 | 4 | 13 | 1.07 |
| C8 CI | 16 | 1 | 11 | 0.82 |
| **C9 gates wired** | **27** | **0** | **1** | **0.07** |
| C10 secret hygiene | 0 | 8 | 20 | 1.71 |
| C11 PR workflow | 16 | 1 | 11 | 0.82 |
| C12 closure law | 16 | 5 | 7 | 0.68 |

**C9 is the portfolio's defining gap.** Exactly one repo enforces the pipeline's own
gates, and that repo is `agentic-pipeline` itself — and until this change even it ran
only 2 of its 4 gates in CI (`scan_gate.py` and `blast_radius.py` shipped with tests
but were never invoked). The gates exist as artifacts, not as enforcement.

C3 (continuity) is the second gap and the one that costs the most per-session: 21 of
28 repos give an incoming agent nothing to resume from.

C6 (README) and C10 (secret hygiene) are portfolio strengths — no tracked `.env` or
credential file was found in any repo.

---

## Score table

| Repo | Tier | C1 | C2 | C3 | C4 | C5 | C6 | C7 | C8 | C9 | C10 | C11 | C12 | Total | % |
|---|---|--|--|--|--|--|--|--|--|--|--|--|--|---:|---:|
| agentic-pipeline | canonical | 1 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 1 | 2 | **22** | 91% |
| clickup_bot_CM_WA | active | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 0 | 2 | 2 | 2 | **22** | 91% |
| newshub-collector | active | 2 | 2 | 2 | 2 | 2 | 2 | 0 | 2 | 0 | 2 | 2 | 2 | **20** | 83% |
| bluemagic-events | active | 2 | 2 | 2 | 2 | 0 | 2 | 2 | 2 | 0 | 2 | 2 | 2 | **20** | 83% |
| bluemagic-front | active | 2 | 2 | 2 | 2 | 2 | 2 | 0 | 2 | 0 | 2 | 2 | 2 | **20** | 83% |
| PortalApp | active | 2 | 2 | 2 | 2 | 2 | 2 | 0 | 2 | 0 | 2 | 2 | 2 | **20** | 83% |
| clawdinha-do-rh | active | 2 | 2 | 0 | 1 | 0 | 2 | 2 | 2 | 0 | 2 | 2 | 1 | **16** | 66% |
| wa_ai_dev_hub | active | 2 | 0 | 0 | 0 | 2 | 2 | 2 | 2 | 0 | 2 | 2 | 1 | **15** | 62% |
| guidelines_IA | deprecated | 0 | 2 | 0 | 2 | 2 | 2 | 1 | 0 | 0 | 2 | 2 | 2 | **15** | 62% |
| wa_audio_bot_FIS | hibernating | 2 | 2 | 0 | 2 | 1 | 2 | 2 | 0 | 0 | 2 | 0 | 1 | **14** | 58% |
| motorista-exec | active | 2 | 2 | 0 | 0 | 0 | 2 | 1 | 2 | 0 | 2 | 0 | 1 | **12** | 50% |
| mixed-reality-photobooth | on-hold | 0 | 0 | 0 | 0 | 0 | 2 | 2 | 2 | 0 | 2 | 2 | 0 | **10** | 41% |
| teste_refactor_whitelabel | deprecated | 0 | 0 | 2 | 0 | 2 | 2 | 0 | 0 | 0 | 2 | 0 | 0 | **8** | 33% |
| cozy-coffee-iso | active | 0 | 2 | 0 | 0 | 0 | 2 | 0 | 0 | 0 | 1 | 2 | 0 | **7** | 29% |
| worth-calculator-br | active | 0 | 0 | 0 | 0 | 0 | 2 | 1 | 0 | 0 | 2 | 2 | 0 | **7** | 29% |
| wa-router | active | 0 | 0 | 0 | 0 | 0 | 2 | 2 | 0 | 0 | 2 | 0 | 0 | **6** | 25% |
| garimpo | active | 0 | 0 | 0 | 0 | 0 | 2 | 2 | 0 | 0 | 2 | 0 | 0 | **6** | 25% |
| baton | on-hold | 0 | 0 | 0 | 0 | 0 | 2 | 2 | 0 | 0 | 2 | 0 | 0 | **6** | 25% |
| homelab-demo-app | on-hold | 0 | 0 | 0 | 0 | 0 | 2 | 1 | 2 | 0 | 1 | 0 | 0 | **6** | 25% |
| feirinha | active | 0 | 0 | 0 | 0 | 0 | 2 | 2 | 0 | 0 | 2 | 0 | 0 | **6** | 25% |
| pr-dashboard | active | 0 | 0 | 0 | 0 | 0 | 2 | 0 | 1 | 0 | 2 | 0 | 0 | **5** | 20% |
| ile-loci-fungos | on-hold | 0 | 0 | 0 | 0 | 0 | 2 | 2 | 0 | 0 | 1 | 0 | 0 | **5** | 20% |
| ile-loci-fungi | on-hold | 0 | 0 | 0 | 0 | 0 | 2 | 2 | 0 | 0 | 1 | 0 | 0 | **5** | 20% |
| sismulta | hibernating | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 0 | 1 | **5** | 20% |
| homelab-iac | on-hold | 0 | 0 | 0 | 1 | 0 | 2 | 0 | 0 | 0 | 1 | 0 | 0 | **4** | 16% |
| voxel-scale-io | hibernating | 0 | 0 | 0 | 0 | 0 | 2 | 0 | 0 | 0 | 1 | 0 | 0 | **3** | 12% |
| sao-bernardino-brain | active | 0 | 0 | 0 | 0 | 0 | 2 | 0 | 0 | 0 | 1 | 0 | 0 | **3** | 12% |
| cv | active | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0 | **2** | 8% |

---

## Worktree map

Collapsed 30 directories into 6 canonical repos. **Bold = newest checkout**, i.e. the
one to open when resuming work.

**`clawdinha-do-rh`** — 1 clone + 11 worktrees + 3 stale dirs

| Dir | Branch | Last commit |
|---|---|---|
| `clawdinha_do_rh` | `fix/inhire-drop-a-link-uses-json-api` | 2026-08-03 · ⚠ 24 uncommitted |
| **`clawdinha-fidelity-skills`** | `fix/html-resume-months-gender-voice` | **2026-08-14** |
| `clawdinha-quanto-pedir` | `feat/quanto-pedir-salary-inversion` | 2026-08-13 · 1 dirty |
| `clawdinha-pii-ats-calibration` | `fix/pii-log-redaction-ats-calibration` | 2026-08-12 |
| `clawdinha-resume-scoping-fix` | `fix/resume-scoping-tenant-zero-fallback` | 2026-08-12 |
| `clawdinha-arc-andela` | `feat/arc-dev-andela-sources` | 2026-08-06 |
| `clawdinha-notifier-visibility` | `fix/notifier-silent-failures` | 2026-08-06 |
| `clawdinha-linkedin-login` | `fix/dockerignore-linkedin-sessions` | 2026-08-06 |
| `clawdinha-reentry` | `feat/reentry-summary` | 2026-08-06 |
| `clawdinha-tz-consistency` | `fix/brt-day-consistency` | 2026-08-06 |
| `clawdinha-gamification-tz` | `fix/tailor-loop-scheduler` | 2026-08-06 |
| `clawdinha-apply-loop` | `feat/apply-loop` | 2026-08-05 |
| `clawdinha-cv-undo-redo` | `feat/cv-edit-history` | 2026-08-04 |

Stale, no git — leftover dirs from removed worktrees, safe to `mv` to `.archive/`:
`clawdinha-fix-boards`, `clawdinha-fix-model-fallback`, `clawdinha-fix-recruitcrm`.

⚠ The main clone carries **24 uncommitted files** and is the *oldest* checkout. That
is the single most likely place to lose work.

**`bluemagic-events`** — `bluemagic-events` (06-21 12:34, 4 dirty) · **`bluemagic-events-webhook`** (`feat/webhook-push-dispatch`, **06-21 15:56**) · `bluemagic-events-autopop` (06-21 10:16) · `bluemagic-events-fix-rewrite-gateway` (06-19)

**`newshub-collector`** — **`newshub-collector`** (`feat/tag-llm-stage-collector`, **06-21 12:30**, 2 dirty) · `newshub-collector-pause` (06-21 11:55) · `newshub-collector-timeout` (06-20) · `newshub-collector-source-ops` (06-20) · `newshub-collector-fix-memory` (06-19)

**`clickup_bot_CM_WA`** — **`clickup_bot_CM_WA-webhook`** (`feat/realtime-webhook-consumer`, **06-21**) · `clickup_bot_CM_WA` (06-18)

**`bluemagic-front`** — **`bluemagic-front`** (`feat/lixeira-empresa-removida`, **06-04**) · `bluemagic-front-work` (05-10, 1 dirty)

**`wa_audio_bot_FIS`** — two independent clones, not worktrees: **`wa_audio_bot_FIS_test`** (**07-01**) · `wa_audio_bot_FIS` (03-30, detached HEAD)

---

## Findings

### 1. `agentic-pipeline`'s own `AGENTS.md` is an unfilled template (C1 = 1)
It still contains `<project_name>`, `<tier>`, `<maintainer>` placeholders. The
canonical repo does not model the thing it asks every other repo to do.

### 2. Two repos have no remote at all
`feirinha` and `sao-bernardino-brain` have commits but no `origin`. They exist only on
this laptop — no backup, no PR history. `feirinha` has 14 uncommitted files.

### 3. `cv` scores 2/24 — the lowest in the portfolio
It is public and it is the repo a recruiter is most likely to open.

### 4. Secret hygiene is clean, but eight repos lack an `.env` rule
No tracked `.env` or credentials file was found anywhere (C10 zero-count = 0). Eight
repos scored 1 only because `.gitignore` has no `.env` pattern — latent, not active.

### 5. `guidelines_IA` is a tombstone with content that never migrated
It scores 15/24 while declaring itself superseded. Files present there and absent from
`agentic-pipeline`: `MODEL-SELECTION.guidelines.md`, `AGENTS.balanced.md`,
`AGENTS.minimal.md`, `AGENTS.opus48.balanced.md`, `AGENTS.assessment.md`,
`AGENTS.usage-guidelines.md`, `.docs/analysis/`, `.docs/conventions/repo-tiering.md`,
`.docs/strategy/`, `.docs/admin/`, `.docs/skills/`, `.docs/tasks/` (23-task roadmap),
`.template/`, `infra/`, `publish-core.sh`. The tombstone is currently load-bearing.

---

## Recommended order of work

1. **Fill in `agentic-pipeline/AGENTS.md`.** Cheap, and it unblocks copying it.
2. **Finish the `guidelines_IA` → `agentic-pipeline` migration.** The canonical repo is
   missing the model-selection policy and the AGENTS variants — the two things another
   repo most needs when adopting the doctrine.
3. **Ship a `core-sync` script.** C1/C2/C3 fail in 17–21 repos because adoption is
   manual copy-paste. One command that drops `AGENTS.md` + `.claude/skills/` +
   `scripts/` into a target repo turns a 21-repo backlog into an afternoon.
4. **Commit or discard the 24 dirty files in `clawdinha_do_rh`,** and archive the three
   stale `clawdinha-fix-*` dirs.
5. **Give `feirinha` and `sao-bernardino-brain` a remote.**
6. **Roll C9 outward** to the four repos that already have CI and tests
   (`clawdinha-do-rh`, `wa_ai_dev_hub`, `bluemagic-events`, `mixed-reality-photobooth`).
