"""Tests for partition UQ infrastructure.

Tests cover:
- NoiseModel implementations
- Partition distance metrics
- Partition reducers
- PartitionUQ class
"""

from __future__ import annotations

import numpy as np
import pytest

from py3plex.core import multinet
from py3plex.uncertainty.noise_models import (
    EdgeDrop,
    WeightNoise,
    LayerDrop,
    TemporalWindowBootstrap,
    noise_model_from_dict,
)
from py3plex.uncertainty.partition_metrics import (
    variation_of_information,
    normalized_mutual_information,
    adjusted_rand_index,
)
from py3plex.uncertainty.partition_reducers import (
    NodeEntropyReducer,
    CoAssignmentReducer,
    PartitionDistanceReducer,
    ConsensusReducer,
)
from py3plex.uncertainty.partition_uq import PartitionUQ


# ============================================================================
# Noise Model Tests
# ============================================================================

class TestNoiseModels:
    """Tests for noise model implementations."""
    
    def test_edge_drop_init_validation(self):
        """Test EdgeDrop parameter validation."""
        # Valid
        EdgeDrop(p=0.1)
        
        # Invalid: p out of range
        with pytest.raises(ValueError):
            EdgeDrop(p=0.0)
        with pytest.raises(ValueError):
            EdgeDrop(p=1.0)
        with pytest.raises(ValueError):
            EdgeDrop(p=1.5)
    
    def test_edge_drop_apply(self):
        """Test EdgeDrop application."""
        net = multinet.multi_layer_network(directed=False)
        net.add_edges([
            ['A', 'L1', 'B', 'L1', 1],
            ['B', 'L1', 'C', 'L1', 1],
            ['C', 'L1', 'D', 'L1', 1],
            ['D', 'L1', 'A', 'L1', 1],
        ], input_type='list')
        
        original_edges = net.core_network.number_of_edges()
        
        # Drop 50% of edges
        noise = EdgeDrop(p=0.5)
        perturbed = noise.apply(net, seed=42)
        
        # Check that edges were dropped
        perturbed_edges = perturbed.core_network.number_of_edges()
        assert perturbed_edges < original_edges
        
        # Check determinism
        perturbed2 = noise.apply(net, seed=42)
        assert perturbed2.core_network.number_of_edges() == perturbed_edges
    
    def test_edge_drop_serialization(self):
        """Test EdgeDrop serialization."""
        noise = EdgeDrop(p=0.2, preserve_connectivity=True)
        data = noise.to_dict()
        
        assert data["type"] == "EdgeDrop"
        assert data["p"] == 0.2
        assert data["preserve_connectivity"] is True
        
        # Test deserialization
        noise2 = noise_model_from_dict(data)
        assert isinstance(noise2, EdgeDrop)
        assert noise2.p == 0.2
    
    def test_weight_noise_init_validation(self):
        """Test WeightNoise parameter validation."""
        # Valid
        WeightNoise(dist="lognormal", sigma=0.2)
        WeightNoise(dist="uniform", sigma=0.1)
        WeightNoise(dist="normal", sigma=0.3)
        
        # Invalid distribution
        with pytest.raises(ValueError):
            WeightNoise(dist="unknown", sigma=0.1)
        
        # Invalid sigma
        with pytest.raises(ValueError):
            WeightNoise(dist="lognormal", sigma=0.0)
        with pytest.raises(ValueError):
            WeightNoise(dist="lognormal", sigma=-0.1)
    
    def test_weight_noise_apply(self):
        """Test WeightNoise application."""
        net = multinet.multi_layer_network(directed=False)
        net.add_edges([
            ['A', 'L1', 'B', 'L1', 1.0],
            ['B', 'L1', 'C', 'L1', 2.0],
        ], input_type='list')
        
        noise = WeightNoise(dist="lognormal", sigma=0.2)
        perturbed = noise.apply(net, seed=42)
        
        # Check that weights changed
        original_weights = []
        for u, v, data in net.core_network.edges(data=True):
            original_weights.append(data.get('weight', 1.0))
        
        perturbed_weights = []
        for u, v, data in perturbed.core_network.edges(data=True):
            perturbed_weights.append(data.get('weight', 1.0))
        
        # Weights should be different
        assert not np.allclose(original_weights, perturbed_weights)
        
        # Weights should be positive
        assert all(w > 0 for w in perturbed_weights)
    
    def test_layer_drop_init_validation(self):
        """Test LayerDrop parameter validation."""
        # Valid
        LayerDrop(p=0.2)
        LayerDrop(layers=["L1", "L2"])
        
        # Invalid: neither p nor layers
        with pytest.raises(ValueError):
            LayerDrop()
        
        # Invalid: both p and layers
        with pytest.raises(ValueError):
            LayerDrop(p=0.2, layers=["L1"])
        
        # Invalid: p out of range
        with pytest.raises(ValueError):
            LayerDrop(p=0.0)
        with pytest.raises(ValueError):
            LayerDrop(p=1.0)
    
    def test_layer_drop_apply_explicit(self):
        """Test LayerDrop with explicit layers."""
        net = multinet.multi_layer_network(directed=False)
        net.add_edges([
            ['A', 'L1', 'B', 'L1', 1],
            ['A', 'L2', 'B', 'L2', 1],
            ['A', 'L3', 'B', 'L3', 1],
        ], input_type='list')
        
        # Drop L2
        noise = LayerDrop(layers=["L2"])
        perturbed = noise.apply(net, seed=42)
        
        # Check that L2 edges were removed
        assert perturbed.core_network.has_edge(('A', 'L1'), ('B', 'L1'))
        assert not perturbed.core_network.has_edge(('A', 'L2'), ('B', 'L2'))
        assert perturbed.core_network.has_edge(('A', 'L3'), ('B', 'L3'))


