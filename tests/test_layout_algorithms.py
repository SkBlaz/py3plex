"""
Tests for layout algorithms with seed support.
"""

import pytest
import numpy as np

try:
    import networkx as nx
    from py3plex.visualization.layout_algorithms import (
        compute_random_layout,
        compute_force_directed_layout,
    )
    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False


@pytest.mark.skipif(not NETWORKX_AVAILABLE, reason="NetworkX not available")
class TestLayoutAlgorithms:
    
    def test_compute_random_layout_with_seed(self):
        """Test that compute_random_layout with seed is reproducible."""
        G = nx.karate_club_graph()
        
        # Generate layouts with same seed
        pos1 = compute_random_layout(G, seed=42)
        pos2 = compute_random_layout(G, seed=42)
        
        # Should have same number of nodes
        assert len(pos1) == len(pos2) == len(G.nodes())
        
        # Positions should be identical
        for node in G.nodes():
            np.testing.assert_array_almost_equal(
                pos1[node], pos2[node],
                err_msg=f"Position mismatch for node {node}"
            )
    
    def test_compute_random_layout_different_seeds(self):
        """Test that different seeds produce different layouts."""
        G = nx.karate_club_graph()
        
        pos1 = compute_random_layout(G, seed=1)
        pos2 = compute_random_layout(G, seed=2)
        
        # At least one node should have different position
        positions_differ = False
        for node in G.nodes():
            if not np.allclose(pos1[node], pos2[node]):
                positions_differ = True
                break
        
        assert positions_differ, "Different seeds should produce different layouts"
    
    def test_compute_random_layout_no_seed(self):
        """Test that compute_random_layout works without seed."""
        G = nx.karate_club_graph()
        
        pos = compute_random_layout(G)
        
        assert len(pos) == len(G.nodes())
        
        # Check all positions are in valid range [0, 1]
        for node, position in pos.items():
            assert len(position) == 2, "Position should be 2D"
            assert 0 <= position[0] <= 1, "X coordinate should be in [0, 1]"
            assert 0 <= position[1] <= 1, "Y coordinate should be in [0, 1]"
    
    def test_compute_force_directed_layout_with_seed(self):
        """Test that force_directed_layout with seed is reproducible."""
        # Use small graph for speed
        G = nx.path_graph(5)
        
        # When using fallback to spring_layout, should be reproducible
        pos1 = compute_force_directed_layout(
            G, seed=42, forceImport=False, verbose=False
        )
        pos2 = compute_force_directed_layout(
            G, seed=42, forceImport=False, verbose=False
        )
        
        # Should have same number of nodes
        assert len(pos1) == len(pos2) == len(G.nodes())
        
        # Positions should be similar (allowing for numerical precision)
        for node in G.nodes():
            np.testing.assert_array_almost_equal(
                pos1[node], pos2[node], decimal=5,
                err_msg=f"Position mismatch for node {node}"
            )
    
    def test_compute_force_directed_layout_returns_dict(self):
        """Test that force_directed_layout returns dictionary."""
        G = nx.path_graph(3)
        
        pos = compute_force_directed_layout(
            G, seed=123, forceImport=False, verbose=False
        )
        
        assert isinstance(pos, dict)
        assert len(pos) == len(G.nodes())
        
        # Check positions are arrays
        for node, position in pos.items():
            assert isinstance(position, np.ndarray)
            assert len(position) == 2


@pytest.mark.skipif(not NETWORKX_AVAILABLE, reason="NetworkX not available")
def test_layout_seed_parameter_exists():
    """Test that layout functions accept seed parameter."""
    import inspect
    
    # Check compute_random_layout
    sig = inspect.signature(compute_random_layout)
    assert 'seed' in sig.parameters, "compute_random_layout should have seed parameter"
    
    # Check compute_force_directed_layout
    sig = inspect.signature(compute_force_directed_layout)
    assert 'seed' in sig.parameters, "compute_force_directed_layout should have seed parameter"


@pytest.mark.skipif(not NETWORKX_AVAILABLE, reason="NetworkX not available")
class TestComputeRandomLayoutExtended:
    """Extended tests for compute_random_layout function."""

    def test_single_node_graph(self):
        """Test layout with single node graph."""
        G = nx.Graph()
        G.add_node(0)
        
        pos = compute_random_layout(G, seed=42)
        
        assert len(pos) == 1
        assert 0 in pos
        assert len(pos[0]) == 2

    def test_empty_positions_range(self):
        """Test that all positions are within [0, 1] range."""
        G = nx.complete_graph(10)
        
        pos = compute_random_layout(G, seed=123)
        
        for node, position in pos.items():
            assert 0 <= position[0] <= 1
            assert 0 <= position[1] <= 1

    def test_disconnected_graph(self):
        """Test layout with disconnected graph."""
        G = nx.Graph()
        G.add_edge(0, 1)
        G.add_edge(2, 3)
        # Disconnected components
        
        pos = compute_random_layout(G, seed=42)
        
        assert len(pos) == 4
        for node in [0, 1, 2, 3]:
            assert node in pos

    def test_reproducibility_multiple_calls(self):
        """Test reproducibility over multiple calls."""
        G = nx.cycle_graph(20)
        
        positions = [compute_random_layout(G, seed=777) for _ in range(5)]
        
        # All should be identical
        for i in range(1, 5):
            for node in G.nodes():
                np.testing.assert_array_equal(
                    positions[0][node], positions[i][node]
                )


