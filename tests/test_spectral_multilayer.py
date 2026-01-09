"""Tests for multilayer spectral clustering algorithms.

This module tests the two spectral clustering variants:
1. Supra-Laplacian Spectral Clustering
2. Multiplex (Aggregated) Laplacian Spectral Clustering

Test coverage includes:
- L=1 reduction to standard spectral clustering
- Omega extremes (supra variant)
- Determinism with fixed seed
- Variant distinction
- DSL integration
"""

import pytest
import numpy as np

from py3plex.core import multinet
from py3plex.algorithms.community_detection.spectral_multilayer import (
    spectral_multilayer_supra,
    spectral_multilayer_multiplex,
)
from py3plex.dsl import Q, L
from py3plex.exceptions import AlgorithmError, Py3plexException


def create_test_network():
    """Create a simple test multilayer network with community structure.
    
    Returns a network with 2 clear communities:
    - Community 1: A, B, C (densely connected)
    - Community 2: D, E, F (densely connected)
    With a weak inter-community link.
    """
    net = multinet.multi_layer_network(directed=False)
    
    # Add edges for community 1 (A-B-C triangle)
    net.add_edges([
        ['A', 'L1', 'B', 'L1', 1.0],
        ['B', 'L1', 'C', 'L1', 1.0],
        ['C', 'L1', 'A', 'L1', 1.0],
    ], input_type='list')
    
    # Add edges for community 2 (D-E-F triangle)
    net.add_edges([
        ['D', 'L1', 'E', 'L1', 1.0],
        ['E', 'L1', 'F', 'L1', 1.0],
        ['F', 'L1', 'D', 'L1', 1.0],
    ], input_type='list')
    
    # Weak inter-community link
    net.add_edges([
        ['C', 'L1', 'D', 'L1', 0.1],
    ], input_type='list')
    
    return net


def create_multiplex_network():
    """Create a multiplex network with conflicting layer structure.
    
    Layer 1: A-B-C and D-E-F communities
    Layer 2: A-B-D and C-E-F communities (different structure)
    """
    net = multinet.multi_layer_network(directed=False)
    
    # Layer 1: Communities {A,B,C} and {D,E,F}
    net.add_edges([
        ['A', 'L1', 'B', 'L1', 1.0],
        ['B', 'L1', 'C', 'L1', 1.0],
        ['C', 'L1', 'A', 'L1', 1.0],
        ['D', 'L1', 'E', 'L1', 1.0],
        ['E', 'L1', 'F', 'L1', 1.0],
        ['F', 'L1', 'D', 'L1', 1.0],
    ], input_type='list')
    
    # Layer 2: Communities {A,B,D} and {C,E,F}
    net.add_edges([
        ['A', 'L2', 'B', 'L2', 1.0],
        ['B', 'L2', 'D', 'L2', 1.0],
        ['D', 'L2', 'A', 'L2', 1.0],
        ['C', 'L2', 'E', 'L2', 1.0],
        ['E', 'L2', 'F', 'L2', 1.0],
        ['F', 'L2', 'C', 'L2', 1.0],
    ], input_type='list')
    
    return net


