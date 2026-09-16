---
name: debt-ledger
description: Read-only harvest of deliberate TODO/FIXME/HACK shortcuts into a traceable ledger, separating markers with a revisit task from markers with no trigger. Triggers - "debt ledger", "harvest shortcuts", or a repository housekeeping run.
tools: Bash, Read
---

# Debt Ledger

This skill is read-only. It identifies shortcuts that are intentionally left
behind and makes the dangerous class visible: a shortcut with no revisit
trigger tends to become permanent “later.” It never edits code or creates
tasks silently.

## Marker convention

Recognize `TODO`, `FIXME`, `HACK`, `XXX`, and `ponytail` markers, preferably in
the repository's documented format:

```text
# TODO(<agent>): <what was simplified> — see task <NNNN>
```

The `see task NNNN`/`task NNNN` phrase is the revisit trigger. A marker without
one is `no-trigger` and is the primary review queue.

## Output contract

Produce both a human ledger and a machine ledger in a caller-selected output
directory:

- `ledger.md`: “No trigger” entries first, then tracked entries.
- `ledger.json`: `schema_version`, totals, counts by marker kind, and entries
  with file, line, marker, text, and revisit task (if any).

Skip `.git`, dependency trees, build outputs, archives, and documentation files
unless the repository explicitly opts into them. Documentation commonly quotes
TODOs and creates false positives; the caller can run a second explicit docs
pass when needed.

## When to run

- Monthly with a repository conformance audit.
- Before closing an epic, so untracked shortcuts become explicit tasks.
- After a builder deliberately defers work under the Closure Law.

## Hard rules

- Never “fix” a marker from this read-only skill; create a scoped task for a
  builder instead.
- Do not treat tracked debt as urgent merely because it exists; prioritize
  `no-trigger` and report totals honestly.
- Never claim a clean ledger when the scan was partial or a directory was
  unreadable; include scan errors in the receipt.
