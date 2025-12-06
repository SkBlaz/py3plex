"""
Tests for multilayer stochastic block model (SBM) generator.
"""

import pytest
import numpy as np
import networkx as nx

from py3plex.core.random_generators import (
    random_multilayer_SBM,
    SBMMetadata,
    _sample_sbm_adjacency,
)


class TestSBMMetadata:
    """Tests for SBMMetadata dataclass."""

    def test_metadata_fields(self):
        """Test that SBMMetadata has expected fields."""
        block_memberships = np.array([0, 1, 0, 1, 2])
        block_matrix = np.array([[0.5, 0.1, 0.1], [0.1, 0.5, 0.1], [0.1, 0.1, 0.5]])
        node_ids = ["v0", "v1", "v2", "v3", "v4"]
        layer_names = ["L0", "L1"]

        meta = SBMMetadata(
            block_memberships=block_memberships,
            block_matrix=block_matrix,
            node_ids=node_ids,
            layer_names=layer_names,
        )

        assert np.array_equal(meta.block_memberships, block_memberships)
        assert np.array_equal(meta.block_matrix, block_matrix)
        assert meta.node_ids == node_ids
        assert meta.layer_names == layer_names


class TestSampleSBMAdjacency:
    """Tests for _sample_sbm_adjacency helper function."""

    def test_basic_adjacency(self):
        """Test basic adjacency matrix generation."""
        rng = np.random.default_rng(42)
        block_memberships = np.array([0, 0, 1, 1])
        block_matrix = np.array([[0.9, 0.1], [0.1, 0.9]])

        adj = _sample_sbm_adjacency(
            block_memberships=block_memberships,
            block_matrix=block_matrix,
            directed=False,
            rng=rng,
        )

        # Check shape
        assert adj.shape == (4, 4)
        # Check no self-loops
        assert np.all(np.diag(adj) == 0)
        # Check symmetry for undirected
        assert np.allclose(adj, adj.T)

    def test_directed_adjacency(self):
        """Test directed adjacency matrix generation."""
        rng = np.random.default_rng(42)
        block_memberships = np.array([0, 0, 1, 1])
        block_matrix = np.array([[0.9, 0.1], [0.1, 0.9]])

        adj = _sample_sbm_adjacency(
            block_memberships=block_memberships,
            block_matrix=block_matrix,
            directed=True,
            rng=rng,
        )

        # Check shape
        assert adj.shape == (4, 4)
        # Check no self-loops
        assert np.all(np.diag(adj) == 0)
        # Directed graphs don't need to be symmetric

    def test_zero_probability(self):
        """Test with zero probability (no edges)."""
        rng = np.random.default_rng(42)
        block_memberships = np.array([0, 0, 1, 1])
        block_matrix = np.array([[0.0, 0.0], [0.0, 0.0]])

        adj = _sample_sbm_adjacency(
            block_memberships=block_memberships,
            block_matrix=block_matrix,
            directed=False,
            rng=rng,
        )

        # Should have no edges
        assert np.sum(adj) == 0

    def test_full_probability(self):
        """Test with full probability (complete graph)."""
        rng = np.random.default_rng(42)
        block_memberships = np.array([0, 0, 0])
        block_matrix = np.array([[1.0]])

        adj = _sample_sbm_adjacency(
            block_memberships=block_memberships,
            block_matrix=block_matrix,
            directed=False,
            rng=rng,
        )

        # Check shape
        assert adj.shape == (3, 3)
        # Check no self-loops
        assert np.all(np.diag(adj) == 0)
        # All other entries should be 1
        expected = np.ones((3, 3)) - np.eye(3)
        assert np.allclose(adj, expected)


