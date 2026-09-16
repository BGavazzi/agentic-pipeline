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