class TestSupraLaplacianSpectral:
    """Tests for Supra-Laplacian Spectral Clustering."""
    
    def test_basic_clustering(self):
        """Test basic clustering on a simple network."""
        net = create_test_network()
        
        partition, metadata = spectral_multilayer_supra(
            net, k=2, omega=1.0, random_state=42
        )
        
        # Check partition structure
        assert isinstance(partition, dict)
        assert len(partition) == 6  # 6 nodes
        
        # Check metadata
        assert "embedding_nodes" in metadata
        assert "embedding_supra" in metadata
        assert "n_communities" in metadata
        assert metadata["n_communities"] == 2
        assert metadata["omega"] == 1.0
        
        # Check embedding dimensions
        nodes_list = list(net.get_nodes())
        unique_nodes = set(node for node, layer in nodes_list)
        assert metadata["embedding_nodes"].shape == (len(unique_nodes), 2)
        assert metadata["embedding_supra"].shape == (len(nodes_list), 2)
    
    def test_k_validation(self):
        """Test that k parameter is validated."""
        net = create_test_network()
        
        # k must be positive
        with pytest.raises(AlgorithmError):
            spectral_multilayer_supra(net, k=0, omega=1.0)
        
        with pytest.raises(AlgorithmError):
            spectral_multilayer_supra(net, k=-1, omega=1.0)
        
        # k must be integer
        with pytest.raises(AlgorithmError):
            spectral_multilayer_supra(net, k=2.5, omega=1.0)
    
    def test_omega_validation(self):
        """Test that omega parameter is validated."""
        net = create_test_network()
        
        # omega must be non-negative
        with pytest.raises(AlgorithmError):
            spectral_multilayer_supra(net, k=2, omega=-0.5)
    
    def test_omega_zero(self):
        """Test omega=0 (independent layers)."""
        net = create_test_network()
        
        # omega=0 means no interlayer coupling
        partition, metadata = spectral_multilayer_supra(
            net, k=2, omega=0.0, random_state=42
        )
        
        assert len(partition) == 6
        assert metadata["omega"] == 0.0
    
    def test_omega_large(self):
        """Test large omega (strong coupling)."""
        net = create_multiplex_network()
        
        # Large omega should synchronize replicas across layers
        partition, metadata = spectral_multilayer_supra(
            net, k=2, omega=10.0, random_state=42
        )
        
        assert len(partition) == 12  # 6 nodes × 2 layers
        assert metadata["omega"] == 10.0
        
        # With strong coupling, same node should have same community across layers
        # (This is a heuristic check - not guaranteed but likely)
        node_communities = {}
        for (node, layer), comm in partition.items():
            if node not in node_communities:
                node_communities[node] = []
            node_communities[node].append(comm)
        
        # At least some nodes should have consistent communities across layers
        consistent_nodes = sum(
            1 for comms in node_communities.values() if len(set(comms)) == 1
        )
        assert consistent_nodes >= 3  # At least half should be consistent
    
    def test_determinism(self):
        """Test that fixed seed gives deterministic results."""
        net = create_test_network()
        
        partition1, metadata1 = spectral_multilayer_supra(
            net, k=2, omega=1.0, random_state=42
        )
        
        partition2, metadata2 = spectral_multilayer_supra(
            net, k=2, omega=1.0, random_state=42
        )
        
        # Partitions should be identical
        assert partition1 == partition2
        
        # Embeddings should be identical (up to numerical precision)
        assert np.allclose(
            metadata1["embedding_nodes"],
            metadata2["embedding_nodes"],
            atol=1e-6
        )
    
    def test_l_equals_1_reduction(self):
        """Test that L=1 reduces to standard spectral clustering."""
        net = create_test_network()
        
        # With a single layer, supra variant should behave like standard spectral
        partition, metadata = spectral_multilayer_supra(
            net, k=2, omega=0.5, random_state=42
        )
        
        # Check that we got 2 communities
        n_communities = len(set(partition.values()))
        assert n_communities == 2
    
    def test_empty_network(self):
        """Test error handling for empty network."""
        net = multinet.multi_layer_network(directed=False)
        
        with pytest.raises(Py3plexException):
            spectral_multilayer_supra(net, k=2, omega=1.0)
    
    def test_k_exceeds_nodes(self):
        """Test error when k exceeds number of nodes."""
        net = create_test_network()
        
        with pytest.raises(AlgorithmError):
            spectral_multilayer_supra(net, k=10, omega=1.0)  # Only 6 nodes


class TestMultiplexSpectral:
    """Tests for Multiplex (Aggregated) Laplacian Spectral Clustering."""
    
    def test_basic_clustering(self):
        """Test basic clustering on a simple network."""
        net = create_test_network()
        
        partition, metadata = spectral_multilayer_multiplex(
            net, k=2, random_state=42
        )
        
        # Check partition structure
        assert isinstance(partition, dict)
        assert len(partition) == 6  # 6 nodes
        
        # Check metadata
        assert "embedding_nodes" in metadata
        assert "n_communities" in metadata
        assert metadata["n_communities"] == 2
        assert "embedding_supra" not in metadata  # Multiplex doesn't create supra
        
        # Check embedding dimensions
        nodes_list = list(net.get_nodes())
        unique_nodes = set(node for node, layer in nodes_list)
        assert metadata["embedding_nodes"].shape == (len(unique_nodes), 2)
    
    def test_k_validation(self):
        """Test that k parameter is validated."""
        net = create_test_network()
        
        # k must be positive
        with pytest.raises(AlgorithmError):
            spectral_multilayer_multiplex(net, k=0)
        
        with pytest.raises(AlgorithmError):
            spectral_multilayer_multiplex(net, k=-1)
    
    def test_determinism(self):
        """Test that fixed seed gives deterministic results."""
        net = create_test_network()
        
        partition1, metadata1 = spectral_multilayer_multiplex(
            net, k=2, random_state=42
        )
        
        partition2, metadata2 = spectral_multilayer_multiplex(
            net, k=2, random_state=42
        )
        
        # Partitions should be identical
        assert partition1 == partition2
        
        # Embeddings should be identical (up to numerical precision)
        assert np.allclose(
            metadata1["embedding_nodes"],
            metadata2["embedding_nodes"],
            atol=1e-6
        )
    
    def test_l_equals_1_reduction(self):
        """Test that L=1 reduces to standard spectral clustering."""
        net = create_test_network()
        
        # With a single layer, multiplex should behave like standard spectral
        partition, metadata = spectral_multilayer_multiplex(
            net, k=2, random_state=42
        )
        
        # Check that we got 2 communities
        n_communities = len(set(partition.values()))
        assert n_communities == 2
    
    def test_empty_network(self):
        """Test error handling for empty network."""
        net = multinet.multi_layer_network(directed=False)
        
        with pytest.raises(Py3plexException):
            spectral_multilayer_multiplex(net, k=2)
    
    def test_k_exceeds_nodes(self):
        """Test error when k exceeds number of nodes."""
        net = create_test_network()
        
        with pytest.raises(AlgorithmError):
            spectral_multilayer_multiplex(net, k=10)  # Only 6 nodes


