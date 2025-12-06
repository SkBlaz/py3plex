"""Tests for the py3plex.alignment module."""

import numpy as np
import pytest

from py3plex.alignment import (
    AlignmentResult,
    align_networks,
    cosine_similarity_matrix,
    degree_correlation,
    edge_agreement,
    multilayer_node_features,
)
from py3plex.core import multinet


class TestMultilayerNodeFeatures:
    """Tests for multilayer_node_features function."""

    def test_basic_feature_extraction(self):
        """Test basic feature extraction from a simple network."""
        net = multinet.multi_layer_network(directed=False)
        net.add_edges([
            {'source': 'A', 'target': 'B', 'source_type': 'L1', 'target_type': 'L1'},
            {'source': 'B', 'target': 'C', 'source_type': 'L1', 'target_type': 'L1'},
        ])

        features = multilayer_node_features(net)

        # Should have 3 nodes
        assert len(features) == 3
        assert 'A' in features
        assert 'B' in features
        assert 'C' in features

        # All feature vectors should have the same length
        feature_lengths = [len(f) for f in features.values()]
        assert len(set(feature_lengths)) == 1

    def test_multilayer_feature_extraction(self):
        """Test feature extraction from a multilayer network."""
        net = multinet.multi_layer_network(directed=False)
        net.add_edges([
            {'source': 'A', 'target': 'B', 'source_type': 'L1', 'target_type': 'L1'},
            {'source': 'A', 'target': 'C', 'source_type': 'L2', 'target_type': 'L2'},
        ])

        features = multilayer_node_features(net)

        # Node A should have edges in both layers
        assert 'A' in features
        # Feature vector should include total degree, per-layer degree, and entropy
        # For 2 layers: 1 (total) + 2 (per-layer) + 1 (entropy) = 4
        assert len(features['A']) == 4

    def test_feature_extraction_with_selected_layers(self):
        """Test feature extraction with specific layers."""
        net = multinet.multi_layer_network(directed=False)
        net.add_edges([
            {'source': 'A', 'target': 'B', 'source_type': 'L1', 'target_type': 'L1'},
            {'source': 'A', 'target': 'C', 'source_type': 'L2', 'target_type': 'L2'},
        ])

        # Only consider L1
        features = multilayer_node_features(net, layers=['L1'])

        # Feature vector for single layer: 1 (total) + 1 (per-layer) + 1 (entropy) = 3
        assert len(features['A']) == 3

    def test_feature_extraction_options(self):
        """Test feature extraction with different options."""
        net = multinet.multi_layer_network(directed=False)
        net.add_edges([
            {'source': 'A', 'target': 'B', 'source_type': 'L1', 'target_type': 'L1'},
        ])

        # Only total degree
        features = multilayer_node_features(
            net,
            include_total_degree=True,
            include_per_layer_degree=False,
            include_layer_entropy=False,
        )
        assert len(features['A']) == 1

        # Only per-layer degree
        features = multilayer_node_features(
            net,
            include_total_degree=False,
            include_per_layer_degree=True,
            include_layer_entropy=False,
        )
        assert len(features['A']) == 1

        # Only entropy
        features = multilayer_node_features(
            net,
            include_total_degree=False,
            include_per_layer_degree=False,
            include_layer_entropy=True,
        )
        assert len(features['A']) == 1


