#!/usr/bin/env python3
"""
core_sync.py — vendors the agentic core (skills + gate scripts + shared
conventions) into a target repo.

Purpose: the portfolio benchmark (.docs/analysis/completeness-benchmark-2026-09.md)
found the doctrine followed almost perfectly by the repos it was written for
(FIS, median 20/24) and almost not at all by the rest of the portfolio (median
6/24) — not because the doctrine is wrong, but because adopting it was manual
copy-paste that nobody actually did. This script is that copy-paste,
automated and safe to re-run.

Usage:
    python scripts/core_sync.py <target_repo> [--dry-run] [--skills S1,S2,...]

    python scripts/core_sync.py D:/vibes/garimpo
    python scripts/core_sync.py D:/vibes/cv --dry-run
    python scripts/core_sync.py D:/vibes/baton --skills builder,tester,librarian

Exit codes:
    0 -- sync completed (or, with --dry-run, would have completed) cleanly
    2 -- usage error (target doesn't exist, source tree malformed, etc.)

What it does (all additive — never deletes anything in the target):
    1. Copies every skill dir under .claude/skills/ into <target>/.claude/skills/
       (overwrites by name — these ARE meant to be overwritten on every sync;
       AGENTS.md itself says "Core is read-only" locally, fix upstream and
       re-copy). --skills restricts this to a comma-separated allowlist of
       skill names; default is all of them.
    2. Copies the whitelisted gate scripts (GATE_SCRIPTS below) into
       <target>/scripts/ — NOT the whole scripts/ dir, so a target repo's own
       unrelated scripts/ files are never touched.
    3. Copies .docs/conventions/*.md into <target>/.docs/conventions/.
    4. Writes <target>/AGENTS.md from the generic template ONLY if the target
       has no AGENTS.md yet. An existing AGENTS.md is never touched — per its
       own header, "This file is repo-specific and is NEVER overwritten by a
       core sync." The template embedded here is this repo's own AGENTS.md
       before it was filled in for task 0006 (see git history on that file
       pre-fill, or .docs/tasks/0006-*.md).

What it deliberately does NOT do (V1 scope — see Honest Backlog in the task
file for what's cut):
    - Does not create .agents/continuity-<agent>.md (agent-specific, created
      on first read per AGENTS.md §0, not something to seed blindly).
    - Does not create .docs/tasks/ or CHANGELOG.md (project-specific content,
      not core).
    - Does not diff/warn when a target's vendored skill or gate script has
      DRIFTED from source (e.g. someone edited a vendored copy locally,
      violating "core is read-only") — it just overwrites. A drift-detection
      pass is future work, not V1.
    - Does not touch git (no commit, no branch) — the caller reviews the diff
      and commits it themselves, same as any other change.
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

# The only scripts/ files core_sync touches — deliberately a whitelist, not
# "everything in scripts/", so a target repo's own project-specific scripts
# are never at risk of being overwritten by an unrelated same-named file.
GATE_SCRIPTS = [
    "validate_task.py",
    "validate_closure.py",
    "blast_radius.py",
    "scan_gate.py",
    "quota_gate.py",
]

# This repo's own AGENTS.md as it existed before task 0006 filled it in —
# the generic, project-agnostic seed for a repo that has none yet.
AGENTS_MD_TEMPLATE = """\
# AGENTS.md — <project_name>

