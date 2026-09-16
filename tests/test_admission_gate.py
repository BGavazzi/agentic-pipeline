import copy
import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import admission_gate

BASE, HEAD = "a" * 40, "b" * 40


def documents(level="low"):
    identity = dict(schema_version=1, base_sha=BASE, head_sha=HEAD)
    required = admission_gate.required_gates_for(level, [])
    risk = dict(identity, risk_level=level, risk_triggers=[], required_gates=required)
    receipts = dict(identity, gates=[dict(gate=g, status="pass")
                                   for g in sorted(set(required) | {"sast", "sca", "secrets", "policy"})])
    return risk, receipts


@pytest.mark.parametrize("level", ["low", "medium", "high"])
def test_complete_evidence_admits(level):
    result = admission_gate.evaluate(*documents(level), BASE, HEAD)
    assert result["admitted"]
    assert result["metrics"]["evidence_completeness"] == 1


@pytest.mark.parametrize("status", ["fail", "error", "skipped", "not_applicable"])
def test_non_pass_cannot_admit(status):
    risk, receipts = documents()
    receipts["gates"][0]["status"] = status
    assert not admission_gate.evaluate(risk, receipts, BASE, HEAD)["admitted"]


def test_missing_high_risk_obligation_blocks():
    risk, receipts = documents("high")
    receipts["gates"] = [r for r in receipts["gates"] if r["gate"] != "ultrareview"]
    result = admission_gate.evaluate(risk, receipts, BASE, HEAD)
    assert result["blockers"] == {"ultrareview": "missing"}


@pytest.mark.parametrize("mutation", ["sha", "version", "duplicate", "unknown", "removed", "empty"])
def test_invalid_evidence_rejected(mutation):
    risk, receipts = documents("high")
    if mutation == "sha": receipts["head_sha"] = "c" * 40
    if mutation == "version": receipts["schema_version"] = 2
    if mutation == "duplicate": receipts["gates"].append(copy.deepcopy(receipts["gates"][0]))
    if mutation == "unknown": receipts["gates"][0]["gate"] = "magic"
    if mutation == "removed": risk["required_gates"] = ["unit"]
    if mutation == "empty": risk["required_gates"] = []
    with pytest.raises(ValueError):
        admission_gate.evaluate(risk, receipts, BASE, HEAD)


def test_cli_rejects_missing_input(tmp_path):
    p = subprocess.run([sys.executable, str(SCRIPTS / "admission_gate.py"),
                        "--risk", str(tmp_path / "absent"), "--receipts", str(tmp_path / "absent"),
                        "--base-sha", BASE, "--head-sha", HEAD], capture_output=True, text=True)
    assert p.returncode == 2
    assert json.loads(p.stdout)["admitted"] is False