# ============================================================================
# Partition Metrics Tests
# ============================================================================

class TestPartitionMetrics:
    """Tests for partition distance metrics."""
    
    def test_vi_identical_partitions(self):
        """Test VI=0 for identical partitions."""
        p1 = np.array([0, 0, 1, 1])
        p2 = np.array([0, 0, 1, 1])
        
        vi = variation_of_information(p1, p2)
        assert abs(vi) < 1e-10
    
    def test_vi_label_invariance(self):
        """Test VI is invariant to label permutation."""
        p1 = np.array([0, 0, 1, 1])
        p2 = np.array([5, 5, 7, 7])  # Same structure, different labels
        
        vi = variation_of_information(p1, p2)
        assert abs(vi) < 1e-10
    
    def test_vi_symmetry(self):
        """Test VI is symmetric."""
        p1 = np.array([0, 0, 1, 1])
        p2 = np.array([0, 0, 0, 1])
        
        vi1 = variation_of_information(p1, p2)
        vi2 = variation_of_information(p2, p1)
        
        assert abs(vi1 - vi2) < 1e-10
    
    def test_vi_different_partitions(self):
        """Test VI > 0 for different partitions."""
        p1 = np.array([0, 0, 1, 1])
        p2 = np.array([0, 1, 0, 1])
        
        vi = variation_of_information(p1, p2)
        assert vi > 0
    
    def test_nmi_range(self):
        """Test NMI is in [0, 1]."""
        p1 = np.array([0, 0, 1, 1])
        p2 = np.array([0, 1, 0, 1])
        
        nmi = normalized_mutual_information(p1, p2)
        assert 0 <= nmi <= 1
    
    def test_nmi_identical_partitions(self):
        """Test NMI=1 for identical partitions."""
        p1 = np.array([0, 0, 1, 1])
        p2 = np.array([0, 0, 1, 1])
        
        nmi = normalized_mutual_information(p1, p2)
        assert abs(nmi - 1.0) < 1e-10
    
    def test_nmi_symmetry(self):
        """Test NMI is symmetric."""
        p1 = np.array([0, 0, 1, 1])
        p2 = np.array([0, 0, 0, 1])
        
        nmi1 = normalized_mutual_information(p1, p2)
        nmi2 = normalized_mutual_information(p2, p1)
        
        assert abs(nmi1 - nmi2) < 1e-10


# ============================================================================
# Partition Reducer Tests
# ============================================================================

