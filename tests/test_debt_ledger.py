from __future__ import annotations

from scripts.debt_ledger import markdown, scan


def test_scan_separates_no_trigger_and_tracked_code(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "service.py").write_text(
        "# TODO(agent): simplify this — see task 0042\n"
        "# FIXME: this has no revisit task\n"
        "value = 1\n",
        encoding="utf-8",
    )
    (tmp_path / "README.md").write_text("TODO in docs\n", encoding="utf-8")
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "ignored.py").write_text("HACK ignored\n", encoding="utf-8")

    report = scan(tmp_path)

    assert report["status"] == "pass"
    assert report["totals"] == {"markers": 2, "no_trigger": 1, "with_trigger": 1}
    assert report["by_kind"] == {"FIXME": 1, "TODO": 1}
    assert report["entries"][0]["classification"] == "no-trigger"
    assert report["entries"][1]["revisit_task"] == "0042"


def test_docs_are_opt_in_and_markdown_prioritizes_no_trigger(tmp_path):
    (tmp_path / "src.py").write_text("# HACK: no task\n", encoding="utf-8")
    (tmp_path / "README.md").write_text("TODO: docs task 0043\n", encoding="utf-8")

    default = scan(tmp_path)
    with_docs = scan(tmp_path, include_docs=True)

    assert default["totals"]["markers"] == 1
    assert with_docs["totals"]["markers"] == 2
    rendered = markdown(with_docs)
    assert rendered.index("## No trigger") < rendered.index("## Tracked")
    assert "src.py:1" in rendered
    assert "README.md:1" in rendered


def test_scan_skips_build_and_archive_outputs(tmp_path):
    for directory in (".git", ".archive", "dist", "build", ".next"):
        target = tmp_path / directory
        target.mkdir()
        (target / "generated.py").write_text("TODO: generated\n", encoding="utf-8")
    report = scan(tmp_path)
    assert report["totals"]["markers"] == 0
