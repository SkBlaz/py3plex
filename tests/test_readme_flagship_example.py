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


def test_uq_profiles_alternative():
    """Test that UQ profiles work as an alternative to explicit .uq() params."""
    net = multinet.multi_layer_network(directed=False, verbose=False)
    
    edges = [
        ["A", "L0", "B", "L0", 1.0],
        ["B", "L0", "C", "L0", 1.0],
    ]
    net.add_edges(edges, input_type="list")
    
    # Test UQ.fast() as might be referenced
    result = (
        Q.nodes()
         .uq(UQ.fast(seed=42))
         .compute("degree")
         .execute(net)
    )
    
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
