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
