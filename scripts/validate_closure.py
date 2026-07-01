#!/usr/bin/env python3
"""
validate_closure.py — Lei de Fechamento §3 compliance check for task .md files

Purpose: gate before the Librarian skill (or human) marks a task `done`. Catches
the "0/7 items, demais [N/A]" rubber-stamp anti-pattern — every artefato in Lei
de Fechamento §3 must be EITHER:
    - [x]      checked
    - [N/A]    with same-line justification (e.g. "[N/A] — repo has no CHANGELOG")
    - [ ]      with same-line justification OR mentioned in §Pendências Honestas

Usage:
    python scripts/validate_closure.py <task_path>
    python scripts/validate_closure.py .docs/tasks/0021-*.md

Exit codes:
    0  -- task passes Lei de Fechamento §3 check
    1  -- task has at least one unresolved/unjustified item
    2  -- usage error or task missing the closure section entirely

Canonical 7 items (AGENTS.balanced.md §3):
    1. CHANGELOG.md (or CHANGELOG_BRANCH.md per-branch variant)
    2. function-catalog.md
    3. SDD_KIT.md
    4. README.md
    5. .agents/continuity-<agent>.md
    6. Testes passando
    7. ROUTE_BEHAVIOR_MAP.md (omit if no HTTP routes in repo)

Section search (case-insensitive; first match wins):
    - ## Lei de Fechamento §3
    - ## Lei de Fechamento
    - ## Documentação Obrigatória (Lei de Fechamento)
    - ## Documentação Obrigatória

Part\ of\ the\ guidelines_IA\ pipeline (Fase 2 F2-2 sibling of validate_task.py).
"""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

# Force UTF-8 on stdout (Windows cp1252 chokes on §/—/accented chars in messages)
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML required. Install with: pip install pyyaml", file=sys.stderr)
    sys.exit(2)


FRONTMATTER_PATTERN = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
SECTION_PATTERN_TMPL = r"^##\s+{title}\s*$"

CLOSURE_SECTION_TITLES = [
    "Lei de Fechamento §3",
    "Lei de Fechamento",
    "Documentação Obrigatória (Lei de Fechamento)",
    "Documentação Obrigatória",
]

# Each canonical item: (display_name, list of regex aliases to match in text)
CANONICAL_ITEMS = [
    ("CHANGELOG", [r"changelog(?:_branch)?(?:\.md)?"]),
    ("function-catalog", [r"function[-_]catalog(?:\.md)?"]),
    ("SDD_KIT", [r"sdd[-_]kit(?:\.md)?"]),
    ("README", [r"readme(?:\.md)?"]),
    ("continuity", [r"continuity(?:[-_]\w+)?(?:\.md)?", r"\.agents/continuity"]),
    ("tests", [r"\btestes?\b", r"\btests? passing\b", r"\bunit\b", r"\be2e\b"]),
    ("ROUTE_BEHAVIOR_MAP", [r"route[-_]behavior[-_]map(?:\.md)?", r"\broute[-_]map\b"]),
]


@dataclass
class ClosureReport:
    task_path: Path
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    items_seen: dict[str, str] = field(default_factory=dict)  # name -> state symbol

    @property
    def passed(self) -> bool:
        return not self.errors

    def emit(self, exit_on_fail: bool = True) -> int:
        rel = self.task_path.name
        if self.passed:
            print(f"PASS  {rel}  ({len(self.items_seen)}/7 items resolved)")
            for w in self.warnings:
                print(f"  WARN: {w}")
            return 0
        print(f"FAIL  {rel}")
        for name, state in self.items_seen.items():
            print(f"  {state} {name}")
        for e in self.errors:
            print(f"  ERROR: {e}")
        for w in self.warnings:
            print(f"  WARN: {w}")
        return 1 if exit_on_fail else 0


def find_section(body: str, title: str) -> tuple[int, int] | None:
    pat = re.compile(SECTION_PATTERN_TMPL.format(title=re.escape(title)), re.MULTILINE)
    match = pat.search(body)
    if not match:
        return None
    start = match.end()
    next_section = re.search(r"^##\s+\S", body[start:], re.MULTILINE)
    end = start + next_section.start() if next_section else len(body)
    return start, end


def find_closure_section(body: str) -> tuple[str, str] | None:
    """Return (section_title, section_text) of the first matching closure section."""
    for title in CLOSURE_SECTION_TITLES:
        loc = find_section(body, title)
        if loc:
            s, e = loc
            return title, body[s:e]
    return None


def find_line_for_item(closure_text: str, aliases: list[str]) -> str | None:
    """Return the first line in `closure_text` that mentions any alias."""
    for line in closure_text.splitlines():
        for pat in aliases:
            if re.search(pat, line, re.IGNORECASE):
                return line
    return None


def extract_state_from_line(line: str) -> str | None:
    """Return state symbol from a checkbox line OR table cell, or None if unclear."""
    # Explicit checkbox: - [x] / - [ ] / - [N/A] / - [~] / | [x] | / etc.
    m = re.search(r"\[(x|X|\s|N/A|n/a|~)\]", line)
    if m:
        s = m.group(1)
        if s in ("x", "X"):
            return "[x]"
        if s.strip() == "":
            return "[ ]"
        if s.upper() == "N/A":
            return "[N/A]"
        if s == "~":
            return "[~]"
    # Implied: ✅ / ❌ commonly used in markdown tables where [x] doesn't render
    if "✅" in line:
        return "[x]"
    if "❌" in line:
        return "[ ]"
    return None


