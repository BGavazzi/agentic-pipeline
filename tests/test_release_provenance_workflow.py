from __future__ import annotations

from pathlib import Path

import yaml


WORKFLOW = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "release-provenance.yml"


def test_release_provenance_is_tag_only_and_minimally_privileged():
    data = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    # PyYAML's YAML 1.1 resolver treats the unquoted `on` key as boolean True.
    trigger = data.get("on", data.get(True))
    assert list(trigger) == ["push"]
    assert trigger["push"]["tags"] == ["v*"]
    assert data["permissions"] == {}
    permissions = data["jobs"]["attest-source-release"]["permissions"]
    assert permissions == {
        "contents": "read",
        "id-token": "write",
        "attestations": "write",
        "artifact-metadata": "write",
    }


def test_release_provenance_uses_immutable_action_refs_and_attests_sbom():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "actions/checkout@11d5960a326750d5838078e36cf38b85af677262" in text
    assert "anchore/sbom-action@e22c389904149dbc22b58101806040fa8d37a610" in text
    assert "actions/attest@1e69f48acb82d1966a394da916b4c1698aa569d6" in text
    assert text.count("actions/attest@1e69f48acb82d1966a394da916b4c1698aa569d6") == 2
    assert "Attest source build provenance" in text
    assert "Attest source SBOM" in text
    assert "sbom-path:" in text
    assert "pull_request" not in text
    assert "GITHUB_TOKEN" not in text
