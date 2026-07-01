# Portability Audit — agentic-pipeline skills

**Date:** 2026-07-01
**Scope:** `agentic-pipeline/.claude/skills/` — 10 skills audited
**Goal:** Determine whether each skill can run in a company-agnostic environment and what a new user must do to activate it.

---

## Summary table

| Skill | Tier | Blockers | Action |
|---|---|---|---|
| dispatcher | PLATFORM-COUPLED | Hard path to `guidelines_IA/scripts`; ClickUp baked in via notifier | Bundle scripts with pipeline; make notifier optional |
| codebase-grounding | READY | None | None |
| builder | BYO-KEY | Optional ClickUp + Figma integrations; requires `.docs/templates/PR_BODY_BUILDER.md` | Supply template; document optional integrations |
| tester | READY | `visual-tester` opt-in dep for `fe_real` mode | Document opt-in deps clearly |
| ultrareview | READY | `visual-tester` opt-in dep | Document opt-in deps clearly |
| librarian | BYO-KEY | Hard path to `guidelines_IA/scripts/validate_closure.py`; GitHub `gh` CLI required | Bundle scripts or make path configurable via env var |
| notifier | PLATFORM-COUPLED | ClickUp is the primary channel and required; member table is org-specific | Abstract channels; make ClickUp opt-in |
| grill-me | PLATFORM-COUPLED | ClickUp-native throughout; "All Blue" org space name hard-wired; Brazilian Portuguese mandated | Full rebuild needed to be org-agnostic |
| codebase-audit | READY | None | None |
| meta-test | READY | Sandboxes in `/tmp`; only builder tested today | Ensure test scripts ship with pipeline |

---

## Per-skill findings

---

### dispatcher

**Tier: PLATFORM-COUPLED**

**Org-specific references:**

1. Hard-coded path to org's internal repo (`guidelines_IA/scripts`):
   ```bash
   SCRIPTS_DIR=$(realpath <path>/guidelines_IA/scripts)
   ```
   This appears in §2 of the SKILL.md and is the gate to all three deterministic validators (`validate_task.py`, `validate_closure.py`, `quota_gate.py`). A new user has no `guidelines_IA` directory; the path is unresolvable as-is.

2. ClickUp is a mandatory downstream target. §4 step 8 reads:
   > `Invoke Skill(notifier) com event='pr.opened' + payload {clickup_id, pr_url, title}`

   And §5 output includes:
   > `ClickUp comment: <id>`

   There is no path where the dispatcher skips ClickUp notification. The `clickup_id` field in task frontmatter is treated as a standard output target.

3. Branch naming convention (`feat/<NNNN>-<slug>`) and task file naming (`NNNN-*.md`) are pipeline-internal conventions — not org-specific but must be understood by the new user.

**Workflow assumptions:**
- Assumes a specific two-repo topology: a `guidelines_IA` repo (scripts) and a `target_repo` (code). A new user would need to understand this split and either replicate it or point the scripts directory at whatever bundled location they choose.
- Quota gate assumes Claude Code Pro/Max `rate_limits` injection via `statusline_quota.py`. Any other billing model (API tokens, teams plan) will trigger STOP fail-safe.
- `integration` branch as base is checked via `git ls-remote` — org-specific branch topology assumption.

**BYO checklist for activation:**
- [ ] Place `validate_task.py`, `validate_closure.py`, `quota_gate.py` somewhere accessible and update `SCRIPTS_DIR` (or expose as env var `PIPELINE_SCRIPTS_DIR`)
- [ ] Set `CLICKUP_API_KEY` if ClickUp notifications are wanted (or disable notifier invocation)
- [ ] Configure `.claude/settings.json` statusLine to populate `quota-state.json`
- [ ] Ensure `gh` CLI is authenticated for PR creation
- [ ] Decide on base branch name (`integration` vs. `main`); the current logic auto-detects but the expectation is `integration` as the preferred branch

---

### codebase-grounding

**Tier: READY**

**Assessment:** Clean. The skill reads whatever rules the _target repo_ declares (`CLAUDE.md`, `AGENTS.md`, `SDD_KIT.md`, etc.) and enriches a brief with codebase context. No org-specific values are hard-coded.

The example rule quoted in §Step 0 — `"Every new HTTP endpoint requires a .bru file under docs/api/Blue Events API/"` — is clearly marked as an illustrative example from a `CLAUDE.md`, not a hard requirement of the skill itself.

The Portuguese-language search terms in §Step 4 (`rg "Publicadas|Agendadas|Rascunhos"`) are example search queries for an illustrative use case, not hard-coded behavior.