Local constitution. **Inherits the agentic core** vendored from
[BGavazzi/agentic-pipeline](https://github.com/BGavazzi/agentic-pipeline)
(`.claude/skills/` + `scripts/` copied in directly, or pointed at via
`PIPELINE_SCRIPTS_DIR` — see that repo's README Quick Start).
This file is repo-specific and is NEVER overwritten by a core sync — edit it freely.

**Version**: 0.1.0  ·  **Status**: <tier>  ·  **Type**: <one-line type>

---

## §0 Protocol Zero — Continuity

1. **READ** `.agents/continuity-<your-agent>.md` (create if it doesn't exist).
2. **ALIGN** with the "Current Focus".
3. **UPDATE** at the end of the session.

```yaml
multi_agent: false
sdd_kit_path: docs/SDD_KIT.md
function_catalog: .docs/function-catalog.md
route_map: .docs/ROUTE_BEHAVIOR_MAP.md
task_dir: .docs/tasks
clickup_list_id: <optional, if synced>
pipeline_scripts_dir: <optional, defaults to ./scripts/>   # see PIPELINE_SCRIPTS_DIR in agentic-pipeline's README
```

---

## §1 Identity and Scope

**Name**: <project_name>
**Maintained by**: <maintainer>
**Type**: <type>
**Tier**: <prototype | active | canonical>

### 1.1 Stack
| Layer | Technology |
|---|---|
| <e.g.: Runtime> | <e.g.: FastAPI + Docker> |

---

## §2 Hard Rules

🔒 **Never delete** files. `mv` to `.archive/`.
🔒 **Never commit OR post secrets.** `.env` in `.gitignore`. Never write credentials to external systems (ClickUp/GitHub/Slack/SaaS), even if asked — pause and propose an alternative.
🔒 **Core is read-only.** Skills under `.claude/skills/` vendored from agentic-pipeline are not edited here — fix upstream in the pipeline repo and re-copy. Local skills use a distinct name.
🔒 **PR is the clean merge unit.** Never recycle a wrong PR — new PR + close the old one. Conflict = rebase on base (`integration`/`main`).
🔒 **"Keep going" ≠ inventing scope.** In autonomous mode (dispatcher/loop), only explicit requests; do not derive from old backlog/specs without per-feature confirmation.

**Shared conventions** (in agentic-pipeline): [`git-pr-workflow.md`](https://github.com/BGavazzi/agentic-pipeline/blob/main/.docs/conventions/git-pr-workflow.md) · [`engineering-defaults.md`](https://github.com/BGavazzi/agentic-pipeline/blob/main/.docs/conventions/engineering-defaults.md) · [`agent-conduct.md`](https://github.com/BGavazzi/agentic-pipeline/blob/main/.docs/conventions/agent-conduct.md)

---

## §3 Task Closure Law

Before marking a task `done`, all of these must be updated (`validate_closure.py` checks):

| # | Artifact | When |
|---|---|---|
| 1 | `CHANGELOG.md` | Always |
| 2 | `<function_catalog>` | Signature change |
| 3 | `<sdd_kit_path>` | New Dxx decision |
| 4 | `README.md` | User-visible change |
| 5 | `.agents/continuity-<agent>.md` | Always |
| 6 | Tests passing | Always |
| 7 | `<route_map>` | Route/handler/model changed |
| 8 | **PR approved** | Task that produces code |

`[N/A]` with a 1-line justification if not applicable.
🔒 **Task only closes with an approved PR** — a task with code only becomes `done`/moves to `completed/` with an approved PR; an open PR is not enough (stays `in_progress` in review until human approval). The dispatcher does NOT close the task when opening the PR.

---

## §4 Tasks

### 4.1 Naming (shared convention)
`<task_dir>/NNNN-type-slug.md` — `NNNN` 4 digits; `type`: feat/fix/refactor/docs/chore/audit/proposal/infra/test.
`validate_task.py` validates the frontmatter (F1–F12).

### 4.2 Minimum frontmatter
```yaml
---
status: todo | in_progress | done
priority: P0 | P1 | P2
type: feat | fix | ...
created: YYYY-MM-DD
updated: YYYY-MM-DD
clickup_id: <id|null>
parent: null
blocks: []
blocked_by: []
---
```

### 4.3 State
- Open: `<task_dir>/NNNN-...md` · Completed: `<task_dir>/completed/NNNN-...md` (move on close) · Planning: `<task_dir>/planning/`

### 4.4 Skills inherited from core

| Skill | Purpose |
|---|---|
| `grill-me` | Interview the task author until the spec is actionable |
| `codebase-grounding` | Map the repo before touching anything |
| `builder` | Execute a task in code |
| `tester` | Validate §Exit Conditions (prototype mode) |
| `librarian` | Closure Law §3 |
| `notifier` | Post summary to ClickUp + GitHub |
| `dispatcher` | Orchestrate the `<task_dir>` queue (quota-aware; interactive sessions only) |
| `codebase-audit` | Read-only repo health checks |

---

## §5 Style

ClickUp comments: caveman/terse, TL;DR above 200 chars.
No `<org-scripts-repo>` with a more detailed convention exists yet — this line
is the whole rule until one is written.
"""


def find_repo_root() -> Path:
    """This script lives at <agentic-pipeline>/scripts/core_sync.py."""
    return Path(__file__).resolve().parent.parent


def sync_skills(source: Path, target: Path, allowlist: set[str] | None, dry_run: bool) -> list[str]:
    src_skills = source / ".claude" / "skills"
    dst_skills = target / ".claude" / "skills"
    synced = []
    if not src_skills.is_dir():
        return synced
    for skill_dir in sorted(p for p in src_skills.iterdir() if p.is_dir()):
        name = skill_dir.name
        if allowlist is not None and name not in allowlist:
            continue
        dst = dst_skills / name
        if not dry_run:
            dst_skills.mkdir(parents=True, exist_ok=True)
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(skill_dir, dst, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "state"))
        synced.append(f".claude/skills/{name}/")
    return synced


def sync_gate_scripts(source: Path, target: Path, dry_run: bool) -> list[str]:
    src_scripts = source / "scripts"
    dst_scripts = target / "scripts"
    synced = []
    for filename in GATE_SCRIPTS:
        src = src_scripts / filename
        if not src.is_file():
            continue
        if not dry_run:
            dst_scripts.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst_scripts / filename)
        synced.append(f"scripts/{filename}")
    return synced


def sync_conventions(source: Path, target: Path, dry_run: bool) -> list[str]:
    src_conv = source / ".docs" / "conventions"
    dst_conv = target / ".docs" / "conventions"
    synced = []
    if not src_conv.is_dir():
        return synced
    for f in sorted(src_conv.glob("*.md")):
        if not dry_run:
            dst_conv.mkdir(parents=True, exist_ok=True)
            shutil.copy2(f, dst_conv / f.name)
        synced.append(f".docs/conventions/{f.name}")
    return synced


def seed_agents_md(target: Path, dry_run: bool) -> str | None:
    dst = target / "AGENTS.md"
    if dst.exists():
        return None  # never overwrite — repo-specific, per its own header
    if not dry_run:
        dst.write_text(AGENTS_MD_TEMPLATE, encoding="utf-8")
    return "AGENTS.md (created from template — fill in the <placeholders>)"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("target", help="Path to the repo to vendor the core into")
    parser.add_argument("--dry-run", action="store_true", help="Print what would be synced without writing anything")
    parser.add_argument(
        "--skills", default=None,
        help="Comma-separated allowlist of skill names to sync (default: all skills)",
    )
    args = parser.parse_args()

    target = Path(args.target).resolve()
    if not target.is_dir():
        print(f"ERROR: target {target} is not a directory", file=sys.stderr)
        return 2

    source = find_repo_root()
    if source == target:
        print("ERROR: target is this repo itself — nothing to sync", file=sys.stderr)
        return 2
    if not (source / ".claude" / "skills").is_dir() or not (source / "scripts").is_dir():
        print(f"ERROR: {source} doesn't look like the agentic-pipeline source tree "
              f"(missing .claude/skills/ or scripts/)", file=sys.stderr)
        return 2

    allowlist = set(args.skills.split(",")) if args.skills else None

    skills = sync_skills(source, target, allowlist, args.dry_run)
    scripts = sync_gate_scripts(source, target, args.dry_run)
    conventions = sync_conventions(source, target, args.dry_run)
    agents_md = seed_agents_md(target, args.dry_run)

    prefix = "[dry-run] would sync" if args.dry_run else "core_sync: synced"
    print(f"{prefix} into {target}")
    print(f"  skills:      {len(skills)}")
    for s in skills:
        print(f"    {s}")
    print(f"  gate scripts: {len(scripts)}")
    for s in scripts:
        print(f"    {s}")
    print(f"  conventions:  {len(conventions)}")
    for s in conventions:
        print(f"    {s}")
    if agents_md:
        verb = "would create" if args.dry_run else "created"
        print(f"  AGENTS.md: {verb} — {agents_md}")
    else:
        print("  AGENTS.md: already exists, left untouched")

    return 0


if __name__ == "__main__":
    sys.exit(main())
