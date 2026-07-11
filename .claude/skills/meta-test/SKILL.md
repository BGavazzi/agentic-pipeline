---
name: meta-test
description: Runs test fixtures for pipeline skills (builder/tester/notifier) using the Agent tool — spawns an isolated subagent per fixture, validates git state + task state + trajectory against expected.yaml. Triggers - "/test-builder", "/test-skills", "run skill tests", or user asks to validate a change in SKILL.md. Runtime - Claude Code session (kept open) — consumes subscription quota, not API tokens.
tools: Bash, Read, Glob, Agent
---

# meta-test

**Status: design spec, not yet implemented.** No fixture has been built and no
`tests/skills/` directory exists in this repo yet — everything below describes
the target architecture, not something that has run. Don't cite this skill's
tables as evidence of test coverage until at least one fixture under "How to
add a fixture" has actually been committed and passed.

For coverage that *does* exist today, see `tests/test_blast_radius.py` — a
plain pytest suite (no Agent-subagent sandboxing) that unit-tests
`scripts/blast_radius.py` directly. It's a different, simpler testing
approach than the one this skill describes.

**Runtime: open Claude Code session.** Skill for **testing skills** — no API tokens, no CI gate-on-PR; use manually after changing any `.claude/skills/<X>/SKILL.md` or periodically via `/loop /test-builder`.

"Tests in-session" architecture:
- Each fixture is an **isolated subagent** spawned via `Agent` tool.
- Subagent inherits the parent session context, receives a lean prompt pointing to the seed task.
- Parent session validates: git state + task.md state + trajectory (from subagent report) vs `expected.yaml`.
- No external process, no direct API calls — all within the session.

## When to invoke

- After editing `.claude/skills/<X>/SKILL.md` in any tested skill.
- When a new fixture is added to `tests/skills/fixtures/`.
- Periodically in loop (`/loop /test-builder`) — manual, not externally automated.

## What it tests today

Nothing yet — zero fixtures exist in this repo. The table below is the
planned first-batch coverage, not current state.

| Skill | Planned fixtures | Status |
|---|---|---|
| `builder` | 001-trivial-readme-edit | not implemented |
| `tester` | — | not planned yet |
| `notifier` | — | not planned yet |

Each fixture should cover a distinct case: happy path, decision-tree branch, anti-pattern detection. Don't duplicate.

## Main loop

```
1. Glob: tests/skills/fixtures/*/expected.yaml
   → list of executable fixtures

2. For each fixture:
   a. Bash: tests/skills/lib/setup.sh <fixture_name>
      → creates /tmp/test-<fixture_name>/ with extracted seed-repo
      → returns absolute path of the sandbox

   b. Agent tool spawn:
      subagent_type: general-purpose
      description: "Test <skill> via <fixture_name>"
      prompt: see "Subagent prompt template" §below

   c. Subagent returns text describing what it did:
      - list of tool calls in order
      - commits created (sha + msg)
      - final task status
      - any errors encountered

   d. Bash: tests/skills/lib/assert.sh <fixture_name> <sandbox_path>
      → compares git state + task.md vs expected.yaml
      → returns 0 (pass) or 1 (fail) + human-readable diff

   e. Bash: tests/skills/lib/teardown.sh <fixture_name> (cleans sandbox)
      ← OPTIONAL: skip teardown if TESTS_KEEP=1 (debug)

3. Output: summary table
   fixture | skill | pass | duration | notes
   001     | builder | ✅ | 45s | -
   002     | builder | ❌ | 32s | §Condition [3] not marked
```

## Subagent prompt template

Passed via `Agent` tool, adjusting `<placeholders>`:

```
You are a Builder subagent under test. Read your full instructions from
.claude/skills/builder/SKILL.md and behave exactly as production would.

Test context:
  Sandbox repo: <sandbox_path>
  Task to execute: <sandbox_path>/.docs/tasks/<task_filename>
  Working directory: <sandbox_path>

Constraints (NON-NEGOTIABLE — same as production):
  - Surgical changes only — §Affected Files is contract
  - Tests must pass at commit
  - Closure Law §3 complete or [N/A] with justification
  - NEVER --no-verify, --force, commit secrets
  - NEVER push (this is a sandbox)

At the end, report back in this exact format:

  RESULT
  ======
  Task status final: <todo|in_progress|done>
  Branch created: <branch_name>
  Commits: <count>
    - <sha1> <subject>
    - <sha2> <subject>
  Files touched: [<path1>, <path2>, ...]
  §Conditions marked done: <count>/<total>
  Closure Law §3 items addressed:
    - CHANGELOG: <yes|no|N/A>
    - function-catalog: <yes|no|N/A>
    - SDD_KIT: <yes|no|N/A>
    - README: <yes|no|N/A>
    - continuity: <yes|no|N/A>
    - tests passing: <yes|no|N/A>
    - ROUTE_BEHAVIOR_MAP: <yes|no|N/A>
  Errors encountered: [<list or 'none'>]
  Tool call sequence (high level): [Read, Read, Edit, Bash, Edit, Bash, Edit, Bash]

Begin execution.
```

## Fixture structure

