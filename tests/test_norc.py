"""
Tests for NoRC (Node Ranking and Clustering) community detection.

This module tests the NoRC algorithm for community detection in networks.
"""
import networkx as nx
import pytest

from py3plex.algorithms.community_detection.NoRC import NoRC_communities_main


def test_norc_kmeans_small_graph():
    """Test NoRC with k-means clustering on a small graph."""
    # Create a simple graph with two clear communities
    G = nx.Graph()
    G.add_edges_from([(0, 1), (1, 2), (0, 2)])  # Community 1
    G.add_edges_from([(3, 4), (4, 5), (3, 5)])  # Community 2
    G.add_edge(2, 3)  # Bridge between communities
    
    communities = NoRC_communities_main(
        G,
        clustering_scheme="kmeans",
        verbose=False,
        community_range=[2, 3],
        parallel_step=2,
    )
    
    assert communities is not None
    assert isinstance(communities, dict)
    assert len(communities) > 0


def test_norc_hierarchical_small_graph():
    """Test NoRC with hierarchical clustering on a small graph."""
    # Create a simple graph with two clear communities
    G = nx.Graph()
    G.add_edges_from([(0, 1), (1, 2), (0, 2)])  # Community 1
    G.add_edges_from([(3, 4), (4, 5), (3, 5)])  # Community 2
    G.add_edge(2, 3)  # Bridge between communities
    
    communities = NoRC_communities_main(
        G,
        clustering_scheme="hierarchical",
        verbose=False,
        community_range=[2, 3],
        parallel_step=2,
    )
    
    assert communities is not None
    assert isinstance(communities, dict)
    assert len(communities) > 0


def test_norc_returns_valid_partition():
    """Test that NoRC returns a valid partition structure."""
    G = nx.karate_club_graph()
    
    communities = NoRC_communities_main(
        G,
        clustering_scheme="kmeans",
        verbose=False,
        community_range=[2, 3, 4],
        parallel_step=2,
    )
    
    # Check that all nodes are assigned to some community
    all_nodes = set()
    for community in communities.values():
        all_nodes.update(community)
    
    assert len(all_nodes) == len(G.nodes())


def test_norc_auto_parallel_step():
    """Test NoRC with automatic parallel step detection."""
    G = nx.karate_club_graph()
    
    communities = NoRC_communities_main(
        G,
        clustering_scheme="kmeans",
        verbose=False,
        community_range=[2, 3],
        parallel_step=None,  # Should auto-detect
    )
    
    assert communities is not None
    assert isinstance(communities, dict)


def test_norc_weighted_graph():
    """Test NoRC on weighted graphs."""
    G = nx.Graph()
    G.add_edge(0, 1, weight=2.0)
    G.add_edge(1, 2, weight=2.0)
    G.add_edge(2, 3, weight=0.1)  # Weak connection
    G.add_edge(3, 4, weight=2.0)
    
    communities = NoRC_communities_main(
        G,
        clustering_scheme="hierarchical",
        verbose=False,
        community_range=[2],
        parallel_step=2,
    )
    
    assert communities is not None
    assert isinstance(communities, dict)


def test_norc_directed_graph():
    """Test NoRC on directed graphs."""
    G = nx.DiGraph()
    G.add_edges_from([(0, 1), (1, 2), (2, 0)])  # Cycle
    G.add_edges_from([(3, 4), (4, 5), (5, 3)])  # Another cycle
    G.add_edge(2, 3)
    
    communities = NoRC_communities_main(
        G,
        clustering_scheme="kmeans",
        verbose=False,
        community_range=[2],
        parallel_step=2,
    )
    
    assert communities is not None
    assert isinstance(communities, dict)


def test_norc_threshold_parameter():
    """Test NoRC with different probability thresholds."""
    G = nx.karate_club_graph()
    
    # Higher threshold should result in sparser representation
    communities_high = NoRC_communities_main(
        G,
        clustering_scheme="kmeans",
        verbose=False,
        community_range=[2],
        parallel_step=2,
        prob_threshold=0.001,
    )
    
    assert communities_high is not None
    assert isinstance(communities_high, dict)


def test_norc_lag_threshold():
    """Test NoRC early stopping with lag threshold."""
    G = nx.karate_club_graph()
    
    communities = NoRC_communities_main(
        G,
        clustering_scheme="kmeans",
        verbose=False,
        community_range=[2, 3, 4, 5, 6, 7, 8, 9, 10],
        parallel_step=2,
        lag_threshold=3,  # Stop after 3 iterations without improvement
    )
    
    assert communities is not None
    assert isinstance(communities, dict)


def test_norc_community_range():
    """Test NoRC with custom community range."""
    G = nx.karate_club_graph()
    
    communities = NoRC_communities_main(
        G,
        clustering_scheme="hierarchical",
        verbose=False,
        community_range=[2, 4, 6],
        parallel_step=2,
    )
    
    assert communities is not None
    assert isinstance(communities, dict)


@pytest.mark.slow
def test_norc_larger_graph():
    """Test NoRC on a larger graph (marked as slow)."""
    G = nx.powerlaw_cluster_graph(100, 3, 0.1)
    
    communities = NoRC_communities_main(
        G,
        clustering_scheme="kmeans",
        verbose=False,
        community_range=[3, 5, 7],
        parallel_step=2,
    )
    
    assert communities is not None
    assert isinstance(communities, dict)
    assert len(communities) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
