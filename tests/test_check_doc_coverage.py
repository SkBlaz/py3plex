import ast
import json
import sys
import tempfile
import textwrap
from pathlib import Path

import pytest

import docfiles.check_doc_coverage as cdc


def test_function_collector_skips_private_and_keeps_init():
    source = textwrap.dedent(
        """
        class Public:
            def __init__(self):
                pass

            def method(self):
                pass

            def _hidden(self):
                pass


        def top_level():
            pass


        def _private():
            pass


        class _PrivateClass:
            def method(self):
                pass
        """
    )

    tree = ast.parse(source)
    collector = cdc.FunctionCollector("file.py", "py3plex.module")
    collector.visit(tree)

    assert collector.classes == {"py3plex.module.Public"}
    assert collector.functions == {
        "py3plex.module.Public.__init__",
        "py3plex.module.Public.method",
        "py3plex.module.top_level",
    }


def test_collect_functions_from_code_skips_patterns_and_syntax_error():
    with tempfile.TemporaryDirectory(prefix="proj") as tempdir:
        project_root = Path(tempdir)
        py_dir = project_root / "py3plex"
        py_dir.mkdir(parents=True)

        good_file = py_dir / "good.py"
        good_file.write_text(
            textwrap.dedent(
                """
                class Public:
                    def __init__(self):
                        pass

                    def visible(self):
                        pass

                    def _hidden(self):
                        pass


                def top_fn():
                    pass


                def _internal():
                    pass
                """
            )
        )

        # Excluded by name pattern
        skip_file = py_dir / "test_skip.py"
        skip_file.write_text("def should_not_count():\n    pass\n")

        # Syntax error should be ignored, not raised
        bad_file = py_dir / "bad.py"
        bad_file.write_text("def broken(:\n    pass\n")

        functions, classes = cdc.collect_functions_from_code(py_dir)

        assert classes == {"py3plex.good.Public"}
        assert functions == {
            "py3plex.good.Public.__init__",
            "py3plex.good.Public.visible",
            "py3plex.good.top_fn",
        }


def test_collect_documented_items_from_rst_handles_directives_and_members():
    with tempfile.TemporaryDirectory(prefix="proj") as tempdir:
        project_root = Path(tempdir)
        py_dir = project_root / "py3plex"
        doc_dir = project_root / "docfiles"
        py_dir.mkdir(parents=True)
        doc_dir.mkdir()

        # Module documented via autofunction/automethod/autoclass and automodule :members:
        mod = py_dir / "mod.py"
        mod.write_text(
            textwrap.dedent(
                """
                def func_a():
                    pass


                class MyClass:
                    def __init__(self):
                        pass

                    def method_a(self):
                        pass
                """
            )
        )

        # Package documented via automodule :members:
        pack_dir = py_dir / "pack"
        pack_dir.mkdir()
        (pack_dir / "__init__.py").write_text(
            textwrap.dedent(
                """
                def pack_func():
                    pass


                class PackClass:
                    def __init__(self):
                        pass
                """
            )
        )

        doc = doc_dir / "index.rst"
        doc.write_text(
            textwrap.dedent(
                """
                .. autofunction:: py3plex.mod.func_a

                .. automethod:: py3plex.mod.MyClass.method_a

                .. autoclass:: py3plex.mod.MyClass

                .. automodule:: py3plex.mod
                   :members:

                .. automodule:: py3plex.pack
                   :members:
                """
            )
        )

        documented_functions, documented_classes = cdc.collect_documented_items_from_rst(
            doc_dir, py_dir
        )

        assert {
            "py3plex.mod.func_a",
            "py3plex.mod.MyClass.method_a",
            "py3plex.pack.pack_func",
        }.issubset(documented_functions)

        assert {
            "py3plex.mod.MyClass",
            "py3plex.pack.PackClass",
        }.issubset(documented_classes)


def test_calculate_coverage_handles_empty_and_partial_sets():
    assert cdc.calculate_coverage(set(), set()) == (100.0, 0)

    coverage, count = cdc.calculate_coverage({"a", "b", "c"}, {"b"})
    assert count == 1
    assert coverage == pytest.approx(33.333333, rel=1e-3)


def test_generate_badge_url_color_thresholds():
    cases = [
        (80, "brightgreen"),
        (60, "green"),
        (40, "yellow"),
        (20, "orange"),
        (0, "red"),
    ]

    for value, color in cases:
        url = cdc.generate_badge_url(value)
        assert color in url
        assert "docs%20coverage" in url


def test_find_undocumented_items_sorted():
    missing = cdc.find_undocumented_items({"b", "a", "c"}, {"a", "c"})
    assert missing == ["b"]


def test_main_emits_badge_only(monkeypatch, capsys):
    with tempfile.TemporaryDirectory(prefix="proj") as tempdir:
        project_root = Path(tempdir)
        doc_dir = project_root / "docfiles"
        py_dir = project_root / "py3plex"
        doc_dir.mkdir(parents=True)
        py_dir.mkdir()

        (py_dir / "mod.py").write_text("def func():\n    pass\n")
        (doc_dir / "index.rst").write_text(".. autofunction:: py3plex.mod.func\n")

        fake_script = doc_dir / "check_doc_coverage.py"
        fake_script.write_text("# stub\n")

        monkeypatch.setattr(cdc, "__file__", str(fake_script))
        monkeypatch.setattr(sys, "argv", ["prog", "--badge-only"])

        exit_code = cdc.main()
        out = capsys.readouterr().out.strip()

        expected = cdc.generate_badge_url(100.0)
        assert exit_code == 0
        assert out == expected


