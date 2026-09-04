# agentic-pipeline

[![CI](https://github.com/BGavazzi/agentic-pipeline/actions/workflows/ci.yml/badge.svg)](https://github.com/BGavazzi/agentic-pipeline/actions/workflows/ci.yml)

Minimal agentic task-processing pipeline for Claude Code — skills, task lifecycle, and deterministic gates you can drop into any repo.

Pick up tasks from `.docs/tasks/`, run them through grounding → build → test → adversarial review → closure, and ship PRs — unattended or interactively. Every handoff between stages is either a **skill** (an LLM doing bounded, spec'd work) or a **deterministic gate** (a plain script that returns pass/fail with no model reasoning involved) — that split is the core design idea, and it comes up constantly below.

This README is the practical, implemented subset. [`GDFRSBT.md`](GDFRSBT.md) documents the broader eight-practice methodology (Goal/Domain/Feature/Readme/Spec/Behavior/Domain/Test-Driven Development) this repo operationalizes — read it if you want the philosophy; read this if you want to run the thing.

---

## Why it's shaped this way

Three failure modes kept recurring in earlier, less-structured attempts at agent-driven delivery, and most of what's below exists specifically to close one of them:

1. **An agent says "done" without having actually verified it.** A model can hallucinate a passing test run, mark a checkbox without exercising the behavior it claims, or read `grep import` and call something an orphan when it isn't. → **Deterministic gates** (`validate_task.py`, `blast_radius.py`, `validate_closure.py`) and the **proof-of-execution artifact** (§Concepts) exist so verification never depends on a model's self-report.
2. **An agent invents scope in autonomous mode.** Left running overnight, "keep going" can quietly turn into "derive new work from an old backlog nobody re-confirmed." → `dispatcher` only ever processes what's already in the queue with `status: todo`; see [`agent-conduct.md`](.docs/conventions/agent-conduct.md) §1.
3. **Documentation rots the moment code ships.** CHANGELOG, architecture decisions, and route maps drift from reality within a sprint. → **Closure Law §3** (§Concepts) makes updating them a gated, checked step of every task, not an afterthought.

---

## How the pipeline flows

```
                 ┌─────────────┐
   (optional)    │  grill-me   │  interrogate a vague plan/task until it's
                 └──────┬──────┘  actionable (PO/Designer + Developer lenses)
                        │
                        ▼
┌───────────────┐  ┌──────────────────┐  ┌─────────┐
│  dispatcher   │─▶│ codebase-grounding│─▶│ builder │
│ (picks NNNN,  │  │ (loads repo's own │  │ (writes │
│  opens branch)│  │  CLAUDE.md/AGENTS │  │  diff,  │
└───────────────┘  │  .md as a hard    │  │  commits│
                    │  constitution)    │  └────┬────┘
                    └──────────────────┘        │
                                                 ▼
                                        ┌──────────────────┐
                                        │  blast_radius.py │  (script, not a skill)
                                        │  → risk_level +  │
                                        │    required_gates│
                                        └────────┬─────────┘
                                                 ▼
                                          ┌─────────────┐
                                          │   tester    │  emits a proof-of-
                                          │ (prototype  │  execution artifact,
                                          │  mode V1)   │  not just prose
                                          └──────┬──────┘
                                                 ▼
                                          ┌─────────────┐
                                          │ ultrareview │  INDEPENDENT subagent,
                                          │ (adversarial│  re-runs the suite,
                                          │  gate)      │  hunts fake-green
                                          └──────┬──────┘
                                     BLOCK ◀──────┴──────▶ PASS
                                  (back to builder)         │
                                                             ▼
                                                      ┌─────────────┐
                                                      │  librarian  │  Closure
                                                      │             │  Law §3
                                                      └──────┬──────┘
                                                             ▼
                                                      ┌─────────────┐
                                                      │  notifier   │  PR comment
                                                      │             │  (+ ClickUp
                                                      └─────────────┘   opt-in)
```

`dispatcher` runs this whole chain per task, either once (`/dispatcher`) or repeatedly via `/loop /dispatcher`, gated at the end of every task by `quota_gate.py` (§Concepts). `codebase-audit` and `clickup-audit` sit **outside** this chain entirely — periodic, read-only housekeeping, not something the critical path waits on.

A note on terminology you'll find inside individual `SKILL.md` files: `ultrareview` describes itself as "stage 6 (Reviewer) of the Triple-Diamond," and `tester` references a `production` mode reserved for "post-Diamond-2 features." Neither "Triple-Diamond" nor "Diamond 2" is fully spelled out anywhere in this repo yet — best read as informal shorthand for a discover→build→close shape (roughly: **Diamond 1** = grill-me's divergent questioning → convergent shared understanding of the spec; **Diamond 2** = grounding→builder→tester's divergent implementation exploration → convergent working, tested code; **Diamond 3** = ultrareview→librarian→notifier's divergent adversarial scrutiny → convergent shipped, documented PR) rather than a precisely numbered stage list. The sequence diagram above is the part that's actually implemented and checkable; treat the Diamond/stage-number language you see in the skill files as color commentary until someone writes it up properly.

---

## Concepts you'll see everywhere

A glossary for terms that recur across `AGENTS.md`, `GDFRSBT.md`, and every `SKILL.md` — useful to have defined once instead of re-derived per file.

| Term | What it means |
|---|---|
| **Task** | One unit of work: `.docs/tasks/NNNN-*.md`, 4-digit ID, YAML frontmatter (`status`, `priority`, `type`, `blocks`/`blocked_by`, `clickup_id`) + body (§Context, §What To Do, §Affected Files, §Exit Conditions, §Required Documentation). Template: `.docs/tasks/000-template.md`. |
| **Closure Law §3** | The 7 (technically 8, counting PR approval) artifacts that must be addressed — updated **or** marked `[N/A]` with a one-line factual justification — before a task can move to `completed/`: CHANGELOG, function-catalog, SDD_KIT, README, continuity file, tests passing, ROUTE_BEHAVIOR_MAP, and an approved PR. Enforced by `validate_closure.py`, executed by `librarian`. "Small change" is not a valid `[N/A]` justification — the reason has to be structural (e.g. "CSS-only, no schema/route/API change"). |
| **Honest Backlog** | A section in the task file (and in a builder/tester's report) for anything left genuinely unresolved, with a one-line factual reason. The whole point is that "partially done + declared honestly" is a legitimate, trackable state — distinct from silently marking something `[x]` that wasn't actually verified. |
| **Dxx decision / `SDD_KIT.md`** | Every architectural decision that affects global behavior gets a flag (`D01`, `D02`, …) in the repo's `SDD_KIT.md`: the decision, the rejected alternative, and where it originated (often a task's §Divergences). Code references the flag in a comment (`# D07: retry 3x with backoff`). `librarian` proposes new flags; a human ratifies them. |
| **§Divergences** | Where `builder` records any point where the implementation diverged from the task's literal spec (different library, different endpoint shape, different schema). Never silent — a divergence is a candidate `Dxx` decision, not a shortcut. |
| **Proof-of-execution artifact** | A machine-checkable file (`.docs/test-reports/<NNNN>.json`, plus JUnit XML when the runner supports it) stamped with the exit code of every test step and the branch's git revision. This is what `dispatcher` and `ultrareview` gate on — **prose ("✅ all tests pass") is never trusted on its own**, because a model can write that sentence without having run anything. |
| **Fake-green** | The pattern `ultrareview` exists to hunt: an `it()`/`test()` block with no assertion, a tautological assert (`expect(true).toBe(true)`), a disguised skip (`it.skip` on a checkbox marked `[x]`), a snapshot stamped without checking the value, or a claim ("matches Figma", "route exists") made without an attached artifact to back it up. |
| **Blast radius / `risk_level` / `required_gates`** | `blast_radius.py`'s output (`.docs/blast-reports/<NNNN>.json`): which modules a diff plausibly touches (via a hand-maintained ownership map + import grep + historical co-change — three cheap, individually-sloppy signals unioned together, not a real dependency graph) and a resulting tier — `low` (isolated/leaf change), `medium` (touches shared code), or `high` (touches auth/RBAC/migrations/payments/infra manifests, or spans more than 8 modules). `tester` and `ultrareview` read this artifact instead of guessing scope themselves. |
| **Adversarial majority** | For `risk_level: high` findings only, `ultrareview` spawns 3 independent subagents whose job is to try to *refute* a finding. A finding survives (counts as real) only if the majority can't refute it — default-refuted keeps false positives down; default-not-proven on a bare "pass" keeps false negatives down. Reserved for high risk to avoid burning quota on routine changes. |
| **Grounding vs. Audit** | Two different verbs applied to two different scopes. *Grounding* (`codebase-grounding`, `clickup-grounding`) enriches a specific piece of upcoming work with current-state context, **before** acting. *Audit* (`codebase-audit`, `clickup-audit`) is a periodic, read-only, aggregate health check **against a repo's or workspace's own declared rules**, decoupled from any single task — it never gates the critical path. |
| **Prototype vs. production mode** (`tester`) | `prototype` (V1, the only mode actually runnable today) = type-check + lint + unit tests + "boots and responds" (health check, or `build`+`lint` for frontend, or full CDP-driven DOM assertion if `fe_real: true`). `production` (V2, not yet buildable) = adds a sandboxed DB, full regression suite, and contract tests — reserved for post-`Diamond-2` features, migrations, and RBAC. `tester` reads a repo's own declared tier (`.docs/conventions/repo-tiering.md`: `prototype`/`active`/`canonical`, set in that repo's `AGENTS.md` §1) to decide — no tier declared → conservative default `prototype`. |
| **Loop mode vs. single-shot** | `/dispatcher` processes exactly one task and stops. `/loop /dispatcher` re-fires itself via `ScheduleWakeup` after each task, bounded by the quota gate below — this is the unattended/overnight mode. |
| **Quota gate** | `quota_gate.py`, called after every task in loop mode. Reads `.claude/quota-state.json` (written by a statusline script off Claude Code's `rate_limits` injection — Pro/Max only) and enforces three ceilings plus a task cap: 70% of the rolling 5-hour window, 10 points/day and 50 points/week added to the 7-day window, and a max of 5 tasks per loop-day. Missing quota signal → fail-safe **STOP**, never a silent continue. This is the only authority on "can the loop keep going" — `dispatcher` never estimates quota itself. |
| **BYO (bring your own) credentials** | The pattern used throughout: a skill checks its own precondition (an env var like `CLICKUP_API_KEY` or `FIGMA_API_KEY`) at the top of its run, and if it's absent, prints setup instructions and exits — it never guesses, degrades silently, or fabricates a result. This is what lets platform-specific skills (ClickUp, Figma, WhatsApp) live in this same repo without forcing every user to configure all of them. |
| **`[[skill-name]]`** | The cross-reference notation used inside every `SKILL.md` to point at another skill's file (e.g. `[[builder]]` → `../builder/SKILL.md`). Not a wiki link anywhere outside this repo — just a lightweight convention for tracing "upstream/downstream" relationships between skills. |

---

## What's here

```
.claude/skills/          ← pipeline skills (invoke via Claude Code Skill tool)
  dispatcher/            ← orchestrator: reads task queue, chains all stages
  codebase-grounding/    ← enriches brief with repo context before building
  builder/               ← codegen: implements the task, runs tests
  tester/                ← validates §Exit Conditions, emits proof artifact
  ultrareview/           ← adversarial independent review (fake-green scanner)
  librarian/             ← Closure Law §3: updates CHANGELOG, SDD_KIT, README
  notifier/              ← posts structured comments to GitHub PR + ClickUp
  grill-me/              ← relentless plan/design interview (gate before build)
  codebase-audit/        ← read-only audit of repo against its own rules
  meta-test/             ← design spec for fixture-based skill tests (not yet implemented — see SKILL.md)
  clickup-api/           ← generic ClickUp API v2 reference (auth, rate limit, discovery) — BYO credentials
  clickup-grounding/     ← enriches a single ClickUp task with its own list/comment/blocker context
  clickup-audit/         ← read-only audit of a ClickUp workspace against its own conventions
  figma-api/             ← generic Figma REST API reference (auth, node fetch, image export) — BYO credentials
  figma-frontend-context/← turns a Figma frame/sticky into a structured implementation brief
  implement-figma-task/  ← builder specialization: writes the diff for a Figma-sourced brief
  visual-tester/         ← CDP screenshot + pixel diff vs. a reference image (design or baseline)
  zap-comms/             ← generic WhatsApp messaging over a self-hosted Evolution API instance — BYO instance
  whatsapp-clickup/      ← inbound WhatsApp message → ClickUp task, composed from zap-comms + clickup-api

scripts/
  quota_gate.py          ← daily/weekly token budget enforcement for /loop
  validate_task.py       ← validates .docs/tasks/*.md schema before dispatch
  validate_closure.py    ← validates Closure Law §3 compliance post-librarian
  blast_radius.py        ← diff-scoped blast-radius + risk-tier classifier
  scan_gate.py           ← SAST/SCA/secret-scan gate (Trivy/Semgrep/gitleaks/OWASP-DC via Docker), gated behind blast_radius's sast/sca required_gates

tests/
  test_blast_radius.py   ← real pytest unit tests for blast_radius.py (run in CI)
  test_scan_gate.py      ← real pytest unit tests for scan_gate.py's normalization/severity/degrade logic (run in CI)

.docs/
  tasks/
    000-template.md      ← template for new task files
    0001-*, 0002-*, ...  ← real open tasks tracking this repo's own backlog
  module-owners.md       ← hand-maintained ownership map, blast_radius.py's signal #1
  conventions/
    agent-conduct.md     ← how an agent must behave (scope, boards, grilling)
    git-pr-workflow.md   ← branch/PR lifecycle rules
    engineering-defaults.md ← coding defaults (backend, frontend, DB)
    notify-on-stop.md    ← agent must notify human before stopping unattended
    migration-timestamp.md ← DB migration naming convention (ms-timestamp, not sequential)

AGENTS.md                ← repo constitution (loaded by every Claude Code session)
GDFRSBT.md               ← the full 8-practice methodology this repo operationalizes a subset of
```

### The skills, grouped by what they're for

**Core pipeline** (no external credentials needed — works on any git repo):

| Skill | Reads | Produces | Hands off to |
|---|---|---|---|
| `dispatcher` | task queue, `quota-state.json` | branch, PR, task moved to `completed/` | orchestrates all of the below |
| `grill-me` | a plan/design/task in conversation | up to 5 (or 10, dual-variant) pointed questions **with a recommended answer each** | human/task-author reply |
| `codebase-grounding` | a brief + target repo's `CLAUDE.md`/`AGENTS.md`/`SDD_KIT.md` | the brief + a `codebase_context` block (constitution, tech stack, design system, conventions) | `builder` |
| `builder` | task + grounding output | commits on a branch, checkboxes marked, Closure Law addressed/`[N/A]`'d | `tester` |
| `tester` | branch + `blast_report` | prose test report + proof-of-execution artifact | `librarian` (pass) or `builder` (fail) |
| `ultrareview` | branch + tester's artifact + `blast_report` | independent PASS/BLOCK verdict, fake-green scan | `librarian` (pass) or `builder` (block) |
| `librarian` | branch + green tester report | Closure Law §3 commits, updated PR body | `notifier` |
| `notifier` | an event + payload | GitHub PR comment (always) + ClickUp comment (opt-in) | end of cycle |
| `codebase-audit` | a repo's own constitution | violation report (10 dimensions, 5 implemented) | human triage |
| `meta-test` | fixtures under `tests/skills/fixtures/` | pass/fail table per fixture | **design spec — no fixture exists yet, see its `SKILL.md`** |

**ClickUp adapters** (need `CLICKUP_API_KEY`):

| Skill | What it adds on top of `clickup-api` |
|---|---|
| `clickup-api` | the base adapter — auth, rate limiting, discovery, assignee/due-date resolution |
| `clickup-grounding` | pulls one task's list schema, comment history, and blockers before it reaches `codebase-grounding`/`builder` |
| `clickup-audit` | workspace-level housekeeping: naming drift, stale statuses, local↔ClickUp drift, unassigned tasks |

**Figma adapters** (need `FIGMA_API_KEY`; `visual-tester` additionally needs a CDP-reachable Chrome):

| Skill | What it does |
|---|---|
| `figma-api` | the base adapter — auth, node fetch, image export, comments |
| `figma-frontend-context` | turns a Figma frame or "sticky" comment into the structured JSON brief `codebase-grounding` expects |
| `implement-figma-task` | a `builder` specialization: maps the brief's target children onto real components (reusing the design system instead of cloning it) and writes the diff |
| `visual-tester` | screenshots the rendered result via CDP and pixel-diffs it against the Figma export (or a prior baseline) — the axis that closes the "build green ≠ looks right" gap in `tester`'s `fe_real` mode |

**WhatsApp adapters** (need a self-hosted Evolution API instance):

| Skill | What it does |
|---|---|
| `zap-comms` | the base adapter — send/read WhatsApp messages, check instance connection state |
| `whatsapp-clickup` | composes `zap-comms` + `clickup-api`: an inbound message becomes a created/updated ClickUp task, with a WhatsApp reply confirming what happened |

All nine adapter skills live in **this repo**, under the same `.claude/skills/` as the core ten — they're not a separate package or a vendored external repo. They're generic: no company, team, or bot persona is encoded in them, and each one checks its own precondition and prints setup instructions rather than guessing when a credential is missing (§BYO in the glossary above).

---

## The deterministic gates (`scripts/`)

These are the non-negotiable, model-free checks the skills above lean on. Each is a plain script — no LLM call, no network (except where noted) — precisely so a gate can't be talked out of failing.

- **`validate_task.py`** — schema validator for `.docs/tasks/NNNN-*.md`, run before `builder` picks up a task. Twelve checks (`F1`–`F12`): filename pattern, valid YAML frontmatter, required keys present, `status`/`priority`/`type` from a closed vocabulary, required sections present (`§Context`, `§What To Do`, `§Exit Conditions`) with at least one checkbox each, and — if `status: done` — every checkbox is either `[x]`, `[N/A]`, or accounted for in `§Honest Backlog`. Doesn't check whether the spec is *good*, only whether it's well-formed enough to hand to an agent without ambiguity.
- **`blast_radius.py`** — computes `risk_level` + `required_gates` from a git diff (see §Concepts: Blast radius). Deliberately imprecise: unions three cheap signals (hand-maintained `module-owners.md`, an import/grep heuristic, and historical co-change from git log) rather than building a real dependency graph.
- **`validate_closure.py`** — checks Closure Law §3 compliance on a task file before `librarian` (or a human) marks it `done`. Catches the "0/7 items, rest `[N/A]`" rubber-stamp pattern specifically.
- **`quota_gate.py`** — the STOP/CONTINUE authority for `/loop /dispatcher` (see §Concepts: Quota gate).
- **`scan_gate.py`** — the deterministic SAST/SCA/secret-scan half of what a paid tool like CodeRabbit/SonarQube would otherwise cover (the LLM-judgment half is `ultrareview`). Runs Semgrep, Trivy, and gitleaks as Docker images (`docker run --rm -v <repo>:/src <image> ...` — the BYO footprint is "has Docker," not four separate package-manager installs); OWASP Dependency-Check is opt-in only (`--enable-dependency-check`) since its vulnerability database needs an API key to sync at a usable speed. Normalizes all findings into a SARIF file plus a verdict JSON (`.docs/scan-reports/<NNNN>.{sarif,json}`) that `tester` reads as a required step whenever `blast_radius.py` marked the diff `sast`/`sca`. A `critical`/`high` finding on a changed file blocks (exit 1); Docker/scanners unavailable degrades honestly (`"degraded": true`, exit 0, no fabricated pass) rather than erroring or silently passing.

All five are covered by real pytest tests (`tests/test_blast_radius.py`, `tests/test_scan_gate.py` — both CI-run) — the only skill-adjacent things in this repo with actual automated test coverage today; `meta-test` describes the target architecture for testing the *skills themselves* but hasn't been built yet. One honest caveat on `scan_gate.py` specifically: its normalization/severity/degrade logic is unit-tested against canned tool-output fixtures, but the actual `docker run` invocations haven't been exercised against a live Docker daemon in this pipeline yet (no environment this was developed in had one reachable) — see the test file's own module docstring.

---

## The conventions (`.docs/conventions/`)

Shared rules referenced by §2 Hard Rules of any repo's `AGENTS.md` — promoted here because they're operational laws, not one person's preference.

- **`agent-conduct.md`** — "keep going" in autonomous mode never means inventing scope from an old backlog without per-feature confirmation; don't bulk-mutate shared boards without an explicit go-ahead; route questions to the audience that actually has the answer (product questions to a PO, not an agent); don't jump to "the API must have been deprecated" as a first hypothesis for an unexpected error.
- **`git-pr-workflow.md`** — never recycle a broken/wrong PR (open a new one, close the old one, don't pile up fixup commits or merge `main` back into a PR branch to "save" it); check a PR's merge state before stacking a new commit on its branch; in repos with automatic deployment, feature PRs target `integration`, not `main` directly (`main` mirrors staging, tags cut prod).
- **`engineering-defaults.md`** — coding defaults for backend/frontend/DB (e.g. every new UI component ships with its Storybook story in the same PR; reuse the canonical component instead of cloning a `ButtonV2`; design tokens, not hardcoded hex/px values).
- **`notify-on-stop.md`** — a long-running/autonomous agent must push a contextual notification to the human's async channel (not a static "Claude stopped" spam) via a `Stop` hook when it finishes a turn, deduplicated by content so silent turns don't page anyone.
- **`migration-timestamp.md`** — new DB migrations are named with a millisecond Unix timestamp, never a sequential/manual increment — avoids filename collisions across parallel branches.
- **`repo-tiering.md`** — the `prototype | active | canonical` vocabulary a repo declares in its own `AGENTS.md` §1, and how `tester` reads it to decide its mode (today: mostly documents intent, since `production` mode itself isn't buildable yet — see §Concepts).

---

## Quick start

### 1. Sync the core into your target repo
`.claude/skills/`, the gate scripts, and `.docs/conventions/` are meant to be
vendored into the repo you're actually building — this repo is the source,
not the workspace.

```
python scripts/core_sync.py /path/to/your-repo
```

This copies `.claude/skills/` (or a `--skills a,b,c` subset), the gate
scripts (`validate_task.py`, `validate_closure.py`, `blast_radius.py`,
`scan_gate.py`, `quota_gate.py`) into `<target>/scripts/`, and
`.docs/conventions/*.md` — and seeds `AGENTS.md` from a generic template
**only if the target has none yet** (an existing `AGENTS.md` is repo-specific
and is never overwritten). Use `--dry-run` to preview first. Re-run it any
time the core changes to re-sync; skills and gate scripts are meant to be
overwritten on each sync (that's what "core is read-only" means locally —
fix upstream here, then re-sync).

Alternatively, set `PIPELINE_SCRIPTS_DIR` to point at wherever you placed the
scripts instead of copying them in (`dispatcher` and `librarian` both read
this env var; default is `<repo>/scripts/`).

### 2. Fill in your constitution
If `core_sync.py` created a fresh `AGENTS.md` for you, edit it — fill in your
repo name, stack, and any project-specific rules. (If you already had one, it
was left untouched.)

### 3. Create a task
```
cp .docs/tasks/000-template.md .docs/tasks/0001-my-first-task.md
# edit it, fill in §What To Do and §Exit Conditions
```

### 4. Run the pipeline
```
# Interactive (single task):
/codebase-grounding
/builder
/tester
/ultrareview
/librarian

# Unattended (full queue, bounded by quota):
/dispatcher
# or: /loop
```

---

## BYO dependencies

| Skill | What you need |
|---|---|
| `dispatcher`, `librarian` | `gh` CLI, authenticated — both open/edit PRs via `gh pr create` / `gh pr edit` |
| `dispatcher`, `librarian` | `scripts/` (this repo's) copied into your target repo, or `PIPELINE_SCRIPTS_DIR` set |
| `validate_task.py`, `validate_closure.py` | Python 3 + `pyyaml` (`pip install pyyaml`) |
| `scan_gate.py` | Docker (daemon reachable, e.g. `docker info` succeeds) to run Semgrep/Trivy/gitleaks as containers — no native binaries needed. `--enable-dependency-check` additionally needs an NVD API key synced into the OWASP Dependency-Check image's data volume (slow without one — opt-in for a reason). Missing Docker degrades the gate honestly rather than erroring. |
| `dispatcher` (`/loop` unattended mode only) | `.claude/statusline_quota.py` writing `.claude/quota-state.json` from Claude Code's `rate_limits` injection (Pro/Max only), wired via `.claude/settings.json`'s `statusLine`. **Not bundled in this repo — you write it.** Without it, `quota_gate.py` fails safe (STOP) and `/loop` can't run unattended; interactive single-task use (step 4, top block) doesn't need this at all. |
| `notifier` | GitHub token (`GITHUB_TOKEN`) for PR comments; ClickUp token optional |
| `grill-me` | ClickUp API key (`CLICKUP_API_KEY`) for poll/per-task modes; interactive mode works without |
| `quota_gate.py` | No external deps — reads/writes `.claude/quota-state.json` (see `/loop` row above for how that file gets populated) |
| `clickup-api`, `clickup-grounding`, `clickup-audit` | `CLICKUP_API_KEY` (+ `CLICKUP_WORKSPACE_ID`/`CLICKUP_SPACE_ID` for grounding/audit) — no org, workspace, or bot persona baked in |
| `figma-api`, `figma-frontend-context`, `implement-figma-task` | `FIGMA_API_KEY` — no team/project/file baked in |
| `visual-tester` | A Chrome instance reachable via CDP (`--remote-debugging-port`), already logged into whatever the app under test requires; the CDP-attach + diff scripts (`live_shot.mjs`/`figma_export.mjs`/`diff.mjs`) are BYO, wired per repo |
| `zap-comms`, `whatsapp-clickup` | A self-hosted [Evolution API](https://github.com/EvolutionAPI/evolution-api) instance (`EVOLUTION_API_URL`, `EVOLUTION_API_KEY`, `EVOLUTION_INSTANCE_NAME`); `whatsapp-clickup` additionally needs `clickup-api`'s vars |

Every skill above sits idle (and costs nothing) until its own env vars are set — none of them guess, degrade silently, or fabricate a result when a credential is missing. Each `SKILL.md` documents its own precondition check and prints setup instructions instead.

## License

MIT
