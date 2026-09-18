from pathlib import Path


WORKFLOW = Path(".github/workflows/pr-summary.yml")


def test_trusted_pr_summary_surfaces_hitl_metrics_without_checkout():
    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert "Deterministic HITL" in workflow
    assert "Changed files" in workflow
    assert "Diff churn" in workflow
    assert "Contact surfaces" in workflow
    assert "pr.base.sha" in workflow
    assert "actions/checkout" not in workflow
    assert "execution of candidate" in workflow
