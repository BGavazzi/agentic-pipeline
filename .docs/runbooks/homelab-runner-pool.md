# Runbook — ephemeral homelab worker pool

> **Quarantined as of task 0042.** CI currently routes all candidate jobs to
> GitHub-hosted runners, even when USE_HOMELAB_POOL is true. The activation
> checklist below is necessary but not evidence it has been completed. See
> [review remediation](review-remediation.md) for the new trusted host contracts.

This runbook covers trusted CI workers for `agentic-pipeline`. It does not
contain credentials and must not be used to expose `sao-bernardino-brain`, the
Evolution/WhatsApp credentials, or any other confidential local-only data.

## Trust matrix

| Event | Worker | Secrets | Policy |
|---|---|---|---|
| Fork `pull_request` | GitHub-hosted | none | Never route to homelab |
| Same-repo `pull_request` | Homelab only when pool is healthy and enabled | none by default | Candidate code is untrusted until gates pass; isolate worker |
| Push to protected branch | Protected worker/environment | least privilege | Separate deployment policy; never share the PR worker workspace |
| Manual reviewer run | Ephemeral reviewer worker | reviewer credential only | Credential mounted just for the process; revoke on failure |

The workflow's `route` job already pins fork PRs to `ubuntu-latest` and only
selects `[self-hosted, linux, x64, homelab-pool]` when
`USE_HOMELAB_POOL=true`. Do not weaken that branch guard to make the queue move
faster.

## Pool model and current topology

`BGavazzi` is a GitHub User account, not an Organization, so native
organization-wide runner groups are unavailable. The pool is emulated with a
uniform `homelab-pool` label and per-repository registration. Moving these
repositories into an Organization would be the long-term way to share one
runner group.

The last observed homelab layout had persistent runners at:

| Install | Repository | Existing labels |
|---|---|---|
| `~/actions-runner` | `homelab-demo-app` | `self-hosted,Linux,X64,homelab` |
| `~/actions-runner-clawdinha` | `clawdinha-do-rh` | `self-hosted,Linux,X64,homeserver,clawdinha` |
| `~/actions-runner-pr-dashboard` | `pr-dashboard` | `self-hosted,Linux,X64,pr-dashboard` |

`agentic-pipeline` had no registered runner at the time of the original audit.
The host was `bernardo@192.168.1.249` with Docker available; verify current
capacity before changing that state because the box also hosts clawdinha,
Evolution/WhatsApp, feirinha, and other workloads.

The pool is useful because `scan_gate.py` runs Semgrep, Trivy, and Gitleaks in
Docker. A machine without a reachable daemon must fail closed; the homelab can
execute the scanners and the clean-room integration gate. This benefit never
overrides the isolation requirements above.

Self-hosted admission also requires the host facts to include
`network_policy_verified: true`. This means the trusted host adapter checked the
worker's egress policy; Docker reachability alone is not proof of isolation.

## Registration outline for the current GitHub User setup

For each repository that genuinely needs the pool, mint a repository-scoped
registration token and register a separate **ephemeral** worker. The old
persistent two-worker recipe is retained here only as migration context; do
not use it for public PR validation.

```bash
# Operator machine; token is short-lived and must not enter shell history.
gh api -X POST repos/BGavazzi/agentic-pipeline/actions/runners/registration-token --jq .token

# On the disposable host, configure one worker per directory. Prefer the
# runner's --ephemeral/JIT mode and a disposable work volume.
D=$HOME/runner-pool/w1
mkdir -p "$D" && cd "$D"
./config.sh --unattended --replace \
  --url https://github.com/BGavazzi/agentic-pipeline \
  --token "$TOKEN" \
  --name debian249-pool-w1 \
  --labels homelab-pool,homelab \
  --work _work \
  --ephemeral
./run.sh
```

If the installed runner package rejects `--ephemeral`, stop and upgrade the
runner or use a disposable runner image. Do not fall back to a persistent
service merely to clear the queue. Existing runners can be inspected with:

```bash
gh api repos/BGavazzi/<repo>/actions/runners
```

Adding `homelab-pool` to an existing persistent runner is migration-only and
does not satisfy this task's public-PR acceptance condition.

## Required worker lifecycle

Each worker must be single-use:

1. Mint a short-lived repository registration/JIT token from a credentialed
   operator machine; never commit or paste it into a task, log, or `.env` file.
2. Register one worker with labels `homelab-pool,homelab` and an isolated work
   directory. Prefer GitHub's ephemeral/JIT mode; if the chosen runner image
   cannot provide it, do not enable the pool for public PR validation.
3. Run exactly one job. Do not mount host home directories, Docker sockets,
   Evolution/WhatsApp data, SSH keys, or application databases into the job.
4. On completion or failure, deregister the worker, destroy the workspace and
   container/VM, and rotate any credential used by the worker. A crashed or
   unreachable worker is revoked before replacement.
5. Record only operational metrics, never source contents or secret values.

### Supervisor contract

The host-side wrapper can enforce the lifecycle around the runner process with
the canonical supervisor:

