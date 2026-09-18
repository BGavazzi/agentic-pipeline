from __future__ import annotations

import json
from pathlib import Path

import scripts.integration_queue as queue
from scripts.local_integration_loop import Candidate


def test_group_by_base_is_deterministic():
    values = [
        Candidate(2, "two", "origin/two", base_ref="feature"),
        Candidate(1, "one", "origin/one", base_ref="master"),
        Candidate(3, "three", "origin/three", base_ref="feature"),
    ]
    groups = queue.group_by_base(values)
    assert list(groups) == ["feature", "master"]
    assert [candidate.number for candidate in groups["feature"]] == [2, 3]
    assert queue.local_base_ref("master") == "origin/master"
    assert queue.local_base_ref("origin/integration") == "origin/integration"


def test_discovery_binds_remote_head_and_draft(monkeypatch):
    seen: list[list[str]] = []

    class Result:
        returncode = 0
        stdout = json.dumps([{
            "number": 7, "title": "draft", "headRefName": "feature",
            "headRefOid": "a" * 40, "baseRefName": "master", "isDraft": True,
            "isCrossRepository": False,
        }])

    monkeypatch.setattr(queue.subprocess, "run", lambda args, **kwargs: (seen.append(args) or Result()))
    candidates = queue.discover_all_open("OWNER/REPO")
    assert candidates[0].ref == "origin/feature"
    assert candidates[0].is_draft is True
    assert "isDraft" in seen[0][-1]


def test_run_queue_aggregates_multiple_bases_without_remote_write(tmp_path: Path, monkeypatch):
    values = [
        Candidate(1, "included", "head-one", base_ref="master"),
        Candidate(2, "held", "head-two", base_ref="integration"),
    ]
    seen: list[str] = []

    def fake_integrate(repo, base, candidates, command, timeout, fetch_missing=False):
        seen.append(base)
        candidate = list(candidates)[0]
        status = "included" if candidate.number == 1 else "held_for_human"
        return {
            "candidates": [{"pr": candidate.number, "status": status,
                            "classification": "routine" if status == "included" else "acute",
                            "base_ref": candidate.base_ref}],
        }

    monkeypatch.setattr(queue.loop, "integrate", fake_integrate)
    report = queue.run_queue(tmp_path, values, command=("pytest",), timeout=3)
    assert seen == ["origin/integration", "origin/master"]
    assert report["included_prs"] == [1]
    assert report["held_prs"] == [2]
    assert report["metrics"]["base_groups"] == 2
    assert report["metrics"]["routine_survivor_rate"] == 0.5
    assert report["policy"]["staging_pr_created"] is False
