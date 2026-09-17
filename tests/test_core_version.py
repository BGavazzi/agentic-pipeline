from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.core_version import CORE_RELEASE_VERSION, metadata, validate


def test_metadata_is_versioned_and_validated():
    value = validate(metadata("a" * 40))
    assert value["core_release_version"] == CORE_RELEASE_VERSION
    assert value["supported_contracts"]["receipt_schema"] == 1


@pytest.mark.parametrize("field", ["metadata_schema_version", "source_repository", "supported_contracts"])
def test_invalid_metadata_is_rejected(field):
    value = metadata("a" * 40)
    value[field] = 99 if field == "metadata_schema_version" else None
    with pytest.raises(ValueError):
        validate(value)


def test_cli_validates_installed_metadata(tmp_path: Path):
    source = tmp_path / "core.json"
    output = tmp_path / "normalized.json"
    source.write_text(json.dumps(metadata("b" * 40)), encoding="utf-8")
    result = subprocess.run(
        [sys.executable, "scripts/core_version.py", "--metadata", str(source),
         "--output", str(output)], capture_output=True, text=True,
    )
    assert result.returncode == 0
    assert json.loads(output.read_text())["source_commit"] == "b" * 40
