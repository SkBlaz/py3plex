"""Tests for multilayer-specific community quality metrics.

Tests cover:
- Determinism (repeated calls yield identical results)
- Correctness (known partitions yield expected metric values)
- Edge cases (single-layer nodes, single community, fragmentation)
- Hard-to-game behavior (giant cluster vs reasonable partition)
- Performance (no quadratic blowups)
- Integration with AutoCommunity
"""

import pytest
import numpy as np
from collections import defaultdict

from py3plex.core import multinet
from py3plex.algorithms.community_detection.multilayer_quality_metrics import (
    replica_consistency,
    layer_entropy,
    iter_layered_assignments,
)


class TestPartitionAdapter:
    """Test iter_layered_assignments adapter."""
    
    def test_adapter_tuple_format(self):
        """Test adapter with (node_id, layer) format."""
        partition = {
            ('A', 'social'): 0,
            ('A', 'work'): 0,
            ('B', 'social'): 1,
            ('B', 'work'): 1,
        }
        
        net = multinet.multi_layer_network(directed=False)
        
        assignments = list(iter_layered_assignments(partition, net))
        
        assert len(assignments) == 4
        assert ('A', 'social', 0) in assignments
        assert ('A', 'work', 0) in assignments
        assert ('B', 'social', 1) in assignments
        assert ('B', 'work', 1) in assignments


class TestReplicaConsistency:
    """Test replica consistency metric."""
    
    def test_determinism(self):
        """Metric should be deterministic (repeated calls yield same result)."""
        partition = {
            ('A', 'layer1'): 0,
            ('A', 'layer2'): 0,
            ('A', 'layer3'): 0,
            ('B', 'layer1'): 1,
            ('B', 'layer2'): 1,
            ('C', 'layer1'): 2,
        }
        
        net = multinet.multi_layer_network(directed=False)
        
        # Compute multiple times
        rc1 = replica_consistency(partition, net)
        rc2 = replica_consistency(partition, net)
        rc3 = replica_consistency(partition, net)
        
        assert rc1 == rc2 == rc3
        assert isinstance(rc1, float)
    
    def test_perfect_consistency(self):
        """All replicas aligned → RC = 1.0."""
        partition = {
            ('A', 'layer1'): 0,
            ('A', 'layer2'): 0,
            ('A', 'layer3'): 0,
            ('B', 'layer1'): 1,
            ('B', 'layer2'): 1,
            ('B', 'layer3'): 1,
            ('C', 'layer1'): 2,
            ('C', 'layer2'): 2,
        }
        
        net = multinet.multi_layer_network(directed=False)
        
        rc = replica_consistency(partition, net)
        
        assert rc == pytest.approx(1.0, abs=1e-6)
    
    def test_no_consistency(self):
        """Each replica different community → RC = 0.0."""
        partition = {
            ('A', 'layer1'): 0,
            ('A', 'layer2'): 1,
            ('A', 'layer3'): 2,
            ('B', 'layer1'): 3,
            ('B', 'layer2'): 4,
            ('B', 'layer3'): 5,
        }
        
        net = multinet.multi_layer_network(directed=False)
        
        rc = replica_consistency(partition, net)
        
        assert rc == pytest.approx(0.0, abs=1e-6)
    
    def test_partial_consistency(self):
        """Mixed alignment → RC in (0, 1)."""
        # Node A: 2 layers with label 0, 1 layer with label 1
        # Agreement pairs = 2*(2-1)/2 = 1
        # Total pairs = 3*(3-1)/2 = 3
        # RC(A) = 1/3
        partition = {
            ('A', 'layer1'): 0,
            ('A', 'layer2'): 0,
            ('A', 'layer3'): 1,
        }
        
        net = multinet.multi_layer_network(directed=False)
        
        rc = replica_consistency(partition, net)
        
        expected = 1.0 / 3.0
        assert rc == pytest.approx(expected, abs=1e-6)
    
    def test_single_layer_nodes_ignored(self):
        """Nodes in single layer should be skipped."""
        partition = {
            ('A', 'layer1'): 0,  # Single layer → skip
            ('B', 'layer1'): 1,
            ('B', 'layer2'): 1,  # Two layers → include
        }
        
        net = multinet.multi_layer_network(directed=False)
        
        rc = replica_consistency(partition, net)
        
        # Only B is considered (perfect consistency)
        assert rc == pytest.approx(1.0, abs=1e-6)
    
    def test_no_eligible_nodes_warning(self):
        """No nodes with replicas in ≥2 layers → warning and RC=0.0."""
        partition = {
            ('A', 'layer1'): 0,
            ('B', 'layer2'): 1,
            ('C', 'layer3'): 2,
        }
        
        net = multinet.multi_layer_network(directed=False)
        
        with pytest.warns(UserWarning, match="No nodes with replicas"):
            rc = replica_consistency(partition, net)
        
        assert rc == 0.0
    
    def test_label_permutation_invariance(self):
        """Metric should be invariant to label permutations."""
        # Same structure, different labels
        partition1 = {
            ('A', 'layer1'): 0,
            ('A', 'layer2'): 0,
            ('B', 'layer1'): 1,
            ('B', 'layer2'): 1,
        }
        
        partition2 = {
            ('A', 'layer1'): 42,
            ('A', 'layer2'): 42,
            ('B', 'layer1'): 99,
            ('B', 'layer2'): 99,
        }
        
        net = multinet.multi_layer_network(directed=False)
        
        rc1 = replica_consistency(partition1, net)
        rc2 = replica_consistency(partition2, net)
        
        assert rc1 == rc2 == pytest.approx(1.0, abs=1e-6)
    
    def test_efficient_count_formula(self):
        """Test that efficient count-based formula is used."""
        # Large partition to test efficiency
        partition = {}
        
        # 100 nodes, each in 10 layers
        for node_id in range(100):
            for layer_idx in range(10):
                # Half nodes: all same community
                # Half nodes: all different communities
                if node_id < 50:
                    comm = 0  # Same community
                else:
                    comm = layer_idx  # Different communities
                
                partition[(f'node_{node_id}', f'layer_{layer_idx}')] = comm
        
        net = multinet.multi_layer_network(directed=False)
        
        # Should complete quickly (< 1 second)
        import time
        start = time.time()
        rc = replica_consistency(partition, net)
        elapsed = time.time() - start
        
        assert elapsed < 1.0
        assert 0.0 <= rc <= 1.0


