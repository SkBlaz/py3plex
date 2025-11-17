"""
Comprehensive tests for community detection measures.
"""

import pytest
import networkx as nx
import numpy as np

from py3plex.algorithms.community_detection.community_measures import (
    modularity,
    size_distribution,
    number_of_communities,
)


class TestModularity:
    """Tests for the modularity function."""

    def test_perfect_partition(self):
        """Test modularity for a perfect partition (two cliques)."""
        G = nx.Graph()
        # Create two separate cliques
        G.add_edges_from([(0, 1), (0, 2), (1, 2)])  # Clique 1
        G.add_edges_from([(3, 4), (3, 5), (4, 5)])  # Clique 2
        
        communities = {
            0: [0, 1, 2],
            1: [3, 4, 5]
        }
        
        Q = modularity(G, communities)
        assert isinstance(Q, float)
        assert Q > 0  # Should be positive for good partition

    def test_single_community(self):
        """Test modularity when all nodes are in one community."""
        G = nx.karate_club_graph()
        communities = {0: list(G.nodes())}
        
        Q = modularity(G, communities)
        assert isinstance(Q, float)
        assert abs(Q) < 0.01  # Should be close to 0

    def test_bad_partition(self):
        """Test modularity for a bad partition."""
        G = nx.karate_club_graph()
        # Put each node in its own community
        communities = {i: [i] for i in G.nodes()}
        
        Q = modularity(G, communities)
        assert isinstance(Q, float)
        assert Q < 0.5  # Should be low for poor partition

    def test_weighted_graph(self):
        """Test modularity with weighted edges."""
        G = nx.Graph()
        G.add_edge(0, 1, weight=2.0)
        G.add_edge(1, 2, weight=1.0)
        G.add_edge(2, 3, weight=2.0)
        
        communities = {
            0: [0, 1],
            1: [2, 3]
        }
        
        Q = modularity(G, communities, weight="weight")
        assert isinstance(Q, float)

    def test_directed_graph(self):
        """Test modularity with directed graph."""
        G = nx.DiGraph()
        G.add_edges_from([(0, 1), (1, 2), (2, 0)])  # Directed cycle
        G.add_edges_from([(3, 4), (4, 5), (5, 3)])  # Another cycle
        
        communities = {
            0: [0, 1, 2],
            1: [3, 4, 5]
        }
        
        Q = modularity(G, communities)
        assert isinstance(Q, float)

    def test_multigraph(self):
        """Test modularity with multigraph."""
        G = nx.MultiGraph()
        G.add_edge(0, 1)
        G.add_edge(0, 1)  # Duplicate edge
        G.add_edge(1, 2)
        G.add_edge(2, 3)
        G.add_edge(3, 4)
        
        communities = {
            0: [0, 1],
            1: [2, 3, 4]
        }
        
        Q = modularity(G, communities)
        assert isinstance(Q, float)

    def test_self_loops(self):
        """Test modularity with self-loops."""
        G = nx.Graph()
        G.add_edge(0, 0)  # Self-loop
        G.add_edge(0, 1)
        G.add_edge(1, 1)  # Self-loop
        
        communities = {0: [0, 1]}
        
        Q = modularity(G, communities)
        assert isinstance(Q, float)

    def test_disconnected_components(self):
        """Test modularity with disconnected components."""
        G = nx.Graph()
        G.add_edges_from([(0, 1), (1, 2)])  # Component 1
        G.add_edges_from([(3, 4), (4, 5)])  # Component 2
        
        communities = {
            0: [0, 1, 2],
            1: [3, 4, 5]
        }
        
        Q = modularity(G, communities)
        assert isinstance(Q, float)
        assert Q > 0  # Should be high for natural partition

    def test_empty_community(self):
        """Test with partition containing empty list."""
        G = nx.karate_club_graph()
        communities = {
            0: list(G.nodes())[:10],
            1: list(G.nodes())[10:20],
            2: []  # Empty community
        }
        
        Q = modularity(G, communities)
        assert isinstance(Q, float)


