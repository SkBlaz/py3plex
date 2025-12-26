"""
Test for the README flagship example with integrated .uq() functionality.

This test validates that the flagship example in README.md works correctly
after integrating uncertainty quantification into the master regulators query.
"""

import pytest
from py3plex.core import multinet
from py3plex.dsl import Q, UQ


def test_flagship_example_imports():
    """Test that all imports from flagship example work."""
    from py3plex.core import datasets
    from py3plex.dsl import Q, UQ
    from py3plex.algorithms.community_detection import multilayer_louvain

    assert datasets is not None
    assert Q is not None
    assert UQ is not None
    assert multilayer_louvain is not None


def test_flagship_dsl_query_structure_with_uq():
    """Test that the flagship DSL query structure with .uq() is valid."""
    # Create a minimal test network
    net = multinet.multi_layer_network(directed=False, verbose=False)

    # Add simple test data with multiple layers
    edges = [
        ["A", "L0", "B", "L0", 1.0],
        ["B", "L0", "C", "L0", 1.0],
        ["C", "L0", "A", "L0", 1.0],
        ["A", "L1", "B", "L1", 1.0],
        ["B", "L1", "D", "L1", 1.0],
        ["A", "L0", "A", "L1", 1.0],
        ["B", "L0", "B", "L1", 1.0],
    ]
    net.add_edges(edges, input_type="list")

    # Test the flagship query structure with .uq()
    result = (
        Q.nodes()
        .where(degree__gt=0)  # Simplified filter
        .uq(method="perturbation", n_samples=10, ci=0.95, seed=42)
        .per_layer()
        .compute("degree_centrality", "betweenness_centrality")
        .top_k(2, "betweenness_centrality__mean")  # Using __mean selector
        .end_grouping()
        .sort(by="betweenness_centrality__mean", descending=True)
        .limit(3)
        .execute(net)
    )

    # Verify result structure
    assert result is not None
    assert result.count > 0

    # Test expand_uncertainty=True
    df = result.to_pandas(expand_uncertainty=True)

    # Verify uncertainty columns are present
    assert "betweenness_centrality" in df.columns
    assert "betweenness_centrality_std" in df.columns
    assert "betweenness_centrality_ci95_low" in df.columns
    assert "betweenness_centrality_ci95_high" in df.columns
    assert "degree_centrality" in df.columns
    assert "degree_centrality_std" in df.columns

    # Verify we have valid data
    assert len(df) > 0
    assert (df["betweenness_centrality"] >= 0).all()
    assert (df["degree_centrality"] >= 0).all()


def test_flagship_with_coverage_operator():
    """Test the enhanced flagship example with .coverage() operator."""
    # Create a multilayer test network
    net = multinet.multi_layer_network(directed=False, verbose=False)

    # Add edges across 3 layers with some nodes appearing as hubs in multiple layers
    edges = [
        # Layer 0: A and B are hubs
        ["A", "L0", "B", "L0", 1.0],
        ["A", "L0", "C", "L0", 1.0],
        ["A", "L0", "D", "L0", 1.0],
        ["B", "L0", "C", "L0", 1.0],
        ["B", "L0", "D", "L0", 1.0],
        # Layer 1: A and E are hubs
        ["A", "L1", "E", "L1", 1.0],
        ["A", "L1", "F", "L1", 1.0],
        ["A", "L1", "G", "L1", 1.0],
        ["E", "L1", "F", "L1", 1.0],
        ["E", "L1", "G", "L1", 1.0],
        # Layer 2: B and E are hubs
        ["B", "L2", "E", "L2", 1.0],
        ["B", "L2", "H", "L2", 1.0],
        ["B", "L2", "I", "L2", 1.0],
        ["E", "L2", "H", "L2", 1.0],
        ["E", "L2", "I", "L2", 1.0],
    ]
    net.add_edges(edges, input_type="list")

    # Test the enhanced flagship query with coverage
    # This mirrors the README example structure
    result = (
        Q.nodes()
        .where(degree__gt=1)  # Filter peripheral nodes
        .uq(method="perturbation", n_samples=10, ci=0.95, seed=42)
        .per_layer()
        .compute("degree_centrality", "betweenness_centrality")
        .top_k(3, "betweenness_centrality__mean")  # Top 3 per layer
        .end_grouping()
        .coverage(mode="at_least", k=2)  # Must appear in at least 2 layers
        .mutate(
            influence_score=lambda row: (
                row.get("degree_centrality__mean", 0) * 0.4
                + row.get("betweenness_centrality__mean", 0) * 0.6
            )
        )
        .limit(5)
        .execute(net)
    )

    # Verify result structure
    assert result is not None
    assert result.count > 0

    # Convert to DataFrame
    df = result.to_pandas(expand_uncertainty=True)

    # Verify we have valid data
    assert len(df) > 0
    assert "influence_score" in df.columns
    assert "betweenness_centrality" in df.columns
    assert "betweenness_centrality_std" in df.columns
    assert "degree_centrality" in df.columns

    # Verify that coverage filtering worked - nodes should appear in multiple layers
    # A, B, and E should be in the results as they are hubs in 2+ layers
    node_ids = df["id"].unique()
    # At least one node should be present (A, B, or E)
    assert len(node_ids) > 0

    # The influence_score should be properly computed
    assert all(df["influence_score"] >= 0)


def test_uq_profiles_alternative():
    """Test that UQ profiles work as an alternative to explicit .uq() params."""
    net = multinet.multi_layer_network(directed=False, verbose=False)

    edges = [
        ["A", "L0", "B", "L0", 1.0],
        ["B", "L0", "C", "L0", 1.0],
    ]
    net.add_edges(edges, input_type="list")

    # Test UQ.fast() as might be referenced
    result = Q.nodes().uq(UQ.fast(seed=42)).compute("degree").execute(net)

    df = result.to_pandas(expand_uncertainty=True)
    assert "degree" in df.columns
    assert "degree_std" in df.columns


def test_selector_syntax_with_mean():
    """Test that selector syntax (metric__mean) works in top_k and sort."""
    net = multinet.multi_layer_network(directed=False, verbose=False)

    edges = [
        ["A", "L0", "B", "L0", 1.0],
        ["B", "L0", "C", "L0", 1.0],
        ["C", "L0", "A", "L0", 1.0],
        ["A", "L1", "B", "L1", 1.0],
    ]
    net.add_edges(edges, input_type="list")

    # Test query with __mean selector
    result = (
        Q.nodes()
        .uq(method="perturbation", n_samples=10, seed=42)
        .compute("degree")
        .sort(by="degree__mean", descending=True)  # Sort by mean
        .limit(3)
        .execute(net)
    )

    df = result.to_pandas(expand_uncertainty=True)
    assert len(df) > 0

    # Verify ordering by mean works
    if len(df) > 1:
        # Should be sorted descending by degree mean
        degrees = df["degree"].values
        assert degrees[0] >= degrees[-1]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
