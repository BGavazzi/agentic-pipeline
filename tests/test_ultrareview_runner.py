import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import ultrareview_runner


def fixture_repo(tmp_path: Path) -> tuple[Path, str, str]:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "tests@example.invalid"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "runner tests"], cwd=repo, check=True)
    (repo / "file.txt").write_text("base\n", encoding="utf-8")
    subprocess.run(["git", "add", "file.txt"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-qm", "base"], cwd=repo, check=True)
    base = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
    (repo / "file.txt").write_text("head\n", encoding="utf-8")
    subprocess.run(["git", "commit", "-qam", "head"], cwd=repo, check=True)
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
    return repo, base, head


def reviewer_command() -> list[str]:
    code = (
        "import json, os; "
        "print(json.dumps({'schema_version':1,'task':os.environ['PIPELINE_REVIEW_TASK'],"
        "'base_sha':os.environ['PIPELINE_REVIEW_BASE_SHA'],"
        "'head_sha':os.environ['PIPELINE_REVIEW_HEAD_SHA'],'verdict':'pass',"
        "'independent':True,'reviewer':{'kind':'worker','invocation_id':'test-run'},"
        "'evidence':[{'kind':'diff','citation':os.environ['PIPELINE_REVIEW_CONTEXT']}],"
        "'findings':[],'metrics':{'reviewed_files':1}}))"
    )
    return [sys.executable, "-c", code]


def test_worker_returns_valid_pass_receipt(tmp_path):
    repo, base, head = fixture_repo(tmp_path)
    result = ultrareview_runner.run_reviewer(repo, "0012", base, head, reviewer_command())
    assert result["status"] == "pass"
    assert result["metrics"]["reviewed_files"] == 1
    assert result["metrics"]["worker_duration_seconds"] >= 0


def test_worker_rejects_nonzero_reviewer(tmp_path):
    repo, base, head = fixture_repo(tmp_path)
    result = ultrareview_runner.run_reviewer(
        repo, "0012", base, head, [sys.executable, "-c", "raise SystemExit(4)"]
    )
    assert result["status"] == "error"


def test_worker_rejects_malformed_stdout(tmp_path):
    repo, base, head = fixture_repo(tmp_path)
    result = ultrareview_runner.run_reviewer(
        repo, "0012", base, head, [sys.executable, "-c", "print('not json')"]
    )
    assert result["status"] == "error"


def test_worker_timeout_is_error(tmp_path):
    repo, base, head = fixture_repo(tmp_path)
    result = ultrareview_runner.run_reviewer(
        repo, "0012", base, head,
        [sys.executable, "-c", "import time; time.sleep(2)"], timeout_seconds=1,
    )
    assert result["status"] == "error"


def test_cli_writes_receipt(tmp_path):
    repo, base, head = fixture_repo(tmp_path)
    output = tmp_path / "review.json"
    result = subprocess.run(
        [sys.executable, str(Path(__file__).parents[1] / "scripts" / "ultrareview_runner.py"),
         "0012", "--base-sha", base, "--head-sha", head, "--repo", str(repo),
         "--output", str(output), "--command", *reviewer_command()],
        capture_output=True, text=True,
    )
    assert result.returncode == 0
    assert json.loads(output.read_text(encoding="utf-8"))["status"] == "pass"
