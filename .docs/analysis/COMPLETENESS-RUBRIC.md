# Completeness Rubric v1 — agentic-pipeline conformance

Scoring rubric used to benchmark every repo in the org against the doctrine in
`agentic-pipeline` (`AGENTS.balanced.md` §0–§5) and `guidelines_IA` (archived).

Each repo is scored on 12 criteria. Each criterion: **2 = full**, **1 = partial**, **0 = absent**.
Max score = 24. Report both raw score and percentage.

| # | Criterion | 2 (full) | 1 (partial) | 0 (absent) |
|---|---|---|---|---|
| C1 | **AGENTS.md present** | Exists at repo root, placeholders filled, references agentic-pipeline as core | Exists but templated placeholders left (`<project_name>`) or no core reference | No AGENTS.md |
| C2 | **CLAUDE.md / harness config** | `.claude/` with settings + skills or a CLAUDE.md that matches actual stack | One present but thin/stale | Neither |
| C3 | **Continuity file** | `.agents/continuity-<agent>.md` exists and updated within 60d of last commit | Exists but stale (>60d behind HEAD) | Missing |
| C4 | **Task dir + schema** | `.docs/tasks/` with `NNNN-type-slug.md` files that pass `validate_task.py` | Task dir exists but naming/frontmatter non-conformant | No task dir |
| C5 | **CHANGELOG.md** | Exists, entries reach the latest commit | Exists but stale | Missing |
| C6 | **README.md** | Explains what/why/how-to-run, current | Exists but stub or stale | Missing |
| C7 | **Test suite** | Tests exist AND pass when run | Tests exist but fail / are trivial / cannot run | No tests |
| C8 | **CI workflow** | `.github/workflows/` runs tests on PR | Workflow exists but does not run tests, or is disabled | No CI |
| C9 | **Gates wired** | Runs pipeline gates (`validate_task`, `validate_closure`, `scan_gate`, `blast_radius`) in CI or pre-commit | Gate scripts vendored/present but not enforced | No gates |
| C10 | **Secret hygiene** | `.env` gitignored, no plaintext credentials in tracked files | `.gitignore` covers env but suspicious strings present | Secrets in tracked files |
| C11 | **PR workflow** | History shows merges via PR, not direct-to-default commits | Mixed | All commits direct to default branch |
| C12 | **Closure Law artifacts** | Completed tasks carry the §3 checklist resolved | Checklist present but unresolved | No notion of closure |

## Tiering (from `.docs/conventions/repo-tiering.md`)
Classify each repo: `canonical` | `active` | `on-hold` | `hibernating` | `deprecated`.
A `hibernating`/`deprecated` repo scoring low is NOT a finding — weight findings by tier.

## Worktree handling (IMPORTANT)
Many directories are **git worktrees** of a parent repo, not distinct repos.
- Run `git rev-parse --git-common-dir` in each dir. If it points outside the dir, it is a worktree/linked checkout.
- Run `git worktree list` to enumerate siblings.
- Group all worktrees under their canonical repo (identified by `git remote get-url origin`).
- Score the **canonical repo once**, evaluating the checkout with the newest commit (`git log -1 --format=%cI` across worktrees), and list the worktrees as satellites.
- Never report the same repo N times because it has N worktrees.
