# Module Owners

Hand-maintained ownership map consumed by `scripts/blast_radius.py` (signal 1
of 3 — see `.docs/tasks/0002-feat-blast-radius-risk-classifier.md`). Cheap and
imprecise by design: a changed path matching a prefix below marks its owner
tag and consumer prefixes as "affected," even if no import/co-change signal
finds them. Missing entries just widen scope less — not an error.

| Path prefix | Owner tag | Consumers (path prefixes) |
|---|---|---|
| scripts/validate_task.py | pipeline-scripts | .claude/skills/dispatcher/SKILL.md, .claude/skills/librarian/SKILL.md |
| scripts/validate_closure.py | pipeline-scripts | .claude/skills/dispatcher/SKILL.md, .claude/skills/librarian/SKILL.md |
| scripts/blast_radius.py | pipeline-scripts | .claude/skills/tester/SKILL.md, .claude/skills/ultrareview/SKILL.md, .claude/skills/dispatcher/SKILL.md |
| scripts/quota_gate.py | pipeline-scripts | .claude/skills/dispatcher/SKILL.md |
| .claude/skills/dispatcher/SKILL.md | pipeline-skills | README.md, AGENTS.md |
| .docs/conventions/ | shared-conventions | AGENTS.md, .claude/skills/ |

Update this file when a script/skill gains a new consumer — it's a heuristic,
not ground truth, so staleness degrades signal quality rather than breaking
anything.
