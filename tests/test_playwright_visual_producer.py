from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from PIL import Image

from scripts.playwright_visual_producer import run_producer


def fixture_repo(tmp_path: Path) -> tuple[Path, str, str]:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "tests@example.invalid"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "visual tests"], cwd=repo, check=True)
    (repo / "index.html").write_text("<main>fixture</main>\n", encoding="utf-8")
    subprocess.run(["git", "add", "index.html"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-qm", "base"], cwd=repo, check=True)
    base = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
    (repo / "index.html").write_text("<main>candidate</main>\n", encoding="utf-8")
    subprocess.run(["git", "commit", "-qam", "candidate"], cwd=repo, check=True)
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
    return repo, base, head


def setup_baseline(tmp_path: Path) -> tuple[Path, Path]:
    root = tmp_path / "baselines"
    root.mkdir()
    Image.new("RGBA", (4, 4), (255, 0, 0, 255)).save(root / "home.png")
    manifest = tmp_path / "baseline.json"
    manifest.write_text(json.dumps({
        "schema_version": 1,
        "ref": "baseline-main-2026-09-17",
        "views": [{"id": "home", "path": "home.png", "viewport": "4x4"}],
    }), encoding="utf-8")
    return manifest, root


def capture_command(color: tuple[int, int, int, int]) -> list[str]:
    code = (
        "import json, os; from pathlib import Path; from PIL import Image; "
        f"Image.new('RGBA',(4,4),{color!r}).save(Path(os.environ['PIPELINE_VISUAL_CAPTURE_DIR'])/'home.png'); "
        "print(json.dumps({'views':[{'id':'home','path':'.pipeline-visual-captures/home.png'}]}))"
    )
    return [sys.executable, "-c", code]


def test_identical_render_passes_and_emits_decoded_metrics(tmp_path: Path):
    repo, base, head = fixture_repo(tmp_path)
    manifest, root = setup_baseline(tmp_path)
    receipt = run_producer(repo, "0046", base, head, manifest, root,
                           tmp_path / "reports" / "visual.json", 0.0,
                           capture_command((255, 0, 0, 255)))
    assert receipt["status"] == "pass"
    assert receipt["metrics"]["changed_pixels"] == 0
    assert receipt["metrics"]["total_pixels"] == 16
    assert receipt["producer"]["kind"] == "visual-producer"
    assert list((tmp_path / "reports").glob("visual-artifacts-*/diff/home.png"))


def test_changed_render_fails_pixel_threshold(tmp_path: Path):
    repo, base, head = fixture_repo(tmp_path)
    manifest, root = setup_baseline(tmp_path)
    receipt = run_producer(repo, "0046", base, head, manifest, root,
                           tmp_path / "reports" / "visual.json", 0.0,
                           capture_command((0, 0, 255, 255)))
    assert receipt["status"] == "fail"
    assert receipt["metrics"]["changed_pixels"] == 16
    assert receipt["metrics"]["diff_ratio"] == 1.0


def test_capture_views_must_match_protected_baseline(tmp_path: Path):
    repo, base, head = fixture_repo(tmp_path)
    manifest, root = setup_baseline(tmp_path)
    command = [sys.executable, "-c", "import json; print(json.dumps({'views': []}))"]
    try:
        run_producer(repo, "0046", base, head, manifest, root,
                     tmp_path / "reports" / "visual.json", 0.0, command)
    except ValueError as exc:
        assert "exactly match" in str(exc)
    else:
        raise AssertionError("mismatched capture views must fail closed")
