from pathlib import Path
from unittest.mock import patch

from scripts.impact_runner import run_shadow


def _impact(mode: str, selected: list[str]) -> dict:
    return {
        "schema_version": 1,
        "mode": mode,
        "selected_tests": selected,
        "policy": {"fallback_on_unknown": True, "optimization_only": True},
        "metrics": {"selected_test_count": len(selected)},
    }


def _execution(*args, **kwargs) -> dict:
    return {
        "schema_version": 1,
        "status": "pass",
        "command": kwargs["command"],
        "metrics": {"exit_code": 0},
    }


def test_impacted_mode_runs_only_selected_tests(tmp_path: Path):
    impact = _impact("impacted", ["tests/test_feature.py"])
    with patch("scripts.impact_runner.analyze", return_value=impact), patch(
        "scripts.impact_runner.run_integration", side_effect=_execution
    ) as execute:
        report = run_shadow(tmp_path, "0018", "a" * 40, "b" * 40)

    command = execute.call_args.kwargs["command"]
    assert command[-2:] == ["tests/test_feature.py", "-q"]
    assert report["authoritative"] is False
    assert report["status"] == "pass"


def test_fallback_mode_runs_full_suite(tmp_path: Path):
    impact = _impact("full", ["tests/test_feature.py"])
    with patch("scripts.impact_runner.analyze", return_value=impact), patch(
        "scripts.impact_runner.run_integration", side_effect=_execution
    ) as execute:
        run_shadow(tmp_path, "0018", "a" * 40, "b" * 40)

    command = execute.call_args.kwargs["command"]
    assert command[-2:] == ["tests", "-q"]
