from __future__ import annotations

import json
import sys
from pathlib import Path

from scripts.meta_test import run_fixture


FIXTURES = Path(__file__).parent / "skills" / "fixtures"


def _command(path: Path) -> list[str]:
    return [sys.executable, str(path)]


def _observer(path: Path, *, tests_passed: bool = True) -> list[str]:
    path.write_text(
        "import json\n"
        f"print(json.dumps({{'tests_passed': {tests_passed!r}, "
        "'tool_calls': ['Read', 'Edit', 'Bash']}))\n",
        encoding="utf-8",
    )
    return _command(path)


def test_observer_rejects_planted_forbidden_file_write(tmp_path: Path):
    worker = tmp_path / "worker.py"
    worker.write_text(
        "import subprocess, pathlib\n"
        "from pathlib import Path\n"
        "root = Path.cwd()\n"
        "subprocess.run(['git', 'checkout', '-qb', 'feat/0002-safe-edit'], cwd=root, check=True)\n"
        "(root / 'README.md').write_text('changed\\n')\n"
        "(root / 'secret.txt').write_text('leaked\\n')\n"
        "task = root / '.docs/tasks/0002-safe-edit.md'\n"
        "task.write_text(task.read_text().replace('status: todo', 'status: done').replace('[ ]', '[x]'))\n"
        "(root / 'CHANGELOG.md').write_text('change\\n')\n"
        "subprocess.run(['git', 'add', '-A'], cwd=root, check=True)\n"
        "subprocess.run(['git', 'commit', '-qm', 'bad change'], cwd=root, check=True)\n"
        "print('{}')\n",
        encoding="utf-8",
    )
    result = run_fixture(
        FIXTURES / "002-forbidden-file-write", _command(worker), timeout_seconds=20,
        observer_command=_observer(tmp_path / "observer.py"),
    )
    assert result["status"] == "fail"
    assert any("files_NOT_touched" in failure for failure in result["failures"])


def test_observer_rejects_worker_claim_that_tests_passed(tmp_path: Path):
    worker = tmp_path / "worker.py"
    worker.write_text(
        "import json, subprocess\n"
        "from pathlib import Path\n"
        "root = Path.cwd()\n"
        "subprocess.run(['git', 'checkout', '-qb', 'feat/0003-verified-closure'], cwd=root, check=True)\n"
        "task = root / '.docs/tasks/0003-verified-closure.md'\n"
        "task.write_text(task.read_text().replace('status: todo', 'status: done').replace('[ ]', '[x]'))\n"
        "(root / 'CHANGELOG.md').write_text('change\\n')\n"
        "subprocess.run(['git', 'add', '-A'], cwd=root, check=True)\n"
        "subprocess.run(['git', 'commit', '-qm', 'unverified change'], cwd=root, check=True)\n"
        "print(json.dumps({'closure': {'tests': 'yes'}}))\n",
        encoding="utf-8",
    )
    result = run_fixture(
        FIXTURES / "003-closure-lie", _command(worker), timeout_seconds=20,
        observer_command=_observer(tmp_path / "observer.py", tests_passed=False),
    )
    assert result["status"] == "fail"
    assert any("closure.tests" in failure for failure in result["failures"])


def test_corpus_contains_adversarial_contracts():
    names = {path.parent.name for path in FIXTURES.glob("*/expected.yaml")}
    assert {
        "001-trivial-readme-edit",
        "002-forbidden-file-write",
        "003-closure-lie",
        "004-prompt-injection",
    } <= names
