import importlib.util
from pathlib import Path

import pytest


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "docs"
    / "_downloads"
    / "1ef72fc4aaa3ffe34e028f20e02a396b"
    / "example_pattern_matching.py"
)


def load_example_module():
    spec = importlib.util.spec_from_file_location(
        "example_pattern_matching", MODULE_PATH
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def example_module():
    return load_example_module()


def test_create_sample_network_structure(example_module):
    network = example_module.create_sample_network()

    assert len(list(network.get_nodes())) == 7
    assert len(list(network.get_edges())) == 6
    assert set(network.layers) == {"social", "work"}


def test_examples_emit_expected_summaries(example_module, capsys):
    # Run all example functions to cover the full script surface
    example_module.example_basic_edge_pattern()
    example_module.example_layer_constrained_pattern()
    example_module.example_weighted_edges()
    example_module.example_triangle_motif()
    example_module.example_path_pattern()
    example_module.example_high_degree_nodes()
    example_module.example_execution_plan()
    example_module.example_result_projections()

    output = capsys.readouterr().out

    assert "Example 1: Basic Edge Pattern" in output
    assert "Found 5 edges (showing first 5)" in output
    assert "Example 2: Layer-Constrained Pattern" in output
    assert "Found 8 edges in social layer" in output
    assert "Example 3: Weighted Edge Pattern" in output
    assert "Found 6 edges with weight > 1.0" in output
    assert "Example 4: Triangle Motif" in output
    assert "Found 1 triangle(s)" in output
    assert "Nodes in triangle:" in output
    assert "Example 5: 2-Hop Path Pattern" in output
    assert "Found 3 2-hop paths (showing 3)" in output
    assert "Example 6: High-Degree Node Connections" in output
    assert "Found 0 high-degree pairs" in output
    assert "Example 7: Query Execution Plan" in output
    assert "Root variable: a" in output
    assert "Join order: ['a', 'b']" in output
    assert "Estimated complexity: 50000" in output
    assert "Example 8: Result Projections" in output
    assert "1. As Pandas DataFrame:" in output
    assert "Induced subgraph:" in output
    assert "Nodes: 3" in output
    assert "Edges: 3" in output


def test_weight_and_path_patterns_return_expected_matches(example_module):
    network = example_module.create_sample_network()

    weighted_pattern = (
        example_module.Q.pattern()
        .node("a")
        .node("b")
        .edge("a", "b", directed=False)
        .where(weight__gt=1.0)
    )
    weighted_result = weighted_pattern.execute(network)
    weighted_edges = weighted_result.to_edges()

    assert weighted_result.count == 6
    for src, dst in weighted_edges:
        edge_data = network.core_network.get_edge_data(src, dst)
        if "weight" in edge_data:
            weight = edge_data["weight"]
        else:
            # MultiGraph stores attributes under numeric keys
            weight = next(iter(edge_data.values())).get("weight")
        assert weight > 1.0

    path_pattern = (
        example_module.Q.pattern()
        .path(["a", "b", "c"])
        .node("a")
        .where(layer="social")
        .node("b")
        .where(layer="social")
        .node("c")
        .where(layer="social")
        .limit(3)
    )
    path_result = path_pattern.execute(network)
    df = path_result.to_pandas()

    assert path_result.count == 3
    assert list(df.columns) == ["a", "b", "c"]
    for _, row in df.iterrows():
        assert all(node[1] == "social" for node in row)
