from scripts.trusted_policy import evaluate


BASE = "a" * 40
HEAD = "b" * 40
POLICY = "c" * 40


def policy(status="pass"):
    return {
        "schema_version": 1,
        "gate": "policy",
        "base_sha": BASE,
        "head_sha": HEAD,
        "trusted_policy_ref": POLICY,
        "status": status,
        "trusted_review": {
            "base_sha": BASE,
            "head_sha": HEAD,
            "approved": True,
            "reviewer": "maintainer",
            "review_id": "review-1",
        },
    }


def attestation(**overrides):
    result = {
        "schema_version": 1,
        "base_sha": BASE,
        "head_sha": HEAD,
        "policy_ref": POLICY,
        "workflow_ref": "BGavazzi/agentic-pipeline/.github/workflows/policy-gate-reusable.yml@main",
        "run_id": "run-1",
        "protected": True,
    }
    result.update(overrides)
    return result


def test_exact_pair_and_protected_producer_pass():
    result = evaluate(policy(), attestation(), BASE, HEAD, POLICY)
    assert result["verified"] is True
    assert result["status"] == "pass"
    assert result["blockers"] == {}


def test_missing_attestation_is_blocked_not_pass():
    result = evaluate(policy(), None, BASE, HEAD)
    assert result["status"] == "blocked"
    assert result["blockers"]["producer"] == "protected_producer_attestation_missing"


def test_unprotected_or_mismatched_producer_is_blocked():
    result = evaluate(policy(), attestation(protected=False, head_sha=BASE), BASE, HEAD)
    assert result["status"] == "blocked"
    assert "producer_identity" in result["blockers"]
    assert "producer_protection" in result["blockers"]


def test_stale_policy_receipt_is_rejected():
    stale = policy()
    stale["head_sha"] = BASE
    try:
        evaluate(stale, attestation(), BASE, HEAD)
    except ValueError as exc:
        assert "stale" in str(exc)
    else:
        raise AssertionError("stale policy receipt was accepted")


def test_policy_pin_mismatch_is_rejected():
    try:
        evaluate(policy(), attestation(), BASE, HEAD, "d" * 40)
    except ValueError as exc:
        assert "approved immutable pin" in str(exc)
    else:
        raise AssertionError("unapproved policy pin was accepted")
