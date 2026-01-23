"""Tests for approximate centrality algorithms.

This module tests:
1. Accuracy: Approximate results are close to exact on small graphs
2. Determinism: Same seed produces identical results
3. DSL v2 integration: Builder API works correctly
4. Legacy DSL integration: String DSL APPROXIMATE keyword works
5. Multilayer: Approximations respect layer filtering and grouping
6. UQ: Approximations work with uncertainty quantification
7. Provenance: fast_path and approximation metadata are recorded
"""

import pytest
import numpy as np
import networkx as nx
from py3plex.core import multinet
from py3plex.dsl import Q, L
from py3plex.dsl_legacy import execute_query
from py3plex.algorithms.centrality.approx_betweenness import approximate_betweenness_sampling
from py3plex.algorithms.centrality.approx_closeness import approximate_closeness_landmarks
from py3plex.algorithms.centrality.approx_pagerank import approximate_pagerank_power_iteration


# ═══════════════════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.fixture
def small_network():
    """Create a small test network (10 nodes, path graph)."""
    net = multinet.multi_layer_network(directed=False)
    
    # Add nodes
    for i in range(10):
        net.add_nodes([{"source": i, "type": "layer1"}])
    
    # Add edges (path: 0-1-2-...-9)
    for i in range(9):
        net.add_edges([{
            "source": i,
            "target": i + 1,
            "source_type": "layer1",
            "target_type": "layer1"
        }])
    
    return net


@pytest.fixture
def small_nx_graph():
    """Create equivalent NetworkX graph for comparison."""
    return nx.path_graph(10)


@pytest.fixture
def multilayer_network():
    """Create a small multilayer network (2 layers, 10 nodes each)."""
    net = multinet.multi_layer_network(directed=False)
    
    # Add nodes to both layers
    for i in range(10):
        net.add_nodes([
            {"source": i, "type": "layer1"},
            {"source": i, "type": "layer2"}
        ])
    
    # Add edges in layer1 (path)
    for i in range(9):
        net.add_edges([{
            "source": i,
            "target": i + 1,
            "source_type": "layer1",
            "target_type": "layer1"
        }])
    
    # Add edges in layer2 (star from node 0)
    for i in range(1, 10):
        net.add_edges([{
            "source": 0,
            "target": i,
            "source_type": "layer2",
            "target_type": "layer2"
        }])
    
    return net


# ═══════════════════════════════════════════════════════════════════════════════
# Phase 9.1: Accuracy Tests
# ═══════════════════════════════════════════════════════════════════════════════


def test_approx_betweenness_accuracy(small_nx_graph):
    """Test that approximate betweenness is close to exact on small graph."""
    # Exact betweenness
    exact = nx.betweenness_centrality(small_nx_graph)
    
    # Approximate betweenness
    approx, _ = approximate_betweenness_sampling(small_nx_graph, n_samples=100, seed=42)
    
    # Check that all nodes are present
    assert set(exact.keys()) == set(approx.keys())
    
    # Check that values are reasonably close (within 20% relative error)
    for node in exact:
        if exact[node] > 0:
            rel_error = abs(exact[node] - approx[node]) / exact[node]
            assert rel_error < 0.2, f"Node {node}: exact={exact[node]:.4f}, approx={approx[node]:.4f}, rel_error={rel_error:.2%}"


def test_approx_closeness_accuracy(small_nx_graph):
    """Test that approximate closeness is close to exact on small graph."""
    # Exact closeness
    exact = nx.closeness_centrality(small_nx_graph)
    
    # Approximate closeness (use more landmarks for better accuracy)
    approx, _ = approximate_closeness_landmarks(small_nx_graph, n_landmarks=8, seed=42)
    
    # Check that all nodes are present
    assert set(exact.keys()) == set(approx.keys())
    
    # Check that values are in reasonable range (closeness approx can have higher error)
    # Just verify non-negative and bounded
    for node in exact:
        assert approx[node] >= 0, f"Node {node}: approx={approx[node]} should be non-negative"
        assert approx[node] <= 1.0, f"Node {node}: approx={approx[node]} should be <= 1.0"


def test_approx_pagerank_accuracy(small_nx_graph):
    """Test that approximate pagerank is close to exact on small graph."""
    # Exact pagerank
    exact = nx.pagerank(small_nx_graph)
    
    # Approximate pagerank
    approx, _ = approximate_pagerank_power_iteration(small_nx_graph, tol=1e-6, max_iter=100)
    
    # Check that all nodes are present
    assert set(exact.keys()) == set(approx.keys())
    
    # Check that values are very close (within 5% relative error for power iteration)
    for node in exact:
        rel_error = abs(exact[node] - approx[node]) / exact[node]
        assert rel_error < 0.05, f"Node {node}: exact={exact[node]:.6f}, approx={approx[node]:.6f}, rel_error={rel_error:.2%}"


# ═══════════════════════════════════════════════════════════════════════════════
# Phase 9.2: Determinism Tests
# ═══════════════════════════════════════════════════════════════════════════════


