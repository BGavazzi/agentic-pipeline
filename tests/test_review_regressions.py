"""Counterexamples from the independent PR review, not just happy receipts."""
import concurrent.futures
import hashlib
import json
import subprocess
import sys
import threading
from pathlib import Path

import pytest

from scripts import (admission_gate, ci_receipts, core_sync, impact_benchmark,
                     integration_gate, meta_test, policy_integrity, pr_intelligence,
                     quality_metrics_dashboard, receipt_journal, staging_pr,
                     worker_preflight, worker_supervisor, visual_receipt)
from scripts import impact_promotion

A, B = "a" * 40, "b" * 40


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")
    return path


def git(root, *args):
    return subprocess.check_output(["git", "-c", "user.name=Review", "-c",
                                    "user.email=review@example.invalid", *args],
                                   cwd=root, text=True).strip()


def repo(root):
    root.mkdir()
    git(root, "init", "-q")
    (root / "version.txt").write_text("first")
    git(root, "add", "-A")
    git(root, "commit", "-qm", "first")
    first = git(root, "rev-parse", "HEAD")
    (root / "version.txt").write_text("second")
    git(root, "commit", "-qam", "second")
    return root, first, git(root, "rev-parse", "HEAD")


@pytest.mark.parametrize("verdict,findings", [("block", [{"severity": "high"}]),
                                             ("pass", [{"severity": "high"}]),
                                             ("degraded", []), (None, [])])
def test_scanner_execution_success_never_erases_veto(tmp_path, verdict, findings):
    risk = {"schema_version": 1, "base_sha": A, "head_sha": B,
            "risk_level": "low", "risk_triggers": [], "required_gates": ["unit"]}
    scan = {"base_sha": A, "head_sha": B, "verdict": verdict, "blocking_findings": findings,
            "tool_status": {x: {"status": "ok"} for x in ("semgrep", "trivy", "gitleaks")}}
    policy = {"schema_version": 1, "gate": "policy", "base_sha": A, "head_sha": B, "status": "pass"}
    unit = tmp_path / "unit.exit"
    write_json(unit, {"schema_version": 1, "base_sha": A, "head_sha": B, "exit_code": 0})
    bundle = ci_receipts.build_receipts(write_json(tmp_path / "risk", risk),
                                       write_json(tmp_path / "scan", scan), unit, A, B,
                                       policy_path=write_json(tmp_path / "policy", policy))
    assert not admission_gate.evaluate(risk, bundle, A, B)["admitted"]


def test_archive_uses_exact_candidate_not_checkout_head(tmp_path):
    root, first, second = repo(tmp_path / "repo")
    with integration_gate.staged_workspace(root, first) as tree:
        assert (tree / "version.txt").read_text() == "first"
    assert git(root, "rev-parse", "HEAD") == second


def test_nonexistent_claimed_commit_is_rejected_before_execution(tmp_path):
    root, first, _ = repo(tmp_path / "repo")
    with pytest.raises(ValueError):
        integration_gate.run_integration(root, "review", first, B, [sys.executable, "-c", "pass"])


def test_integration_contains_staging_base_and_candidate(tmp_path):
    root, first, head = repo(tmp_path / "repo")
    git(root, "checkout", "-q", first)
    (root / "base-only.txt").write_text("staging")
    git(root, "add", "-A")
    git(root, "commit", "-qm", "base moved")
    base = git(root, "rev-parse", "HEAD")
    result = integration_gate.run_integration(root, "review", base, head, [sys.executable, "-c",
        "from pathlib import Path; assert Path('version.txt').read_text()=='second'; assert Path('base-only.txt').exists()"])
    assert result["status"] == "pass"
    assert result["integration_mode"] == "base-head-merge"


@pytest.mark.parametrize("value", ["false", "true", 0, 1, None])
def test_preflight_rejects_non_boolean_flags(value):
    with pytest.raises(ValueError):
        worker_preflight.evaluate("self-hosted", False, ["homelab-pool"], value, 0, True, 0, True)