def test_main_fails_under_threshold(monkeypatch, capsys):
    with tempfile.TemporaryDirectory(prefix="proj") as tempdir:
        project_root = Path(tempdir)
        doc_dir = project_root / "docfiles"
        py_dir = project_root / "py3plex"
        doc_dir.mkdir(parents=True)
        py_dir.mkdir()

        # Undocumented function to keep coverage at 0%
        (py_dir / "mod.py").write_text("def func():\n    pass\n")
        (doc_dir / "index.rst").write_text("\n")

        fake_script = doc_dir / "check_doc_coverage.py"
        fake_script.write_text("# stub\n")

        monkeypatch.setattr(cdc, "__file__", str(fake_script))
        monkeypatch.setattr(sys, "argv", ["prog", "--fail-under", "50"])

        exit_code = cdc.main()
        out = capsys.readouterr().out

        assert exit_code == 1
        assert "ERROR: Coverage 0.0% is below threshold 50.0%" in out


def test_main_errors_when_py3plex_missing(monkeypatch, tmp_path):
    doc_dir = tmp_path / "docfiles"
    doc_dir.mkdir()
    fake_script = doc_dir / "check_doc_coverage.py"
    fake_script.write_text("# stub\n")

    monkeypatch.setattr(cdc, "__file__", str(fake_script))
    monkeypatch.setattr(sys, "argv", ["prog"])

    with pytest.raises(SystemExit) as excinfo:
        cdc.main()

    assert excinfo.value.code == 1


def test_main_errors_when_docfiles_missing(monkeypatch, capsys, tmp_path):
    # py3plex present but docfiles missing triggers stderr + exit
    py_dir = tmp_path / "py3plex"
    py_dir.mkdir()
    script_dir = tmp_path / "scripts"
    script_dir.mkdir()
    fake_script = script_dir / "check_doc_coverage.py"
    fake_script.write_text("# stub\n")

    monkeypatch.setattr(cdc, "__file__", str(fake_script))
    monkeypatch.setattr(sys, "argv", ["prog"])

    with pytest.raises(SystemExit) as excinfo:
        cdc.main()

    err = capsys.readouterr().err
    assert excinfo.value.code == 1
    assert f"Error: docfiles directory not found at {tmp_path / 'docfiles'}" in err


def test_main_json_output_and_verbose_lists_missing(monkeypatch, capsys):
    with tempfile.TemporaryDirectory(prefix="proj") as tempdir:
        project_root = Path(tempdir)
        doc_dir = project_root / "docfiles"
        py_dir = project_root / "py3plex"
        doc_dir.mkdir(parents=True)
        py_dir.mkdir()

        # One documented, one undocumented
        (py_dir / "mod.py").write_text(
            textwrap.dedent(
                """
                def documented():
                    pass

                def undocumented():
                    pass
                """
            )
        )
        (doc_dir / "index.rst").write_text(".. autofunction:: py3plex.mod.documented\n")

        fake_script = doc_dir / "check_doc_coverage.py"
        fake_script.write_text("# stub\n")

        output_json = project_root / "result.json"

        monkeypatch.setattr(cdc, "__file__", str(fake_script))
        monkeypatch.setattr(
            sys,
            "argv",
            ["prog", "--json", str(output_json), "--verbose", "--fail-under", "0"],
        )

        exit_code = cdc.main()
        out = capsys.readouterr().out

        assert exit_code == 0
        # JSON written with both totals
        data = json.loads(output_json.read_text())
        assert data["total_functions"] == 2
        assert data["documented_functions"] == 1
        assert data["badge_url"] == cdc.generate_badge_url(data["overall_coverage"])
        # Verbose output lists the missing function
        assert "undocumented" in out.lower()
        assert "py3plex.mod.undocumented" in out


def test_main_at_threshold_reports_undocumented_classes(monkeypatch, capsys):
    with tempfile.TemporaryDirectory(prefix="proj") as tempdir:
        project_root = Path(tempdir)
        doc_dir = project_root / "docfiles"
        py_dir = project_root / "py3plex"
        doc_dir.mkdir(parents=True)
        py_dir.mkdir()

        (py_dir / "mod.py").write_text(
            textwrap.dedent(
                """
                def documented():
                    pass


                class Undocumented:
                    pass
                """
            )
        )
        (doc_dir / "index.rst").write_text(".. autofunction:: py3plex.mod.documented\n")

        fake_script = doc_dir / "check_doc_coverage.py"
        fake_script.write_text("# stub\n")

        monkeypatch.setattr(cdc, "__file__", str(fake_script))
        monkeypatch.setattr(sys, "argv", ["prog", "--verbose", "--fail-under", "50"])

        exit_code = cdc.main()
        out = capsys.readouterr().out

        assert exit_code == 0  # threshold is inclusive
        assert "Overall documentation coverage: 50.0%" in out
        assert "Undocumented Classes (1)" in out
        assert "py3plex.mod.Undocumented" in out
