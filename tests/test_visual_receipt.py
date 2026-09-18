import json
import hashlib
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import visual_receipt


BASE, HEAD = "a" * 40, "b" * 40


def report(root, diff_ratio=0.01):
    picture = root / "home.png"
    picture.write_bytes(b"screenshot-fixture")
    artifact = {"path": "home.png", "sha256": hashlib.sha256(picture.read_bytes()).hexdigest()}
    return {
        "schema_version": 1,
        "task": "0016",
        "base_sha": BASE,
        "head_sha": HEAD,
        "baseline": {"ref": "main-baseline-2026-09-16", **artifact},
        "evidence": [{"kind": "screenshot", **artifact,
                      "viewport": "1440x900"}],
        "metrics": {"pages": 1, "comparisons": 1, "changed_pixels": int(diff_ratio * 1000),
                    "total_pixels": 1000, "diff_ratio": diff_ratio, "threshold": 0.02},
    }


def test_under_threshold_is_pass(tmp_path):
    result = visual_receipt.validate_report(report(tmp_path), BASE, HEAD, tmp_path, 0.02)
    assert result["gate"] == "visual"
    assert result["status"] == "pass"


def test_over_threshold_is_fail(tmp_path):
    result = visual_receipt.validate_report(report(tmp_path, 0.2), BASE, HEAD, tmp_path, 0.02)
    assert result["status"] == "fail"


@pytest.mark.parametrize("field", ["evidence", "baseline", "metrics"])
def test_missing_provenance_is_rejected(field, tmp_path):
    value = report(tmp_path)
    value.pop(field)
    with pytest.raises(ValueError):
        visual_receipt.validate_report(value, BASE, HEAD, tmp_path, 0.02)


def test_comparison_count_cannot_hide_missing_screenshots(tmp_path):
    value = report(tmp_path)
    value["metrics"]["comparisons"] = 2
    with pytest.raises(ValueError, match="comparisons"):
        visual_receipt.validate_report(value, BASE, HEAD, tmp_path, 0.02)


def test_stale_identity_is_rejected(tmp_path):
    with pytest.raises(ValueError, match="commit identity"):
        visual_receipt.validate_report(report(tmp_path), BASE, "c" * 40, tmp_path, 0.02)


def test_protected_baseline_policy_binds_ref_digest_and_browser(tmp_path):
    value = report(tmp_path)
    value["baseline"]["ref"] = "baseline-ref"
    protected = {
        "schema_version": 1,
        "baseline_ref": "baseline-ref",
        "baseline_sha256": value["baseline"]["sha256"],
        "browser_image": "mcr.microsoft.com/playwright:v1.55.0-noble",
        "threshold": 0.02,
    }
    result = visual_receipt.validate_report(value, BASE, HEAD, tmp_path, 0.02, protected)
    assert result["status"] == "pass"
    assert result["baseline_policy"]["browser_image"].startswith("mcr.microsoft.com/")


def test_candidate_cannot_replace_protected_baseline(tmp_path):
    value = report(tmp_path)
    protected = {
        "schema_version": 1,
        "baseline_ref": "protected-baseline",
        "baseline_sha256": value["baseline"]["sha256"],
        "browser_image": "playwright:v1",
    }
    with pytest.raises(ValueError, match="baseline ref"):
        visual_receipt.validate_report(value, BASE, HEAD, tmp_path, 0.02, protected)


def test_cli_writes_receipt(tmp_path):
    source = tmp_path / "visual.json"
    output = tmp_path / "receipt.json"
    source.write_text(json.dumps(report(tmp_path)), encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(Path(__file__).parents[1] / "scripts" / "visual_receipt.py"),
         "--input", str(source), "--output", str(output), "--base-sha", BASE,
         "--head-sha", HEAD, "--artifact-root", str(tmp_path), "--threshold", "0.02"], capture_output=True, text=True,
    )
    assert result.returncode == 0
    assert json.loads(output.read_text(encoding="utf-8"))["status"] == "pass"
