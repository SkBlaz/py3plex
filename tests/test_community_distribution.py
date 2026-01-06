"""Tests for distributional community detection and uncertainty quantification."""

from __future__ import annotations

import numpy as np
import pytest

from py3plex.core import multinet
from py3plex.algorithms.community_detection import multilayer_louvain_distribution
from py3plex.uncertainty import (
    CommunityDistribution,
    partition_dict_to_array,
    partition_array_to_dict,
    perturb_network_edges,
    bootstrap_network_edges,
)
from py3plex.exceptions import AlgorithmError


def create_simple_multilayer_network():
    """Create a simple test multilayer network."""
    net = multinet.multi_layer_network(directed=False)
    net.add_edges([
        ['A', 'L1', 'B', 'L1', 1],
        ['B', 'L1', 'C', 'L1', 1],
        ['C', 'L1', 'D', 'L1', 1],
        ['D', 'L1', 'A', 'L1', 1],
        ['A', 'L2', 'B', 'L2', 1],
        ['C', 'L2', 'D', 'L2', 1],
    ], input_type='list')
    return net


def create_community_network():
    """Create a network with clear community structure."""
    net = multinet.multi_layer_network(directed=False)
    # Community 1: A-B-C (tightly connected)
    net.add_edges([
        ['A', 'L1', 'B', 'L1', 1],
        ['B', 'L1', 'C', 'L1', 1],
        ['C', 'L1', 'A', 'L1', 1],
    ], input_type='list')
    # Community 2: D-E-F (tightly connected)
    net.add_edges([
        ['D', 'L1', 'E', 'L1', 1],
        ['E', 'L1', 'F', 'L1', 1],
        ['F', 'L1', 'D', 'L1', 1],
    ], input_type='list')
    # Weak connection between communities
    net.add_edges([
        ['C', 'L1', 'D', 'L1', 0.1],
    ], input_type='list')
    return net


