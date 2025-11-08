#!/usr/bin/env python3
"""
Property-based tests for algorithms.multicentrality module.

Tests invariants and properties of Multiplex Participation Coefficient:
- MPC bounded between 0 and 1 (when normalized)
- MPC = 0 for isolated nodes
- MPC increases with more even distribution across layers
- MPC invariants for multiplex networks
"""

import networkx as nx
import pytest
from hypothesis import given, settings, assume, strategies as st
from hypothesis import HealthCheck

# Import multicentrality module
try:
    from py3plex.algorithms.multicentrality import (
        multiplex_participation_coefficient,
    )
    from py3plex.core import multinet
    MULTICENTRALITY_AVAILABLE = True
except ImportError:
    MULTICENTRALITY_AVAILABLE = False
    pytest.skip("Multicentrality module not available", allow_module_level=True)


# ============================================================================
# Property Tests: MPC Bounds
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=15, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=10),
    num_layers=st.integers(min_value=2, max_value=4),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_mpc_normalized_bounded_zero_one(num_nodes, num_layers, seed):
    """Property: Normalized MPC is bounded between 0 and 1."""
    # Create a multiplex network
    net = multinet.multi_layer_network()
    
    # Add nodes and edges for each layer
    for layer_idx in range(num_layers):
        layer_name = f"layer_{layer_idx}"
        for node_idx in range(num_nodes):
            node_name = f"node_{node_idx}"
            net.add_nodes({
                "source": node_name,
                "type": layer_name
            })
        
        # Add some random edges within the layer
        import random
        random.seed(seed + layer_idx)
        for _ in range(num_nodes):
            i = random.randint(0, num_nodes - 1)
            j = random.randint(0, num_nodes - 1)
            if i != j:
                net.add_edges({
                    "source": f"node_{i}",
                    "target": f"node_{j}",
                    "source_type": layer_name,
                    "target_type": layer_name,
                    "weight": 1.0
                })
    
    assume(net.number_of_edges() > 0)
    
    # Compute MPC with normalization
    mpc = multiplex_participation_coefficient(net, normalized=True, check_multiplex=True)
    
    # All MPC values should be in [0, 1]
    for node, value in mpc.items():
        assert 0.0 <= value <= 1.0, \
            f"Normalized MPC for node {node} should be in [0, 1], got {value}"


@pytest.mark.property
@settings(deadline=None, max_examples=15, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=10),
    num_layers=st.integers(min_value=2, max_value=4),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_mpc_non_negative(num_nodes, num_layers, seed):
    """Property: MPC values are always non-negative."""
    # Create a multiplex network
    net = multinet.multi_layer_network()
    
    # Add nodes and edges
    for layer_idx in range(num_layers):
        layer_name = f"layer_{layer_idx}"
        for node_idx in range(num_nodes):
            node_name = f"node_{node_idx}"
            net.add_nodes({
                "source": node_name,
                "type": layer_name
            })
        
        # Add edges
        import random
        random.seed(seed + layer_idx)
        for _ in range(num_nodes):
            i = random.randint(0, num_nodes - 1)
            j = random.randint(0, num_nodes - 1)
            if i != j:
                net.add_edges({
                    "source": f"node_{i}",
                    "target": f"node_{j}",
                    "source_type": layer_name,
                    "target_type": layer_name,
                    "weight": 1.0
                })
    
    assume(net.number_of_edges() > 0)
    
    # Compute MPC (normalized and unnormalized)
    mpc_normalized = multiplex_participation_coefficient(net, normalized=True, check_multiplex=True)
    mpc_unnormalized = multiplex_participation_coefficient(net, normalized=False, check_multiplex=True)
    
    # All values should be non-negative
    for node, value in mpc_normalized.items():
        assert value >= 0.0, f"MPC should be non-negative, got {value} for node {node}"
    
    for node, value in mpc_unnormalized.items():
        assert value >= 0.0, f"Unnormalized MPC should be non-negative, got {value} for node {node}"


