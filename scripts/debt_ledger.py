#!/usr/bin/env python3
"""Harvest deliberate code shortcuts into a deterministic debt ledger.

The scanner is read-only. It prioritizes markers without a revisit task and
does not create, close, or mutate tasks. Documentation is excluded by default
because docs often quote TODOs; callers can opt into a separate docs pass.

Exit codes:
    0 -- scan completed, including when entries were found
    2 -- invalid input or an unreadable repository path
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

SCHEMA_VERSION = 1
LEDGER_VERSION = 1
MARKER_RE = re.compile(r"\b(TODO|FIXME|HACK|XXX|PONYTAIL)\b", re.IGNORECASE)
TASK_RE = re.compile(r"(?:see|ver)?\s*(?:task|tarefa)\s*#?\s*(\d{3,6})\b", re.IGNORECASE)
CODE_EXTENSIONS = {
    ".c", ".cc", ".cpp", ".cs", ".go", ".h", ".hpp", ".java", ".js",
    ".jsx", ".kt", ".mjs", ".php", ".py", ".rb", ".rs", ".scala", ".sh",
    ".sql", ".swift", ".ts", ".tsx", ".vue",
}
SKIP_DIRS = {
    ".archive", ".git", ".next", ".pytest_cache", ".venv", "__pycache__",
    "build", "coverage", "dist", "node_modules", "target", "venv",
}


def _iter_files(root: Path, include_docs: bool) -> Iterable[Path]:
    allowed = set(CODE_EXTENSIONS)
    if include_docs:
        allowed.update({".md", ".markdown", ".rst", ".txt", ".yaml", ".yml"})
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in allowed:
            continue
        if any(part in SKIP_DIRS for part in path.relative_to(root).parts):
            continue
        yield path


def scan(repo: Path, include_docs: bool = False) -> dict[str, Any]:
    if not repo.is_dir():
        raise ValueError("repository path is not a directory")
    entries: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    for path in _iter_files(repo, include_docs):
        relative = path.relative_to(repo).as_posix()
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeError) as exc:
            errors.append({"file": relative, "error": type(exc).__name__})
            continue
        for line_number, text in enumerate(lines, start=1):
            for match in MARKER_RE.finditer(text):
                task = TASK_RE.search(text)
                entries.append({
                    "file": relative,
                    "line": line_number,
                    "kind": match.group(1).upper(),
                    "text": text.strip(),
                    "revisit_task": task.group(1) if task else None,
                    "classification": "tracked" if task else "no-trigger",
                })
    entries.sort(key=lambda item: (item["classification"] != "no-trigger", item["file"], item["line"], item["kind"]))
    by_kind = Counter(item["kind"] for item in entries)
    no_trigger = sum(item["classification"] == "no-trigger" for item in entries)
    return {
        "schema_version": SCHEMA_VERSION,
        "ledger_version": LEDGER_VERSION,
        "repo": str(repo),
        "include_docs": include_docs,
        "status": "pass" if not errors else "degraded",
        "totals": {
            "markers": len(entries),
            "no_trigger": no_trigger,
            "with_trigger": len(entries) - no_trigger,
        },
        "by_kind": dict(sorted(by_kind.items())),
        "errors": errors,
        "entries": entries,
    }


def markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Debt ledger",
        "",
        f"Status: `{report['status']}`  ",
        f"Markers: **{report['totals']['markers']}** · "
        f"No trigger: **{report['totals']['no_trigger']}** · "
        f"Tracked: **{report['totals']['with_trigger']}**",
        "",
        "## No trigger",
        "",
    ]
    no_trigger = [item for item in report["entries"] if item["classification"] == "no-trigger"]
    tracked = [item for item in report["entries"] if item["classification"] == "tracked"]
    for item in no_trigger or [{"file": "—", "line": "", "kind": "", "text": "none", "revisit_task": None}]:
        lines.append(f"- `{item['file']}:{item['line']}` **{item['kind']}** — {item['text']}")
    lines.extend(["", "## Tracked", ""])
    for item in tracked or [{"file": "—", "line": "", "kind": "", "text": "none", "revisit_task": None}]:
        lines.append(f"- `{item['file']}:{item['line']}` **{item['kind']}** — task `{item['revisit_task']}` — {item['text']}")
    if report["errors"]:
        lines.extend(["", "## Scan errors", ""])
        lines.extend(f"- `{item['file']}` — {item['error']}" for item in report["errors"])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--include-docs", action="store_true")
    args = parser.parse_args()
    try:
        report = scan(args.repo.resolve(), args.include_docs)
        args.output_dir.mkdir(parents=True, exist_ok=True)
        (args.output_dir / "ledger.json").write_text(
            json.dumps(report, indent=2) + "\n", encoding="utf-8"
        )
        (args.output_dir / "ledger.md").write_text(markdown(report), encoding="utf-8")
    except (OSError, TypeError, ValueError, UnicodeError) as exc:
        print("ERROR: debt ledger failed: " + type(exc).__name__, flush=True)
        return 2
    print(
        f"debt_ledger: {report['status']} markers={report['totals']['markers']} "
        f"no_trigger={report['totals']['no_trigger']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