class TestSizeDistribution:
    """Tests for the size_distribution function."""

    def test_equal_sized_communities(self):
        """Test with equal-sized communities."""
        partition = {
            0: [0, 1, 2],
            1: [3, 4, 5],
            2: [6, 7, 8]
        }
        
        sizes = size_distribution(partition)
        assert isinstance(sizes, np.ndarray)
        assert len(sizes) == 3
        assert all(sizes == 3)

    def test_variable_sized_communities(self):
        """Test with variable-sized communities."""
        partition = {
            0: [0],
            1: [1, 2],
            2: [3, 4, 5, 6]
        }
        
        sizes = size_distribution(partition)
        assert isinstance(sizes, np.ndarray)
        assert len(sizes) == 3
        assert set(sizes) == {1, 2, 4}

    def test_single_community(self):
        """Test with a single community."""
        partition = {0: list(range(10))}
        
        sizes = size_distribution(partition)
        assert isinstance(sizes, np.ndarray)
        assert len(sizes) == 1
        assert sizes[0] == 10

    def test_singleton_communities(self):
        """Test with all singleton communities."""
        partition = {i: [i] for i in range(5)}
        
        sizes = size_distribution(partition)
        assert isinstance(sizes, np.ndarray)
        assert len(sizes) == 5
        assert all(sizes == 1)

    def test_empty_partition(self):
        """Test with empty partition."""
        partition = {}
        
        sizes = size_distribution(partition)
        assert isinstance(sizes, np.ndarray)
        assert len(sizes) == 0


class TestNumberOfCommunities:
    """Tests for the number_of_communities function."""

    def test_multiple_communities(self):
        """Test counting multiple communities."""
        partition = {
            0: [0, 1],
            1: [2, 3],
            2: [4, 5]
        }
        
        n = number_of_communities(partition)
        assert n == 3

    def test_single_community(self):
        """Test with single community."""
        partition = {0: list(range(10))}
        
        n = number_of_communities(partition)
        assert n == 1

    def test_many_communities(self):
        """Test with many communities."""
        partition = {i: [i] for i in range(100)}
        
        n = number_of_communities(partition)
        assert n == 100

    def test_empty_partition(self):
        """Test with empty partition."""
        partition = {}
        
        n = number_of_communities(partition)
        assert n == 0

    def test_with_empty_communities(self):
        """Test counting includes empty communities."""
        partition = {
            0: [0, 1],
            1: [],
            2: [2, 3]
        }
        
        n = number_of_communities(partition)
        assert n == 3


class TestCommunityMeasuresIntegration:
    """Integration tests combining multiple measures."""

    def test_karate_club_real_partition(self):
        """Test measures on karate club with real communities."""
        G = nx.karate_club_graph()
        
        # Split based on the known faction split
        communities = {
            0: [n for n in G.nodes() if G.nodes[n]['club'] == 'Mr. Hi'],
            1: [n for n in G.nodes() if G.nodes[n]['club'] == 'Officer']
        }
        
        Q = modularity(G, communities)
        sizes = size_distribution(communities)
        n_comm = number_of_communities(communities)
        
        assert Q > 0.3  # Known to have reasonable modularity
        assert n_comm == 2
        assert len(sizes) == 2
        assert sum(sizes) == G.number_of_nodes()

    def test_stochastic_block_model(self):
        """Test on a stochastic block model with known structure."""
        sizes = [20, 20, 20]
        p_matrix = [[0.25, 0.01, 0.01],
                    [0.01, 0.25, 0.01],
                    [0.01, 0.01, 0.25]]
        G = nx.stochastic_block_model(sizes, p_matrix, seed=42)
        
        # Perfect partition
        communities = {
            0: list(range(0, 20)),
            1: list(range(20, 40)),
            2: list(range(40, 60))
        }
        
        Q = modularity(G, communities)
        assert Q > 0.4  # Should have high modularity
        assert number_of_communities(communities) == 3
        
        comm_sizes = size_distribution(communities)
        assert all(comm_sizes == 20)

    def test_measure_consistency(self):
        """Test that measures are consistent with each other."""
        partition = {
            0: [0, 1, 2],
            1: [3, 4],
            2: [5, 6, 7, 8]
        }
        
        sizes = size_distribution(partition)
        n_comm = number_of_communities(partition)
        
        assert len(sizes) == n_comm
        assert sum(sizes) == sum(len(nodes) for nodes in partition.values())
