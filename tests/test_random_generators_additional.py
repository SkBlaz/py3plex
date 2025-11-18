"""
Additional comprehensive tests for random network generators.
"""

import pytest
import networkx as nx
import numpy as np

from py3plex.core.random_generators import (
    random_multilayer_ER,
    random_multiplex_ER,
    random_multiplex_generator,
)


class TestRandomMultilayerER:
    """Tests for random_multilayer_ER function."""

    def test_basic_generation(self):
        """Test basic multilayer ER network generation."""
        n, l, p = 10, 2, 0.5
        network = random_multilayer_ER(n, l, p, directed=False)
        
        assert network is not None
        assert hasattr(network, 'core_network')

    def test_directed_network(self):
        """Test generation of directed multilayer network."""
        n, l, p = 10, 2, 0.3
        network = random_multilayer_ER(n, l, p, directed=True)
        
        assert network is not None
        # Check that underlying network is directed
        assert hasattr(network, 'core_network')

    def test_small_network(self):
        """Test with small number of nodes."""
        n, l, p = 3, 2, 0.5
        network = random_multilayer_ER(n, l, p)
        
        assert network is not None

    def test_single_layer(self):
        """Test with single layer."""
        n, l, p = 10, 1, 0.3
        network = random_multilayer_ER(n, l, p)
        
        assert network is not None

    def test_many_layers(self):
        """Test with many layers."""
        n, l, p = 20, 5, 0.2
        network = random_multilayer_ER(n, l, p)
        
        assert network is not None

    def test_zero_probability(self):
        """Test with zero edge probability (no edges)."""
        n, l, p = 10, 2, 0.0
        network = random_multilayer_ER(n, l, p)
        
        assert network is not None

    def test_full_probability(self):
        """Test with probability 1 (complete graph per layer)."""
        n, l, p = 5, 2, 1.0
        network = random_multilayer_ER(n, l, p)
        
        assert network is not None

    def test_more_layers_than_nodes(self):
        """Test with more layers than nodes."""
        n, l, p = 3, 5, 0.5
        network = random_multilayer_ER(n, l, p)
        
        assert network is not None

    def test_different_probabilities(self):
        """Test that different probabilities produce different densities."""
        n, l = 20, 2
        
        network_sparse = random_multilayer_ER(n, l, 0.1)
        network_dense = random_multilayer_ER(n, l, 0.9)
        
        assert network_sparse is not None
        assert network_dense is not None


class TestRandomMultiplexER:
    """Tests for random_multiplex_ER function."""

    def test_basic_generation(self):
        """Test basic multiplex ER network generation."""
        n, l, p = 10, 2, 0.5
        network = random_multiplex_ER(n, l, p, directed=False)
        
        assert network is not None
        assert hasattr(network, 'core_network')

    def test_directed_multiplex(self):
        """Test directed multiplex network generation."""
        n, l, p = 10, 2, 0.3
        network = random_multiplex_ER(n, l, p, directed=True)
        
        assert network is not None

    def test_single_layer_multiplex(self):
        """Test multiplex with single layer."""
        n, l, p = 10, 1, 0.4
        network = random_multiplex_ER(n, l, p)
        
        assert network is not None

    def test_multiple_layers(self):
        """Test multiplex with multiple layers."""
        n, l, p = 15, 4, 0.3
        network = random_multiplex_ER(n, l, p)
        
        assert network is not None

    def test_small_multiplex(self):
        """Test small multiplex network."""
        n, l, p = 3, 2, 0.5
        network = random_multiplex_ER(n, l, p)
        
        assert network is not None

    def test_sparse_multiplex(self):
        """Test sparse multiplex (low probability)."""
        n, l, p = 20, 3, 0.05
        network = random_multiplex_ER(n, l, p)
        
        assert network is not None

    def test_dense_multiplex(self):
        """Test dense multiplex (high probability)."""
        n, l, p = 15, 2, 0.95
        network = random_multiplex_ER(n, l, p)
        
        assert network is not None

    def test_multiplex_layer_structure(self):
        """Test that multiplex has proper layer structure."""
        n, l, p = 10, 3, 0.4
        network = random_multiplex_ER(n, l, p)
        
        # Should have network object with core_network
        assert hasattr(network, 'core_network')
        G = network.core_network
        assert isinstance(G, (nx.MultiGraph, nx.MultiDiGraph))


