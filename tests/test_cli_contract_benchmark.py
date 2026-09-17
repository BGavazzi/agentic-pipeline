"""Subprocess contract tests for the canonical core gate-script registry."""
from __future__ import annotations

import os
from pathlib import Path

from scripts import cli_contract_benchmark


REPO = Path(__file__).resolve().parent.parent


def test_registry_builds_bounded_help_and_invalid_input_cases():
    cases = cli_contract_benchmark.build_cases(REPO)

    assert len({case.script for case in cases}) == 23
    assert sum(case.category == "help" for case in cases) == 21
    assert sum(case.category == "invalid-input" for case in cases) == 23
    assert all(case.expected_exit in {0, 2} for case in cases)


def test_benchmark_runs_every_case_in_subprocess():
    report = cli_contract_benchmark.run_benchmark(REPO, timeout=5.0)

    assert report["status"] == "pass"
    assert report["execution"] == {
        "transport": "subprocess",
        "shell": False,
        "network": False,
        "credentials_forwarded": False,
        "timeout_seconds": 5.0,
    }
    assert report["metrics"]["cases_total"] == 44
    assert report["metrics"]["cases_passed"] == 44
    assert report["metrics"]["cases_failed"] == 0
    assert report["metrics"]["timeouts"] == 0


def test_child_environment_does_not_forward_credentials(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "must-not-forward")
    monkeypatch.setenv("GITHUB_TOKEN", "must-not-forward")
    monkeypatch.setenv("PIPELINE_SECRET", "must-not-forward")

    environment = cli_contract_benchmark._safe_environment()

    assert "OPENAI_API_KEY" not in environment
    assert "GITHUB_TOKEN" not in environment
    assert "PIPELINE_SECRET" not in environment
    assert environment["PYTHONUTF8"] == "1"
    assert all(
        not any(marker in key.upper() for marker in cli_contract_benchmark.SENSITIVE_ENV_MARKERS)
        for key in environment
    )
    assert os.environ["OPENAI_API_KEY"] == "must-not-forward"
