import json
import subprocess
import sys
import textwrap
from pathlib import Path
from types import SimpleNamespace

import pytest

import docfiles.check_type_coverage as ctc


def test_run_mypy_coverage_invokes_subprocess(monkeypatch, tmp_path):
    calls = []

    def fake_run(cmd, capture_output, text, timeout):
        calls.append(
            {
                "cmd": cmd,
                "capture_output": capture_output,
                "text": text,
                "timeout": timeout,
            }
        )
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(ctc.subprocess, "run", fake_run)

    package = tmp_path / "pkg"
    package.mkdir()

    report_path, code = ctc.run_mypy_coverage(package, tmp_path)

    assert code == 0
    assert report_path == str(tmp_path / "txt" / "index.txt")

    assert len(calls) == 1
    cmd = calls[0]["cmd"]
    assert cmd[:2] == ["mypy", str(package)]
    assert "--lineprecision-report" in cmd
    assert "--html-report" in cmd
    assert "--txt-report" in cmd
    assert "--any-exprs-report" in cmd
    assert calls[0]["capture_output"] is True
    assert calls[0]["text"] is True
    assert calls[0]["timeout"] == 300


def test_run_mypy_coverage_times_out(monkeypatch, tmp_path, capsys):
    def fake_run(cmd, capture_output, text, timeout):
        raise subprocess.TimeoutExpired(cmd, timeout)

    monkeypatch.setattr(ctc.subprocess, "run", fake_run)

    pkg = tmp_path / "pkg"
    pkg.mkdir()

    with pytest.raises(SystemExit) as excinfo:
        ctc.run_mypy_coverage(pkg, tmp_path)

    assert excinfo.value.code == 1
    assert "mypy timed out" in capsys.readouterr().err


def test_run_mypy_coverage_missing_binary(monkeypatch, tmp_path, capsys):
    def fake_run(cmd, capture_output, text, timeout):
        raise FileNotFoundError("mypy missing")

    monkeypatch.setattr(ctc.subprocess, "run", fake_run)

    pkg = tmp_path / "pkg"
    pkg.mkdir()

    with pytest.raises(SystemExit) as excinfo:
        ctc.run_mypy_coverage(pkg, tmp_path)

    assert excinfo.value.code == 1
    assert "mypy not found" in capsys.readouterr().err


def test_parse_linecount_report_parses_totals_and_modules(tmp_path):
    report = tmp_path / "index.txt"
    report.write_text(
        textwrap.dedent(
            """
            | py3plex.alpha | 10.00% imprecise | 100 LOC |
            | py3plex.beta  | 50.00% imprecise |  20 LOC |
            | Total         | 25.00% imprecise | 120 LOC |
            """
        )
    )

    metrics = ctc.parse_linecount_report(str(report))

    assert metrics["total_loc"] == 120
    assert metrics["precise_loc"] == 90
    assert metrics["imprecise_loc"] == 30
    assert metrics["precise_percent"] == 75.0
    assert metrics["imprecise_percent"] == 25.0

    assert [m["name"] for m in metrics["modules"]] == [
        "py3plex.alpha",
        "py3plex.beta",
    ]
    assert metrics["modules"][0]["precise_percent"] == 90.0
    assert metrics["modules"][1]["imprecise_loc"] == 10


def test_parse_linecount_report_errors_when_missing_file(tmp_path, capsys):
    missing = tmp_path / "does_not_exist.txt"

    with pytest.raises(SystemExit) as excinfo:
        ctc.parse_linecount_report(str(missing))

    assert excinfo.value.code == 1
    assert "Report file not found" in capsys.readouterr().err


def test_parse_linecount_report_errors_without_total_line(tmp_path, capsys):
    report = tmp_path / "index.txt"
    report.write_text("no totals here\n")

    with pytest.raises(SystemExit) as excinfo:
        ctc.parse_linecount_report(str(report))

    assert excinfo.value.code == 1
    assert "Could not parse total coverage" in capsys.readouterr().err


@pytest.mark.parametrize(
    "value,color",
    [
        (95, "brightgreen"),
        (85, "green"),
        (70, "yellowgreen"),
        (65, "yellow"),
        (50, "orange"),
        (30, "red"),
    ],
)
def test_generate_badge_url_color_thresholds(value, color):
    url = ctc.generate_badge_url(value)
    assert color in url
    assert f"{value:.1f}%25" in url


def test_format_top_imprecise_modules_sorts_and_truncates():
    modules = [
        {"name": "py3plex.beta", "imprecise_percent": 20.0, "total_loc": 50},
        {"name": "py3plex.alpha", "imprecise_percent": 50.0, "total_loc": 10},
        {"name": "py3plex.gamma", "imprecise_percent": 5.0, "total_loc": 5},
    ]

    output = ctc.format_top_imprecise_modules(modules, top_n=2)

    assert "Top 2 Most Imprecise Modules" in output
    assert output.index("py3plex.alpha") < output.index("py3plex.beta")
    assert "py3plex.gamma" not in output