class TestCommunityDistribution:
    """Tests for CommunityDistribution class."""
    
    def test_initialization(self):
        """Test basic initialization."""
        partitions = [
            np.array([0, 0, 1]),
            np.array([0, 0, 1]),
            np.array([0, 1, 1]),
        ]
        nodes = ['A', 'B', 'C']
        
        dist = CommunityDistribution(
            partitions=partitions,
            nodes=nodes,
            meta={'method': 'test'}
        )
        
        assert dist.n_nodes == 3
        assert dist.n_partitions == 3
        assert dist.nodes == nodes
        assert len(dist.partitions) == 3
    
    def test_empty_partitions_error(self):
        """Test that empty partition list raises error."""
        with pytest.raises(AlgorithmError):
            CommunityDistribution(partitions=[], nodes=['A', 'B'])
    
    def test_partition_length_mismatch_error(self):
        """Test that mismatched partition lengths raise error."""
        partitions = [
            np.array([0, 0]),  # Length 2
            np.array([0, 0, 1]),  # Length 3 - mismatch!
        ]
        
        with pytest.raises(AlgorithmError):
            CommunityDistribution(partitions=partitions, nodes=['A', 'B'])
    
    def test_uniform_weights(self):
        """Test that uniform weights are created when weights=None."""
        partitions = [np.array([0, 0]), np.array([0, 1])]
        dist = CommunityDistribution(partitions=partitions, nodes=['A', 'B'])
        
        weights = dist.weights
        assert len(weights) == 2
        assert np.allclose(weights, [0.5, 0.5])
    
    def test_custom_weights(self):
        """Test custom weights are normalized."""
        partitions = [np.array([0, 0]), np.array([0, 1])]
        weights = np.array([2.0, 3.0])
        
        dist = CommunityDistribution(
            partitions=partitions,
            nodes=['A', 'B'],
            weights=weights
        )
        
        # Should be normalized to sum to 1
        assert np.allclose(dist.weights.sum(), 1.0)
        assert np.allclose(dist.weights, [0.4, 0.6])
    
    def test_coassociation_dense(self):
        """Test dense co-association matrix computation."""
        partitions = [
            np.array([0, 0, 1]),  # A,B together
            np.array([0, 0, 1]),  # A,B together
            np.array([0, 1, 1]),  # B,C together
        ]
        
        dist = CommunityDistribution(
            partitions=partitions,
            nodes=['A', 'B', 'C']
        )
        
        coassoc = dist.coassociation(mode='dense')
        
        # Check shape
        assert coassoc.shape == (3, 3)
        
        # Check diagonal (always 1)
        assert np.allclose(np.diag(coassoc), 1.0)
        
        # Check symmetry
        assert np.allclose(coassoc, coassoc.T)
        
        # Check specific values
        # A-B are together in 2/3 partitions
        assert np.isclose(coassoc[0, 1], 2/3, atol=0.01)
        # B-C are together in 1/3 partitions
        assert np.isclose(coassoc[1, 2], 1/3, atol=0.01)
    
    def test_coassociation_sparse(self):
        """Test sparse co-association representation."""
        partitions = [
            np.array([0, 0, 1, 1]),
            np.array([0, 0, 1, 1]),
        ]
        
        dist = CommunityDistribution(
            partitions=partitions,
            nodes=['A', 'B', 'C', 'D']
        )
        
        coassoc_sparse = dist.coassociation(mode='sparse', topk=2)
        
        # Check structure
        assert isinstance(coassoc_sparse, dict)
        assert len(coassoc_sparse) == 4  # One entry per node
        
        # Check that each node has at most topk neighbors
        for node_idx, neighbors in coassoc_sparse.items():
            assert len(neighbors) <= 2
            # Each neighbor is (idx, prob) tuple
            for neighbor_idx, prob in neighbors:
                assert 0 <= prob <= 1
    
    def test_coassociation_auto_mode(self):
        """Test that auto mode selects appropriately."""
        # Small network -> dense
        partitions = [np.array([0, 0, 1]) for _ in range(5)]
        dist_small = CommunityDistribution(
            partitions=partitions,
            nodes=['A', 'B', 'C']
        )
        
        coassoc_small = dist_small.coassociation(mode='auto')
        assert isinstance(coassoc_small, np.ndarray)  # Dense for small n
    
    def test_consensus_partition_medoid(self):
        """Test consensus partition using medoid method."""
        partitions = [
            np.array([0, 0, 1]),
            np.array([0, 0, 1]),
            np.array([0, 1, 1]),  # Different
        ]
        
        dist = CommunityDistribution(
            partitions=partitions,
            nodes=['A', 'B', 'C']
        )
        
        consensus = dist.consensus_partition(method='medoid')
        
        # Should return array of same length
        assert len(consensus) == 3
        assert consensus.dtype == np.int32
        
        # Should be one of the input partitions (medoid)
        found = False
        for p in partitions:
            if np.array_equal(consensus, p):
                found = True
                break
        assert found
    
    def test_node_confidence(self):
        """Test per-node confidence computation."""
        partitions = [
            np.array([0, 0, 1]),
            np.array([0, 0, 1]),
            np.array([0, 0, 1]),  # Node 0,1 always together -> high confidence
        ]
        
        dist = CommunityDistribution(
            partitions=partitions,
            nodes=['A', 'B', 'C']
        )
        
        confidence = dist.node_confidence()
        
        # Check shape and range
        assert len(confidence) == 3
        assert np.all((confidence >= 0) & (confidence <= 1))
        
        # Nodes 0 and 1 should have high confidence (always together)
        assert confidence[0] > 0.9
        assert confidence[1] > 0.9
    
    def test_node_entropy(self):
        """Test per-node entropy computation."""
        partitions = [
            np.array([0, 0, 1]),
            np.array([0, 1, 1]),
            np.array([1, 0, 1]),
        ]
        
        dist = CommunityDistribution(
            partitions=partitions,
            nodes=['A', 'B', 'C']
        )
        
        entropy = dist.node_entropy()
        
        # Check shape
        assert len(entropy) == 3
        # Entropy should be non-negative
        assert np.all(entropy >= 0)
    
    def test_node_margin(self):
        """Test per-node margin computation."""
        partitions = [
            np.array([0, 0, 1]),
            np.array([0, 0, 1]),
        ]
        
        dist = CommunityDistribution(
            partitions=partitions,
            nodes=['A', 'B', 'C']
        )
        
        margin = dist.node_margin()
        
        # Check shape and range
        assert len(margin) == 3
        assert np.all((margin >= 0) & (margin <= 1))
    
    def test_label_alignment(self):
        """Test label alignment using Hungarian matching."""
        # Create partitions with permuted labels
        partitions = [
            np.array([0, 0, 1]),
            np.array([1, 1, 0]),  # Same structure, different labels
        ]
        
        dist = CommunityDistribution(
            partitions=partitions,
            nodes=['A', 'B', 'C']
        )
        
        # Align labels
        dist.align_labels(reference='first')
        
        # Should now have membership probs
        probs = dist.node_membership_probs()
        assert probs.shape[0] == 3  # n_nodes
        
        # Probabilities should sum to 1 per node
        for i in range(3):
            assert np.isclose(probs[i].sum(), 1.0)
    
    def test_membership_probs_without_alignment_error(self):
        """Test that membership probs without alignment raises error."""
        partitions = [np.array([0, 0, 1])]
        dist = CommunityDistribution(partitions=partitions, nodes=['A', 'B', 'C'])
        
        with pytest.raises(AlgorithmError):
            dist.node_membership_probs()
    
    def test_to_dict(self):
        """Test node info export to dict."""
        partitions = [np.array([0, 0, 1])]
        dist = CommunityDistribution(partitions=partitions, nodes=['A', 'B', 'C'])
        
        info = dist.to_dict('A')
        
        assert 'consensus' in info
        assert 'confidence' in info
        assert 'entropy' in info
        assert 'margin' in info
        assert isinstance(info['consensus'], int)