class TestLayerEntropy:
    """Test layer entropy metric."""
    
    def test_determinism(self):
        """Metric should be deterministic."""
        partition = {
            ('A', 'layer1'): 0,
            ('B', 'layer1'): 1,
            ('C', 'layer2'): 0,
            ('D', 'layer2'): 1,
        }
        
        net = multinet.multi_layer_network(directed=False)
        
        h1 = layer_entropy(partition, net)
        h2 = layer_entropy(partition, net)
        h3 = layer_entropy(partition, net)
        
        assert h1 == h2 == h3
        assert isinstance(h1, float)
    
    def test_single_community_per_layer(self):
        """Single community per layer → H = 0.0 (clipped to 0.1)."""
        partition = {
            ('A', 'layer1'): 0,
            ('B', 'layer1'): 0,
            ('C', 'layer1'): 0,
            ('D', 'layer2'): 0,
            ('E', 'layer2'): 0,
        }
        
        net = multinet.multi_layer_network(directed=False)
        
        h = layer_entropy(partition, net)
        
        # Default clipping: [0.1, 0.9]
        assert h == pytest.approx(0.1, abs=1e-6)
    
    def test_balanced_communities(self):
        """Two equal communities per layer → H ≈ 1.0."""
        partition = {
            ('A', 'layer1'): 0,
            ('B', 'layer1'): 1,
            ('C', 'layer2'): 0,
            ('D', 'layer2'): 1,
        }
        
        net = multinet.multi_layer_network(directed=False)
        
        h = layer_entropy(partition, net)
        
        # Perfect balance → H = 1.0 (may be clipped to 0.9)
        assert h == pytest.approx(0.9, abs=1e-6)
    
    def test_skewed_communities(self):
        """Skewed community sizes → H < 1.0."""
        partition = {
            ('A', 'layer1'): 0,
            ('B', 'layer1'): 0,
            ('C', 'layer1'): 0,
            ('D', 'layer1'): 1,  # 3:1 ratio
        }
        
        net = multinet.multi_layer_network(directed=False)
        
        h = layer_entropy(partition, net)
        
        # Skewed → H < 1.0 but > 0.0
        assert 0.1 < h < 0.9
    
    def test_clipping_applied(self):
        """Clipping should constrain values to [clip_min, clip_max]."""
        # Giant cluster (should clip to 0.1)
        partition_giant = {
            ('A', 'layer1'): 0,
            ('B', 'layer1'): 0,
            ('C', 'layer1'): 0,
        }
        
        net = multinet.multi_layer_network(directed=False)
        
        h_giant = layer_entropy(partition_giant, net)
        assert h_giant == pytest.approx(0.1, abs=1e-6)
        
        # Balanced (should clip to 0.9)
        partition_balanced = {
            ('A', 'layer1'): 0,
            ('B', 'layer1'): 1,
            ('C', 'layer2'): 0,
            ('D', 'layer2'): 1,
        }
        
        h_balanced = layer_entropy(partition_balanced, net)
        assert h_balanced == pytest.approx(0.9, abs=1e-6)
    
    def test_custom_clipping(self):
        """Custom clipping bounds should be respected."""
        partition = {
            ('A', 'layer1'): 0,
            ('B', 'layer1'): 0,
        }
        
        net = multinet.multi_layer_network(directed=False)
        
        # Custom clip: [0.2, 0.8]
        h = layer_entropy(partition, net, clip=(0.2, 0.8))
        
        assert h == pytest.approx(0.2, abs=1e-6)
    
    def test_multiple_layers_aggregation(self):
        """Entropy should be averaged across layers."""
        # Layer 1: 2 equal communities (H=1.0)
        # Layer 2: 1 community (H=0.0)
        # Mean: 0.5 → clipped
        partition = {
            ('A', 'layer1'): 0,
            ('B', 'layer1'): 1,
            ('C', 'layer2'): 0,
            ('D', 'layer2'): 0,
        }
        
        net = multinet.multi_layer_network(directed=False)
        
        h = layer_entropy(partition, net)
        
        # Mean of 1.0 (clipped to 0.9) and 0.0 (clipped to 0.1) = 0.5
        # But clipping happens after mean, so:
        # Mean of (1.0, 0.0) = 0.5 → clipped to [0.1, 0.9] = 0.5
        assert 0.1 <= h <= 0.9
    
    def test_empty_layer_warning(self):
        """Empty layer should trigger warning and be skipped."""
        partition = {}  # Empty
        
        net = multinet.multi_layer_network(directed=False)
        
        with pytest.warns(UserWarning, match="No valid layers"):
            h = layer_entropy(partition, net)
        
        assert h == 0.0


