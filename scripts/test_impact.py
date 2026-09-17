#!/usr/bin/env python3
"""Select tests conservatively from a git diff.

This is an optimization report, not a correctness oracle. Direct Python import
edges and conventional test paths may select an impacted subset; any unknown
file type, unresolved changed module, or empty selection falls back to the
full test suite. Callers must never interpret a partial selection as proof
that unrelated tests are unnecessary for release.
"""
from __future__ import annotations

import argparse
import ast
import json
import subprocess
from pathlib import Path

try:
    from .integration_gate import staged_workspace, commit_sha
except ImportError:
    from integration_gate import staged_workspace, commit_sha

SCHEMA_VERSION = 1


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(["git", *args], cwd=repo, capture_output=True,
                            text=True, encoding="utf-8", errors="replace")
    if result.returncode != 0:
        raise RuntimeError("git query failed")
    return result.stdout


def _module_name(path: str) -> str:
    value = path.replace("\\", "/")
    if value.endswith("/__init__.py"):
        value = value[:-12]
    elif value.endswith(".py"):
        value = value[:-3]
    return value.strip("/").replace("/", ".")


def _imports(path: Path, module: str) -> set[str]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (OSError, SyntaxError, UnicodeError):
        return set()
    result: set[str] = set()
    package = module if path.name == "__init__.py" else (module.rsplit(".", 1)[0] if "." in module else "")
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            result.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                parts = package.split(".") if package else []
                prefix = ".".join(parts[: max(0, len(parts) - node.level + 1)])
                name = ".".join(part for part in (prefix, node.module or "") if part)
            else:
                # Absolute imports are already rooted at the module named in
                # the statement; prepending the importer's package would turn
                # `from src.shared import X` inside `src.service` into the
                # nonexistent `src.src.shared`.
                name = node.module or ""
            if name:
                result.add(name)
                result.update(name + "." + alias.name for alias in node.names if alias.name != "*")
    return result


def _conventional_matches(changed: str, tests: list[str]) -> set[str]:
    stem = Path(changed).stem
    if stem == "__init__":
        return set()
    candidates = {f"test_{stem}.py", f"{stem}_test.py"}
    return {test for test in tests if Path(test).name in candidates}


def _reverse_dependency_closure(
    repo: Path, tracked: list[str], module_paths: dict[str, str],
    changed_modules: set[str],
) -> set[str]:
    """Return changed modules plus every known reverse importer.

    The first TIA version only inspected imports from tests directly to the
    changed module. That is safe but misses a common chain such as
    ``test_service -> service -> shared``. Building a conservative reverse
    graph over the tracked Python tree closes that gap without claiming to
    understand dynamic imports: unresolved imports simply contribute no edge,
    and the caller still falls back on unknown changed modules.
    """
    reverse: dict[str, set[str]] = {}
    known = set(module_paths)
    for path in tracked:
        if not path.endswith(".py"):
            continue
        importer = _module_name(path)
        for imported in _imports(repo / path, importer):
            candidates = [
                target for target in known
                if imported == target or imported.startswith(target + ".")
            ]
            if not candidates:
                continue
            target = max(candidates, key=len)
            reverse.setdefault(target, set()).add(importer)

    closure = set(changed_modules)
    frontier = set(changed_modules)
    while frontier:
        next_frontier: set[str] = set()
        for module in frontier:
            for importer in reverse.get(module, set()):
                if importer not in closure:
                    closure.add(importer)
                    next_frontier.add(importer)
        frontier = next_frontier
    return closure


def analyze(repo: Path, base: str, head: str) -> dict:
    base, head = commit_sha(repo, base), commit_sha(repo, head)
    with staged_workspace(repo, head) as tree:
        return _analyze(repo, base, head, tree)


def _analyze(repo: Path, base: str, head: str, tree: Path) -> dict:
    changed = [line for line in _git(repo, "diff", "--name-only",
                                     "--diff-filter=ACDMRT", f"{base}..{head}").splitlines()
               if line]
    tracked = [line for line in _git(repo, "ls-tree", "-r", "--name-only", head).splitlines() if line]
    test_files = sorted(path for path in tracked if path.endswith(".py") and (
        path.startswith("tests/") or Path(path).name.startswith("test_")
        or Path(path).name.endswith("_test.py")))
    selected: set[str] = set()
    reasons: list[str] = []
    fallback = False
    for path in tracked:
        if not path.endswith(".py"):
            continue
        try:
            parsed = ast.parse((tree / path).read_text(encoding="utf-8"))
            dynamic = any(isinstance(node, ast.Call) and (
                isinstance(node.func, ast.Name) and node.func.id == "__import__" or
                isinstance(node.func, ast.Attribute) and node.func.attr in {"import_module", "spec_from_file_location"})
                for node in ast.walk(parsed))
            if dynamic:
                fallback = True
                reasons.append(f"dynamic import graph: {path}")
        except (OSError, SyntaxError, UnicodeError):
            fallback = True
            reasons.append(f"unparseable module: {path}")

    module_paths = {_module_name(path): path for path in tracked if path.endswith(".py")}
    changed_modules = {_module_name(path) for path in changed if path.endswith(".py")}
    dependency_closure = _reverse_dependency_closure(
        tree, tracked, module_paths, changed_modules,
    )
    for changed_path in changed:
        if changed_path not in tracked or Path(changed_path).name == "conftest.py":
            fallback = True
            reasons.append(f"deleted file or shared pytest configuration: {changed_path}")
            continue
        if not changed_path.endswith(".py"):
            fallback = True
            reasons.append(f"non-python change: {changed_path}")
            continue
        if changed_path.startswith("tests/") or Path(changed_path).name.startswith("test_"):
            if changed_path in test_files:
                selected.add(changed_path)
            continue
        direct = _conventional_matches(changed_path, test_files)
        selected.update(direct)
        for test in test_files:
            module = _module_name(test)
            imported = _imports(tree / test, module)
            if module in dependency_closure or any(
                target in dependency_closure
                or any(target.startswith(changed_module + ".")
                       for changed_module in changed_modules)
                for target in imported
            ):
                selected.add(test)
        if not any(module == changed_path[:-3].replace("/", ".")
                   or module == changed_path[:-12].replace("/", ".")
                   for module in module_paths):
            fallback = True
            reasons.append(f"unresolved changed module: {changed_path}")

    if not changed:
        fallback = True
        reasons.append("empty diff")
    if not selected and changed:
        fallback = True
        reasons.append("no reliable impacted test")
    mode = "full" if fallback else "impacted"
    return {
        "schema_version": SCHEMA_VERSION,
        "base_sha": base,
        "head_sha": head,
        "mode": mode,
        "changed_files": changed,
        "selected_tests": sorted(test_files if fallback else selected),
        "metrics": {
            "changed_file_count": len(changed),
            "available_test_count": len(test_files),
            "selected_test_count": len(test_files if fallback else selected),
            "selection_ratio": (len(test_files if fallback else selected) / len(test_files)
                                if test_files else 1.0),
            "fallback_reasons": reasons,
            "dependency_closure_count": len(dependency_closure),
        },
        "policy": {"fallback_on_unknown": True, "optimization_only": True},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--base", required=True)
    parser.add_argument("--head", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = analyze(args.repo.resolve(), args.base, args.head)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    except (OSError, RuntimeError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print("ERROR: test impact analysis failed: " + type(exc).__name__, flush=True)
        return 2
    print(f"test_impact: mode={result['mode']} selected="
          f"{result['metrics']['selected_test_count']}/{result['metrics']['available_test_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