class TestPartitionReducers:
    """Tests for partition reducers."""
    
    def test_node_entropy_reducer_deterministic(self):
        """Test entropy=0 for deterministic partitions."""
        reducer = NodeEntropyReducer(n_nodes=4)
        
        # All samples identical
        reducer.update(np.array([0, 0, 1, 1]))
        reducer.update(np.array([0, 0, 1, 1]))
        reducer.update(np.array([0, 0, 1, 1]))
        
        entropy = reducer.finalize()
        
        # All nodes have zero entropy
        assert np.allclose(entropy, 0.0)
    
    def test_node_entropy_reducer_variable(self):
        """Test entropy > 0 for variable partitions."""
        reducer = NodeEntropyReducer(n_nodes=4)
        
        # Different samples
        reducer.update(np.array([0, 0, 1, 1]))
        reducer.update(np.array([0, 0, 0, 1]))
        reducer.update(np.array([0, 1, 0, 1]))
        
        entropy = reducer.finalize()
        
        # Some nodes have non-zero entropy
        assert np.any(entropy > 0)
    
    def test_consensus_reducer(self):
        """Test consensus partition (mode)."""
        reducer = ConsensusReducer(n_nodes=4)
        
        # Majority votes
        reducer.update(np.array([0, 0, 1, 1]))
        reducer.update(np.array([0, 0, 1, 1]))
        reducer.update(np.array([0, 1, 1, 1]))
        
        consensus = reducer.finalize()
        
        # Node 0 should be 0 (3/3 votes)
        # Node 1 should be 0 (2/3 votes)
        # Nodes 2,3 should be 1 (3/3 votes)
        assert consensus[0] == 0
        assert consensus[1] == 0
        assert consensus[2] == 1
        assert consensus[3] == 1
    
    def test_coassignment_reducer_dense(self):
        """Test co-assignment matrix (dense mode)."""
        reducer = CoAssignmentReducer(n_nodes=4, sparse=False)
        
        # Two samples
        reducer.update(np.array([0, 0, 1, 1]))
        reducer.update(np.array([0, 0, 0, 1]))
        
        coassoc = reducer.finalize()
        
        # Check shape
        assert coassoc.shape == (4, 4)
        
        # Diagonal should be 1
        assert np.allclose(np.diag(coassoc), 1.0)
        
        # Nodes 0 and 1 always together
        assert coassoc[0, 1] == 1.0
        assert coassoc[1, 0] == 1.0
        
        # Node 2 sometimes with node 1 (1 out of 2 samples)
        assert coassoc[1, 2] == 0.5
    
    def test_partition_distance_reducer(self):
        """Test partition distance accumulation."""
        reducer = PartitionDistanceReducer(metric="vi", store_samples=True)
        
        # Three samples
        reducer.update(np.array([0, 0, 1, 1]))
        reducer.update(np.array([0, 0, 0, 1]))
        reducer.update(np.array([0, 1, 0, 1]))
        
        stats = reducer.finalize()
        
        # Check that statistics are computed
        assert "vi_mean" in stats
        assert "vi_std" in stats
        assert "vi_min" in stats
        assert "vi_max" in stats
        
        # Mean should be >= min
        assert stats["vi_mean"] >= stats["vi_min"]
        # Max should be >= mean
        assert stats["vi_max"] >= stats["vi_mean"]


# ============================================================================
# PartitionUQ Tests
# ============================================================================

class TestPartitionUQ:
    """Tests for PartitionUQ class."""
    
    def test_from_samples_basic(self):
        """Test basic PartitionUQ creation from samples."""
        partitions = [
            np.array([0, 0, 1, 1]),
            np.array([0, 0, 0, 1]),
            np.array([0, 1, 0, 1]),
        ]
        node_ids = ['A', 'B', 'C', 'D']
        
        uq = PartitionUQ.from_samples(
            partitions=partitions,
            node_ids=node_ids,
            store="sketch"
        )
        
        # Check basic properties
        assert uq.n_nodes == 4
        assert uq.n_samples == 3
        assert len(uq.consensus_partition) == 4
        assert len(uq.membership_entropy) == 4
        assert len(uq.p_max_membership) == 4
    
    def test_from_samples_deterministic(self):
        """Test PartitionUQ with identical samples."""
        partitions = [
            np.array([0, 0, 1, 1]),
            np.array([0, 0, 1, 1]),
            np.array([0, 0, 1, 1]),
        ]
        node_ids = ['A', 'B', 'C', 'D']
        
        uq = PartitionUQ.from_samples(
            partitions=partitions,
            node_ids=node_ids,
            store="none"
        )
        
        # All nodes should have zero entropy
        assert np.allclose(uq.membership_entropy, 0.0)
        
        # All nodes should have confidence=1
        assert np.allclose(uq.p_max_membership, 1.0)
        
        # VI should be zero (all partitions identical)
        assert uq.vi_mean < 1e-10
        assert uq.vi_std < 1e-10
    
    def test_from_samples_with_weights(self):
        """Test PartitionUQ with weighted samples."""
        partitions = [
            np.array([0, 0, 1, 1]),
            np.array([0, 1, 0, 1]),
        ]
        node_ids = ['A', 'B', 'C', 'D']
        weights = np.array([0.9, 0.1])  # First partition dominates
        
        uq = PartitionUQ.from_samples(
            partitions=partitions,
            node_ids=node_ids,
            weights=weights,
            store="none"
        )
        
        # Consensus should match first partition (higher weight)
        # Node 0 should be 0, node 1 should be 0
        assert uq.consensus_partition[0] == 0
        assert uq.consensus_partition[1] == 0
    
    def test_boundary_nodes(self):
        """Test boundary node identification."""
        partitions = [
            np.array([0, 0, 1, 1]),
            np.array([0, 0, 0, 1]),
            np.array([0, 1, 0, 1]),
        ]
        node_ids = ['A', 'B', 'C', 'D']
        
        uq = PartitionUQ.from_samples(
            partitions=partitions,
            node_ids=node_ids,
            store="none"
        )
        
        # Get boundary nodes (high entropy)
        boundary = uq.boundary_nodes(threshold=0.0, metric="entropy")
        
        # At least some nodes should have non-zero entropy
        assert len(boundary) > 0
    
    def test_stability_summary(self):
        """Test stability summary."""
        partitions = [
            np.array([0, 0, 1, 1]),
            np.array([0, 0, 0, 1]),
        ]
        node_ids = ['A', 'B', 'C', 'D']
        
        uq = PartitionUQ.from_samples(
            partitions=partitions,
            node_ids=node_ids,
            store="none"
        )
        
        summary = uq.stability_summary()
        
        # Check required keys
        assert "vi_mean" in summary
        assert "vi_std" in summary
        assert "nmi_mean" in summary
        assert "nmi_std" in summary
        assert "n_samples" in summary
        assert "n_communities" in summary
        assert "mean_entropy" in summary
        assert "mean_confidence" in summary
    
    def test_storage_modes(self):
        """Test different storage modes."""
        partitions = [
            np.array([0, 0, 1, 1]),
            np.array([0, 0, 0, 1]),
        ]
        node_ids = ['A', 'B', 'C', 'D']
        
        # None mode
        uq_none = PartitionUQ.from_samples(
            partitions=partitions,
            node_ids=node_ids,
            store="none"
        )
        assert uq_none.coassoc_matrix is None
        assert uq_none.samples is None
        
        # Sketch mode
        uq_sketch = PartitionUQ.from_samples(
            partitions=partitions,
            node_ids=node_ids,
            store="sketch"
        )
        assert uq_sketch.coassoc_matrix is not None
        assert uq_sketch.samples is None
        
        # Samples mode
        uq_samples = PartitionUQ.from_samples(
            partitions=partitions,
            node_ids=node_ids,
            store="samples"
        )
        assert uq_samples.coassoc_matrix is not None
        assert uq_samples.samples is not None
        assert len(uq_samples.samples) == 2
    
    def test_serialization(self):
        """Test PartitionUQ serialization."""
        partitions = [
            np.array([0, 0, 1, 1]),
            np.array([0, 0, 0, 1]),
        ]
        node_ids = ['A', 'B', 'C', 'D']
        
        uq = PartitionUQ.from_samples(
            partitions=partitions,
            node_ids=node_ids,
            store="none"
        )
        
        # Serialize
        data = uq.to_dict()
        
        # Check required keys
        assert "node_ids" in data
        assert "n_samples" in data
        assert "consensus_partition" in data
        assert "membership_entropy" in data
        assert "p_max_membership" in data
        assert "vi_mean" in data
        assert "nmi_mean" in data


