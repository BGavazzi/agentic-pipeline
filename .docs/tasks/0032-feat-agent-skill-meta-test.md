---
status: in_progress
priority: P1
type: feat
created: 2026-09-16
updated: 2026-09-16
clickup_id: null
parent: 0031
blocks: []
blocked_by: []
---

# 0032 — feat: add the agent-skill meta-test integration gate

## Context
The harness already runs deterministic unit, integration, scanner, risk,
policy, visual, and reviewer receipts, but it had no executable contract for
testing the agent skills themselves. The old `meta-test` skill was prose only.
That left a gap between “an agent ran” and “the agent's observable work stayed
within task scope, closure rules, and branch discipline.”

## Problem
Agent-produced code must survive an isolated worker test before the system
offers a staging-review PR. The check must be reproducible, versioned, bound to
the exact candidate commit pair, and safe to run on a homelab worker without a
real checkout, credentials, or push remote. A prose-only report is not enough.

## What To Do
- [x] Implement `scripts/meta_test.py` with disposable fixture repositories,
      no-shell worker execution, deterministic assertions, and bounded metrics.
- [x] Add a committed builder happy-path fixture under
      `tests/skills/fixtures/001-trivial-readme-edit/`.
- [x] Carry a schema-v1 `meta-test` receipt through receipt aggregation and
      scorecard metrics, with exact base/head identity checks.
- [x] Classify `.claude/skills/*/SKILL.md` changes as `agent-skill` and require
      the `meta-test` gate for high-risk admission.
- [x] Add unit coverage for pass, worker failure, and versioned metrics.
- [x] Update the skill documentation and README to describe the executable
      contract rather than a design-only status.

## Affected Files
- `scripts/meta_test.py`
- `scripts/ci_receipts.py`
- `scripts/quality_scorecard.py`
- `scripts/admission_gate.py`
- `scripts/blast_radius.py`
- `scripts/policy_integrity.py`
- `scripts/core_sync.py`
- `.github/workflows/ci.yml`
- `.claude/skills/meta-test/SKILL.md`
- `tests/test_meta_test.py`
- `tests/skills/fixtures/001-trivial-readme-edit/`
- `README.md`

## Exit Conditions
- [x] A worker can run a fixture only inside a disposable git repository with
      no configured remote.
- [x] Branch, commit count, touched-file scope, task state, Closure Law
      markers, and trajectory assertions are deterministic and fail closed.
- [x] The receipt reports fixture counts, assertion counts, duration, and
      schema version, and is identity-bound when used by CI.
- [x] A skill change requires `meta-test` in the high-risk gate set.
- [x] Tests and workflow parsing pass.

## Required Documentation (Closure Law)
- [x] `CHANGELOG.md` updated
- [N/A] `function-catalog.md` — no function catalog exists
- [N/A] `SDD_KIT.md` — no new product decision
- [x] `README.md` updated
- [N/A] `.agents/continuity-<agent>.md` — no continuity file in this checkout
- [x] Tests passing
- [N/A] `ROUTE_BEHAVIOR_MAP.md` — no route/handler/model change
- [ ] PR approved

## Honest Backlog
- The core provides the worker protocol and receipt contract, but the
  repository does not invent an agent API or silently choose a model. A
  trusted homelab dispatcher must supply the worker command and upload the
  receipt before a skill-changing candidate can be admitted.
- Additional fixtures for builder failure recovery, tester, notifier, and
  lock-conflict behavior remain future work.
