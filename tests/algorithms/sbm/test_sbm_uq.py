"""
Tests for SBM uncertainty quantification (UQ).
"""

import numpy as np
import pytest

from py3plex.core import multinet
from py3plex.algorithms.sbm.uq import (
    align_labels_hungarian,
    compute_node_stability,
    sbm_seed_resampling_uq,
    compute_co_assignment_matrix
)
from py3plex.algorithms.sbm.conversions import extract_layer_adjacencies


def create_test_network(n_nodes=30, K=2, n_layers=1, seed=42):
    """Create a simple test network."""
    rng = np.random.default_rng(seed)
    
    net = multinet.multi_layer_network(directed=False)
    
    nodes = [f"N{i}" for i in range(n_nodes)]
    block_assignments = rng.choice(K, size=n_nodes)
    
    for layer_idx in range(n_layers):
        layer = f"L{layer_idx}"
        
        for node in nodes:
            net.add_node(node, layer=layer)
        
        for i in range(n_nodes):
            for j in range(i + 1, n_nodes):
                if block_assignments[i] == block_assignments[j]:
                    p = 0.5
                else:
                    p = 0.05
                
                if rng.random() < p:
                    net.add_edge(nodes[i], nodes[j], layer_src=layer, layer_dst=layer)
    
    return net, block_assignments


def test_align_labels_basic():
    """Test basic label alignment."""
    # Create two partitions with swapped labels
    p1 = np.array([0, 0, 0, 1, 1, 1])
    p2 = np.array([1, 1, 1, 0, 0, 0])  # Labels swapped
    
    aligned, costs = align_labels_hungarian([p1, p2])
    
    # After alignment, partitions should match
    assert len(aligned) == 2
    np.testing.assert_array_equal(aligned[0], aligned[1])
    
    # Cost should be 0 (perfect alignment)
    assert costs[1] == 0.0


def test_align_labels_partial():
    """Test label alignment with partial disagreement."""
    p1 = np.array([0, 0, 0, 1, 1, 1])
    p2 = np.array([1, 1, 0, 0, 0, 1])  # Some disagreement
    
    aligned, costs = align_labels_hungarian([p1, p2])
    
    # Cost should be number of misaligned nodes
    assert costs[1] >= 0
    assert costs[1] <= len(p1)


def test_align_labels_identity():
    """Test alignment when partitions already match."""
    p1 = np.array([0, 0, 1, 1, 2, 2])
    p2 = np.array([0, 0, 1, 1, 2, 2])
    
    aligned, costs = align_labels_hungarian([p1, p2])
    
    # Partitions should remain unchanged
    np.testing.assert_array_equal(aligned[0], p1)
    np.testing.assert_array_equal(aligned[1], p2)
    
    # Cost should be 0
    assert costs[1] == 0.0


def test_compute_node_stability_entropy():
    """Test node stability computation using entropy."""
    # Node 0 is stable (always in community 0)
    # Node 1 varies between communities
    p1 = np.array([0, 0])
    p2 = np.array([0, 1])
    p3 = np.array([0, 2])
    
    stability = compute_node_stability([p1, p2, p3], method="entropy")
    
    # Node 0 should be more stable (lower entropy)
    assert stability[0] < stability[1]


def test_compute_node_stability_variance():
    """Test node stability computation using variance."""
    p1 = np.array([0, 0, 0])
    p2 = np.array([0, 1, 1])
    p3 = np.array([0, 2, 2])
    
    stability = compute_node_stability([p1, p2, p3], method="variance")
    
    # Node 0 should be stable (variance = 0)
    assert stability[0] == 0.0
    
    # Other nodes should have positive variance
    assert stability[1] > 0
    assert stability[2] > 0


def test_sbm_seed_resampling_basic():
    """Test basic seed resampling UQ."""
    net, _ = create_test_network(n_nodes=25, K=2, n_layers=1, seed=42)
    
    # Extract adjacency matrices
    A_layers, layers, node_to_idx = extract_layer_adjacencies(
        net, layers=None, directed=False
    )
    
    # Run UQ with small number of samples
    uq_result = sbm_seed_resampling_uq(
        A_layers=A_layers,
        K=2,
        layers=layers,
        node_to_idx=node_to_idx,
        n_samples=5,
        master_seed=42,
        model="dc_sbm",
        verbose=False,
        max_iter=30
    )
    
    # Check result structure
    assert 'models' in uq_result
    assert 'aligned_partitions' in uq_result
    assert 'node_stability' in uq_result
    assert 'consensus_partition' in uq_result
    assert 'consensus_confidence' in uq_result
    
    # Check dimensions
    assert len(uq_result['models']) == 5
    assert len(uq_result['aligned_partitions']) == 5
    assert len(uq_result['node_stability']) == 25
    assert len(uq_result['consensus_partition']) == 25
    assert len(uq_result['consensus_confidence']) == 25


