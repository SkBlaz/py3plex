"""
Tests for multiplex participation coefficient (MPC) computation.

This module tests the MPC metric for multiplex networks.
"""
import pytest

from py3plex.algorithms.multicentrality import multiplex_participation_coefficient
from py3plex.core import multinet


def test_mpc_simple_multiplex():
    """Test MPC on a simple multiplex network."""
    # Create a simple multiplex network with 2 layers
    net = multinet.multi_layer_network()
    
    # Add nodes to both layers
    net.add_nodes([
        {'source': 'A', 'type': 'layer1'},
        {'source': 'B', 'type': 'layer1'},
        {'source': 'C', 'type': 'layer1'},
        {'source': 'A', 'type': 'layer2'},
        {'source': 'B', 'type': 'layer2'},
        {'source': 'C', 'type': 'layer2'},
    ])
    
    # Add edges - A is equally active in both layers
    net.add_edges([
        {'source': 'A', 'target': 'B', 'source_type': 'layer1', 'target_type': 'layer1'},
        {'source': 'A', 'target': 'C', 'source_type': 'layer2', 'target_type': 'layer2'},
    ])
    
    mpc = multiplex_participation_coefficient(net, normalized=True)
    
    # Check result is a dictionary
    assert isinstance(mpc, dict)
    # Check all values are numeric
    assert all(isinstance(v, (int, float)) for v in mpc.values())
    # MPC should be in [0, 1] when normalized
    assert all(0 <= v <= 1 for v in mpc.values())


def test_mpc_uniform_participation():
    """Test MPC when node has equal degree in all layers."""
    net = multinet.multi_layer_network()
    
    # Add nodes to 3 layers
    for layer in ['layer1', 'layer2', 'layer3']:
        net.add_nodes([
            {'source': 'A', 'type': layer},
            {'source': 'B', 'type': layer},
        ])
    
    # Add equal number of connections in each layer
    for layer in ['layer1', 'layer2', 'layer3']:
        net.add_edges([
            {'source': 'A', 'target': 'B', 'source_type': layer, 'target_type': layer},
        ])
    
    mpc = multiplex_participation_coefficient(net, normalized=True)
    
    # Node A should have maximum MPC (uniform participation)
    assert mpc['A'] > 0.9  # Should be close to 1.0


def test_mpc_concentrated_participation():
    """Test MPC when node is active in only one layer."""
    net = multinet.multi_layer_network()
    
    # Add nodes to 2 layers
    for layer in ['layer1', 'layer2']:
        net.add_nodes([
            {'source': 'A', 'type': layer},
            {'source': 'B', 'type': layer},
        ])
    
    # Add edges only in layer1
    net.add_edges([
        {'source': 'A', 'target': 'B', 'source_type': 'layer1', 'target_type': 'layer1'},
    ])
    
    mpc = multiplex_participation_coefficient(net, normalized=True)
    
    # Node A should have low MPC (concentrated in one layer)
    assert mpc['A'] < 0.1  # Should be close to 0


def test_mpc_isolated_node():
    """Test MPC for isolated nodes."""
    net = multinet.multi_layer_network()
    
    # Add nodes to 2 layers
    for layer in ['layer1', 'layer2']:
        net.add_nodes([
            {'source': 'A', 'type': layer},
            {'source': 'B', 'type': layer},
        ])
    
    # Add no edges - A and B are isolated
    
    mpc = multiplex_participation_coefficient(net, normalized=True)
    
    # Isolated nodes should have MPC = 0
    assert mpc['A'] == 0.0
    assert mpc['B'] == 0.0


def test_mpc_normalized_vs_unnormalized():
    """Test difference between normalized and unnormalized MPC."""
    net = multinet.multi_layer_network()
    
    # Add nodes to 2 layers
    for layer in ['layer1', 'layer2']:
        net.add_nodes([
            {'source': 'A', 'type': layer},
            {'source': 'B', 'type': layer},
        ])
    
    # Add edges
    net.add_edges([
        {'source': 'A', 'target': 'B', 'source_type': 'layer1', 'target_type': 'layer1'},
        {'source': 'A', 'target': 'B', 'source_type': 'layer2', 'target_type': 'layer2'},
    ])
    
    mpc_norm = multiplex_participation_coefficient(net, normalized=True)
    mpc_unnorm = multiplex_participation_coefficient(net, normalized=False)
    
    # Values should differ
    assert mpc_norm['A'] != mpc_unnorm['A']
    # Normalized should generally be larger
    assert mpc_norm['A'] >= mpc_unnorm['A']


