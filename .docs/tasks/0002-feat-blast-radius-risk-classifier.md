---
status: todo
priority: P1
type: feat
created: 2026-07-04
updated: 2026-07-04
clickup_id: null
parent: null
blocks: []
blocked_by: []
---

# 0002 — Feat: diff-scoped blast-radius + risk-tier classifier gate

## Context
Discussion (2026-07-04) on scaling test scope to the size/risk of a change
instead of either "always run everything" or "trust the LLM to pick tests."
`ultrareview` already computes `risk_level: high` for tasks touching
schema/RBAC/migration/contract (see its SKILL.md), but nothing today computes
*blast radius* (which modules/tests a diff plausibly affects) or extends risk
classification to infra changes (Ansible/Rancher/Nexus-shaped tasks). This
task adds a single deterministic script that both `tester` and `ultrareview`
can consume, rather than each guessing scope independently.

## Problem
Today, `tester` and `ultrareview` either run a fixed test scope or rely on
the model's judgment about what's "relevant" to re-run — which is exactly the
kind of self-reported claim the pipeline's anti-fake-green philosophy
(gate on artifacts, not prose) already refuses to trust elsewhere.

## What To Do
- [ ] Add `scripts/blast_radius.py`, run right after [[builder]] and before
  [[tester]]:
  - Input: `git diff <base>...<branch>` (changed files)
  - Signal 1 — ownership map: cheap per-module "who depends on me" list
    (hand-maintained `.docs/module-owners.md` or similar; missing entries
    default to "unknown, widen scope")
  - Signal 2 — import/grep heuristic: what references each changed file
    (language-appropriate grep/AST, not a full dependency-graph build)
  - Signal 3 — historical co-change: files that have changed together with
    the diff's files in prior commits (`git log` mining), catching coupling
    imports miss (config, migrations, docs)
  - Union the three signals into `affected_modules`
- [ ] Extend risk classification (reuse, don't duplicate, `ultrareview`'s
  existing `risk_level` logic) with path/diff triggers for: auth/RBAC,
  migrations, payment logic, and — per the Ansible/Rancher/Nexus discussion —
  IaC changes touching prod inventory, Rancher RBAC/cluster-role manifests,
  Fleet bundles, or Nexus repository/firewall policy
- [ ] Emit `.docs/blast-reports/<NNNN>.json`:
  `{changed_files, affected_modules, risk_level, required_gates}` where
  `required_gates` is drawn from `["unit","integration","sast","sca",
  "ultrareview","infra-dry-run"]` based on risk tier
- [ ] Wire `tester` and `ultrareview` SKILL.md to read `required_gates` from
  this artifact instead of deciding scope themselves
- [ ] For `risk_level: high` infra tasks, `required_gates` must include
  `infra-dry-run` (`ansible-playbook --check --diff`, `helm template` +
  `kubeconform`, or Fleet dry-run depending on what changed)

## Affected Files
- `scripts/blast_radius.py` (new)
- `.claude/skills/tester/SKILL.md` (consume `required_gates`)
- `.claude/skills/ultrareview/SKILL.md` (consume `required_gates`; extend
  risk-trigger list)
- `.gitignore` (`.docs/blast-reports/`)

## Exit Conditions
- [ ] `blast_radius.py` runs standalone against a diff and emits a valid
  JSON artifact with all four keys populated
- [ ] Risk-tier trigger list is a single shared source (not copy-pasted
  between `blast_radius.py` and `ultrareview`'s own logic)
- [ ] At least one `meta-test` fixture confirms a change under a path tagged
  high-risk (e.g. an auth/ or infra/ sandbox path) produces
  `risk_level: high` and the expected `required_gates`

## Required Documentation (Closure Law)
- [ ] `CHANGELOG.md` updated
- [ ] `<function_catalog>` — [N/A] core/tooling repo, no function-catalog.md
- [ ] `<sdd_kit_path>` — [N/A] no SDD_KIT.md in this repo yet
- [ ] `README.md` updated (mention the new gate in the pipeline diagram)
- [ ] `.agents/continuity-<agent>.md` — [N/A] no continuity ledger in use yet
- [ ] Tests passing (meta-test fixture)
- [ ] `<route_map>` — [N/A] no HTTP routes in this repo
- [ ] PR approved

## Honest Backlog
- Historical co-change mining (signal 3) needs a minimum commit-history depth
  to be useful; on a fresh/shallow-cloned repo it degrades to signals 1+2
  only — acceptable for V1, flagged here rather than blocking the task.
