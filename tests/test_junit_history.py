from __future__ import annotations

from pathlib import Path

import pytest

from scripts.junit_history import build_history


SHA = "a" * 40


def write_report(path: Path, body: str) -> None:
    path.write_text(body, encoding="utf-8")


def test_normalizes_nested_junit_statuses_and_durations(tmp_path: Path):
    report = tmp_path / "results.xml"
    write_report(report, """<testsuites><testsuite name="unit">
      <testcase classname="pkg.test" name="ok" time="0.125" />
      <testcase classname="pkg.test" name="bad" time="1.5"><failure /></testcase>
      <testcase classname="pkg.test" name="broken"><error /></testcase>
      <testcase classname="pkg.test" name="later"><skipped /></testcase>
    </testsuite></testsuites>""")
    result = build_history(report, SHA, "b" * 40, "run-1", "2026-09-18T12:00:00-03:00")
    assert result["history_version"] == 1
    assert result["occurred_at"] == "2026-09-18T15:00:00+00:00"
    assert [(item["test_id"], item["status"], item["duration_ms"]) for item in result["tests"]] == [
        ("pkg.test::bad", "fail", 1500), ("pkg.test::broken", "error", 0),
        ("pkg.test::later", "skip", 0), ("pkg.test::ok", "pass", 125)]


def test_preserves_parameterized_ids_with_spaces(tmp_path: Path):
    report = tmp_path / "parameterized.xml"
    write_report(report, "<testsuite><testcase classname='pkg.test' name='case[raise SystemExit(7)]' /></testsuite>")
    result = build_history(report, SHA, SHA, "run with spaces", "2026-09-18T12:00:00Z")
    assert result["tests"][0]["test_id"] == "pkg.test::case[raise SystemExit(7)]"


def test_rejects_duplicate_or_unsafe_reports(tmp_path: Path):
    duplicate = tmp_path / "duplicate.xml"
    write_report(duplicate, "<testsuite><testcase classname='x' name='same'/><testcase classname='x' name='same'/></testsuite>")
    with pytest.raises(ValueError, match="duplicate"):
        build_history(duplicate, SHA, SHA, "run", "2026-09-18T12:00:00Z")
    unsafe = tmp_path / "unsafe.xml"
    write_report(unsafe, "<!DOCTYPE foo [ <!ENTITY xxe SYSTEM 'file:///secret'> ]><testsuite><testcase name='&xxe;'/></testsuite>")
    with pytest.raises(ValueError, match="DTD|entity"):
        build_history(unsafe, SHA, SHA, "run", "2026-09-18T12:00:00Z")


def test_rejects_bad_identity_duration_and_empty_report(tmp_path: Path):
    bad = tmp_path / "bad.xml"
    write_report(bad, "<testsuite><testcase name='x' time='nan'/></testsuite>")
    with pytest.raises(ValueError, match="full hexadecimal"):
        build_history(bad, "short", SHA, "run", "2026-09-18T12:00:00Z")
    with pytest.raises(ValueError, match="out of bounds"):
        build_history(bad, SHA, SHA, "run", "2026-09-18T12:00:00Z")
    empty = tmp_path / "empty.xml"
    write_report(empty, "<testsuite />")
    with pytest.raises(ValueError, match="no testcase"):
        build_history(empty, SHA, SHA, "run", "2026-09-18T12:00:00Z")