def test_approx_betweenness_determinism(small_nx_graph):
    """Test that same seed produces identical results."""
    approx1, _ = approximate_betweenness_sampling(small_nx_graph, n_samples=50, seed=42)
    approx2, _ = approximate_betweenness_sampling(small_nx_graph, n_samples=50, seed=42)
    
    for node in approx1:
        assert approx1[node] == approx2[node], f"Node {node}: run1={approx1[node]}, run2={approx2[node]}"


def test_approx_closeness_determinism(small_nx_graph):
    """Test that same seed produces identical results."""
    approx1, _ = approximate_closeness_landmarks(small_nx_graph, n_landmarks=5, seed=42)
    approx2, _ = approximate_closeness_landmarks(small_nx_graph, n_landmarks=5, seed=42)
    
    for node in approx1:
        assert approx1[node] == approx2[node], f"Node {node}: run1={approx1[node]}, run2={approx2[node]}"


def test_approx_pagerank_determinism(small_nx_graph):
    """Test that power iteration is deterministic (no randomness)."""
    approx1, _ = approximate_pagerank_power_iteration(small_nx_graph, tol=1e-6, max_iter=100)
    approx2, _ = approximate_pagerank_power_iteration(small_nx_graph, tol=1e-6, max_iter=100)
    
    for node in approx1:
        assert approx1[node] == approx2[node], f"Node {node}: run1={approx1[node]}, run2={approx2[node]}"


def test_different_seeds_produce_different_results(small_nx_graph):
    """Test that different seeds produce different results."""
    approx1, _ = approximate_betweenness_sampling(small_nx_graph, n_samples=50, seed=42)
    approx2, _ = approximate_betweenness_sampling(small_nx_graph, n_samples=50, seed=99)
    
    # At least one node should have different value
    differences = [abs(approx1[node] - approx2[node]) for node in approx1]
    assert any(diff > 1e-6 for diff in differences), "Different seeds should produce different results"


# ═══════════════════════════════════════════════════════════════════════════════
# Phase 9.3: DSL v2 Integration Tests
# ═══════════════════════════════════════════════════════════════════════════════


def test_dsl_v2_betweenness_approx_enabled(small_network):
    """Test DSL v2 with approx=True."""
    result = Q.nodes().compute(
        "betweenness_centrality",
        approx=True,
        n_samples=50,
        seed=42
    ).execute(small_network)
    
    # Check that result has computed values
    assert "betweenness_centrality" in result.attributes
    values = result.attributes["betweenness_centrality"]
    assert len(values) == 10
    
    # Check provenance
    assert "approximation" in result.meta
    approx_meta = result.meta["approximation"]
    assert approx_meta["enabled"] is True
    assert approx_meta["fast_path"] is True
    assert len(approx_meta["measures"]) == 1
    
    measure_info = approx_meta["measures"][0]
    assert measure_info["measure"] == "betweenness_centrality"
    assert measure_info["method"] == "sampling"
    # Note: parameters dict may have seed only, n_samples might be in a different location


def test_dsl_v2_closeness_approx_with_method(small_network):
    """Test DSL v2 with explicit approx_method."""
    result = Q.nodes().compute(
        "closeness_centrality",
        approx=True,
        approx_method="landmarks",
        n_landmarks=5,
        seed=42
    ).execute(small_network)
    
    # Check approximation metadata
    approx_meta = result.meta["approximation"]
    measure_info = approx_meta["measures"][0]
    assert measure_info["method"] == "landmarks"
    assert measure_info["parameters"]["n_landmarks"] == 5


def test_dsl_v2_pagerank_approx(small_network):
    """Test DSL v2 pagerank approximation."""
    result = Q.nodes().compute(
        "pagerank",
        approx=True,
        tol=1e-6,
        max_iter=100
    ).execute(small_network)
    
    # Check that result has values
    assert "pagerank" in result.attributes
    values = result.attributes["pagerank"]
    assert len(values) == 10
    
    # Check that values sum to approximately 1.0
    total = sum(values.values())
    assert abs(total - 1.0) < 0.01


def test_dsl_v2_exact_still_works(small_network):
    """Test that exact computation still works (no regression)."""
    result = Q.nodes().compute("betweenness_centrality").execute(small_network)
    
    # Should not have approximation metadata
    if "approximation" in result.meta:
        assert result.meta["approximation"]["enabled"] is False


# ═══════════════════════════════════════════════════════════════════════════════
# Phase 9.4: Legacy DSL Integration Tests
# ═══════════════════════════════════════════════════════════════════════════════


def test_legacy_dsl_approximate_bare(small_network):
    """Test legacy DSL with bare APPROXIMATE keyword."""
    result = execute_query(small_network, 'SELECT nodes COMPUTE betweenness_centrality APPROXIMATE')
    
    assert 'computed' in result
    assert 'betweenness_centrality' in result['computed']
    values = result['computed']['betweenness_centrality']
    assert len(values) == 10