**Nothing a new user must do** — the skill works against any repo as-is. The only input required is `repo_path`, which is either passed explicitly or prompted.

---

### builder

**Tier: BYO-KEY**

**Org-specific references:**

1. Optional ClickUp integration:
   > `[[clickup-api]] se task tem clickup_id (sync status + post TL;DR como comment)`

   Activated only when the task frontmatter contains `clickup_id`. New users not using ClickUp can ignore this entirely.

2. Optional Figma integration:
   > `[[implement-figma-task]] se task é frontend com sticky Figma`

   Similarly opt-in.

3. `PR_BODY_BUILDER.md` template:
   > `PR body segue .docs/templates/PR_BODY_BUILDER.md (3 modos de review + Divergências)`

   This file must exist in the pipeline. If absent, the builder will not have a PR body template. New users must either supply this file or the builder will fail to find it.

4. The concrete example in §5 references `guidelines_IA` as the target repo name:
   > `Read AGENTS.balanced.md (guidelines_IA tem AGENTS.balanced)`

   This is narrative context in an example, not a hard code path. No blocker.

**Workflow assumptions:**
- Assumes the task `.md` format with frontmatter (`status`, `priority`, `type`, etc.) and the specific section headings (`§O Que Fazer`, `§Arquivos Afetados`, `§Condições de Saída`). This is pipeline convention, not org-specific — a new user must adopt this task format.
- Lei de Fechamento §3 (7 items) is a pipeline convention. Works generically.

**BYO checklist for activation:**
- [ ] Adopt the pipeline task format (frontmatter + section headings)
- [ ] Create `.docs/templates/PR_BODY_BUILDER.md` (can be minimal)
- [ ] Create `AGENTS.md` in the target repo (builder reads it for hard rules)
- [ ] `CLICKUP_API_KEY` only if tasks have `clickup_id` fields
- [ ] Figma token only if using `implement-figma-task`

---

### tester

**Tier: READY**

**Assessment:** Clean. The skill detects the test stack from the repo's own config files (`package.json`, `pyproject.toml`, `Makefile`, etc.) and adapts accordingly. No org-specific tooling is assumed.

The `fe_real` opt-in mode depends on `visual-tester` (Playwright CDP + `live_shot.mjs`) and an active Chrome debug session. This dependency is:
- Clearly flagged as opt-in (`fe_real: false` default)
- Documented to degrade gracefully: `"Sem o pré-requisito → degrada pra build+lint + warn (não inventa verde)"`

The artefact format (`.docs/test-reports/<NNNN>.json`) is a pipeline convention shared with dispatcher/ultrareview — any new user adopting the pipeline gets this for free.

**BYO checklist for activation:**
- [ ] Standard: nothing. Skill auto-detects the test stack.
- [ ] Optional `fe_real` mode: Chrome with CDP enabled + `visual-tester` scripts (`live_shot.mjs`, `figma_export.mjs`, `diff.mjs`)

---

### ultrareview

**Tier: READY**

**Assessment:** Clean. The adversarial review pattern is fully generic. The skill re-runs the test suite independently, inspects the diff for fake-green patterns, and optionally spawns adversarial sub-agents for high-risk findings.

The `visual-tester` dependency for UI claim verification is optional and clearly scoped:
> `Reusa: [[visual-tester]] (evidência visual p/ claims de UI)`

The fake-green scan patterns (empty `expect()`, tautologies, snapshot-only, skipped tests disguised as passing) are language/framework-agnostic.

The `Agent tool` dependency for the adversarial majority panel (`risk_level: high`) has a documented degradation path:
> `Agent tool indisponível (risco alto) → degradar pra 1 passada cética + WARN "maioria adversarial não rodou"`

**BYO checklist for activation:**
- [ ] Standard: nothing.
- [ ] Optional visual claim verification: `visual-tester` scripts
- [ ] Optional adversarial majority: `Agent` tool access (standard in Claude Code)

---

### librarian

**Tier: BYO-KEY**

**Org-specific references:**

1. Hard path to `guidelines_IA/scripts/validate_task.py` in §2 Preconditions:
   ```bash
   python <guidelines_IA>/scripts/validate_task.py "$task_path"
   ```
   The `<guidelines_IA>` placeholder is not resolved from any env var or config — it is an unresolved path that will fail for any new user.

2. Same issue with `validate_closure.py` in §3 step 4.5:
   ```bash
   python <guidelines_IA>/scripts/validate_closure.py "$task_path"
   ```
   This is the Lei de Fechamento §3 validation gate — a hard STOP if the script is missing.

3. GitHub `gh` CLI required for PR body update:
   > `gh pr edit <PR_NUMBER> --body-file <new_body.md>`
   Standard BYO-KEY pattern; not org-specific.

