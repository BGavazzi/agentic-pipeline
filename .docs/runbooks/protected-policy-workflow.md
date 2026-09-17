# Protected policy workflow

> Task 0043 supersedes the activation claims in the original example below.
> A reusable workflow called by candidate-owned YAML is not by itself an
> immutable required control. The active CI integration now consumes a separately
> dispatched metadata-only producer, verified through GitHub's API. No protection
> settings or approved policy pin were installed by this implementation.

`policy_integrity.py` detects changes to the workflow and gate surface, but a
workflow stored in the candidate repository cannot be its own final trust
anchor. A consuming repository should call
`.github/workflows/policy-gate-reusable.yml` from a protected, immutable commit
of `BGavazzi/agentic-pipeline`.

Example caller job:

```yaml
jobs:
  protected-policy:
    if: github.event_name == 'pull_request'
    uses: BGavazzi/agentic-pipeline/.github/workflows/policy-gate-reusable.yml@<IMMUTABLE_CORE_SHA>
    with:
      core_ref: <IMMUTABLE_CORE_SHA>
      base_sha: ${{ github.event.pull_request.base.sha }}
      head_sha: ${{ github.event.pull_request.head.sha }}
      task_id: policy
```

Pin both the workflow reference and `core_ref` to the same reviewed full commit
SHA. Require the resulting `Protected policy integrity` check in branch
protection. Fork PRs can use the GitHub-hosted runner because the job only reads
the candidate tree and emits an artifact; no secrets are needed.

This is a reusable producer interface, not proof that its caller is protected.
The candidate-local receipt remains diagnostic. Required platform ownership and
an independently protected final evaluator must be verified before promotion.

## Task 0043: controlled producer and API verifier

### What runs

1. An operator dispatches `trusted-policy.yml` with PR number and full base/head
   SHAs, from a reviewed revision whose SHA equals external `TRUSTED_POLICY_SHA`.
   The workflow uses read-only contents/pull-requests/actions permissions, checks
   out only its approved implementation, and never checks out/executes candidate
   code. The Python producer makes fixed GET calls through `gh api`.
2. The producer observes current PR files and reviews. Sensitive/policy paths or
   churn >=400 require independent exact-head authorized approval; any outstanding
   authorized changes-requested review blocks even an ordinary change. Author or
   bot approval never satisfies HITL. Permission loss/dismissal invalidates evidence.
3. `envelope.json` contains a v1 subject (repo/PR/base/head/policy SHA), subject tree,
   workflow path/ID, run ID/attempt, producer identity, payload SHA-256 and a policy
   receipt. `executed_tree` is null and execution_kind is metadata-only-policy:
   this is explicitly NOT integration execution proof.
4. CI's route checks out the externally pinned verifier, which discovers the latest
   exact-subject producer, checks GitHub run metadata and archive digest, reads only
   one bounded JSON archive member (no extraction), and compares tree/current review
   state. A newer failed, queued or rerun attempt blocks; no old-success fallback.
5. Admission diagnostics invalidate the prior observation, invoke the pinned
   verifier again and aggregate its result. Candidate policy inventory is never
   substituted. Missing pin/producer writes an explicit policy error receipt.

The envelope's payload digest covers canonical receipt JSON. The ZIP digest comes
from GitHub's artifact API and is checked over downloaded archive bytes; it cannot
be embedded inside its own artifact without circular hashing. Both are recorded.

Valid observation is not approval: CLI exit 0 can emit review_required. A producer
run being successful means it issued an observation, not that promotion is allowed.
Use the policy status and current early_review.allowed decision. Exit 2 writes
blocking error output and must never be ignored in a protected caller.

### Why explicit refresh

The early-review workflow supports metadata-only workflow_dispatch for UI refresh.
The producer is a separate controlled dispatch after approval/dismissal/base change.
There is no privileged pull_request_review workflow: review events can load a
candidate merge-ref workflow. There is also no reliance on run.pull_requests or
on a pull_request_target run head equaling the PR's base. GitHub's default-branch
event semantics differ from that assumption.

