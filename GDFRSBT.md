# GDFRSBT — Specification-Driven Development Methodology

> **First Pass** — Living document. Derived from reading `AGENTS.md` files in sample projects.
> Subsequent passes deepen each stage with examples, templates, and operational workflows.

---

## 0. What Is GDFRSBT

**GDFRSBT** is a software development methodology that combines eight complementary practices into a single sequential, coherent chain. Each practice has a well-defined stage, focus, and output artifact. Together they form a system that goes from "why build this" to "how to prove it works," eliminating the blind spots that cause rework, agent collisions, and long-term entropy.

The acronym breaks down as:

| Acronym | Practice | Description |
|:--------|:---------|:------------|
| **G** | Goal Driven Development | Start with clear business objectives |
| **D** | Domain Driven Design (Strategic) | Map domain boundaries before any technical decision |
| **F** | Feature Driven Development | Prioritize and decompose into deliverable features |
| **R** | Readme Driven Development | Write the README before the implementation |
| **S** | Spec Driven Development | Define contracts between components |
| **B** | Behavior Driven Development | Specify expected behavior via Given/When/Then |
| **T** | Test Driven Development | Prove it works with failing tests first |

> **Note:** The second "D" (Tactical DDD) runs in parallel with BDD and TDD — it is the micro-level domain refinement (Entities, Aggregates, Value Objects) once expected behaviour has been defined.

---

## 1. The Eight Stages in Detail

### Stage 1 — GDD: Goal Driven Development
**Scope:** Macro / Business  
**Core question:** *Why are we building this?*  
**Output artifact:** Clear goals and success metrics (OKRs, KPIs, product acceptance criteria)

Before any line of code or spec, the team defines the business objective with enough precision that any agent — human or AI — can make coherent decisions without having to ask. A vague objective generates vague features.

**In a sample project, GDD appears as:**
- "Zero-Friction Voice-to-API Assistant for Blue Events Management"
- Implicit metrics: zero duplicates in the API, human-in-the-loop via emoji, 100% test coverage

---

### Stage 2 — Strategic DDD: Domain Driven Design (Macro)
**Scope:** Architecture  
**Core question:** *How does the domain divide?*  
**Output artifact:** Bounded Contexts, Context Maps, Subdomains

The domain is mapped into well-delimited boundaries before any technical decision. Each module has a single responsibility and defined interfaces. In multi-agent contexts, this is critical: agents need to know exactly *who owns* each part of the system.

**In a sample project, Strategic DDD appears as:**  
A Modularity Map in AGENTS.md:

| Module | File(s) | Responsibility |
|:-------|:--------|:--------------|
| Webhook Router | `evolution_webhook.py` | Entry point, routing by message type |
| AI Agent | `agno_service.py` | STT + Gemini LLM + Tools |
| API Client | `api_client.py` | Full CRUD adapter |
| Resolution | `resolution_service.py` | Name → UUID, dedup, cache |
| ... | ... | ... |

---

### Stage 3 — FDD: Feature Driven Development
**Scope:** Delivery Management  
**Core question:** *What are we building, in what order?*  
**Output artifact:** Prioritized, decomposed feature list

Features are broken down into deliverable units. The `nnnn-type-subtype-names.md` numbering system is the concrete FDD implementation: it defines priority (first 3 digits = chronological order), parallelism (last digit: `0` = blocker, `1–9` = parallel), type, and subtype.

**FDD appears as the task system in `.docs/tasks/` with convention:**
```
.docs/tasks/
  0010-feat-...   ← blocker (sequential)
  0021-feat-...   ← parallel with 0022 and 0023
  0022-feat-...
  0023-fix-...
  completed/      ← completed tasks
```

---

### Stage 4 — RDD: Readme Driven Development
**Scope:** UX / DX (Developer Experience)  
**Core question:** *How is the product experienced by its users?*  
**Output artifact:** `README.md` that guides the usage experience

The README is written *before* the complete implementation, as an experience contract. It defines how the system presents itself to the external world — humans and agents. Any implemented feature that doesn't fit in the README signals unnecessary scope.

**Update obligation (Closure Law):**  
The README must be updated when closing any task that introduces user-visible functionality or changes system behavior.

---