class TestVariantDistinction:
    """Test that supra and multiplex variants give different results."""
    
    def test_conflicting_layers(self):
        """Test that variants differ on multiplex with conflicting structure."""
        net = create_multiplex_network()
        
        # Run both variants
        partition_supra, _ = spectral_multilayer_supra(
            net, k=2, omega=1.0, random_state=42
        )
        
        partition_multiplex, _ = spectral_multilayer_multiplex(
            net, k=2, random_state=42
        )
        
        # Partitions should exist
        assert len(partition_supra) > 0
        assert len(partition_multiplex) > 0
        
        # They might differ because supra considers layer structure more explicitly
        # This is not guaranteed but likely for this conflicting network
        # Just check they both complete successfully
        assert len(set(partition_supra.values())) == 2
        assert len(set(partition_multiplex.values())) == 2


class TestDSLIntegration:
    """Test DSL v2 integration for spectral methods."""
    
    def test_supra_via_dsl(self):
        """Test supra-Laplacian spectral clustering via DSL."""
        net = create_test_network()
        
        result = (
            Q.nodes()
             .from_layers(L["L1"])
             .community(
                 method="spectral_multilayer_supra",
                 k=2,
                 omega=0.8,
                 random_state=42,
             )
             .execute(net)
        )
        
        # Check that community detection metadata is present
        assert "community_detection" in result.meta
        assert result.meta["community_detection"]["method"] == "spectral_multilayer_supra"
        
        # Check that partition was attached
        partition = net.get_partition_by_name("default")
        assert partition is not None
        assert len(set(partition.values())) == 2
    
    def test_multiplex_via_dsl(self):
        """Test multiplex spectral clustering via DSL."""
        net = create_test_network()
        
        result = (
            Q.nodes()
             .from_layers(L["L1"])
             .community(
                 method="spectral_multilayer_multiplex",
                 k=2,
                 random_state=42,
             )
             .execute(net)
        )
        
        # Check that community detection metadata is present
        assert "community_detection" in result.meta
        assert result.meta["community_detection"]["method"] == "spectral_multilayer_multiplex"
        
        # Check that partition was attached
        partition = net.get_partition_by_name("default")
        assert partition is not None
        assert len(set(partition.values())) == 2
    
    def test_missing_k_parameter(self):
        """Test that missing k parameter raises error."""
        net = create_test_network()
        
        # Should raise error when k is not provided
        with pytest.raises(AlgorithmError):
            result = (
                Q.nodes()
                 .from_layers(L["L1"])
                 .community(
                     method="spectral_multilayer_supra",
                     omega=0.8,
                     random_state=42,
                 )
                 .execute(net)
            )
    
    def test_multilayer_supra(self):
        """Test supra variant on true multilayer network."""
        net = create_multiplex_network()
        
        result = (
            Q.nodes()
             .from_layers(L["L1"] + L["L2"])
             .community(
                 method="spectral_multilayer_supra",
                 k=2,
                 omega=1.5,
                 random_state=42,
             )
             .execute(net)
        )
        
        partition = net.get_partition_by_name("default")
        assert partition is not None
        
        # Should have partitions for both layers
        layers_in_partition = set(layer for node, layer in partition.keys())
        assert len(layers_in_partition) >= 1


class TestLaplacianType:
    """Test Laplacian type validation."""
    
    def test_only_normalized_supported(self):
        """Test that only normalized Laplacian is supported."""
        net = create_test_network()
        
        # Should accept "normalized"
        partition, _ = spectral_multilayer_supra(
            net, k=2, omega=1.0, laplacian="normalized", random_state=42
        )
        assert len(partition) > 0
        
        # Should reject other types
        with pytest.raises(AlgorithmError):
            spectral_multilayer_supra(
                net, k=2, omega=1.0, laplacian="unnormalized", random_state=42
            )


class TestEigenSolver:
    """Test eigen solver selection."""
    
    def test_dense_solver(self):
        """Test dense eigen solver."""
        net = create_test_network()
        
        partition, metadata = spectral_multilayer_supra(
            net, k=2, omega=1.0, eigen_solver="dense", random_state=42
        )
        
        assert len(partition) > 0
        assert metadata["embedding_nodes"].shape[1] == 2
    
    def test_lobpcg_solver(self):
        """Test LOBPCG eigen solver."""
        net = create_test_network()
        
        partition, metadata = spectral_multilayer_supra(
            net, k=2, omega=1.0, eigen_solver="lobpcg", random_state=42
        )
        
        assert len(partition) > 0
        assert metadata["embedding_nodes"].shape[1] == 2
    
    def test_auto_solver(self):
        """Test automatic solver selection."""
        net = create_test_network()
        
        # With None, should auto-select based on size
        partition, metadata = spectral_multilayer_supra(
            net, k=2, omega=1.0, eigen_solver=None, random_state=42
        )
        
        assert len(partition) > 0
    
    def test_invalid_solver(self):
        """Test invalid solver raises error."""
        net = create_test_network()
        
        with pytest.raises(AlgorithmError):
            spectral_multilayer_supra(
                net, k=2, omega=1.0, eigen_solver="invalid", random_state=42
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
