from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest


SCRIPT = Path(__file__).parents[1] / "examples" / "playwright" / "storybook_capture.mjs"


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is required for the Storybook adapter")
def test_storybook_capture_is_valid_node_and_has_bounded_cli():
    syntax = subprocess.run(["node", "--check", str(SCRIPT)], capture_output=True, text=True)
    assert syntax.returncode == 0, syntax.stderr

    help_result = subprocess.run(["node", str(SCRIPT), "--help"], capture_output=True, text=True)
    assert help_result.returncode == 0, help_result.stderr
    assert "--views-file" in help_result.stdout
    assert "PIPELINE_VISUAL_CAPTURE_DIR" in help_result.stdout
    assert "CAPTURE_ADAPTER_VERSION = 1" in SCRIPT.read_text(encoding="utf-8")