class TestPartitionConversion:
    """Tests for partition format conversion utilities."""
    
    def test_dict_to_array(self):
        """Test conversion from dict to array."""
        partition_dict = {
            ('A', 'L1'): 0,
            ('B', 'L1'): 0,
            ('C', 'L1'): 1,
        }
        nodes = [('A', 'L1'), ('B', 'L1'), ('C', 'L1')]
        
        arr = partition_dict_to_array(partition_dict, nodes)
        
        assert isinstance(arr, np.ndarray)
        assert len(arr) == 3
        assert arr.dtype == np.int32
        assert np.array_equal(arr, [0, 0, 1])
    
    def test_array_to_dict(self):
        """Test conversion from array to dict."""
        arr = np.array([0, 0, 1])
        nodes = [('A', 'L1'), ('B', 'L1'), ('C', 'L1')]
        
        d = partition_array_to_dict(arr, nodes)
        
        assert isinstance(d, dict)
        assert len(d) == 3
        assert d[('A', 'L1')] == 0
        assert d[('B', 'L1')] == 0
        assert d[('C', 'L1')] == 1
    
    def test_roundtrip(self):
        """Test that dict->array->dict preserves data."""
        original = {
            'A': 0,
            'B': 1,
            'C': 0,
        }
        nodes = ['A', 'B', 'C']
        
        arr = partition_dict_to_array(original, nodes)
        recovered = partition_array_to_dict(arr, nodes)
        
        assert recovered == original