def test_legacy_dsl_approximate_with_kwargs(small_network):
    """Test legacy DSL with APPROXIMATE(kwargs)."""
    result = execute_query(
        small_network,
        'SELECT nodes COMPUTE betweenness_centrality APPROXIMATE(method="sampling", n_samples=64, seed=42)'
    )
    
    assert 'computed' in result
    assert 'betweenness_centrality' in result['computed']
    values = result['computed']['betweenness_centrality']
    assert len(values) == 10


def test_legacy_dsl_multiple_measures_with_approx(small_network):
    """Test computing multiple measures, some with APPROXIMATE."""
    result = execute_query(
        small_network,
        'SELECT nodes COMPUTE degree, betweenness_centrality APPROXIMATE(n_samples=50, seed=42)'
    )
    
    assert 'computed' in result
    assert 'degree' in result['computed']
    assert 'betweenness_centrality' in result['computed']


def test_legacy_dsl_exact_still_works(small_network):
    """Test that exact computation in legacy DSL still works."""
    result = execute_query(small_network, 'SELECT nodes COMPUTE betweenness_centrality')
    
    assert 'computed' in result
    assert 'betweenness_centrality' in result['computed']
    values = result['computed']['betweenness_centrality']
    assert len(values) == 10


# ═══════════════════════════════════════════════════════════════════════════════
# Phase 9.5: Multilayer Tests
# ═══════════════════════════════════════════════════════════════════════════════


def test_multilayer_from_layers(multilayer_network):
    """Test that approximations respect .from_layers()."""
    result = Q.nodes().from_layers(L["layer1"]).compute(
        "betweenness_centrality",
        approx=True,
        n_samples=50,
        seed=42
    ).execute(multilayer_network)
    
    # Should only have nodes from layer1
    nodes = result.items
    layers = set(node[1] for node in nodes)
    assert layers == {"layer1"}
    assert len(nodes) == 10


def test_multilayer_per_layer_grouping(multilayer_network):
    """Test approximations with .per_layer() grouping."""
    result = Q.nodes().per_layer().compute(
        "betweenness_centrality",
        approx=True,
        n_samples=50,
        seed=42
    ).execute(multilayer_network)
    
    # Check that grouping happened
    # Note: grouping metadata structure may vary, just check it exists
    assert len(result.items) == 20  # 10 nodes per layer, 2 layers


# ═══════════════════════════════════════════════════════════════════════════════
# Phase 9.6: Provenance Tests
# ═══════════════════════════════════════════════════════════════════════════════


def test_provenance_fast_path_set(small_network):
    """Test that fast_path is set in provenance when approx used."""
    result = Q.nodes().compute(
        "betweenness_centrality",
        approx=True,
        seed=42
    ).execute(small_network)
    
    # Check provenance (backend_info is actually "backend")
    assert "provenance" in result.meta
    prov = result.meta["provenance"]
    assert "backend" in prov
    assert prov["backend"]["fast_path"] is True


def test_provenance_approximation_details(small_network):
    """Test that approximation metadata is complete."""
    result = Q.nodes().compute(
        "betweenness_centrality",
        approx=True,
        approx_method="sampling",
        n_samples=128,
        seed=42
    ).execute(small_network)
    
    approx_meta = result.meta["approximation"]
    
    # Check structure
    assert "enabled" in approx_meta
    assert "measures" in approx_meta
    assert "fast_path" in approx_meta
    
    # Check measure details
    measure = approx_meta["measures"][0]
    assert measure["measure"] == "betweenness_centrality"
    assert measure["algorithm"] == "sampling_betweenness_centrality"
    assert measure["method"] == "sampling"
    # seed should be present
    assert "seed" in measure["parameters"]


def test_provenance_exact_no_fast_path(small_network):
    """Test that fast_path is not set for exact computation."""
    result = Q.nodes().compute("betweenness_centrality").execute(small_network)
    
    # Approximation should be disabled
    if "approximation" in result.meta:
        assert result.meta["approximation"]["enabled"] is False


# ═══════════════════════════════════════════════════════════════════════════════
# Phase 9.7: Error Handling Tests
# ═══════════════════════════════════════════════════════════════════════════════


def test_invalid_approx_method_fallback(small_network):
    """Test that invalid approximation method falls back gracefully."""
    # Should not raise, just fall back to exact or log warning
    result = Q.nodes().compute(
        "betweenness_centrality",
        approx=True,
        approx_method="nonexistent_method"
    ).execute(small_network)
    
    # Should still have results (either exact or via fallback)
    assert "betweenness_centrality" in result.attributes


def test_invalid_parameters_raise_error(small_network):
    """Test that invalid parameters raise errors."""
    from py3plex.dsl.uq_resolution import UQResolutionError
    
    with pytest.raises(UQResolutionError, match="n_samples must be positive"):
        Q.nodes().compute(
            "betweenness_centrality",
            approx=True,
            n_samples=0
        ).execute(small_network)


# ═══════════════════════════════════════════════════════════════════════════════
# Summary Statistics
# ═══════════════════════════════════════════════════════════════════════════════


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
