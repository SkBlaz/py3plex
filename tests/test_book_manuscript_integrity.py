from pathlib import Path
import tomllib


BOOK_ROOT = Path(__file__).resolve().parents[1] / "book"
REPO_ROOT = BOOK_ROOT.parent


def _read(path: str) -> str:
    return (BOOK_ROOT / path).read_text(encoding="utf-8")


def test_front_matter_uses_canonical_version():
    text = _read("front_matter.rst")
    assert "version 2.0.0 (2026)" in text
    assert "version 1.0 (2025)" not in text


def test_book_version_matches_project_version():
    project_data = tomllib.loads((BOOK_ROOT.parent / "pyproject.toml").read_text(encoding="utf-8"))
    project_version = project_data["project"]["version"]
    assert f"version {project_version} (2026)" in _read("front_matter.rst")
    assert f"Version {project_version}" in _read("bibliography.rst")


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
        stale = [root for root in old_roots if root in content]
        assert not stale, f"Found stale paths {stale} in {rst}"


def test_case_study_3_is_authored_and_not_template_placeholder():
    text = _read("part4_case_studies/chapter14_case_study_3.rst")
    assert "workflow template" not in text
    assert "transportation resilience claims" in text
    assert "when completed" not in text
    assert "To complete:" not in text


def test_book_mentions_current_repository_subsystems():
    combined_book = "\n".join(
        path.read_text(encoding="utf-8") for path in BOOK_ROOT.rglob("*.rst")
    )
    expected_subsystems = {
        "py3plex/algebra": "py3plex/algebra",
        "py3plex/embeddings": "py3plex/embeddings",
        "py3plex/dsl/lint": "py3plex/dsl/lint",
        "py3plex/dsl/program": "py3plex/dsl/program",
        "py3plex/experiments": "py3plex/experiments",
        "py3plex/meta": "py3plex/meta",
        "py3plex/out_of_core": "py3plex/out_of_core",
        "py3plex/optimizer": "py3plex/optimizer",
        "py3plex/ml/embedding": "py3plex/ml/embedding",
    }

    for path, mention in expected_subsystems.items():
        assert (REPO_ROOT / path).exists(), f"Expected subsystem path missing: {path}"
        assert mention in combined_book, f"Book does not mention current subsystem {mention}"


def test_book_points_to_current_addition_examples():
    combined_book = "\n".join(
        path.read_text(encoding="utf-8") for path in BOOK_ROOT.rglob("*.rst")
    )
    expected_examples = [
        "examples/out_of_core/",
        "examples/advanced/example_graph_program.py",
        "examples/advanced/example_rewrite_engine.py",
        "examples/advanced/example_metapath2vec.py",
    ]

    for example in expected_examples:
        assert (REPO_ROOT / example.rstrip("/")).exists(), f"Expected example missing: {example}"
        assert example in combined_book, f"Book does not point to current example {example}"