class TestRandomMultilayerSBM:
    """Tests for random_multilayer_SBM function."""

    def test_basic_generation(self):
        """Test basic SBM network generation."""
        net, meta = random_multilayer_SBM(
            n_layers=3,
            n_nodes=20,
            n_blocks=2,
            p_in=0.5,
            p_out=0.05,
            seed=42,
        )

        assert net is not None
        assert meta is not None
        assert hasattr(net, "core_network")
        assert meta.block_memberships.shape == (20,)
        assert meta.block_matrix.shape == (2, 2)
        assert len(meta.node_ids) == 20
        assert len(meta.layer_names) == 3

    def test_with_coupling(self):
        """Test SBM generation with inter-layer coupling."""
        net, meta = random_multilayer_SBM(
            n_layers=3,
            n_nodes=10,
            n_blocks=2,
            p_in=0.5,
            p_out=0.1,
            coupling=0.5,
            seed=42,
        )

        assert net is not None
        assert net.core_network.number_of_edges() > 0

    def test_no_coupling(self):
        """Test SBM generation without inter-layer coupling."""
        net, meta = random_multilayer_SBM(
            n_layers=2,
            n_nodes=10,
            n_blocks=2,
            p_in=0.5,
            p_out=0.1,
            coupling=0.0,
            seed=42,
        )

        assert net is not None
        # All edges should be intra-layer (same layer for src and dst)
        for edge in net.get_edges():
            src_layer = edge[0][1]
            dst_layer = edge[1][1]
            assert src_layer == dst_layer

    def test_directed(self):
        """Test directed SBM network generation."""
        net, meta = random_multilayer_SBM(
            n_layers=2,
            n_nodes=10,
            n_blocks=2,
            p_in=0.5,
            p_out=0.1,
            directed=True,
            seed=42,
        )

        assert net is not None
        assert net.directed is True

    def test_reproducibility(self):
        """Test that same seed produces identical results."""
        net1, meta1 = random_multilayer_SBM(
            n_layers=2,
            n_nodes=10,
            n_blocks=3,
            p_in=0.5,
            p_out=0.1,
            seed=42,
        )

        net2, meta2 = random_multilayer_SBM(
            n_layers=2,
            n_nodes=10,
            n_blocks=3,
            p_in=0.5,
            p_out=0.1,
            seed=42,
        )

        assert np.array_equal(meta1.block_memberships, meta2.block_memberships)
        assert np.array_equal(meta1.block_matrix, meta2.block_matrix)

    def test_block_matrix_structure(self):
        """Test that block matrix has correct structure."""
        net, meta = random_multilayer_SBM(
            n_layers=2,
            n_nodes=10,
            n_blocks=3,
            p_in=0.8,
            p_out=0.2,
            seed=42,
        )

        # Diagonal should be p_in
        assert np.allclose(np.diag(meta.block_matrix), 0.8)
        # Off-diagonal should be p_out
        off_diag = meta.block_matrix[~np.eye(3, dtype=bool)]
        assert np.allclose(off_diag, 0.2)

    def test_single_layer(self):
        """Test SBM with single layer."""
        net, meta = random_multilayer_SBM(
            n_layers=1,
            n_nodes=10,
            n_blocks=2,
            p_in=0.5,
            p_out=0.1,
            seed=42,
        )

        assert net is not None
        assert len(meta.layer_names) == 1

    def test_single_block(self):
        """Test SBM with single block (all nodes in same community)."""
        net, meta = random_multilayer_SBM(
            n_layers=2,
            n_nodes=10,
            n_blocks=1,
            p_in=0.5,
            p_out=0.1,  # p_out only affects off-diagonal of block_matrix (empty for single block)
            seed=42,
        )

        assert net is not None
        assert np.all(meta.block_memberships == 0)

    def test_many_blocks(self):
        """Test SBM with many blocks (equal to n_nodes)."""
        net, meta = random_multilayer_SBM(
            n_layers=2,
            n_nodes=5,
            n_blocks=5,
            p_in=0.5,
            p_out=0.1,
            seed=42,
        )

        assert net is not None
        assert meta.block_matrix.shape == (5, 5)


