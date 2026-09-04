# Runbook — homelab self-hosted runner pool

Host: `bernardo@192.168.1.249` (Debian 13 trixie, 8 vCPU, 15 GiB RAM, 119 GiB free,
Docker 29.6.1). Key: `~/.ssh/wa_deploy`.

## Why a "pool" here is emulated, not native

`BGavazzi` is a GitHub **User** account, not an Organization
(`gh api users/BGavazzi --jq .type` -> `User`). Organization-level runner groups —
the native way to share one worker pool across repos — **are not available to user
accounts**. Every self-hosted runner must therefore be registered against a single
repo.

The workaround is a *uniform label*: every worker carries `homelab-pool`, and every
workflow asks for `[self-hosted, linux, x64, homelab-pool]`. Adding a repo to the
pool means registering another worker against it, but no workflow has to change.

If sharing across many repos ever becomes the bottleneck, the real fix is to create
an actual GitHub Organization and move the repos into it — then one runner group
serves all of them.

## Current state (as of 2026-09-03)

Three pre-existing runners, each a separate persistent install, each with a
bespoke label, so nothing pools today:

| Install dir | Repo | Labels |
|---|---|---|
| `~/actions-runner` | `homelab-demo-app` | `self-hosted,Linux,X64,homelab` |
| `~/actions-runner-clawdinha` | `clawdinha-do-rh` | `self-hosted,Linux,X64,homeserver,clawdinha` |
| `~/actions-runner-pr-dashboard` | `pr-dashboard` | `self-hosted,Linux,X64,pr-dashboard` |

`agentic-pipeline` has **no** runner.

## Why the pool is worth it here

`scan_gate.py` runs its four scanners (semgrep, trivy, gitleaks, dependency-check)
as Docker images. On a dev box with no Docker daemon it degrades to
`verdict=degraded (DEGRADED - no scanner ran)` — a real, observed result, not a
hypothetical. The homelab box has a live daemon, so the pool is what makes the SAST
/ SCA / secret-scan gate actually execute instead of skip.

## Step 1 — stage and register two pool workers

Mint a registration token (valid one hour) from a machine holding a GitHub
credential with `repo` scope:

```
gh api -X POST repos/BGavazzi/agentic-pipeline/actions/runners/registration-token --jq .token
```

Then on 192.168.1.249, once per worker (`i` = 1, 2), with that token in `$TOKEN`:

```
D=$HOME/runner-pool/w$i
mkdir -p $D && cd $D
tar xzf $HOME/actions-runner-pr-dashboard/actions-runner-linux-x64-2.335.1.tar.gz
./config.sh --unattended --replace \
  --url https://github.com/BGavazzi/agentic-pipeline \
  --token "$TOKEN" \
  --name debian249-pool-w$i \
  --labels homelab-pool,homelab \
  --work _work
sudo ./svc.sh install bernardo && sudo ./svc.sh start
```

Two workers is the right starting size: load average is ~1.0 on 8 cores, but the box
concurrently hosts the clawdinha stack, Evolution/WhatsApp, feirinha and
worth-calculator-br. Do not exceed 3 without re-checking free RAM (~8.4 GiB today).

## Step 2 — fold the existing runners into the pool

So they can serve pooled jobs too, add the shared label to each. Labels can be added
without re-registering; get `<id>` from
`gh api repos/BGavazzi/<repo>/actions/runners --jq '.runners[].id'`:

```
gh api -X POST repos/BGavazzi/clawdinha-do-rh/actions/runners/<id>/labels \
  -f "labels[]=homelab-pool"
```

## Step 3 — enable the pool for CI

The workflow routes to GitHub-hosted runners until this variable is set, so nothing
queues against a label with no worker behind it:

```
gh variable set USE_HOMELAB_POOL --repo BGavazzi/agentic-pipeline --body true
```

Verify with a no-op PR: the `test` and `gates` jobs should report
`Runner name: debian249-pool-w1`.

## Security posture — read before enabling on a public repo

`agentic-pipeline`, `pr-dashboard`, `worth-calculator-br`, `cv`, `baton`,
`cozy-coffee-iso` and `voxel-scale-io` are **public**. A self-hosted runner that
executes a fork PR runs attacker-controlled code on a box that also holds the
Evolution/WhatsApp credentials and the clawdinha job-application stack.

Mitigations, in order of importance:

1. **`ci.yml` pins fork PRs to GitHub-hosted runners.** This is the primary control
   and it is already in place — the `route` job checks
   `github.event.pull_request.head.repo.fork`.
2. **Keep "Require approval for all outside collaborators"** (Settings -> Actions ->
   Fork pull request workflows). Verify it is still set.
3. **Prefer ephemeral runners.** The workers above are persistent, so state leaks
   between jobs. The upgrade is `--ephemeral` (or
   `myoung34/docker-github-actions-runner` with `EPHEMERAL=1`), which needs a stored
   PAT on the box to re-register after each job — a credential-vs-isolation
   trade-off worth making before the pool serves more public repos.
4. **`pr-dashboard` is public and already has a persistent runner — checked, not
   actually at risk.** Its only workflow (`deploy-kindle.yml`) triggers on
   `push: [master]` and `workflow_dispatch` only, no `pull_request` trigger, so a
   fork PR cannot execute code on it pre-merge (verified 2026-09-04: `grep -rn
   pull_request .github/workflows/` in that repo returns nothing). An earlier draft
   of this runbook flagged it as unguarded without checking the trigger type — that
   was wrong. Re-check this if that workflow ever grows a `pull_request` trigger.