@pytest.mark.skipif(not NETWORKX_AVAILABLE, reason="NetworkX not available")
class TestComputeForceDirectedLayoutExtended:
    """Extended tests for compute_force_directed_layout function."""

    def test_single_node_graph(self):
        """Test force-directed layout with single node."""
        G = nx.Graph()
        G.add_node(0)
        
        pos = compute_force_directed_layout(
            G, seed=42, forceImport=False, verbose=False
        )
        
        assert len(pos) == 1
        assert 0 in pos

    def test_with_layout_parameters(self):
        """Test force-directed layout with custom parameters."""
        G = nx.path_graph(4)
        
        # Provide custom initial positions
        init_pos = {i: np.array([float(i), 0.0]) for i in range(4)}
        
        pos = compute_force_directed_layout(
            G, 
            layout_parameters={'pos': init_pos, 'iterations': 10},
            seed=42,
            forceImport=False,
            verbose=False
        )
        
        assert len(pos) == 4
        assert isinstance(pos, dict)

    def test_gravity_parameter(self):
        """Test that gravity parameter is accepted."""
        G = nx.path_graph(3)
        
        pos = compute_force_directed_layout(
            G, gravity=0.5, seed=42, forceImport=False, verbose=False
        )
        
        assert len(pos) == 3

    def test_scaling_ratio_parameter(self):
        """Test that scalingRatio parameter is accepted."""
        G = nx.path_graph(3)
        
        pos = compute_force_directed_layout(
            G, scalingRatio=5.0, seed=42, forceImport=False, verbose=False
        )
        
        assert len(pos) == 3

    def test_edge_weight_influence(self):
        """Test that edgeWeightInfluence parameter is accepted."""
        G = nx.path_graph(3)
        
        pos = compute_force_directed_layout(
            G, edgeWeightInfluence=0.5, seed=42, forceImport=False, verbose=False
        )
        
        assert len(pos) == 3

    def test_disconnected_components(self):
        """Test force-directed layout with disconnected components."""
        G = nx.Graph()
        G.add_edges_from([(0, 1), (2, 3)])
        
        pos = compute_force_directed_layout(
            G, seed=42, forceImport=False, verbose=False
        )
        
        assert len(pos) == 4

    def test_weighted_graph(self):
        """Test force-directed layout with weighted edges."""
        G = nx.Graph()
        G.add_edge(0, 1, weight=0.5)
        G.add_edge(1, 2, weight=1.5)
        G.add_edge(2, 0, weight=1.0)
        
        pos = compute_force_directed_layout(
            G, seed=42, forceImport=False, verbose=False
        )
        
        assert len(pos) == 3

    def test_complete_graph(self):
        """Test force-directed layout with complete graph."""
        G = nx.complete_graph(5)
        
        pos = compute_force_directed_layout(
            G, seed=42, forceImport=False, verbose=False
        )
        
        assert len(pos) == 5
        # All positions should be different
        positions_list = list(pos.values())
        for i in range(len(positions_list)):
            for j in range(i + 1, len(positions_list)):
                # At least one coordinate should differ
                assert not np.allclose(positions_list[i], positions_list[j])


@pytest.mark.skipif(not NETWORKX_AVAILABLE, reason="NetworkX not available")
class TestLayoutParameterValidation:
    """Test parameter validation and edge cases."""

    def test_random_layout_all_nodes_have_positions(self):
        """Test that all nodes get positions."""
        G = nx.barabasi_albert_graph(20, 3, seed=42)
        
        pos = compute_random_layout(G, seed=123)
        
        for node in G.nodes():
            assert node in pos, f"Node {node} missing from layout"

    def test_force_directed_layout_all_nodes_have_positions(self):
        """Test that all nodes get positions in force-directed layout."""
        G = nx.watts_strogatz_graph(15, 4, 0.3, seed=42)
        
        pos = compute_force_directed_layout(
            G, seed=123, forceImport=False, verbose=False
        )
        
        for node in G.nodes():
            assert node in pos, f"Node {node} missing from layout"

    def test_random_layout_position_dimensions(self):
        """Test that positions are 2D arrays."""
        G = nx.star_graph(10)
        
        pos = compute_random_layout(G, seed=42)
        
        for node, position in pos.items():
            assert isinstance(position, np.ndarray)
            assert position.shape == (2,), f"Position for node {node} has wrong shape"

    def test_force_directed_layout_position_dimensions(self):
        """Test that force-directed positions are 2D arrays."""
        G = nx.ladder_graph(3)
        
        pos = compute_force_directed_layout(
            G, seed=42, forceImport=False, verbose=False
        )
        
        for node, position in pos.items():
            assert isinstance(position, np.ndarray)
            assert position.shape == (2,), f"Position for node {node} has wrong shape"
