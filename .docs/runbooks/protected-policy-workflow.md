# Protected policy workflow

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

Agentic-pipeline's default-branch caller is
`.github/workflows/protected-policy.yml`. It uses `pull_request_target`, pins
both the reusable workflow reference and `core_ref` to the same full SHA, and
passes the exact PR base/head SHAs. It intentionally has no checkout, shell
step, secrets, or candidate execution. The caller must remain on the default
branch, and branch protection must require `Protected policy integrity`.

Pin both the workflow reference and `core_ref` to the same reviewed full commit
SHA. Require the resulting `Protected policy integrity` check in branch
protection. Fork PRs can use the GitHub-hosted runner because the job only reads
the candidate tree and emits an artifact; no secrets are needed.

This is the final trust-boundary layer above the candidate-local workflow. The
candidate-local receipt remains useful for diagnostics, but branch protection
must require this protected job before automatic admission.
