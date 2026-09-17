#!/usr/bin/env python3
"""Validate the external sandbox contract before candidate code is launched.

This validator checks an attestation produced by a trusted host adapter. It
does not create a VM/container, inspect the host, or turn self-reported facts
into proof. The adapter must be outside the candidate workspace and must own
launcher, observer, credential and teardown facts.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
BOUNDARY_VERSION = 1
ATTEMPT = re.compile(r"^[0-9a-f]{32}$")


def _bool(value: object, name: str) -> None:
    if type(value) is not bool:
        raise ValueError(f"{name} must be a JSON boolean")


def _positive(value: object, name: str, maximum: int | None = None) -> None:
    if type(value) is not int or value <= 0 or (maximum is not None and value > maximum):
        raise ValueError(f"{name} must be a bounded positive integer")


def _strings(value: object, name: str) -> list[str]:
    if not isinstance(value, list) or any(type(item) is not str or not item for item in value):
        raise ValueError(f"{name} must be a string list")
    return value


def validate(facts: dict[str, Any], attempt_id: str | None = None) -> dict[str, Any]:
    if not isinstance(facts, dict) or facts.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("unsupported boundary schema")
    if facts.get("boundary_version") != BOUNDARY_VERSION:
        raise ValueError("unsupported boundary contract")
    if attempt_id is not None and facts.get("attempt_id") != attempt_id:
        raise ValueError("boundary attestation is for another attempt")
    if facts.get("attempt_id") is not None and not ATTEMPT.fullmatch(str(facts["attempt_id"])):
        raise ValueError("invalid boundary attempt id")

    isolation = facts.get("isolation")
    if not isinstance(isolation, dict) or isolation.get("kind") not in {"container", "vm"}:
        raise ValueError("isolation must be a container or VM")
    host_mounts = _strings(isolation.get("host_mounts"), "isolation.host_mounts")
    if host_mounts:
        raise ValueError("host mounts are forbidden")
    for key in ("docker_socket_mounted", "privileged"):
        _bool(isolation.get(key), f"isolation.{key}")
        if isolation[key] is True:
            raise ValueError(f"isolation.{key} is forbidden")

    network = facts.get("network")
    if not isinstance(network, dict) or network.get("mode") not in {"deny", "allowlist"}:
        raise ValueError("network mode must be deny or allowlist")
    allowlist = _strings(network.get("allowlist", []), "network.allowlist")
    if network["mode"] == "allowlist" and not allowlist:
        raise ValueError("allowlist mode requires explicit destinations")
    if any("/" in item or "\\" in item or item.startswith(".") for item in allowlist):
        raise ValueError("network allowlist contains a path")

    credentials = facts.get("credentials")
    if not isinstance(credentials, dict):
        raise ValueError("credential boundary is required")
    mounts = _strings(credentials.get("mounted"), "credentials.mounted")
    if mounts:
        raise ValueError("mounted credentials are forbidden")
    _bool(credentials.get("host_secret_access"), "credentials.host_secret_access")
    if credentials["host_secret_access"]:
        raise ValueError("host secret access is forbidden")
    if credentials.get("scope") != "single-job-registration":
        raise ValueError("credential scope must be single-job-registration")
    _positive(credentials.get("ttl_seconds"), "credentials.ttl_seconds", 3600)

    ownership = facts.get("ownership")
    if not isinstance(ownership, dict):
        raise ValueError("external ownership is required")
    for key in ("launcher", "observer", "cleanup"):
        if ownership.get(key) != "trusted-host":
            raise ValueError(f"ownership.{key} must be trusted-host")
    if ownership.get("receipt_source") != "host-api":
        raise ValueError("receipt_source must be host-api")
    _bool(ownership.get("candidate_can_write_receipt"), "ownership.candidate_can_write_receipt")
    if ownership["candidate_can_write_receipt"]:
        raise ValueError("candidate receipt writes are forbidden")

    lifecycle = facts.get("lifecycle")
    if not isinstance(lifecycle, dict):
        raise ValueError("lifecycle contract is required")
    if lifecycle.get("one_job_max") != 1:
        raise ValueError("worker must have one-job maximum")
    for key in ("destroy_after_job", "revoke_after_job", "teardown_on_failure", "teardown_on_timeout"):
        _bool(lifecycle.get(key), f"lifecycle.{key}")
        if lifecycle[key] is not True:
            raise ValueError(f"lifecycle.{key} must be true")

    resources = facts.get("resources")
    if not isinstance(resources, dict):
        raise ValueError("resource limits are required")
    _positive(resources.get("cpu_millis"), "resources.cpu_millis", 16000)
    _positive(resources.get("memory_mb"), "resources.memory_mb", 32768)
    _positive(resources.get("pids"), "resources.pids", 4096)

    workspace = facts.get("workspace")
    if not isinstance(workspace, dict) or workspace.get("kind") not in {"tmpfs", "ephemeral-volume"}:
        raise ValueError("workspace must be disposable")
    _bool(workspace.get("retained_after_job"), "workspace.retained_after_job")
    if workspace["retained_after_job"]:
        raise ValueError("workspace retention is forbidden")

    return {
        "schema_version": SCHEMA_VERSION,
        "boundary_version": BOUNDARY_VERSION,
        "gate": "worker-boundary",
        "status": "pass",
        "attempt_id": facts.get("attempt_id"),
        "isolation": {"kind": isolation["kind"], "host_mounts": []},
        "metrics": {
            "network_allowlist_count": len(allowlist),
            "credential_ttl_seconds": credentials["ttl_seconds"],
            "cpu_millis": resources["cpu_millis"],
            "memory_mb": resources["memory_mb"],
            "pids": resources["pids"],
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--facts", type=Path, required=True)
    parser.add_argument("--attempt-id")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        report = validate(json.loads(args.facts.read_text(encoding="utf-8")), args.attempt_id)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    except (OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps({"schema_version": SCHEMA_VERSION,
            "gate": "worker-boundary", "status": "error", "error": type(exc).__name__}) + "\n", encoding="utf-8")
        print(f"worker_boundary: blocked={type(exc).__name__}")
        return 1
    print("worker_boundary: status=pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