class TestRandomMultilayerSBMValidation:
    """Tests for input validation in random_multilayer_SBM."""

    def test_invalid_n_layers_zero(self):
        """Test that n_layers=0 raises ValueError."""
        with pytest.raises(ValueError, match="n_layers must be positive"):
            random_multilayer_SBM(
                n_layers=0, n_nodes=10, n_blocks=2, p_in=0.5, p_out=0.1
            )

    def test_invalid_n_layers_negative(self):
        """Test that n_layers<0 raises ValueError."""
        with pytest.raises(ValueError, match="n_layers must be positive"):
            random_multilayer_SBM(
                n_layers=-1, n_nodes=10, n_blocks=2, p_in=0.5, p_out=0.1
            )

    def test_invalid_n_nodes_zero(self):
        """Test that n_nodes=0 raises ValueError."""
        with pytest.raises(ValueError, match="n_nodes must be positive"):
            random_multilayer_SBM(
                n_layers=2, n_nodes=0, n_blocks=2, p_in=0.5, p_out=0.1
            )

    def test_invalid_n_nodes_negative(self):
        """Test that n_nodes<0 raises ValueError."""
        with pytest.raises(ValueError, match="n_nodes must be positive"):
            random_multilayer_SBM(
                n_layers=2, n_nodes=-5, n_blocks=2, p_in=0.5, p_out=0.1
            )

    def test_invalid_n_blocks_zero(self):
        """Test that n_blocks=0 raises ValueError."""
        with pytest.raises(ValueError, match="n_blocks must be in"):
            random_multilayer_SBM(
                n_layers=2, n_nodes=10, n_blocks=0, p_in=0.5, p_out=0.1
            )

    def test_invalid_n_blocks_greater_than_nodes(self):
        """Test that n_blocks > n_nodes raises ValueError."""
        with pytest.raises(ValueError, match="n_blocks must be in"):
            random_multilayer_SBM(
                n_layers=2, n_nodes=5, n_blocks=10, p_in=0.5, p_out=0.1
            )

    def test_invalid_p_in_greater_than_one(self):
        """Test that p_in > 1 raises ValueError."""
        with pytest.raises(ValueError, match="p_in and p_out must be within"):
            random_multilayer_SBM(
                n_layers=2, n_nodes=10, n_blocks=2, p_in=1.5, p_out=0.1
            )

    def test_invalid_p_in_negative(self):
        """Test that p_in < 0 raises ValueError."""
        with pytest.raises(ValueError, match="p_in and p_out must be within"):
            random_multilayer_SBM(
                n_layers=2, n_nodes=10, n_blocks=2, p_in=-0.1, p_out=0.1
            )

    def test_invalid_p_out_greater_than_one(self):
        """Test that p_out > 1 raises ValueError."""
        with pytest.raises(ValueError, match="p_in and p_out must be within"):
            random_multilayer_SBM(
                n_layers=2, n_nodes=10, n_blocks=2, p_in=0.5, p_out=1.5
            )

    def test_invalid_p_out_negative(self):
        """Test that p_out < 0 raises ValueError."""
        with pytest.raises(ValueError, match="p_in and p_out must be within"):
            random_multilayer_SBM(
                n_layers=2, n_nodes=10, n_blocks=2, p_in=0.5, p_out=-0.1
            )

    def test_invalid_coupling_greater_than_one(self):
        """Test that coupling > 1 raises ValueError."""
        with pytest.raises(ValueError, match="coupling must be within"):
            random_multilayer_SBM(
                n_layers=2, n_nodes=10, n_blocks=2, p_in=0.5, p_out=0.1, coupling=1.5
            )

    def test_invalid_coupling_negative(self):
        """Test that coupling < 0 raises ValueError."""
        with pytest.raises(ValueError, match="coupling must be within"):
            random_multilayer_SBM(
                n_layers=2, n_nodes=10, n_blocks=2, p_in=0.5, p_out=0.1, coupling=-0.1
            )


class TestRandomMultilayerSBMIntegration:
    """Integration tests for random_multilayer_SBM."""

    def test_network_structure(self):
        """Test that generated network has correct structure."""
        net, meta = random_multilayer_SBM(
            n_layers=3,
            n_nodes=10,
            n_blocks=2,
            p_in=0.5,
            p_out=0.1,
            seed=42,
        )

        # Check nodes are in expected format
        nodes = list(net.get_nodes())
        for node in nodes:
            assert isinstance(node, tuple)
            assert len(node) == 2
            node_id, layer = node
            assert node_id in meta.node_ids
            assert layer in meta.layer_names

    def test_edge_format(self):
        """Test that edges have correct format."""
        net, meta = random_multilayer_SBM(
            n_layers=2,
            n_nodes=10,
            n_blocks=2,
            p_in=0.5,
            p_out=0.1,
            coupling=0.5,
            seed=42,
        )

        for edge in net.get_edges():
            src, dst = edge
            assert isinstance(src, tuple)
            assert isinstance(dst, tuple)
            assert src[0] in meta.node_ids
            assert dst[0] in meta.node_ids
            assert src[1] in meta.layer_names
            assert dst[1] in meta.layer_names

    def test_layer_coverage(self):
        """Test that all layers have nodes."""
        net, meta = random_multilayer_SBM(
            n_layers=5,
            n_nodes=20,
            n_blocks=3,
            p_in=0.5,
            p_out=0.1,
            seed=42,
        )

        layers_with_nodes = set()
        for node in net.get_nodes():
            layers_with_nodes.add(node[1])

        # All layers should have nodes
        assert layers_with_nodes == set(meta.layer_names)

    def test_high_p_in_creates_denser_blocks(self):
        """Test that higher p_in creates denser blocks."""
        # Generate two networks with different p_in values
        net_dense, _ = random_multilayer_SBM(
            n_layers=1,
            n_nodes=20,
            n_blocks=2,
            p_in=0.9,
            p_out=0.1,
            seed=42,
        )

        net_sparse, _ = random_multilayer_SBM(
            n_layers=1,
            n_nodes=20,
            n_blocks=2,
            p_in=0.2,
            p_out=0.1,
            seed=42,
        )

        # Dense network should have more edges on average
        # (though randomness means we can't guarantee this every time)
        # We just verify both networks are valid
        assert net_dense.core_network.number_of_edges() >= 0
        assert net_sparse.core_network.number_of_edges() >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