# ============================================================================
# Property-Based Tests
# ============================================================================

@pytest.mark.property
class TestPartitionUQProperties:
    """Property-based tests for PartitionUQ."""
    
    def test_entropy_bounds(self):
        """Test that entropy is non-negative."""
        partitions = [
            np.array([0, 0, 1, 1]),
            np.array([0, 0, 0, 1]),
            np.array([0, 1, 0, 1]),
        ]
        node_ids = ['A', 'B', 'C', 'D']
        
        uq = PartitionUQ.from_samples(
            partitions=partitions,
            node_ids=node_ids,
            store="none"
        )
        
        # Entropy must be non-negative
        assert np.all(uq.membership_entropy >= 0)
    
    def test_confidence_bounds(self):
        """Test that confidence is in [0, 1]."""
        partitions = [
            np.array([0, 0, 1, 1]),
            np.array([0, 0, 0, 1]),
        ]
        node_ids = ['A', 'B', 'C', 'D']
        
        uq = PartitionUQ.from_samples(
            partitions=partitions,
            node_ids=node_ids,
            store="none"
        )
        
        # Confidence must be in [0, 1]
        assert np.all(uq.p_max_membership >= 0)
        assert np.all(uq.p_max_membership <= 1)
    
    def test_consensus_in_samples(self):
        """Test that consensus labels come from samples."""
        partitions = [
            np.array([0, 0, 1, 1]),
            np.array([0, 0, 0, 1]),
        ]
        node_ids = ['A', 'B', 'C', 'D']
        
        uq = PartitionUQ.from_samples(
            partitions=partitions,
            node_ids=node_ids,
            store="samples"
        )
        
        # Each consensus label should be most frequent in samples
        for i in range(uq.n_nodes):
            consensus_label = uq.consensus_partition[i]
            
            # Count frequency of this label in samples
            label_counts = {}
            for partition in uq.samples:
                label = partition[i]
                label_counts[label] = label_counts.get(label, 0) + 1
            
            # Consensus should be the most frequent label
            most_frequent = max(label_counts, key=label_counts.get)
            assert consensus_label == most_frequent
