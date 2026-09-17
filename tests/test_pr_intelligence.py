from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "pr_intelligence.py"
spec = importlib.util.spec_from_file_location("pr_intelligence", SCRIPT)
module = importlib.util.module_from_spec(spec)
sys.modules["pr_intelligence"] = module
assert spec.loader is not None
spec.loader.exec_module(module)

BASE, HEAD = "a" * 40, "b" * 40


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-c", "user.email=test@test.local", "-c", "user.name=test",
         "-C", str(repo), *args], capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    return result.stdout


def write(repo: Path, path: str, text: str) -> None:
    target = repo / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")


def test_surfaces_and_human_checkpoint_are_deterministic(tmp_path: Path):
    paths = ["src/auth/login.py", ".github/workflows/ci.yml",
             "scripts/admission_gate.py", "tests/test_login.py", "ui/App.tsx"]
    risk = {"base_sha": BASE, "head_sha": HEAD, "changed_files": paths,
            "affected_modules": ["src/auth", "ui"], "risk_level": "high",
            "risk_triggers": ["auth", "ci-workflow", "gate-script"],
            "required_gates": ["unit", "integration", "sast", "sca", "ultrareview"]}
    surfaces = module.surfaces(paths)
    assert "security/identity" in surfaces
    assert "CI/workflow" in surfaces
    assert "harness/policy" in surfaces
    assert "tests" in surfaces
    gate = {"status": "blocked", "passed_count": 3, "observed_count": 5,
            "failed_or_nonpass": ["ultrareview:missing"], "statuses": {}}
    result = module.human_review(paths, risk,
                                 {"churn": 10, "additions": 5, "deletions": 5},
                                 gate, surfaces, {"status": "pass"})
    assert result["decision"] == "required_before_staging"
    assert result["checkpoint"] == "before integration"
    assert any("protected harness" in x["reason"] for x in result["triggers"])


def test_build_binds_diff_stats_and_optional_receipts(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "-q", "-b", "master")
    write(repo, "README.md", "seed\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "seed")
    base = git(repo, "rev-parse", "HEAD").strip()
    git(repo, "checkout", "-q", "-b", "feat/x")
    write(repo, "src/service.py", "return 1\nreturn 2\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "change")
    head = git(repo, "rev-parse", "HEAD").strip()
    risk_path = tmp_path / "risk.json"
    risk_path.write_text(json.dumps({"schema_version": 1, "base_sha": base,
        "head_sha": head, "changed_files": ["src/service.py"],
        "affected_modules": [], "risk_level": "low", "risk_triggers": [],
        "required_gates": ["unit"]}), encoding="utf-8")
    receipts = tmp_path / "receipts.json"
    receipts.write_text(json.dumps({"schema_version": 1, "base_sha": base, "head_sha": head,
        "gates": [{"gate": "unit", "status": "pass"},
        {"gate": "sast", "status": "pass"}, {"gate": "sca", "status": "pass"},
        {"gate": "secrets", "status": "pass"}, {"gate": "policy", "status": "pass"}]}), encoding="utf-8")
    report = module.build_intelligence(repo, risk_path, base, head, receipts)
    assert report["diff"]["changed_file_count"] == 1
    assert report["diff"]["churn"] == 2
    assert report["diff"]["source_file_count"] == 1
    assert report["gates"]["status"] == "complete"
    assert report["human_review"]["decision"] == "recommended"


def test_stale_risk_identity_is_rejected(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "-q", "-b", "master")
    write(repo, "README.md", "seed\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "seed")
    head = git(repo, "rev-parse", "HEAD").strip()
    risk = tmp_path / "risk.json"
    risk.write_text(json.dumps({"base_sha": "c" * 40, "head_sha": head}), encoding="utf-8")
    try:
        module.build_intelligence(repo, risk, "a" * 40, head)
    except ValueError as exc:
        assert "stale" in str(exc)
    else:
        raise AssertionError("stale risk identity was accepted")


def test_hidden_governance_directories_are_not_application_source():
    result = module.surfaces([".docs/tasks/0039.md", ".agents/continuity-codex.md", "src/service.py"])
    assert ".docs/tasks/0039.md" in result["documentation/governance"]
    assert ".agents/continuity-codex.md" in result["documentation/governance"]
    assert "src/service.py" in result["application/source"]


def test_markdown_never_claims_admission_from_advisory_summary():
    report = {"base_sha": BASE, "head_sha": HEAD,
        "risk": {"level": "high", "triggers": ["gate-script"], "affected_module_count": 1, "required_gate_count": 5},
        "diff": {"changed_file_count": 1, "churn": 4, "additions": 3, "deletions": 1},
        "gates": {"passed_count": 1, "observed_count": 5, "status": "blocked", "failed_or_nonpass": ["policy:fail"], "statuses": {}},
        "test_impact": {"status": "missing"},
        "human_review": {"checkpoint": "before integration", "decision": "required_before_staging", "triggers": [{"severity": "required", "reason": "policy"}]},
        "contact_surfaces": {"harness/policy": {"file_count": 1, "files": ["scripts/admission_gate.py"]}}}
    text = module.markdown(report)
    assert "required_before_staging" in text
    assert "cannot override admission" in text
    assert "policy:fail" in text
