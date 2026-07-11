# Convention — Git / PR Workflow (shared convention)

Versioning and pull-request laws that apply to **all** repos. Referenced by §2 Hard Rules of constitutions.

> Origin: real production lessons (May–Jun 2026), promoted from personal memory to the constitution because these are engineering laws, not one person's preferences.

---

## 1. 🔒 Never recycle a PR

A PR is a **clean, complete, correct unit of merge**. If a PR is wrong, incomplete, or needs to be redone → **open a NEW PR** containing **everything that needs to merge**, and **close the previous wrong PR**.

**Do NOT:**
- pile up fixup commits on a broken PR trying to salvage it;
- `git merge origin/main` back into the PR branch to resolve a conflict and "save" the PR;
- reuse an open branch/PR for a different purpose than the original.

**Resolving a conflict:** rebase the branch on top of current `origin/main` (or, if already dirty, new branch rebased + new PR). **Never** `merge origin/main` into a PR branch.

**Why:** recycling a PR taints history and review, mixes the wrong with the right, and leaves the merge-unit ambiguous. A fresh PR with the complete diff is easy to review and merge; the wrong one simply closes. Trigger: a `merge origin/main` into a PR branch while trying to "resolve a conflict".

Don't confuse with **normal review iteration** (responding to a comment on a live PR is OK). The focus is a PR that is **wrong/redone** — that one doesn't get recycled.

---

## 2. Check merge status before stacking a commit

Before `git push` on a feature branch that already has a PR, **check the PR state**:

```bash
gh pr view <n> --json state,mergedAt
# or
gh pr list --head <branch> --state all
```

If **MERGED/CLOSED**: create a **new branch from current `origin/main`** and open a **new PR** — never reuse an already-merged branch.

```bash
git -c credential.helper='!gh auth git-credential' fetch origin main
git checkout -b <new> origin/main
git cherry-pick <orphaned-commits>   # if any
```

Detect orphaned commits (on branch, not in main, without PR): `git log origin/main..HEAD`.

**Why:** stacking fix after fix on an already-merged branch leaves commits orphaned — on the branch, outside main, without review. (Flagged 2026-06-01 on `feat/event-importer-iv-forum` after #1278 had merged.)

---

## 3. Branch topology and PR base

In repos **with automatic deployment** (staging fires on `push→main`, prod on tag push) the PR base is **`integration`**, not `main`:

- **`integration`** = merge branch. **Feature PRs target `integration`.** Pushing here **triggers no build** (no `pull_request` trigger or deploy on branches ≠ main).
- **`main`** = staging mirror. Every push **deploys staging**. Receives **batch merges** from `integration` (`git merge --no-ff integration` → 1 build), **not** individual PRs.
- **tags** (`*`) = prod release, **100% immediate**. Cut from `main`, or from a specific commit for isolated hotfixes.

Repos **without deployment** (docs/tooling like `<org-scripts-repo>`, libs) continue with base = **`main`** directly (not master/develop/staging).

Flow: `feat/x` (from `integration`) → PR to `integration` → local build (§6) → merge → … → batch ready → `merge integration→main` (1 staging build) → test homolog → `tag` (prod deploy).

**Why:** each merge to `main` = 1 paid staging build; individual PRs to main multiply builds **and** force main to accumulate work from multiple teams between your feature and the release → forces cherry-pick or full-release (everything on homolog goes together). `integration` batches (9 features = 1 build), keeps `main` always in a "can tag now" state, and isolates what goes to prod.

---

## 4. Approved PR closes the task (Closure Law §3, item 8)

A task that produces code **only closes** (`status: done` + move to `completed/`) when the **PR is approved** (review approved). The lifecycle:

```
task todo → in_progress → (code + PR opened) → in_progress/review → PR approved → done + completed/
                                               ^ NOT done here
```

- PR **merely opened/pushed does not close the task** — it stays `in_progress` (in review) until human approval.
- Closing the task at PR opening, or merging without approval, **violates** the Closure Law.
- Check before closing: `gh pr view <n> --json reviewDecision` → close only if `APPROVED`.
- Tasks without code (doc-only / chore without PR) close via items 1–7 of §3, without item 8.

**Implication for dispatcher** (and any autonomous loop): do NOT move the task to `completed/` when opening the PR. Leave `in_progress` and report "awaiting approval". The flip to `done` happens after a human approves (manual step or a future watcher).

**Why:** PR opened ≠ work accepted. Closing at opening marks as done something that may come back in review; it breaks tracking of "what actually landed."

---

## 5. General discipline

- **New branch from fresh `integration`** (or `main` in repos without deployment) for each unit of work — fetch first (helper `'!gh auth git-credential'` avoids AFK credential hang).
- Factual commit message; no `--no-verify` / hook bypass without explicit authorization.
- Push and merge **only when the user asks**. The agent opens the PR; the human reviews/merges on GitHub.

---

## 6. Local build before CI

Validate **locally** before pushing — it's free and catches most CI breaks (type/compile errors) without spending a runner:

- **NestJS / backend:** `npm run build` (nest build); full stack with DB: `docker compose -f docker-compose.dev.yml up`; or `npm run start:dev`.
- **Next.js / frontend:** `npm run build` (next build); view the screen: `npm run dev` (uses `.env.local`).

If `npm run build` passes locally, the CI build almost never breaks — and you can click through the screen without deploying to homolog.

**Cost of each git trigger** (hence local build + `integration` base):

| Event | Triggers | Cost |
|---|---|---|
| PR (any target) | nothing (no `pull_request` trigger) | **zero** |
| push to `integration` / any branch ≠ `main` | nothing | **zero** |
| push/merge to **`main`** | build + **staging** deploy | 1 build |
| **tag** push (`*`) | build + **prod** deploy (100% immediate) | 1 build |

**Why:** CI cost lives in push→`main` and tags, not in PRs. Batching on `integration` and validating locally cuts wasted builds and most pipeline failures.