class TestGuardrailBehavior:
    """Test that metrics act as guardrails (hard-to-game)."""
    
    def test_giant_cluster_vs_reasonable(self):
        """Giant cluster should score worse than reasonable partition."""
        net = multinet.multi_layer_network(directed=False)
        
        # Giant cluster (degenerate)
        partition_giant = {
            ('A', 'layer1'): 0,
            ('B', 'layer1'): 0,
            ('C', 'layer1'): 0,
            ('D', 'layer1'): 0,
            ('A', 'layer2'): 0,
            ('B', 'layer2'): 0,
            ('C', 'layer2'): 0,
            ('D', 'layer2'): 0,
        }
        
        # Reasonable partition (2 balanced communities)
        partition_reasonable = {
            ('A', 'layer1'): 0,
            ('B', 'layer1'): 0,
            ('C', 'layer1'): 1,
            ('D', 'layer1'): 1,
            ('A', 'layer2'): 0,
            ('B', 'layer2'): 0,
            ('C', 'layer2'): 1,
            ('D', 'layer2'): 1,
        }
        
        h_giant = layer_entropy(partition_giant, net)
        h_reasonable = layer_entropy(partition_reasonable, net)
        
        # Reasonable should have higher entropy
        assert h_reasonable > h_giant
    
    def test_per_layer_noise_vs_coherent(self):
        """Per-layer noise should score worse on RC than coherent partition."""
        net = multinet.multi_layer_network(directed=False)
        
        # Coherent partition (replicas aligned)
        partition_coherent = {
            ('A', 'layer1'): 0,
            ('A', 'layer2'): 0,
            ('A', 'layer3'): 0,
            ('B', 'layer1'): 1,
            ('B', 'layer2'): 1,
            ('B', 'layer3'): 1,
        }
        
        # Noisy partition (replicas not aligned)
        partition_noisy = {
            ('A', 'layer1'): 0,
            ('A', 'layer2'): 1,
            ('A', 'layer3'): 2,
            ('B', 'layer1'): 3,
            ('B', 'layer2'): 4,
            ('B', 'layer3'): 5,
        }
        
        rc_coherent = replica_consistency(partition_coherent, net)
        rc_noisy = replica_consistency(partition_noisy, net)
        
        # Coherent should have higher RC
        assert rc_coherent > rc_noisy
        assert rc_coherent == pytest.approx(1.0, abs=1e-6)
        assert rc_noisy == pytest.approx(0.0, abs=1e-6)
    
    def test_metrics_independent(self):
        """RC and layer_entropy should be independent."""
        net = multinet.multi_layer_network(directed=False)
        
        # High RC, low entropy (giant cluster, coherent)
        partition1 = {
            ('A', 'layer1'): 0,
            ('A', 'layer2'): 0,
            ('B', 'layer1'): 0,
            ('B', 'layer2'): 0,
        }
        
        rc1 = replica_consistency(partition1, net)
        h1 = layer_entropy(partition1, net)
        
        assert rc1 == pytest.approx(1.0, abs=1e-6)
        assert h1 == pytest.approx(0.1, abs=1e-6)  # Clipped
        
        # High RC, high entropy (balanced, coherent)
        partition2 = {
            ('A', 'layer1'): 0,
            ('A', 'layer2'): 0,
            ('B', 'layer1'): 1,
            ('B', 'layer2'): 1,
        }
        
        rc2 = replica_consistency(partition2, net)
        h2 = layer_entropy(partition2, net)
        
        assert rc2 == pytest.approx(1.0, abs=1e-6)
        assert h2 == pytest.approx(0.9, abs=1e-6)  # Clipped


