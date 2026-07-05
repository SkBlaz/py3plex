from pathlib import Path
import tomllib


BOOK_ROOT = Path(__file__).resolve().parents[1] / "book"
REPO_ROOT = BOOK_ROOT.parent

BOOK_DOCUMENTED_PACKAGE_LANDMARKS = {
    "algebra",
    "algorithms",
    "centrality",
    "core",
    "dsl",
    "dynamics",
    "embeddings",
    "experiments",
    "io",
    "meta",
    "ml",
    "optimizer",
    "out_of_core",
    "semiring",
    "uncertainty",
    "visualization",
}

SUPPORTING_OR_SPECIALIZED_PACKAGE_DIRS = {
    "alignment",
    "benchmarks",
    "claims",
    "comparison",
    "compat",
    "contracts",
    "counterexamples",
    "counterfactual",
    "datasets",
    "diagnostics",
    "lab",
    "multinet",
    "nullmodels",
    "paths",
    "plugins",
    "provenance",
    "robustness",
    "runtime",
    "selection",
    "sensitivity",
    "stats",
    "wrappers",
}

BOOK_DOCUMENTED_NESTED_LANDMARKS = {
    "py3plex/dsl/lint",
    "py3plex/dsl/program",
    "py3plex/ml/embedding",
}

BOOK_DOCUMENTED_EXAMPLE_FOLDERS = {
    "advanced",
    "dsl_zoo",
    "getting_started",
    "io_and_data",
    "network_analysis",
    "out_of_core",
    "pipelines",
    "visualization",
}

NON_PUBLIC_EXAMPLE_FOLDERS = {"docs_outputs"}


def _read(path: str) -> str:
    return (BOOK_ROOT / path).read_text(encoding="utf-8")


def _combined_book_text() -> str:
    return "\n".join(path.read_text(encoding="utf-8") for path in BOOK_ROOT.rglob("*.rst"))


def _book_mentions_package_dir(combined_book: str, package_dir: str) -> bool:
    return f"py3plex/{package_dir}" in combined_book or f"``{package_dir}/``" in combined_book


def test_front_matter_uses_canonical_version():
    text = _read("front_matter.rst")
    assert "version 2.0.1 (2026)" in text
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
    combined_book = _combined_book_text()

    for package in sorted(BOOK_DOCUMENTED_PACKAGE_LANDMARKS):
        path = f"py3plex/{package}"
        assert (REPO_ROOT / path).exists(), f"Expected subsystem path missing: {path}"
        assert _book_mentions_package_dir(combined_book, package), (
            f"Book does not mention current subsystem {path}"
        )

    for path in sorted(BOOK_DOCUMENTED_NESTED_LANDMARKS):
        assert (REPO_ROOT / path).exists(), f"Expected subsystem path missing: {path}"
        assert path in combined_book, f"Book does not mention current subsystem {path}"


def test_package_landmarks_are_classified_for_book_coverage():
    actual_package_dirs = {
        path.name
        for path in (REPO_ROOT / "py3plex").iterdir()
        if path.is_dir() and not path.name.startswith("__")
    }
    classified = BOOK_DOCUMENTED_PACKAGE_LANDMARKS | SUPPORTING_OR_SPECIALIZED_PACKAGE_DIRS

    assert actual_package_dirs == classified, (
        "Top-level py3plex package directories must be classified. "
        "If a new high-level subsystem is added, add it to "
        "BOOK_DOCUMENTED_PACKAGE_LANDMARKS and mention it in the book; "
        "otherwise classify it as a supporting/specialized package."
    )


def test_book_points_to_current_addition_examples():
    combined_book = _combined_book_text()
    expected_examples = [
        "examples/out_of_core/",
        "examples/advanced/example_graph_program.py",
        "examples/advanced/example_rewrite_engine.py",
        "examples/advanced/example_metapath2vec.py",
    ]

    for example in expected_examples:
        assert (REPO_ROOT / example.rstrip("/")).exists(), f"Expected example missing: {example}"
        assert example in combined_book, f"Book does not point to current example {example}"


def test_public_example_folders_are_covered_by_book_map():
    actual_example_dirs = {
        path.name
        for path in (REPO_ROOT / "examples").iterdir()
        if path.is_dir() and not path.name.startswith("__")
    }
    classified = BOOK_DOCUMENTED_EXAMPLE_FOLDERS | NON_PUBLIC_EXAMPLE_FOLDERS
    combined_book = _combined_book_text()

    assert actual_example_dirs == classified, (
        "Example folders must be classified. Public example folders should be "
        "added to BOOK_DOCUMENTED_EXAMPLE_FOLDERS and mentioned in the book."
    )

    for folder in sorted(BOOK_DOCUMENTED_EXAMPLE_FOLDERS):
        example_path = f"examples/{folder}/"
        assert example_path in combined_book, f"Book does not mention {example_path}"
