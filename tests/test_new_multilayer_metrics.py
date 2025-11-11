#!/usr/bin/env python3
"""
Tests for new multilayer network metrics.

This test suite validates the newly implemented metrics for multiplex networks.
"""

import pytest
import numpy as np
from py3plex.core import multinet
from py3plex.algorithms.statistics import multilayer_statistics


@pytest.fixture
def simple_multiplex():
    """Create a simple multiplex network for testing."""
    network = multinet.multi_layer_network(directed=False)
    
    # Layer 1: Triangle
    network.add_edges([
        ['A', 'L1', 'B', 'L1', 1],
        ['B', 'L1', 'C', 'L1', 1],
        ['C', 'L1', 'A', 'L1', 1]
    ], input_type='list')
    
    # Layer 2: Star
    network.add_edges([
        ['A', 'L2', 'B', 'L2', 1],
        ['A', 'L2', 'C', 'L2', 1],
        ['A', 'L2', 'D', 'L2', 1]
    ], input_type='list')
    
    return network


@pytest.fixture
def simple_communities():
    """Simple community structure for testing."""
    return {
        ('A', 'L1'): 0,
        ('B', 'L1'): 0,
        ('C', 'L1'): 1,
        ('A', 'L2'): 0,
        ('B', 'L2'): 0,
        ('C', 'L2'): 1,
        ('D', 'L2'): 1,
    }


class TestMultiplexBetweenness:
    """Tests for multiplex betweenness centrality."""
    
    def test_returns_dict(self, simple_multiplex):
        """Test that betweenness returns a dictionary."""
        result = multilayer_statistics.multiplex_betweenness_centrality(simple_multiplex)
        assert isinstance(result, dict)
    
    def test_non_negative_values(self, simple_multiplex):
        """Test that all betweenness values are non-negative."""
        result = multilayer_statistics.multiplex_betweenness_centrality(simple_multiplex)
        assert all(v >= 0 for v in result.values())
    
    def test_normalized_range(self, simple_multiplex):
        """Test that normalized betweenness values are in valid range."""
        result = multilayer_statistics.multiplex_betweenness_centrality(
            simple_multiplex, normalized=True
        )
        assert all(0 <= v <= 1 for v in result.values())


class TestMultiplexCloseness:
    """Tests for multiplex closeness centrality."""
    
    def test_returns_dict(self, simple_multiplex):
        """Test that closeness returns a dictionary."""
        result = multilayer_statistics.multiplex_closeness_centrality(simple_multiplex)
        assert isinstance(result, dict)
    
    def test_non_negative_values(self, simple_multiplex):
        """Test that all closeness values are non-negative."""
        result = multilayer_statistics.multiplex_closeness_centrality(simple_multiplex)
        assert all(v >= 0 for v in result.values())
    
    def test_normalized_range(self, simple_multiplex):
        """Test that normalized closeness values are in valid range."""
        result = multilayer_statistics.multiplex_closeness_centrality(
            simple_multiplex, normalized=True
        )
        assert all(0 <= v <= 1 for v in result.values())


class TestCommunityParticipation:
    """Tests for community participation metrics."""
    
    def test_participation_coefficient_range(self, simple_multiplex, simple_communities):
        """Test that participation coefficient is in [0, 1]."""
        result = multilayer_statistics.community_participation_coefficient(
            simple_multiplex, simple_communities, 'A'
        )
        assert 0 <= result <= 1
    
    def test_participation_entropy_non_negative(self, simple_multiplex, simple_communities):
        """Test that participation entropy is non-negative."""
        result = multilayer_statistics.community_participation_entropy(
            simple_multiplex, simple_communities, 'A'
        )
        assert result >= 0


class TestLayerRedundancy:
    """Tests for layer redundancy metrics."""
    
    def test_redundancy_coefficient_range(self, simple_multiplex):
        """Test that redundancy coefficient is in [0, 1]."""
        result = multilayer_statistics.layer_redundancy_coefficient(
            simple_multiplex, 'L1', 'L2'
        )
        assert 0 <= result <= 1
    
    def test_unique_redundant_edges_non_negative(self, simple_multiplex):
        """Test that edge counts are non-negative."""
        unique, redundant = multilayer_statistics.unique_redundant_edges(
            simple_multiplex, 'L1', 'L2'
        )
        assert unique >= 0
        assert redundant >= 0


class TestRichClub:
    """Tests for rich-club coefficient."""
    
    def test_returns_float(self, simple_multiplex):
        """Test that rich-club returns a float."""
        result = multilayer_statistics.multiplex_rich_club_coefficient(
            simple_multiplex, k=1
        )
        assert isinstance(result, float)
    
    def test_range_valid(self, simple_multiplex):
        """Test that rich-club coefficient is in valid range."""
        result = multilayer_statistics.multiplex_rich_club_coefficient(
            simple_multiplex, k=1
        )
        assert 0 <= result <= 1


class TestPercolation:
    """Tests for percolation analysis."""
    
    def test_percolation_threshold_range(self, simple_multiplex):
        """Test that percolation threshold is in [0, 1]."""
        result = multilayer_statistics.percolation_threshold(
            simple_multiplex, removal_strategy='random', trials=2
        )
        assert 0 <= result <= 1
    
    def test_targeted_layer_removal_resilience(self, simple_multiplex):
        """Test targeted layer removal with resilience score."""
        result = multilayer_statistics.targeted_layer_removal(
            simple_multiplex, 'L1', return_resilience=True
        )
        assert isinstance(result, float)
        assert 0 <= result <= 1


class TestModularity:
    """Tests for modularity computation."""
    
    def test_compute_modularity_returns_float(self, simple_multiplex, simple_communities):
        """Test that modularity computation returns a float."""
        result = multilayer_statistics.compute_modularity_score(
            simple_multiplex, simple_communities
        )
        assert isinstance(result, (float, np.floating))
    
    def test_modularity_range(self, simple_multiplex, simple_communities):
        """Test that modularity is in valid range [-1, 1]."""
        result = multilayer_statistics.compute_modularity_score(
            simple_multiplex, simple_communities
        )
        # Modularity can be negative (worse than random) or positive (better than random)
        assert -1 <= result <= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
