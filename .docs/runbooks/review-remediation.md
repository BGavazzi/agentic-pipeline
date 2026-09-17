# Reviewed harness remediation — task 0042

## Trust model and release status

This patch repairs the code defects found in the review of PRs #14–#44. It
does **not** claim that an unmerged workflow or a local test makes GitHub or
the homelab secure. Candidate-controlled scripts provide diagnostics; the
final required policy must run from protected ownership outside that candidate.

The corrective branch includes the reviewed stack and its regression fixes.
Do not merge an older uncorrected PR independently. Retain the original PRs as
history until the corrective merge unit is accepted.

## Findings to implementation

| Finding | Repair |
|---|---|
| F1 scanner veto | Aggregate block/error/unknown verdicts veto scanner receipts; scan and unit evidence require exact identities. |
| F2 execution identity | Integration archives the merge tree of actual base/head commits; reviewer and infra archive the named candidate. Unknown commits fail before launch. |
| F3 worker trust | Required typed facts; fresh supervisor nonce; teardown callback runs even after worker failure/timeout; no candidate-written post-facts input. Pool routing is quarantined. |
| F4 staging | Match local origin and GitHub remote head/base; match duplicate PR base; create draft only and revalidate after creation. A race never marks a PR ready. |
| F5 credentials | Candidate jobs have no PR-write grant. A separate default-branch workflow publishes links without checkout or candidate execution. |
| F6 meta-test | Read actual task/checklists and committed/staged/unstaged/untracked/ignored files. Host observer supplies tests/trajectory; unavailable observations block. Candidate skills and fixture digests are recorded. |
| F7 policy | Protect all scripts/workflows/skills, including new files. Enforce externally approved full-SHA pin; protected workflow obtains exact-head independent review directly from GitHub. |
| F8 visual | Verify screenshot/baseline files within an artifact root, hashes, protected threshold and consistent nonempty pixel measurements. |
| F9 test impact | Materialize the named candidate; include deletions, package aliases and conservative dynamic/parse-error fallbacks. |
| F10 promotion | Compare executed selection, nested identities, benchmark version, selector digest and fixture corpus digest. |
| F11 intelligence | Reuse admission evaluation, preserve extra failures and reject stale optional evidence. Trusted metadata review precedes integration. |
| F12 provenance | Describe manifest-verified files actually present in the target, not every source skill. |
| F13 dashboard | Quarantine invalid records; deduplicate candidate pairs; quarantine conflicting duplicates; expose metric denominators and no automatic statistical-confidence threshold. |
| F14 journal | Serialize insert-or-verify with BEGIN IMMEDIATE; reject incompatible schema and conflicting metadata; normalize timezone-aware timestamps. |

## Compatibility changes

- The file historically called `unit.exit` now contains JSON:
  `{"schema_version":1,"base_sha":"<full SHA>","head_sha":"<full SHA>","exit_code":0}`.
  A bare `0` is no longer evidence. Old receipts must be regenerated, not relabeled.
- Integration emits `integration_mode: base-head-merge` and `executed_tree`.
  Staging requires this evidence and `--repository owner/name`.
- `visual_receipt.py` requires `--artifact-root DIR --threshold NUMBER` from
  trusted configuration. Screenshot and baseline objects need `path` and
  `sha256`. Counts and ratios must agree. The adapter still does not run a browser.
- `worker_supervisor.py` requires `--cleanup-command /trusted/host-adapter`
  before `--command ...`. The callback returns JSON on stdout with the exact
  `PIPELINE_CLEANUP_ATTEMPT` it receives, plus `jobs_completed: 1`,
  `workspace_clean: true`, `mounted_secret_count: 0`, and `registered: false`.
  `--post-facts` is now a supervisor-written output, never candidate input.
- `meta_test_dispatch.py` accepts `--source-repo`, `--cleanup-command`, and
  `--observer-command`. The source repo must be at the candidate commit with
  clean skill files. The protected observer reads its own runtime audit trace
  and runs verification, returning `tests_passed` and `tool_calls`. It must
  not repeat the candidate's JSON claims. Missing observation fails fixtures
  that require it. Test stubs exercise the interface, not operational isolation.
- TIA benchmark revision is `0.3`, with selector/corpus SHA-256 fields.
- Staging creation returns `draft_created`; humans still review the exact PR
  identity. A branch can move later, so all protections must rerun on synchronize.
- Staging `--intelligence-file` now accepts versioned JSON for the exact pair,
  not arbitrary Markdown. Dry-run output includes rendered body text and labels
  its ephemeral command as a preview, not an executable saved command.

## Platform activation — mandatory, not completed by this patch

1. Review and land trusted workflows on the protected default branch using an
   explicit maintainer bootstrap. Do not bypass existing protection rules to
   bootstrap; this repository was observed to have no master protection.
2. Set repository variable `TRUSTED_POLICY_SHA` to the reviewed immutable core
   commit. Pin the caller's reusable-workflow reference to that same commit.
   Require the protected workflow using repository/organization controls that
   cannot be weakened by candidate workflow edits. A same-named candidate check
   alone is not an immutable trust anchor.
3. Require the trusted policy, early review and functional checks; prevent
   unreviewed changes to the workflows and scripts. Do not give agents a
   protection-bypass credential. A maintainer must verify the effective rules.
4. `early-review.yml` uses `pull_request_target` only for GitHub metadata API
   calls: **no checkout, imports, shell execution, or candidate artifacts**.
   Elevated changes require an independent authorized human's exact-head
   approval. Rerun the trusted check after approval, then CI. The CI route holds
   integration/shadow until that workflow succeeded for the exact base/head.
   Unit/scanner diagnostics remain available without waiting on approval.
5. `pr-summary.yml` runs from the default branch on CI completion. It posts a
   SHA-checked link to risk/contact/gate evidence; it never executes downloaded
   content. Do not restore a write token to the candidate admission job.
6. Demonstrate a disposable worker with OS/VM separation, externally owned
   facts/observer/teardown, bounded network access and no host application
   credentials. Verify cleanup after failure/timeout, not just success. Only
   then propose re-enabling pool routing. USE_HOMELAB_POOL alone cannot enable it.

No signatures are invented here: receipt validators establish consistency;
trusted provenance comes from protected execution and platform controls. The
same user credential shared by a human and an agent cannot distinguish them.
An independent reviewer identity or independently controlled approval surface
is necessary for a genuine human gate.

## Verification

Run `python -m pytest tests -q`. Run live scanner contracts explicitly with
`PIPELINE_LIVE_SCANNERS=1 python -m pytest tests/test_live_scanners.py -q`.
The tests use synthetic fixtures only. Then commit and run integration against
the exact commit and current base; uncommitted changes are never execution proof.

Keep admission blocked when protected review, worker, visual or independent
review evidence is missing. A red safety gate is not permission to fabricate
a pass or weaken the threshold.
