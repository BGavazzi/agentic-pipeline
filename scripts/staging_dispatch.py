#!/usr/bin/env python3
"""Safely hand an admitted survivor to the staging-review PR adapter.

The dispatcher is intentionally conservative: it is dry-run by default and
requires ``--create`` for the one external write (opening a PR). It verifies
that the local candidate head and staging base still match the eligibility
receipt, then delegates duplicate detection and human-review markers to
``staging_pr.py``. It never merges, approves, deploys, or pushes.
"""
from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path
from typing import Any

try:
    from . import staging_pr
    from .pr_intelligence import markdown
except ImportError:  # pragma: no cover
    import staging_pr  # type: ignore
    from pr_intelligence import markdown


def compose_body(body_file: Path, intelligence_file: Path | None,
                  base_sha: str | None = None, head_sha: str | None = None) -> str:
    body = body_file.read_text(encoding="utf-8")
    if intelligence_file is None:
        return body
    intelligence = json.loads(intelligence_file.read_text(encoding="utf-8"))
    if (not base_sha or not head_sha or not isinstance(intelligence, dict)
            or intelligence.get("schema_version") != 1 or intelligence.get("intelligence_version") != 1
            or intelligence.get("base_sha") != base_sha or intelligence.get("head_sha") != head_sha):
        raise ValueError("intelligence must be a versioned JSON report for the exact commit pair")
    return body.rstrip() + "\n\n---\n\n" + markdown(intelligence) + "\n"


def dispatch(
    eligibility: Path,
    repo_path: Path,
    repo: str,
    head: str,
    base: str,
    title: str,
    body_file: Path,
    intelligence_file: Path | None = None,
    *,
    create: bool = False,
) -> dict[str, Any]:
    expected_head = staging_pr.git_sha(repo_path, head)
    expected_base = staging_pr.git_sha(repo_path, base)
    report = json.loads(eligibility.read_text(encoding="utf-8"))
    if not isinstance(report, dict):
        raise ValueError("eligibility must be a JSON object")
    if report.get("base_sha") != expected_base:
        raise ValueError("eligibility base SHA does not match the staging ref")
    if report.get("head_sha") != expected_head:
        raise ValueError("eligibility head SHA does not match the candidate ref")

    with tempfile.TemporaryDirectory(prefix="pipeline-staging-body-") as raw:
        composed = Path(raw) / "body.md"
        rendered = compose_body(body_file, intelligence_file, expected_base, expected_head)
        composed.write_text(rendered, encoding="utf-8")
        result = staging_pr.create_staging_pr(
            eligibility, repo_path, repo, head, base, title, composed,
            dry_run=not create,
        )
    result["write_authorized"] = create
    if "command" in result:
        result["command_preview"] = result.pop("command")
        result["body"] = rendered
        result["command_preview_note"] = "Temporary body path is not reusable; body text is included separately."
    result["human_review_required"] = True
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--eligibility", type=Path, required=True)
    parser.add_argument("--repo-path", type=Path, default=Path.cwd())
    parser.add_argument("--repo", required=True)
    parser.add_argument("--head", required=True)
    parser.add_argument("--base", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--body-file", type=Path, required=True)
    parser.add_argument("--intelligence-file", type=Path)
    parser.add_argument("--create", action="store_true",
                        help="open the PR; without this flag, only plan it")
    args = parser.parse_args()
    try:
        result = dispatch(args.eligibility, args.repo_path.resolve(), args.repo,
                          args.head, args.base, args.title, args.body_file,
                          args.intelligence_file, create=args.create)
    except PermissionError as exc:
        print(json.dumps({"status": "blocked", "reason": str(exc)}))
        return 1
    except (OSError, RuntimeError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "error", "error_type": type(exc).__name__}))
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
