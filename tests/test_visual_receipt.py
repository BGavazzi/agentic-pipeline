import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import visual_receipt


BASE, HEAD = "a" * 40, "b" * 40


def report(diff_ratio=0.01):
    return {
        "schema_version": 1,
        "task": "0016",
        "base_sha": BASE,
        "head_sha": HEAD,
        "baseline": {"ref": "main-baseline-2026-09-16"},
        "evidence": [{"kind": "screenshot", "path": "artifacts/home.png",
                      "viewport": "1440x900"}],
        "metrics": {"pages": 1, "comparisons": 1, "changed_pixels": 10,
                    "total_pixels": 1000, "diff_ratio": diff_ratio, "threshold": 0.02},
    }


def test_under_threshold_is_pass():
    result = visual_receipt.validate_report(report(), BASE, HEAD)
    assert result["gate"] == "visual"
    assert result["status"] == "pass"


def test_over_threshold_is_fail():
    result = visual_receipt.validate_report(report(0.2), BASE, HEAD)
    assert result["status"] == "fail"


@pytest.mark.parametrize("field", ["evidence", "baseline", "metrics"])
def test_missing_provenance_is_rejected(field):
    value = report()
    value.pop(field)
    with pytest.raises(ValueError):
        visual_receipt.validate_report(value, BASE, HEAD)


def test_comparison_count_cannot_hide_missing_screenshots():
    value = report()
    value["metrics"]["comparisons"] = 2
    with pytest.raises(ValueError, match="comparisons"):
        visual_receipt.validate_report(value, BASE, HEAD)


def test_stale_identity_is_rejected():
    with pytest.raises(ValueError, match="commit identity"):
        visual_receipt.validate_report(report(), BASE, "c" * 40)


def test_cli_writes_receipt(tmp_path):
    source = tmp_path / "visual.json"
    output = tmp_path / "receipt.json"
    source.write_text(json.dumps(report()), encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(Path(__file__).parents[1] / "scripts" / "visual_receipt.py"),
         "--input", str(source), "--output", str(output), "--base-sha", BASE,
         "--head-sha", HEAD], capture_output=True, text=True,
    )
    assert result.returncode == 0
    assert json.loads(output.read_text(encoding="utf-8"))["status"] == "pass"
