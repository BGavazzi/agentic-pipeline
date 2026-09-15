import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from ci_receipts import build_receipts

BASE, HEAD = "a" * 40, "b" * 40


def files(tmp_path):
    risk = tmp_path / "risk.json"
    scan = tmp_path / "scan.json"
    unit = tmp_path / "unit.exit"
    risk.write_text(json.dumps({"schema_version": 1, "base_sha": BASE, "head_sha": HEAD,
                                "required_gates": ["unit"], "risk_level": "low"}))
    scan.write_text(json.dumps({"base_sha": BASE, "head_sha": HEAD,
                                "tool_status": {name: {"status": "ok"}
                                                 for name in ("semgrep", "trivy", "gitleaks")}}))
    unit.write_text("0")
    return risk, scan, unit


def test_builds_pass_receipts_from_job_artifacts(tmp_path):
    result = build_receipts(*files(tmp_path), BASE, HEAD)
    assert result["schema_version"] == 1
    assert {g["gate"] for g in result["gates"]} == {"unit", "sast", "sca", "secrets"}
    assert all(g["status"] == "pass" for g in result["gates"])


def test_missing_unit_artifact_is_error(tmp_path):
    risk, scan, unit = files(tmp_path)
    unit.unlink()
    result = build_receipts(risk, scan, unit, BASE, HEAD)
    assert {g["status"] for g in result["gates"] if g["gate"] == "unit"} == {"error"}


def test_stale_risk_report_rejected(tmp_path):
    risk, scan, unit = files(tmp_path)
    data = json.loads(risk.read_text())
    data["head_sha"] = "c" * 40
    risk.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="commit pair"):
        build_receipts(risk, scan, unit, BASE, HEAD)
