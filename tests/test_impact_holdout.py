from pathlib import Path

from scripts.impact_holdout import run_holdout_benchmark


ROOT = Path(__file__).parent
TRAINING = ROOT / "impact" / "fixtures"
HOLDOUT = ROOT / "impact" / "holdout"


def test_heldout_benchmark_reports_seeded_fault_metrics():
    report = run_holdout_benchmark(TRAINING, HOLDOUT)

    assert report["status"] == "pass"
    assert report["benchmark_version"] == "1.0"
    assert report["metrics"]["holdout_cases"] == 3
    assert report["metrics"]["holdout_passed"] == 3
    assert report["metrics"]["holdout_worst_recall"] == 1.0
    assert report["metrics"]["fault_types"] == [
        "non-python-config-change", "package-import-change", "test-file-change"
    ]
    assert report["promotion_ready"] is True


def test_holdout_never_promotes_with_insufficient_independent_cases(tmp_path):
    holdout = tmp_path / "holdout"
    holdout.mkdir()
    source = (HOLDOUT / "001-test-edit.json").read_text(encoding="utf-8")
    (holdout / "001-test-edit.json").write_text(source, encoding="utf-8")

    report = run_holdout_benchmark(TRAINING, holdout)

    assert report["status"] == "pass"
    assert report["promotion_ready"] is False
    assert report["corpus"]["holdout_case_count"] < report["corpus"]["minimum_holdout_cases"]
