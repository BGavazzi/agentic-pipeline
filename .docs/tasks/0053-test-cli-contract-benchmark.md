---
status: in_progress
priority: P2
type: test
created: 2026-09-17
updated: 2026-09-17
clickup_id: null
parent: null
blocks: []
blocked_by: []
---

# 0053 — test: bounded cross-platform core CLI contract benchmark

## Context
The core has accumulated a registry of gate scripts with independent command
line entry points. Unit tests exercise internal behavior, but a parser or exit
code regression can still break CI before those tests run. This task adds a
small Windows/Linux-compatible subprocess corpus for the CLI boundary only.

## Problem
There was no single, bounded check that every registered gate accepts `--help`
where supported and returns the documented usage exit code for missing input.
Ad hoc shell invocations also risked accidentally reaching scanners, network
services, or credential-dependent paths.

## What To Do
- [x] Read the canonical gate-script registry without executing it.
- [x] Exercise help and missing-input contracts through argv-only subprocesses.
- [x] Bound every child process and avoid forwarding credentials or using a shell.
- [x] Emit JSON metrics and register the benchmark in the existing CI test job.
- [x] Add focused tests and documentation for the corpus and its limits.
- [ ] Commit, push, and open a draft PR; leave merge and approval to a human.

## Affected Files
- `scripts/cli_contract_benchmark.py`
- `tests/test_cli_contract_benchmark.py`
- `.docs/benchmarks/core-cli-contract.md`
- `.docs/tasks/0053-test-cli-contract-benchmark.md`
- `.docs/function-catalog.md`
- `.github/workflows/ci.yml`
- `CHANGELOG.md`

## Exit Conditions
- [x] All 23 registered core gate scripts have a missing-input exit-code case.
- [x] All 21 argparse-based gates have a `--help` exit-0 case.
- [x] Cases run via subprocess with a per-case timeout and no credential env.
- [x] Full pytest suite, task/closure validators, and diff-scoped gates pass.
- [ ] Draft PR is pushed and available for human review; do not merge.

## Required Documentation (Closure Law)
- [x] `CHANGELOG.md` updated
- [x] `.docs/function-catalog.md` updated for the new benchmark entry points
- [N/A] `<sdd_kit_path>` — no SDD_KIT.md exists; this is a bounded test harness with no architecture decision
- [N/A] `README.md` — the dedicated benchmark document is the user-facing reference and the existing README registry remains accurate
- [x] `.agents/continuity-codex.md` updated
- [x] Tests passing
- [N/A] `<route_map>` — no web routes, handlers, or models changed
- [ ] PR approved — remains `in_progress` until human review

## Honest Backlog
- The benchmark does not assert scanner behavior or prove network isolation at
  the operating-system firewall layer; those remain separate live contracts.
- The two legacy validators do not expose `--help`; adding that flag would be a
  separate compatibility change outside this test-only write set.
