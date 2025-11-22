"""
Tests for community detection quality measures and utilities.

This module tests community quality metrics like modularity, size distribution,
and community counting.
"""
import networkx as nx
import pytest

from py3plex.algorithms.community_detection.community_measures import (
    modularity,
    number_of_communities,
    size_distribution,
)


def test_modularity_simple_graph():
    """Test modularity calculation on a simple graph with known communities."""
    # Create a simple graph with two clear communities
    G = nx.Graph()
    G.add_edges_from([(0, 1), (1, 2), (0, 2)])  # Community 1
    G.add_edges_from([(3, 4), (4, 5), (3, 5)])  # Community 2
    G.add_edge(2, 3)  # Bridge between communities
    
    # Perfect partition
    perfect_partition = {
        0: [0, 1, 2],
        1: [3, 4, 5]
    }
    
    mod = modularity(G, perfect_partition)
    
    # Modularity should be positive for good partition
    assert mod > 0
    assert mod <= 1.0


def test_modularity_weighted_graph():
    """Test modularity with weighted edges."""
    G = nx.Graph()
    G.add_edge(0, 1, weight=2.0)
    G.add_edge(1, 2, weight=2.0)
    G.add_edge(2, 3, weight=0.1)  # Weak connection
    G.add_edge(3, 4, weight=2.0)
    
    partition = {
        0: [0, 1, 2],
        1: [3, 4]
    }
    
    mod = modularity(G, partition, weight="weight")
    
    assert isinstance(mod, float)
    assert mod > 0


def test_modularity_single_community():
    """Test modularity when all nodes are in single community."""
    G = nx.karate_club_graph()
    
    # Put all nodes in one community
    all_nodes = list(G.nodes())
    single_partition = {0: all_nodes}
    
    mod = modularity(G, single_partition)
    
    # Single community should have modularity close to 0
    assert abs(mod) < 0.01


def test_modularity_all_separate_communities():
    """Test modularity when each node is its own community."""
    G = nx.path_graph(5)
    
    # Each node in its own community
    separate_partition = {i: [i] for i in range(5)}
    
    mod = modularity(G, separate_partition)
    
    # This should have low or negative modularity
    assert mod < 0.5


def test_modularity_directed_graph():
    """Test modularity on directed graph."""
    G = nx.DiGraph()
    G.add_edges_from([(0, 1), (1, 2), (2, 0)])  # Cycle
    G.add_edges_from([(3, 4), (4, 5), (5, 3)])  # Another cycle
    
    partition = {
        0: [0, 1, 2],
        1: [3, 4, 5]
    }
    
    mod = modularity(G, partition)
    
    assert isinstance(mod, float)
    assert -1.0 <= mod <= 1.0


def test_modularity_multigraph():
    """Test modularity on multigraph with parallel edges."""
    G = nx.MultiGraph()
    G.add_edge(0, 1)
    G.add_edge(0, 1)  # Parallel edge
    G.add_edge(1, 2)
    G.add_edge(2, 3)
    
    partition = {
        0: [0, 1],
        1: [2, 3]
    }
    
    mod = modularity(G, partition)
    
    assert isinstance(mod, float)


def test_size_distribution_simple():
    """Test size distribution calculation."""
    partition = {
        0: [1, 2, 3],
        1: [4, 5],
        2: [6, 7, 8, 9]
    }
    
    sizes = size_distribution(partition)
    
    assert list(sorted(sizes)) == [2, 3, 4]
    assert len(sizes) == 3


def test_size_distribution_empty():
    """Test size distribution with empty partition."""
    partition = {}
    
    sizes = size_distribution(partition)
    
    assert len(sizes) == 0


def test_size_distribution_single_community():
    """Test size distribution with single community."""
    partition = {0: [1, 2, 3, 4, 5]}
    
    sizes = size_distribution(partition)
    
    assert len(sizes) == 1
    assert sizes[0] == 5


def test_number_of_communities_simple():
    """Test counting communities."""
    partition = {
        0: [1, 2, 3],
        1: [4, 5],
        2: [6, 7, 8, 9]
    }
    
    count = number_of_communities(partition)
    
    assert count == 3


def test_number_of_communities_empty():
    """Test counting communities with empty partition."""
    partition = {}
    
    count = number_of_communities(partition)
    
    assert count == 0


def test_number_of_communities_single():
    """Test counting communities with single community."""
    partition = {0: [1, 2, 3, 4, 5]}
    
    count = number_of_communities(partition)
    
    assert count == 1


def test_modularity_karate_club():
    """Test modularity on karate club graph with known structure."""
    G = nx.karate_club_graph()
    
    # Simple partition based on club attribute
    partition = {}
    partition[0] = [n for n in G.nodes() if G.nodes[n]['club'] == 'Mr. Hi']
    partition[1] = [n for n in G.nodes() if G.nodes[n]['club'] == 'Officer']
    
    mod = modularity(G, partition)
    
    # The real karate club split should have positive modularity
    assert mod > 0.3


def test_size_distribution_types():
    """Test that size_distribution returns numpy array."""
    import numpy as np
    
    partition = {
        0: [1, 2],
        1: [3, 4, 5]
    }
    
    sizes = size_distribution(partition)
    
    assert isinstance(sizes, np.ndarray)


def test_modularity_self_loops():
    """Test modularity with self-loops."""
    G = nx.Graph()
    G.add_edges_from([(0, 1), (1, 2)])
    G.add_edge(0, 0)  # Self-loop
    
    partition = {0: [0, 1, 2]}
    
    mod = modularity(G, partition)
    
    # Should handle self-loops without error
    assert isinstance(mod, float)


def test_modularity_returns_float():
    """Test that modularity always returns a float."""
    G = nx.complete_graph(5)
    partition = {0: [0, 1, 2], 1: [3, 4]}
    
    mod = modularity(G, partition)
    
    assert isinstance(mod, float)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
