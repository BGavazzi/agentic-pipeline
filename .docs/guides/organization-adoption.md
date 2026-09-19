# Adopting agentic-pipeline in a new organization

This guide is for an organization that wants coding agents to produce useful
software continuously while keeping correctness, security and accountability
explicit. It describes the smallest sensible adoption path, the decisions it
forces, and the controls that are usually overkill at the beginning.

## Executive summary

`agentic-pipeline` is an evidence-and-admission layer around agentic software
development. It is not an autonomous merge bot, an LLM reviewer sold as a
security boundary, or a replacement for repository ownership.

The central operating rule is:

> An agent may produce a candidate and machine-checkable evidence. A protected
> policy decides whether that evidence is sufficient. Humans retain the
> decision for acute risk, uncertain evidence and irreversible effects.

The project currently has a strong deterministic core: task/closure contracts,
risk classification, static security scans, versioned receipts, clean-room
integration, test-impact experiments, agent-skill fixtures, worker preflight,
visual evidence, telemetry adapters and local integration queues. The current
static capability audit is **24/34 points (70.6%)**: 7 capabilities pass and 10
are partial because their production activation depends on external worker,
review, browser, telemetry or deployment infrastructure.

Do not try to activate every capability at once. Adopt the evidence model first,
then add execution capacity only when volume or risk justifies it.

## If you are a traditional tech lead introducing AI

The first job is not to “transform the team.” It is to remove a few painful,
neglected bottlenecks without lowering the team's engineering bar.

Good first targets are usually underserved work:

- flaky tests, missing regression cases and slow feedback;
- repetitive refactors with clear acceptance criteria;
- stale documentation and difficult onboarding paths;
- dependency, secret and configuration hygiene;
- small maintenance tasks that never win priority against feature delivery;
- release checklists, evidence collection and incident follow-up.

Avoid starting with autonomous production changes, customer-data access,
architecture decisions made only by an agent, or a mandate that every developer
must use the same tool. Let the team see useful results before asking it to
change its habits.

### A practical 30/60/90-day transition

**First 30 days — observe and assist**

Pick one repository and two or three low-risk tasks. Use AI in a transparent
pairing mode. Require the normal tests and human review, but capture simple
metrics: cycle time, review rounds, escaped defects, test coverage of changed
behavior and developer-reported usefulness. Do not automate merge or deploy.

**Days 31–60 — introduce evidence**

Add task scope, deterministic tests, scanners, risk/contact summaries and a
clean-room integration pass. Let agents prepare repair loops and review bundles;
humans still decide what enters staging. Turn every serious failure into a
regression fixture or a documented backlog item.

**Days 61–90 — selectively automate**

Allow routine, well-scoped work to reach a staging-review bundle automatically.
Keep high-risk changes, uncertain evidence and policy/gate edits on an earlier
human checkpoint. Review the metrics with the team and remove controls that do
not reduce risk or waiting time.

### What changes for the tech lead

The role shifts from personally inspecting every line to designing the system
in which inspection is proportionate and evidence is trustworthy:

| Traditional emphasis | AI-assisted emphasis |
|---|---|
| Review every change manually | Define risk tiers and review exceptions |
| Keep tribal knowledge in memory | Turn decisions and failure modes into task/docs/eval artifacts |
| Ask whether the agent “seems good” | Require reproducible evidence and exact commit identity |
| Optimize one developer's speed | Optimize feedback latency, escaped defects and team capacity |
| Add process when incidents happen | Add the smallest regression gate that prevents recurrence |

This is not abdication of technical leadership. It is moving leadership upward:
from being the highest-throughput reviewer to owning boundaries, quality signals,
architecture decisions and the team's ability to recover from automation
mistakes.

### How to bring the team along

1. Start from a team pain point, not an AI slogan.
2. State what the agent is not allowed to do before showing what it can do.
3. Publish both wins and failures; never present generated code as inherently
   trustworthy.
4. Keep normal code ownership and review responsibilities intact.
5. Invite skeptics to design negative tests and failure scenarios.
6. Measure time saved and defects avoided, not prompts or lines generated.
7. Give developers a way to opt out of agent assistance while the pilot is
   being evaluated.

The adoption succeeds when the team says “the feedback loop is better,” not
when it says “we installed an agent platform.”

## The target operating model

```text
task / intent
    ↓
candidate diff → risk + contact surfaces + required gates
    ↓
clean-room execution → unit / contract / security / agent / visual evidence
    ↓
independent checks → admission receipt + quality scorecard
    ↓
routine survivor bundle ───────────────┐
acute / uncertain / stale evidence ────┴→ human review
    ↓
staging handoff → deploy health → rollback evidence → post-merge sampling
```

Every evidence edge should be bound to the same `base_sha`, `head_sha`, policy
version, environment identity and artifact digests. Missing, stale or
contradictory evidence is `blocked`, not an inferred pass.

## Order of implementation