### Stage 5 — SDD: Spec Driven Development ← *Focus of this document*
**Scope:** Integration / Contracts  
**Core question:** *What is the contract between components?*  
**Output artifact:** Machine-readable specs (OpenAPI, JSON Schema, Pydantic Models, SDD_KIT.md)

See Section 2 for full detail.

---

### Stage 6 — BDD: Behavior Driven Development
**Scope:** Business Rules  
**Core question:** *What should the system do in each situation?*  
**Output artifact:** Structured scenarios (Given / When / Then)

Defines the expected behavior of each feature in business-close language. In the project context, this appears in task acceptance criteria (the `[ ]` checkboxes) and exit conditions.

**Real example from a task:**
```
- [ ] _send_ambiguity_list(self, jid, operations, partial_task) implemented and functional
- [ ] _build_ceo_summary(self, operations, results) implemented and functional
- [ ] No AttributeError on ambiguity and CEO mode paths
- [ ] pytest tests/ -v --tb=short passes 100%
```

---

### Stage 7 — Tactical DDD: Domain Driven Design (Micro)
**Scope:** Business Logic  
**Core question:** *How is the domain modelled in code?*  
**Output artifact:** Entities, Aggregates, Value Objects (Pydantic Models)

The project law is explicit: **"API payloads MUST use strict Pydantic models (`api_models.py`). Never use raw dicts for API requests."** This is Tactical DDD in practice: the domain is expressed in types, not generic structures.

---

### Stage 8 — TDD: Test Driven Development
**Scope:** Code / Unit  
**Core question:** *How do you prove it works?*  
**Output artifact:** Unit tests (failing → implementation → refactor)

The law: *"Any code change MUST be verified against the unit test suite: `pytest tests/ -v --tb=short`. Do not declare a task complete if tests are failing."*

---

## 2. SDD In Depth — Spec Driven Development

### 2.1 What Is a "Spec" In This System

A **spec** is any artifact that defines a contract between parts of the system precisely enough to be verified automatically or by an agent without ambiguity. In GDFRSBT, specs exist in three layers:

**Layer 1 — Architectural Decisions (`SDD_KIT.md`)**  
Each design decision that affects global behavior gets a `Dxx` flag:
```markdown
| D11 | Duplicate Detection | Resolution service searches backend API before any create_* |
| D17 | Idempotency + Sequential | Redis lock per user. Duplicate msg_ids rejected. |
| D25 | UUID Safety Gate | Dispatcher rejects payload with non-UUID IDs (except $! placeholders) |
```

**Layer 2 — Module Contracts (code + comments)**  
Every public interface point has an explicit `# CONTRACT:`:
```python
# CONTRACT: Returns None on 404 (entity not found), raises APIClientError
# on 5xx. Callers MUST handle None gracefully (see dispatcher.py:L145).
```

**Layer 3 — Task Contracts (task files)**  
Each task defines its contract as Exit Conditions:
```markdown
## Exit Conditions
- [ ] _send_ambiguity_list implemented and functional
- [ ] pytest passes 100%
```

### 2.2 The `SDD_KIT.md` — The Heart of SDD

The `SDD_KIT.md` is the central Spec Driven Development document in a project. It has a fixed structure:

```
1. Executive Summary     ← What the system does, in one page
2. Core Design Decisions ← Table of Dxx flags with decision, rationale and files
3. Architecture Overview ← Pipeline flow + Services Map + Tools
4. (Project-specific extensions)
```

**Flag addition rule:**
- Every new architectural decision generates a new `Dxx` flag
- Every change to an existing decision updates the corresponding entry
- Flags marked `(Planned)` are future specs not yet implemented — this is the "design first" mechanism
- Code should reference flags in comments: `# D07: retry 3x with backoff...`

**Flag lifecycle:**
```
Idea → Proposal (planning/) → Dxx flag (Planned) in SDD_KIT →
Task nnnn created → Implementation → Flag updated (status: implemented) →
Task closed
```

### 2.3 Anatomy of an SDD-Compliant Task

A well-formed task in the GDFRSBT system must contain:

