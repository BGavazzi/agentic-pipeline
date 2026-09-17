import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import ultrareview_receipt


BASE, HEAD = "a" * 40, "b" * 40


def report(verdict="pass"):
    return {
        "schema_version": 1,
        "task": "0011",
        "base_sha": BASE,
        "head_sha": HEAD,
        "verdict": verdict,
        "independent": True,
        "reviewer": {"kind": "agent", "invocation_id": "run-0011"},
        "evidence": [{"kind": "test-run", "citation": ".docs/test-reports/unit.xml"}],
        "findings": [] if verdict == "pass" else [{"severity": "high", "citation": "scripts/x.py:4"}],
        "metrics": {"reviewed_files": 12},
    }


def test_pass_is_normalized_to_ultrareview_receipt():
    result = ultrareview_receipt.validate_report(report(), BASE, HEAD)
    assert result["gate"] == "ultrareview"
    assert result["status"] == "pass"
    assert result["independent"] is True


def test_block_is_a_valid_non_pass_receipt():
    result = ultrareview_receipt.validate_report(report("block"), BASE, HEAD)
    assert result["status"] == "fail"
    assert result["findings"]


@pytest.mark.parametrize("field", ["evidence", "reviewer", "metrics"])
def test_missing_proof_fields_are_rejected(field):
    value = report()
    value.pop(field)
    with pytest.raises(ValueError):
        ultrareview_receipt.validate_report(value, BASE, HEAD)


def test_pass_without_evidence_is_rejected():
    value = report()
    value["evidence"] = []
    with pytest.raises(ValueError, match="evidence"):
        ultrareview_receipt.validate_report(value, BASE, HEAD)


def test_block_without_findings_is_rejected():
    value = report("block")
    value["findings"] = []
    with pytest.raises(ValueError, match="finding"):
        ultrareview_receipt.validate_report(value, BASE, HEAD)


def test_stale_identity_is_rejected():
    with pytest.raises(ValueError, match="commit identity"):
        ultrareview_receipt.validate_report(report(), BASE, "c" * 40)


def test_cli_writes_canonical_receipt(tmp_path):
    source = tmp_path / "review.json"
    output = tmp_path / "receipt.json"
    source.write_text(json.dumps(report()), encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(Path(__file__).parents[1] / "scripts" / "ultrareview_receipt.py"),
         "--input", str(source), "--output", str(output), "--base-sha", BASE,
         "--head-sha", HEAD], capture_output=True, text=True,
    )
    assert result.returncode == 0
    assert json.loads(output.read_text(encoding="utf-8"))["status"] == "pass"
