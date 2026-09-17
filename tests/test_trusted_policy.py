"""Offline GitHub fixtures: authenticity requires these responses from the API."""
import copy
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import zipfile

import pytest
import yaml

from scripts import trusted_policy as policy

A, B, P, T = (c * 40 for c in "abcd")
SUBJECT = policy.identity("example/harness", 7, A, B, P)


def data():
    pr = dict(number=7, state="open", user=dict(login="builder"), changed_files=1, additions=1, deletions=0,
              base=dict(sha=A, repo=dict(full_name="example/harness")), head=dict(sha=B))
    files = [dict(filename="scripts/new_gate.py")]
    reviews = [dict(id=11, state="APPROVED", commit_id=B, user=dict(login="reviewer", type="User"))]
    return pr, files, reviews, {"reviewer": "write"}


class API:
    def __init__(self):
        self.pr, self.files, self.reviews, self.permissions = data()
        self.run = dict(id=99, workflow_id=12, repository=dict(full_name="example/harness"),
                        path=policy.WORKFLOW, event="workflow_dispatch", head_sha=P,
                        display_title=policy.title(SUBJECT), run_attempt=1, status="completed", conclusion="success")
        self.runs = [self.run]
        self.envelope = policy.produce(self, SUBJECT, 99, 1)
        self.repack()

    def repack(self, entries=None):
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, "w") as archive:
            for name, value in (entries or {"envelope.json": json.dumps(self.envelope)}).items():
                archive.writestr(name, value)
        self.raw_bytes = stream.getvalue()
        self.artifact = dict(id=55, size_in_bytes=len(self.raw_bytes), digest="sha256:" + hashlib.sha256(self.raw_bytes).hexdigest(),
                             expired=False, name=policy.artifact_name(SUBJECT, 1), workflow_run=dict(id=99))
        self.artifacts = [self.artifact]

    def get(self, path):
        if path == "actions/workflows/trusted-policy.yml":
            return dict(id=12)
        if path.startswith("actions/runs/"):
            return copy.deepcopy(self.run)
        if path == "pulls/7":
            return copy.deepcopy(self.pr)
        if path.startswith("collaborators/"):
            return dict(permission=self.permissions[path.split("/")[1]])
        if path == f"git/commits/{B}":
            return dict(tree=dict(sha=T))
        raise AssertionError(path)

    def pages(self, path, key=None):
        if path == "pulls/7/files":
            return copy.deepcopy(self.files)
        if path == "pulls/7/reviews":
            return copy.deepcopy(self.reviews)
        if path.startswith("actions/workflows/"):
            return copy.deepcopy(self.runs)
        if path == "actions/runs/99/artifacts":
            return copy.deepcopy(self.artifacts)
        raise AssertionError(path)

    def raw(self, path):
        assert path == "actions/artifacts/55/zip"
        return self.raw_bytes


def test_end_to_end_approved_policy_fixture():
    api = API()
    result = policy.consume(api, SUBJECT)
    assert result["status"] == "pass"
    assert result["provenance"]["run_attempt"] == 1
    assert result["provenance"]["artifact_digest"] == api.artifact["digest"]
    assert api.envelope["executed_tree"] is None  # no claimed candidate execution


def test_ordinary_change_without_approval_is_live():
    pr, _, _, _ = data()
    decision = policy.evaluate_review(pr, [dict(filename="README.md")], [], {})
    assert decision["allowed"] and not decision["impactful"]


def test_successful_producer_can_issue_a_blocking_observation():
    api = API()
    api.reviews = []
    api.envelope = policy.produce(api, SUBJECT, 99, 1)
    api.repack()
    report = policy.consume(api, SUBJECT)
    assert report["status"] == "review_required"
    assert report["early_review"]["allowed"] is False


def test_wrong_run_repository_rejected():
    api = API()
    api.run["repository"]["full_name"] = "other/harness"
    with pytest.raises(ValueError, match="repository"):
        policy.consume(api, SUBJECT)


@pytest.mark.parametrize("value", [None, [], "pass"])
def test_non_object_envelope_is_invalid(value):
    api = API()
    api.repack({"envelope.json": json.dumps(value)})
    with pytest.raises(ValueError, match="object"):
        policy.consume(api, SUBJECT)


