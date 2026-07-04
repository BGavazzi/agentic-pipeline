---
name: dispatcher
description: Local orchestrator of the agentic pipeline. Processes task queue in <cwd>/.docs/tasks/*.md (status=todo) — invokes grounding → builder → tester → librarian → notifier sequentially; automatic push + PR when cycle is green; optional ClickUp comment (only when task has clickup_id AND CLICKUP_API_KEY is set). Trust mode (no pause-confirm between tasks; queue is the gate). Nightly loop bounded by REAL plan quota (quota_gate.py reads rate_limits from statusline: stops at 70% of the 5h window, 10pts/day and 50pts/week of the 7d window, task cap). Pipeline scripts in PIPELINE_SCRIPTS_DIR (default: <repo>/scripts/). Triggers - "/dispatcher", "run queue", "process tasks", "pick next task". Supports /loop /dispatcher via ScheduleWakeup. STATUS - V1.1 quota-bounded, TOS-safe (within interactive Claude Code session).
tools: Bash, Read, Edit, Write, Glob, Grep, Skill, ScheduleWakeup
---

# Dispatcher

**Runtime: open + interactive Claude Code session.** Human spec: `.docs/skills/dispatcher.md`.

Orchestrator. When invoked: picks 1 ready task from the queue, runs pipeline end-to-end, closes it. In `/loop` mode uses ScheduleWakeup to re-fire.

## 1. Inputs

- `cwd`: working dir of the Claude Code session (assumed = target repo)
- `repo_path`: optional override (default = cwd)
- `loop_mode`: detected via prompt `/loop /dispatcher` (Claude Code primitive)

**Quota source (loop mode):** `<repo_path>/.claude/quota-state.json`, written by the statusline (`.claude/statusline_quota.py`) from the `rate_limits` block that Claude Code injects (`five_hour`/`seven_day` windows, Pro/Max only, populated after the 1st API response). Prerequisite: `.claude/settings.json` with `statusLine` pointing to the script. If absent, the gate gives STOP fail-safe. Loop state in `<repo_path>/.claude/dispatcher-loop-state.json` (gitignored).

## 2. Find next ready task

```bash
# Locate pipeline scripts — set PIPELINE_SCRIPTS_DIR env var to override
SCRIPTS_DIR="${PIPELINE_SCRIPTS_DIR:-$repo_path/scripts}"
# (copy agentic-pipeline/scripts/ into your repo root, or point PIPELINE_SCRIPTS_DIR
#  at wherever validate_task.py / validate_closure.py / quota_gate.py live)

# Scan task dir
TASK_DIR="$repo_path/.docs/tasks"
test -d "$TASK_DIR" || exit "no .docs/tasks/ in repo"

# Iterate tasks in priority + NNNN order
for task in $(ls "$TASK_DIR"/*.md | sort); do
  # Parse frontmatter status + priority + blocked_by
  # (use head -30 + grep/awk; OR Python one-liner via PyYAML)

  # Filter: status==todo
  # Filter: blocked_by tasks all in completed/
  # Filter: no PR already open for feat/<NNNN>-*

  echo "$task"  # first match wins
  break
done
```

**Priority order**:
1. `priority: P0` first
2. then `P1`
3. then `P2`
4. Within same priority: ascending NNNN

**Skip criteria**:
- `status != todo`
- Any `blocked_by` task is NOT in `completed/` (still active)
- Branch `feat/<NNNN>-*` already exists on origin with open PR

If queue is empty → §6 (exit without ScheduleWakeup).

## 3. Validate task (deterministic gate)

```bash
python "$SCRIPTS_DIR/validate_task.py" "$task"
```

- exit 0 → proceed
- exit 1 → mark task as blocked + append validator error to §Honest Backlog; continue queue (does not block)
- exit 2 → script error (PyYAML missing) → STOP, log fatal

## 4. Main loop (per task)

```
1. Read task: parse frontmatter (status, priority, type, target_repo, clickup_id, blocks, blocked_by, files_affected)
2. Update task: status: in_progress, updated: <today>
3. Branch (base = integration in repo with deploy; else main):
   BASE=$(git ls-remote --heads origin integration | grep -q . && echo integration || echo main)
   git checkout "$BASE"
   git pull --rebase origin "$BASE"
   git checkout -b feat/<NNNN>-<slug>  (or checkout existing if already created)
4. Invoke Skill(codebase-grounding) with task_path + repo_path
   → result: context + constitution loaded
5. Invoke Skill(builder) with task_path + brief from grounding
   → result: commits on branch, task checkboxes marked
6. Invoke Skill(tester) with task_path + branch + mode='prototype'
   → result: prose report + ARTIFACT .docs/test-reports/<NNNN>.{xml,json}
   - GATE ON ARTIFACT, not prose (anti-AI-pitfall): read the .json and require
     exists? · git_rev == branch HEAD? · all steps exit 0? · coverage ≥ threshold (if §Condition requires)?
   - Any one fails/absent:
     → append §Honest Backlog in task with link to report
     → SKIP downstream; jump to §5 (continue queue)
6b. Invoke Skill(ultrareview) with task_path + branch + test_report + risk_level
    (INDEPENDENT subagent — does not inherit the tester's "passed")
    → re-runs the suite + fake-green scan + (high risk) adversarial majority
    → result: .docs/review-reports/<NNNN>-<ts>.md with verdict PASS|BLOCK
    - risk_level: 'high' if task touches schema/RBAC/migration/contract; else 'normal'
    - BLOCK → append §Backlog + link; SKIP downstream; jump §5
7. Invoke Skill(librarian) with task_path + branch + tester_report_path
   → librarian runs validate_closure.py internally (already wired)
   → result: docs committed, frontmatter librarian_pass set
   - If librarian fails: same as above (skip downstream, continue)
8. Push + PR + notification:
   git push origin feat/<NNNN>-<slug>  (non-interactive — token cached / SSH key)
   gh pr create --base "$BASE" --title "<title from task>" --body-file <prepared from CHANGELOG_BRANCH>   # $BASE from §3
   - No --reviewer flag (no @-mention; solo pattern)
   # ClickUp is opt-in: only notify if task has clickup_id AND CLICKUP_API_KEY is set
   if task.clickup_id AND env.CLICKUP_API_KEY:
     Invoke Skill(notifier) with event='pr.opened' + payload {clickup_id, pr_url, title, channels=['clickup','github']}
     → notifier posts ClickUp comment + GitHub PR comment
   else:
     Invoke Skill(notifier) with event='pr.opened' + payload {pr_url, title, channels=['github']}
     → notifier posts GitHub PR comment only
9. Move task → completed/:
   git mv .docs/tasks/<NNNN>-*.md .docs/tasks/completed/
   git commit -m "chore(NNNN): move task to completed/"
   git push
10. Log:
    Write <repo>/.docs/dispatcher-log/<YYYY-MM-DD>-<NNNN>.md with TL;DR
11. Quota gate (loop mode) — run the deterministic gate marking this task as complete:
    python "$SCRIPTS_DIR/quota_gate.py" --repo "$repo_path" --record --json
    Stores the verdict + quota numbers (5h/7d, day consumption, loop day). Exit code
    (0=CONTINUE / 1=STOP) decides §6. Single-shot mode: run without --record just to report.
12. Output to caller (§5)
```

## 5. Output (per task)

```
✅ Dispatcher — task <NNNN>: <title>
Repo: <repo>
Branch: feat/<NNNN>-<slug>
PR: #<num> https://github.com/<org>/<repo>/pull/<num>
Commits: <N>
Tests: <pass details OR pending>
Librarian: 7/7 Closure Law §3 OK
ClickUp: <comment_id | skipped (no clickup_id or no CLICKUP_API_KEY)>
Quota: 5h <X%> · 7d <Y%> · loop consumption today <D>/10pts · day <N> of cycle · tasks <T>/5
Next: <CONTINUE → ScheduleWakeup 60s | STOP <gate reason> → loop ends>
```

If task SKIPPED (validator fail OR tester red OR librarian fail):
```
⚠️ Dispatcher — task <NNNN> SKIPPED: <reason>
State: status remains in_progress, §Honest Backlog updated
Branch: <branch_status — created/dirty/clean>
Next: human triage required BEFORE next invocation
```

## 6. Stop / ScheduleWakeup

After task processed (success OR skip):

**Single-shot mode** (`/dispatcher`):
- Normal exit. No ScheduleWakeup. Awaits new human invocation.

**Loop mode** (`/loop /dispatcher`):

Decision gated by REAL plan quota. Only fires next wake if **ALL** are true:
1. queue still has a ready task, AND
2. `quota_gate.py` (§4 step 11) returned **exit 0 (CONTINUE)**.

→ `ScheduleWakeup(60, '/dispatcher', 'next task in queue')`

**Stops the loop (no ScheduleWakeup) if ANY:**
- queue empty → "queue empty, loop ends".
- `quota_gate.py` exit 1 (**STOP**) → report the exact gate reason (e.g.: "5h at 71%", "daily 7d budget spent: 10pts", "weekly budget 50pts", "task cap 5/5", "quota signal missing — fail-safe"). **DO NOT bypass, DO NOT retry.** Loop ends cleanly; resumes next night (new loop-day) or when window resets.
- 3 consecutive tasks SKIPPED → exit (human triage).

The gate is the only authority on "can we continue?". The dispatcher NEVER estimates quota on its own nor ignores a STOP. If `quota-state.json` doesn't exist (statusline not configured), the gate gives STOP fail-safe — configuring `.claude/settings.json` + `statusline_quota.py` is a loop mode prerequisite.

## 7. Hard rules

- **TOS-safe**: runs ONLY within the interactive Claude Code session opened by the human. NEVER invoke `claude` CLI as a subprocess.
- **Quota is law.** In loop mode, `quota_gate.py` is the only authority on "can we continue?". Gate STOP = loop ends, no exception, no bypass, no retry (aligned with ToS mitigation: volume bounded → [[anthropic-tos-loop-considerations]]). Ceilings: 70% of 5h window; 10pts/day and 50pts/week of 7d window; task cap. Missing quota signal → STOP fail-safe (never CONTINUE in the dark).
- **Does not invent tasks.** Only processes what exists in `.docs/tasks/` with `status: todo`. (See memory [[feedback-keep-going-not-scope-inventing]].)
- **Does not modify task spec.** Reads §What To Do + §Exit Conditions; if ambiguous, marks blocked in §Backlog.
- **No @-mention of reviewer** in ClickUp/GitHub comments. Solo pattern. Notifier without `mentions` payload.
- **Does not merge** on GitHub. Only push + PR. Merge is always human.
- **Does not choose model.** Runs on the current session's model.
- **Idempotency**: task already in `completed/` = no-op. Branch with open PR already = skip create; if ClickUp active, update comment.
- **Crash safety**: if Claude Code dies, task in `in_progress` is re-pickable on next invocation (validate_task detects state and retries).
- **Push non-interactive**: if push prompts credentials, ABORT + log + skip task. Does not wait for input (reference [[git-push-hang-is-afk-timeout]]).

## 8. Failure modes

| Error | What to do |
|---|---|
| Queue empty | Exit, no ScheduleWakeup. Log "queue empty, /loop ends". |
| `validate_task.py` exit 1 | Append error to §Backlog, continue queue |
| Branch exists + PR open | Skip create; if ClickUp active (clickup_id + key), update comment |
| `git push` rejected (non-fast-forward) | `git pull --rebase origin main`; if conflict → mark blocked, continue |
| `git push` hang (credential prompt) | Timeout 30s → kill + skip task + log [[git-push-hang-is-afk-timeout]] |
| `gh pr create` fails (auth) | Log + continue queue (next invocation retries) |
| Tester red / artifact absent | Continue queue; report in .docs/test-reports/. No artifact = gate blocks (tester didn't run). |
| Ultrareview BLOCK | Continue queue; task stays in_progress; .docs/review-reports/ has the finding. DO NOT bypass (it's the anti-pitfall). |
| Librarian error | Continue queue; task stays in_progress for re-run |
| Notifier fails (ClickUp 4xx) | Log; does not block (PR already open) |
| 3 consecutive tasks SKIPPED | Exit /loop. Signal of a queue or environment problem. |
| `quota_gate.py` exit 1 (STOP) | Exit /loop cleanly. Report reason (5h/daily/weekly/cap/fail-safe). Do not bypass. Resumes next night or at window reset. |
| `quota-state.json` absent/empty | Gate gives STOP fail-safe. Check `.claude/settings.json` statusLine + 1st API response occurred. |
| Network down | Retry with backoff (15s, 60s, 300s); then mark task blocked, continue |
| Claude Code session interrupted (Ctrl+C) | Current task stays `in_progress`; queue does not progress. Next invocation picks it back up. |

## 9. Anti-patterns

- ❌ Polling `.docs/tasks/` in parallel (race condition on `status: in_progress` update)
- ❌ Auto-push with `--force` (rule: never force push)
- ❌ ClickUp comment trying to "sell" the work ("Looks great! All tests passing! 🎉") — caveman + factual (see ClickUp comment convention)
- ❌ Skipping validator with `|| true` ("should be fine")
- ❌ Processing task with missing `priority` — validate_task fails anyway
- ❌ Spawning subagents for different tasks in parallel V1 (race condition on git branches)
- ❌ Inventing `status: todo` on a task that didn't have it (= inventing work)

## 10. Skills consumed

Upstream (none — dispatcher is the top).

Downstream (orchestrated by this skill):
- [[codebase-grounding]] (Step 0 constitution loading)
- [[builder]] (impl + commits)
- [[tester]] (V1 prototype mode — emits the proof-of-execution artifact)
- [[ultrareview]] (independent adversarial gate; gates on artifact + re-run, not prose)
- [[librarian]] (Closure Law §3, runs validate_closure.py)
- [[notifier]] (ClickUp comment + GH comment if applicable)

Validators / gates (in `$PIPELINE_SCRIPTS_DIR`, default `<repo>/scripts/`):
- `validate_task.py` (before builder)
- `validate_closure.py` (inside librarian)
- `quota_gate.py` (end of each task in loop mode — decides ScheduleWakeup)

## 11. Concrete example

User invokes `/loop /dispatcher` in Claude Code open in `<path>/my-repo/`:

```
Turn 1:
  - Scan .docs/tasks/ → P0 first → finds 0095-feat-something.md (status: todo)
  - Validate task: PASS
  - Update status: in_progress
  - git checkout -b feat/0095-something main
  - Skill(codebase-grounding) → constitution loaded
  - Skill(builder) → 5 commits, checkboxes [x]
  - Skill(tester) → type-check + lint + boots OK
  - Skill(librarian) → CHANGELOG, SDD entry, continuity; validate_closure PASS
  - git push, gh pr create → PR #N
  - Skill(notifier) → ClickUp comment ✅
  - git mv task → completed/, commit, push
  - quota_gate.py --record → CONTINUE (5h 22% · 7d +3pts today · day 1 · tasks 1/5)
  - ScheduleWakeup(60s, '/dispatcher', 'next task')

Turn 2 (60s later):
  - Scan → 0096-fix-xyz.md (status: todo)
  - ... same cycle → quota_gate CONTINUE (tasks 2/5) → ScheduleWakeup

Turn N (one of these ends the loop):
  - Scan → queue empty → exit, "/loop ends"
  - OR quota_gate STOP "5h at 71%" / "daily budget 10pts" / "cap 5/5" → exit, reports reason
  - OR 3 SKIPPED in a row → exit
```

User can `/stop` the /loop at any time. The gate ensures that, AFK, the loop
stops itself on hitting any quota ceiling — it doesn't blow through the plan.

## 12. V2 backlog

- ClickUp `AI: ready to start!` tag polling (requires proxy/webhook)
- Multi-repo scan (`--repos R1,R2,R3`)
- Model selection per task (consults `MODEL-SELECTION.guidelines.md`)
- Concurrent dispatch via Agent subagents for independent tasks
- Metrics: tokens/task, wallclock, % first-try pass — writes `.docs/dispatcher-metrics.jsonl`
- Resume after crash: detect `in_progress` tasks and offer re-run vs abandon
