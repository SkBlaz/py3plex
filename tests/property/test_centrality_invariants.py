#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Property-based tests for multilayer centrality metric invariants.

This module tests fundamental mathematical properties and invariants that all
centrality metrics should satisfy, such as:
- Non-negativity
- Finite values
- Normalization properties
- Invariance under graph isomorphism
- Consistency across operations
"""

import pytest
import networkx as nx
import numpy as np
from hypothesis import given, settings, assume, strategies as st
from hypothesis import HealthCheck

# Import shared strategies
from .strategies import small_graphs, node_names, layer_labels, positive_weights

# Conditional imports with proper error handling
try:
    from py3plex.core import multinet
    from py3plex.algorithms.multilayer_algorithms.centrality import (
        MultilayerCentrality,
        compute_all_centralities,
    )
    CENTRALITY_AVAILABLE = True
except ImportError:
    CENTRALITY_AVAILABLE = False
    pytest.skip("Centrality module not available", allow_module_level=True)


# ============================================================================
# Helper Functions
# ============================================================================

def create_simple_multilayer_network(num_nodes=4, num_layers=2):
    """Create a simple multilayer network for testing."""
    network = multinet.multi_layer_network(directed=False)
    
    nodes = [f'N{i}' for i in range(num_nodes)]
    layers = [f'L{i}' for i in range(num_layers)]
    
    # Add edges to create a connected network in each layer
    for layer in layers:
        for i in range(len(nodes) - 1):
            network.add_edges([
                [nodes[i], layer, nodes[i+1], layer, 1.0]
            ], input_type='list')
    
    return network


def relabel_network_nodes(network, mapping):
    """Create a new network with relabeled nodes (isomorphic)."""
    new_network = multinet.multi_layer_network(directed=network.directed)
    
    edges = network.get_edges()
    for edge in edges:
        # Handle both list and dict edge formats
        if isinstance(edge, dict):
            source = edge.get('source')
            source_layer = edge.get('source_layer')
            target = edge.get('target')
            target_layer = edge.get('target_layer')
            weight = edge.get('weight', 1.0)
        else:
            # Handle tuple/list format - check length to avoid index errors
            try:
                if len(edge) < 4:
                    # Skip malformed edges
                    continue
                source = edge[0]
                source_layer = edge[1]
                target = edge[2]
                target_layer = edge[3]
                weight = edge[4] if len(edge) > 4 else 1.0
            except (IndexError, TypeError):
                # Skip edges that can't be parsed
                continue
        
        new_source = mapping.get(source, source)
        new_target = mapping.get(target, target)
        
        new_network.add_edges([
            [new_source, source_layer, new_target, target_layer, weight]
        ], input_type='list')
    
    return new_network


# ============================================================================
# Property Tests: Non-negativity and Finiteness
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=2, max_value=6),
    num_layers=st.integers(min_value=1, max_value=3)
)
def test_degree_centrality_non_negative(num_nodes, num_layers):
    """Test that degree centrality values are always non-negative."""
    network = create_simple_multilayer_network(num_nodes, num_layers)
    calc = MultilayerCentrality(network)
    
    # Test unweighted degree
    result = calc.supra_degree_centrality(weighted=False)
    assert all(v >= 0 for v in result.values()), "Degree centrality must be non-negative"
    
    # Test weighted degree
    result_weighted = calc.supra_degree_centrality(weighted=True)
    assert all(v >= 0 for v in result_weighted.values()), "Weighted degree must be non-negative"


@pytest.mark.property
@settings(deadline=None, max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=6),
    num_layers=st.integers(min_value=1, max_value=3)
)
def test_centrality_values_finite(num_nodes, num_layers):
    """Test that centrality values are always finite (no NaN or inf)."""
    network = create_simple_multilayer_network(num_nodes, num_layers)
    calc = MultilayerCentrality(network)
    
    # Test multiple centrality metrics
    metrics = [
        calc.supra_degree_centrality(),
        calc.overlapping_degree_centrality(),
        calc.participation_coefficient(),
    ]
    
    for result in metrics:
        assert all(np.isfinite(v) for v in result.values()), "All values must be finite"


@pytest.mark.property
@settings(deadline=None, max_examples=15, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=5),
    num_layers=st.integers(min_value=2, max_value=3)
)
def test_participation_coefficient_bounded(num_nodes, num_layers):
    """Test that participation coefficient is bounded between 0 and 1."""
    network = create_simple_multilayer_network(num_nodes, num_layers)
    calc = MultilayerCentrality(network)
    
    result = calc.participation_coefficient(weighted=False)
    
    for node, value in result.items():
        assert 0.0 <= value <= 1.0, f"Participation coefficient for {node} must be in [0, 1], got {value}"


@pytest.mark.property
@settings(deadline=None, max_examples=15, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=5),
    num_layers=st.integers(min_value=1, max_value=3)
)
def test_closeness_centrality_non_negative(num_nodes, num_layers):
    """Test that closeness centrality values are non-negative."""
    network = create_simple_multilayer_network(num_nodes, num_layers)
    calc = MultilayerCentrality(network)
    
    result = calc.multilayer_closeness_centrality(normalized=True)
    
    assert all(v >= 0 for v in result.values()), "Closeness centrality must be non-negative"
    assert all(np.isfinite(v) for v in result.values()), "Closeness values must be finite"


@pytest.mark.property
@settings(deadline=None, max_examples=15, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=5),
    num_layers=st.integers(min_value=1, max_value=3)
)
def test_betweenness_centrality_non_negative(num_nodes, num_layers):
    """Test that betweenness centrality values are non-negative."""
    network = create_simple_multilayer_network(num_nodes, num_layers)
    calc = MultilayerCentrality(network)
    
    result = calc.multilayer_betweenness_centrality(normalized=True)
    
    assert all(v >= 0 for v in result.values()), "Betweenness centrality must be non-negative"
    assert all(np.isfinite(v) for v in result.values()), "Betweenness values must be finite"


# ============================================================================
# Property Tests: Normalization
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=15, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=6),
    num_layers=st.integers(min_value=2, max_value=3)
)
def test_eigenvector_centrality_normalization(num_nodes, num_layers):
    """Test that eigenvector centrality returns valid results."""
    network = create_simple_multilayer_network(num_nodes, num_layers)
    calc = MultilayerCentrality(network)
    
    try:
        # Note: multiplex_eigenvector_centrality doesn't have a normalize parameter
        # It returns node-layer centralities
        result = calc.multiplex_eigenvector_centrality()
        values = np.array(list(result.values()))
        
        # All values should be finite
        assert all(np.isfinite(v) for v in values), "All values must be finite"
        
        # Values should be non-negative (Perron-Frobenius for non-negative matrices)
        assert all(v >= 0 for v in values), "Eigenvector centrality should be non-negative"
    except Exception as e:
        # Some networks may not support eigenvector centrality (e.g., disconnected)
        # This is acceptable - we just want to ensure that when it works, it's valid
        if "singular" not in str(e).lower() and "convergence" not in str(e).lower():
            raise


@pytest.mark.property
@settings(deadline=None, max_examples=15, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=6),
    num_layers=st.integers(min_value=2, max_value=3),
    p_norm=st.sampled_from([1, 2, float('inf')])
)
def test_lp_aggregated_centrality_properties(num_nodes, num_layers, p_norm):
    """Test that Lp-aggregated centrality has correct properties."""
    network = create_simple_multilayer_network(num_nodes, num_layers)
    calc = MultilayerCentrality(network)
    
    # Get layer centralities
    layer_degrees = calc.layer_degree_centrality(weighted=False)
    
    # Compute Lp aggregation
    result = calc.lp_aggregated_centrality(layer_degrees, p=p_norm)
    
    # Results should be non-negative
    assert all(v >= 0 for v in result.values()), "Lp-aggregated values must be non-negative"
    
    # Results should be finite
    assert all(np.isfinite(v) for v in result.values()), "Lp-aggregated values must be finite"
    
    # Results should not be empty
    assert len(result) > 0, "Should have results for nodes"


# ============================================================================
# Property Tests: Isomorphism Invariance
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=5),
    num_layers=st.integers(min_value=1, max_value=2)
)
def test_degree_invariant_under_relabeling(num_nodes, num_layers):
    """Test that degree centrality is invariant under node relabeling."""
    network = create_simple_multilayer_network(num_nodes, num_layers)
    calc1 = MultilayerCentrality(network)
    result1 = calc1.supra_degree_centrality(weighted=False)
    
    # Create isomorphic network with different node labels
    nodes = [f'N{i}' for i in range(num_nodes)]
    new_nodes = [f'X{i}' for i in range(num_nodes)]
    mapping = dict(zip(nodes, new_nodes))
    
    network2 = relabel_network_nodes(network, mapping)
    calc2 = MultilayerCentrality(network2)
    result2 = calc2.supra_degree_centrality(weighted=False)
    
    # The multiset of degree values should be the same
    # Note: supra_degree_centrality returns node-layer tuples as keys
    values1 = sorted(result1.values())
    values2 = sorted(result2.values())
    
    assert len(values1) == len(values2), "Should have same number of node-layer pairs"
    assert all(abs(v1 - v2) < 1e-6 for v1, v2 in zip(values1, values2)), \
        "Degree multiset should be identical under relabeling"


@pytest.mark.property
@settings(deadline=None, max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=5),
    num_layers=st.integers(min_value=1, max_value=2)
)
def test_betweenness_ranking_invariant(num_nodes, num_layers):
    """Test that betweenness centrality ranking is preserved under relabeling."""
    network = create_simple_multilayer_network(num_nodes, num_layers)
    calc1 = MultilayerCentrality(network)
    result1 = calc1.multilayer_betweenness_centrality(normalized=True)
    
    # Create isomorphic network
    nodes = [f'N{i}' for i in range(num_nodes)]
    new_nodes = [f'Y{i}' for i in range(num_nodes)]
    mapping = dict(zip(nodes, new_nodes))
    
    network2 = relabel_network_nodes(network, mapping)
    calc2 = MultilayerCentrality(network2)
    result2 = calc2.multilayer_betweenness_centrality(normalized=True)
    
    # The sorted centrality values should be identical
    # Note: betweenness may return node or node-layer tuples
    values1 = sorted(result1.values())
    values2 = sorted(result2.values())
    
    assert len(values1) == len(values2), "Should have same number of centrality values"
    assert all(abs(v1 - v2) < 1e-6 for v1, v2 in zip(values1, values2)), \
        "Betweenness ranking should be preserved under relabeling"


# ============================================================================
# Property Tests: Consistency and Monotonicity
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=15, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=6),
    num_layers=st.integers(min_value=2, max_value=3)
)
def test_layer_degree_sum_equals_overlapping(num_nodes, num_layers):
    """Test that summing layer degrees equals overlapping degree."""
    network = create_simple_multilayer_network(num_nodes, num_layers)
    calc = MultilayerCentrality(network)
    
    # Get overlapping degree (should be sum across all layers)
    overlapping = calc.overlapping_degree_centrality(weighted=False)
    
    # Get per-layer degrees and sum them
    layer_degrees_sum = {}
    layers = [f'L{i}' for i in range(num_layers)]
    
    for layer in layers:
        layer_result = calc.layer_degree_centrality(layer=layer, weighted=False)
        for node, degree in layer_result.items():
            layer_degrees_sum[node] = layer_degrees_sum.get(node, 0) + degree
    
    # The sums should match (within floating point tolerance)
    for node in overlapping:
        if node in layer_degrees_sum:
            assert abs(overlapping[node] - layer_degrees_sum[node]) < 1e-6, \
                f"Overlapping degree should equal sum of layer degrees for {node}"


@pytest.mark.property
@settings(deadline=None, max_examples=15, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=5),
    num_layers=st.integers(min_value=1, max_value=3)
)
def test_weighted_degree_greater_equal_unweighted(num_nodes, num_layers):
    """Test that weighted degree is at least unweighted degree (with weights >= 1)."""
    network = multinet.multi_layer_network(directed=False)
    
    nodes = [f'N{i}' for i in range(num_nodes)]
    layers = [f'L{i}' for i in range(num_layers)]
    
    # Add edges with weights >= 1
    for layer in layers:
        for i in range(len(nodes) - 1):
            network.add_edges([
                [nodes[i], layer, nodes[i+1], layer, 2.0]  # Weight >= 1
            ], input_type='list')
    
    calc = MultilayerCentrality(network)
    
    unweighted = calc.supra_degree_centrality(weighted=False)
    weighted = calc.supra_degree_centrality(weighted=True)
    
    # Weighted degree should be >= unweighted when all weights >= 1
    for node in unweighted:
        if node in weighted:
            assert weighted[node] >= unweighted[node] - 1e-6, \
                f"Weighted degree should be >= unweighted for {node} when weights >= 1"


# ============================================================================
# Property Tests: Extended Centrality Metrics
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=5),
    num_layers=st.integers(min_value=1, max_value=2)
)
def test_information_centrality_properties(num_nodes, num_layers):
    """Test properties of information centrality."""
    network = create_simple_multilayer_network(num_nodes, num_layers)
    calc = MultilayerCentrality(network)
    
    try:
        result = calc.information_centrality()
        
        # Should have results
        assert len(result) > 0, "Should compute information centrality"
        
        # All values should be finite
        assert all(np.isfinite(v) for v in result.values()), "Values must be finite"
        
        # Values should be positive (for connected components)
        assert all(v >= 0 for v in result.values()), "Information centrality should be non-negative"
    except Exception as e:
        # Some networks may not support this metric
        # Just ensure it doesn't crash unexpectedly
        if "not supported" in str(e).lower() or "invalid" in str(e).lower():
            pytest.skip(f"Information centrality not supported for this network: {e}")
        raise


@pytest.mark.property
@settings(deadline=None, max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=5),
    num_layers=st.integers(min_value=1, max_value=2),
    radius=st.integers(min_value=1, max_value=3)
)
def test_collective_influence_properties(num_nodes, num_layers, radius):
    """Test properties of collective influence centrality."""
    network = create_simple_multilayer_network(num_nodes, num_layers)
    calc = MultilayerCentrality(network)
    
    result = calc.collective_influence(radius=radius)
    
    # Should have results
    assert len(result) > 0, "Should compute collective influence"
    
    # All values should be finite
    assert all(np.isfinite(v) for v in result.values()), "Values must be finite"
    
    # Values should be non-negative
    assert all(v >= 0 for v in result.values()), "Collective influence should be non-negative"


@pytest.mark.property
@settings(deadline=None, max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=5),
    num_layers=st.integers(min_value=1, max_value=2)
)
def test_harmonic_closeness_properties(num_nodes, num_layers):
    """Test properties of harmonic closeness centrality."""
    network = create_simple_multilayer_network(num_nodes, num_layers)
    calc = MultilayerCentrality(network)
    
    result = calc.harmonic_closeness_centrality()
    
    # Should have results
    assert len(result) > 0, "Should compute harmonic closeness"
    
    # All values should be finite
    assert all(np.isfinite(v) for v in result.values()), "Values must be finite"
    
    # Values should be non-negative
    assert all(v >= 0 for v in result.values()), "Harmonic closeness should be non-negative"


# ============================================================================
# Property Tests: Compute All Centralities
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=5),
    num_layers=st.integers(min_value=1, max_value=2)
)
def test_compute_all_centralities_basic(num_nodes, num_layers):
    """Test that compute_all_centralities returns valid results."""
    network = create_simple_multilayer_network(num_nodes, num_layers)
    
    results = compute_all_centralities(network, include_path_based=False, include_extended=False)
    
    # Should have some results
    assert len(results) > 0, "Should compute some centralities"
    
    # All results should be dictionaries with node keys
    for metric_name, metric_values in results.items():
        assert isinstance(metric_values, dict), f"{metric_name} should return a dict"
        
        # All values should be finite
        for node, value in metric_values.items():
            assert np.isfinite(value), f"{metric_name} for {node} must be finite, got {value}"


@pytest.mark.property
@settings(deadline=None, max_examples=8, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=5),
    num_layers=st.integers(min_value=1, max_value=2)
)
def test_compute_all_centralities_extended(num_nodes, num_layers):
    """Test that compute_all_centralities with extended flag includes more metrics."""
    network = create_simple_multilayer_network(num_nodes, num_layers)
    
    basic_results = compute_all_centralities(network, include_extended=False)
    extended_results = compute_all_centralities(network, include_extended=True)
    
    # Extended should include more or equal metrics
    assert len(extended_results) >= len(basic_results), \
        "Extended mode should include at least as many metrics as basic"
    
    # All extended results should be valid
    for metric_name, metric_values in extended_results.items():
        assert isinstance(metric_values, dict), f"{metric_name} should return a dict"
        assert len(metric_values) > 0, f"{metric_name} should have results"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-m', 'property'])
