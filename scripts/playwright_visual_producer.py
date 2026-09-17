#!/usr/bin/env python3
"""Run a trusted Playwright-style capture command and compute pixel evidence.

The browser command is supplied by the protected runtime (for example
``npx.cmd playwright test``); this adapter never chooses a browser, opens a
shell, accepts a candidate-provided baseline, or treats a textual PASS as
visual evidence. The command must write a JSON manifest to stdout containing
one candidate image path per protected baseline view. Pillow decodes both
images and computes changed pixels before ``visual_receipt`` validates the
provenance-bound report.

This is a producer/consistency boundary, not cryptographic attestation. A
protected caller must own the command, baseline manifest and artifact upload.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
import uuid
from pathlib import Path
from typing import Any

try:
    from PIL import Image, ImageChops
except ImportError:  # pragma: no cover - exercised by deployment diagnostics.
    Image = None
    ImageChops = None

try:
    from .integration_gate import staged_workspace
    from .visual_receipt import validate_report
except ImportError:  # pragma: no cover - direct CLI execution.
    from integration_gate import staged_workspace  # type: ignore
    from visual_receipt import validate_report  # type: ignore

SCHEMA_VERSION = 1
PRODUCER_VERSION = 1
FULL_SHA = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")
MAX_OUTPUT_BYTES = 64 * 1024
SENSITIVE_ENV = re.compile(r"(TOKEN|SECRET|PASSWORD|PRIVATE_KEY|API_KEY)", re.IGNORECASE)


def _safe_environment() -> dict[str, str]:
    return {
        key: value for key, value in os.environ.items()
        if not SENSITIVE_ENV.search(key)
        and not key.startswith(("PIPELINE_CLEANUP_", "PIPELINE_WORKER_"))
    }


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _argv_digest(command: list[str]) -> str:
    return hashlib.sha256(json.dumps(command, separators=(",", ":"), ensure_ascii=True).encode()).hexdigest()


def _manifest_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _inside(path: Path, root: Path) -> Path:
    resolved = path.resolve()
    if not resolved.is_relative_to(root.resolve()):
        raise ValueError("visual path escapes its trusted root")
    return resolved


def _load_baselines(path: Path) -> tuple[str, list[dict[str, str]]]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or value.get("schema_version") != 1:
        raise ValueError("unsupported baseline manifest")
    reference = value.get("ref")
    views = value.get("views")
    if not isinstance(reference, str) or not reference.strip() or not isinstance(views, list) or not views:
        raise ValueError("baseline manifest needs ref and views")
    result: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in views:
        if not isinstance(item, dict):
            raise ValueError("baseline view is not an object")
        view_id, rel, viewport = item.get("id"), item.get("path"), item.get("viewport")
        if not all(isinstance(x, str) and x.strip() for x in (view_id, rel, viewport)):
            raise ValueError("baseline view needs id, path and viewport")
        if view_id in seen:
            raise ValueError("duplicate baseline view")
        seen.add(view_id)
        result.append({"id": view_id, "path": rel, "viewport": viewport})
    return reference, result


def _pixel_diff(baseline: Path, candidate: Path, diff_path: Path) -> tuple[int, int]:
    if Image is None or ImageChops is None:
        raise RuntimeError("Pillow is required for pixel evidence")
    with Image.open(baseline) as before, Image.open(candidate) as after:
        before_rgba, after_rgba = before.convert("RGBA"), after.convert("RGBA")
        if before_rgba.size != after_rgba.size:
            raise ValueError("baseline and candidate dimensions differ")
        diff = ImageChops.difference(before_rgba, after_rgba)
        pixels = (diff.get_flattened_data() if hasattr(diff, "get_flattened_data")
                  else diff.getdata())
        changed = sum(1 for pixel in pixels if any(channel != 0 for channel in pixel))
        total = before_rgba.width * before_rgba.height
        diff_path.parent.mkdir(parents=True, exist_ok=True)
        diff.save(diff_path, format="PNG")
        return changed, total


def run_producer(repo: Path, task_id: str, base_sha: str, head_sha: str,
                 baseline_manifest: Path, baseline_root: Path, output: Path,
                 threshold: float, command: list[str], timeout_seconds: int = 900) -> dict[str, Any]:
    if not FULL_SHA.fullmatch(base_sha) or not FULL_SHA.fullmatch(head_sha):
        raise ValueError("base/head must be full commit SHAs")
    if not command:
        raise ValueError("capture command is empty")
    if type(threshold) not in (int, float) or not 0 <= threshold <= 1:
        raise ValueError("threshold must be between 0 and 1")
    reference, views = _load_baselines(baseline_manifest)
    baseline_root = baseline_root.resolve()
    invocation_id = uuid.uuid4().hex
    artifact_root = output.parent.resolve() / f"visual-artifacts-{invocation_id}"
    artifact_root.mkdir(parents=True)
    started = time.monotonic()
    with staged_workspace(repo, head_sha) as workspace:
        capture_dir = workspace / ".pipeline-visual-captures"
        capture_dir.mkdir()
        env = _safe_environment()
        env.update({
            "CI": "1",
            "PIPELINE_VISUAL_CAPTURE_DIR": str(capture_dir),
            "PIPELINE_VISUAL_TASK": task_id,
            "PIPELINE_VISUAL_BASE_SHA": base_sha,
            "PIPELINE_VISUAL_HEAD_SHA": head_sha,
        })
        try:
            result = subprocess.run(command, cwd=workspace, env=env, capture_output=True,
                                    text=True, encoding="utf-8", errors="replace",
                                    timeout=timeout_seconds, shell=False, close_fds=True)
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError("visual capture timed out") from exc
        if result.returncode != 0:
            raise RuntimeError("visual capture exited non-zero")
        if len(result.stdout.encode("utf-8")) > MAX_OUTPUT_BYTES:
            raise ValueError("visual capture manifest exceeds bounded input")
        manifest = json.loads(result.stdout)
        captures = manifest.get("views") if isinstance(manifest, dict) else None
        if not isinstance(captures, list):
            raise ValueError("capture manifest needs views")
        by_id = {item.get("id"): item for item in captures if isinstance(item, dict)}
        if set(by_id) != {view["id"] for view in views}:
            raise ValueError("capture views do not exactly match protected baselines")
        evidence: list[dict[str, Any]] = []
        baseline_evidence: dict[str, Any] | None = None
        changed_pixels = total_pixels = 0
        for view in views:
            candidate = _inside(workspace / str(by_id[view["id"]].get("path", "")), workspace)
            baseline = _inside(baseline_root / view["path"], baseline_root)
            if not candidate.is_file() or not baseline.is_file():
                raise ValueError("missing candidate or baseline screenshot")
            candidate_rel = f"candidate/{view['id']}.png"
            baseline_rel = f"baseline/{view['id']}.png"
            diff_rel = f"diff/{view['id']}.png"
            candidate_dst = artifact_root / candidate_rel
            baseline_dst = artifact_root / baseline_rel
            candidate_dst.parent.mkdir(parents=True, exist_ok=True)
            baseline_dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(candidate, candidate_dst)
            shutil.copy2(baseline, baseline_dst)
            changed, total = _pixel_diff(baseline, candidate, artifact_root / diff_rel)
            changed_pixels += changed
            total_pixels += total
            evidence.append({"kind": "screenshot", "path": candidate_rel,
                             "sha256": _sha256(candidate_dst), "viewport": view["viewport"],
                             "diff_path": diff_rel, "diff_sha256": _sha256(artifact_root / diff_rel)})
            baseline_evidence = {"ref": reference, "path": baseline_rel,
                                "sha256": _sha256(baseline_dst)}
    if baseline_evidence is None or total_pixels <= 0:
        raise ValueError("no visual comparisons were produced")
    raw = {
        "schema_version": SCHEMA_VERSION, "task": task_id,
        "base_sha": base_sha, "head_sha": head_sha,
        "baseline": baseline_evidence, "evidence": evidence,
        "metrics": {"pages": len(views), "comparisons": len(views),
                     "changed_pixels": changed_pixels, "total_pixels": total_pixels,
                     "diff_ratio": changed_pixels / total_pixels, "threshold": threshold},
    }
    receipt = validate_report(raw, base_sha, head_sha, artifact_root, threshold)
    receipt["producer"] = {
        "schema_version": PRODUCER_VERSION, "kind": "visual-producer",
        "adapter": "scripts/playwright_visual_producer.py",
        "invocation_id": invocation_id, "execution": "clean-room-command",
        "capture_command_sha256": _argv_digest(command),
        "baseline_manifest_sha256": _manifest_digest(baseline_manifest),
        "candidate_tree": head_sha,
        "credential_filter": "sensitive-environment-variables-excluded",
        "duration_seconds": round(time.monotonic() - started, 3),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("task_id")
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--base-sha", required=True)
    parser.add_argument("--head-sha", required=True)
    parser.add_argument("--baseline-manifest", type=Path, required=True)
    parser.add_argument("--baseline-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--threshold", type=float, required=True)
    parser.add_argument("--timeout", type=int, default=900)
    parser.add_argument("--command", nargs=argparse.REMAINDER, required=True)
    args = parser.parse_args()
    command = list(args.command)
    if command[:1] == ["--"]:
        command = command[1:]
    try:
        receipt = run_producer(args.repo.resolve(), args.task_id, args.base_sha, args.head_sha,
                               args.baseline_manifest.resolve(), args.baseline_root.resolve(),
                               args.output.resolve(), args.threshold, command, args.timeout)
    except (OSError, TypeError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
        print("ERROR: visual producer failed: " + type(exc).__name__, flush=True)
        return 2
    print(f"playwright_visual_producer: status={receipt['status']} "
          f"diff_ratio={receipt['metrics']['diff_ratio']:.6f}")
    return 0 if receipt["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
