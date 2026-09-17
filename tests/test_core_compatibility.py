import copy

import pytest

from scripts.core_compatibility import evaluate
from scripts.core_version import metadata


MATRIX = {
    "schema_version": 1,
    "matrix_version": "1.0",
    "consumers": [{
        "name": "consumer",
        "minimum_core_release": "0.1.0",
        "required_contracts": {"receipt_schema": 1, "producer_envelope": 1},
    }],
}


def test_compatible_consumer_matrix_reports_full_compatibility():
    result = evaluate(metadata("a" * 40), MATRIX)
    assert result["status"] == "pass"
    assert result["metrics"]["compatibility_rate"] == 1.0


@pytest.mark.parametrize("field", ["minimum_core_release", "required_contracts"])
def test_incompatible_consumer_fails_closed(field):
    matrix = copy.deepcopy(MATRIX)
    matrix["consumers"][0][field] = "0.2.0" if field == "minimum_core_release" else {"missing": 1}
    result = evaluate(metadata("a" * 40), matrix)
    assert result["status"] == "fail"
    assert result["metrics"]["consumers_incompatible"] == 1


def test_invalid_matrix_is_rejected():
    with pytest.raises(ValueError):
        evaluate(metadata("a" * 40), {"schema_version": 1, "consumers": []})
