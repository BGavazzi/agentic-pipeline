#!/usr/bin/env python3
"""Create and verify a deterministic release provenance contract.

The contract binds an artifact and SPDX/CycloneDX SBOM to a source commit,
workflow ref, tag ref and event. It is deliberately not a signature verifier:
the tag-only workflow uses GitHub's ``actions/attest`` for the cryptographic
SLSA/Sigstore layer, while this CLI checks the local subject and metadata
identity before the attestation step can run.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
SHA_RE = re.compile(r"^[0-9a-f]{40,64}$")
TAG_RE = re.compile(r"^refs/tags/v[0-9]+(?:\.[0-9]+){1,2}(?:[-+][0-9A-Za-z.-]+)?$")


def digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _read_sbom(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("SBOM must be a JSON object")
    if not (value.get("spdxVersion") or value.get("bomFormat") == "CycloneDX"):
        raise ValueError("SBOM must identify SPDX or CycloneDX format")
    return value


def build_manifest(artifact: Path, sbom: Path, commit: str, workflow: str,
                   event: str, ref: str) -> dict[str, Any]:
    if not SHA_RE.fullmatch(commit):
        raise ValueError("commit must be a hexadecimal source SHA")
    if event != "push":
        raise ValueError("release provenance requires a push event")
    if not TAG_RE.fullmatch(ref):
        raise ValueError("release provenance requires a semantic version tag ref")
    if not workflow or len(workflow) > 500:
        raise ValueError("workflow ref is required and bounded")
    _read_sbom(sbom)
    return {"schema_version": SCHEMA_VERSION, "provenance_version": 1,
            "predicate": "release-artifact", "artifact": {
                "path": artifact.name, "sha256": digest(artifact)},
            "sbom": {"path": sbom.name, "sha256": digest(sbom)},
            "source": {"commit": commit, "workflow_ref": workflow,
                       "event": event, "ref": ref}}


def verify_manifest(manifest_path: Path, artifact: Path, sbom: Path,
                    commit: str, ref: str) -> dict[str, Any]:
    value = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or value.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("unsupported provenance schema")
    if value.get("source", {}).get("commit") != commit:
        raise ValueError("provenance commit does not match expected source")
    if value.get("source", {}).get("ref") != ref:
        raise ValueError("provenance tag ref does not match expected source")
    _read_sbom(sbom)
    if value.get("artifact", {}).get("sha256") != digest(artifact):
        raise ValueError("artifact digest does not match provenance")
    if value.get("sbom", {}).get("sha256") != digest(sbom):
        raise ValueError("SBOM digest does not match provenance")
    return {"status": "pass", "schema_version": SCHEMA_VERSION,
            "artifact_sha256": digest(artifact), "sbom_sha256": digest(sbom),
            "commit": commit, "ref": ref}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    create = sub.add_parser("create")
    create.add_argument("--artifact", type=Path, required=True)
    create.add_argument("--sbom", type=Path, required=True)
    create.add_argument("--commit", required=True)
    create.add_argument("--workflow", required=True)
    create.add_argument("--event", required=True)
    create.add_argument("--ref", required=True)
    create.add_argument("--output", type=Path, required=True)
    verify = sub.add_parser("verify")
    verify.add_argument("--manifest", type=Path, required=True)
    verify.add_argument("--artifact", type=Path, required=True)
    verify.add_argument("--sbom", type=Path, required=True)
    verify.add_argument("--commit", required=True)
    verify.add_argument("--ref", required=True)
    args = parser.parse_args()
    try:
        if args.command == "create":
            result = build_manifest(args.artifact, args.sbom, args.commit,
                                    args.workflow, args.event, args.ref)
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        else:
            result = verify_manifest(args.manifest, args.artifact, args.sbom,
                                     args.commit, args.ref)
        print(json.dumps(result, sort_keys=True))
    except (OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: provenance contract failed: {type(exc).__name__}")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
