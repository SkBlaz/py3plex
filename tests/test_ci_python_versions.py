from pathlib import Path


def test_main_tests_workflow_includes_python_313_and_drops_38():
    workflow = Path(__file__).resolve().parents[1] / ".github/workflows/tests.yml"
    text = workflow.read_text(encoding="utf-8")

    assert 'python-version: ["3.9", "3.10", "3.11", "3.12", "3.13"]' in text
    assert "python-version: \"3.8\"" not in text


def test_pyproject_classifiers_include_python_313():
    pyproject = Path(__file__).resolve().parents[1] / "pyproject.toml"
    text = pyproject.read_text(encoding="utf-8")

    assert "Programming Language :: Python :: 3.13" in text