### Phase 0 — Decide the boundary before installing tools

Write down:

- which repositories and data classes agents may touch;
- which actions are forbidden to agents (production writes, secret access,
  merges, deployments, customer-data access);
- which changes always require a human before execution;
- who owns the protected policy, runner fleet and rollback decision;
- what “staging” means in this organization.

Create one small policy decision record. This prevents the common failure mode
of installing an agent runner first and deciding its authority afterward.

**Exit condition:** a candidate can be classified as routine, uncertain or
acute without asking an agent to invent the policy.

### Phase 1 — Install the repository constitution and task contract

For each pilot repository:

1. Add an `AGENTS.md` describing scope, stack, forbidden actions, test commands
   and ownership.
2. Add `.docs/tasks/000-template.md` and require four-digit task IDs.
3. Run `validate_task.py` before work starts.
4. Require the Closure Law before a task can be called complete.
5. Keep the canonical scripts and skills in one core repository; sync them into
   consumers instead of hand-editing copies.

Start with one or two representative repositories, not the whole portfolio.

**Impact:** work becomes more explicit and auditable; agents spend more time
reading task context and less time guessing. The cost is modest process
friction and a short-lived backlog of incomplete task metadata.

### Phase 2 — Add deterministic local gates

The minimum useful gate set is:

```text
task schema → unit/contract tests → blast radius → SAST/SCA/secrets
→ closure/docs checks
```

Run the same commands locally and in CI. Pin the Python dependencies and make
scanner failures visible as `error` or `blocked`; never silently degrade to a
green result.

At this phase, use GitHub-hosted runners or the existing trusted CI service.
Do not introduce a self-hosted pool merely to run a few commands.

**Exit condition:** a deliberately planted bad task, secret, high-risk path and
failing test each produce a deterministic non-pass result.

### Phase 3 — Add the clean-room integration layer

Before a human sees a routine candidate, execute it in a disposable workspace
created from the exact base/head merge tree. Record:

- candidate and executed tree identity;
- command and environment fingerprint;
- exit code and duration;
- bounded stdout/stderr metrics;
- cleanup status and artifact digests.

The integration worker may test, merge locally and discard. It must not push,
approve, merge remotely, deploy or receive production secrets.

This is the first genuinely agentic loop: agents can repair and retest
locally, while only survivors become a staging-review candidate.

**Exit condition:** a dirty checkout, stale branch, merge conflict and test
failure are all detected without touching the developer's worktree or remote.

### Phase 4 — Introduce receipts, admission and PR intelligence

Aggregate independent outputs into versioned receipts and a quality scorecard.
Show the following near the top of every PR:

- exact base/head identity;
- risk tier and classifier triggers;
- affected modules and changed-file count;
- contact surfaces (security, CI/policy, data/schema, infrastructure, UI,
  dependencies, tests);
- required/passed/missing gates;
- test-impact selection and fallback metrics;
- integration duration and isolation status;
- explicit HITL checkpoint and reason.

Treat PR comments as advisory. The authoritative decision must be a protected
check whose implementation and policy inputs cannot be replaced by the PR.

### Phase 5 — Add risk-weighted human review

Use a simple policy first:

| Candidate | Agent may do | Human checkpoint |
|---|---|---|
| Low-risk routine change | test, scan, local integrate, bundle | before staging or sampled after merge |
| Medium / uncertain | test and gather evidence | before integration or staging |
| High-risk / acute | inspect and produce evidence only | before execution when possible |
| Fork / untrusted origin | GitHub-hosted isolation only | before any privileged route |
| Missing or contradictory evidence | stop and explain | required |

Acute examples include auth/identity, secrets, infrastructure, migrations,
production configuration, CI/policy/gate code, wide blast radius, visual
baseline changes and external writes.

The goal is not “no human review.” The goal is to spend human attention where
the consequence or uncertainty is high, while preserving an auditable sample
of routine automation.

### Phase 6 — Scale workers only after measuring demand

When queue age or CI throughput becomes a real bottleneck, add a worker pool.
For self-hosted workers require all of:

- ephemeral or just-in-time registration;
- one job per worker lifecycle;
- clean workspace proof;
- zero mounted secrets;
- verified network policy;
- Docker/image identity where required;
- post-job deregistration and teardown evidence;
- no fork PRs on the privileged pool.

The homelab pool should be opt-in until one trusted same-repository job has
completed and deregistered cleanly. Persistent runners are a migration
fallback, not the target architecture.

### Phase 7 — Add specialized evidence where it pays

Add these in response to measured need:

- **Test-impact analysis:** only after a full-suite baseline and history exist;
  keep full-suite fallback authoritative until recall is proven.
- **Agent-eval corpus:** begin with 20–50 representative tasks and promote
  production incidents into permanent regression cases.
- **Visual regression:** only for repositories with meaningful UI risk; pin the
  browser/OS/font image and baseline ownership before blocking merges.
