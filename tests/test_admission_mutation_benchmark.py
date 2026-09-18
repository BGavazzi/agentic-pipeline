from pathlib import Path

from scripts.admission_mutation_benchmark import run_benchmark


FIXTURE = Path(__file__).parent / "harness" / "fixtures" / "001-admission-pass.json"


def test_all_admission_mutations_are_killed():
    report = run_benchmark(FIXTURE)
    assert report["status"] == "pass"
    assert report["metrics"]["mutation_score"] == 1.0
    assert report["metrics"]["mutations_survived"] == 0
    assert report["policy"]["admission_authority"] is False
