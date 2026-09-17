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
                                "verdict": "pass", "blocking_findings": [],
                                "tool_status": {name: {"status": "ok"}
                                                 for name in ("semgrep", "trivy", "gitleaks")}}))
    unit.write_text(json.dumps({"schema_version": 1, "base_sha": BASE, "head_sha": HEAD, "exit_code": 0}))
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
                                "status": status,
                                "producer": {"schema_version": 1,
                                             "kind": "ultrareview-producer",
                                             "invocation_id": "review-1"}}))
    return path


def infra_file(tmp_path, status="pass", base=BASE, head=HEAD):
    path = tmp_path / "infra.json"
    path.write_text(json.dumps({"schema_version": 1, "gate": "infra-dry-run",
                                "base_sha": base, "head_sha": head,
                                "status": status}))
    return path


def visual_file(tmp_path, status="pass", base=BASE, head=HEAD):
    path = tmp_path / "visual.json"
    path.write_text(json.dumps({"schema_version": 1, "gate": "visual",
                                "base_sha": base, "head_sha": head,
                                "status": status,
                                "metrics": {"diff_ratio": 0.0, "comparisons": 1}}))
    return path


def meta_test_file(tmp_path, status="pass", base=BASE, head=HEAD):
    path = tmp_path / "meta-test.json"
    path.write_text(json.dumps({"schema_version": 1, "gate": "meta-test",
                                "base_sha": base, "head_sha": head,
                                "status": status,
                                "metrics": {"fixtures_total": 1,
                                             "fixtures_passed": 1},
                                "producer": {"schema_version": 1,
                                             "kind": "meta-test-producer",
                                             "invocation_id": "meta-1"}}))
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


def test_ultrareview_without_producer_is_rejected(tmp_path):
    risk, scan, unit, policy = files(tmp_path)
    path = ultrareview_file(tmp_path)
    value = json.loads(path.read_text())
    del value["producer"]
    path.write_text(json.dumps(value))
    with pytest.raises(ValueError, match="provenance envelope"):
        build_receipts(risk, scan, unit, BASE, HEAD,
                       ultrareview_path=path, policy_path=policy)


def test_infra_report_is_carried_when_applicable(tmp_path):
    risk, scan, unit, policy = files(tmp_path)
    result = build_receipts(risk, scan, unit, BASE, HEAD,
                            policy_path=policy, infra_path=infra_file(tmp_path))
    infra = next(g for g in result["gates"] if g["gate"] == "infra-dry-run")
    assert infra["status"] == "pass"


def test_not_applicable_infra_report_does_not_create_a_blocker(tmp_path):
    risk, scan, unit, policy = files(tmp_path)
    result = build_receipts(
        risk, scan, unit, BASE, HEAD, policy_path=policy,
        infra_path=infra_file(tmp_path, status="not_applicable"),
    )
    assert "infra-dry-run" not in {g["gate"] for g in result["gates"]}


def test_stale_infra_report_rejected(tmp_path):
    risk, scan, unit, policy = files(tmp_path)
    with pytest.raises(ValueError, match="infra report"):
        build_receipts(risk, scan, unit, BASE, HEAD,
                       policy_path=policy,
                       infra_path=infra_file(tmp_path, head="c" * 40))


def test_visual_report_is_carried_into_receipts(tmp_path):
    risk, scan, unit, policy = files(tmp_path)
    result = build_receipts(
        risk, scan, unit, BASE, HEAD, policy_path=policy,
        visual_path=visual_file(tmp_path),
    )
    visual = next(g for g in result["gates"] if g["gate"] == "visual")
    assert visual["status"] == "pass"


def test_stale_visual_report_rejected(tmp_path):
    risk, scan, unit, policy = files(tmp_path)
    with pytest.raises(ValueError, match="visual report"):
        build_receipts(
            risk, scan, unit, BASE, HEAD, policy_path=policy,
            visual_path=visual_file(tmp_path, head="c" * 40),
        )


def test_meta_test_report_is_carried_and_identity_bound(tmp_path):
    risk, scan, unit, policy = files(tmp_path)
    result = build_receipts(
        risk, scan, unit, BASE, HEAD, policy_path=policy,
        meta_test_path=meta_test_file(tmp_path),
    )
    meta = next(g for g in result["gates"] if g["gate"] == "meta-test")
    assert meta["status"] == "pass"


def test_stale_meta_test_report_rejected(tmp_path):
    risk, scan, unit, policy = files(tmp_path)
    with pytest.raises(ValueError, match="meta-test report"):
        build_receipts(
            risk, scan, unit, BASE, HEAD, policy_path=policy,
            meta_test_path=meta_test_file(tmp_path, head="c" * 40),
        )


def test_meta_test_without_producer_is_rejected(tmp_path):
    risk, scan, unit, policy = files(tmp_path)
    path = meta_test_file(tmp_path)
    value = json.loads(path.read_text())
    del value["producer"]
    path.write_text(json.dumps(value))
    with pytest.raises(ValueError, match="provenance envelope"):
        build_receipts(risk, scan, unit, BASE, HEAD,
                       meta_test_path=path, policy_path=policy)
