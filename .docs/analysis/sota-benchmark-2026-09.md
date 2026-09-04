# SOTA Benchmark: Agentic Development Pipeline Governance (2026-09)

Scope: where `agentic-pipeline` (BGavazzi/agentic-pipeline, formerly `guidelines_IA`) sits relative to the public state of the art in AI-coding-agent governance, as of 2026-09-03. Star/activity counts pulled live from the GitHub API on that date.

---

## TL;DR

1. **AGENTS.md won the instruction-file format war.** Formalized Aug 2025 (OpenAI + Google/Cursor/Factory), donated to the Linux Foundation's Agentic AI Foundation Dec 2025, 60k+ adopting repos, 20+ tools including GitHub Copilot (native support since Aug 2025). Our `AGENTS.md` template variants sit on top of this substrate correctly.
2. **The public spec is deliberately weak: plain Markdown, no required sections, no schema, no enforcement.** Everything mandatory in our repo — §0 continuity protocol, §3 Task Closure Law, §4 YAML-frontmatter task schema — is *our* invention layered on top of a format that, in the wild, is closer to a README.
3. **Spec-driven development is now mainstream and well-funded**: GitHub spec-kit (133k★, Constitution→Specify→Plan→Tasks→Implement), BMAD-METHOD (52.6k★, multi-persona agile), Amazon Kiro (requirements→design→tasks, native IDE), Tessl (spec-as-artifact, spec registry). Our GDFRSBT is a legitimate peer of these, not a toy — but none of ours is a CLI/slash-command product, so it has zero install-and-go distribution.
4. **Nobody in the public ecosystem ships an automated, git-diff-scoped "Closure Law" gate.** BMAD has a Definition-of-Done *checklist*, human- or agent-checked at persona handoff; spec-kit's `/analyze` is read-only consistency checking. Our `validate_closure.py` enforcing 7 mandatory artifacts as a CI-blocking gate is more mechanical than anything found.
5. **Blast-radius / change-risk classification is a live, named category** (CodeRabbit "Security Blast Radius", `sem` by Ataraxy-Labs, Meta's RADAR system) but it is a *review-prioritization* aid everywhere else, not a merge-blocking CI gate keyed to a task ID. `blast_radius.py` doing that as a hard gate is uncommon.
6. **We found no public prior art for the exact bug we just fixed** (a diff-scoped risk classifier failing to flag edits to its own gate scripts / CI workflow as high-risk). The closest documented parallel is the CodeRabbit "PwnedRabbit" RCE (privileged CI trusting PR-supplied config) and generic advice to CODEOWNERS-protect `.github/workflows/`. Nobody publicly documents an *automated classifier* doing this self-check — ours may be a genuinely novel gate.
7. **Self-hosted runner security best practice has converged hard on ephemeral, JIT-token, one-job-per-VM/pod.** Our homelab pool is currently non-ephemeral/persistent (per the shipped CI routing), which is the exact anti-pattern GitHub's own docs and every hardening guide warn about. This is the single clearest gap to close.
8. **GitHub personal (non-Org) accounts genuinely cannot use native runner groups** — confirmed via GitHub docs: runner groups require an Org or Enterprise. Our "shared label" emulation is the correct workaround, not a shortcut.
9. **Model-routing-by-task-tier is now a documented, common pattern** (cheap/mid/frontier tiers by task difficulty) — our `MODEL-SELECTION.guidelines.md` is directionally aligned but isn't migrated into this repo yet, and nobody's public routing policy is wired into a CI quota gate the way our `quota_gate.py` is.
10. **Cross-session continuity files are a recognized-but-unstandardized pattern** (`.agents/continuity-<agent>.md` analog: "agent-handoff", akitaonrails/ai-memory, ESAA-Conversational academic work) — no dominant convention exists; ours is a reasonable implementation of an open problem, not a laggard.

---

## Landscape map

| Project | Link | What it is | Governance primitives it ships | Activity/adoption (2026-09-03) |
|---|---|---|---|---|
| **openai/codex** | github.com/openai/codex | OpenAI's CLI coding agent | Own `AGENTS.md` (dogfooded), layered global/project/nested instruction chain, `AGENTS.override.md` precedence | 121,167★, pushed same day — very active |
| **github/spec-kit** | github.com/github/spec-kit | Spec-driven-development toolkit/CLI, 30+ agent backends | `constitution.md`, `specify`/`plan`/`tasks`/`implement`/`clarify`/`analyze` slash commands, read-only consistency checker | 133,244★ — explosive growth, pushed same day |
| **bmad-code-org/BMAD-METHOD** | github.com/bmad-code-org/BMAD-METHOD | Multi-persona "agile AI-driven development" framework | 12+ specialized agent personas (PM/Architect/Dev/QA/SM), stage-transition quality gates, Definition-of-Done checklists | 52,639★, active |
| **OpenHands/OpenHands** (was All-Hands-AI) | github.com/OpenHands/OpenHands | Open, self-hostable autonomous coding-agent platform | Ships its own `AGENTS.md`; SDK/harness for custom runtimes; CI (lint/test/build) gates on itself | 86,068★, active |
| **cline/cline** | github.com/cline/cline | VS Code agent extension, plan-then-diff-approval model | `.clinerules/` directory (scoped rule files, frontmatter-gated), enterprise tier adds SSO/RBAC/policy/audit trail | 67,402★, active |
| **aaif-goose/goose** (was block/goose) | github.com/aaif-goose/goose | Block's open agent, now under Linux Foundation's Agentic AI Foundation | `.goosehints` (single-file convention, weaker than `.clinerules`), YAML "recipe" runner for repeatable workflows | 53,879★, active |
| **SWE-agent/SWE-agent** (was princeton-nlp) | github.com/SWE-agent/SWE-agent | Academic (NeurIPS'24) issue-to-PR agent, Agent-Computer Interface (ACI) design | No repo-governance layer — it's a research harness for solving SWE-bench-style issues, not a team-policy tool | 20,209★, active |
| **ruvnet/ruflo** (was claude-flow) | github.com/ruvnet/ruflo | Multi-agent swarm orchestration layer for Claude Code/Codex | SPARC methodology, 60+ agent roles, "hive-mind" coordination, persistent memory/MCP bridging | 70,315★, active — renamed mid-2026 |
| **RooCodeInc/Roo-Code** | github.com/RooCodeInc/Roo-Code | VS Code agent, Cline fork, 5 built-in modes (Code/Architect/Ask/Debug/Orchestrator) | Per-mode system prompts/tool permissions/rule files — the most granular rules-by-role system found | 24,313★ — **archived, project shut down ~May 2026** |
| **actions/actions-runner-controller (ARC)** | github.com/actions/actions-runner-controller | Kubernetes operator for self-hosted GH Actions runners | Ephemeral, one-pod-per-job runner scale sets; Kubernetes-mode vs Docker-in-Docker mode | 6,476★, active |
| **myoung34/docker-github-actions-runner** | github.com/myoung34/docker-github-actions-runner | Docker image wrapping the official runner binary, used for homelab/single-box pools | No governance built in — explicitly warns that env vars aren't safe from exfiltration and workflow changes must be gated | 2,447★, active |
| **Ataraxy-Labs/sem** | github.com/ataraxy-labs/sem | Entity-level (tree-sitter, 28 languages) semantic diff/blame/impact tool "built for coding agents" | Pre-commit hook showing entity-level blast radius of staged changes — closest public analog to `blast_radius.py`'s intent | 3,332★, newer/smaller |
| **anthropics/claude-code-action** | github.com/anthropics/claude-code-action | Official GitHub Action wiring Claude Code into PR/issue workflows | Actor-permission checks, blocks external contributors/bots unless allow-listed, restores base-ref config in PR context | 8,783★, active |
| **hesreallyhim/awesome-claude-code** | github.com/hesreallyhim/awesome-claude-code | Curated list of Claude Code skills/hooks/subagents/plugins | Not a governance tool itself — the closest public analog to cataloguing what our vendored skills (grill-me, builder, tester, librarian…) resemble | 53,443★, active |
| **disler/claude-code-hooks-mastery** | github.com/disler/claude-code-hooks-mastery | Reference implementation of every Claude Code hook type | Builder/Validator agent pattern, prompt-submit validation, command-blocking security hooks | 3,907★, moderate |
| Cognition **Devin** | cognition.com | Closed-source autonomous engineer product | Self-review before PR, "Devin Review" for human PR comprehension, FedRAMP High (gov compliance framework) — no open governance artifacts to inspect | N/A (closed source) |

Not found as a public/open project: **sourcegraph/amp** returned 404 on the GitHub API — Amp appears to be closed-source or not published under that path; no public governance artifacts could be verified.

---

## Standards status

**AGENTS.md** (agents.md) — the only one of these with a real claim to "spec" status.
- History: formalized as an open specification in Aug 2025 by OpenAI with Google (Jules/Gemini), Cursor, and Factory; donated to the **Agentic AI Foundation under the Linux Foundation** in Dec 2025.
- Format: plain Markdown, **no required schema, no required sections** — "just standard Markdown, use any headings you like." Common but non-mandatory sections: overview, setup/build/test commands, code style, testing instructions, PR/security notes.
- Discovery/precedence (Codex's implementation, representative of the ecosystem): global (`~/.codex/AGENTS.md`) → project root → nested directories, more-local wins; `AGENTS.override.md` beats `AGENTS.md` where present.
- Adoption: 60,000+ open-source projects, 20+ tools (Codex, Cursor, Copilot [native, Aug 2025], Google Jules/Gemini, Factory, Amp, Windsurf, Zed, Roo Code before its shutdown, OpenHands, Aider).
- Explicit limitation acknowledged by the ecosystem itself: it "shapes behavior through instruction, not enforcement" and is "not a long-term memory system" — static, loaded at startup, no learning.

**CLAUDE.md** — Anthropic convention, not a spec. No required schema; Anthropic's own guidance is "keep it under 200 lines," point at files rather than describe them, treat it as a living document Claude itself edits on correction. No cross-tool ambition — it is Claude Code–specific, coexists with `AGENTS.md` in the same repo in practice.

**Cursor `.cursor/rules/*.mdc`** — the most *mechanically* sophisticated of the instruction-file conventions: YAML frontmatter (`description`, `globs`, `alwaysApply`) gives path-scoped and conditional activation, i.e. rules can auto-load only for matching files. This is a capability our flat `AGENTS.md` variants don't have — Cursor's system is closer to a routing table than a single doctrine file. Legacy single `.cursorrules` still works but is deprecated in favor of the directory form.

**GitHub Copilot** — `.github/copilot-instructions.md` (repo-wide, no schema) plus `.github/instructions/*.instructions.md` (frontmatter-scoped, same idea as Cursor's globs) for the coding agent and PR-review flows specifically. Copilot added native `AGENTS.md` parsing in Aug 2025, so a repo can now serve one file to both ecosystems.

**Net assessment**: our repo's real differentiator was never the *instruction file* — that space is a commodity now, standardized, and we're correctly building on it rather than competing with it. Our differentiator is everything layered on top (Closure Law, task schema validator, gates) that the standard explicitly declines to specify.

---

## Feature matrix

Columns: **Ours** = agentic-pipeline. Others chosen for genuine overlap with our category (governance/pipeline layer), not raw popularity.

| Capability | **Ours** | spec-kit | BMAD-METHOD | OpenHands | Cline | Goose | SWE-agent | Devin (Cognition) |
|---|---|---|---|---|---|---|---|---|
| Agent constitution file | **Yes** — `AGENTS.md` in 4 variants, §0–§5 mandatory | Yes — `constitution.md` via `/constitution` | Partial — persona files + `core-config`, no single doctrine | Yes — ships own `AGENTS.md` | Partial — `.clinerules/` dir, no mandated sections | Partial — single `.goosehints` file | No | Unknown (closed) |
| Task schema validator | **Yes** — `validate_task.py`, YAML frontmatter (status/priority/type/clickup_id/parent/blocks) | No — `tasks.md` is a checklist, not schema-validated | Partial — story template convention, not machine-validated | No | No | No | No | Unknown |
| Closure/DoD gate (CI-blocking) | **Yes** — `validate_closure.py`, 7 mandatory artifacts, blocks merge | Partial — `/analyze` is read-only, doesn't block | Partial — DoD checklist, enforced at persona handoff, not CI | No | No | No | No | Claimed (self-review before PR) but unverifiable — closed |
| Static-analysis gate (SAST/secrets, SARIF) | **Yes** — `scan_gate.py`, Semgrep/Trivy/gitleaks as Docker images → SARIF | No | No | Standard CI only (lint/test/build) | No | No | No | Unknown |
| Risk/blast-radius classifier (diff-scoped, CI-blocking) | **Yes** — `blast_radius.py`, ownership map + import-grep + co-change heuristic | No | No | No | No | No | No | Claimed internally, not public |
| Quota/cost governor wired into CI dispatch | **Yes** — `quota_gate.py` | No | No | No | No | No | No | No |
| Continuity/memory across sessions | **Yes** — `.agents/continuity-<agent>.md` | No | Partial — story files carry state forward | No standardized file | No | No | No | Unknown |
| Spec-driven method (structured, named) | **Yes** — GDFRSBT (Goal/Domain/Feature/Readme/Spec/Behavior/DDD/Test) | Yes — Constitution→Specify→Plan→Tasks→Implement, **CLI product, 133k★** | Yes — full SDLC persona pipeline, **52.6k★** | No | No | No | No | Proprietary equivalent, unverifiable |
| Model routing policy (task→model tier) | Partial — `MODEL-SELECTION.guidelines.md` exists in predecessor repo, **not yet migrated** | No | No | No | No | No | No | Unknown |
| Skill/subagent library | **Yes** — 8 vendored skills (grill-me, builder, tester, librarian, codebase-grounding, notifier, dispatcher, codebase-audit) | No (commands, not skills) | Yes — 12+ personas, arguably richer role separation | No | No | Yes — YAML "recipes" | No | Unknown |
| Self-hosted runner pool (for agent CI workloads) | Partial — shipped today, **fork-PR pinned to GitHub-hosted, pool opt-in via repo var, label-emulated (personal account)** | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| Eval/benchmark harness | No — no SWE-bench-style suite, no fake-green detector beyond `ultrareview` skill's adversarial pass | No | No | Yes — integrates with SWE-bench-style evals | No | No | **Yes — this is SWE-agent's whole purpose (SWE-bench)** | Yes (internal, published selectively) |

---

## Where we are ahead

Specific and verifiable, not just "we have more files":

- **CI-blocking Closure Law is unusual.** Every DoD-style mechanism found elsewhere (BMAD's checklist, spec-kit's `/analyze`) is advisory or agent-self-checked at best. Ours is a Python script in the merge-gating CI job that structurally can't be talked past by an agent that's in a hurry, because it isn't the agent enforcing it.
- **Task schema + gate combo is genuinely rare.** Nobody surveyed validates a machine-readable task frontmatter schema (status/priority/clickup_id/parent/blocks) as a CI gate. spec-kit's `tasks.md` and BMAD's stories are both prose checklists a human or agent reads, not YAML a script parses and rejects.
- **`quota_gate.py` has no public analog we could find wired specifically into a coding-agent CI pipeline.** LLM cost-governor patterns exist (token buckets, per-agent rate limits) but as API gateways in front of runtime traffic, not as a pre-dispatch CI gate tied to a ticket/task queue.
- **The blast-radius-must-cover-its-own-gates fix has no documented public precedent.** This is worth being confident about: searches for the general problem class (CI trusting PR-supplied config that can defang the pipeline) return only the generic CODEOWNERS-branch-protection mitigation and the CodeRabbit "PwnedRabbit" RCE writeup — nobody describes an *automated risk classifier* that specifically flags edits to its own gate definitions as high-risk. If accurate, this is a legitimately original contribution, not a reinvention.
- **Vendored skill library maps 1:1 onto SDLC roles** (grounding → build → test → adversarial review → close → notify) in a way BMAD's persona system approaches but spec-kit and the raw AGENTS.md ecosystem don't attempt at all — most tools stop at "write the code," ours has librarian/notifier/ultrareview stages most competitors lack entirely.
- **Fork-PR routing to GitHub-hosted while keeping a trusted-event path to a homelab pool, gated behind an explicit opt-in repo variable**, is a sounder default posture than the myoung34 image's own docs warn about (that image explicitly does nothing to gate untrusted PRs — it's on the operator to add that, which we did).

## Where we are behind / gaps to close

Ranked by how load-bearing the gap is, each with concrete public prior art to copy from.

1. **Runners are not ephemeral/JIT.** This is the sharpest gap. GitHub's own `actions/runner` supports JIT (just-in-time) single-use registration tokens (`docker-github-actions-runner`'s wiki, GitHub's 2023 JIT changelog); ARC's whole model is one-pod-per-job, destroyed after. A persistent homelab runner accumulates shell history, cached credentials, and workspace remnants across jobs — exactly the persistence vector the Sysdig writeup on self-hosted-runners-as-backdoors describes. **Fix**: even without Kubernetes, `myoung34/docker-github-actions-runner` supports an ephemeral flag (`--ephemeral`/`EPHEMERAL=true`) that de-registers after one job; wrap that in a supervisor (systemd + a re-registration loop, or a slim `act_runner`-style watcher) so the homelab pool re-provisions per job instead of running long-lived containers. Copy: `actions/actions-runner-controller` for the target architecture even if Kubernetes itself isn't adopted; `docker-github-actions-runner`'s `--once`/ephemeral usage docs for the minimal single-box version.
2. **No eval/benchmark harness.** SWE-agent exists purely to be scored against SWE-bench; OpenHands wires into SWE-bench-style evals natively. We have no equivalent — `ultrareview` catches fake-green patterns in a single PR but there's no held-out task suite to regression-test the *pipeline itself* (does a new blast-radius rule still correctly gate a known-bad diff?). Worth at minimum a small fixture suite (the `meta-test` skill is a start, but it tests skills, not the gates' classification accuracy over time).
3. **Model routing is written but not shipped.** `MODEL-SELECTION.guidelines.md` lives in the predecessor repo and per the task brief hasn't been migrated. The public pattern (cheap/mid/frontier by task-difficulty tier) is well-documented now — migrate it into `agentic-pipeline` and, if there's appetite, wire it as an actual router rather than a static doc, the way `quota_gate.py` already governs dispatch volume.
4. **No path-scoped rule activation.** Cursor's `.mdc` frontmatter (`globs`, `alwaysApply`) and Copilot's `.instructions.md` both let different parts of a monorepo load different rules automatically. Our `AGENTS.md` variants are flat, whole-repo files (balanced/minimal/opus48/assessment picked per-repo, not per-directory). For a monorepo this becomes a real limitation — worth stealing the frontmatter-glob pattern for a future `AGENTS.d/` layout.
5. **Skill/persona breadth is behind BMAD's 12+ roles.** BMAD splits Analyst/PM/Architect/Dev/QA/SM as distinct agents with distinct handoff contracts; our 8 skills cover build/test/close/notify well but nothing plays the "Analyst/PM" upstream role (turning a vague idea into a scoped brief) beyond `grill-me`. Not urgent, but a documented gap if the pipeline is ever asked to originate work rather than execute pre-scoped ClickUp tickets.
6. **No SARIF-consuming policy layer beyond upload.** `scan_gate.py` emits SARIF and we upload it to code scanning, which is table stakes (matches the common Semgrep+Trivy+gitleaks→SARIF pattern everywhere). What's missing relative to more mature setups is OpenSSF Scorecard-style continuous repo-health scoring (branch protection, review requirements, dependency posture) — cheap to add (`ossf/scorecard-action`), currently absent.

## Homelab runner pool notes

What we shipped today, restated precisely from `.github/workflows/ci.yml`: a `route` job inspects `github.event.pull_request.head.repo.fork` — true → pinned to `ubuntu-latest` (GitHub-hosted) regardless of pool settings; false → routes to `["self-hosted","linux","x64","homelab-pool"]` only if the repo variable `USE_HOMELAB_POOL` is `true`, otherwise still GitHub-hosted. This is a **trust-boundary-correct default**: it matches the consensus mitigation found everywhere in the research — GitHub's own secure-use docs, the Wiz hardening guide, and the `community` discussion on self-hosted-runner risk all converge on "never let a fork-PR touch a self-hosted runner; run fork-PR workflows with a read-only token and no secrets on GitHub-hosted infra instead."

Where it diverges from best practice / should upgrade:

- **Persistence.** Nothing in the shipped setup indicates the pool workers are ephemeral or JIT-registered. The dominant 2026 pattern — ARC's ephemeral one-pod-per-job model, Buildkite's "provisioned on demand and destroyed after each job," Woodpecker's "no state leaks between builds" — treats a runner surviving past one job as the vulnerability, not an optimization. For a single Debian box (no Kubernetes), the closest thing to ARC's model without adopting Kubernetes is `myoung34/docker-github-actions-runner` run with its ephemeral flag under a restart-on-exit supervisor, so each container instance really does register → run one job → de-register → get torn down, and a fresh container comes up for the next job. Persistent long-lived containers (even if only reachable by trusted-event jobs) still accumulate state across every push/PR from a repo you don't fully control the review process for.
- **Personal-account label emulation is correct, not a workaround to feel bad about.** Confirmed via GitHub Docs: self-hosted runner *groups* (the native mechanism for trust-tiering runner pools) require an Organization or Enterprise account — a personal User account genuinely cannot create them. Using a shared `homelab-pool` label plus the `route` job's conditional as a manual stand-in for what a runner group would enforce natively is the documented workaround pattern (per the GitHub community discussion on personal-account runners) — not a compromise unique to this repo.
- **No network/secret isolation layer documented beyond the routing job itself.** Hardening guides (systemshardening.com, Wiz) recommend a "secretless trust zone with deny-by-default network rules" as a second containment layer *in addition to* trust-based routing, on the theory that routing logic itself could have a bug (as ours just did, for blast-radius). Given the homelab box also hosts WhatsApp/Evolution credentials per repo comments in `ci.yml`, this is worth a look: at minimum, confirm the runner container/user has no filesystem/network path to the other services on that box, independent of trusting the workflow-routing YAML to always be correct.
- **JIT tokens specifically**: GitHub's JIT self-hosted runner API (single-use, ~60-minute registration tokens, auto-removed after one job) is the mechanism `docker-github-actions-runner`'s own wiki and multiple hardening guides point to as the current baseline for anyone not using ARC/Kubernetes. Worth checking whether the pool's current registration uses a long-lived PAT/registration token (the simpler, more common but weaker myoung34 default) versus JIT config — if it's the former, that's the concrete next hardening step.

Net: the fork-PR-vs-trusted-event trust split shipped today is correctly designed and matches the field's consensus mitigation for the *entry-point* risk. The remaining gap is entirely on the *lifecycle* side — ephemeral/JIT vs persistent — which is the single most consistently repeated piece of advice across every self-hosted-runner hardening source found in this research.

---

## Sources

**Standards / instruction files**
- https://agents.md/
- https://gist.github.com/0xfauzi/7c8f65572930a21efa62623557d83f6e
- https://developers.redhat.com/articles/2026/07/27/standardize-project-context-agentsmd-and-agent-skills
- https://asdlc.io/practices/agents-md-spec/
- https://www.morphllm.com/agents-md-guide
- https://github.com/openai/codex/blob/main/AGENTS.md
- https://developers.openai.com/codex/guides/agents-md
- https://kirill-markin.com/articles/codex-rules-for-ai/
- https://code.claude.com/docs/en/best-practices
- https://www.turbodocx.com/blog/how-to-write-claude-md-best-practices
- https://cursor.com/docs/rules
- https://techsy.io/en/blog/cursor-rules-guide
- https://github.com/PatrickJS/awesome-cursorrules
- https://docs.github.com/en/copilot/how-tos/configure-custom-instructions-in-your-ide/add-repository-instructions-in-your-ide
- https://github.blog/changelog/2025-07-23-github-copilot-coding-agent-now-supports-instructions-md-custom-instructions/
- https://docs.github.com/en/copilot/tutorials/customization-library/custom-instructions/your-first-custom-instructions

**Spec-driven development**
- https://github.com/github/spec-kit
- https://github.github.com/spec-kit/
- https://github.blog/ai-and-ml/generative-ai/spec-driven-development-with-ai-get-started-with-a-new-open-source-toolkit/
- https://zread.ai/github/spec-kit/5-core-commands-constitution-specify-plan-tasks-and-implement
- https://blog.scottlogic.com/2025/11/26/putting-spec-kit-through-its-paces-radical-idea-or-reinvented-waterfall.html
- https://github.com/bmad-code-org/BMAD-METHOD
- https://github.com/bmad-code-org/BMAD-METHOD/issues/39
- https://diegorodrigo.dev/en/2026/04/06/sdd-in-practice-quality-gates-tests-and-templates/
- https://reenbit.com/bmad-vs-spec-kit-vs-openspec-choosing-your-spec-driven-ai-framework/
- https://kiro.dev/docs/specs/
- https://kiro.dev/docs/specs/best-practices/
- https://specs.md/compare/vs-kiro
- https://tessl.io/blog/tessl-launches-spec-driven-framework-and-registry
- https://tessl.io/blog/how-tessls-products-pioneer-spec-driven-development

**Public agent/harness projects**
- https://github.com/openai/codex
- https://github.com/anthropics/claude-code-action
- https://github.com/aaif-goose/goose (redirects from block/goose)
- https://block.xyz/inside/block-open-source-introduces-codename-goose
- https://github.com/OpenHands/OpenHands (redirects from All-Hands-AI/OpenHands)
- https://github.com/OpenHands/OpenHands/blob/main/AGENTS.md
- https://www.openhands.dev/
- https://github.com/SWE-agent/SWE-agent (redirects from princeton-nlp/SWE-agent)
- https://github.com/SWE-agent/SWE-agent/blob/main/docs/background/aci.md
- https://github.com/cline/cline
- https://github.com/cline/clinerules
- https://docs.cline.bot/customization/cline-rules
- https://www.qodo.ai/blog/roo-code-vs-cline/
- https://thepromptshelf.dev/blog/cline-vs-roo-code-rules-2026/
- https://github.com/RooCodeInc/Roo-Code (confirmed archived via API)
- https://github.com/ruvnet/ruflo (redirects from ruvnet/claude-flow)
- https://dev.to/stevengonsalvez/claude-flow-the-multi-agent-swarm-orchestrator-before-it-got-a-new-name-4kd4
- https://github.com/disler/claude-code-hooks-mastery
- https://github.com/hesreallyhim/awesome-claude-code
- https://github.com/Aider-AI/aider
- https://github.com/Aider-AI/conventions
- https://aider.chat/docs/usage/tips.html
- https://cognition.com/blog
- https://cognition.com/blog/devin-fedramp-high-in-process

**Gates / verification / risk classification**
- https://docs.coderabbit.ai/security-agent/blast-radius
- https://www.coderabbit.ai/blog/introducing-semantic-diff
- https://github.com/ataraxy-labs/sem
- https://arxiv.org/abs/2605.30208 (Meta RADAR)
- https://pharaoh.so/blog/code-change-blast-radius/
- https://riftmap.dev/blog/ai-doesnt-understand-blast-radius/
- https://danger.systems/js/
- https://github.com/danger/danger-js
- https://scorecard.dev/
- https://openssf.org/projects/scorecard/
- https://epoch.ai/benchmarks/swe-bench-verified
- https://manabpokhrel7.medium.com/building-a-secure-gitlab-ci-cd-pipeline-with-sast-tools-gitleaks-hadolint-checkov-semgrep-8bd5501ec841
- https://sanj.dev/post/ai-code-security-tools-comparison/
- https://engineering.fb.com/2025/09/30/security/llms-are-the-key-to-mutation-testing-and-better-compliance/
- https://github.com/githubnext/llmorpheus
- https://www.endorlabs.com/learn/when-coderabbit-became-pwnedrabbit-a-cautionary-tale-for-every-github-app-vendor-and-their-customers
- https://www.propelcode.ai/blog/coderabbit-vulnerability-how-ai-code-review-security-flaw-exposed-1m-repositories
- https://github.com/orgs/community/discussions/120676 (protecting workflow files)
- https://github.com/orgs/community/discussions/25236

**Self-hosted runner pools**
- https://github.com/actions/actions-runner-controller
- https://docs.github.com/en/actions/concepts/runners/actions-runner-controller
- https://www.stepsecurity.io/blog/github-actions-runner-controller-blog-series
- https://some-natalie.dev/blog/securing-ghactions-with-arc/
- https://github.com/myoung34/docker-github-actions-runner
- https://github.com/myoung34/docker-github-actions-runner/wiki/Usage
- https://dev.to/alvic/ephemeral-self-hosted-github-actions-runners-42ma
- https://chrisliebaer.de/blog/gitea-actions/
- https://www.gilricardo.com/blog/forgejo-actions-proxmox-self-hosted-git-ci-2026
- https://zairalabs.ai/guide/tools/woodpecker-ci/
- https://buildkite.com/docs/agent/buildkite-hosted
- https://www.wiz.io/blog/github-actions-security-guide
- https://github.com/orgs/community/discussions/26722
- https://www.sysdig.com/blog/how-threat-actors-are-using-self-hosted-github-actions-runners-as-backdoors
- https://latchkey.dev/learn/ci-how-to/secure-self-hosted-runner-public-repo-github-actions
- https://github.blog/changelog/2023-06-02-github-actions-just-in-time-self-hosted-runners/
- https://github.com/actions/runner/issues/4248
- https://github.com/orgs/community/discussions/179202 (personal-account runner limits)
- https://docs.github.com/en/actions/hosting-your-own-runners/managing-self-hosted-runners/managing-access-to-self-hosted-runners-using-groups

**Cost governance / model routing**
- https://www.requesty.ai/blog/ai-agent-cost-optimization-how-to-cut-llm-spend-by-80-percent-with-routing
- https://www.augmentcode.com/guides/ai-model-routing-guide
- https://www.sonarsource.com/resources/library/model-routing-for-ai-coding/
- https://github.com/day0ops/quota-management
- https://www.openlegion.ai/en/learn/ai-agent-rate-limiting

**Continuity/memory**
- https://github.com/akitaonrails/ai-memory
- https://medium.com/@sourabh.node/persistent-memory-for-ai-coding-agents-an-engineering-blueprint-for-cross-session-continuity-999136960877
- https://codes1gn.github.io/agent-handoff/
- https://arxiv.org/pdf/2606.23752 (ESAA-Conversational)

Live GitHub API star/activity counts (curl against `api.github.com/repos/...`) pulled 2026-09-03 for: openai/codex, anthropics/claude-code-action, aaif-goose/goose, OpenHands/OpenHands, SWE-agent/SWE-agent, github/spec-kit, bmad-code-org/BMAD-METHOD, ruvnet/ruflo, disler/claude-code-hooks-mastery, hesreallyhim/awesome-claude-code, Aider-AI/aider, actions/actions-runner-controller, cline/cline, RooCodeInc/Roo-Code, Ataraxy-Labs/sem, myoung34/docker-github-actions-runner, nektos/act (sourcegraph/amp returned 404 — not found as a public repo under that path).