def test_main_badge_only_uses_metrics(monkeypatch, capsys, tmp_path):
    project_root = tmp_path
    doc_dir = project_root / "docfiles"
    pkg_dir = project_root / "py3plex"
    doc_dir.mkdir()
    pkg_dir.mkdir()

    fake_script = doc_dir / "check_type_coverage.py"
    fake_script.write_text("# stub\n")

    monkeypatch.setattr(ctc, "__file__", str(fake_script))

    run_calls = []

    def fake_run(pkg_path, temp_dir):
        run_calls.append((pkg_path, temp_dir))
        return str(temp_dir / "txt" / "index.txt"), 0

    monkeypatch.setattr(ctc, "run_mypy_coverage", fake_run)

    parse_calls = []
    metrics = {
        "total_loc": 10,
        "precise_loc": 8,
        "imprecise_loc": 2,
        "precise_percent": 80.0,
        "imprecise_percent": 20.0,
        "modules": [],
    }

    monkeypatch.setattr(
        ctc, "parse_linecount_report", lambda path: parse_calls.append(path) or metrics
    )

    seen_coverage = []

    def fake_badge(value):
        seen_coverage.append(value)
        return f"badge-{value}"

    monkeypatch.setattr(ctc, "generate_badge_url", fake_badge)
    monkeypatch.setattr(sys, "argv", ["prog", "--badge-only"])

    ctc.main()

    out = capsys.readouterr().out.strip()

    assert out == "badge-80.0"
    assert seen_coverage == [80.0]
    assert len(run_calls) == 1
    assert run_calls[0][0] == pkg_dir
    assert parse_calls[0].endswith("index.txt")


def test_main_json_and_verbose_warns_when_low_coverage(monkeypatch, capsys, tmp_path):
    project_root = tmp_path
    doc_dir = project_root / "docfiles"
    pkg_dir = project_root / "py3plex"
    doc_dir.mkdir()
    pkg_dir.mkdir()

    output_json = project_root / "type_metrics.json"

    fake_script = doc_dir / "check_type_coverage.py"
    fake_script.write_text("# stub\n")
    monkeypatch.setattr(ctc, "__file__", str(fake_script))

    monkeypatch.setattr(
        ctc,
        "run_mypy_coverage",
        lambda pkg_path, temp_dir: (str(temp_dir / "txt" / "index.txt"), 0),
    )

    metrics = {
        "total_loc": 200,
        "precise_loc": 90,
        "imprecise_loc": 110,
        "precise_percent": 45.678,
        "imprecise_percent": 54.322,
        "modules": [
            {
                "name": "py3plex.alpha",
                "imprecise_percent": 80.0,
                "precise_percent": 20.0,
                "total_loc": 50,
                "imprecise_loc": 40,
                "precise_loc": 10,
            }
        ],
    }
    monkeypatch.setattr(ctc, "parse_linecount_report", lambda path: metrics)

    monkeypatch.setattr(
        sys, "argv", ["prog", "--json", str(output_json), "--verbose"]
    )

    with pytest.raises(SystemExit) as excinfo:
        ctc.main()

    assert excinfo.value.code == 0

    captured = capsys.readouterr()
    assert "TYPE COVERAGE REPORT" in captured.out
    assert "Top 20 Most Imprecise Modules" in captured.out
    assert "py3plex.alpha" in captured.out
    assert "Warning: Type coverage is below 50" in captured.err

    data = json.loads(output_json.read_text())
    assert data["total_loc"] == 200
    assert data["precise_loc"] == 90
    assert data["imprecise_loc"] == 110
    assert data["precise_percent"] == 45.68
    assert data["imprecise_percent"] == 54.32
    assert data["badge_url"] == ctc.generate_badge_url(metrics["precise_percent"])
    assert data["modules"] == metrics["modules"]


def test_main_errors_when_package_missing(monkeypatch, tmp_path, capsys):
    doc_dir = tmp_path / "docfiles"
    doc_dir.mkdir()
    fake_script = doc_dir / "check_type_coverage.py"
    fake_script.write_text("# stub\n")

    monkeypatch.setattr(ctc, "__file__", str(fake_script))
    monkeypatch.setattr(sys, "argv", ["prog"])

    with pytest.raises(SystemExit) as excinfo:
        ctc.main()

    assert excinfo.value.code == 1
    assert "Package not found" in capsys.readouterr().err


def test_main_succeeds_without_warning_when_coverage_high(
    monkeypatch, tmp_path, capsys
):
    project_root = tmp_path
    doc_dir = project_root / "docfiles"
    pkg_dir = project_root / "py3plex"
    doc_dir.mkdir()
    pkg_dir.mkdir()

    fake_script = doc_dir / "check_type_coverage.py"
    fake_script.write_text("# stub\n")

    monkeypatch.setattr(ctc, "__file__", str(fake_script))

    run_calls = []

    def fake_run(pkg_path, temp_dir):
        run_calls.append(pkg_path)
        return str(temp_dir / "txt" / "index.txt"), 0

    monkeypatch.setattr(ctc, "run_mypy_coverage", fake_run)

    metrics = {
        "total_loc": 100,
        "precise_loc": 80,
        "imprecise_loc": 20,
        "precise_percent": 80.0,
        "imprecise_percent": 20.0,
        "modules": [
            {"name": "py3plex.alpha", "imprecise_percent": 20.0, "total_loc": 50}
        ],
    }
    monkeypatch.setattr(ctc, "parse_linecount_report", lambda path: metrics)

    monkeypatch.setattr(sys, "argv", ["prog"])

    with pytest.raises(SystemExit) as excinfo:
        ctc.main()

    assert excinfo.value.code == 0

    captured = capsys.readouterr()
    assert "TYPE COVERAGE REPORT" in captured.out
    assert "Type Coverage:            80.00%" in captured.out
    assert "Warning" not in captured.err
    assert "Top" not in captured.out  # only shown in verbose mode
    assert run_calls == [pkg_dir]
