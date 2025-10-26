"""
Extended tests for core/random_generators module.

These tests focus on increasing coverage for random network generation functions.
"""
import unittest

import networkx as nx

from py3plex.core.random_generators import (
    random_multilayer_ER,
    random_multiplex_ER,
    random_multiplex_generator,
)


class TestRandomMultilayerER(unittest.TestCase):
    """Test random multilayer Erdős-Rényi network generation."""

    def test_basic_generation_undirected(self):
        """Test basic undirected multilayer network generation."""
        network = random_multilayer_ER(n=10, l=3, p=0.3, directed=False)
        
        self.assertIsNotNone(network)
        # Check that the network has nodes
        self.assertGreater(len(list(network.get_nodes())), 0)

    def test_basic_generation_directed(self):
        """Test basic directed multilayer network generation."""
        network = random_multilayer_ER(n=10, l=3, p=0.3, directed=True)
        
        self.assertIsNotNone(network)
        # Check that the network has nodes
        self.assertGreater(len(list(network.get_nodes())), 0)

    def test_small_network(self):
        """Test generation with minimal parameters."""
        network = random_multilayer_ER(n=5, l=2, p=0.5)
        
        self.assertIsNotNone(network)

    def test_sparse_network(self):
        """Test generation with low edge probability."""
        network = random_multilayer_ER(n=10, l=2, p=0.1)
        
        self.assertIsNotNone(network)

    def test_dense_network(self):
        """Test generation with high edge probability."""
        network = random_multilayer_ER(n=10, l=2, p=0.9)
        
        self.assertIsNotNone(network)

    def test_zero_probability(self):
        """Test generation with zero edge probability (no edges)."""
        network = random_multilayer_ER(n=10, l=2, p=0.0)
        
        self.assertIsNotNone(network)

    def test_full_probability(self):
        """Test generation with full edge probability."""
        network = random_multilayer_ER(n=10, l=2, p=1.0)
        
        self.assertIsNotNone(network)


class TestRandomMultiplexER(unittest.TestCase):
    """Test random multiplex Erdős-Rényi network generation."""

    def test_basic_generation_undirected(self):
        """Test basic undirected multiplex network generation."""
        network = random_multiplex_ER(n=10, l=3, p=0.3, directed=False)
        
        self.assertIsNotNone(network)
        # Check that the network has nodes
        self.assertGreater(len(list(network.get_nodes())), 0)

    def test_basic_generation_directed(self):
        """Test basic directed multiplex network generation."""
        network = random_multiplex_ER(n=10, l=3, p=0.3, directed=True)
        
        self.assertIsNotNone(network)
        # Check that the network has nodes
        self.assertGreater(len(list(network.get_nodes())), 0)

    def test_single_layer(self):
        """Test generation with a single layer."""
        network = random_multiplex_ER(n=10, l=1, p=0.5)
        
        self.assertIsNotNone(network)

    def test_many_layers(self):
        """Test generation with many layers."""
        network = random_multiplex_ER(n=5, l=10, p=0.3)
        
        self.assertIsNotNone(network)

    def test_sparse_network(self):
        """Test generation with low edge probability."""
        network = random_multiplex_ER(n=10, l=2, p=0.1)
        
        self.assertIsNotNone(network)

    def test_dense_network(self):
        """Test generation with high edge probability."""
        network = random_multiplex_ER(n=10, l=2, p=0.9)
        
        self.assertIsNotNone(network)

    def test_zero_probability(self):
        """Test generation with zero edge probability (no edges)."""
        network = random_multiplex_ER(n=10, l=2, p=0.0)
        
        self.assertIsNotNone(network)

    def test_full_probability(self):
        """Test generation with full edge probability."""
        network = random_multiplex_ER(n=10, l=2, p=1.0)
        
        self.assertIsNotNone(network)


class TestRandomMultiplexGenerator(unittest.TestCase):
    """Test random multiplex network generator from bipartite graph."""

    def test_basic_generation(self):
        """Test basic multiplex network generation."""
        G = random_multiplex_generator(n=10, m=3, d=0.9)
        
        self.assertIsNotNone(G)
        self.assertIsInstance(G, nx.MultiGraph)

    def test_minimal_network(self):
        """Test generation with minimal parameters."""
        G = random_multiplex_generator(n=5, m=2, d=0.5)
        
        self.assertIsNotNone(G)
        self.assertIsInstance(G, nx.MultiGraph)

    def test_single_layer(self):
        """Test generation with a single layer."""
        G = random_multiplex_generator(n=10, m=1, d=0.5)
        
        self.assertIsNotNone(G)
        self.assertIsInstance(G, nx.MultiGraph)

    def test_many_layers(self):
        """Test generation with many layers."""
        G = random_multiplex_generator(n=5, m=10, d=0.5)
        
        self.assertIsNotNone(G)
        self.assertIsInstance(G, nx.MultiGraph)

    def test_high_dropout(self):
        """Test generation with high dropout (sparse within layers)."""
        G = random_multiplex_generator(n=10, m=3, d=0.2)
        
        self.assertIsNotNone(G)
        self.assertIsInstance(G, nx.MultiGraph)

    def test_low_dropout(self):
        """Test generation with low dropout (dense within layers)."""
        G = random_multiplex_generator(n=10, m=3, d=0.95)
        
        self.assertIsNotNone(G)
        self.assertIsInstance(G, nx.MultiGraph)

    def test_zero_dropout(self):
        """Test generation with zero dropout (no edges)."""
        G = random_multiplex_generator(n=10, m=3, d=0.0)
        
        self.assertIsNotNone(G)
        self.assertIsInstance(G, nx.MultiGraph)

    def test_full_dropout(self):
        """Test generation with full dropout (all edges within layers)."""
        G = random_multiplex_generator(n=10, m=3, d=1.0)
        
        self.assertIsNotNone(G)
        self.assertIsInstance(G, nx.MultiGraph)

    def test_small_nodes_many_layers(self):
        """Test edge case: few nodes but many layers."""
        G = random_multiplex_generator(n=3, m=5, d=0.5)
        
        self.assertIsNotNone(G)
        self.assertIsInstance(G, nx.MultiGraph)


if __name__ == "__main__":
    unittest.main()
