#!/usr/bin/env python3
"""
Property-based tests for Leiden multilayer community detection.

Tests properties of the Leiden algorithm for multilayer networks:
- Every node assigned to exactly one community
- No foreign nodes in partition
- Invariance properties under graph transformations
- Non-triviality for separated components
- Determinism with seed
- Modularity bounds
"""

import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from py3plex.core.multinet import multi_layer_network

# Guard for leiden availability
try:
    from py3plex.algorithms.community_detection.leiden_multilayer import (
        leiden_multilayer,
        LeidenResult,
    )
    LEIDEN_AVAILABLE = True
except ImportError:
    LEIDEN_AVAILABLE = False
    leiden_multilayer = None
    LeidenResult = None


@pytest.mark.skipif(not LEIDEN_AVAILABLE, reason="Leiden not available")
@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(n=st.integers(min_value=4, max_value=10))
def test_leiden_every_node_assigned(n):
    """
    Test that every node-layer pair is assigned to exactly one community.
    
    Property: All node-layer tuples in network appear in partition.
    """
    # Create simple 2-layer network
    net = multi_layer_network(directed=False)
    
    # Add nodes in two layers
    for i in range(n):
        net.add_nodes([
            {'source': f'n{i}', 'type': 'layer1'},
            {'source': f'n{i}', 'type': 'layer2'},
        ])
    
    # Add some edges within each layer
    for i in range(n-1):
        net.add_edges([
            {'source': f'n{i}', 'target': f'n{i+1}', 
             'source_type': 'layer1', 'target_type': 'layer1'},
            {'source': f'n{i}', 'target': f'n{i+1}', 
             'source_type': 'layer2', 'target_type': 'layer2'},
        ])
    
    # Run Leiden
    result = leiden_multilayer(net, resolution=1.0, interlayer_coupling=0.5, seed=42)
    
    # Check all node-layer pairs assigned
    node_layers = set()
    for node in net.get_nodes():
        node_layers.add(node)
    
    assert set(result.communities.keys()) == node_layers, \
        "Not all node-layer pairs assigned to communities"


@pytest.mark.skipif(not LEIDEN_AVAILABLE, reason="Leiden not available")
@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(n=st.integers(min_value=4, max_value=10))
def test_leiden_no_foreign_nodes(n):
    """
    Test that partition contains no nodes not in the graph.
    
    Property: partition.keys() ⊆ network nodes
    """
    net = multi_layer_network(directed=False)
    
    # Add nodes and edges
    for i in range(n):
        net.add_nodes([{'source': f'n{i}', 'type': 'L1'}])
    
    for i in range(n-1):
        net.add_edges([
            {'source': f'n{i}', 'target': f'n{i+1}', 
             'source_type': 'L1', 'target_type': 'L1'}
        ])
    
    result = leiden_multilayer(net, seed=42)
    
    # Check no foreign nodes
    partition_nodes = set(result.communities.keys())
    graph_nodes = set(net.get_nodes())
    
    assert partition_nodes.issubset(graph_nodes), \
        f"Foreign nodes in partition: {partition_nodes - graph_nodes}"


@pytest.mark.skipif(not LEIDEN_AVAILABLE, reason="Leiden not available")
@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(n=st.integers(min_value=4, max_value=10))
def test_leiden_community_ids_valid(n):
    """
    Test that community IDs are valid non-negative integers.
    
    Property: All community IDs should be non-negative integers.
    """
    net = multi_layer_network(directed=False)
    
    for i in range(n):
        net.add_nodes([{'source': f'n{i}', 'type': 'L1'}])
    
    for i in range(n-1):
        net.add_edges([
            {'source': f'n{i}', 'target': f'n{i+1}', 
             'source_type': 'L1', 'target_type': 'L1'}
        ])
    
    result = leiden_multilayer(net, seed=42)
    
    # Check all community IDs are valid
    for comm_id in result.communities.values():
        assert isinstance(comm_id, int), \
            f"Community ID not an integer: {comm_id}"
        assert comm_id >= 0, \
            f"Community ID negative: {comm_id}"