@pytest.mark.property
@settings(deadline=None, max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=8),
    num_layers=st.integers(min_value=2, max_value=4)
)
def test_mpc_isolated_node_is_zero(num_nodes, num_layers):
    """Property: Isolated nodes have MPC = 0."""
    # Create a multiplex network with one isolated node
    net = multinet.multi_layer_network()
    
    # Add all nodes
    for layer_idx in range(num_layers):
        layer_name = f"layer_{layer_idx}"
        for node_idx in range(num_nodes):
            node_name = f"node_{node_idx}"
            net.add_nodes({
                "source": node_name,
                "type": layer_name
            })
    
    # Add edges only between nodes 1 to num_nodes-1, leaving node_0 isolated
    for layer_idx in range(num_layers):
        layer_name = f"layer_{layer_idx}"
        for i in range(1, num_nodes):
            for j in range(i + 1, num_nodes):
                net.add_edges({
                    "source": f"node_{i}",
                    "target": f"node_{j}",
                    "source_type": layer_name,
                    "target_type": layer_name,
                    "weight": 1.0
                })
    
    assume(net.number_of_edges() > 0)
    
    # Compute MPC
    mpc = multiplex_participation_coefficient(net, normalized=True, check_multiplex=True)
    
    # Isolated node should have MPC = 0
    if "node_0" in mpc:
        assert mpc["node_0"] == 0.0, \
            f"Isolated node should have MPC = 0, got {mpc['node_0']}"


@pytest.mark.property
@settings(deadline=None, max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=8),
    num_layers=st.integers(min_value=2, max_value=4)
)
def test_mpc_uniform_distribution_high(num_nodes, num_layers):
    """Property: Nodes with uniform degree across layers have high MPC."""
    # Create a multiplex network where each node has same degree in all layers
    net = multinet.multi_layer_network()
    
    # Add nodes and create regular structure
    for layer_idx in range(num_layers):
        layer_name = f"layer_{layer_idx}"
        for node_idx in range(num_nodes):
            node_name = f"node_{node_idx}"
            net.add_nodes({
                "source": node_name,
                "type": layer_name
            })
        
        # Create a cycle so all nodes have degree 2 in each layer
        for i in range(num_nodes):
            next_i = (i + 1) % num_nodes
            net.add_edges({
                "source": f"node_{i}",
                "target": f"node_{next_i}",
                "source_type": layer_name,
                "target_type": layer_name,
                "weight": 1.0
            })
    
    # Compute MPC
    mpc = multiplex_participation_coefficient(net, normalized=True, check_multiplex=True)
    
    # All nodes should have high MPC (close to 1) since degrees are uniform
    for node, value in mpc.items():
        # With uniform distribution across layers, MPC should be high
        # For L layers with equal participation, normalized MPC approaches 1
        expected_min = (num_layers - 1) / num_layers * 0.5  # Allow some tolerance
        assert value >= expected_min or value == 1.0, \
            f"Node {node} with uniform participation should have MPC >= {expected_min}, got {value}"


@pytest.mark.property
@settings(deadline=None, max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=8),
    num_layers=st.integers(min_value=3, max_value=4)
)
def test_mpc_concentrated_distribution_low(num_nodes, num_layers):
    """Property: Nodes with all degree in one layer have low MPC."""
    # Create a multiplex network where node_0 has all edges in layer_0 only
    net = multinet.multi_layer_network()
    
    # Add all nodes
    for layer_idx in range(num_layers):
        layer_name = f"layer_{layer_idx}"
        for node_idx in range(num_nodes):
            node_name = f"node_{node_idx}"
            net.add_nodes({
                "source": node_name,
                "type": layer_name
            })
    
    # Add edges for node_0 only in layer_0
    for i in range(1, num_nodes):
        net.add_edges({
            "source": "node_0",
            "target": f"node_{i}",
            "source_type": "layer_0",
            "target_type": "layer_0",
            "weight": 1.0
        })
    
    # Add some edges for other nodes in other layers to make it valid
    for layer_idx in range(1, num_layers):
        layer_name = f"layer_{layer_idx}"
        for i in range(1, min(num_nodes, 3)):
            for j in range(i + 1, min(num_nodes, 3)):
                net.add_edges({
                    "source": f"node_{i}",
                    "target": f"node_{j}",
                    "source_type": layer_name,
                    "target_type": layer_name,
                    "weight": 1.0
                })
    
    assume(net.number_of_edges() > 0)
    
    # Compute MPC
    mpc = multiplex_participation_coefficient(net, normalized=True, check_multiplex=True)
    
    # node_0 should have low MPC (close to 0) since all degree is in one layer
    if "node_0" in mpc:
        assert mpc["node_0"] < 0.5, \
            f"Node with concentrated participation should have low MPC, got {mpc['node_0']}"


