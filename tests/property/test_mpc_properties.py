#!/usr/bin/env python3
"""
Property-based tests for algorithms.multicentrality module.

Tests invariants for Multiplex Participation Coefficient (MPC).
"""

import networkx as nx
import pytest
from hypothesis import given, settings, assume, strategies as st
from hypothesis import HealthCheck

# Import multicentrality module
try:
    from py3plex.algorithms.multicentrality import multiplex_participation_coefficient
    from py3plex.core.multinet import multi_layer_network
    MPC_AVAILABLE = True
except ImportError:
    MPC_AVAILABLE = False
    pytest.skip("Multicentrality module not available", allow_module_level=True)


# ============================================================================
# Property Tests: MPC Invariants
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=15, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    n_nodes=st.integers(min_value=3, max_value=10),
    n_layers=st.integers(min_value=2, max_value=5),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_mpc_normalized_range(n_nodes, n_layers, seed):
    """Test that normalized MPC values are in [0, 1]."""
    # Create a multiplex network
    multinet = multi_layer_network()
    
    # Add edges to each layer with same nodes
    for layer_idx in range(n_layers):
        layer_name = f"layer_{layer_idx}"
        for i in range(n_nodes):
            for j in range(i + 1, n_nodes):
                if (seed + i * n_nodes + j + layer_idx) % 3 == 0:
                    multinet.add_edges(
                        [[i, layer_name, j, layer_name, 1.0]],
                        input_type="list"
                    )
    
    # Compute MPC
    mpc = multiplex_participation_coefficient(multinet, normalized=True)
    
    # All values should be in [0, 1]
    for node, value in mpc.items():
        assert 0 <= value <= 1, f"Normalized MPC for node {node} is {value}, expected [0, 1]"


@pytest.mark.property
@settings(deadline=None, max_examples=15, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    n_nodes=st.integers(min_value=3, max_value=10),
    n_layers=st.integers(min_value=2, max_value=5),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_mpc_returns_dict(n_nodes, n_layers, seed):
    """Test that MPC returns a dictionary."""
    # Create a multiplex network
    multinet = multi_layer_network()
    
    # Add edges to each layer
    for layer_idx in range(n_layers):
        layer_name = f"layer_{layer_idx}"
        for i in range(n_nodes):
            for j in range(i + 1, n_nodes):
                if (seed + i * n_nodes + j + layer_idx) % 3 == 0:
                    multinet.add_edges(
                        [[i, layer_name, j, layer_name, 1.0]],
                        input_type="list"
                    )
    
    # Compute MPC
    mpc = multiplex_participation_coefficient(multinet)
    
    # Should return a dictionary
    assert isinstance(mpc, dict), "MPC should return a dictionary"
    # All values should be numeric
    for node, value in mpc.items():
        assert isinstance(value, (int, float)), f"MPC value for node {node} should be numeric"


@pytest.mark.property
@settings(deadline=None, max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    n_nodes=st.integers(min_value=3, max_value=8),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_mpc_isolated_node_zero(n_nodes, seed):
    """Test that isolated nodes have MPC = 0."""
    # Create a multiplex network
    multinet = multi_layer_network()
    
    # Add edges to two layers, but leave node 0 isolated
    for layer_idx in range(2):
        layer_name = f"layer_{layer_idx}"
        for i in range(1, n_nodes):
            for j in range(i + 1, n_nodes):
                if (seed + i * n_nodes + j + layer_idx) % 3 == 0:
                    multinet.add_edges(
                        [[i, layer_name, j, layer_name, 1.0]],
                        input_type="list"
                    )
    
    # Compute MPC
    mpc = multiplex_participation_coefficient(multinet)
    
    # Isolated node should have MPC = 0
    if 0 in mpc:
        assert mpc[0] == 0.0, "Isolated node should have MPC = 0"


@pytest.mark.property
@settings(deadline=None, max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    n_nodes=st.integers(min_value=3, max_value=8),
    n_layers=st.integers(min_value=2, max_value=4)
)
def test_mpc_requires_at_least_two_layers(n_nodes, n_layers):
    """Test that MPC requires at least 2 layers."""
    # Create a network with only one layer
    multinet = multi_layer_network()
    
    # Add edges to only one layer
    layer_name = "single_layer"
    for i in range(n_nodes):
        for j in range(i + 1, n_nodes):
            if (i + j) % 2 == 0:
                multinet.add_edges(
                    [[i, layer_name, j, layer_name, 1.0]],
                    input_type="list"
                )
    
    # Should raise ValueError for single layer
    with pytest.raises(ValueError, match="at least 2 layers"):
        multiplex_participation_coefficient(multinet)


@pytest.mark.property
@settings(deadline=None, max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    n_nodes=st.integers(min_value=3, max_value=8),
    n_layers=st.integers(min_value=2, max_value=4),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_mpc_unnormalized_range(n_nodes, n_layers, seed):
    """Test that unnormalized MPC values are in valid range."""
    # Create a multiplex network
    multinet = multi_layer_network()
    
    # Add edges to each layer
    for layer_idx in range(n_layers):
        layer_name = f"layer_{layer_idx}"
        for i in range(n_nodes):
            for j in range(i + 1, n_nodes):
                if (seed + i * n_nodes + j + layer_idx) % 3 == 0:
                    multinet.add_edges(
                        [[i, layer_name, j, layer_name, 1.0]],
                        input_type="list"
                    )
    
    # Compute unnormalized MPC
    mpc = multiplex_participation_coefficient(multinet, normalized=False)
    
    # Unnormalized MPC should be in [0, 1 - 1/L]
    max_value = 1 - 1/n_layers
    for node, value in mpc.items():
        assert 0 <= value <= 1, \
            f"Unnormalized MPC for node {node} is {value}, expected [0, {max_value}]"


@pytest.mark.property
@settings(deadline=None, max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    n_nodes=st.integers(min_value=3, max_value=8),
    n_layers=st.integers(min_value=2, max_value=4),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_mpc_numeric_stability(n_nodes, n_layers, seed):
    """Test that MPC computation is numerically stable."""
    # Create a multiplex network
    multinet = multi_layer_network()
    
    # Add edges to each layer
    for layer_idx in range(n_layers):
        layer_name = f"layer_{layer_idx}"
        for i in range(n_nodes):
            for j in range(i + 1, n_nodes):
                if (seed + i * n_nodes + j + layer_idx) % 3 == 0:
                    multinet.add_edges(
                        [[i, layer_name, j, layer_name, 1.0]],
                        input_type="list"
                    )
    
    # Compute MPC
    mpc = multiplex_participation_coefficient(multinet)
    
    # All values should be finite (no inf or nan)
    import math
    for node, value in mpc.items():
        assert math.isfinite(value), \
            f"MPC for node {node} is not finite: {value}"