@pytest.mark.skipif(not LEIDEN_AVAILABLE, reason="Leiden not available")
@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(n=st.integers(min_value=3, max_value=10))
def test_leiden_at_least_one_community(n):
    """
    Test that Leiden always finds at least one community.
    
    Property: Number of communities >= 1.
    """
    net = multi_layer_network(directed=False)
    
    for i in range(n):
        net.add_nodes([{'source': f'n{i}', 'type': 'L1'}])
    
    # Add path edges
    for i in range(n-1):
        net.add_edges([
            {'source': f'n{i}', 'target': f'n{i+1}', 
             'source_type': 'L1', 'target_type': 'L1'}
        ])
    
    result = leiden_multilayer(net, seed=42)
    n_communities = len(set(result.communities.values()))
    
    assert n_communities >= 1, \
        f"Found {n_communities} communities (expected >= 1)"


@pytest.mark.skipif(not LEIDEN_AVAILABLE, reason="Leiden not available")
@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(n=st.integers(min_value=2, max_value=10))
def test_leiden_at_most_n_times_layers_communities(n):
    """
    Test that Leiden finds at most n * num_layers communities.
    
    Property: Number of communities <= num_node_layer_pairs.
    """
    net = multi_layer_network(directed=False)
    
    # Create 2-layer network
    for i in range(n):
        net.add_nodes([
            {'source': f'n{i}', 'type': 'L1'},
            {'source': f'n{i}', 'type': 'L2'},
        ])
    
    result = leiden_multilayer(net, seed=42)
    n_communities = len(set(result.communities.values()))
    n_node_layers = len(result.communities)
    
    assert n_communities <= n_node_layers, \
        f"Found {n_communities} communities but only {n_node_layers} node-layer pairs"


@pytest.mark.skipif(not LEIDEN_AVAILABLE, reason="Leiden not available")
@pytest.mark.property
@settings(deadline=None, max_examples=15)
@given(n_per_component=st.integers(min_value=3, max_value=5))
def test_leiden_disconnected_components_separate_communities(n_per_component):
    """
    Test that disconnected components are in different communities.
    
    Property: For a graph with K disconnected components,
    number of communities >= K.
    """
    net = multi_layer_network(directed=False)
    
    # Create 2 disconnected components in same layer
    for comp in range(2):
        for i in range(n_per_component):
            node_id = f'c{comp}_n{i}'
            net.add_nodes([{'source': node_id, 'type': 'L1'}])
        
        # Make each component a clique
        for i in range(n_per_component):
            for j in range(i+1, n_per_component):
                net.add_edges([{
                    'source': f'c{comp}_n{i}',
                    'target': f'c{comp}_n{j}',
                    'source_type': 'L1',
                    'target_type': 'L1'
                }])
    
    result = leiden_multilayer(net, seed=42)
    n_communities = len(set(result.communities.values()))
    
    # Should find at least 2 communities (one per component)
    assert n_communities >= 2, \
        f"Found {n_communities} communities but have 2 disconnected components"


@pytest.mark.skipif(not LEIDEN_AVAILABLE, reason="Leiden not available")
@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(n=st.integers(min_value=4, max_value=10))
def test_leiden_deterministic_with_seed(n):
    """
    Test that Leiden is deterministic when given same random_state.
    
    Property: Same random_state produces same partition.
    """
    net = multi_layer_network(directed=False)
    
    for i in range(n):
        net.add_nodes([{'source': f'n{i}', 'type': 'L1'}])
    
    for i in range(n-1):
        net.add_edges([
            {'source': f'n{i}', 'target': f'n{i+1}', 
             'source_type': 'L1', 'target_type': 'L1'}
        ])
    
    seed = 42
    
    # Run twice with same seed
    result1 = leiden_multilayer(net, seed=seed)
    result2 = leiden_multilayer(net, seed=seed)
    
    # Should be identical
    assert result1.communities == result2.communities, \
        "Leiden not deterministic with same random_state"


@pytest.mark.skipif(not LEIDEN_AVAILABLE, reason="Leiden not available")
@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(n=st.integers(min_value=4, max_value=10))
def test_leiden_modularity_in_bounds(n):
    """
    Test that modularity score is within theoretical bounds.
    
    Property: -0.5 <= modularity <= 1.0
    """
    net = multi_layer_network(directed=False)
    
    for i in range(n):
        net.add_nodes([{'source': f'n{i}', 'type': 'L1'}])
    
    # Add cycle edges
    for i in range(n):
        net.add_edges([
            {'source': f'n{i}', 'target': f'n{(i+1)%n}', 
             'source_type': 'L1', 'target_type': 'L1'}
        ])
    
    result = leiden_multilayer(net, seed=42)
    
    assert -0.5 <= result.modularity <= 1.0, \
        f"Modularity {result.modularity} out of bounds [-0.5, 1.0]"


