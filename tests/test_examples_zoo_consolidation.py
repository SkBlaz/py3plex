"""Regression tests for DSL examples zoo consolidation."""

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_dsl_query_zoo_folder_removed():
    """Legacy dsl_query_zoo directory should be removed after consolidation."""
    assert not (REPO_ROOT / "examples" / "dsl_query_zoo").exists()


def test_query_zoo_helpers_live_in_dsl_zoo():
    """Query zoo helper modules should now live in examples/dsl_zoo."""
    assert (REPO_ROOT / "examples" / "dsl_zoo" / "datasets.py").is_file()
    assert (REPO_ROOT / "examples" / "dsl_zoo" / "queries.py").is_file()


def test_docs_updated_to_consolidated_folder():
    """Primary docs should point to examples/dsl_zoo instead of dsl_query_zoo."""
    files = [
        REPO_ROOT / "docfiles" / "examples" / "index.rst",
        REPO_ROOT / "docfiles" / "how-to" / "query_zoo.rst",
        REPO_ROOT / "docfiles" / "user_guide" / "dsl.rst",
        REPO_ROOT / "book" / "part3_dsl" / "chapter08_intro_dsl.rst",
    ]

    for file_path in files:
        content = file_path.read_text(encoding="utf-8")
        assert "examples/dsl_query_zoo" not in content
        assert "dsl_query_zoo/" not in content
        assert "dsl_zoo" in content