@pytest.mark.parametrize("mutation", ["author", "bot", "stale", "read", "dismissed", "changes_requested"])
def test_impactful_change_rejects_invalid_approval(mutation):
    pr, files, reviews, permissions = data()
    review = reviews[0]
    if mutation == "author":
        pr["user"]["login"] = "reviewer"
    elif mutation == "bot":
        review["user"]["type"] = "Bot"
    elif mutation == "stale":
        review["commit_id"] = A
    elif mutation == "read":
        permissions["reviewer"] = "read"
    else:
        review["state"] = mutation.upper()
    assert not policy.evaluate_review(pr, files, reviews, permissions)["allowed"]


def test_other_reviewer_objection_blocks_even_ordinary_change():
    pr, _, reviews, permissions = data()
    reviews.append(dict(id=12, state="CHANGES_REQUESTED", commit_id=A, user=dict(login="second", type="User")))
    permissions["second"] = "write"
    assert not policy.evaluate_review(pr, [dict(filename="README.md")], reviews, permissions)["allowed"]


def test_comment_does_not_erase_approval_and_latest_substantive_wins():
    pr, files, reviews, permissions = data()
    reviews.append(dict(reviews[0], id=12, state="COMMENTED"))
    assert policy.evaluate_review(pr, files, reviews, permissions)["allowed"]
    reviews.insert(0, dict(reviews[0], id=13, state="DISMISSED"))
    assert not policy.evaluate_review(pr, files, reviews, permissions)["allowed"]


def test_rename_out_of_policy_and_large_change_require_review():
    pr, _, _, _ = data()
    assert not policy.evaluate_review(pr, [dict(filename="docs/old.md", previous_filename="scripts/gate.py")], [], {})["allowed"]
    pr["additions"] = 400
    assert not policy.evaluate_review(pr, [dict(filename="README.md")], [], {})["allowed"]


@pytest.mark.parametrize("field,value", [("event", "pull_request"), ("path", ".github/workflows/evil.yml"),
    ("head_sha", B), ("workflow_id", 13), ("conclusion", "failure"), ("status", "in_progress"), ("run_attempt", True)])
def test_wrong_or_unsuccessful_workflow_rejected(field, value):
    api = API()
    api.run[field] = value
    with pytest.raises(ValueError):
        policy.consume(api, SUBJECT)


@pytest.mark.parametrize("field,value", [("repository", "other/harness"), ("base_sha", P), ("head_sha", A),
    ("pull_request", 8), ("run_attempt", 2), ("producer", "builder"), ("executed_tree", T),
    ("envelope_version", True), ("workflow_id", 77), ("payload_sha256", "0" * 64), ("subject_tree", A)])
def test_forged_or_replayed_envelope_rejected(field, value):
    api = API()
    api.envelope[field] = value
    api.repack()
    with pytest.raises(ValueError):
        policy.consume(api, SUBJECT)


@pytest.mark.parametrize("field,value", [("expired", True), ("digest", "sha256:" + "0" * 64),
    ("size_in_bytes", 0), ("name", "trusted-policy-7-old-1"), ("workflow_run", dict(id=100))])
def test_wrong_artifact_metadata_rejected(field, value):
    api = API()
    api.artifact[field] = value
    with pytest.raises(ValueError):
        policy.consume(api, SUBJECT)


def test_archive_paths_and_duplicates_are_not_extracted(tmp_path):
    api = API()
    api.repack({"../escape.json": json.dumps(api.envelope)})
    with pytest.raises(ValueError):
        policy.consume(api, SUBJECT)
    api.repack()
    api.artifacts.append(api.artifact)
    with pytest.raises(ValueError):
        policy.consume(api, SUBJECT)


@pytest.mark.parametrize("change", ["base", "head", "closed", "dismissal", "permission", "incomplete", "rerun"])
def test_current_state_invalidates_old_success(change):
    api = API()
    if change in {"base", "head"}:
        api.pr[change]["sha"] = P
    elif change == "closed":
        api.pr["state"] = "closed"
    elif change == "dismissal":
        api.reviews[0]["state"] = "DISMISSED"
    elif change == "permission":
        api.permissions["reviewer"] = "read"
    elif change == "incomplete":
        api.pr["changed_files"] = 2
    else:
        api.run["run_attempt"] = 2
    with pytest.raises(ValueError):
        policy.consume(api, SUBJECT)