**Workflow assumptions:**
- Expects the seven-item Lei de Fechamento §3 checklist. This is a pipeline convention, not org-specific — a new user adopts it as part of the pipeline.
- `function-catalog.md`, `SDD_KIT.md`, `ROUTE_BEHAVIOR_MAP.md` are pipeline/repo conventions. Librarian handles absence gracefully with `[N/A]`.

**BYO checklist for activation:**
- [ ] Bundle `validate_task.py` and `validate_closure.py` with the pipeline and expose `PIPELINE_SCRIPTS_DIR` env var (or hardcode path after placement)
- [ ] `gh` CLI authenticated
- [ ] `AGENTS.md` present in target repo (read for Lei de Fechamento compliance)

---

### notifier

**Tier: PLATFORM-COUPLED**

**Org-specific references:**

1. ClickUp is the primary and non-optional V1 channel. The skill's entire §3 is dedicated to ClickUp comment mechanics. The opening description explicitly positions GitHub PR comment as co-equal V1 output, but the `CLICKUP_API_KEY` is required:
   > `| CLICKUP_API_KEY ausente | STOP, perguntar (não auto-fetch — segredo) |`

2. The member/mention table (§2) was sanitized but leaves a placeholder that still requires org-specific population:
   > `| (adicione membros da sua equipe aqui) | — | — |`

   Resolution of mentions requires ClickUp user IDs, which are workspace-specific.

3. Reference to org-specific memory:
   > `Memória [[clickup-api-org-conventions]] doc o gotcha — sempre seguir`

   This is a memory link to an org-specific convention document, not a portable reference.

4. V2 backlog mentions:
   > `WhatsApp via Evolution API (bot config)`

   Evolution API is the org's self-hosted WhatsApp gateway — not a generic solution.

**Workflow assumptions:**
- ClickUp task IDs (`clickup_id`) are expected in every task that goes through the full pipeline cycle. There is no code path in V1 that skips ClickUp when `clickup_id` is absent — unlike the builder, which gates on the field being present.
- The UTF-8 Windows-safe `--data-binary` pattern is a real technical requirement for Windows machines; non-org-specific but noteworthy.

**BYO checklist for activation:**
- [ ] `CLICKUP_API_KEY` — workspace-specific, set via env var
- [ ] Populate §2 member table with your team's ClickUp user IDs and GitHub handles
- [ ] Remove or replace the `[[clickup-api-org-conventions]]` memory reference with a local doc
- [ ] Decide whether to enable V2 channels (Slack/Discord/Telegram) from the backlog; none are runnable in V1

**To make READY:** Refactor §1 inputs to make `clickup_id` truly optional (skip ClickUp steps when absent); make GitHub-only mode a first-class path.

---

### grill-me

**Tier: PLATFORM-COUPLED**

This skill is the most tightly coupled to org-specific infrastructure and culture.

**Org-specific references:**

1. "All Blue" space name — baked into the description and poll mode:
   > `Scan the All Blue space for newly created tasks`

   "All Blue" is the org's ClickUp space name. A new user has no "All Blue" space; the `$CLICKUP_SPACE_ID` env var mitigates the hardcode but the concept is ClickUp-native throughout.

2. ClickUp-native architecture — the entire per-task mode (§Mode 2) and poll mode (§Mode 3) post to ClickUp task comments and poll ClickUp for new tasks. There is no GitHub Issues, Linear, Jira, or generic adapter.

3. `CLICKUP_BOT_USER_ID` and `CLICKUP_SPACE_ID` are mandatory env vars for modes 2 and 3.

4. `member-roles.json` file mapping ClickUp user IDs to roles — org-specific:
   > `"<user-id>": { "name": "PO Name", "roles": ["po"] }`

   These are ClickUp-workspace-specific numeric user IDs. A new user must re-populate this entirely.

5. Language mandate:
   > `Write in Brazilian Portuguese, not European Portuguese.`
   > `Match how a Carioca PM writes in Slack`

   Both are org-specific cultural requirements. "Carioca PM" (PM from Rio de Janeiro) makes this explicitly tied to the org's team demographic. `LGPD` (Brazilian data protection law) appears in the question framework.

6. Example task IDs in the walkthrough appear to use real ClickUp format IDs (`86c1abc`, `86c1def`) — plausibly from the org's own workspace, though they read as illustrative.

7. Reference to internal pattern:
   > `../clickup-api/SKILL.md — full ClickUp API reference`

   Assumes the `clickup-api` skill is a sibling in the same skills directory.