def test_mpc_single_layer_error():
    """Test that MPC raises error for network with only 1 layer."""
    net = multinet.multi_layer_network()
    
    # Add nodes to only 1 layer
    net.add_nodes([
        {'source': 'A', 'type': 'layer1'},
        {'source': 'B', 'type': 'layer1'},
    ])
    
    # Should raise ValueError for < 2 layers
    with pytest.raises(ValueError, match="must have at least 2 layers"):
        multiplex_participation_coefficient(net)


def test_mpc_different_node_sets_error():
    """Test that MPC raises error when layers have different nodes (with check)."""
    net = multinet.multi_layer_network()
    
    # Add different nodes to different layers
    net.add_nodes([
        {'source': 'A', 'type': 'layer1'},
        {'source': 'B', 'type': 'layer1'},
        {'source': 'C', 'type': 'layer2'},  # Different node set
        {'source': 'D', 'type': 'layer2'},
    ])
    
    # Should raise ValueError when check_multiplex=True
    with pytest.raises(ValueError, match="Non-multiplex structure"):
        multiplex_participation_coefficient(net, check_multiplex=True)


def test_mpc_different_node_sets_no_check():
    """Test that MPC works with different node sets when check is disabled."""
    net = multinet.multi_layer_network()
    
    # Add different nodes to different layers
    net.add_nodes([
        {'source': 'A', 'type': 'layer1'},
        {'source': 'B', 'type': 'layer1'},
        {'source': 'C', 'type': 'layer2'},
        {'source': 'D', 'type': 'layer2'},
    ])
    
    # Should work when check_multiplex=False
    mpc = multiplex_participation_coefficient(net, check_multiplex=False)
    
    assert isinstance(mpc, dict)


def test_mpc_three_layers():
    """Test MPC with three layers."""
    net = multinet.multi_layer_network()
    
    # Add nodes to 3 layers
    for layer in ['layer1', 'layer2', 'layer3']:
        net.add_nodes([
            {'source': 'A', 'type': layer},
            {'source': 'B', 'type': layer},
            {'source': 'C', 'type': layer},
        ])
    
    # Add edges with varying participation
    net.add_edges([
        # A active in all layers equally
        {'source': 'A', 'target': 'B', 'source_type': 'layer1', 'target_type': 'layer1'},
        {'source': 'A', 'target': 'C', 'source_type': 'layer2', 'target_type': 'layer2'},
        {'source': 'A', 'target': 'B', 'source_type': 'layer3', 'target_type': 'layer3'},
        # B only in layer1
        {'source': 'B', 'target': 'C', 'source_type': 'layer1', 'target_type': 'layer1'},
    ])
    
    mpc = multiplex_participation_coefficient(net, normalized=True)
    
    # A should have higher MPC than B
    assert mpc['A'] > mpc['B']


def test_mpc_returns_all_nodes():
    """Test that MPC returns values for all nodes."""
    net = multinet.multi_layer_network()
    
    # Add nodes to 2 layers
    nodes = ['A', 'B', 'C', 'D']
    for layer in ['layer1', 'layer2']:
        for node in nodes:
            net.add_nodes([{'source': node, 'type': layer}])
    
    # Add some edges
    net.add_edges([
        {'source': 'A', 'target': 'B', 'source_type': 'layer1', 'target_type': 'layer1'},
        {'source': 'C', 'target': 'D', 'source_type': 'layer2', 'target_type': 'layer2'},
    ])
    
    mpc = multiplex_participation_coefficient(net)
    
    # Should have MPC for all nodes
    assert set(mpc.keys()) == set(nodes)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