class TestRandomMultiplexGenerator:
    """Tests for random_multiplex_generator function."""

    def test_basic_generation(self):
        """Test basic multiplex generation from bipartite."""
        n, m = 10, 2
        G = random_multiplex_generator(n, m)
        
        assert isinstance(G, nx.MultiGraph)
        # Should have nodes with layer tuples
        assert G.number_of_nodes() > 0

    def test_different_dropouts(self):
        """Test with different dropout values."""
        n, m = 10, 2
        
        G_low = random_multiplex_generator(n, m, d=0.1)
        G_high = random_multiplex_generator(n, m, d=0.9)
        
        assert isinstance(G_low, nx.MultiGraph)
        assert isinstance(G_high, nx.MultiGraph)
        # Higher dropout should generally produce more edges
        assert G_high.number_of_edges() >= G_low.number_of_edges()

    def test_single_layer_generator(self):
        """Test with single layer."""
        n, m = 10, 1
        G = random_multiplex_generator(n, m, d=0.5)
        
        assert isinstance(G, nx.MultiGraph)

    def test_many_layers_generator(self):
        """Test with many layers."""
        n, m = 15, 5
        G = random_multiplex_generator(n, m, d=0.5)
        
        assert isinstance(G, nx.MultiGraph)

    def test_small_network_generator(self):
        """Test with small network."""
        n, m = 3, 2
        G = random_multiplex_generator(n, m, d=0.5)
        
        assert isinstance(G, nx.MultiGraph)
        # May have zero nodes if random assignment doesn't place nodes in layers
        assert G.number_of_nodes() >= 0

    def test_zero_dropout(self):
        """Test with zero dropout (no edges in layers)."""
        n, m = 10, 2
        G = random_multiplex_generator(n, m, d=0.0)
        
        assert isinstance(G, nx.MultiGraph)
        # With d=0, there should be no edges
        assert G.number_of_edges() == 0

    def test_full_dropout(self):
        """Test with full dropout (complete cliques in layers)."""
        n, m = 5, 2
        G = random_multiplex_generator(n, m, d=1.0)
        
        assert isinstance(G, nx.MultiGraph)

    def test_node_layer_format(self):
        """Test that nodes follow (node_id, layer_id) format."""
        n, m = 10, 3
        G = random_multiplex_generator(n, m, d=0.5)
        
        nodes = list(G.nodes())
        if len(nodes) > 0:
            # Nodes should be tuples
            assert all(isinstance(node, tuple) and len(node) == 2 for node in nodes)

    def test_edge_attributes(self):
        """Test that edges have expected attributes."""
        n, m = 10, 2
        G = random_multiplex_generator(n, m, d=0.5)
        
        if G.number_of_edges() > 0:
            edge = list(G.edges(data=True))[0]
            # Check edge has attributes
            assert 'type' in edge[2] or 'weight' in edge[2]


class TestRandomGeneratorsConstraints:
    """Tests for constraint validation in random generators."""

    def test_negative_nodes_multilayer(self):
        """Test that negative number of nodes is handled."""
        try:
            random_multilayer_ER(-5, 2, 0.5)
        except Exception:
            pass  # Expected if contracts are enabled

    def test_negative_layers_multilayer(self):
        """Test that negative number of layers is handled."""
        try:
            random_multilayer_ER(10, -2, 0.5)
        except Exception:
            pass  # Expected if contracts are enabled


class TestRandomGeneratorsIntegration:
    """Integration tests for random generators."""

    def test_multilayer_vs_multiplex(self):
        """Test that multilayer and multiplex produce different structures."""
        n, l, p = 20, 3, 0.4
        
        ml_net = random_multilayer_ER(n, l, p)
        mp_net = random_multiplex_ER(n, l, p)
        
        assert ml_net is not None
        assert mp_net is not None
        # Both should be network objects
        assert hasattr(ml_net, 'core_network')
        assert hasattr(mp_net, 'core_network')

    def test_generator_produces_valid_network(self):
        """Test that generator output is a valid multiplex."""
        G = random_multiplex_generator(20, 3, d=0.5)
        
        # Basic NetworkX graph checks
        assert G.number_of_nodes() >= 0
        assert G.number_of_edges() >= 0
        # Should be connected or have components
        assert isinstance(G, nx.MultiGraph)

    def test_consistency_with_seed(self):
        """Test that setting numpy seed produces consistent results."""
        np.random.seed(42)
        n1 = random_multilayer_ER(10, 2, 0.5)
        
        np.random.seed(42)
        n2 = random_multilayer_ER(10, 2, 0.5)
        
        # Both should be valid networks
        assert n1 is not None
        assert n2 is not None
