import subprocess
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from test_impact import analyze


def fixture_repo(tmp_path: Path):
    repo = tmp_path / "repo"
    (repo / "tests").mkdir(parents=True)
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "tests@example.invalid"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "impact tests"], cwd=repo, check=True)
    (repo / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
    (repo / "tests" / "test_app.py").write_text("from app import VALUE\n\ndef test_value(): assert VALUE\n", encoding="utf-8")
    (repo / "tests" / "test_other.py").write_text("def test_other(): assert True\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-qm", "base"], cwd=repo, check=True)
    base = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
    return repo, base


def commit(repo, path, content, message):
    (repo / path).write_text(content, encoding="utf-8")
    subprocess.run(["git", "add", path], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-qm", message], cwd=repo, check=True)
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()


def test_selects_directly_impacted_test(tmp_path):
    repo, base = fixture_repo(tmp_path)
    head = commit(repo, "app.py", "VALUE = 2\n", "change app")
    report = analyze(repo, base, head)
    assert report["mode"] == "impacted"
    assert report["selected_tests"] == ["tests/test_app.py"]
    assert report["metrics"]["selection_ratio"] == 0.5


def test_non_python_change_falls_back_to_full_suite(tmp_path):
    repo, base = fixture_repo(tmp_path)
    head = commit(repo, "settings.toml", "[tool]\n", "change config")
    report = analyze(repo, base, head)
    assert report["mode"] == "full"
    assert set(report["selected_tests"]) == {"tests/test_app.py", "tests/test_other.py"}


def test_unknown_python_module_falls_back_to_full_suite(tmp_path):
    repo, base = fixture_repo(tmp_path)
    head = commit(repo, "new_module.py", "VALUE = 3\n", "add module")
    report = analyze(repo, base, head)
    assert report["mode"] == "full"
    assert report["policy"]["fallback_on_unknown"] is True
