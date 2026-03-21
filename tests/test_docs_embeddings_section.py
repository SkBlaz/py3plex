from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_main_docs_index_includes_embeddings_section_entry():
    index_path = REPO_ROOT / "docfiles" / "index.rst"
    assert index_path.exists()
    content = index_path.read_text(encoding="utf-8")

    assert "Part VI: Examples, Recipes & Embeddings" in content
    assert "user_guide/random_walks_embeddings" in content
    assert ":caption: Examples, Recipes & Embeddings" in content


def test_api_index_documents_core_embedding_modules():
    api_index_path = REPO_ROOT / "docfiles" / "reference" / "api_index.rst"
    assert api_index_path.exists()
    content = api_index_path.read_text(encoding="utf-8")

    expected_modules = [
        "py3plex.ml.embedding.base",
        "py3plex.ml.embedding.trainer",
        "py3plex.ml.embedding.node2vec",
        "py3plex.ml.embedding.deepwalk",
        "py3plex.ml.embedding.netmf",
        "py3plex.ml.embedding.line",
        "py3plex.ml.embedding.metapath2vec",
    ]

    for module in expected_modules:
        assert module in content, f"Module {module} not found in API index"