def test_failed_latest_does_not_fall_back_to_previous_pass():
    api = API()
    api.runs.append(dict(api.run, id=100, conclusion="failure"))
    original_get = api.get
    api.get = lambda path: api.runs[-1] if path == "actions/runs/100" else original_get(path)
    with pytest.raises(ValueError, match="not successful"):
        policy.consume(api, SUBJECT)


def test_new_producer_during_verification_blocks():
    api = API()
    original_pages = api.pages
    calls = 0
    def pages(path, key=None):
        nonlocal calls
        if path.startswith("actions/workflows/"):
            calls += 1
            if calls == 2:
                return [dict(api.run, id=100)]
        return original_pages(path, key)
    api.pages = pages
    with pytest.raises(ValueError, match="superseded"):
        policy.consume(api, SUBJECT)


def test_error_overwrites_stale_pass_without_network(tmp_path):
    output = tmp_path / "policy.json"
    output.write_text('{"status":"pass"}')
    result = subprocess.run([sys.executable, "scripts/trusted_policy.py", "consume", "--repository", "example/harness",
        "--pr", "7", "--base-sha", A, "--head-sha", B, "--policy-sha", "not-a-pin", "--output", str(output)], capture_output=True)
    assert result.returncode == 2
    assert json.loads(output.read_text())["status"] == "error"


def test_workflow_wiring_does_not_substitute_candidate_policy():
    ci = Path(".github/workflows/ci.yml").read_text()
    assert "policy=.docs/trusted-policy/policy.json" in ci
    assert "run.head_sha === pr.base.sha" not in ci
    assert "trusted_policy.py consume" in ci
    assert "Invalidate earlier policy observation" in ci
    producer = yaml.safe_load(Path(".github/workflows/trusted-policy.yml").read_text())
    assert producer["permissions"] == {"contents": "read", "pull-requests": "read", "actions": "read"}
    assert "pull_request_review:" not in Path(".github/workflows/early-review.yml").read_text()


@pytest.mark.parametrize("scenario", ["ordinary", "approved", "dismissed", "moved", "objection"])
def test_actual_early_workflow_javascript_with_offline_events(scenario):
    workflow = yaml.safe_load(Path(".github/workflows/early-review.yml").read_text())
    script = workflow["jobs"]["review"]["steps"][0]["with"]["script"]
    pr, files, reviews, _ = data()
    if scenario == "ordinary":
        files[0]["filename"] = "README.md"
        reviews = []
    if scenario in {"dismissed", "objection"}:
        reviews[0]["state"] = "DISMISSED" if scenario == "dismissed" else "CHANGES_REQUESTED"
    inputs = dict(pr=pr, files=files, reviews=reviews, moved=scenario == "moved")
    harness = r'''
const fixture = JSON.parse(process.argv[1]); let gets=0; let failed=false;
const context = {repo:{owner:'example',repo:'harness'},payload:{inputs:{pr_number:'7'}}};
const core = {setFailed:()=>{failed=true},summary:{addHeading(){return this},addRaw(){return this},async write(){}}};
const github={rest:{pulls:{get:async()=>{gets++;return {data:gets>1 && fixture.moved?{...fixture.pr,state:'closed'}:fixture.pr}},listFiles:'files',listReviews:'reviews'},repos:{getCollaboratorPermissionLevel:async()=>({data:{permission:'write'}})}},paginate:async(which)=>fixture[which]};
(async()=>{try{ await (async()=>{ SCRIPT })(); }catch(e){failed=true} console.log(JSON.stringify({failed}));})();
'''.replace("SCRIPT", script)
    result = subprocess.run(["node", "-e", harness, json.dumps(inputs)], capture_output=True, text=True, check=True)
    assert json.loads(result.stdout)["failed"] == (scenario in {"dismissed", "moved", "objection"})
