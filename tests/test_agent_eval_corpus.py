from __future__ import annotations

from scripts.agent_eval_corpus import configuration_digest, summarize


def case(status: str, duration: float = 1.0, **metrics):
    return {"status": status, "metrics": {"duration_seconds": duration, **metrics}}


def meta(*cases):
    return {"schema_version": 1, "gate": "meta-test", "status": "pass", "cases": list(cases)}


def test_small_green_corpus_is_calibration_not_pass():
    report = summarize(meta(case("pass", tokens=10, cost_usd=0.2)), min_cases=2)
    assert report["status"] == "insufficient_corpus"
    assert report["metrics"]["pass_rate"] == 1.0
    assert report["metrics"]["corpus_ready"] is False
    assert report["policy"]["insufficient_corpus_is_not_pass"] is True


def test_ready_corpus_reports_duration_tokens_cost_and_pass_rate():
    report = summarize(meta(case("pass", 2.0, tokens=10, cost_usd=0.2),
                            case("pass", 4.0, tokens=30, cost_usd=0.4)), min_cases=2)
    assert report["status"] == "pass"
    assert report["metrics"]["pass_rate"] == 1.0
    assert report["metrics"]["duration_p95_seconds"] == 4.0
    assert report["metrics"]["tokens_total"] == 40
    assert report["metrics"]["cost_usd_total"] == 0.6000000000000001


def test_baseline_regression_blocks_even_when_current_cases_are_green():
    report = summarize(meta(case("pass"), case("fail")), min_cases=1,
                       baseline={"metrics": {"pass_rate": 1.0}})
    assert report["status"] == "regression"
    assert report["metrics"]["regression_detected"] is True


def test_configuration_digest_is_stable_and_changes_with_configuration():
    first = configuration_digest(["worker", "--safe"], {"model": "test"})
    second = configuration_digest(["worker", "--safe"], {"model": "test"})
    changed = configuration_digest(["worker", "--safe"], {"model": "other"})
    assert first == second
    assert first != changed
    assert len(first) == 64
