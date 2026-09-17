from scripts.receipt_mutation_benchmark import run_benchmark


def test_all_deterministic_receipt_mutations_fail_closed():
    report = run_benchmark()

    assert report["status"] == "pass"
    assert report["benchmark_version"] == "1.0"
    assert report["metrics"]["mutations_total"] == 9
    assert report["metrics"]["mutations_blocked"] == 9
    assert report["metrics"]["mutations_unsafe"] == 0
    assert report["metrics"]["fail_closed_rate"] == 1.0
