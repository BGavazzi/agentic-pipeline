from pathlib import Path

from scripts.harness_selftest import run_case, run_suite


FIXTURES = Path(__file__).parent / "harness" / "fixtures"


def test_fixture_corpus_is_green():
    report = run_suite(FIXTURES)
    assert report["status"] == "pass"
    assert report["metrics"] == {
        "cases_total": 4,
        "cases_passed": 4,
        "cases_failed": 0,
        "duration_seconds": report["metrics"]["duration_seconds"],
    }


def test_stale_identity_fixture_expects_fail_closed_error():
    result = run_case(FIXTURES / "003-admission-stale-identity.json")
    assert result["status"] == "pass"
    assert result["observed"] == {"error_type": "ValueError"}
