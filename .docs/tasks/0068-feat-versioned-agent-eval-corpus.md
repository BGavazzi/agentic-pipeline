---
status: in_progress
priority: P1
type: feat
created: 2026-09-18
updated: 2026-09-18
clickup_id: null
parent: 0067
blocks: []
blocked_by: []
---

# 0068 — Feature: versioned agent-evaluation corpus metrics

## Context
SOTA agentic SDLC practice treats agent instructions, skills, hooks, and
worker behavior as continuously evaluated production configuration. The
existing `meta_test.py` fixture boundary is a good execution primitive, but a
single green fixture cannot establish quality or detect configuration drift.

## Problem
The harness needs a denominator-preserving corpus report that distinguishes
pass, failure, regression, and insufficient sample size, while measuring
latency, tokens, cost, and configuration identity without leaking commands or
credentials.

## What To Do
- [x] Add a versioned corpus summarizer over meta-test receipts.
- [x] Report pass/fail rate, minimum-corpus readiness, baseline regression,
      p50/p95 duration, token/cost totals, and configuration digest.
- [x] Mark fewer than the configured minimum cases as `insufficient_corpus`.
- [x] Scrub secret and repository-control variables before meta-test workers.
- [x] Add focused tests for calibration, regression, metrics, hashing, and
      environment isolation.
- [ ] Grow the repository's representative fixture set to 20–50 real tasks and
      activate scheduled/config-change CI evaluation in a separate task.

## Affected Files
- `scripts/agent_eval_corpus.py`
- `scripts/meta_test.py`
- `tests/test_agent_eval_corpus.py`, `tests/test_meta_test.py`
- `scripts/core_sync.py`, `scripts/blast_radius.py`, `scripts/sota_audit.py`
- `README.md`, `CHANGELOG.md`, `.docs/function-catalog.md`

## Exit Conditions
- [x] A small green corpus cannot report production-ready pass.
- [x] Baseline degradation reports `regression`.
- [x] Metrics preserve denominators and omit raw worker command contents.
- [x] Agent workers do not inherit obvious secrets or repository-control env.
- [x] Focused tests pass.
- [ ] 20–50-case representative corpus and scheduled/config-triggered evals.
- [ ] PR approved.

## Required Documentation (Closure Law)
- [x] `CHANGELOG.md` updated
- [x] `.docs/function-catalog.md` updated
- [N/A] `<sdd_kit_path>`: no new architectural decision record
- [x] `README.md` updated
- [x] `.agents/continuity-codex.md` updated
- [x] Tests passing
- [N/A] `<route_map>`: no route changed
- [ ] PR approved

## Honest Backlog
This adds the measurement contract, not the representative corpus, model
matrix, scheduler, homelab worker provisioning, or external eval collector.