class TestCosineSimilarityMatrix:
    """Tests for cosine_similarity_matrix function."""

    def test_identical_vectors(self):
        """Test cosine similarity of identical vectors."""
        A = np.array([[1.0, 2.0, 3.0]])
        B = np.array([[1.0, 2.0, 3.0]])

        S = cosine_similarity_matrix(A, B)

        assert S.shape == (1, 1)
        assert np.isclose(S[0, 0], 1.0)

    def test_orthogonal_vectors(self):
        """Test cosine similarity of orthogonal vectors."""
        A = np.array([[1.0, 0.0]])
        B = np.array([[0.0, 1.0]])

        S = cosine_similarity_matrix(A, B)

        assert S.shape == (1, 1)
        assert np.isclose(S[0, 0], 0.0)

    def test_opposite_vectors(self):
        """Test cosine similarity of opposite vectors."""
        A = np.array([[1.0, 0.0]])
        B = np.array([[-1.0, 0.0]])

        S = cosine_similarity_matrix(A, B)

        assert S.shape == (1, 1)
        assert np.isclose(S[0, 0], -1.0)

    def test_zero_vector(self):
        """Test cosine similarity with zero vector."""
        A = np.array([[0.0, 0.0]])
        B = np.array([[1.0, 2.0]])

        S = cosine_similarity_matrix(A, B)

        assert S.shape == (1, 1)
        assert S[0, 0] == 0.0

    def test_multiple_vectors(self):
        """Test cosine similarity matrix with multiple vectors."""
        A = np.array([
            [1.0, 0.0],
            [0.0, 1.0],
        ])
        B = np.array([
            [1.0, 0.0],
            [1.0, 1.0],
        ])

        S = cosine_similarity_matrix(A, B)

        assert S.shape == (2, 2)
        # A[0] vs B[0] should be 1 (identical)
        assert np.isclose(S[0, 0], 1.0)
        # A[1] vs B[0] should be 0 (orthogonal)
        assert np.isclose(S[1, 0], 0.0)


class TestAlignNetworks:
    """Tests for align_networks function."""

    def test_identical_networks(self):
        """Test alignment of identical networks."""
        net_a = multinet.multi_layer_network(directed=False)
        net_a.add_edges([
            {'source': 'A', 'target': 'B', 'source_type': 'L1', 'target_type': 'L1'},
            {'source': 'B', 'target': 'C', 'source_type': 'L1', 'target_type': 'L1'},
        ])

        net_b = multinet.multi_layer_network(directed=False)
        net_b.add_edges([
            {'source': 'A', 'target': 'B', 'source_type': 'L1', 'target_type': 'L1'},
            {'source': 'B', 'target': 'C', 'source_type': 'L1', 'target_type': 'L1'},
        ])

        result = align_networks(net_a, net_b)

        assert isinstance(result, AlignmentResult)
        assert len(result.node_mapping) == 3
        # Should have high alignment score for identical networks
        assert result.score >= 0.9

    def test_isomorphic_networks(self):
        """Test alignment of isomorphic networks with different node names."""
        net_a = multinet.multi_layer_network(directed=False)
        net_a.add_edges([
            {'source': 'A', 'target': 'B', 'source_type': 'L1', 'target_type': 'L1'},
        ])

        net_b = multinet.multi_layer_network(directed=False)
        net_b.add_edges([
            {'source': 'X', 'target': 'Y', 'source_type': 'L1', 'target_type': 'L1'},
        ])

        result = align_networks(net_a, net_b)

        assert len(result.node_mapping) == 2
        assert result.score >= 0.9
        assert result.similarity_matrix is not None
        assert result.similarity_matrix.shape == (2, 2)

    def test_size_mismatch_error(self):
        """Test that mismatched network sizes raise an error."""
        net_a = multinet.multi_layer_network(directed=False)
        net_a.add_edges([
            {'source': 'A', 'target': 'B', 'source_type': 'L1', 'target_type': 'L1'},
        ])

        net_b = multinet.multi_layer_network(directed=False)
        net_b.add_edges([
            {'source': 'X', 'target': 'Y', 'source_type': 'L1', 'target_type': 'L1'},
            {'source': 'Y', 'target': 'Z', 'source_type': 'L1', 'target_type': 'L1'},
        ])

        with pytest.raises(ValueError, match="Network size mismatch"):
            align_networks(net_a, net_b)

    def test_layer_mapping(self):
        """Test that layer mapping is created correctly."""
        net_a = multinet.multi_layer_network(directed=False)
        net_a.add_edges([
            {'source': 'A', 'target': 'B', 'source_type': 'L1', 'target_type': 'L1'},
        ])

        net_b = multinet.multi_layer_network(directed=False)
        net_b.add_edges([
            {'source': 'X', 'target': 'Y', 'source_type': 'L1', 'target_type': 'L1'},
        ])

        result = align_networks(net_a, net_b)

        assert result.layer_mapping is not None
        assert 'L1' in result.layer_mapping
        assert result.layer_mapping['L1'] == 'L1'

    def test_unsupported_method(self):
        """Test that unsupported methods raise an error."""
        net_a = multinet.multi_layer_network(directed=False)
        net_a.add_edges([
            {'source': 'A', 'target': 'B', 'source_type': 'L1', 'target_type': 'L1'},
        ])

        net_b = multinet.multi_layer_network(directed=False)
        net_b.add_edges([
            {'source': 'X', 'target': 'Y', 'source_type': 'L1', 'target_type': 'L1'},
        ])

        with pytest.raises(ValueError, match="Unsupported alignment method"):
            align_networks(net_a, net_b, method="unsupported")  # type: ignore