def test_missing_teardown_fields_do_not_prove_cleanup():
    assert set(worker_supervisor._postconditions({"jobs_completed": 1, "workspace_clean": True})) == {"secrets", "registration"}


def test_stale_child_cleanup_file_cannot_authorize_worker(tmp_path):
    facts = write_json(tmp_path / "pre.json", {"worker_kind": "self-hosted", "labels": ["homelab-pool"],
        "fork_pr": False,
        "ephemeral": True, "workspace_clean": True, "mounted_secret_count": 0, "jobs_completed": 0, "docker_reachable": True})
    post = write_json(tmp_path / "post.json", {"registered": False, "jobs_completed": 1, "workspace_clean": True, "mounted_secret_count": 0})
    result = worker_supervisor.supervise(facts, post, [sys.executable, "-c", "raise RuntimeError('must not run')"])
    assert result["status"] == "blocked"


@pytest.mark.parametrize("behavior", ["raise SystemExit(7)", "import time; time.sleep(3)"])
def test_cleanup_runs_after_failure_and_timeout(tmp_path, behavior):
    facts = write_json(tmp_path / "pre.json", {"worker_kind": "self-hosted", "labels": ["homelab-pool"],
        "fork_pr": False,
        "ephemeral": True, "workspace_clean": True, "mounted_secret_count": 0, "jobs_completed": 0, "docker_reachable": True})
    adapter = tmp_path / "cleanup.py"
    adapter.write_text('import os, json\nprint(json.dumps({"attempt_id":os.environ["PIPELINE_CLEANUP_ATTEMPT"],"registered":False,"jobs_completed":1,"workspace_clean":True,"mounted_secret_count":0}))')
    post = tmp_path / "post.json"
    result = worker_supervisor.supervise(facts, post, [sys.executable, "-c", behavior],
        timeout_seconds=1, cleanup_command=[sys.executable, str(adapter)])
    assert result["status"] != "pass"
    assert json.loads(post.read_text())["attempt_id"] == result["attempt_id"]


def test_meta_test_prefers_disk_and_counts_uncommitted_forbidden_changes(tmp_path):
    fixture = tmp_path / "fixture"
    seed = fixture / "seed-repo/.docs/tasks"
    seed.mkdir(parents=True)
    (seed / "0001-task.md").write_text("status: todo\n")
    (fixture / "task-id.txt").write_text("0001")
    (fixture / "expected.yaml").write_text("expected:\n  task_status_final: done\n  files_NOT_touched: [forbidden.py]\n")
    sandbox = tmp_path / "sandbox"
    sandbox.mkdir()
    meta_test._seed_repo(fixture, sandbox)
    baseline = git(sandbox, "rev-parse", "HEAD")
    (sandbox / "forbidden.py").write_text("changed")
    failures, _, metrics = meta_test._assertions(fixture, sandbox, baseline, {"task_status_final": "done"})
    assert len(failures) == 2
    assert metrics["files_touched"] == 1


@pytest.mark.parametrize("path", ["scripts/new_dispatcher.py", "scripts/core_version.py", ".github/workflows/new-policy.yml", ".claude/skills/new/SKILL.md"])
def test_policy_protects_new_acceptance_files(tmp_path, path):
    root, _, base = repo(tmp_path / "repo")
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("policy")
    git(root, "add", "-A")
    git(root, "commit", "-qm", "policy changed")
    result = policy_integrity.build_report(root, base, git(root, "rev-parse", "HEAD"))
    assert result["status"] == "review_required"
    assert path in result["changed_policy_files"]


def test_mixed_deletion_falls_back_to_full_suite(tmp_path):
    before = {"src/removed.py": "x=1\n", "src/kept.py": "x=1\n",
              "tests/test_removed.py": "from src.removed import x\n",
              "tests/test_kept.py": "from src.kept import x\n"}
    after = dict(before)
    after.pop("src/removed.py")
    after["src/kept.py"] = "x=2\n"
    fixture = write_json(tmp_path / "case.json", {"before": before, "after": after,
         "expected_mode": "full", "relevant_tests": ["tests/test_removed.py", "tests/test_kept.py"]})
    result = impact_benchmark.run_case(fixture)
    assert result["mode"] == "full" and result["metrics"]["recall"] == 1


