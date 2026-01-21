#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Property-based tests for centrality ranking stability and metamorphic relations.

This module tests properties related to:
- Ranking stability under small perturbations
- Monotonicity of centrality with respect to network growth
- Scale invariance of normalized centralities
- Centrality orderings and comparisons
"""

import pytest
import numpy as np
from hypothesis import given, settings, assume, strategies as st
from hypothesis import HealthCheck

# Import shared strategies
from .strategies import node_names, layer_labels

# Conditional imports
try:
    from py3plex.core import multinet
    from py3plex.algorithms.multilayer_algorithms.centrality import MultilayerCentrality
    CENTRALITY_AVAILABLE = True
except ImportError:
    CENTRALITY_AVAILABLE = False
    pytest.skip("Centrality module not available", allow_module_level=True)


# ============================================================================
# Helper Functions
# ============================================================================

def create_star_network(num_spokes=4, num_layers=2):
    """Create a star network (hub-and-spoke topology)."""
    network = multinet.multi_layer_network(directed=False)
    
    hub = 'Hub'
    spokes = [f'S{i}' for i in range(num_spokes)]
    layers = [f'L{i}' for i in range(num_layers)]
    
    for layer in layers:
        for spoke in spokes:
            network.add_edges([
                [hub, layer, spoke, layer, 1.0]
            ], input_type='list')
    
    return network, hub, spokes


def create_path_network(length=5, num_layers=2):
    """Create a path network (linear chain)."""
    network = multinet.multi_layer_network(directed=False)
    
    nodes = [f'N{i}' for i in range(length)]
    layers = [f'L{i}' for i in range(num_layers)]
    
    for layer in layers:
        for i in range(len(nodes) - 1):
            network.add_edges([
                [nodes[i], layer, nodes[i+1], layer, 1.0]
            ], input_type='list')
    
    return network, nodes


def get_ranking(centrality_dict):
    """Get node ranking from centrality values (highest to lowest)."""
    return sorted(centrality_dict.items(), key=lambda x: x[1], reverse=True)


def spearman_rank_correlation(rank1, rank2):
    """Compute Spearman rank correlation coefficient."""
    # Create dictionaries mapping nodes to ranks
    rank_dict1 = {node: i for i, (node, _) in enumerate(rank1)}
    rank_dict2 = {node: i for i, (node, _) in enumerate(rank2)}
    
    # Get common nodes
    common_nodes = set(rank_dict1.keys()) & set(rank_dict2.keys())
    if len(common_nodes) < 2:
        return 1.0  # Perfect correlation for single node
    
    # Compute rank differences
    diff_sum = sum((rank_dict1[node] - rank_dict2[node])**2 for node in common_nodes)
    n = len(common_nodes)
    
    # Spearman correlation formula
    rho = 1 - (6 * diff_sum) / (n * (n**2 - 1))
    return rho


# ============================================================================
# Property Tests: Network Topology Effects
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_spokes=st.integers(min_value=3, max_value=6),
    num_layers=st.integers(min_value=1, max_value=3)
)
def test_star_network_hub_highest_degree(num_spokes, num_layers):
    """Test that the hub node has the highest degree in a star network."""
    network, hub, spokes = create_star_network(num_spokes, num_layers)
    calc = MultilayerCentrality(network)
    
    # supra_degree_centrality returns node-layer tuples as keys: {(node, layer): degree}
    degree = calc.supra_degree_centrality(weighted=False)
    
    # Sum degrees across all layers for each node
    node_degrees = {}
    for (node, layer), deg in degree.items():
        node_degrees[node] = node_degrees.get(node, 0) + deg
    
    # Hub should have highest total degree
    hub_degree = node_degrees.get(hub, 0)
    for spoke in spokes:
        spoke_degree = node_degrees.get(spoke, 0)
        assert hub_degree > spoke_degree, \
            f"Hub should have higher degree than spokes: hub={hub_degree}, spoke={spoke_degree}"


@pytest.mark.property
@settings(deadline=None, max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_spokes=st.integers(min_value=3, max_value=6),
    num_layers=st.integers(min_value=1, max_value=3)
)
def test_star_network_hub_highest_betweenness(num_spokes, num_layers):
    """Test that the hub node has highest betweenness in a star network."""
    assume(num_spokes >= 3)  # Need at least 3 spokes for meaningful betweenness
    
    network, hub, spokes = create_star_network(num_spokes, num_layers)
    calc = MultilayerCentrality(network)
    
    betweenness = calc.multilayer_betweenness_centrality(normalized=True)
    
    # Hub should have highest betweenness (it's on all shortest paths)
    # betweenness may return node or node-layer tuples, aggregate by node
    node_betweenness = {}
    for key, value in betweenness.items():
        if isinstance(key, tuple):
            node = key[0]
        else:
            node = key
        node_betweenness[node] = node_betweenness.get(node, 0) + value
    
    hub_betweenness = node_betweenness.get(hub, 0)
    
    for spoke in spokes:
        spoke_betweenness = node_betweenness.get(spoke, 0)
        # Spokes typically have 0 betweenness (not on paths between other spokes)
        assert hub_betweenness >= spoke_betweenness, \
            f"Hub should have higher betweenness: hub={hub_betweenness}, spoke={spoke_betweenness}"


@pytest.mark.property
@settings(deadline=None, max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    length=st.integers(min_value=4, max_value=7),
    num_layers=st.integers(min_value=1, max_value=3)
)
def test_path_network_endpoints_lowest_centrality(length, num_layers):
    """Test that endpoint nodes have lower centrality in a path network."""
    network, nodes = create_path_network(length, num_layers)
    calc = MultilayerCentrality(network)
    
    # Test with closeness centrality
    closeness = calc.multilayer_closeness_centrality(normalized=True)
    
    # closeness may return node or node-layer tuples, aggregate by node
    node_closeness = {}
    for key, value in closeness.items():
        if isinstance(key, tuple):
            node = key[0]
        else:
            node = key
        node_closeness[node] = node_closeness.get(node, 0) + value
    
    # Endpoints should have lower closeness than middle nodes (on average)
    endpoint_closeness = (node_closeness.get(nodes[0], 0) + node_closeness.get(nodes[-1], 0)) / 2
    middle_nodes = nodes[1:-1]
    
    if middle_nodes:
        middle_closeness = sum(node_closeness.get(n, 0) for n in middle_nodes) / len(middle_nodes)
        
        # Middle nodes should generally have higher closeness
        # (allowing small tolerance for numerical issues)
        assert middle_closeness >= endpoint_closeness - 1e-6, \
            f"Middle nodes should have higher closeness: middle={middle_closeness}, endpoints={endpoint_closeness}"


# ============================================================================
# Property Tests: Scale Invariance
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=5),
    num_layers=st.integers(min_value=1, max_value=2),
    scale_factor=st.floats(min_value=0.5, max_value=10.0)
)
def test_normalized_centrality_scale_invariant(num_nodes, num_layers, scale_factor):
    """Test that normalized centralities are invariant to edge weight scaling."""
    # Create network with unit weights
    network1 = multinet.multi_layer_network(directed=False)
    nodes = [f'N{i}' for i in range(num_nodes)]
    layers = [f'L{i}' for i in range(num_layers)]
    
    for layer in layers:
        for i in range(len(nodes) - 1):
            network1.add_edges([
                [nodes[i], layer, nodes[i+1], layer, 1.0]
            ], input_type='list')
    
    # Create network with scaled weights
    network2 = multinet.multi_layer_network(directed=False)
    for layer in layers:
        for i in range(len(nodes) - 1):
            network2.add_edges([
                [nodes[i], layer, nodes[i+1], layer, scale_factor]
            ], input_type='list')
    
    calc1 = MultilayerCentrality(network1)
    calc2 = MultilayerCentrality(network2)
    
    # Test closeness (normalized)
    closeness1 = calc1.multilayer_closeness_centrality(normalized=True)
    closeness2 = calc2.multilayer_closeness_centrality(normalized=True)
    
    # Rankings should be identical (scale invariant)
    rank1 = get_ranking(closeness1)
    rank2 = get_ranking(closeness2)
    
    for (n1, _), (n2, _) in zip(rank1, rank2):
        assert n1 == n2, "Normalized centrality ranking should be scale invariant"


@pytest.mark.property
@settings(deadline=None, max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=5),
    num_layers=st.integers(min_value=1, max_value=2),
    scale_factor=st.floats(min_value=1.0, max_value=5.0)
)
def test_weighted_degree_scales_linearly(num_nodes, num_layers, scale_factor):
    """Test that weighted degree scales linearly with edge weights."""
    # Create network with unit weights
    network1 = multinet.multi_layer_network(directed=False)
    nodes = [f'N{i}' for i in range(num_nodes)]
    layers = [f'L{i}' for i in range(num_layers)]
    
    for layer in layers:
        for i in range(len(nodes) - 1):
            network1.add_edges([
                [nodes[i], layer, nodes[i+1], layer, 1.0]
            ], input_type='list')
    
    # Create network with scaled weights
    network2 = multinet.multi_layer_network(directed=False)
    for layer in layers:
        for i in range(len(nodes) - 1):
            network2.add_edges([
                [nodes[i], layer, nodes[i+1], layer, scale_factor]
            ], input_type='list')
    
    calc1 = MultilayerCentrality(network1)
    calc2 = MultilayerCentrality(network2)
    
    degree1 = calc1.supra_degree_centrality(weighted=True)
    degree2 = calc2.supra_degree_centrality(weighted=True)
    
    # Weighted degrees should scale linearly
    for node in degree1:
        if node in degree2:
            expected = degree1[node] * scale_factor
            actual = degree2[node]
            assert abs(actual - expected) < 1e-6, \
                f"Weighted degree should scale linearly for {node}: expected {expected}, got {actual}"


# ============================================================================
# Property Tests: Monotonicity
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=4, max_value=6),
    num_layers=st.integers(min_value=1, max_value=2)
)
def test_adding_edges_increases_total_degree(num_nodes, num_layers):
    """Test that networks with more edges have higher total degree."""
    nodes = [f'N{i}' for i in range(num_nodes)]
    layers = [f'L{i}' for i in range(num_layers)]
    
    # Network 1: Create a path (fewer edges)
    network1 = multinet.multi_layer_network(directed=False)
    for layer in layers:
        for i in range(len(nodes) - 1):
            network1.add_edges([
                [nodes[i], layer, nodes[i+1], layer, 1.0]
            ], input_type='list')
    
    calc1 = MultilayerCentrality(network1)
    degree1 = calc1.supra_degree_centrality(weighted=False)
    total_degree1 = sum(degree1.values())
    
    # Network 2: Create a complete graph (more edges)
    network2 = multinet.multi_layer_network(directed=False)
    for layer in layers:
        for i in range(len(nodes)):
            for j in range(i + 1, len(nodes)):
                network2.add_edges([
                    [nodes[i], layer, nodes[j], layer, 1.0]
                ], input_type='list')
    
    calc2 = MultilayerCentrality(network2)
    degree2 = calc2.supra_degree_centrality(weighted=False)
    total_degree2 = sum(degree2.values())
    
    # Complete graph should have higher total degree than path
    assert total_degree2 > total_degree1, \
        f"Complete graph should have higher total degree than path: {total_degree1} -> {total_degree2}"


@pytest.mark.property
@settings(deadline=None, max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=5),
    num_layers=st.integers(min_value=2, max_value=3)
)
def test_more_layers_increases_overlapping_degree(num_nodes, num_layers):
    """Test that adding layers increases overlapping degree centrality."""
    assume(num_layers >= 2)
    
    # Create network with fewer layers
    network1 = multinet.multi_layer_network(directed=False)
    nodes = [f'N{i}' for i in range(num_nodes)]
    layers_subset = [f'L{i}' for i in range(num_layers - 1)]
    
    for layer in layers_subset:
        for i in range(len(nodes) - 1):
            network1.add_edges([
                [nodes[i], layer, nodes[i+1], layer, 1.0]
            ], input_type='list')
    
    # Create network with all layers
    network2 = multinet.multi_layer_network(directed=False)
    layers_all = [f'L{i}' for i in range(num_layers)]
    
    for layer in layers_all:
        for i in range(len(nodes) - 1):
            network2.add_edges([
                [nodes[i], layer, nodes[i+1], layer, 1.0]
            ], input_type='list')
    
    calc1 = MultilayerCentrality(network1)
    calc2 = MultilayerCentrality(network2)
    
    overlap1 = calc1.overlapping_degree_centrality(weighted=False)
    overlap2 = calc2.overlapping_degree_centrality(weighted=False)
    
    # Network with more layers should have higher overlapping degrees
    for node in overlap1:
        if node in overlap2:
            assert overlap2[node] >= overlap1[node], \
                f"More layers should increase overlapping degree for {node}"


# ============================================================================
# Property Tests: Ranking Stability
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=4, max_value=6),
    num_layers=st.integers(min_value=1, max_value=2)
)
def test_degree_ranking_stability(num_nodes, num_layers):
    """Test that degree centrality ranking is stable across multiple computations."""
    network = multinet.multi_layer_network(directed=False)
    nodes = [f'N{i}' for i in range(num_nodes)]
    layers = [f'L{i}' for i in range(num_layers)]
    
    for layer in layers:
        for i in range(len(nodes) - 1):
            network.add_edges([
                [nodes[i], layer, nodes[i+1], layer, 1.0]
            ], input_type='list')
    
    calc = MultilayerCentrality(network)
    
    # Compute degree multiple times
    degree1 = calc.supra_degree_centrality(weighted=False)
    degree2 = calc.supra_degree_centrality(weighted=False)
    
    rank1 = get_ranking(degree1)
    rank2 = get_ranking(degree2)
    
    # Rankings should be identical
    assert rank1 == rank2, "Degree centrality ranking should be stable"


@pytest.mark.property
@settings(deadline=None, max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=5),
    num_layers=st.integers(min_value=1, max_value=2)
)
def test_centrality_consistent_node_set(num_nodes, num_layers):
    """Test that all centrality measures return values for the same node set."""
    network = multinet.multi_layer_network(directed=False)
    nodes = [f'N{i}' for i in range(num_nodes)]
    layers = [f'L{i}' for i in range(num_layers)]
    
    for layer in layers:
        for i in range(len(nodes) - 1):
            network.add_edges([
                [nodes[i], layer, nodes[i+1], layer, 1.0]
            ], input_type='list')
    
    calc = MultilayerCentrality(network)
    
    degree = calc.supra_degree_centrality(weighted=False)
    closeness = calc.multilayer_closeness_centrality(normalized=True)
    
    # Both should have the same node set
    assert set(degree.keys()) == set(closeness.keys()), \
        "Different centrality measures should return values for the same nodes"


# ============================================================================
# Property Tests: Participation Coefficient
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=5),
    num_layers=st.integers(min_value=2, max_value=4)
)
def test_uniform_distribution_increases_participation(num_nodes, num_layers):
    """Test that uniform degree distribution across layers gives higher participation."""
    assume(num_layers >= 2)
    
    nodes = [f'N{i}' for i in range(num_nodes)]
    layers = [f'L{i}' for i in range(num_layers)]
    
    # Network 1: All edges in first layer (low participation)
    network1 = multinet.multi_layer_network(directed=False)
    for i in range(len(nodes) - 1):
        network1.add_edges([
            [nodes[i], layers[0], nodes[i+1], layers[0], 1.0]
        ], input_type='list')
    
    # Network 2: Edges distributed across all layers (high participation)
    network2 = multinet.multi_layer_network(directed=False)
    for i, layer in enumerate(layers):
        # Add edges to each layer
        node_idx = i % (len(nodes) - 1)
        network2.add_edges([
            [nodes[node_idx], layer, nodes[node_idx+1], layer, 1.0]
        ], input_type='list')
    
    calc1 = MultilayerCentrality(network1)
    calc2 = MultilayerCentrality(network2)
    
    pc1 = calc1.participation_coefficient(weighted=False)
    pc2 = calc2.participation_coefficient(weighted=False)
    
    # Average participation should be higher when edges are distributed
    avg_pc1 = np.mean(list(pc1.values()))
    avg_pc2 = np.mean(list(pc2.values()))
    
    # Network 2 should have higher or equal average participation
    # (within tolerance for edge cases)
    assert avg_pc2 >= avg_pc1 - 1e-6, \
        f"Distributing edges across layers should increase participation: {avg_pc1} -> {avg_pc2}"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-m', 'property'])
