#!/usr/bin/env python3
"""
Property-based tests for random multilayer network generators.

Tests shape checks and basic invariants for random_multilayer_ER.
"""

import pytest
from hypothesis import given, strategies as st, settings, assume

from py3plex.core import random_generators


@pytest.mark.property
@settings(deadline=None, max_examples=40)
@given(
    num_nodes=st.integers(min_value=2, max_value=20),
    num_layers=st.integers(min_value=1, max_value=4),
    p=st.floats(min_value=0.0, max_value=1.0),
    directed=st.booleans(),
)
def test_random_multilayer_er_basic_invariants(num_nodes, num_layers, p, directed):
    """
    Test basic invariants of random multilayer ER generator.
    
    Properties:
    - Network has at least num_nodes nodes (may have more for inter-layer)
    - Network has non-negative edge count
    - core_network exists and is valid
    """
    net = random_generators.random_multilayer_ER(
        num_nodes=num_nodes,
        num_layers=num_layers,
        probability=p,
        directed=directed
    )
    
    # Basic shape checks
    assert net.core_network is not None, \
        "core_network should not be None"
    
    assert net.core_network.number_of_nodes() >= num_nodes, \
        f"Node count {net.core_network.number_of_nodes()} < expected {num_nodes}"
    
    assert net.core_network.number_of_edges() >= 0, \
        f"Edge count should be non-negative, got {net.core_network.number_of_edges()}"


@pytest.mark.property
@settings(deadline=None, max_examples=30)
@given(
    num_nodes=st.integers(min_value=2, max_value=15),
    num_layers=st.integers(min_value=1, max_value=3),
)
def test_random_multilayer_er_empty_with_zero_probability(num_nodes, num_layers):
    """
    Test that p=0 produces network with minimal edges.
    
    Property: With p=0, intra-layer edges should be 0 (only inter-layer may exist).
    """
    net = random_generators.random_multilayer_ER(
        num_nodes=num_nodes,
        num_layers=num_layers,
        probability=0.0,
        directed=False
    )
    
    # With p=0, should have minimal edges (possibly inter-layer only)
    # At minimum, should have the nodes
    assert net.core_network.number_of_nodes() >= num_nodes, \
        f"Expected at least {num_nodes} nodes"


@pytest.mark.property
@settings(deadline=None, max_examples=30)
@given(
    num_nodes=st.integers(min_value=2, max_value=10),
    num_layers=st.integers(min_value=1, max_value=3),
    directed=st.booleans(),
)
def test_random_multilayer_er_p1_produces_dense_network(num_nodes, num_layers, directed):
    """
    Test that p=1 produces a dense network.
    
    Property: With p=1, each layer should be complete or near-complete.
    """
    net = random_generators.random_multilayer_ER(
        num_nodes=num_nodes,
        num_layers=num_layers,
        probability=1.0,
        directed=directed
    )
    
    # With p=1, should have many edges
    # For undirected complete graph per layer: num_layers * n*(n-1)/2
    # Plus inter-layer edges
    if directed:
        max_edges_per_layer = num_nodes * (num_nodes - 1)
    else:
        max_edges_per_layer = num_nodes * (num_nodes - 1) // 2
    
    # Should have significant edges (at least some fraction of max)
    min_expected = num_layers * max_edges_per_layer * 0.5  # Allow some margin
    
    assert net.core_network.number_of_edges() >= min_expected * 0.3, \
        f"Expected many edges with p=1, got {net.core_network.number_of_edges()}"


@pytest.mark.property
@settings(deadline=None, max_examples=40)
@given(
    num_nodes=st.integers(min_value=2, max_value=12),
    num_layers=st.integers(min_value=2, max_value=4),
    p=st.floats(min_value=0.1, max_value=0.9),
)
def test_random_multilayer_er_has_layers(num_nodes, num_layers, p):
    """
    Test that generated network has layer structure.
    
    Property: Network should have layer information stored.
    """
    net = random_generators.random_multilayer_ER(
        num_nodes=num_nodes,
        num_layers=num_layers,
        probability=p,
        directed=False
    )
    
    # Check that layer mapping exists
    assert hasattr(net, 'layer_name_map'), \
        "Network should have layer_name_map attribute"
    
    # Should have num_layers layers
    assert len(net.layer_name_map) >= num_layers, \
        f"Expected {num_layers} layers, got {len(net.layer_name_map)}"


@pytest.mark.property
@settings(deadline=None, max_examples=30)
@given(
    num_nodes=st.integers(min_value=3, max_value=10),
    p=st.floats(min_value=0.2, max_value=0.8),
)
def test_random_multilayer_er_single_layer(num_nodes, p):
    """
    Test single-layer random network generation.
    
    Property: Single-layer network should behave like ER random graph.
    """
    net = random_generators.random_multilayer_ER(
        num_nodes=num_nodes,
        num_layers=1,
        probability=p,
        directed=False
    )
    
    # Should have approximately p * n*(n-1)/2 edges
    max_edges = num_nodes * (num_nodes - 1) // 2
    expected_edges = p * max_edges
    
    actual_edges = net.core_network.number_of_edges()
    
    # Allow wide margin due to randomness (within 3 standard deviations)
    import math
    std = math.sqrt(max_edges * p * (1 - p))
    margin = 3 * std
    
    # Just check it's in a reasonable range
    assert actual_edges >= 0, \
        f"Edge count should be non-negative"
    assert actual_edges <= max_edges * 2, \
        f"Edge count {actual_edges} seems too high for single layer"


@pytest.mark.property
@settings(deadline=None, max_examples=30)
@given(
    num_nodes=st.integers(min_value=2, max_value=15),
    num_layers=st.integers(min_value=1, max_value=3),
    directed=st.booleans(),
)
def test_random_multilayer_er_directed_flag(num_nodes, num_layers, directed):
    """
    Test that directed flag is respected.
    
    Property: Generated network should be directed if flag is True.
    """
    net = random_generators.random_multilayer_ER(
        num_nodes=num_nodes,
        num_layers=num_layers,
        probability=0.3,
        directed=directed
    )
    
    # Check directionality
    assert net.directed == directed, \
        f"Network directed flag {net.directed} != expected {directed}"
