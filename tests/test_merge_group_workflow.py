from pathlib import Path


def test_ci_declares_merge_group_trigger_and_contract_job():
    workflow = Path(".github/workflows/ci.yml").read_text(encoding="utf-8")
    assert "merge_group:" in workflow
    assert "merge-group-contract:" in workflow
    assert "merge_group_contract.py" in workflow
