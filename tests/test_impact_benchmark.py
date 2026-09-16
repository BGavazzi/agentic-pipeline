from pathlib import Path

from scripts.impact_benchmark import run_benchmark, run_case


FIXTURES = Path(__file__).parent / "impact" / "fixtures"


def test_benchmark_reports_selection_quality_and_known_transitive_gap():
    report = run_benchmark(FIXTURES)
    assert report["status"] == "pass"
    assert report["metrics"]["cases_total"] == 3
    assert report["promotion_ready"] is False
    transitive = next(case for case in report["cases"] if "transitive" in case["name"])
    assert transitive["metrics"]["recall"] == 0.5


def test_direct_import_fixture_is_promotion_safe():
    result = run_case(FIXTURES / "001-direct-import.json")
    assert result["promotion_safe"] is True
    assert result["metrics"]["precision"] == 1.0
    assert result["metrics"]["recall"] == 1.0