```
tests/skills/fixtures/<NNN>-<slug>/
├─ seed-repo.tar.gz        bundled mini-repo with AGENTS.md + .docs/tasks/ + initial state
├─ task-id.txt             contains the task filename to execute (e.g., 0001-add-greeting.md)
├─ skill.txt               which skill is under test (builder | tester | notifier)
├─ expected.yaml           assertions to compare against subagent report + git state
└─ README.md               short description of what this fixture covers
```

`expected.yaml` schema:

```yaml
skill: builder
task_id: 0001-add-greeting
expected:
  task_status_final: done
  branch_pattern: "^feat/0001-"               # regex
  commits_min: 1
  commits_max: 3
  files_touched: [src/greeting.ts, .docs/tasks/0001-add-greeting.md, CHANGELOG.md]
  files_NOT_touched: [.env, package-lock.json]
  conditions_marked_done: 3                    # all conditions
  lei_de_fechamento:
    CHANGELOG: yes
    continuity: yes
    tests: yes
    # rest: N/A acceptable
  tool_calls_must_include_in_order:
    - Read         # AGENTS.md first
    - Read         # task
    - Edit         # implementation
    - Bash         # test
  tool_calls_must_NOT_include:
    - "git push"   # sandbox: no push allowed
  errors_expected: []
```

## Assertions (tests/skills/lib/assert.sh)

Bash script reads:
- expected.yaml
- subagent report (text)
- git state via `git -C <sandbox> log --oneline`, `git -C <sandbox> diff --stat`, `git -C <sandbox> branch`
- task file frontmatter via `head -20 <task_file>`

Compares field by field, outputs `PASS` or `FAIL: <field>: expected <X> got <Y>`. Exit 0 if all green.

## Decision tree — failures

```
Subagent exceeded quota / timeout:
├─ Fixture takes > 5min → mark SKIP, continue to next.
│
Subagent returned text outside RESULT format:
├─ Parsing fails → log the text, mark FAIL with reason "report format".
│
Git state assertion fails:
├─ Notes diff between expected and actual, marks FAIL.
├─ Does NOT teardown (preserves sandbox for manual inspection).
│
Task.md frontmatter still at "todo" at end:
├─ Subagent didn't complete the cycle. FAIL: "task not advanced".
│
Tool call sequence violated must_include_in_order:
├─ FAIL: "trajectory: missed <X> before <Y>".
```

## Hard rules

- **Never executes against a real repo** — always sandbox in `/tmp/test-*/`.
- **Never commit test results** to agentic-pipeline — `tests/skills/.last-run/` is in `.gitignore`.
- **Never calls API directly** (`curl https://api.anthropic.com/...`) — always `Agent` tool.
- **Idempotent**: running twice in a row must give the same result (complete teardown).
- **Subagent is isolated**: each fixture spawns 1 new subagent, no context leak between fixtures.

## Final output format

Illustrative — no run has produced this output yet:

```
META-TEST run @ <timestamp>
=============================
fixture                          skill    pass   duration   notes
001-trivial-readme-edit          builder  ✅     42s        —
002-failing-test-regression      builder  ❌     31s        Tests: did not stop at red
003-files-afetados-drift         builder  ✅     58s        Updated §Affected Files (1 extra commit OK)
004-lock-conflict-parallel       builder  SKIP   —          multi_agent: false in fixture AGENTS.md
005-push-blocked                 builder  ✅     38s        Reported branch local, no push

TOTAL: 3 pass / 1 fail / 1 skip out of 5 (60% pass)

Failed details:
  002-failing-test-regression:
    expected.errors_expected: ["task: blocked by fix/<NNNN>-broke-by-builder"]
    actual.errors_encountered: []
    → subagent did not detect the broken pre-existing test
```

## Anti-patterns

- ❌ Fixture that assumes state from another fixture (cross-contamination).
- ❌ Assertions on subagent text output (fragile) — use git state + task.md.
- ❌ Spawning subagent without a sandbox (will modify the real repo).
- ❌ `tool_calls_must_include` too specific (e.g.: "Bash with exact argument X") — breaks with SKILL.md refactor without benefit.

## Fixture roadmap

None of these have been built yet — this is a backlog, not a status report.

| Fixture | Covers | Status |
|---|---|---|
| `001-trivial-readme-edit` | simplest happy path — edits 1 file, 1 commit | not implemented |
| `002-failing-test-regression` | trap: pre-existing test breaks during implementation — Builder must STOP + create fix-task + blocked_by | not implemented |
| `003-files-afetados-drift` | trap: §What To Do needs a file outside §Affected Files — Builder updates contract first | not implemented |
| `004-never-delete-archive-instead` | trap: task asks to "remove" but AGENTS §2 forbids delete — Builder uses `mv .archive/` | not implemented |
| `005-lock-conflict-parallel` | trap: 3 subagents, 1 lock conflict resolved (parallelism via Agent tool) | not implemented — requires extra instrumentation |
| `006-tester-prototype-mode` | tester skill, boots-and-responds | not implemented (after tester upgrade) |
| `007-notifier-clickup-comment` | notifier skill, post comment with TL;DR | not implemented (after notifier upgrade) |

## How to add a fixture

1. `mkdir tests/skills/fixtures/<NNN>-<slug>/`
2. Create `seed-repo.tar.gz` with mini-repo (5–15 files max — small is important)
3. Create `task-id.txt`, `skill.txt`, `expected.yaml`, `README.md`
4. Run `/test-builder` locally; verify it passes
5. Commit + PR