- **Release provenance/SBOM:** when artifacts leave the organization or supply
  chain risk justifies it.
- **Telemetry/history:** when queue age, flake rate, worker saturation or
  review delay cannot be managed from local reports.
- **Deployment health/rollback:** when the pipeline is allowed to promote
  beyond staging.

## Overall impact of the decision

Adopting this framework changes the unit of work from “an agent edited files”
to “a candidate produced a provenance-bound evidence packet.” That has several
organizational consequences.

### Engineering process

- Tasks, acceptance conditions and negative tests become first-class inputs.
- A green unit suite is necessary but no longer sufficient for risky changes.
- Agents can own implementation and repair loops; humans own authority and
  exceptions.
- Work becomes easier to resume because receipts and exact SHAs preserve state.

### Security and compliance

- The system records what was tested, where, with which policy and worker.
- Forks, secrets, production writes and policy changes get explicit routing.
- Evidence is tamper-resistant only when produced by protected callers and
  isolated workers; local JSON alone is not an attestation.

### Capacity and cost

- Early adoption adds small runtime and documentation costs.
- At scale, test selection, sharding, caching and worker pools become capacity
  engineering problems with queue-age and p95 SLOs.
- Storing compact KPI vectors and receipt digests is cheaper and safer than
  retaining every raw trace forever; retain raw artifacts only for a bounded
  debugging window.

### Organizational ownership

Assign explicit owners for:

| Surface | Owner |
|---|---|
| Core policy and gate versions | platform / developer productivity |
| Repository constitution and task scope | repository maintainers |
| Worker images, isolation and teardown | infrastructure / security |
| Baselines and visual thresholds | frontend owners |
| Eval corpus and oracle quality | agent-platform / QA |
| Protected checks and merge rules | repository administration |
| Post-deploy health and rollback | service owners / SRE |

Without these owners, the framework produces impressive reports but no
accountable decisions.

## What can be overkill

Do not adopt a control just because it appears in the full capability map.

### Usually overkill for a small or low-risk organization

- A homelab runner pool before hosted CI is actually saturated.
- Test-impact analysis before there is reliable per-test history.
- Playwright visual gates for backend or data-only repositories.
- Three-agent adversarial review for every typo or isolated leaf change.
- Signed release attestations for artifacts that never leave the workstation.
- ClickUp, WhatsApp, Figma and deployment adapters when the repository task
  file is sufficient.
- A centralized OpenTelemetry collector before local scorecards answer the
  operational questions.
- Autonomous remote merge or deploy. The hard part is authority and rollback,
  not issuing the final API call.

### Dangerous forms of “simplification”

These are not acceptable overkill cuts:

- removing exact commit identity from receipts;
- treating candidate-authored reports as trusted;
- running fork code on a privileged self-hosted worker;
- allowing a persistent worker to accumulate secrets or workspace state;
- replacing a missing gate with an LLM assertion;
- skipping the full suite solely because test-impact analysis selected fewer
  tests;
- allowing a policy or gate change to self-approve.

## Adoption profiles

### Solo developer or small team

Adopt Phases 0–4 on one repository. Use hosted CI, local clean-room runs and
the core scanners. Keep human review on all medium/high-risk changes. Defer
worker pools, visual gates, durable telemetry and automated staging.

### Growing engineering organization

Adopt Phases 0–5 across a small pilot portfolio. Add PR intelligence, bounded
local integration queues, a representative agent-eval corpus and sampled
post-merge review. Add a self-hosted pool only after queue metrics show a need.

### Regulated or high-consequence organization

Adopt the full trust boundary early: protected policy callers, immutable pins,
ephemeral workers, network policy, artifact provenance, independent review,
retention rules, visual/browser identity where relevant, deployment health and
rollback. Keep routine automation narrow until evidence quality and ownership
are demonstrated.

## First-week checklist

- [ ] Pick one pilot repository and name its owners.
- [ ] Write the constitution and forbidden-effects policy.
- [ ] Add a task template and closure validator.
- [ ] Install unit, task, blast-radius and scanner gates.
- [ ] Plant negative fixtures and verify fail-closed behavior.
- [ ] Run one clean-room integration pass locally.
- [ ] Publish risk/contact/gate metrics on a draft PR.
- [ ] Decide the human checkpoint before enabling any autonomous loop.
- [ ] Record external gaps instead of marking them green.

## References in this repository

- [README](../../README.md) — command-level usage and component inventory.
- [SOTA analysis](../analysis/agentic-sdlc-testing-sota-2026-09.md) — evidence
  graph, metrics and remaining gaps.
- [Homelab worker runbook](../runbooks/homelab-runner-pool.md) — worker trust,
  lifecycle and activation checks.
- [Protected policy runbook](../runbooks/protected-policy-workflow.md) —
  default-branch policy ownership and immutable pins.
- [Completeness rubric](../analysis/COMPLETENESS-RUBRIC.md) — portfolio
  adoption scoring.
