#!/usr/bin/env python3
"""Emit a secret-free, versioned CI environment fingerprint.

The fingerprint makes dependency and runner drift observable. It is not a
hermetic-build proof: network policy, host isolation and toolchain provenance
remain separate controls.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
import platform
import re
import sys
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
PIN_RE = re.compile(r"^([A-Za-z0-9_.-]+)==([^\s#]+)$")


def _requirements(path: Path) -> tuple[dict[str, str], str]:
    raw = path.read_bytes()
    packages: dict[str, str] = {}
    for line in raw.decode("utf-8").splitlines():
        line = line.split("#", 1)[0].strip()
        if not line:
            continue
        match = PIN_RE.fullmatch(line)
        if not match:
            raise ValueError("requirements must use exact name==version pins")
        name, version = match.groups()
        key = re.sub(r"[-_.]+", "-", name).lower()
        if key in packages:
            raise ValueError(f"duplicate requirement: {name}")
        packages[key] = version
    if not packages:
        raise ValueError("requirements file is empty")
    return packages, hashlib.sha256(raw).hexdigest()


def build_fingerprint(requirements: Path, observed: dict[str, str] | None = None,
                      platform_values: dict[str, str] | None = None) -> dict[str, Any]:
    expected, requirements_sha256 = _requirements(requirements)
    observed = observed or {}
    versions: dict[str, str | None] = {}
    mismatches: list[dict[str, str]] = []
    for package, expected_version in sorted(expected.items()):
        actual = observed.get(package)
        if actual is None:
            try:
                actual = importlib.metadata.version(package)
            except importlib.metadata.PackageNotFoundError:
                actual = None
        versions[package] = actual
        if actual != expected_version:
            mismatches.append({"package": package, "expected": expected_version,
                               "observed": actual or "missing"})
    platform_values = platform_values or {
        "system": platform.system(), "release": platform.release(),
        "machine": platform.machine(), "python_implementation": platform.python_implementation(),
        "python_version": platform.python_version(),
    }
    # Only explicitly non-secret CI identity fields are captured.
    runner = {key: os.environ.get(key) for key in ("CI", "GITHUB_ACTIONS", "RUNNER_OS", "RUNNER_ARCH")}
    return {"schema_version": SCHEMA_VERSION, "fingerprint_version": 1,
            "status": "pass" if not mismatches else "error",
            "requirements_sha256": requirements_sha256,
            "packages": versions, "mismatches": mismatches,
            "platform": platform_values, "runner": runner,
            "secret_free": True}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--requirements", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        report = build_fingerprint(args.requirements)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    except (OSError, TypeError, ValueError, UnicodeError) as exc:
        print(f"ERROR: environment fingerprint failed: {type(exc).__name__}")
        return 2
    print(f"environment_fingerprint: {report['status']} packages={len(report['packages'])}")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