def test_sbm_seed_resampling_deterministic():
    """Test that seed resampling is deterministic."""
    net, _ = create_test_network(n_nodes=20, K=2, n_layers=1, seed=43)
    
    A_layers, layers, node_to_idx = extract_layer_adjacencies(
        net, layers=None, directed=False
    )
    
    # Run UQ twice with same master seed
    uq1 = sbm_seed_resampling_uq(
        A_layers=A_layers, K=2, layers=layers, node_to_idx=node_to_idx,
        n_samples=3, master_seed=100, model="dc_sbm", verbose=False, max_iter=20
    )
    
    uq2 = sbm_seed_resampling_uq(
        A_layers=A_layers, K=2, layers=layers, node_to_idx=node_to_idx,
        n_samples=3, master_seed=100, model="dc_sbm", verbose=False, max_iter=20
    )
    
    # Results should be identical
    np.testing.assert_array_equal(uq1['consensus_partition'], uq2['consensus_partition'])
    np.testing.assert_allclose(uq1['node_stability'], uq2['node_stability'], rtol=1e-10)


def test_sbm_seed_resampling_confidence():
    """Test that consensus confidence is in [0, 1]."""
    net, _ = create_test_network(n_nodes=20, K=2, n_layers=1, seed=44)
    
    A_layers, layers, node_to_idx = extract_layer_adjacencies(
        net, layers=None, directed=False
    )
    
    uq_result = sbm_seed_resampling_uq(
        A_layers=A_layers, K=2, layers=layers, node_to_idx=node_to_idx,
        n_samples=5, master_seed=44, model="dc_sbm", verbose=False, max_iter=20
    )
    
    confidence = uq_result['consensus_confidence']
    
    # Confidence should be in [0, 1]
    assert np.all(confidence >= 0)
    assert np.all(confidence <= 1)
    
    # At least one node should have high confidence
    assert np.max(confidence) > 0.5


def test_sbm_seed_resampling_multilayer():
    """Test seed resampling with multilayer networks."""
    net, _ = create_test_network(n_nodes=20, K=2, n_layers=2, seed=45)
    
    A_layers, layers, node_to_idx = extract_layer_adjacencies(
        net, layers=None, directed=False
    )
    
    uq_result = sbm_seed_resampling_uq(
        A_layers=A_layers, K=2, layers=layers, node_to_idx=node_to_idx,
        n_samples=3, master_seed=45, model="dc_sbm", 
        layer_mode="shared_blocks", verbose=False, max_iter=20
    )
    
    # Check that it works with multiple layers
    assert len(uq_result['models']) == 3
    assert len(uq_result['consensus_partition']) == 20


def test_compute_co_assignment_matrix():
    """Test co-assignment matrix computation."""
    # Create simple partitions
    p1 = np.array([0, 0, 1, 1])
    p2 = np.array([0, 0, 1, 1])
    p3 = np.array([0, 1, 0, 1])  # Different structure
    
    co_assignment = compute_co_assignment_matrix([p1, p2, p3])
    
    # Check shape
    assert co_assignment.shape == (4, 4)
    
    # Check diagonal (always 1.0)
    np.testing.assert_allclose(np.diag(co_assignment), 1.0)
    
    # Check symmetry
    np.testing.assert_allclose(co_assignment, co_assignment.T)
    
    # Nodes 0 and 1 are together in 2 out of 3 partitions
    assert co_assignment[0, 1] == pytest.approx(2.0 / 3.0)


def test_alignment_with_different_K():
    """Test label alignment when partitions have different number of communities."""
    # p1 has 2 communities, p2 has 3
    p1 = np.array([0, 0, 1, 1, 1])
    p2 = np.array([0, 0, 1, 1, 2])  # One node in new community
    
    aligned, costs = align_labels_hungarian([p1, p2])
    
    # Should still align as best as possible
    assert len(aligned) == 2
    assert costs[1] >= 0  # Some cost due to mismatch


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
