# Convention — Repo Tiering (shared convention)

Defines the tier vocabulary a repo declares in its own `AGENTS.md` §1
(`**Tier**: <prototype | active | canonical>`), and how pipeline skills are
expected to read and act on it. Written to close a real gap: `tester`'s
`SKILL.md` has read `.docs/conventions/repo-tiering.md` to decide its mode
since it was first specified, but this file didn't exist until now — every
repo using this pipeline was silently falling back to `tester`'s conservative
default (`prototype`) regardless of its actual maturity.

---

## 1. The three tiers

| Tier | Meaning | Typical signals |
|---|---|---|
| `prototype` | Exploratory, pre-product-market-fit, or a personal/internal tool. Correctness matters less than iteration speed. No SLA, no real user data at risk if it's briefly broken. | No CI required; may have zero or partial test coverage; single maintainer; README says "WIP"/"experimental." |
| `active` | Shipping to real users, under active development. Breakage has a real cost (users notice, revenue/workflow impact) but the system is still evolving quickly and isn't expected to be perfectly stable. | Has CI; has a deploy pipeline (staging/prod); PRs get reviewed before merge; `AGENTS.md` §3 Closure Law is enforced in practice, not just on paper. |
| `canonical` | The reference/stable implementation of something — other repos or teams depend on its behavior being correct and its contracts being honored. Regressions here have the widest blast radius. | Has a documented API/contract (`SDD_KIT.md` with real `Dxx` entries, OpenAPI spec, or equivalent); changes go through a stricter review bar; breaking changes require a deprecation path. |

A repo declares its tier once, in its own `AGENTS.md` §1:

```markdown
## §1 Identity and Scope
**Tier**: active
```

There is no automatic tier detection — a repo's tier is a maintainer
decision, not something a skill infers from the code. If `AGENTS.md` §1
doesn't declare a tier at all, treat the repo as `prototype` (same
conservative-default principle as `tester`'s own fallback).

---

## 2. What tier controls today

**`tester`'s mode selection** (`.claude/skills/tester/SKILL.md` §2) is the
only pipeline skill that currently reads this file:

```
1. Read task frontmatter: `mode: prototype` → use prototype (explicit
   per-task override always wins)
2. Else read this repo's declared tier (AGENTS.md §1):
   - tier matches `^prototype` (covers "prototype" and any hyphenated
     sub-variant a repo chooses to use, e.g. "prototype-poc") → use
     prototype mode
   - tier is `active` or `canonical` → eligible for `production` mode,
     but `production` mode is V2 / not yet buildable in this pipeline
     (see tester §6) — until it exists, `active`/`canonical` repos still
     run in `prototype` mode, just without the tier-based excuse of "this
     repo doesn't need rigor"; the gap is tracked, not hidden
3. No tier declared anywhere → default to `prototype` (fail conservative,
   never assume a repo is mature enough to skip rigor)
```

In other words: today, tier mostly documents **intent** (what rigor a repo
*should eventually* get from `tester`) rather than changing behavior, since
`production` mode itself hasn't been built. That will change once
`production` mode (Docker-sandboxed DB, full regression, contract tests —
see `tester` §6/§13) ships; declaring a repo's real tier now means it's
already correctly configured when that lands, instead of every repo needing
a follow-up edit.

---

## 3. Changing tiers

Promotions (`prototype` → `active` → `canonical`) and demotions are a
one-line edit to `AGENTS.md` §1, not a task on their own — but the
*reasoning* for a promotion is worth a CHANGELOG entry if the repo has
real users depending on the distinction (e.g. "promoted to `active`:
first external user onboarded 2026-08-01"). Don't promote a repo's tier
to unlock a *behavior* you actually want today (e.g. bumping to `canonical`
just to get more scrutiny) — tier is a statement about the repo's real
stakes, not a dial for tuning gate strictness. If you want stricter
scrutiny without the tier being accurate, ask for `mode: production` at
the task level instead (once it exists) or flag it to `ultrareview` via
`blast_radius.py`'s risk classification, which is the mechanism actually
built for per-change risk today.

---

## 4. Anti-patterns

- ❌ Declaring `canonical` on day one "to be safe" — inflates review overhead for a repo that's actually still a prototype, and devalues what `canonical` means on repos where it's true.
- ❌ Leaving tier undeclared indefinitely on a repo everyone knows is `active` — `tester` has no way to know that and will keep defaulting conservative.
- ❌ Treating this file as something a skill should infer automatically (e.g. "repo has CI, so it must be active") — tier is a maintainer's explicit statement, not a heuristic output.
