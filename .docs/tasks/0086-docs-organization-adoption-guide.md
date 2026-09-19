---
status: in_progress
priority: P1
type: docs
created: 2026-09-19
updated: 2026-09-19
clickup_id: null
parent: 0078
blocks: []
blocked_by: []
---

# 0086 — [Docs]: Organization adoption guide and project status

## Context
The repository has accumulated a broad agentic SDLC capability set, but a new
organization needs a practical order of implementation and an honest boundary
between shipped core behavior and external activation.

## Problem
The existing README is a detailed component reference, not an adoption
decision guide. Without sequencing and an explicit overkill analysis, teams may
install worker pools, visual gates or autonomous promotion before they have
basic policy ownership, receipts and rollback accountability.

## What To Do
- [x] Publish a phased organization adoption guide.
- [x] Document process, security, capacity and ownership impact.
- [x] Identify controls that are overkill early and controls that are never
  acceptable to remove.
- [x] Link the guide and current capability status from the README.
- [ ] Review the guide against one external pilot organization.

## Affected Files
- `.docs/guides/organization-adoption.md`
- `README.md`
- `.docs/tasks/0086-docs-organization-adoption-guide.md`
- `CHANGELOG.md`
- `.agents/continuity-codex.md`

## Exit Conditions
- [x] New adopters have an ordered implementation path from foundation to
  protected staging.
- [x] Decision impact and ownership are explicit.
- [x] Overkill and non-negotiable safety controls are distinguished.
- [x] Project status separates repository evidence from external activation.
- [ ] Full documentation and repository gates pass.
- [ ] PR receives independent review and approval.

## Required Documentation (Closure Law)
- [x] `CHANGELOG.md` updated
- [N/A] `<function_catalog>` — no public script signature changed.
- [N/A] `<sdd_kit_path>` — no new architectural decision was ratified.
- [x] `README.md` updated
- [x] `.agents/continuity-codex.md` updated
- [x] Tests and documentation validators passing
- [N/A] `<route_map>` — no route/handler/model changed.
- [ ] PR approved

## Honest Backlog
The guide has not yet been reviewed by an external adopting organization;
its recommendations remain grounded in this repository's current evidence and
the SOTA analysis already recorded here.