Once activation is approved, the operator workflow is:

```powershell
# Read exact current PR identities first; examples are templates, not prefilled approvals.
gh pr view <PR> --repo BGavazzi/agentic-pipeline --json baseRefOid,headRefOid
gh workflow run trusted-policy.yml --repo BGavazzi/agentic-pipeline --ref <APPROVED_REF> -f pr_number=<PR> -f base_sha=<BASE_SHA> -f head_sha=<HEAD_SHA>
# Wait for that exact producer, inspect its decision, then rerun the candidate CI.
# Optional metadata summary refresh (does not grant policy approval):
gh workflow run early-review.yml --repo BGavazzi/agentic-pipeline --ref master -f pr_number=<PR>
```

`APPROVED_REF` must resolve to TRUSTED_POLICY_SHA. A later default-branch commit
does not automatically inherit the pin; dispatching it is rejected. Choose a
maintainer-owned immutable release ref and pin-rotation policy, or explicitly
reapprove each producer-source revision. No tag/branch or variable is created here.
Run discovery is bounded (31 pages); old evidence outside the bound requires a
fresh controlled dispatch. A final consumer must verify again before side effects;
there is no atomic transaction spanning GitHub approval and a later deployment.

### Activation proposal and pilot acceptance

1. Review/land this code; choose and independently approve an immutable producer
   revision. Verify action/dependency sourcing and the policy pin's write controls.
2. Choose a genuinely independent authorized reviewer or a separately controlled
   approval surface. A shared agent/maintainer GitHub login cannot prove a human
   approved. Do not relax the author exclusion or synthesize a review receipt.
3. With explicit operator authorization, set TRUSTED_POLICY_SHA and establish the
   reviewed dispatch ref. Inspect effective rules/account capabilities before
   choosing mandatory enforcement. No variables/protections were changed here.
4. Pilot non-sensitive ordinary and elevated PRs: ordinary can pass without a human;
   elevated waits until an independent current-head review. Verify API ZIP size and
   digest semantics, run title/ID/attempt, exact subject and permissions in live data.
5. Force review dismissal, changes-requested, synchronize/base movement, failed
   producer, retry, permission removal and corrupted/missing artifact. Each must
   block. A new valid producer should restore progress; record run/artifact URLs.
   A read-only implementation probe of existing artifact 10478935080 from run
   35176046147 confirmed API size/digest match the downloaded ZIP. This verifies
   the archive convention only, not the new producer's live lifecycle.
6. Demonstrate an attacker cannot change the final evaluator/pin, remove the required
   workflow, forge its check identity or substitute a candidate artifact. Until
   independently enforced controls make those tests fail, call CI diagnostic only.
7. Rollback: stop dispatches and remove/disable the approved pin under operator
   control; the consumer must report error, not fall back to local policy approval.
   Never roll back by accepting fabricated success or weakening missing gates.

### Scope and remaining limits

This path authenticates one policy producer through trusted GitHub API metadata,
not through self-described provenance fields. A consumer executing changed code
can still lie about its result; candidate CI is NOT final enforcement. The other
test/scanner/integration/meta-test/reviewer producers are not authenticated here.
Their protected issuer and final admission wiring remain explicit follow-up work.

Existing `policy-gate-reusable.yml` remains available for consumers but is not the
receipt source in this repo's new path. Do not configure two contradictory required
policy sources or assume old bare JSON receipts satisfy the new envelope contract.
The verifier requires `gh`, Python and read-only API access. Tokens are handled by
the runtime/gh; no credential material is written to reports or error output.

### Primary references checked during implementation

- [GitHub event semantics](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows)
- [Default-branch pull_request_target change](https://github.blog/changelog/2025-11-07-actions-pull_request_target-and-environment-branch-protections-changes/)
- [Workflow run API](https://docs.github.com/en/rest/actions/workflow-runs)
- [Artifact metadata/digest API](https://docs.github.com/en/rest/actions/artifacts)