class TestGraphResampling:
    """Tests for graph resampling utilities."""
    
    def test_perturb_edges_immutability(self):
        """Test that perturbation doesn't mutate original network."""
        net = create_simple_multilayer_network()
        original_edges = list(net.get_edges())
        
        perturbed = perturb_network_edges(net, edge_drop_p=0.3, seed=42)
        
        # Original should be unchanged
        assert list(net.get_edges()) == original_edges
        # Perturbed should be different object
        assert perturbed is not net
    
    def test_perturb_edges_drop_rate(self):
        """Test that edge drop rate is approximately correct."""
        net = create_simple_multilayer_network()
        n_edges_original = len(list(net.get_edges()))
        
        # Drop 50% of edges
        perturbed = perturb_network_edges(net, edge_drop_p=0.5, seed=42)
        n_edges_perturbed = len(list(perturbed.get_edges()))
        
        # Should have approximately 50% of edges (allow some variance)
        expected = n_edges_original * 0.5
        assert abs(n_edges_perturbed - expected) <= n_edges_original * 0.3
    
    def test_perturb_edges_deterministic(self):
        """Test that same seed produces same perturbation."""
        net = create_simple_multilayer_network()
        
        perturbed1 = perturb_network_edges(net, edge_drop_p=0.3, seed=42)
        perturbed2 = perturb_network_edges(net, edge_drop_p=0.3, seed=42)
        
        edges1 = sorted(list(perturbed1.get_edges()))
        edges2 = sorted(list(perturbed2.get_edges()))
        
        assert edges1 == edges2
    
    def test_perturb_edges_invalid_prob_error(self):
        """Test that invalid edge_drop_p raises error."""
        net = create_simple_multilayer_network()
        
        with pytest.raises(AlgorithmError):
            perturb_network_edges(net, edge_drop_p=-0.1, seed=42)
        
        with pytest.raises(AlgorithmError):
            perturb_network_edges(net, edge_drop_p=1.5, seed=42)
    
    def test_perturb_edges_zero_drop(self):
        """Test that edge_drop_p=0 preserves all edges."""
        net = create_simple_multilayer_network()
        n_edges = len(list(net.get_edges()))
        
        perturbed = perturb_network_edges(net, edge_drop_p=0.0, seed=42)
        
        assert len(list(perturbed.get_edges())) == n_edges
    
    def test_bootstrap_edges_immutability(self):
        """Test that bootstrap doesn't mutate original."""
        net = create_simple_multilayer_network()
        original_edges = list(net.get_edges())
        
        boot = bootstrap_network_edges(net, seed=42)
        
        assert list(net.get_edges()) == original_edges
        assert boot is not net
    
    def test_bootstrap_edges_deterministic(self):
        """Test that bootstrap is deterministic with same seed."""
        net = create_simple_multilayer_network()
        
        boot1 = bootstrap_network_edges(net, seed=42)
        boot2 = bootstrap_network_edges(net, seed=42)
        
        edges1 = sorted(list(boot1.get_edges()))
        edges2 = sorted(list(boot2.get_edges()))
        
        assert edges1 == edges2
    
    def test_bootstrap_preserves_node_set(self):
        """Test that bootstrap preserves all nodes."""
        net = create_simple_multilayer_network()
        original_nodes = set(net.get_nodes())
        
        boot = bootstrap_network_edges(net, seed=42)
        boot_nodes = set(boot.get_nodes())
        
        assert boot_nodes == original_nodes


