#!/usr/bin/env python3
"""
validate_task.py — schema validator for .docs/tasks/NNNN-*.md files

Purpose: deterministic gate before Builder skill picks up a task. Confirms the
task is well-formed enough for agentic execution without LLM reasoning about
"is this spec clear?".

Usage:
    python scripts/validate_task.py <task_path>
    python scripts/validate_task.py .docs/tasks/0021-feat-x.md

Exit codes:
    0  -- task passes all checks
    1  -- task has at least one validation error
    2  -- usage error (file not found, etc.)

Checks (V1):
    F1  filename matches NNNN-tipo-slug.md pattern
    F2  frontmatter parses as YAML
    F3  frontmatter has required keys: status, priority, type, created, updated
    F4  status is one of: todo | in_progress | done
    F5  priority is one of: P0 | P1 | P2
    F6  type is one of: feat | fix | refactor | docs | chore | audit | proposal | infra | test
    F7  body has ## Contexto section
    F8  body has ## O Que Fazer section
    F9  body has ## Condições de Saída section
    F10 §O Que Fazer contains at least one checkbox (- [ ] or - [x])
    F11 §Condições de Saída contains at least one checkbox
    F12 if status == done: ALL checkboxes in O Que Fazer + Condições are [x], [N/A]
        or listed in §Pendências Honestas

This script does NOT:
    - Verify that referenced files in §Arquivos Afetados exist (covered by
      validate_closure.py)
    - Check semantic quality of the description (out of scope for deterministic
      validator; that's grill-me / human review territory)
    - Run any code, network calls, or file edits

Part\ of\ the\ guidelines_IA\ pipeline (Fase 2 F2-2, ClickUp 86ahfq031 family).
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


FILENAME_PATTERN = re.compile(
    r"^(\d{4})-(feat|fix|refactor|docs|chore|audit|proposal|infra|test)-([a-z0-9][a-z0-9-]*)\.md$"
)
FRONTMATTER_PATTERN = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
CHECKBOX_PATTERN = re.compile(r"^[\s]*-\s*\[(x|X|\s|N/A|~)\]\s+(.+?)\s*$", re.MULTILINE)
SECTION_PATTERN_TMPL = r"^##\s+{title}\s*$"

REQUIRED_FRONTMATTER_KEYS = {"status", "priority", "type", "created", "updated"}
VALID_STATUS = {"todo", "in_progress", "done"}
VALID_PRIORITY = {"P0", "P1", "P2"}
VALID_TYPE = {
    "feat",
    "fix",
    "refactor",
    "docs",
    "chore",
    "audit",
    "proposal",
    "infra",
    "test",
}


@dataclass
class ValidationReport:
    task_path: Path
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return not self.errors

    def emit(self, exit_on_fail: bool = True) -> int:
        rel = self.task_path.name
        if self.passed:
            print(f"PASS  {rel}")
            for w in self.warnings:
                print(f"  WARN: {w}")
            return 0
        print(f"FAIL  {rel}")
        for e in self.errors:
            print(f"  ERROR: {e}")
        for w in self.warnings:
            print(f"  WARN: {w}")
        return 1 if exit_on_fail else 0


def find_section(body: str, title: str) -> tuple[int, int] | None:
    """Return (start, end) char offsets of the named ## section body (excluding header).

    `title` is the literal section title without the ## prefix.
    Returns None if section absent.
    """
    pat = re.compile(SECTION_PATTERN_TMPL.format(title=re.escape(title)), re.MULTILINE)
    match = pat.search(body)
    if not match:
        return None
    start = match.end()
    next_section = re.search(r"^##\s+\S", body[start:], re.MULTILINE)
    end = start + next_section.start() if next_section else len(body)
    return start, end


def extract_checkboxes(text: str) -> list[tuple[str, str]]:
    """Return [(state, label)] where state is one of: ' ', 'x', 'X', 'N/A', '~'."""
    return [(m.group(1), m.group(2).strip()) for m in CHECKBOX_PATTERN.finditer(text)]


def validate(task_path: Path) -> ValidationReport:
    report = ValidationReport(task_path=task_path)

    if not task_path.exists():
        report.errors.append(f"file not found: {task_path}")
        return report

    # F1: filename pattern
    fname = task_path.name
    if not FILENAME_PATTERN.match(fname):
        report.errors.append(
            f"F1 filename '{fname}' does not match NNNN-tipo-slug.md "
            f"(tipo in {sorted(VALID_TYPE)})"
        )

    text = task_path.read_text(encoding="utf-8")

    # F2: frontmatter parses
    fm_match = FRONTMATTER_PATTERN.search(text)
    if not fm_match:
        report.errors.append("F2 frontmatter (--- block at top) not found")
        return report

    try:
        frontmatter = yaml.safe_load(fm_match.group(1))
    except yaml.YAMLError as e:
        report.errors.append(f"F2 frontmatter YAML parse failed: {e}")
        return report

    if not isinstance(frontmatter, dict):
        report.errors.append("F2 frontmatter is not a YAML mapping")
        return report

    # F3: required keys
    missing = REQUIRED_FRONTMATTER_KEYS - set(frontmatter.keys())
    if missing:
        report.errors.append(f"F3 frontmatter missing keys: {sorted(missing)}")

    # F4-F6: enum values
    if "status" in frontmatter and frontmatter["status"] not in VALID_STATUS:
        report.errors.append(
            f"F4 status '{frontmatter['status']}' not in {sorted(VALID_STATUS)}"
        )
    if "priority" in frontmatter and frontmatter["priority"] not in VALID_PRIORITY:
        report.errors.append(
            f"F5 priority '{frontmatter['priority']}' not in {sorted(VALID_PRIORITY)}"
        )
    if "type" in frontmatter and frontmatter["type"] not in VALID_TYPE:
        report.errors.append(
            f"F6 type '{frontmatter['type']}' not in {sorted(VALID_TYPE)}"
        )

    body = text[fm_match.end() :]

    # F7-F9: required sections
    contexto = find_section(body, "Contexto")
    if contexto is None:
        report.errors.append("F7 ## Contexto section missing")

    oque = find_section(body, "O Que Fazer")
    if oque is None:
        report.errors.append("F8 ## O Que Fazer section missing")

    cond = find_section(body, "Condições de Saída")
    if cond is None:
        report.errors.append("F9 ## Condições de Saída section missing")

    # F10-F11: checkboxes in sections
    oque_boxes: list[tuple[str, str]] = []
    if oque is not None:
        start, end = oque
        oque_boxes = extract_checkboxes(body[start:end])
        if not oque_boxes:
            report.errors.append("F10 §O Que Fazer has no checkboxes (- [ ] or - [x])")

    cond_boxes: list[tuple[str, str]] = []
    if cond is not None:
        start, end = cond
        cond_boxes = extract_checkboxes(body[start:end])
        if not cond_boxes:
            report.errors.append(
                "F11 §Condições de Saída has no checkboxes"
            )

    # F12: status==done requires all checkboxes resolved
    if frontmatter.get("status") == "done":
        unresolved_oque = [
            label for (state, label) in oque_boxes if state.strip() == ""
        ]
        unresolved_cond = [
            label for (state, label) in cond_boxes if state.strip() == ""
        ]
        # Check if §Pendências Honestas exists — open boxes are tolerated there
        pendencias_section = find_section(body, "Pendências Honestas")
        pendencias_text = ""
        if pendencias_section is not None:
            s, e = pendencias_section
            pendencias_text = body[s:e]

        for label in unresolved_oque + unresolved_cond:
            label_words = label.split()
            mentioned = pendencias_text and any(
                w.lower() in pendencias_text.lower() for w in label_words[:3] if len(w) > 3
            )
            if not mentioned:
                report.errors.append(
                    f"F12 status=done but checkbox unresolved: '{label[:60]}...' "
                    "(neither [x]/[N/A] nor in §Pendências Honestas)"
                )

    # Warnings (non-fatal)
    if "clickup_id" not in frontmatter:
        report.warnings.append("clickup_id key absent — task has no ClickUp mirror")
    if "arquivos_afetados" in frontmatter:
        affected = frontmatter["arquivos_afetados"]
        if not affected or (isinstance(affected, list) and len(affected) == 0):
            report.warnings.append("arquivos_afetados is empty")

    return report


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2

    exit_code = 0
    for arg in sys.argv[1:]:
        path = Path(arg)
        if path.is_dir():
            # Validate all NNNN-*.md in the dir (skip template, completed/)
            files = sorted(
                p
                for p in path.glob("*.md")
                if FILENAME_PATTERN.match(p.name)
            )
            for f in files:
                report = validate(f)
                rc = report.emit(exit_on_fail=False)
                exit_code = max(exit_code, rc)
        else:
            report = validate(path)
            rc = report.emit(exit_on_fail=False)
            exit_code = max(exit_code, rc)

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
