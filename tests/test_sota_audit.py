from __future__ import annotations

import json
from pathlib import Path

from scripts.sota_audit import audit, main, markdown


def test_audit_is_conservative_about_external_controls(tmp_path: Path):
    for relative in ("AGENTS.md", "scripts/validate_task.py", "scripts/validate_closure.py",
                     "tests/test_validate_task.py", "tests/test_validate_closure.py",
                     ".docs/tasks/000-template.md", ".github/workflows/ci.yml"):
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("placeholder", encoding="utf-8")
    report = audit(tmp_path)
    doctrine = next(item for item in report["capabilities"] if item["id"] == "doctrine-closure")
    assert doctrine["status"] == "pass"
    provenance = next(item for item in report["capabilities"] if item["id"] == "artifact-provenance-sbom")
    assert provenance["status"] == "missing"
    assert report["metrics"]["coverage_ratio"] < 1.0


def test_real_repo_report_has_versioned_metrics():
    report = audit(Path(__file__).resolve().parents[1])
    assert report["schema_version"] == 1
    assert report["audit_version"] == 1
    assert report["metrics"]["capabilities_total"] >= 10
    assert 0.0 <= report["metrics"]["coverage_ratio"] <= 1.0
    # Once the repository implements a capability, the audit must not keep
    # asserting the old missing state merely because protected deployment
    # activation remains external.
    assert any(item["status"] == "partial" for item in report["capabilities"])
    independent = next(item for item in report["capabilities"] if item["id"] == "independent-review")
    assert independent["status"] == "partial"


def test_markdown_and_cli_outputs_are_deterministic(tmp_path: Path, monkeypatch):
    output, rendered = tmp_path / "audit.json", tmp_path / "audit.md"
    monkeypatch.setattr("sys.argv", ["sota_audit.py", "--repo",
                                      str(Path(__file__).resolve().parents[1]),
                                      "--output", str(output), "--markdown-output", str(rendered)])
    assert main() == 0
    report = json.loads(output.read_text(encoding="utf-8"))
    assert rendered.read_text(encoding="utf-8") == markdown(report)
    assert "SOTA agentic harness capability audit" in rendered.read_text(encoding="utf-8")
