from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_load_and_build_networks_includes_expected_outputs_for_all_creation_methods():
    path = REPO_ROOT / "docfiles" / "how-to" / "load_and_build_networks.rst"
    content = path.read_text(encoding="utf-8")

    assert "Method 2: Add Nodes First" in content
    assert "Method 3: Use Dictionary Format" in content
    assert "Use this pattern when you need explicit node-layer registration before edges." in content
    assert "Number of unique node IDs (across all layers): 4" in content
    assert "Number of unique node IDs (across all layers): 3" in content


def test_query_with_dsl_documents_layer_count_with_concrete_example_and_output():
    path = REPO_ROOT / "docfiles" / "how-to" / "query_with_dsl.rst"
    content = path.read_text(encoding="utf-8")

    assert "Concrete example (using the network built in this page):" in content
    assert "layer_specific = Q.nodes().where(layer_count__eq=1).execute(network)" in content
    assert "connectors = Q.nodes().where(layer_count__gte=2).execute(network)" in content
    assert "Layer-specific nodes:" in content
    assert "Connector nodes:" in content


def test_query_with_dsl_uncertainty_section_shows_dict_like_result_shape():
    path = REPO_ROOT / "docfiles" / "how-to" / "query_with_dsl.rst"
    content = path.read_text(encoding="utf-8")

    assert "print(df[['id', 'degree', 'betweenness_centrality']].head(3))" in content
    assert "The ``degree`` and ``betweenness_centrality`` columns now contain dictionaries" in content


def test_tutorial_10min_example_1_contains_expected_output_block():
    path = REPO_ROOT / "docfiles" / "getting_started" / "tutorial_10min.rst"
    content = path.read_text(encoding="utf-8")

    assert "Expected output (illustrative):" in content
    assert "Found 8 high-degree nodes" in content
    assert "Top high-degree nodes:" in content
    assert "degree_centrality" in content
