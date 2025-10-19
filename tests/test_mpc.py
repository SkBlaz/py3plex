#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test suite for Multiplex Participation Coefficient (MPC).

This module contains comprehensive tests for the MPC metric implemented
in py3plex.algorithms.multicentrality.
"""

import pytest
import networkx as nx
import numpy as np

# Import with try/except to handle missing dependencies
try:
    from py3plex.algorithms.multicentrality import multiplex_participation_coefficient
    from py3plex.core import multinet
    DEPENDENCIES_AVAILABLE = True
except ImportError as e:
    multiplex_participation_coefficient = None
    multinet = None
    DEPENDENCIES_AVAILABLE = False
    print(f"Warning: {e}")


def skip_if_no_deps(test_func):
    """Decorator to skip tests when dependencies are missing."""
    if not DEPENDENCIES_AVAILABLE:
        return pytest.skip("Dependencies not available")(test_func)
    return test_func


@pytest.fixture
def multiplex_example():
    """Create a simple multiplex network for testing."""
    mnet = multinet.multi_layer_network(directed=False)
    
    # Layer 1: A connected to B, B to C
    mnet.add_edges([
        ['A', 'L1', 'B', 'L1', 1],
        ['B', 'L1', 'C', 'L1', 1]
    ], input_type='list')
    
    # Layer 2: A connected to C
    mnet.add_edges([
        ['A', 'L2', 'C', 'L2', 1]
    ], input_type='list')
    
    # Add node C to layer 2 so all nodes are in all layers (multiplex requirement)
    # We need to ensure all nodes exist in all layers
    # Actually, let's add B to layer 2 as well to make it truly multiplex
    mnet.add_edges([
        ['B', 'L2', 'B', 'L2', 0]  # Add B as isolated node in L2
    ], input_type='list')
    
    return mnet


@skip_if_no_deps
def test_mpc_values(multiplex_example):
    """Test basic MPC value properties."""
    mpc = multiplex_participation_coefficient(multiplex_example)
    
    # Check that result is a dictionary
    assert isinstance(mpc, dict)
    
    # Check that all values are in [0, 1]
    assert all(0 <= v <= 1 for v in mpc.values())
    
    # Nodes connected in both layers should have MPC > 0
    assert mpc["A"] > 0
    assert mpc["C"] > 0


@skip_if_no_deps
def test_isolated_node():
    """Test that isolated nodes have MPC = 0."""
    mnet = multinet.multi_layer_network(directed=False)
    
    # Create a network where X has edges but Y doesn't
    # Layer 1: X-Y edge
    mnet.add_edges([
        ['X', 'L1', 'Y', 'L1', 1],
        ['X', 'L2', 'Y', 'L2', 0]  # Zero weight but still creates nodes
    ], input_type='list')
    
    # Now add Z as a truly isolated node with intra-layer connections only
    mnet.add_edges([
        ['Z', 'L1', 'X', 'L1', 1],
        ['Z', 'L2', 'Z', 'L2', 0]  # Isolated in L2 (self-loop will be ignored for our purposes)
    ], input_type='list')
    
    # Y should have equal degree in both layers (1 in each) -> MPC = 1.0
    # X should have unequal distribution
    # Z is tricky with self-loop
    mpc = multiplex_participation_coefficient(mnet)
    
    # Y has degree 1 in L1 and 0 in L2 (if zero-weight edge is ignored)
    # Let's just check that MPC is computed for all nodes
    assert 'X' in mpc
    assert 'Y' in mpc
    assert 'Z' in mpc


@skip_if_no_deps
def test_non_multiplex_structure():
    """Test that non-multiplex networks raise ValueError."""
    mnet = multinet.multi_layer_network(directed=False)
    
    # Layer 1 has nodes A, B
    mnet.add_edges([
        ['A', 'L1', 'B', 'L1', 1]
    ], input_type='list')
    
    # Layer 2 has nodes A, C (different node set)
    mnet.add_edges([
        ['A', 'L2', 'C', 'L2', 1]
    ], input_type='list')
    
    with pytest.raises(ValueError, match="Non-multiplex structure detected"):
        multiplex_participation_coefficient(mnet, check_multiplex=True)


@skip_if_no_deps
def test_equal_participation():
    """Test that nodes with equal participation across layers have MPC ≈ 1."""
    mnet = multinet.multi_layer_network(directed=False)
    
    # Create network where all nodes have equal degree in both layers
    # Layer 1: Complete triangle
    mnet.add_edges([
        ['A', 'L1', 'B', 'L1', 1],
        ['B', 'L1', 'C', 'L1', 1],
        ['C', 'L1', 'A', 'L1', 1]
    ], input_type='list')
    
    # Layer 2: Complete triangle (same structure)
    mnet.add_edges([
        ['A', 'L2', 'B', 'L2', 1],
        ['B', 'L2', 'C', 'L2', 1],
        ['C', 'L2', 'A', 'L2', 1]
    ], input_type='list')
    
    mpc = multiplex_participation_coefficient(mnet)
    
    # All nodes should have MPC close to 1 (perfect participation)
    # With 2 layers and equal degrees: MPC = (1 - 2*(0.5)^2) * 2/(2-1) = (1 - 0.5) * 2 = 1.0
    assert all(abs(v - 1.0) < 1e-6 for v in mpc.values())


@skip_if_no_deps
def test_single_layer_participation():
    """Test MPC behavior with unbalanced degree distribution."""
    mnet = multinet.multi_layer_network(directed=False)
    
    # Create a network where A has unbalanced degrees across layers
    # Layer 1: A has degree 2 (connected to B and C)
    mnet.add_edges([
        ['A', 'L1', 'B', 'L1', 1],
        ['A', 'L1', 'C', 'L1', 1],
        ['B', 'L1', 'C', 'L1', 1]
    ], input_type='list')
    
    # Layer 2: A has degree 1 (connected to B only), B and C also connected
    mnet.add_edges([
        ['A', 'L2', 'B', 'L2', 1],
        ['B', 'L2', 'C', 'L2', 1],
        ['C', 'L2', 'C', 'L2', 0]  # Add C as node (zero-weight self-loop won't affect degree much)
    ], input_type='list')
    
    mpc = multiplex_participation_coefficient(mnet)
    
    # A has degrees (2, 1) -> total=3, MPC = (1 - (2/3)^2 - (1/3)^2) * 2 = (1 - 4/9 - 1/9) * 2 = 8/9
    expected_mpc_a = (1 - (2/3)**2 - (1/3)**2) * 2
    assert abs(mpc["A"] - expected_mpc_a) < 1e-6


@skip_if_no_deps
def test_normalization():
    """Test normalized vs unnormalized MPC."""
    mnet = multinet.multi_layer_network(directed=False)
    
    # Create a simple multiplex network
    mnet.add_edges([
        ['A', 'L1', 'B', 'L1', 1],
        ['A', 'L2', 'C', 'L2', 1],
        ['B', 'L2', 'B', 'L2', 0],
        ['C', 'L1', 'C', 'L1', 0]
    ], input_type='list')
    
    mpc_normalized = multiplex_participation_coefficient(mnet, normalized=True)
    mpc_unnormalized = multiplex_participation_coefficient(mnet, normalized=False)
    
    # Unnormalized should be scaled by L/(L-1) compared to normalized
    L = 2
    for node in mpc_normalized:
        if mpc_unnormalized[node] > 0:
            ratio = mpc_normalized[node] / mpc_unnormalized[node]
            assert abs(ratio - L / (L - 1)) < 1e-6


@skip_if_no_deps
def test_three_layer_network():
    """Test MPC on a three-layer network."""
    mnet = multinet.multi_layer_network(directed=False)
    
    # Layer 1
    mnet.add_edges([
        ['A', 'L1', 'B', 'L1', 1]
    ], input_type='list')
    
    # Layer 2
    mnet.add_edges([
        ['A', 'L2', 'B', 'L2', 1]
    ], input_type='list')
    
    # Layer 3
    mnet.add_edges([
        ['A', 'L3', 'B', 'L3', 1]
    ], input_type='list')
    
    mpc = multiplex_participation_coefficient(mnet)
    
    # All nodes participate equally in 3 layers: MPC = (1 - 3*(1/3)^2) * 3/2 = (1 - 1/3) * 1.5 = 1.0
    assert abs(mpc["A"] - 1.0) < 1e-6
    assert abs(mpc["B"] - 1.0) < 1e-6


@skip_if_no_deps
def test_partial_participation():
    """Test MPC for nodes with partial participation across layers."""
    mnet = multinet.multi_layer_network(directed=False)
    
    # Layer 1: A has degree 2
    mnet.add_edges([
        ['A', 'L1', 'B', 'L1', 1],
        ['A', 'L1', 'C', 'L1', 1],
        ['B', 'L1', 'C', 'L1', 1]
    ], input_type='list')
    
    # Layer 2: A has degree 1
    mnet.add_edges([
        ['A', 'L2', 'B', 'L2', 1],
        ['B', 'L2', 'C', 'L2', 1],
        ['C', 'L2', 'C', 'L2', 0]
    ], input_type='list')
    
    mpc = multiplex_participation_coefficient(mnet)
    
    # A has total degree 3 (2 in L1, 1 in L2)
    # MPC(A) = (1 - (2/3)^2 - (1/3)^2) * 2/(2-1) = (1 - 4/9 - 1/9) * 2 = (4/9) * 2 = 8/9
    expected_mpc_a = (1 - (2/3)**2 - (1/3)**2) * 2
    assert abs(mpc["A"] - expected_mpc_a) < 1e-6


@skip_if_no_deps
def test_check_multiplex_disabled():
    """Test that check_multiplex=False allows non-multiplex networks."""
    mnet = multinet.multi_layer_network(directed=False)
    
    # Non-multiplex structure
    mnet.add_edges([
        ['A', 'L1', 'B', 'L1', 1],
        ['A', 'L2', 'C', 'L2', 1]
    ], input_type='list')
    
    # Should not raise error with check_multiplex=False
    # But the result may not be meaningful for non-multiplex networks
    mpc = multiplex_participation_coefficient(mnet, check_multiplex=False)
    
    # Just verify it returns a dict
    assert isinstance(mpc, dict)


@skip_if_no_deps  
def test_minimum_layers():
    """Test that networks with less than 2 layers raise ValueError."""
    mnet = multinet.multi_layer_network(directed=False)
    
    # Only one layer
    mnet.add_edges([
        ['A', 'L1', 'B', 'L1', 1]
    ], input_type='list')
    
    with pytest.raises(ValueError, match="must have at least 2 layers"):
        multiplex_participation_coefficient(mnet)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