**Workflow assumptions:**
- The entire Phase B (reply scanning) is built around monitoring ClickUp comment threads. The `~/.claude/skills/grill-me/state/grilled-tasks.json` cache is keyed on ClickUp task IDs.
- The "relentless grilling" concept and the question frameworks (PO variant, Developer variant) are generic and reusable — these are the portable core.

**BYO checklist to get partial value (interactive mode only):**
- [ ] Skip modes 2 and 3 entirely; use mode 1 (interactive `/grill-me`) which has no ClickUp dependency
- [ ] Rewrite language section to remove Brazilian Portuguese mandate and "Carioca PM" reference

**To make READY for any org:** Strip ClickUp coupling entirely; replace per-task mode with a generic "read task from file / GitHub Issue / Jira ticket" input; make language configurable; make `member-roles.json` schema generic (no ClickUp user IDs).

---

### codebase-audit

**Tier: READY**

**Assessment:** Clean. The skill audits a repo against its _own_ declared rules (`CLAUDE.md`, `AGENTS.md`, `SDD_KIT.md`). It does not assume any org-specific rules — it reads them from the target repo.

The report example in §6 quotes the phrase `"Every HTTP endpoint requires a .bru file under docs/api/Blue Events API/"` — this is clearly an illustrative quote from one specific repo's CLAUDE.md, not a hard-coded rule of the audit skill itself.

The NestJS decorator pattern used in check 4.1 (`@(Get|Post|Put|Patch|Delete)\(`) is one implementation of endpoint detection. The skill is designed to find endpoints based on the repo's constitution, so a Django or Express repo would need slightly different patterns — but this is a limitation of the example implementation, not an org coupling.

The check for `.bru` files (Bruno API client) in check 4.1 is also derived from whatever the repo's CLAUDE.md requires; the skill does not assume `.bru` files are mandatory.

**BYO checklist for activation:**
- [ ] Nothing. Point at any repo with a `CLAUDE.md` or `AGENTS.md` and run.
- [ ] Optional: populate `ROUTE_BEHAVIOR_MAP.md` and `SDD_KIT.md` in the target repo to enable checks 4.2 and 4.3.

---

### meta-test

**Tier: READY**

**Assessment:** Largely clean. This is the pipeline's self-test harness — it tests the other skills using isolated sandbox repos.

The only item worth noting for a new user:
- Sandboxes are created in `/tmp/test-<fixture_name>/` (line: `Bash: tests/skills/lib/setup.sh <fixture_name>` → `cria /tmp/test-<fixture_name>/`). On Windows, `/tmp` may not exist. The hard rule `**Nunca executa contra repo real** — sempre sandbox em /tmp/test-*/` will need to use the platform temp directory.
- The test scripts (`tests/skills/lib/setup.sh`, `assert.sh`, `teardown.sh`) must ship with the pipeline. They are referenced but not defined in the SKILL.md.
- Only the builder skill has working fixtures today; tester and notifier fixtures are TODO.
- The `007-notifier-clickup-comment` fixture (TODO) will require ClickUp credentials when implemented.

**BYO checklist for activation:**
- [ ] Ensure `tests/skills/lib/` scripts ship with the pipeline package
- [ ] On Windows: update sandbox path from `/tmp/` to `$TEMP` or equivalent
- [ ] Run `001-trivial-readme-edit` to confirm baseline works in your environment

---

## Cross-cutting observations

### Scripts dependency (`guidelines_IA/scripts`)
Two skills (dispatcher, librarian) reference Python scripts at an unresolved `<path>/guidelines_IA/scripts` location. These scripts are the pipeline's deterministic gates. For the pipeline to be portable, they must be bundled inside `agentic-pipeline/` itself (e.g., under `scripts/`) and referenced via a single configurable env var (`PIPELINE_SCRIPTS_DIR`).

### ClickUp as a first-class assumption
Three skills (dispatcher, notifier, grill-me) treat ClickUp as a required integration. The builder and librarian treat it as optional. For a truly org-agnostic pipeline, ClickUp notification should be opt-in across all skills: present `clickup_id` in task frontmatter → notify; absent → skip silently.

### Language / culture coupling (grill-me only)
The Brazilian Portuguese mandate and the "Carioca PM" style reference in grill-me are the most culturally specific items in the entire skill set. They have no equivalent in any other skill. This is a deliberate design choice but is the single biggest barrier to adoption by international teams.

### What is already portable
The core pipeline loop (grounding → build → test → review → document) implemented across codebase-grounding, builder, tester, ultrareview, and librarian is well-abstracted. These five skills rely on the repo's own rules and test infrastructure, not on any org-specific tooling. A new team could adopt them immediately after addressing the `guidelines_IA/scripts` path issue in librarian.
