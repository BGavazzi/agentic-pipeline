import pytest

import scripts.receipt_fuzz_benchmark as benchmark


def test_bounded_property_corpus_fails_closed_deterministically():
    first = benchmark.run_benchmark()
    second = benchmark.run_benchmark()

    assert first == second
    assert first["status"] == "pass"
    assert first["benchmark_version"] == "1.0"
    assert first["bounds"]["cases_requested"] == 128
    assert first["metrics"]["cases_total"] == 128
    assert first["metrics"]["cases_fail_closed"] == 128
    assert first["metrics"]["cases_unsafe"] == 0
    assert first["metrics"]["fail_closed_rate"] == 1.0
    assert first["metrics"]["mutation_paths_covered"] == len(benchmark._case_specs())


@pytest.mark.parametrize(
    ("case_count", "max_depth"),
    [(0, 3), (benchmark.MAX_CASES + 1, 3), (1, benchmark.MAX_DEPTH + 1)],
)
def test_bounds_are_rejected(case_count, max_depth):
    with pytest.raises(ValueError):
        benchmark.run_benchmark(case_count=case_count, max_depth=max_depth)


def test_unsafe_survivor_is_explicitly_reported(monkeypatch):
    def admit(*args, **kwargs):
        return {"admitted": True}

    monkeypatch.setattr(benchmark, "evaluate", admit)
    report = benchmark.run_benchmark(seed=7, case_count=2, max_depth=1)

    assert report["status"] == "fail"
    assert report["metrics"]["cases_unsafe"] == 2
    assert report["unsafe_survivors"] == ["case-0000", "case-0001"]


def test_report_does_not_claim_authenticity():
    report = benchmark.run_benchmark(seed=9, case_count=1, max_depth=1)

    assert report["policy"]["synthetic_fuzz_evidence"] is True
    assert report["policy"]["authenticity_proven"] is False
