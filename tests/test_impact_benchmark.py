from pathlib import Path

from scripts.impact_benchmark import run_benchmark, run_case


FIXTURES = Path(__file__).parent / "impact" / "fixtures"


def test_benchmark_reports_selection_quality_and_closes_transitive_gap():
    report = run_benchmark(FIXTURES)
    assert report["status"] == "pass"
    assert report["metrics"]["cases_total"] == 3
    assert report["promotion_ready"] is True
    assert report["benchmark_version"] == "0.4"
    assert report["metrics"]["mean_selection_regret"] == 0.0
    assert report["metrics"]["fallback_rate"] == 1 / 3
    assert report["metrics"]["p95_case_duration_seconds"] >= 0.0
    transitive = next(case for case in report["cases"] if "transitive" in case["name"])
    assert transitive["metrics"]["recall"] == 1.0
    assert transitive["metrics"]["dependency_closure_count"] >= 3


def test_direct_import_fixture_is_promotion_safe():
    result = run_case(FIXTURES / "001-direct-import.json")
    assert result["promotion_safe"] is True
    assert result["metrics"]["precision"] == 1.0
    assert result["metrics"]["recall"] == 1.0
    assert result["metrics"]["selection_regret"] == 0.0


def test_benchmark_reports_bounded_load_metrics():
    report = run_benchmark(FIXTURES, iterations=2)
    assert report["metrics"]["iterations"] == 2
    assert report["metrics"]["cases_total"] == 6
    assert report["metrics"]["throughput_cases_per_second"] > 0
    assert len(report["cases"]) == 6
