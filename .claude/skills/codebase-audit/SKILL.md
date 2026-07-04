---
name: codebase-audit
description: Audits a repo (read-only) against its own declared rules in CLAUDE.md/AGENTS.md/SDD_KIT.md. Produces a violation report across 10 dimensions (missing endpoint docs, swagger missing, route not in map, orphan Dxx, migration without rollback, entity without migration, test orphan, route without test, stale continuity, claude.md self-violation). Triggers - "audit the repo", "drift scan", "check CLAUDE.md violations", "monthly housekeeping". STATUS - ready (V1 = 5 core checks; other 5 = backlog).
tools: Read, Bash, Glob, Grep, Write
---

# Codebase Audit

**Runtime: open Claude Code session. Read-only.** Human spec: `.docs/skills/codebase-audit.md`.

**Do NOT confuse with [[clickup-audit]]** (ClickUp workspace). This audits a **repo** against the constitution declared within it.

V1 implements 5 core checks:
1. `endpoint_doc_missing`
2. `route_not_in_map`
3. `sdd_decision_orphan`
4. `claude_md_self_violation`
5. `continuity_stale`

V2 backlog (specified but not V1): swagger_decorators_missing, migration_no_rollback, entity_no_migration, test_orphan, route_no_test.

## 1. Inputs

- `repo_path`: working tree (mandatory)
- `checks`: optional — subset by name (default: all V1)
- `severity_floor`: `info | warn | error` (default: `warn`)
- `since`: optional — only audits files modified after ISO date

## 2. Preconditions

```bash
test -d "$repo_path/.git" || STOP "repo_path is not a git repo"
ls "$repo_path/CLAUDE.md" "$repo_path/AGENTS.md" "$repo_path/AGENTS.balanced.md" 2>/dev/null | \
  head -1 || STOP "repo has no declared constitution — audit is a no-op"
mkdir -p "$repo_path/.docs/audit-reports/"
```

## 3. Main loop

```
1. Load constitution (same flow as codebase-grounding Step 0):
   - Read CLAUDE.md (if exists)
   - Read AGENTS.md / AGENTS.balanced.md (if exists)
   - Read SDD_KIT.md (if exists)
   - Read ROUTE_BEHAVIOR_MAP.md (if exists)
   - Capture hard_rules (phrases must/never/always)

2. For each check in `checks`:
   a. Apply rule to the codebase (§4 below)
   b. List violations [(file, line, endpoint?, severity)]
   c. Filter by severity_floor

3. Write report:
   - Markdown: <repo>/.docs/audit-reports/<YYYY-MM-DD>-codebase-audit.md
   - JSON: <repo>/.docs/audit-reports/<YYYY-MM-DD>-codebase-audit.json

4. Output summary to user (§5 below).

5. Do NOT create tasks. Human triage decides.
```

## 4. Checks — implementation

### 4.1. endpoint_doc_missing

Applies when constitution has a rule like "every endpoint requires .bru" or "every endpoint needs docs in docs/api/...".

```bash
# Find HTTP handlers (NestJS pattern)
grep -rn -E "@(Get|Post|Put|Patch|Delete)\(" --include="*.ts" "$repo_path/src/"
# → list of files:line → endpoint paths

# Find .bru files
find "$repo_path" -name "*.bru" -type f | xargs grep -l "post:\|get:\|put:\|patch:\|delete:"
# → set of documented endpoints

# Diff: handlers WITHOUT a corresponding .bru
```

Severity: `error` (rule says "must/requires").

### 4.2. route_not_in_map

If `ROUTE_BEHAVIOR_MAP.md` exists: each handler should have an entry.

```bash
# Set of routes in the map
grep -E "^- (GET|POST|PUT|PATCH|DELETE) " "$repo_path/ROUTE_BEHAVIOR_MAP.md"
# Set of routes in code (from previous check)
# Diff
```

Severity: `warn` (map is honor-practice, not blocking).

### 4.3. sdd_decision_orphan

`Dxx` references in code without an entry in SDD_KIT.md.

```bash
# Capture all `// D01`, `// D02`, etc in code
grep -rn -E "//\s*D[0-9]+|#\s*D[0-9]+" --include="*.ts" --include="*.py" --include="*.js" "$repo_path/src/"

# Capture D's documented in SDD_KIT
grep -E "^##?\s+D[0-9]+" "$repo_path/SDD_KIT.md" | sed -E 's/.*D([0-9]+).*/D\1/'

