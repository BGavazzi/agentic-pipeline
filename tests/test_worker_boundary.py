from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from scripts.worker_boundary import validate
from scripts.worker_supervisor import supervise


def boundary(**overrides):
    value = {
        "schema_version": 1,
        "boundary_version": 1,
        "isolation": {"kind": "container", "host_mounts": [],
                       "docker_socket_mounted": False, "privileged": False},
        "network": {"mode": "allowlist", "allowlist": ["github.com", "pypi.org"]},
        "credentials": {"mounted": [], "host_secret_access": False,
                         "scope": "single-job-registration", "ttl_seconds": 900},
        "ownership": {"launcher": "trusted-host", "observer": "trusted-host",
                       "cleanup": "trusted-host", "receipt_source": "host-api",
                       "candidate_can_write_receipt": False},
        "lifecycle": {"one_job_max": 1, "destroy_after_job": True,
                       "revoke_after_job": True, "teardown_on_failure": True,
                       "teardown_on_timeout": True},
        "resources": {"cpu_millis": 2000, "memory_mb": 4096, "pids": 256},
        "workspace": {"kind": "ephemeral-volume", "retained_after_job": False},
    }
    for path, value_override in overrides.items():
        if "." in path:
            section, key = path.split(".", 1)
            value[section][key] = value_override
        else:
            value[path] = value_override
    return value


def test_valid_external_boundary_is_eligible():
    report = validate(boundary())
    assert report["status"] == "pass"
    assert report["isolation"]["host_mounts"] == []
    assert report["metrics"]["network_allowlist_count"] == 2


@pytest.mark.parametrize(("field", "value"), [
    ("isolation.host_mounts", ["/var/run/docker.sock"]),
    ("isolation.docker_socket_mounted", True),
    ("isolation.privileged", True),
    ("credentials.mounted", ["runner-token"]),
    ("credentials.host_secret_access", True),
    ("workspace.retained_after_job", True),
    ("lifecycle.one_job_max", 2),
    ("lifecycle.destroy_after_job", False),
    ("lifecycle.teardown_on_failure", False),
    ("resources.pids", 0),
])
def test_boundary_rejects_unsafe_contract(field, value):
    with pytest.raises(ValueError):
        validate(boundary(**{field: value}))


@pytest.mark.parametrize(("field", "value"), [
    ("schema_version", 2),
    ("boundary_version", 2),
    ("isolation.kind", "host"),
    ("network.mode", "open"),
    ("network.allowlist", []),
    ("credentials.scope", "persistent"),
    ("credentials.ttl_seconds", 3601),
    ("ownership.observer", "candidate"),
    ("ownership.receipt_source", "stdout"),
])
def test_boundary_rejects_unknown_or_unbounded_contract(field, value):
    with pytest.raises(ValueError):
        validate(boundary(**{field: value}))


def test_optional_attempt_identity_is_strict():
    with pytest.raises(ValueError):
        validate(boundary(attempt_id="a" * 32), "b" * 32)
    assert validate(boundary(attempt_id="a" * 32), "a" * 32)["attempt_id"] == "a" * 32


def facts(path: Path) -> Path:
    path.write_text(json.dumps({
        "worker_kind": "self-hosted", "fork_pr": False,
        "labels": ["self-hosted", "homelab-pool"], "ephemeral": True,
        "jobs_completed": 0, "workspace_clean": True,
        "mounted_secret_count": 0, "docker_reachable": True,
    }), encoding="utf-8")
    return path


def cleanup(tmp_path: Path) -> list[str]:
    file = tmp_path / "cleanup.py"
    file.write_text("import json,os; print(json.dumps({'attempt_id':os.environ['PIPELINE_CLEANUP_ATTEMPT'], 'jobs_completed':1, 'workspace_clean':True, 'mounted_secret_count':0, 'registered':False}))", encoding="utf-8")
    return [sys.executable, str(file)]


def test_supervisor_requires_boundary_before_launch(tmp_path: Path):
    facts_file = facts(tmp_path / "facts.json")
    output = tmp_path / "post.json"
    result = supervise(facts_file, output, [sys.executable, "-c", "raise SystemExit(99)"],
                       cleanup_command=cleanup(tmp_path), require_boundary=True)
    assert result["status"] == "blocked"
    assert result["blockers"]["boundary"] == "external sandbox attestation required"


def test_supervisor_never_launches_with_invalid_boundary(tmp_path: Path):
    facts_file = facts(tmp_path / "facts.json")
    boundary_file = tmp_path / "boundary.json"
    boundary_file.write_text(json.dumps(boundary(**{"isolation.docker_socket_mounted": True})), encoding="utf-8")
    marker = tmp_path / "launched"
    command = [sys.executable, "-c", f"open(r'{marker}', 'w').write('bad')"]
    result = supervise(facts_file, tmp_path / "post.json", command,
                       cleanup_command=cleanup(tmp_path), boundary_facts_path=boundary_file,
                       require_boundary=True)
    assert result["status"] == "blocked"
    assert not marker.exists()


def test_supervisor_records_boundary_metrics_on_valid_attestation(tmp_path: Path):
    facts_file = facts(tmp_path / "facts.json")
    boundary_file = tmp_path / "boundary.json"
    boundary_file.write_text(json.dumps(boundary()), encoding="utf-8")
    result = supervise(facts_file, tmp_path / "post.json", [sys.executable, "-c", "pass"],
                       cleanup_command=cleanup(tmp_path), boundary_facts_path=boundary_file,
                       require_boundary=True)
    assert result["status"] == "pass"
    assert result["boundary"]["metrics"]["credential_ttl_seconds"] == 900
