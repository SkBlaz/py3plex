import tempfile
import sys
from pathlib import Path

import pytest

from docfiles import check_api_consistency as cac


def test_check_file_reports_missing_sections_and_hints(tmp_path):
    source = """
class PublicClass:
    def method(self, value):
        \"\"\"Docstring lacking sections.\"\"\"
        return value


def public_fn(x, y):
    \"\"\"Summary.

    Args:
        x: first value

    Returns:
        int
    \"\"\"
    return x + y


def _private(z):
    return z
"""
    path = tmp_path / "sample.py"
    path.write_text(source)

    issues = cac.check_file(path)

    issue_pairs = {(issue["type"], issue["name"]) for issue in issues}
    expected_pairs = {
        ("missing_docstring", "class PublicClass"),
        ("missing_args_doc", "PublicClass.method"),
        ("missing_returns_doc", "PublicClass.method"),
        ("missing_example", "PublicClass.method"),
        ("missing_type_hints", "PublicClass.method"),
        ("missing_example", "public_fn"),
        ("missing_type_hints", "public_fn"),
    }
    assert issue_pairs == expected_pairs

    hint_messages = {
        issue["name"]: issue["message"]
        for issue in issues
        if issue["type"] == "missing_type_hints"
    }
    assert "value" in hint_messages["PublicClass.method"]
    assert "x, y" in hint_messages["public_fn"]


def test_check_file_allows_init_without_type_hints_or_returns(tmp_path):
    source = """
class WithInit:
    \"\"\"Docstring present.\"\"\"

    def __init__(self, value):
        \"\"\"Init missing Args and Example.\"\"\"
        return value


class NoDoc:
    def __init__(self):
        pass
"""
    path = tmp_path / "init_sample.py"
    path.write_text(source)

    issues = cac.check_file(path)

    issue_pairs = {(issue["type"], issue["name"]) for issue in issues}

    # __init__ should not trigger missing_type_hints or missing_returns_doc
    assert issue_pairs == {
        ("missing_args_doc", "WithInit.__init__"),
        ("missing_docstring", "class NoDoc"),
        ("missing_docstring", "NoDoc.__init__"),
    }


def test_check_file_reports_syntax_error(tmp_path):
    bad_file = tmp_path / "bad.py"
    bad_file.write_text("def broken(:\n    pass\n")

    issues = cac.check_file(bad_file)
    assert len(issues) == 1
    issue = issues[0]
    assert issue["type"] == "syntax_error"
    assert "bad.py" in issue["location"]
    assert "syntax" in issue["message"]


def test_check_file_handles_generic_exception(monkeypatch, tmp_path):
    target = tmp_path / "ok.py"
    target.write_text("x = 1\n")

    def raise_value_error(*args, **kwargs):
        raise ValueError("boom")

    monkeypatch.setattr(cac.ast, "parse", raise_value_error)

    issues = cac.check_file(target)
    assert len(issues) == 1
    issue = issues[0]
    assert issue["type"] == "error"
    assert "boom" in issue["message"]
    assert issue["name"] == "ok.py"


def test_find_python_files_excludes_patterns(tmp_path):
    with tempfile.TemporaryDirectory(prefix="apicheck") as tmpdir:
        root = Path(tmpdir)
        keep = root / "keep.py"
        keep.write_text("x = 1\n")

        skip1 = root / "test_skip.py"
        skip1.write_text("x = 1\n")

        skip2 = root / "module_test.py"
        skip2.write_text("x = 1\n")

        cache_dir = root / "__pycache__"
        cache_dir.mkdir()
        cached = cache_dir / "cached.py"
        cached.write_text("x = 1\n")

        nested_dir = root / "nested"
        nested_dir.mkdir()
        nested_keep = nested_dir / "nested_keep.py"
        nested_keep.write_text("x = 1\n")

        found = cac.find_python_files(root, ["__pycache__", "test_", "_test"])
        found_names = {path.name for path in found}

        assert found_names == {"keep.py", "nested_keep.py"}


def test_main_returns_error_code_with_fail_on_error(monkeypatch, capsys):
    monkeypatch.setattr(
        cac,
        "find_python_files",
        lambda root, patterns: [Path("fake.py")],
    )
    monkeypatch.setattr(
        cac,
        "check_file",
        lambda filepath: [
            {
                "type": "missing_docstring",
                "location": "fake.py:1",
                "name": "foo",
                "message": "missing docstring",
            }
        ],
    )
    monkeypatch.setattr(sys, "argv", ["prog", "--verbose", "--fail-on-error"])

    exit_code = cac.main()
    out = capsys.readouterr().out

    assert exit_code == 1
    assert "Total issues found: 1" in out
    assert "fake.py:1" in out
    assert "foo: missing docstring" in out


def test_main_ok_when_no_files(monkeypatch, capsys):
    monkeypatch.setattr(cac, "find_python_files", lambda root, patterns: [])
    monkeypatch.setattr(sys, "argv", ["prog"])

    exit_code = cac.main()
    out = capsys.readouterr().out

    assert exit_code == 0
    assert "[OK] No API consistency issues found!" in out


def test_main_with_module_file_uses_specific_file(monkeypatch, capsys):
    temp_module = Path(__file__).resolve().parent.parent / "py3plex" / "_temp_api_module.py"
    temp_module.write_text("def public_fn(x):\n    return x\n")
    monkeypatch.setattr(sys, "argv", ["prog", "--module", "_temp_api_module", "--verbose"])
    try:
        exit_code = cac.main()
        out = capsys.readouterr().out
    finally:
        temp_module.unlink(missing_ok=True)

    assert exit_code == 0  # fail-on-error not set
    assert "Total issues found: 2" in out
    assert str(temp_module) in out
    assert "public_fn: Public function missing docstring" in out


def test_main_exits_when_module_missing(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["prog", "--module", "nonexistent_mod"])
    with pytest.raises(SystemExit) as excinfo:
        cac.main()

    assert excinfo.value.code == 1
    assert "Error: Module nonexistent_mod not found" in capsys.readouterr().out