class TestEdgeAgreement:
    """Tests for edge_agreement function."""

    def test_perfect_agreement(self):
        """Test perfect edge agreement."""
        net_a = multinet.multi_layer_network(directed=False)
        net_a.add_edges([
            {'source': 'A', 'target': 'B', 'source_type': 'L1', 'target_type': 'L1'},
        ])

        net_b = multinet.multi_layer_network(directed=False)
        net_b.add_edges([
            {'source': 'X', 'target': 'Y', 'source_type': 'L1', 'target_type': 'L1'},
        ])

        mapping = {'A': 'X', 'B': 'Y'}
        ea = edge_agreement(net_a, net_b, mapping)

        assert ea == 1.0

    def test_no_agreement(self):
        """Test no edge agreement."""
        net_a = multinet.multi_layer_network(directed=False)
        net_a.add_edges([
            {'source': 'A', 'target': 'B', 'source_type': 'L1', 'target_type': 'L1'},
        ])

        net_b = multinet.multi_layer_network(directed=False)
        net_b.add_edges([
            {'source': 'X', 'target': 'Z', 'source_type': 'L1', 'target_type': 'L1'},
        ])
        # Add nodes Y to net_b to have same node count
        net_b.add_nodes([{'source': 'Y', 'type': 'L1'}])

        mapping = {'A': 'X', 'B': 'Y'}
        ea = edge_agreement(net_a, net_b, mapping)

        assert ea == 0.0

    def test_empty_network(self):
        """Test edge agreement with empty network."""
        net_a = multinet.multi_layer_network(directed=False)
        net_a.add_nodes([{'source': 'A', 'type': 'L1'}])

        net_b = multinet.multi_layer_network(directed=False)
        net_b.add_nodes([{'source': 'X', 'type': 'L1'}])

        mapping = {'A': 'X'}
        ea = edge_agreement(net_a, net_b, mapping)

        assert ea == 0.0