# ============================================================================
# Property Tests: MPC Consistency
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=8),
    num_layers=st.integers(min_value=2, max_value=4),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_mpc_all_nodes_present(num_nodes, num_layers, seed):
    """Property: MPC returns value for all nodes in the network."""
    # Create a multiplex network
    net = multinet.multi_layer_network()
    
    expected_nodes = set()
    
    # Add nodes and edges
    for layer_idx in range(num_layers):
        layer_name = f"layer_{layer_idx}"
        for node_idx in range(num_nodes):
            node_name = f"node_{node_idx}"
            expected_nodes.add(node_name)
            net.add_nodes({
                "source": node_name,
                "type": layer_name
            })
        
        # Add some edges
        import random
        random.seed(seed + layer_idx)
        for _ in range(num_nodes):
            i = random.randint(0, num_nodes - 1)
            j = random.randint(0, num_nodes - 1)
            if i != j:
                net.add_edges({
                    "source": f"node_{i}",
                    "target": f"node_{j}",
                    "source_type": layer_name,
                    "target_type": layer_name,
                    "weight": 1.0
                })
    
    assume(net.number_of_edges() > 0)
    
    # Compute MPC
    mpc = multiplex_participation_coefficient(net, normalized=True, check_multiplex=True)
    
    # Should have MPC for all nodes
    assert set(mpc.keys()) == expected_nodes, \
        f"MPC should cover all nodes. Expected {expected_nodes}, got {set(mpc.keys())}"


@pytest.mark.property
@settings(deadline=None, max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=8),
    num_layers=st.integers(min_value=2, max_value=3),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_mpc_unnormalized_less_than_normalized(num_nodes, num_layers, seed):
    """Property: Unnormalized MPC ≤ Normalized MPC (due to normalization factor)."""
    # Create a multiplex network
    net = multinet.multi_layer_network()
    
    # Add nodes and edges
    for layer_idx in range(num_layers):
        layer_name = f"layer_{layer_idx}"
        for node_idx in range(num_nodes):
            node_name = f"node_{node_idx}"
            net.add_nodes({
                "source": node_name,
                "type": layer_name
            })
        
        # Add edges
        import random
        random.seed(seed + layer_idx)
        for _ in range(num_nodes):
            i = random.randint(0, num_nodes - 1)
            j = random.randint(0, num_nodes - 1)
            if i != j:
                net.add_edges({
                    "source": f"node_{i}",
                    "target": f"node_{j}",
                    "source_type": layer_name,
                    "target_type": layer_name,
                    "weight": 1.0
                })
    
    assume(net.number_of_edges() > 0)
    
    # Compute both normalized and unnormalized MPC
    mpc_normalized = multiplex_participation_coefficient(net, normalized=True, check_multiplex=True)
    mpc_unnormalized = multiplex_participation_coefficient(net, normalized=False, check_multiplex=True)
    
    # Normalized should be >= unnormalized (multiplied by L/(L-1) > 1)
    for node in mpc_normalized.keys():
        if node in mpc_unnormalized:
            assert mpc_normalized[node] >= mpc_unnormalized[node] - 1e-10, \
                f"Normalized MPC should be >= unnormalized for node {node}"


# ============================================================================
# Property Tests: MPC Special Cases
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=8)
)
def test_mpc_two_layers_bounds(num_nodes):
    """Property: For 2 layers, MPC is bounded [0, 1] when normalized."""
    # Create a 2-layer multiplex network
    net = multinet.multi_layer_network()
    num_layers = 2
    
    # Add nodes
    for layer_idx in range(num_layers):
        layer_name = f"layer_{layer_idx}"
        for node_idx in range(num_nodes):
            node_name = f"node_{node_idx}"
            net.add_nodes({
                "source": node_name,
                "type": layer_name
            })
    
    # Add edges in layer 0
    for i in range(num_nodes - 1):
        net.add_edges({
            "source": f"node_{i}",
            "target": f"node_{i+1}",
            "source_type": "layer_0",
            "target_type": "layer_0",
            "weight": 1.0
        })
    
    # Add edges in layer 1
    for i in range(0, num_nodes - 1, 2):
        if i + 1 < num_nodes:
            net.add_edges({
                "source": f"node_{i}",
                "target": f"node_{i+1}",
                "source_type": "layer_1",
                "target_type": "layer_1",
                "weight": 1.0
            })
    
    assume(net.number_of_edges() > 0)
    
    # Compute MPC
    mpc = multiplex_participation_coefficient(net, normalized=True, check_multiplex=True)
    
    # All MPC values should be in [0, 1]
    for node, value in mpc.items():
        assert 0.0 <= value <= 1.0, \
            f"MPC should be in [0, 1] for node {node}, got {value}"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-m', 'property'])