# Diff: codes without entry
```

Severity: `warn`.

### 4.4. claude_md_self_violation

CLAUDE.md cites a file/path/directory that doesn't exist.

```bash
# Extract refs from CLAUDE.md (paths starting with src/, docs/, .docs/, etc)
grep -oE "\`[a-zA-Z0-9_./\-]+\.(ts|tsx|js|jsx|md|py|sql|yaml|yml|json|bru)\`" "$repo_path/CLAUDE.md"

# For each path: test -e (relative to repo_path)
# List broken refs
```

Severity: `error` (rules pointing to nothing = broken rules).

### 4.5. continuity_stale

`.agents/continuity-*.md` with mtime > 90d if there is recent activity on the branch.

```bash
# List continuity files
ls -la "$repo_path/.agents/continuity-"*.md 2>/dev/null

# For each: mtime + compare with repo's last commit
last_commit_ts=$(git -C "$repo_path" log -1 --format=%ct)
for f in continuity-*.md; do
  mtime=$(stat -c %Y "$f")
  delta_days=$(( (last_commit_ts - mtime) / 86400 ))
  if [ "$delta_days" -gt 90 ]; then echo "STALE $f $delta_days days"; fi
done
```

Severity: `info` (human decides whether to keep it).

## 5. Output

```
✅ Audit — <repo>
Constitution: CLAUDE.md, AGENTS.balanced.md, SDD_KIT.md
Checks: 5/5 V1

Violations:
  error: <N>
  warn:  <M>
  info:  <K>

Top 3 (error):
  1. endpoint_doc_missing — POST /notifications/register-token (src/notifications/notificationController.ts:42)
  2. endpoint_doc_missing — POST /notifications/test-notification (src/notifications/notificationController.ts:68)
  3. claude_md_self_violation — `docs/api/Notifications/` (CLAUDE.md §1, target dir doesn't exist)

Report: <repo>/.docs/audit-reports/2026-05-28-codebase-audit.md
JSON:   <repo>/.docs/audit-reports/2026-05-28-codebase-audit.json

Next: human triage → create chore/<NNNN> tasks for what's worth fixing.
```

## 6. Report format (markdown)

```markdown
# Codebase Audit — <repo>

**Date**: <YYYY-MM-DD>
**Constitution sources**: CLAUDE.md, AGENTS.balanced.md
**Checks run**: 5
**Severity floor**: warn

## Summary

| Severity | Count |
|---|---|
| error | 2 |
| warn | 5 |
| info | 10 |

## Violations — error

### endpoint_doc_missing (rule: CLAUDE.md §1)

> "Every HTTP endpoint requires a .bru file under docs/api/Blue Events API/"

- `src/notifications/notificationController.ts:42` — POST /notifications/register-token
- `src/notifications/notificationController.ts:68` — POST /notifications/test-notification

**Suggested action**: create .bru files OR document in SDD_KIT as justified exception.

### claude_md_self_violation

- `CLAUDE.md` line 23: references `docs/api/Notifications/` — directory doesn't exist

## Violations — warn

[...]
```

## 7. Hard rules

- **Read-only.** No file in the audit-target repo is modified outside `.docs/audit-reports/`.
- **Does not create tasks.** Human triage decides.
- **Does not auto-fix.** Even if the violation is trivial (missing .bru), audit doesn't create — to force the human to see the aggregate.
- **Does not invent rules.** If CLAUDE.md doesn't mention `.bru`, audit doesn't check `.bru`.
- **Performance**: cap at 60s. Exceeded → partition by path + warn.

## 8. Failure modes

| Error | What to do |
|---|---|
| Repo without constitution | No-op + log "repo has no CLAUDE.md/AGENTS.md — audit incomplete" |
| Glob returns 10k+ matches | Partition by subdir, warn in report |
| Specific check crashes | Skip, log, continue others |
| Audit interrupted | Save partial with flag `"incomplete": true` in JSON |
| .docs/audit-reports/ doesn't exist | Create (sole exception to read-only) |
| Contradictory constitution detected | Separate report `<date>-constitution-conflicts.md` |

## 9. Anti-patterns

- ❌ Auto-creating ClickUp tasks for each violation (human triage is part of the design).
- ❌ Edit/Write to audit-target repo files outside `.docs/audit-reports/`.
- ❌ Reporting "universal best practices" not declared in the constitution (use TS, use ESLint).
- ❌ Running as a gate in the critical Builder→Tester→Librarian cycle (audit is outside the cycle).
- ❌ Inflated severity — every `error` rule becomes noise.
- ❌ Audit called in a loop by the cycle — 1x/month per repo is the pattern.

## 10. Related skills

- [[codebase-grounding]] — reuses Step 0 (constitution loading).
- [[librarian]] — NNNN scope; this is aggregate scope. Complementary.
- [[clickup-audit]] — workspace, not repo.