def line_has_justification(line: str) -> bool:
    """Heuristic: line has a dash-separated reason after the checkbox/item."""
    # Look for "— <reason>" or "- <reason>" after the checkbox
    after_box = re.split(r"\[[^\]]+\]", line, maxsplit=1)
    if len(after_box) < 2:
        return False
    tail = after_box[1]
    # Strip a leading item name if present (before first dash)
    # Justification = anything after a dash (--, em-dash, single dash with space)
    return bool(re.search(r"\s[—\-–]\s\S", tail))


def validate_closure(task_path: Path) -> ClosureReport:
    report = ClosureReport(task_path=task_path)

    if not task_path.exists():
        report.errors.append(f"file not found: {task_path}")
        return report

    text = task_path.read_text(encoding="utf-8")

    # Parse frontmatter to check status
    fm_match = FRONTMATTER_PATTERN.search(text)
    frontmatter = {}
    if fm_match:
        try:
            frontmatter = yaml.safe_load(fm_match.group(1)) or {}
        except yaml.YAMLError:
            pass

    body = text[fm_match.end() :] if fm_match else text

    status = frontmatter.get("status", "")
    # Only enforce strict closure when status==done; otherwise advisory
    strict = status == "done"

    closure = find_closure_section(body)
    if closure is None:
        if strict:
            report.errors.append(
                "no closure section found "
                f"(expected one of: {CLOSURE_SECTION_TITLES})"
            )
        else:
            report.warnings.append(
                "no closure section found — advisory only (status != done)"
            )
            return report
    if closure is None:
        return report

    section_title, closure_text = closure

    # §Pendências Honestas — open items are tolerated if mentioned here
    pendencias = find_section(body, "Pendências Honestas") or find_section(
        body, "Pendências"
    )
    pendencias_text = ""
    if pendencias:
        s, e = pendencias
        pendencias_text = body[s:e]

    for name, aliases in CANONICAL_ITEMS:
        line = find_line_for_item(closure_text, aliases)
        if line is None:
            if strict:
                report.errors.append(
                    f"§{section_title}: item '{name}' not mentioned"
                )
            else:
                report.warnings.append(f"item '{name}' not mentioned in closure")
            continue

        state = extract_state_from_line(line)
        if state is None:
            # No explicit checkbox AND no ✅/❌ — might be prose ("done") or table row
            if re.search(r"\bN/A\b", line, re.IGNORECASE):
                state = "[N/A]"
            elif re.search(
                r"\b(done|completed|atualizado|added|shipped)\b", line, re.IGNORECASE
            ):
                state = "[x]"
            else:
                state = "[?]"
                if strict:
                    report.errors.append(
                        f"§{section_title}: item '{name}' has unclear state — "
                        f"line: '{line.strip()[:80]}'"
                    )

        report.items_seen[name] = state

        # Validate justification rules
        if state == "[ ]":
            justified_inline = line_has_justification(line)
            justified_pendencias = any(
                pat
                for pat in aliases
                if re.search(pat, pendencias_text, re.IGNORECASE)
            )
            if not (justified_inline or justified_pendencias):
                if strict:
                    report.errors.append(
                        f"§{section_title}: item '{name}' is [ ] without "
                        "justification (need '— reason' OR §Pendências mention)"
                    )

        if state == "[N/A]":
            if not line_has_justification(line):
                if strict:
                    report.errors.append(
                        f"§{section_title}: item '{name}' is [N/A] without "
                        "justification (need '— reason' on same line)"
                    )

    # Sanity: rubber-stamp guard. ALL [N/A] is suspect; needs at least 1 [x].
    # (Distinct from validate_task.py F12 which catches unresolved checkboxes.)
    if strict:
        checked = sum(1 for s in report.items_seen.values() if s == "[x]")
        na_count = sum(1 for s in report.items_seen.values() if s == "[N/A]")
        if checked == 0 and na_count >= 6:
            report.errors.append(
                f"§{section_title}: 0/7 [x] and {na_count}/7 [N/A] — rubber-stamp "
                "suspect (almost-all-N/A pattern). At least continuity should be "
                "[x] since the task itself registers the agent's pass."
            )
        elif checked == 0:
            report.warnings.append(
                f"§{section_title}: 0/7 [x] — verify Lei de Fechamento was actually "
                "exercised, not just acknowledged"
            )

    return report


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2

    exit_code = 0
    for arg in sys.argv[1:]:
        path = Path(arg)
        if path.is_dir():
            files = sorted(p for p in path.glob("*.md"))
            for f in files:
                # Skip template + completed/
                if f.name == "000-template.md":
                    continue
                report = validate_closure(f)
                rc = report.emit(exit_on_fail=False)
                exit_code = max(exit_code, rc)
        else:
            report = validate_closure(path)
            rc = report.emit(exit_on_fail=False)
            exit_code = max(exit_code, rc)

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