@pytest.mark.skipif(not LEIDEN_AVAILABLE, reason="Leiden not available")
@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(n=st.integers(min_value=4, max_value=10))
def test_leiden_partition_covers_graph(n):
    """
    Test that partition covers all node-layer pairs.
    
    Property: Union of all communities == all node-layer pairs.
    """
    net = multi_layer_network(directed=False)
    
    for i in range(n):
        net.add_nodes([{'source': f'n{i}', 'type': 'L1'}])
    
    for i in range(n-1):
        net.add_edges([
            {'source': f'n{i}', 'target': f'n{i+1}', 
             'source_type': 'L1', 'target_type': 'L1'}
        ])
    
    result = leiden_multilayer(net, seed=42)
    
    # Get all node-layer pairs in communities
    nodes_in_communities = set(result.communities.keys())
    graph_nodes = set(net.get_nodes())
    
    # Should be equal
    assert nodes_in_communities == graph_nodes, \
        "Partition doesn't cover all node-layer pairs"


@pytest.mark.skipif(not LEIDEN_AVAILABLE, reason="Leiden not available")
@pytest.mark.property
@settings(deadline=None, max_examples=15)
@given(resolution=st.floats(min_value=0.5, max_value=2.0))
def test_leiden_gamma_parameter_valid(resolution):
    """
    Test that Leiden accepts valid resolution parameters.
    
    Property: Algorithm should run successfully for resolution in [0.5, 2.0].
    """
    net = multi_layer_network(directed=False)
    
    # Small fixed network
    for i in range(5):
        net.add_nodes([{'source': f'n{i}', 'type': 'L1'}])
    
    for i in range(4):
        net.add_edges([
            {'source': f'n{i}', 'target': f'n{i+1}', 
             'source_type': 'L1', 'target_type': 'L1'}
        ])
    
    # Should not raise exception
    result = leiden_multilayer(net, resolution=resolution, seed=42)
    
    assert isinstance(result, LeidenResult), \
        f"Expected LeidenResult, got {type(result)}"


@pytest.mark.skipif(not LEIDEN_AVAILABLE, reason="Leiden not available")
@pytest.mark.property
@settings(deadline=None, max_examples=15)
@given(coupling=st.floats(min_value=0.0, max_value=2.0))
def test_leiden_omega_parameter_valid(coupling):
    """
    Test that Leiden accepts valid interlayer_coupling parameters.
    
    Property: Algorithm should run successfully for interlayer_coupling in [0.0, 2.0].
    """
    net = multi_layer_network(directed=False)
    
    # 2-layer network
    for i in range(5):
        net.add_nodes([
            {'source': f'n{i}', 'type': 'L1'},
            {'source': f'n{i}', 'type': 'L2'},
        ])
    
    for i in range(4):
        net.add_edges([
            {'source': f'n{i}', 'target': f'n{i+1}', 
             'source_type': 'L1', 'target_type': 'L1'},
            {'source': f'n{i}', 'target': f'n{i+1}', 
             'source_type': 'L2', 'target_type': 'L2'},
        ])
    
    # Should not raise exception
    result = leiden_multilayer(net, resolution=1.0, interlayer_coupling=coupling, seed=42)
    
    assert isinstance(result, LeidenResult), \
        f"Expected LeidenResult, got {type(result)}"


@pytest.mark.skipif(not LEIDEN_AVAILABLE, reason="Leiden not available")
@pytest.mark.property
@settings(deadline=None, max_examples=15)
@given(n=st.integers(min_value=3, max_value=8))
def test_leiden_complete_graph_single_community(n):
    """
    Test that complete graph tends toward single community.
    
    Property: Complete graph should have relatively few communities.
    """
    net = multi_layer_network(directed=False)
    
    # Create complete graph
    for i in range(n):
        net.add_nodes([{'source': f'n{i}', 'type': 'L1'}])
    
    for i in range(n):
        for j in range(i+1, n):
            net.add_edges([
                {'source': f'n{i}', 'target': f'n{j}', 
                 'source_type': 'L1', 'target_type': 'L1'}
            ])
    
    result = leiden_multilayer(net, resolution=1.0, seed=42)
    n_communities = len(set(result.communities.values()))
    
    # Complete graph should have few communities (often 1)
    assert n_communities <= max(2, n // 2), \
        f"Complete graph has {n_communities} communities (expected <= {max(2, n//2)})"
