from __future__ import annotations

import json
from pathlib import Path

from scripts.environment_fingerprint import build_fingerprint


def requirements(path: Path) -> None:
    path.write_text("pytest==9.0.2\nPyYAML==6.0.3\n", encoding="utf-8")


def test_fingerprint_is_secret_free_and_passes_exact_pins(tmp_path: Path):
    path = tmp_path / "requirements.txt"
    requirements(path)
    report = build_fingerprint(path, {"pytest": "9.0.2", "pyyaml": "6.0.3"},
                                {"system": "Linux", "release": "test", "machine": "x86_64"})
    assert report["status"] == "pass"
    assert report["secret_free"] is True
    assert report["requirements_sha256"]
    assert report["mismatches"] == []


def test_fingerprint_fails_on_drift(tmp_path: Path):
    path = tmp_path / "requirements.txt"
    requirements(path)
    report = build_fingerprint(path, {"pytest": "9.0.1", "pyyaml": "6.0.3"})
    assert report["status"] == "error"
    assert report["mismatches"] == [{"package": "pytest", "expected": "9.0.2", "observed": "9.0.1"}]


def test_unpinned_requirements_are_rejected(tmp_path: Path):
    path = tmp_path / "requirements.txt"
    path.write_text("pytest\n", encoding="utf-8")
    try:
        build_fingerprint(path)
    except ValueError as exc:
        assert "exact" in str(exc)
    else:
        raise AssertionError("unpinned requirement unexpectedly accepted")
