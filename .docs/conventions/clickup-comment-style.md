---
title: ClickUp comment & description style
status: applied
owner: <maintainer-email>
created: 2026-05-21
applies_to: humans and AI agents posting to ClickUp tasks
based_on: sample of 262 descriptions + 13 comments across 412 tasks (2026-05-21)
---

# ClickUp comment & description style

> **Provenance note (migrated 2026-09).** Migrated from this repo's
> predecessor (`guidelines_IA`, tombstoned). One example `@mention` and one
> internal bot-template name genericized; the sample statistics are kept as
> real-world calibration data, not identifying.

Convention for how to write comments and descriptions on ClickUp tasks. **Applies to humans and AI agents equally.** A real sample (2026-05-21) showed the team writes almost always in a terse/caveman style; the rule below doesn't ask for more verbosity — it asks for **structure when the content earns it**, and **radical brevity when it doesn't**.

## Single principle

> **Response depth should match decision depth.** "Shipping to staging" is perfect for a status update. A bug with 5 repro steps earns headers. An agent that dumps a wall of text into a coordination channel is wrong even if the content is correct.

## Practical tradeoff — caveman ↔ verbose

Inspired by the [`caveman`](https://github.com/juliusbrussee/caveman) pattern (maximum compression), adapted to the fact that ClickUp **isn't an AI log, it's human coordination**. Positions on the spectrum:

| Spectrum | When to use | Anti-pattern |
|---|---|---|
| 🪨 **Caveman** (≤ 30 chars) | obvious status update given the task title context: *"Shipped to staging"*, *"done"*, *"@teammate can you validate?"* | using it for the opening comment on a bug with no context |
| ✂️ **Terse** (30–150 chars) | direct answer to a direct question, recorded decision, point observation | trying to fit a multi-step explanation here |
| 📝 **Brief** (150–400 chars) | minimal bug report, short action plan, 2-3 step follow-up | when there are ≥ 4 items — turns to soup, should become structured instead |
| 🗂️ **Structured** (markdown headers + bullets) | feature spec, audit, ≥ 4 related points, AI proposal | single-action tasks — overkill |
| 📚 **Verbose** (> 800 chars, no structure) | **never in ClickUp** — belongs in the task description, a doc, or a wiki | wall-of-text is the worst of both worlds |

## Practical rules

### For humans

1. **Don't restate the title in the body.** Title is context; the comment picks up where the title left off.
2. **Status update = caveman.** *"Done"*, *"Shipping to staging"*, *"The bug was in the auth layer"*. Nobody's going to read 3 sentences.
3. **Bug report with ≥ 3 repro steps → becomes structured.** Use `## Repro` / `## Expected` / `## Actual`.
4. **@mention whoever needs to act**, not "someone".

### For AI agents

1. **Default: match how the human team writes.** Look at who writes in the channel and mirror the tone.
2. **Max 5 questions per comment** when interviewing (hard rule already in `grill-me`'s `SKILL.md`).
3. **TL;DR mandatory** on any comment > 200 chars. First line **bold** or prefixed `**TL;DR:** ...`.
4. **Don't narrate what you did** — show the result.
5. **Cite the task ID** when referencing another: `<86abc1234>` or a direct link.
6. **Match the team's normal language/voice.** No stiff corporate phrasing ("As requested", "Best regards").
7. **Code blocks** with triple-backtick when pasting a code snippet or stack trace. **Never paste > 30 lines of code** — link to the file on GitHub via a permalink instead.

### For descriptions (task body)

1. **A terse description is OK** if the title is descriptive enough (49% of tasks in the original sample did this and it worked).
2. **≥ 3 actions or ≥ 4 criteria** → becomes structured with headers.
3. **Canonical spec template** when the task will be processed by an agent — see `.docs/tasks/000-template.md`'s section structure in this repo.
4. **Image-only descriptions** (a design-tool attachment) are valid — title + attachment carries the information.

## Calibration from a real sample (2026-05-21)

Healthy distribution observed: **78% terse-or-brief**, 18% structured-or-verbose, the rest medium. The goal is **not to redistribute** that proportion — it's to **make sure each task lands in the right bucket** for its actual complexity.

Drift signal (escalate on any of these):
- A bug report written as caveman (*"doesn't work"* with no repro)
- A status update written as verbose (*"Per yesterday's alignment with the team..."*)
- An AI agent posting a repetitive wall of text with no TL;DR
- A description that should be `## H2` headers but is a wall of text instead

## Related

- `grill-me`'s `SKILL.md` — the 5-questions-per-turn hard rule, already applied
- `AGENTS.balanced.md` §5 — general response style (terse, no postamble, prose)