class TestDistributionalLouvain:
    """Tests for multilayer_louvain_distribution."""
    
    def test_basic_execution(self):
        """Test that distributional Louvain runs successfully."""
        net = create_community_network()
        
        dist = multilayer_louvain_distribution(
            net,
            n_runs=10,
            resampling='seed',
            seed=42,
            n_jobs=1
        )
        
        assert isinstance(dist, CommunityDistribution)
        assert dist.n_partitions == 10
    
    def test_determinism_serial(self):
        """Test determinism with n_jobs=1."""
        net = create_community_network()
        
        dist1 = multilayer_louvain_distribution(
            net, n_runs=20, resampling='seed', seed=42, n_jobs=1
        )
        dist2 = multilayer_louvain_distribution(
            net, n_runs=20, resampling='seed', seed=42, n_jobs=1
        )
        
        # Consensus should be identical
        consensus1 = dist1.consensus_partition()
        consensus2 = dist2.consensus_partition()
        
        assert np.array_equal(consensus1, consensus2)
        
        # Co-association should be identical
        coassoc1 = dist1.coassociation(mode='dense')
        coassoc2 = dist2.coassociation(mode='dense')
        
        assert np.allclose(coassoc1, coassoc2)
    
    def test_determinism_parallel(self):
        """Test determinism with n_jobs>1."""
        net = create_community_network()
        
        dist1 = multilayer_louvain_distribution(
            net, n_runs=20, resampling='seed', seed=42, n_jobs=2
        )
        dist2 = multilayer_louvain_distribution(
            net, n_runs=20, resampling='seed', seed=42, n_jobs=2
        )
        
        consensus1 = dist1.consensus_partition()
        consensus2 = dist2.consensus_partition()
        
        assert np.array_equal(consensus1, consensus2)
    
    def test_perturbation_resampling(self):
        """Test perturbation resampling."""
        net = create_community_network()
        
        dist = multilayer_louvain_distribution(
            net,
            n_runs=10,
            resampling='perturbation',
            perturbation_params={'edge_drop_p': 0.1},
            seed=42,
            n_jobs=1
        )
        
        assert isinstance(dist, CommunityDistribution)
        assert dist.meta['resampling'] == 'perturbation'
    
    def test_bootstrap_resampling(self):
        """Test bootstrap resampling."""
        net = create_community_network()
        
        dist = multilayer_louvain_distribution(
            net,
            n_runs=10,
            resampling='bootstrap',
            seed=42,
            n_jobs=1
        )
        
        assert isinstance(dist, CommunityDistribution)
        assert dist.meta['resampling'] == 'bootstrap'
    
    def test_weight_by_modularity(self):
        """Test modularity weighting."""
        net = create_community_network()
        
        dist = multilayer_louvain_distribution(
            net,
            n_runs=10,
            seed=42,
            weight_by='modularity',
            n_jobs=1
        )
        
        # Weights should not all be exactly equal (some variation expected)
        # However, for stable networks, they might be very similar
        weights = dist.weights
        # Check that at least weights are normalized (sum to 1)
        assert np.isclose(weights.sum(), 1.0)
        # Check that all weights are positive
        assert np.all(weights > 0)
    
    def test_invalid_resampling_error(self):
        """Test that invalid resampling raises error."""
        net = create_community_network()
        
        with pytest.raises(AlgorithmError):
            multilayer_louvain_distribution(
                net,
                resampling='invalid',
                seed=42
            )
    
    def test_invalid_n_runs_error(self):
        """Test that invalid n_runs raises error."""
        net = create_community_network()
        
        with pytest.raises(AlgorithmError):
            multilayer_louvain_distribution(
                net,
                n_runs=0,
                seed=42
            )
    
    def test_metadata(self):
        """Test that metadata is populated correctly."""
        net = create_community_network()
        
        dist = multilayer_louvain_distribution(
            net,
            n_runs=10,
            resampling='seed',
            gamma=1.5,
            seed=42,
            n_jobs=2
        )
        
        meta = dist.meta
        assert meta['method'] == 'multilayer_louvain'
        assert meta['n_runs'] == 10
        assert meta['resampling'] == 'seed'
        assert meta['gamma'] == 1.5
        assert meta['seed'] == 42
        assert meta['n_jobs'] == 2
        assert 'mean_modularity' in meta
        assert 'std_modularity' in meta
    
    def test_confidence_filtering(self):
        """Test filtering nodes by confidence."""
        net = create_community_network()
        
        dist = multilayer_louvain_distribution(
            net,
            n_runs=20,
            resampling='seed',
            seed=42
        )
        
        confidence = dist.node_confidence()
        
        # Find stable core (high confidence)
        stable_mask = confidence >= 0.8
        stable_nodes = [dist.nodes[i] for i in range(dist.n_nodes) if stable_mask[i]]
        
        # Should have at least some stable nodes
        assert len(stable_nodes) > 0


class TestLabelInvariance:
    """Tests for label permutation invariance of co-association."""
    
    def test_coassoc_label_invariant(self):
        """Test that co-association is invariant to label permutation."""
        # Create two identical partitions with different labels
        p1 = np.array([0, 0, 1, 1])
        p2 = np.array([3, 3, 7, 7])  # Same structure, different labels
        
        dist1 = CommunityDistribution(
            partitions=[p1, p1],
            nodes=['A', 'B', 'C', 'D']
        )
        
        dist2 = CommunityDistribution(
            partitions=[p2, p2],
            nodes=['A', 'B', 'C', 'D']
        )
        
        coassoc1 = dist1.coassociation(mode='dense')
        coassoc2 = dist2.coassociation(mode='dense')
        
        # Co-association should be identical (label-invariant)
        assert np.allclose(coassoc1, coassoc2)


class TestMemoryMode:
    """Tests for memory-efficient sparse mode."""
    
    def test_auto_mode_selection(self):
        """Test that auto mode selects sparse for large n."""
        # Create fake large distribution
        n_large = 3000
        partitions = [np.random.randint(0, 10, size=n_large) for _ in range(3)]
        nodes = list(range(n_large))
        
        dist = CommunityDistribution(partitions=partitions, nodes=nodes)
        
        # Auto should select sparse
        coassoc = dist.coassociation(mode='auto')
        
        # Should return sparse dict, not dense array
        assert isinstance(coassoc, dict)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
