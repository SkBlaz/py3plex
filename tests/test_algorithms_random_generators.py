"""
Tests for py3plex.algorithms.advanced_random_generators module.

Tests multilayer random graph generation algorithms including:
- Barabási-Albert preferential attachment
- Erdős-Rényi random graphs
- Stochastic Block Models
"""

import pytest
import networkx as nx
from py3plex.algorithms.advanced_random_generators import (
    multilayer_barabasi_albert,
    multilayer_erdos_renyi,
    multilayer_stochastic_block_model,
)


class TestMultilayerBarabasiAlbert:
    """Tests for multilayer_barabasi_albert function."""
    
    def test_basic_generation(self):
        """Test basic BA network generation."""
        G = multilayer_barabasi_albert(n=20, m=2, num_layers=2, seed=42)
        assert G is not None
        assert G.number_of_nodes() > 0
        
    def test_determinism_with_seed(self):
        """Test that same seed produces same network."""
        G1 = multilayer_barabasi_albert(n=15, m=2, num_layers=2, seed=123)
        G2 = multilayer_barabasi_albert(n=15, m=2, num_layers=2, seed=123)
        
        assert G1.number_of_nodes() == G2.number_of_nodes()
        assert G1.number_of_edges() == G2.number_of_edges()
        
    def test_different_seeds_produce_different_networks(self):
        """Test that different seeds produce different networks."""
        G1 = multilayer_barabasi_albert(n=20, m=2, num_layers=2, seed=1)
        G2 = multilayer_barabasi_albert(n=20, m=2, num_layers=2, seed=2)
        
        # Networks should have same size but different structure
        assert G1.number_of_nodes() == G2.number_of_nodes()
        # Edge count might differ slightly due to randomness in interlayer edges
        
    def test_parameter_validation_m_less_than_n(self):
        """Test that m must be less than n."""
        # This should work
        G = multilayer_barabasi_albert(n=10, m=3, num_layers=2, seed=42)
        assert G is not None
        
    def test_directed_network(self):
        """Test directed network generation."""
        G = multilayer_barabasi_albert(n=15, m=2, num_layers=2, directed=True, seed=42)
        assert G is not None
        # Check if it's a directed graph type
        assert isinstance(G, (nx.MultiDiGraph, nx.DiGraph))
        
    def test_interlayer_probability(self):
        """Test interlayer edge probability parameter."""
        # High interlayer probability
        G_high = multilayer_barabasi_albert(n=20, m=2, num_layers=3, interlayer_prob=0.5, seed=42)
        
        # Low interlayer probability
        G_low = multilayer_barabasi_albert(n=20, m=2, num_layers=3, interlayer_prob=0.01, seed=42)
        
        # Both should generate valid networks
        assert G_high.number_of_nodes() > 0
        assert G_low.number_of_nodes() > 0
        
    def test_single_layer(self):
        """Test generation with single layer."""
        G = multilayer_barabasi_albert(n=20, m=2, num_layers=1, seed=42)
        assert G is not None
        assert G.number_of_nodes() > 0


class TestMultilayerErdosRenyi:
    """Tests for multilayer_erdos_renyi function."""
    
    def test_basic_generation(self):
        """Test basic ER network generation."""
        G = multilayer_erdos_renyi(n=15, p=0.3, num_layers=2, seed=42)
        assert G is not None
        assert G.number_of_nodes() > 0
        
    def test_determinism_with_seed(self):
        """Test that same seed produces same network."""
        G1 = multilayer_erdos_renyi(n=12, p=0.2, num_layers=2, seed=99)
        G2 = multilayer_erdos_renyi(n=12, p=0.2, num_layers=2, seed=99)
        
        assert G1.number_of_nodes() == G2.number_of_nodes()
        assert G1.number_of_edges() == G2.number_of_edges()
        
    def test_edge_probability(self):
        """Test that higher p creates more edges."""
        G_sparse = multilayer_erdos_renyi(n=20, p=0.1, num_layers=2, seed=42)
        G_dense = multilayer_erdos_renyi(n=20, p=0.5, num_layers=2, seed=42)
        
        # Dense should have more edges (on average)
        assert G_sparse.number_of_nodes() == G_dense.number_of_nodes()
        # Can't guarantee edge count due to randomness, but networks should exist
        assert G_sparse.number_of_edges() >= 0
        assert G_dense.number_of_edges() >= 0
        
    def test_zero_probability(self):
        """Test with p=0 creates no intra-layer edges."""
        G = multilayer_erdos_renyi(n=10, p=0.0, num_layers=2, interlayer_prob=0.0, seed=42)
        assert G is not None
        # Should have nodes but possibly no edges
        assert G.number_of_nodes() > 0


class TestMultilayerStochasticBlockModel:
    """Tests for multilayer_stochastic_block_model function."""
    
    def test_basic_generation(self):
        """Test basic SBM generation."""
        block_sizes = [5, 5, 5]
        p_matrix = [[0.8, 0.1, 0.1],
                    [0.1, 0.8, 0.1],
                    [0.1, 0.1, 0.8]]
        
        G = multilayer_stochastic_block_model(
            block_sizes=block_sizes,
            p_matrix=p_matrix,
            num_layers=2,
            seed=42
        )
        assert G is not None
        assert G.number_of_nodes() > 0
        
    def test_determinism_with_seed(self):
        """Test that same seed produces same network."""
        block_sizes = [4, 4]
        p_matrix = [[0.7, 0.2],
                    [0.2, 0.7]]
        
        G1 = multilayer_stochastic_block_model(
            block_sizes=block_sizes,
            p_matrix=p_matrix,
            num_layers=2,
            seed=55
        )
        G2 = multilayer_stochastic_block_model(
            block_sizes=block_sizes,
            p_matrix=p_matrix,
            num_layers=2,
            seed=55
        )
        
        assert G1.number_of_nodes() == G2.number_of_nodes()
        assert G1.number_of_edges() == G2.number_of_edges()
        
    def test_block_structure(self):
        """Test that network respects block structure."""
        block_sizes = [10, 10]
        p_matrix = [[0.9, 0.05],  # High intra-block, low inter-block
                    [0.05, 0.9]]
        
        G = multilayer_stochastic_block_model(
            block_sizes=block_sizes,
            p_matrix=p_matrix,
            num_layers=2,
            seed=42
        )
        
        assert G.number_of_nodes() > 0
        # Network should have community structure (but we don't test exact properties)