```markdown
---
status: open
priority: [P0/P1/P2/high/medium/low]
type: [feat/fix/refactor/docs/chore/audit]
---

# nnnn — [Type]: [Descriptive Title]

## Context
[Why this task exists. What problem it solves. References to ROUTE_BEHAVIOR_MAP,
SDD_KIT, or related tasks.]

## Problem
[Precise technical description of what is wrong or missing.]

## What To Do
- [ ] Subtask 1 (actionable, verifiable)
- [ ] Subtask 2
- [ ] Subtask N

## Affected Files
- `src/services/foo.py` (main)
- `tests/test_foo.py` (tests)

## Exit Conditions
- [ ] Behavior X implemented
- [ ] pytest tests/ -v --tb=short passes 100%

## Required Documentation (Closure Law)
- [ ] `.docs/function-catalog.md` updated
- [ ] `docs/SDD_KIT.md` updated (if new architectural decision → Dxx flag)
- [ ] `README.md` updated (if applicable)
- [ ] `.agents/continuity-*.md` updated
- [ ] Tests written and passing
- [ ] `.docs/ROUTE_BEHAVIOR_MAP.md` updated (if route/action/model changed)
```

### 2.4 Task Naming Convention

```
nnnn-type-subtype-names.md
│    │    │        └─ Descriptive words with hyphens
│    │    └──────── Subtype (optional, e.g.: report, memory, core)
│    └───────────── Type: feat, fix, refactor, docs, chore, audit, proposal
└────────────────── 4 digits:
                    - First 3: chronological planning order
                    - Last: 0 = blocker, 1–9 = parallel
```

**Examples:**
```
0010-feat-...                           ← 1st block, blocker
0021-feat-...                           ← 2nd block, parallel task 1
0022-fix-core-...                       ← 2nd block, parallel task 2 (subtype "core")
0113-feat-image-processing-pipeline.md
0126-refactor-uniform-dedup-strategy.md
```

### 2.5 The Full Spec Cycle

```
┌─────────────────────────────────────────────────────────────────┐
│                     FULL SDD CYCLE                              │
│                                                                 │
│  1. DISCOVERY                                                   │
│     Problem or feature identified                               │
│     → Created in .docs/tasks/planning/ (no code yet)           │
│                                                                 │
│  2. SPECIFICATION                                               │
│     Planning → Formal task with:                                │
│     • Clear Exit Conditions                                     │
│     • Listed Affected Files                                     │
│     • Dxx flag in SDD_KIT.md (if architectural change)         │
│     → File at .docs/tasks/nnnn-type-subtype-names.md           │
│                                                                 │
│  3. IMPLEMENTATION                                              │
│     Agent picks lowest-numbered available task                  │
│     Registers lock in .agents/file-locks.md                     │
│     Implements with Rich Commentary (docstrings, # SYNC:, etc.) │
│     Tests: pytest tests/ -v --tb=short                          │
│                                                                 │
│  4. CLOSURE (Task Closure Gate)                                 │
│     All Closure Law documentation updated                       │
│     Dxx flag updated in SDD_KIT.md                             │
│     Task marked [x] and moved to completed/                    │
│     CHANGELOG.md updated                                        │
│     continuity-agent.md updated                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Operational Protocols That Sustain SDD

### 3.1 Multi-Agent Anti-Collision

SDD only works in a multi-agent environment if there is concurrency control. The system uses:

1. **File Lock Ledger** (`.agents/file-locks.md`): before editing any file, the agent registers the lock. If the file is already locked, it does not edit — leaves a comment and moves to another subtask.

2. **Freshness Check**: if the file was read more than 2 minutes ago or appears in `jj diff`, the agent re-reads it before editing.

3. **Domain per Task**: each task lists the files it will touch in "Affected Files". Agents check for overlap before starting.

4. **Jujutsu (jj)**: the primary VCS, which eliminates `.git/index` lock errors and allows multiple agents to work in isolated simultaneous revisions.

### 3.2 Rich Commentary — The Spec Inside the Code

In a multi-agent environment, code is the communication interface between agents. Comments serve as inline specs:

```python
# CONTRACT: Returns None on 404, raises APIClientError on 5xx.
# D11: Duplicate check via backend API search before any create_* operation.
# SYNC: If you change fields here, also update api_models.py
# [claude-opus | 2026-03-24] Added retry logic — Task: 0022-fix-core.md
```

**Comment types:**
| Tag | Purpose |
|:----|:--------|
| `# CONTRACT:` | Public interface contract — what the caller can expect |
| `# D##:` | Reference to an architectural decision in SDD_KIT.md |
| `# SYNC:` | Interdependency warning — change here implies change there |
| `# [agent \| date]` | Audit — who changed it, when, and why |
| `# TODO(agent):` | Traceable backlog item with assigned owner |

