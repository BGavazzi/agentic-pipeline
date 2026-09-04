# Convention — scope intake

> **Provenance note (migrated 2026-09).** Migrated from this repo's
> predecessor (`guidelines_IA`, tombstoned). The original cited a real
> incident with named people and org-specific roles — removed; the
> principle (§1-3 below) survives intact without them.

How a request becomes work. Exists to stop the drift between what's expected (often oral/fragmented, near-tribal) and what actually gets executed. Ties into the "keep going ≠ inventing scope" hard rule (`agent-conduct.md`).

---

## 1. Every request becomes a card BEFORE it becomes a branch

Nothing starts getting implemented without a trackable task. The card is the contract: no card, nothing to validate or track against. Applies to humans **and** agents equally.

- Request came in via chat/conversation? → the card first, then the branch.
- The card is the unit that maps 1:1 to a PR (`git-pr-workflow.md` §1).

## 2. A request that arrives off-board escalates to the PO first

A request that arrives **outside the board** (e.g. directly from a stakeholder) **doesn't become a branch directly**. Escalate to the PO/product decision-maker, who prioritizes it, turns it into a card, and slots it into the flow. The PO is the gate on "does this happen now?"

**Why:** a direct request that skips the PO means invisible scope, with no validation owner, silently competing with whatever was already prioritized. Managing the stakeholder's expectation is the PO's job, not the dev's or the agent's.

## 3. An agent doesn't derive scope

In autonomous/loop mode, an agent only works what's **explicitly** in this session's card. Never derive tasks from backlog, a superseded PR, or an old spec without per-feature confirmation. Blocked or out of scope → stop and propose options. (Already an `AGENTS.md` §2 hard rule in this repo.)
