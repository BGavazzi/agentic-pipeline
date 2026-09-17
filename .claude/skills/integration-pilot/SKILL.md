---
name: integration-pilot
description: Consume open PRs targeting a reversible integration branch, detect dependency groups, merge in dependency order, observe validation, and automatically revert a broken integration merge. Never promotes to production. Triggers - "/integration-pilot", "process integration PRs", or a bounded integration queue run.
tools: Bash, Read, Glob, Grep, Skill
---

# Integration Pilot

**Runtime: an interactive or explicitly supervised agent session.** The
dispatcher produces PRs; this skill consumes only PRs already open against the
reversible integration branch. It never invents work from a backlog.

## Safety boundary

- Merge and revert only on the configured `integration` branch.
- Never touch `main`, production, release tags, or deployment credentials.
- Promotion from integration to a human-review branch remains outside this
  skill.
- If the quota signal is absent or says STOP, exit cleanly and do not retry by
  bypassing the gate.
- Use worktrees for every repository; never merge from a dirty shared checkout.
- A failed integration validation requires a new revert commit. Never rewrite
  history or force-push.

## Inputs and prerequisites

Set repository identifiers through environment variables rather than encoding
them in this skill:

```bash
INTEGRATION_ANCHOR_REPO=org/frontend-repo
INTEGRATION_DEPENDENCY_REPO=org/backend-repo   # optional
INTEGRATION_BRANCH=integration
```

The repositories must have a live validation workflow triggered by pushes to
the integration branch. The validation should build, boot, and smoke-test the
candidate in an isolated workspace. A missing runner or missing quota signal
is a blocked precondition, not a reason to merge optimistically.

## Queue and dependency discovery

1. List open PRs in the anchor repository with `baseRefName` equal to the
   configured integration branch; process oldest first unless an explicit
   priority convention says otherwise.
2. Detect a dependency PR in this order:
   - an explicit repository/PR reference in the anchor PR body;
   - a shared external task identifier;
   - cross-repository `related`, `blocks`, or `blocked_by` metadata.
3. Confirm the dependency PR is open, targets the same integration branch, and
   has green required checks. A conflict or failed check skips the whole group.
4. Build the group in dependency-first order: `[dependency, anchor]` or
   `[anchor]` when no dependency exists.

## Merge → validate → revert

For each PR in the group:

1. Require `MERGEABLE` and completed green checks. Flag database migrations as
   a compatibility concern: reverting code does not revert an applied schema.
2. Merge with a normal merge commit into integration and record the merge SHA.
3. Locate the validation run for that exact SHA and wait for completion.
4. If validation fails, revert the merge immediately, push the revert, report
   the run URL and bounded diagnostics, and stop the rest of the group. The
   integration branch must return to the last known-good state.
5. If validation passes, record the factual result and continue the group.

The success result is “merged into integration with a green validation receipt,”
not “ready for production.” The failure result is “reverted and reported,” not
“leave integration red for later.”

## Loop rules

In a bounded queue loop, schedule another wake only when there is another open
anchor PR and the quota gate still says CONTINUE. Stop after an empty queue,
quota STOP, or three consecutive skipped/reverted groups so a systemic problem
reaches a human.

## Failure modes

| Condition | Action |
|---|---|
| Conflict with integration | Report rebase required; skip group |
| Pending checks | Wait; never merge on incomplete evidence |
| Failed checks | Skip; do not merge |
| Validation run missing for merge SHA | Treat as failed dispatch; revert |
| Validation red | Revert immediately; abort dependent PRs |
| Revert conflict | Stop and escalate urgently; do not guess |
| Credential or push prompt hangs | Abort on timeout; never wait interactively |
| Three consecutive failures | End loop for human triage |

## Future depth

The MVP validates build/boot/smoke. A deeper mode may add changed-surface
endpoints, affected frontend flows, visual receipts, and proposed-vs-delivered
acceptance evidence. Each additional proof must be concrete and commit-bound;
missing proof blocks acceptance rather than becoming prose.