def test_from_package_import_submodule_retains_transitive_test(tmp_path):
    before = {"pkg/__init__.py": "", "pkg/shared.py": "x=1\n", "pkg/service.py": "from pkg import shared\n",
              "tests/test_shared.py": "from pkg.shared import x\n", "tests/test_service.py": "from pkg.service import shared\n"}
    after = dict(before, **{"pkg/shared.py": "x=2\n"})
    fixture = write_json(tmp_path / "case.json", {"before": before, "after": after,
         "expected_mode": "impacted", "relevant_tests": ["tests/test_shared.py", "tests/test_service.py"]})
    assert impact_benchmark.run_case(fixture)["metrics"]["recall"] == 1


def test_intelligence_preserves_extra_failed_gate():
    risk = {"schema_version": 1, "base_sha": A, "head_sha": B, "risk_level": "low", "risk_triggers": [], "required_gates": ["unit"]}
    bundle = {"schema_version": 1, "base_sha": A, "head_sha": B,
              "gates": [{"gate": name, "status": "pass"} for name in ("unit", "sast", "sca", "secrets", "policy")] + [{"gate": "visual", "status": "fail"}]}
    assert pr_intelligence.gate_metrics(bundle, risk)["status"] == "blocked"


def test_filtered_sync_does_not_claim_uninstalled_skills(tmp_path):
    source, target = tmp_path / "source", tmp_path / "target"
    target.mkdir()
    for name in ("wanted", "not-copied"):
        path = source / ".claude/skills" / name / "SKILL.md"
        path.parent.mkdir(parents=True)
        path.write_text(name)
    manifest = {}
    core_sync.sync_skills(source, target, {"wanted"}, False, manifest)
    core_sync.sync_vendor_metadata(source, target, False, manifest)
    text = (target / ".claude/skills/VENDORED.md").read_text()
    assert "wanted" in text and "not-copied" not in text


def test_dashboard_quarantines_invalid_shapes_and_nonfinite_metrics(tmp_path):
    bad = write_json(tmp_path / "bad.json", {"schema_version": 1, "intelligence_version": 1,
                                            "base_sha": A, "head_sha": B, "risk": None})
    good, invalid = quality_metrics_dashboard.load_reports([bad])
    assert not good and len(invalid) == 1


def test_duplicate_receipts_do_not_inflate_sample():
    value = {"base_sha": A, "head_sha": B, "risk": {}, "human_review": {}, "diff": {}, "gates": {}, "test_impact": {}}
    report = quality_metrics_dashboard.build_dashboard([value] * 30)
    assert report["sample"]["valid_receipt_count"] == 1
    assert report["sample"]["duplicate_receipt_count"] == 29
    assert report["sample"]["calibration_only"]


def test_concurrent_journal_replay_is_idempotent(tmp_path):
    path = write_json(tmp_path / "receipt.json", {"status": "pass"})
    database = tmp_path / "journal.db"
    receipt_journal.connect(database).close()
    barrier = threading.Barrier(4)
    def append(_):
        barrier.wait(timeout=10)
        return receipt_journal.append_event(database, "event", "gate", path, A, B)["status"]
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        statuses = list(pool.map(append, range(4)))
    assert statuses.count("appended") == 1 and statuses.count("duplicate") == 3


def test_existing_staging_pr_must_match_base_and_both_shas():
    with pytest.raises(ValueError):
        staging_pr.verify_pr({"headRefOid": B, "baseRefOid": A, "baseRefName": "production"}, B, A, "staging")


def test_remote_movement_prevents_staging(tmp_path, monkeypatch):
    root, base, head = repo(tmp_path / "repo")
    git(root, "remote", "add", "origin", "https://github.com/owner/repo.git")
    monkeypatch.setattr(staging_pr, "gh_json", lambda _: {"object": {"sha": A}})
    with pytest.raises(ValueError, match="remote branch moved"):
        staging_pr.verify_remote(root, "owner/repo", "candidate", "staging", head, base)


