from pathlib import Path


BOOK_ROOT = Path(__file__).resolve().parents[1] / "book"


def _read(path: str) -> str:
    return (BOOK_ROOT / path).read_text(encoding="utf-8")


def test_front_matter_uses_canonical_version():
    text = _read("front_matter.rst")
    assert "version 1.1.4 (2025)" in text
    assert "version 1.0 (2025)" not in text


def test_index_uses_single_reference_section():
    text = _read("index.rst")
    assert "bibliography" in text
    assert "citation" not in text


def test_outdated_example_paths_removed_from_book():
    old_roots = [
        "examples/00_quickstart",
        "examples/01_network_construction",
        "examples/02_basic_queries",
        "examples/03_dsl_v2",
        "examples/04_graph_ops",
        "examples/05_communities",
        "examples/06_dynamics",
        "examples/07_uncertainty",
    ]
    for rst in BOOK_ROOT.rglob("*.rst"):
        content = rst.read_text(encoding="utf-8")
        for root in old_roots:
            assert root not in content, f"Found stale path {root} in {rst}"


def test_case_study_3_is_explicitly_template_not_pseudo_result():
    text = _read("part4_case_studies/chapter14_case_study_3.rst")
    assert "workflow template" in text
    assert "when completed" not in text
    assert "To complete:" not in text

