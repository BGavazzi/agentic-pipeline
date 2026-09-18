from pathlib import Path


def test_reusable_workflow_requires_immutable_policy_inputs():
    workflow = Path(".github/workflows/policy-gate-reusable.yml").read_text(encoding="utf-8")
    assert "workflow_call:" in workflow
    assert "core_ref:" in workflow
    assert "required: true" in workflow
    assert "--policy-ref \"$BASE_SHA\"" in workflow
    assert "secrets:" not in workflow


def test_run_command_routes_inputs_through_environment():
    workflow = Path(".github/workflows/policy-gate-reusable.yml").read_text(encoding="utf-8")
    assert "BASE_SHA: ${{ inputs.base_sha }}" in workflow
    assert "HEAD_SHA: ${{ inputs.head_sha }}" in workflow
    assert "TASK_ID: ${{ inputs.task_id }}" in workflow
    assert "--base \"$BASE_SHA\"" in workflow


def test_main_ci_activates_pinned_policy_and_does_not_fallback():
    workflow = Path(".github/workflows/protected-policy.yml").read_text(encoding="utf-8")
    assert "pull_request_target:" in workflow
    assert "uses: BGavazzi/agentic-pipeline/.github/workflows/policy-gate-reusable.yml@" in workflow
    assert "core_ref: c5803e4fcd50ef0d646b55823959390a8f54b4f8" in workflow
    assert "task_id: policy-${{ github.event.pull_request.number }}" in workflow
    assert "checkout" not in workflow
    assert "run:" not in workflow


def test_candidate_ci_does_not_claim_protected_policy_authority():
    workflow = Path(".github/workflows/ci.yml").read_text(encoding="utf-8")
    assert "protected-policy.yml" not in workflow
    assert "protected-policy-*" not in workflow
