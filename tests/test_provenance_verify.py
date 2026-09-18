from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.provenance_verify import build_manifest, verify_manifest


COMMIT = "a" * 40
REF = "refs/tags/v1.2.3"


def files(tmp_path: Path):
    artifact = tmp_path / "release.tar.gz"
    sbom = tmp_path / "sbom.spdx.json"
    artifact.write_bytes(b"release")
    sbom.write_text(json.dumps({"spdxVersion": "SPDX-2.3", "packages": []}), encoding="utf-8")
    return artifact, sbom


def test_manifest_binds_artifact_sbom_commit_and_tag(tmp_path: Path):
    artifact, sbom = files(tmp_path)
    manifest = build_manifest(artifact, sbom, COMMIT, "repo/.github/workflows/release.yml@refs/tags/v1.2.3",
                              "push", REF)
    path = tmp_path / "provenance.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    result = verify_manifest(path, artifact, sbom, COMMIT, REF)
    assert result["status"] == "pass"
    assert result["artifact_sha256"] == manifest["artifact"]["sha256"]


def test_tampering_or_wrong_identity_fails_closed(tmp_path: Path):
    artifact, sbom = files(tmp_path)
    manifest = build_manifest(artifact, sbom, COMMIT, "workflow", "push", REF)
    path = tmp_path / "provenance.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    artifact.write_bytes(b"tampered")
    with pytest.raises(ValueError, match="artifact digest"):
        verify_manifest(path, artifact, sbom, COMMIT, REF)
    with pytest.raises(ValueError, match="tag ref"):
        build_manifest(artifact, sbom, COMMIT, "workflow", "push", "refs/heads/main")


def test_non_release_event_and_invalid_sbom_are_rejected(tmp_path: Path):
    artifact, sbom = files(tmp_path)
    with pytest.raises(ValueError, match="push event"):
        build_manifest(artifact, sbom, COMMIT, "workflow", "pull_request", REF)
    sbom.write_text(json.dumps({"packages": []}), encoding="utf-8")
    with pytest.raises(ValueError, match="SPDX or CycloneDX"):
        build_manifest(artifact, sbom, COMMIT, "workflow", "push", REF)
