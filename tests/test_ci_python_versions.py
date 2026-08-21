from pathlib import Path


def test_main_tests_workflow_includes_python_313_and_drops_38():
    workflow = Path(__file__).resolve().parents[1] / ".github/workflows/tests.yml"
    text = workflow.read_text(encoding="utf-8")

    assert 'python-version: ["3.9", "3.10", "3.11", "3.12", "3.13"]' in text
    assert "python-version: \"3.8\"" not in text


def test_main_tests_workflow_does_not_cache_cleared_venv():
    workflow = Path(__file__).resolve().parents[1] / ".github/workflows/tests.yml"
    text = workflow.read_text(encoding="utf-8")
    cache_step = text.split("- name: Cache uv dependencies", 1)[1].split(
        "- name: Install system dependencies", 1
    )[0]

    assert "uses: actions/cache@v4" in cache_step
    assert "path: ~/.cache/uv" in cache_step
    assert ".venv" not in cache_step


def test_pyproject_classifiers_include_python_313():
    pyproject = Path(__file__).resolve().parents[1] / "pyproject.toml"
    text = pyproject.read_text(encoding="utf-8")

    assert "Programming Language :: Python :: 3.13" in text