class TestDegreeCorrelation:
    """Tests for degree_correlation function."""

    def test_perfect_correlation(self):
        """Test perfect degree correlation."""
        net_a = multinet.multi_layer_network(directed=False)
        net_a.add_edges([
            {'source': 'A', 'target': 'B', 'source_type': 'L1', 'target_type': 'L1'},
            {'source': 'B', 'target': 'C', 'source_type': 'L1', 'target_type': 'L1'},
        ])

        net_b = multinet.multi_layer_network(directed=False)
        net_b.add_edges([
            {'source': 'X', 'target': 'Y', 'source_type': 'L1', 'target_type': 'L1'},
            {'source': 'Y', 'target': 'Z', 'source_type': 'L1', 'target_type': 'L1'},
        ])

        # A (deg=1) -> X (deg=1)
        # B (deg=2) -> Y (deg=2)
        # C (deg=1) -> Z (deg=1)
        mapping = {'A': 'X', 'B': 'Y', 'C': 'Z'}
        dc = degree_correlation(net_a, net_b, mapping)

        assert dc == 1.0

    def test_negative_correlation(self):
        """Test negative degree correlation."""
        net_a = multinet.multi_layer_network(directed=False)
        net_a.add_edges([
            {'source': 'A', 'target': 'B', 'source_type': 'L1', 'target_type': 'L1'},
            {'source': 'B', 'target': 'C', 'source_type': 'L1', 'target_type': 'L1'},
        ])

        net_b = multinet.multi_layer_network(directed=False)
        net_b.add_edges([
            {'source': 'X', 'target': 'Y', 'source_type': 'L1', 'target_type': 'L1'},
            {'source': 'Y', 'target': 'Z', 'source_type': 'L1', 'target_type': 'L1'},
        ])

        # A (deg=1) -> Y (deg=2) - wrong match
        # B (deg=2) -> X (deg=1) - wrong match
        # C (deg=1) -> Z (deg=1) - correct
        mapping = {'A': 'Y', 'B': 'X', 'C': 'Z'}
        dc = degree_correlation(net_a, net_b, mapping)

        # Should be negative or low correlation
        assert dc < 0.5

    def test_single_node_correlation(self):
        """Test correlation with single node returns 0."""
        net_a = multinet.multi_layer_network(directed=False)
        net_a.add_nodes([{'source': 'A', 'type': 'L1'}])

        net_b = multinet.multi_layer_network(directed=False)
        net_b.add_nodes([{'source': 'X', 'type': 'L1'}])

        mapping = {'A': 'X'}
        dc = degree_correlation(net_a, net_b, mapping)

        assert dc == 0.0


class TestIntegration:
    """Integration tests for the alignment workflow."""

    def test_full_alignment_workflow(self):
        """Test the complete alignment workflow."""
        # Create two similar networks with varying degrees
        net_a = multinet.multi_layer_network(directed=False)
        net_a.add_edges([
            {'source': 'A', 'target': 'B', 'source_type': 'L1', 'target_type': 'L1'},
            {'source': 'B', 'target': 'C', 'source_type': 'L1', 'target_type': 'L1'},
            {'source': 'B', 'target': 'D', 'source_type': 'L1', 'target_type': 'L1'},
        ])

        net_b = multinet.multi_layer_network(directed=False)
        net_b.add_edges([
            {'source': 'X', 'target': 'Y', 'source_type': 'L1', 'target_type': 'L1'},
            {'source': 'Y', 'target': 'Z', 'source_type': 'L1', 'target_type': 'L1'},
            {'source': 'Y', 'target': 'W', 'source_type': 'L1', 'target_type': 'L1'},
        ])

        # Align networks
        alignment = align_networks(net_a, net_b)

        # Compute metrics
        ea = edge_agreement(net_a, net_b, alignment.node_mapping)
        dc = degree_correlation(net_a, net_b, alignment.node_mapping)

        # Verify results are in valid ranges
        assert 0.0 <= alignment.score <= 1.0
        assert 0.0 <= ea <= 1.0
        assert -1.0 <= dc <= 1.0

        # The alignment should produce a valid mapping
        assert len(alignment.node_mapping) == 4
        assert alignment.layer_mapping is not None
        assert 'L1' in alignment.layer_mapping

    def test_perfect_isomorphic_alignment(self):
        """Test alignment of two networks with identical structure."""
        # Create two identical networks (different node names)
        net_a = multinet.multi_layer_network(directed=False)
        net_a.add_edges([
            {'source': 'A', 'target': 'B', 'source_type': 'L1', 'target_type': 'L1'},
        ])

        net_b = multinet.multi_layer_network(directed=False)
        net_b.add_edges([
            {'source': 'X', 'target': 'Y', 'source_type': 'L1', 'target_type': 'L1'},
        ])

        # Align networks
        alignment = align_networks(net_a, net_b)

        # For simple isomorphic networks, edge agreement should be perfect
        ea = edge_agreement(net_a, net_b, alignment.node_mapping)
        assert ea == 1.0