### 3.3 Changelog as Change Spec

The `CHANGELOG.md` is the historical spec of the system. Immutable format:

```markdown
## [YYYY-MM-DD] - Brief Title
### Added / Changed / Fixed / Removed
- Precise details of the change
**Author**: [Name or Agent ID]
```

Rules: always add at the top, never delete existing entries, never modify past entries (except typos).

### 3.4 Continuity Ledger — Agent Memory

Each agent maintains `.agents/continuity-<name>.md` with:
- What was done in this session (by topic)
- Test status
- What the next agent needs to know
- Critical files touched

This is the handover spec: it ensures that any agent picking up the work has enough context to continue without rework.

---

## 4. GDFRSBT System Directory Structure

```
project/
│
├── AGENTS.md                    ← Project constitution (read by ALL agents)
├── README.md                    ← RDD: end-user experience
├── CHANGELOG.md                 ← Historical change spec (immutable)
│
├── .docs/
│   ├── tasks/
│   │   ├── 000-template.md      ← Standard task template
│   │   ├── nnnn-type-name.md    ← Open tasks (FDD + BDD + SDD)
│   │   ├── planning/            ← Ideas and proposals (pre-task)
│   │   └── completed/           ← Completed tasks
│   ├── tasklist.json            ← Status index (not edited by agents)
│   ├── architecture/
│   │   └── SDD_KIT.md           ← Central spec: Dxx decisions (SDD)
│   ├── function-catalog.md      ← Function catalog (updated at closure)
│   ├── ROUTE_BEHAVIOR_MAP.md    ← Route behavior map
│   └── CHANGELOG.md             ← Technical history
│
├── .agents/
│   ├── file-locks.md            ← Anti-collision: file locks
│   ├── continuity-<agent>.md    ← Per-agent handover memory
│   ├── memories/                ← Shared architectural discoveries
│   └── thoughts/<agent>/        ← Context offload during long tasks
│
├── docs/                        ← Public documentation (end user)
│   └── SDD_KIT.md               ← (may be symlink to .docs/architecture/)
│
└── .archive/                    ← Deprecated code (never delete)
```

---

## 5. Model and Agent Governance

### 5.1 Model Hierarchy

| Use | Preferred Model |
|:----|:---------------|
| Complex reasoning / coding | `claude-opus-4-8` / `gemini-3.1-pro` |
| Fast execution / workhorse | `claude-sonnet-4-6` / `gemini-3-flash` |
| Cheap repeated tests | `claude-haiku-4-5` / `gemini-3.1-flash-lite` / `gpt-5.1-mini` |

### 5.2 Agent Identity

Every agent must assume an identity when working in a repository:
- Based on the tool (e.g.: `claude-code`, `gemini-cli`, `cursor`)
- Registered in `.agents/continuity-<name>.md`
- Used in audit comments in code

---

## 6. Immutable Laws (Summary)

| # | Law | Forbidden Violation |
|:--|:----|:-------------------|
| L1 | Never delete files | Always use `.archive/` |
| L2 | Always update CHANGELOG | Every modification has an entry |
| L3 | Task Closure Gate | Never close a task without complete docs |
| L4 | File Lock before editing | Anti-collision is mandatory |
| L5 | Tests must pass | Never declare a task complete with failing tests |
| L6 | SDD_KIT for every decision | No new pattern without a Dxx flag |
| L7 | Pydantic for API models | Never raw dicts in payloads |

---

## 7. Planned Passes

This is **Pass 1** — model map. Subsequent passes will deepen:

| Pass | Focus |
|:-----|:------|
| **P2** | Full task template with annotated real examples |
| **P3** | SDD_KIT.md in depth — how to create and evolve Dxx flags |
| **P4** | Multi-agent workflow — file locks, jj, continuity in practice |
| **P5** | Rich Commentary — comment guide with project examples |
| **P6** | ClickUp integration — automating the GDFRSBT cycle |

---

*Part of [BGavazzi/agentic-pipeline](https://github.com/BGavazzi/agentic-pipeline) — the open-source agentic task-processing pipeline for Claude Code.*