@pytest.mark.parametrize("malformation", ["pixels", "missing_artifact", "threshold", "digest"])
def test_visual_rejects_impossible_or_unverifiable_evidence(tmp_path, malformation):
    image = tmp_path / "image.png"
    image.write_bytes(b"visual fixture")
    artifact = {"path": image.name, "sha256": hashlib.sha256(image.read_bytes()).hexdigest()}
    report = {"schema_version": 1, "task": "review", "base_sha": A, "head_sha": B,
              "baseline": {"ref": A, **artifact},
              "evidence": [{"kind": "screenshot", "viewport": "desktop", **artifact}],
              "metrics": {"pages": 1, "comparisons": 1, "changed_pixels": 0,
                          "total_pixels": 100, "diff_ratio": 0, "threshold": 0}}
    if malformation == "pixels": report["metrics"].update(total_pixels=0, changed_pixels=100)
    if malformation == "missing_artifact": report["evidence"][0]["path"] = "missing.png"
    if malformation == "threshold": report["metrics"]["threshold"] = 1
    if malformation == "digest": report["evidence"][0]["sha256"] = "0" * 64
    with pytest.raises(ValueError):
        visual_receipt.validate_report(report, A, B, tmp_path, 0)


def test_promotion_rejects_different_executed_subset():
    impact = {"schema_version": 1, "base_sha": A, "head_sha": B, "mode": "impacted",
              "selected_tests": ["tests/test_needed.py"], "metrics": {"available_test_count": 2}}
    shadow = {"schema_version": 1, "base_sha": A, "head_sha": B, "status": "pass",
              "impact": {"base_sha": A, "head_sha": B, "selected_tests": ["tests/test_unrelated.py"]},
              "execution": {"base_sha": A, "head_sha": B, "status": "pass"}}
    result = impact_promotion.evaluate({"schema_version": 1, "status": "pass", "promotion_ready": True},
        impact, shadow, {"base_sha": A, "head_sha": B, "status": "pass"}, A, B)
    assert not result["eligible"]
    assert "executed_selection" in result["blockers"]
    assert "benchmark_identity" in result["blockers"]


def test_unit_receipt_requires_exact_identity(tmp_path):
    unit = write_json(tmp_path / "unit", {"schema_version": 1, "base_sha": A, "head_sha": "c" * 40, "exit_code": 0})
    assert ci_receipts.test_status(unit, A, B) == "error"
    unit.write_text("0")
    assert ci_receipts.test_status(unit, A, B) == "error"


def test_policy_review_is_exact_pair_bound(tmp_path):
    root, _, base = repo(tmp_path / "repo")
    script = root / "scripts/new_policy.py"
    script.parent.mkdir()
    script.write_text("pass")
    git(root, "add", "-A")
    git(root, "commit", "-qm", "policy")
    head = git(root, "rev-parse", "HEAD")
    approval = {"base_sha": base, "head_sha": head, "approved": True, "reviewer": "maintainer", "review_id": 1}
    assert policy_integrity.build_report(root, base, head, review_evidence=approval)["status"] == "pass"
    approval["head_sha"] = B
    assert policy_integrity.build_report(root, base, head, review_evidence=approval)["status"] == "review_required"


def test_workflow_security_invariants():
    import yaml
    workflows = Path(__file__).parents[1] / ".github/workflows"
    ci = yaml.safe_load((workflows / "ci.yml").read_text())
    jobs = ci["jobs"]
    assert jobs["admission"]["permissions"].get("pull-requests") != "write"
    assert "impact-shadow" in jobs["admission"]["needs"]
    for lane in ("integration", "impact-shadow"):
        assert "integration_allowed" in jobs[lane]["if"]
    for name in ("early-review.yml", "pr-summary.yml"):
        workflow = yaml.safe_load((workflows / name).read_text())
        for job in workflow["jobs"].values():
            for step in job["steps"]:
                assert "checkout" not in step.get("uses", "")
                assert "run" not in step
