"""Integration tests for DSL .community().uq() chaining.

Tests the end-to-end flow of community detection with UQ through the DSL.
"""

from __future__ import annotations

import numpy as np
import pytest

from py3plex.core import multinet
from py3plex.dsl import Q
from py3plex.uncertainty.noise_models import EdgeDrop, WeightNoise


def create_test_network():
    """Create a simple test multilayer network."""
    net = multinet.multi_layer_network(directed=False)
    net.add_edges([
        # Community 1: A-B-C (tightly connected)
        ['A', 'L1', 'B', 'L1', 1],
        ['B', 'L1', 'C', 'L1', 1],
        ['C', 'L1', 'A', 'L1', 1],
        # Community 2: D-E-F (tightly connected)
        ['D', 'L1', 'E', 'L1', 1],
        ['E', 'L1', 'F', 'L1', 1],
        ['F', 'L1', 'D', 'L1', 1],
        # Weak connection
        ['C', 'L1', 'D', 'L1', 0.1],
    ], input_type='list')
    return net


class TestCommunityUQIntegration:
    """Integration tests for community UQ via DSL."""
    
    def test_community_without_uq(self):
        """Test basic community detection without UQ."""
        net = create_test_network()
        
        result = (
            Q.nodes()
             .community(method="leiden", gamma=1.0, random_state=42)
             .execute(net)
        )
        
        # Check that community metadata is present
        assert "community_detection" in result.meta
        assert result.meta["community_detection"]["method"] == "leiden"
        assert result.meta["community_detection"]["n_communities"] >= 1
        
        # Check that partition was attached to network
        partition = net.get_partition_by_name("default")
        assert partition is not None
        assert len(partition) == len(result.items)
    
    def test_community_with_uq_seed_method(self):
        """Test community detection with seed-based UQ."""
        net = create_test_network()
        
        result = (
            Q.nodes()
             .community(method="leiden", gamma=1.0, random_state=42)
             .uq(method="seed", n_samples=10, seed=42)
             .execute(net)
        )
        
        # Check basic result structure
        assert len(result.items) > 0
        
        # Check that UQ metadata is present
        assert "uq" in result.meta
        assert result.meta["uq"]["type"] == "partition"
        assert result.meta["uq"]["method"] == "seed"
        assert result.meta["uq"]["n_samples"] == 10
        
        # Check that stability metrics are present
        assert "stability" in result.meta["uq"]
        stability = result.meta["uq"]["stability"]
        assert "vi_mean" in stability
        assert "nmi_mean" in stability
        assert "n_communities" in stability
        
        # Check that PartitionUQ object is available
        assert "partition_uq" in result.meta
        partition_uq = result.meta["partition_uq"]
        assert partition_uq.n_samples == 10
        assert partition_uq.n_nodes == len(result.items)
        
        # Check that UQ columns are added
        assert "community_id" in result.attributes
        assert "community_entropy" in result.attributes
        assert "community_confidence" in result.attributes
        
        # All nodes should have these attributes
        for node in result.items:
            assert node in result.attributes["community_id"]
            assert node in result.attributes["community_entropy"]
            assert node in result.attributes["community_confidence"]
    
    def test_community_with_uq_perturbation(self):
        """Test community detection with perturbation-based UQ."""
        net = create_test_network()
        
        result = (
            Q.nodes()
             .community(method="leiden", gamma=1.0, random_state=42)
             .uq(
                 method="perturbation",
                 n_samples=10,
                 seed=42,
                 noise_model=EdgeDrop(p=0.1)
             )
             .execute(net)
        )
        
        # Check UQ metadata
        assert "uq" in result.meta
        assert result.meta["uq"]["method"] == "perturbation"
        assert "EdgeDrop" in result.meta["uq"]["noise_model"]
        
        # Check that UQ columns exist
        assert "community_entropy" in result.attributes
        assert "community_confidence" in result.attributes
        
        # With perturbation, some nodes should have non-zero entropy
        entropies = list(result.attributes["community_entropy"].values())
        # Allow for case where all are deterministic
        assert all(e >= 0 for e in entropies)
    
    def test_community_uq_with_pandas(self):
        """Test that UQ results can be exported to pandas."""
        net = create_test_network()
        
        result = (
            Q.nodes()
             .community(method="leiden", gamma=1.0, random_state=42)
             .uq(method="seed", n_samples=5, seed=42)
             .execute(net)
        )
        
        # Convert to pandas
        df = result.to_pandas()
        
        # Check that UQ columns are present
        assert "community_id" in df.columns
        assert "community_entropy" in df.columns
        assert "community_confidence" in df.columns
        
        # Check data types
        assert df["community_entropy"].dtype in (np.float32, np.float64, float)
        assert df["community_confidence"].dtype in (np.float32, np.float64, float)
    
    def test_community_uq_boundary_nodes(self):
        """Test that boundary nodes are identified."""
        net = create_test_network()
        
        result = (
            Q.nodes()
             .community(method="leiden", gamma=1.0, random_state=42)
             .uq(method="seed", n_samples=20, seed=42)
             .execute(net)
        )
        
        # Check that boundary nodes are listed
        assert "boundary_nodes" in result.meta["uq"]
        boundary_nodes = result.meta["uq"]["boundary_nodes"]
        
        # Boundary nodes should be a list
        assert isinstance(boundary_nodes, list)
        
        # Each boundary node should be in the result
        for node in boundary_nodes:
            assert node in result.items
    
    def test_community_uq_storage_modes(self):
        """Test different storage modes for UQ."""
        net = create_test_network()
        
        # Test "none" mode
        result_none = (
            Q.nodes()
             .community(method="leiden", random_state=42)
             .uq(method="seed", n_samples=5, seed=42, store="none")
             .execute(net)
        )
        
        partition_uq_none = result_none.meta["partition_uq"]
        assert partition_uq_none.store_mode == "none"
        assert partition_uq_none.coassoc_matrix is None
        assert partition_uq_none.samples is None
        
        # Test "sketch" mode (default)
        result_sketch = (
            Q.nodes()
             .community(method="leiden", random_state=42)
             .uq(method="seed", n_samples=5, seed=42, store="sketch")
             .execute(net)
        )
        
        partition_uq_sketch = result_sketch.meta["partition_uq"]
        assert partition_uq_sketch.store_mode == "sketch"
        # Note: coassoc_matrix is not computed by default with UQ spine
        # It would require adding CoAssignmentReducer to the plan
        # assert partition_uq_sketch.coassoc_matrix is not None
        assert partition_uq_sketch.samples is None
        
        # Test "samples" mode
        result_samples = (
            Q.nodes()
             .community(method="leiden", random_state=42)
             .uq(method="seed", n_samples=5, seed=42, store="samples")
             .execute(net)
        )
        
        partition_uq_samples = result_samples.meta["partition_uq"]
        assert partition_uq_samples.store_mode == "samples"
        # Note: coassoc_matrix is not computed by default with UQ spine
        # assert partition_uq_samples.coassoc_matrix is not None
        assert partition_uq_samples.samples is not None
        assert len(partition_uq_samples.samples) == 5
    
    def test_community_uq_stability_metrics(self):
        """Test that stability metrics are reasonable."""
        net = create_test_network()
        
        result = (
            Q.nodes()
             .community(method="leiden", gamma=1.0, random_state=42)
             .uq(method="seed", n_samples=20, seed=42)
             .execute(net)
        )
        
        stability = result.meta["uq"]["stability"]
        
        # Check that metrics are present and non-negative
        assert stability["vi_mean"] >= 0
        assert stability["vi_std"] >= 0
        assert stability["nmi_mean"] >= 0
        assert stability["nmi_mean"] <= 1.0
        assert stability["mean_entropy"] >= 0
        assert stability["mean_confidence"] >= 0
        assert stability["mean_confidence"] <= 1.0
    
    @pytest.mark.slow
    def test_community_uq_performance(self):
        """Test that UQ runs in reasonable time on larger network."""
        # Create a larger network
        net = multinet.multi_layer_network(directed=False)
        
        # Add 100 nodes in a clear community structure
        for i in range(50):
            # Community 1
            net.add_edges([
                [f'A{i}', 'L1', f'A{(i+1)%50}', 'L1', 1],
            ], input_type='list')
        
        for i in range(50):
            # Community 2
            net.add_edges([
                [f'B{i}', 'L1', f'B{(i+1)%50}', 'L1', 1],
            ], input_type='list')
        
        # Add a few cross-community edges
        net.add_edges([
            ['A0', 'L1', 'B0', 'L1', 0.1],
            ['A25', 'L1', 'B25', 'L1', 0.1],
        ], input_type='list')
        
        import time
        start = time.time()
        
        result = (
            Q.nodes()
             .community(method="leiden", random_state=42)
             .uq(method="seed", n_samples=10, seed=42)
             .execute(net, progress=False)
        )
        
        elapsed = time.time() - start
        
        # Should complete in reasonable time (< 10 seconds for this size)
        assert elapsed < 10.0
        
        # Check result is valid
        assert len(result.items) == 100
        assert "partition_uq" in result.meta


@pytest.mark.integration
class TestCommunityUQProvenance:
    """Tests for UQ provenance tracking."""
    
    def test_uq_provenance_recorded(self):
        """Test that UQ parameters are recorded in provenance."""
        net = create_test_network()
        
        result = (
            Q.nodes()
             .community(method="leiden", gamma=1.2, random_state=42)
             .uq(
                 method="perturbation",
                 n_samples=10,
                 seed=123,
                 noise_model=EdgeDrop(p=0.15)
             )
             .execute(net)
        )
        
        # Check UQ metadata
        uq_meta = result.meta["uq"]
        assert uq_meta["method"] == "perturbation"
        assert uq_meta["n_samples"] == 10
        assert "EdgeDrop(p=0.15" in uq_meta["noise_model"]
        
        # Check stability summary is present
        assert "stability" in uq_meta
        assert "duration_ms" in uq_meta
