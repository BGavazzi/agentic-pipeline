"""Opt-in live Docker contract tests; synthetic data only, no model invocation.

PowerShell: $env:PIPELINE_LIVE_SCANNERS='1'; python -m pytest tests/test_live_scanners.py -v
Images, rules and vulnerability DBs may be downloaded. No credentials required.
"""
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import scan_gate

pytestmark = pytest.mark.skipif(os.environ.get("PIPELINE_LIVE_SCANNERS") != "1",
                                reason="explicit opt-in required for Docker/network tests")


@pytest.fixture(scope="module")
def live_runs(tmp_path_factory):
    assert scan_gate.check_docker_available(), "Docker unavailable (not a passing smoke check)"
    root = tmp_path_factory.mktemp("live-scanners")
    clean = root / "clean"
    planted = root / "planted"
    clean.mkdir()
    planted.mkdir()
    (clean / "app.py").write_text("def add(a, b):\n    return a + b\n", encoding="utf-8")
    # Synthetic never-issued values (public EXAMPLE values are scanner-allowlisted).
    (planted / "config.py").write_text(
        'AWS_ACCESS_KEY_ID = "' + 'AKIA' + 'Q7M2N5R4S6T3U2V5' + '"\n', encoding="utf-8")
    (planted / "requirements.txt").write_text("Django==1.2\n", encoding="utf-8")
    (planted / "app.py").write_text(
        "import subprocess\nfrom flask import Flask, request\napp = Flask(__name__)\n"
        "@app.route('/run')\ndef run():\n"
        "    return subprocess.check_output(request.args['cmd'], shell=True)\n", encoding="utf-8")

    def exercise(name):
        invoke = getattr(scan_gate, "run_" + name)
        results = []
        for directory in (clean, planted):
            targets = [str(path.relative_to(directory)).replace("\\", "/")
                       for path in directory.rglob("*") if path.is_file()]
            results.append((directory, invoke(directory, targets)))
        return name, results

    with pytest.MonkeyPatch.context() as patch:
        if not os.environ.get("TRIVY_CACHE_DIR"):
            patch.setenv("TRIVY_CACHE_DIR", str(root / "cache"))
        with ThreadPoolExecutor(max_workers=3) as pool:
            return dict(pool.map(exercise, scan_gate.REQUIRED_TOOLS))


@pytest.mark.parametrize("tool", scan_gate.REQUIRED_TOOLS)
def test_live_clean_and_planted_contract(tool, live_runs):
    clean, planted = live_runs[tool]
    clean_result, planted_result = clean[1], planted[1]
    assert clean_result.returncode == 0, (tool, clean_result.returncode, clean_result.stderr[-1500:])
    assert not scan_gate.PARSERS[tool](clean_result.stdout), tool
    assert planted_result.returncode in ({0, 1} if tool == "gitleaks" else {0}), (
        tool, planted_result.returncode, planted_result.stderr[-1500:])
    findings = scan_gate.PARSERS[tool](planted_result.stdout)
    assert any(f.severity in {"high", "critical"} for f in findings), (tool, findings)
