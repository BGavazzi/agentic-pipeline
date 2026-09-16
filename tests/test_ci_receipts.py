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
    policy = tmp_path / "policy.json"
    risk.write_text(json.dumps({"schema_version": 1, "base_sha": BASE, "head_sha": HEAD,
                                "required_gates": ["unit"], "risk_level": "low"}))
    scan.write_text(json.dumps({"base_sha": BASE, "head_sha": HEAD,
                                "tool_status": {name: {"status": "ok"}
                                                 for name in ("semgrep", "trivy", "gitleaks")}}))
    unit.write_text("0")
    policy.write_text(json.dumps({"schema_version": 1, "gate": "policy",
                                  "base_sha": BASE, "head_sha": HEAD,
                                  "status": "pass"}))
    return risk, scan, unit, policy


def integration_file(tmp_path, status="pass", base=BASE, head=HEAD):
    path = tmp_path / "integration.json"
    path.write_text(json.dumps({"schema_version": 1, "base_sha": base,
                                "head_sha": head, "status": status}))
    return path


def ultrareview_file(tmp_path, status="pass", base=BASE, head=HEAD):
    path = tmp_path / "ultrareview.json"
    path.write_text(json.dumps({"schema_version": 1, "gate": "ultrareview",
                                "base_sha": base, "head_sha": head,
                                "status": status}))
    return path


def test_builds_pass_receipts_from_job_artifacts(tmp_path):
    risk, scan, unit, policy = files(tmp_path)
    result = build_receipts(risk, scan, unit, BASE, HEAD, policy_path=policy)
    assert result["schema_version"] == 1
    assert {g["gate"] for g in result["gates"]} == {"unit", "sast", "sca", "secrets", "policy"}
    assert all(g["status"] == "pass" for g in result["gates"])


def test_missing_unit_artifact_is_error(tmp_path):
    risk, scan, unit, policy = files(tmp_path)
    unit.unlink()
    result = build_receipts(risk, scan, unit, BASE, HEAD, policy_path=policy)
    assert {g["status"] for g in result["gates"] if g["gate"] == "unit"} == {"error"}


def test_stale_risk_report_rejected(tmp_path):
    risk, scan, unit, policy = files(tmp_path)
    data = json.loads(risk.read_text())
    data["head_sha"] = "c" * 40
    risk.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="commit pair"):
        build_receipts(risk, scan, unit, BASE, HEAD, policy_path=policy)


def test_integration_report_is_carried_into_receipts(tmp_path):
    risk, scan, unit, policy = files(tmp_path)
    result = build_receipts(risk, scan, unit, BASE, HEAD,
                            integration_file(tmp_path), policy_path=policy)
    assert {g["gate"] for g in result["gates"]} == {
        "unit", "integration", "sast", "sca", "secrets", "policy"
    }
    assert next(g for g in result["gates"] if g["gate"] == "integration")["status"] == "pass"


def test_stale_integration_report_rejected(tmp_path):
    risk, scan, unit, policy = files(tmp_path)
    with pytest.raises(ValueError, match="integration report"):
        build_receipts(risk, scan, unit, BASE, HEAD,
                       integration_file(tmp_path, head="c" * 40), policy_path=policy)


def test_ultrareview_report_is_carried_into_receipts(tmp_path):
    risk, scan, unit, policy = files(tmp_path)
    result = build_receipts(risk, scan, unit, BASE, HEAD,
                            ultrareview_path=ultrareview_file(tmp_path), policy_path=policy)
    review = next(g for g in result["gates"] if g["gate"] == "ultrareview")
    assert review["status"] == "pass"


def test_stale_ultrareview_report_rejected(tmp_path):
    risk, scan, unit, policy = files(tmp_path)
    with pytest.raises(ValueError, match="ultrareview report"):
        build_receipts(risk, scan, unit, BASE, HEAD,
                       ultrareview_path=ultrareview_file(tmp_path, head="c" * 40),
                       policy_path=policy)