class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_single_node(self):
        """Single node should handle gracefully."""
        partition = {('A', 'layer1'): 0}
        net = multinet.multi_layer_network(directed=False)
        
        # RC: no nodes with ≥2 layers
        with pytest.warns(UserWarning):
            rc = replica_consistency(partition, net)
        assert rc == 0.0
        
        # Layer entropy: single community
        h = layer_entropy(partition, net)
        assert h == pytest.approx(0.1, abs=1e-6)  # Clipped
    
    def test_fragmentation(self):
        """Extreme fragmentation (each node own community)."""
        partition = {
            ('A', 'layer1'): 0,
            ('B', 'layer1'): 1,
            ('C', 'layer1'): 2,
            ('D', 'layer1'): 3,
        }
        
        net = multinet.multi_layer_network(directed=False)
        
        # Layer entropy should be high (many communities)
        h = layer_entropy(partition, net)
        assert h > 0.5


class TestPerformance:
    """Test performance characteristics."""
    
    def test_no_quadratic_blowup_rc(self):
        """RC should not have quadratic blowup beyond expected."""
        # Create large partition
        partition = {}
        
        # 500 nodes, each in 5 layers
        for node_id in range(500):
            for layer_idx in range(5):
                partition[(f'node_{node_id}', f'layer_{layer_idx}')] = node_id % 10
        
        net = multinet.multi_layer_network(directed=False)
        
        import time
        start = time.time()
        rc = replica_consistency(partition, net)
        elapsed = time.time() - start
        
        # Should complete in reasonable time (< 1 second)
        assert elapsed < 1.0
        assert 0.0 <= rc <= 1.0
    
    def test_no_quadratic_blowup_entropy(self):
        """Layer entropy should be O(|assignments|)."""
        # Create large partition
        partition = {}
        
        # 1000 nodes across 10 layers
        for node_id in range(1000):
            for layer_idx in range(10):
                partition[(f'node_{node_id}', f'layer_{layer_idx}')] = node_id % 20
        
        net = multinet.multi_layer_network(directed=False)
        
        import time
        start = time.time()
        h = layer_entropy(partition, net)
        elapsed = time.time() - start
        
        # Should complete in reasonable time (< 1 second)
        assert elapsed < 1.0
        assert 0.0 <= h <= 1.0


class TestIntegrationWithAutoCommunity:
    """Test integration with AutoCommunity."""
    
    def test_metrics_in_registry(self):
        """Metrics should be registered in metric registry."""
        from py3plex.selection.metric_registry import get_metric_registry
        
        registry = get_metric_registry()
        
        assert "replica_consistency" in registry.metrics
        assert "layer_entropy" in registry.metrics
        
        rc_spec = registry.metrics["replica_consistency"]
        assert rc_spec.direction == "max"
        assert rc_spec.bucket == "structure"
        
        le_spec = registry.metrics["layer_entropy"]
        assert le_spec.direction == "max"
        assert le_spec.bucket == "sanity"
    
    def test_metrics_callable_from_registry(self):
        """Metrics should be callable from registry."""
        from py3plex.selection.metric_registry import get_metric_registry
        
        registry = get_metric_registry()
        
        partition = {
            ('A', 'layer1'): 0,
            ('A', 'layer2'): 0,
            ('B', 'layer1'): 1,
            ('B', 'layer2'): 1,
        }
        
        net = multinet.multi_layer_network(directed=False)
        context = {}
        
        # Call via registry
        rc = registry.metrics["replica_consistency"].callable(partition, net, context)
        h = registry.metrics["layer_entropy"].callable(partition, net, context)
        
        assert 0.0 <= rc <= 1.0
        assert 0.0 <= h <= 1.0
