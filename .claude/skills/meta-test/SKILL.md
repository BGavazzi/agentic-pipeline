---
name: meta-test
description: Runs test fixtures for pipeline skills (builder/tester/notifier) using the Agent tool — spawns an isolated subagent per fixture, validates git state + task state + trajectory against expected.yaml. Triggers - "/test-builder", "/test-skills", "run skill tests", or user asks to validate a change in SKILL.md. Runtime - Claude Code session (kept open) — consumes subscription quota, not API tokens.
tools: Bash, Read, Glob, Agent
---

# meta-test

**Status: implemented contract runner.** `scripts/meta_test.py` runs the
fixture corpus in disposable git sandboxes and emits a schema-v1 receipt with
versioned metrics. A runtime supplies the worker command, so the same contract
can run a local fake worker, a homelab agent worker, or another isolated
adapter without granting the runner a real checkout or remote.

For coverage that *does* exist today, see `tests/test_blast_radius.py` — a
plain pytest suite (no Agent-subagent sandboxing) that unit-tests
`scripts/blast_radius.py` directly. It's a different, simpler testing
approach than the one this skill describes.

**Runtime: isolated worker process.** The runner does not call an agent API
itself; a pool dispatcher supplies the worker command. Use
`python scripts/meta_test.py` after changing any `.claude/skills/<X>/SKILL.md`
or from a trusted integration lane.

"Tests in-session" architecture:
- Each fixture is an **isolated worker process** launched by the runtime.
- The worker receives the sandbox and task through `PIPELINE_META_TEST_*` environment variables.
- The runner validates git state + task state + trajectory against `expected.yaml`.
- No remote is configured and no shell is invoked by the runner.

## When to invoke

- After editing `.claude/skills/<X>/SKILL.md` in any tested skill.
- When a new fixture is added to `tests/skills/fixtures/`.
- Periodically in loop (`/loop /test-builder`) — manual, not externally automated.

## What it tests today

The first fixture is executable and committed. The remaining rows are
intentionally backlog.

| Skill | Planned fixtures | Status |
|---|---|---|
| `builder` | 001-trivial-readme-edit | implemented |
| `tester` | — | not planned yet |
| `notifier` | — | not planned yet |

Each fixture should cover a distinct case: happy path, decision-tree branch, anti-pattern detection. Don't duplicate.

## Main loop

```
1. Run `scripts/meta_test.py --fixtures tests/skills/fixtures --base-sha ...
   --head-sha ... --output .docs/meta-test-reports/<task>.json --command ...`.
   The worker receives `PIPELINE_META_TEST_SANDBOX`, `..._FIXTURE`,
   `..._SKILL`, and `..._TASK` environment variables.

2. For each fixture, the runner creates a fresh git repository, launches the
   worker in it, compares observable results against `expected.yaml`, and
   tears the sandbox down even when the fixture fails.

3. Output: a schema-v1 receipt with metrics and a case table
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

These remain backlog items, not claims of coverage.

| Fixture | Covers | Status |
|---|---|---|
| `001-trivial-readme-edit` | simplest happy path — edits 1 file, 1 commit | implemented |
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
