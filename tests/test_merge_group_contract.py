from __future__ import annotations

import pytest

from scripts.merge_group_contract import validate_event


EVENT = {"action": "checks_requested", "merge_group": {
    "base_sha": "a" * 40, "head_sha": "b" * 40,
    "base_ref": "refs/heads/master", "head_ref": "refs/heads/feature/x",
}}


def test_valid_merge_group_is_identity_only():
    report = validate_event(EVENT, "merge_group", ["CI/test", "CI/gates", "CI/test"])
    assert report["status"] == "pass"
    assert report["required_checks"] == ["CI/gates", "CI/test"]
    assert report["checks_observed"] is False
    assert report["admission_authority"] is False


@pytest.mark.parametrize("event_name", ["pull_request", "push"])
def test_wrong_event_name_is_rejected(event_name: str):
    with pytest.raises(ValueError, match="event_name"):
        validate_event(EVENT, event_name, ["CI/test"])


def test_missing_identity_or_checks_is_rejected():
    with pytest.raises(ValueError, match="head_sha"):
        validate_event({"merge_group": {**EVENT["merge_group"], "head_sha": "short"}},
                       "merge_group", ["CI/test"])
    with pytest.raises(ValueError, match="at least one"):
        validate_event(EVENT, "merge_group", [" "])