```bash
python scripts/worker_supervisor.py \
  --facts "$RUNNER_TEMP/homelab-worker-facts.json" \
  --post-facts "$RUNNER_TEMP/homelab-worker-post-facts.json" \
  --require-docker \
  --output .docs/worker-reports/lifecycle.json \
  --cleanup-command /opt/pipeline/trusted-host-teardown \
  --command ./run.sh
```

The pre-run facts must describe an eligible ephemeral worker with zero prior
jobs, a clean workspace, zero mounted secrets, verified network policy, and
(when required) reachable Docker. The runner command is an argv-only process; the supervisor does not
mint tokens or register the worker. After any exit (including failure/timeout),
the separate trusted host teardown adapter must return fresh JSON on stdout
with the supervisor-provided `PIPELINE_CLEANUP_ATTEMPT` as `attempt_id` and
facts proving `jobs_completed: 1`, `workspace_clean: true`,
`mounted_secret_count: 0`, and `registered: false`. Any missing or contradictory
fact produces a non-pass `worker-lifecycle` receipt and the pool remains
ineligible. `/opt/pipeline/trusted-host-teardown` is an operator-provided adapter,
not a bundled executable. The candidate must not share its filesystem or
credentials. Candidate-written post-facts files are no longer accepted.

## Machine-checkable preflight

Before checkout or any candidate-controlled command, the worker wrapper should
run the canonical `scripts/worker_preflight.py` and stop on exit code `1` or
`2`. A self-hosted worker is accepted only when it has the `homelab-pool`
label, is ephemeral, has completed zero prior jobs, has verified cleanup, and
has zero mounted secrets. Fork PRs are always rejected on self-hosted workers.

Example receipt command on a disposable worker:

```bash
python scripts/worker_preflight.py \
  --facts "$RUNNER_TEMP/homelab-worker-facts.json" \
  --require-docker \
  --output .docs/worker-reports/preflight.json
```

For CI, the supervisor must write the same facts as JSON to
`$RUNNER_TEMP/homelab-worker-facts.json` before the job starts, with keys
`worker_kind`, `labels`, `ephemeral`, `jobs_completed`, `workspace_clean`,
`mounted_secret_count`, and `docker_reachable`. The workflow refuses to run a
self-hosted lane when that file is absent.

The current supervisor schema additionally requires a boolean `fork_pr` from
the trusted event dispatcher; omitting event trust is not equivalent to a
trusted event. A true value always prohibits a self-hosted worker.

The receipt records `worker_age_jobs`, `mounted_secret_count`, cleanup,
Docker reachability, and fork-to-pool routing metrics. It is an operational
acceptance artifact, not proof that a compromised host is safe; the stronger
boundary remains a disposable VM/container with no host application secrets.

## Preflight before enabling `USE_HOMELAB_POOL`

- [ ] Fork PR routing verified on a no-op workflow: runner is GitHub-hosted.
- [ ] Worker is ephemeral/JIT or the pool remains disabled.
- [ ] Runner service account cannot read the host's confidential application
      directories or Docker socket beyond the worker sandbox.
- [ ] Workspace is on a disposable volume with sufficient free space.
- [ ] Outbound network policy allows only required GitHub registries/services;
      inbound access is disabled.
- [ ] At least two workers are available so one failure cannot strand the queue;
      capacity is checked against the clawdinha/Evolution workload.
- [ ] A clean-room integration job and scanner job complete once, with their
      artifacts uploaded and exact base/head SHAs matching.
- [ ] A failed worker leaves no registered stale runner and no mounted secret.

## Pool metrics and acceptance thresholds

Record these as job annotations or a private operational log:

| Metric | Acceptance target |
|---|---|
| `queue_wait_seconds` | p95 < 120s during normal load |
| `worker_age_jobs` | exactly 1 for ephemeral workers |
| `workspace_cleanup` | 100% success; any failure disables the pool |
| `mounted_secret_count` | 0 for ordinary gates; 1 narrowly scoped reviewer credential at most |
| `fork_pr_pool_routes` | 0 |
| `stale_registered_workers` | 0 after each job/revocation sweep |
| `scanner_receipt_sha_match` | 100% exact base/head matches |

## Registration outline

The commands below are intentionally manual and use a short-lived token. Run
them only on the homelab after the preflight is checked:

```bash
gh api -X POST repos/BGavazzi/agentic-pipeline/actions/runners/registration-token --jq .token
# On the disposable worker host: configure one runner with --ephemeral,
# --labels homelab-pool,homelab, and an isolated --work directory.
# Start it once, observe one trusted same-repo job, then verify deregistration.
gh api repos/BGavazzi/agentic-pipeline/actions/runners
```

Do not store the token in shell history. If the runner package cannot support
ephemeral mode, stop here and keep `USE_HOMELAB_POOL` unset/false.

## Incident response

If a worker runs a fork PR, exposes a secret, fails cleanup, or becomes
unreachable: disable `USE_HOMELAB_POOL`, revoke the runner, rotate affected
credentials, preserve only safe operational logs, and inspect the host before
re-enabling. Do not upload confidential repository content as an incident
artifact.
