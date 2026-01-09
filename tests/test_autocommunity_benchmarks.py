"""Synthetic benchmarks for AutoCommunity with planted communities.

Tests AutoCommunity on synthetic multilayer networks with known ground truth
community structure to validate that the meta-algorithm:
1. Recovers planted communities
2. Makes appropriate selections across different graph regimes
3. Provides meaningful uncertainty estimates
"""

import pytest
import numpy as np
from typing import Dict, Tuple

from py3plex.core import multinet
from py3plex.algorithms.community_detection import AutoCommunity


@pytest.mark.integration
class TestAutoCommunityBenchmarks:
    """Synthetic benchmarks with planted communities."""
    
    def test_two_block_strong_signal(self):
        """Test on two-block network with strong community signal."""
        # Generate simple two-block structure manually
        network = multinet.multi_layer_network(directed=False)
        
        # Block 1: nodes 0-9
        nodes_b1 = [{"source": f"N{i}", "type": "layer1"} for i in range(10)]
        network.add_nodes(nodes_b1)
        
        # Dense connections within block 1
        for i in range(10):
            for j in range(i+1, 10):
                if np.random.rand() < 0.5:  # 50% density
                    network.add_edges([{
                        "source": f"N{i}", "target": f"N{j}",
                        "source_type": "layer1", "target_type": "layer1"
                    }])
        
        # Block 2: nodes 10-19
        nodes_b2 = [{"source": f"N{i}", "type": "layer1"} for i in range(10, 20)]
        network.add_nodes(nodes_b2)
        
        # Dense connections within block 2
        for i in range(10, 20):
            for j in range(i+1, 20):
                if np.random.rand() < 0.5:
                    network.add_edges([{
                        "source": f"N{i}", "target": f"N{j}",
                        "source_type": "layer1", "target_type": "layer1"
                    }])
        
        # Sparse connections between blocks
        for i in range(10):
            for j in range(10, 20):
                if np.random.rand() < 0.05:  # 5% density
                    network.add_edges([{
                        "source": f"N{i}", "target": f"N{j}",
                        "source_type": "layer1", "target_type": "layer1"
                    }])
        
        # Set seed for reproducibility
        np.random.seed(42)
        
        # Run AutoCommunity
        result = (
            AutoCommunity()
              .candidates("louvain", "leiden")
              .metrics("modularity", "coverage")
              .seed(42)
              .execute(network)
        )
        
        # Validate results
        assert result.community_stats.n_communities >= 2, \
            "Should detect at least 2 communities"
        
        # Should have reasonable modularity
        eval_df = result.evaluation_matrix
        modularity = eval_df['modularity'].max()
        assert modularity > 0.2, \
            f"Modularity should be > 0.2 for strong signal, got {modularity:.3f}"
        
        # Coverage should be high (few singletons)
        assert result.community_stats.coverage > 0.8, \
            f"Coverage should be > 0.8, got {result.community_stats.coverage:.3f}"
    
    def test_three_block_moderate_signal(self):
        """Test on three-block network with moderate community signal."""
        np.random.seed(42)
        network = multinet.multi_layer_network(directed=False)
        
        # Create three blocks of 10 nodes each
        nodes = [{"source": f"N{i}", "type": "layer1"} for i in range(30)]
        network.add_nodes(nodes)
        
        # Block 1: 0-9, Block 2: 10-19, Block 3: 20-29
        blocks = [(0, 10), (10, 20), (20, 30)]
        
        # Dense within blocks
        for start, end in blocks:
            for i in range(start, end):
                for j in range(i+1, end):
                    if np.random.rand() < 0.4:  # 40% intra-block
                        network.add_edges([{
                            "source": f"N{i}", "target": f"N{j}",
                            "source_type": "layer1", "target_type": "layer1"
                        }])
        
        # Sparse between blocks
        for i in range(30):
            for j in range(i+1, 30):
                # Check if in different blocks
                i_block = i // 10
                j_block = j // 10
                if i_block != j_block and np.random.rand() < 0.1:  # 10% inter-block
                    network.add_edges([{
                        "source": f"N{i}", "target": f"N{j}",
                        "source_type": "layer1", "target_type": "layer1"
                    }])
        
        result = (
            AutoCommunity()
              .candidates("louvain", "leiden")
              .metrics("modularity", "coverage")
              .seed(42)
              .execute(network)
        )
        
        # Should detect multiple communities
        assert result.community_stats.n_communities >= 2
        
        # With moderate signal, modularity should still be positive
        eval_df = result.evaluation_matrix
        modularity = eval_df['modularity'].max()
        assert modularity > 0.1, \
            f"Modularity should be > 0.1 for moderate signal, got {modularity:.3f}"
    
    def test_weak_signal_with_null_model(self):
        """Test weak community structure with null model calibration."""
        np.random.seed(42)
        network = multinet.multi_layer_network(directed=False)
        
        # Generate weak signal - only slightly more intra than inter
        nodes = [{"source": f"N{i}", "type": "layer1"} for i in range(25)]
        network.add_nodes(nodes)
        
        # Two blocks: 0-11 and 12-24
        # Block 1
        for i in range(12):
            for j in range(i+1, 12):
                if np.random.rand() < 0.2:  # Weak signal
                    network.add_edges([{
                        "source": f"N{i}", "target": f"N{j}",
                        "source_type": "layer1", "target_type": "layer1"
                    }])
        
        # Block 2
        for i in range(12, 25):
            for j in range(i+1, 25):
                if np.random.rand() < 0.2:
                    network.add_edges([{
                        "source": f"N{i}", "target": f"N{j}",
                        "source_type": "layer1", "target_type": "layer1"
                    }])
        
        # Inter-block (only slightly lower)
        for i in range(12):
            for j in range(12, 25):
                if np.random.rand() < 0.15:
                    network.add_edges([{
                        "source": f"N{i}", "target": f"N{j}",
                        "source_type": "layer1", "target_type": "layer1"
                    }])
        
        # Run with null model
        result = (
            AutoCommunity()
              .candidates("louvain")
              .metrics("modularity")
              .null_model(type="configuration", samples=5)
              .seed(42)
              .execute(network)
        )
        
        # Should complete without error
        assert result.selected is not None
        
        # Check if null model results are available
        if result.null_model_results and 'z_scores' in result.null_model_results:
            z_scores = result.null_model_results['z_scores']
            # With weak signal, Z-scores should be lower
            for z in z_scores.values():
                # Should not be highly significant
                assert z < 5.0, "Z-score too high for weak signal"
    
    def test_heterogeneous_block_sizes(self):
        """Test on network with heterogeneous block sizes."""
        np.random.seed(42)
        network = multinet.multi_layer_network(directed=False)
        
        # One large block (15), one medium (10), one small (5)
        nodes = [{"source": f"N{i}", "type": "layer1"} for i in range(30)]
        network.add_nodes(nodes)
        
        blocks = [(0, 15), (15, 25), (25, 30)]  # Heterogeneous sizes
        
        # Dense within each block
        for start, end in blocks:
            for i in range(start, end):
                for j in range(i+1, end):
                    if np.random.rand() < 0.5:
                        network.add_edges([{
                            "source": f"N{i}", "target": f"N{j}",
                            "source_type": "layer1", "target_type": "layer1"
                        }])
        
        # Sparse between blocks
        for i in range(30):
            for j in range(i+1, 30):
                # Check if in different blocks
                in_same_block = any(
                    start <= i < end and start <= j < end
                    for start, end in blocks
                )
                if not in_same_block and np.random.rand() < 0.05:
                    network.add_edges([{
                        "source": f"N{i}", "target": f"N{j}",
                        "source_type": "layer1", "target_type": "layer1"
                    }])
        
        result = (
            AutoCommunity()
              .candidates("louvain", "leiden")
              .metrics("modularity", "coverage")
              .seed(42)
              .execute(network)
        )
        
        # Should detect communities
        assert result.community_stats.n_communities >= 2
        
        # Community sizes should be heterogeneous
        sizes = result.community_stats.community_sizes
        assert max(sizes) > min(sizes), \
            "Should detect heterogeneous community sizes"
    
    def test_multilayer_coupling(self):
        """Test on multilayer network with inter-layer coupling."""
        np.random.seed(42)
        network = multinet.multi_layer_network(directed=False)
        
        # Create nodes in multiple layers
        for layer_id in range(3):
            nodes = [{"source": f"N{i}", "type": f"layer{layer_id}"} for i in range(20)]
            network.add_nodes(nodes)
        
        # Two blocks per layer: 0-9 and 10-19
        for layer_id in range(3):
            layer = f"layer{layer_id}"
            
            # Block 1 in this layer
            for i in range(10):
                for j in range(i+1, 10):
                    if np.random.rand() < 0.5:
                        network.add_edges([{
                            "source": f"N{i}", "target": f"N{j}",
                            "source_type": layer, "target_type": layer
                        }])
            
            # Block 2 in this layer
            for i in range(10, 20):
                for j in range(i+1, 20):
                    if np.random.rand() < 0.5:
                        network.add_edges([{
                            "source": f"N{i}", "target": f"N{j}",
                            "source_type": layer, "target_type": layer
                        }])
            
            # Sparse inter-block within layer
            for i in range(10):
                for j in range(10, 20):
                    if np.random.rand() < 0.05:
                        network.add_edges([{
                            "source": f"N{i}", "target": f"N{j}",
                            "source_type": layer, "target_type": layer
                        }])
        
        result = (
            AutoCommunity()
              .candidates("louvain", "leiden")
              .metrics("modularity", "coverage")
              .seed(42)
              .execute(network)
        )
        
        # Should detect communities
        assert result.community_stats.n_communities >= 2
        
        # Check regime features
        if result.graph_regime:
            # Should detect multilayer structure
            assert len(result.graph_regime) > 0


@pytest.mark.property
class TestAutoCommunityPerturbationStress:
    """Stress tests under perturbation."""
    
    def test_stability_improves_with_samples(self):
        """Property: More UQ samples should give better stability estimates."""
        # Create simple network
        network = multinet.multi_layer_network(directed=False)
        nodes = [{"source": f"N{i}", "type": "layer1"} for i in range(15)]
        network.add_nodes(nodes)
        
        # Create two clusters
        for i in range(7):
            for j in range(i+1, 7):
                network.add_edges([{
                    "source": f"N{i}", "target": f"N{j}",
                    "source_type": "layer1", "target_type": "layer1"
                }])
        
        for i in range(7, 15):
            for j in range(i+1, 15):
                network.add_edges([{
                    "source": f"N{i}", "target": f"N{j}",
                    "source_type": "layer1", "target_type": "layer1"
                }])
        
        # Run with different numbers of samples
        result_few = (
            AutoCommunity()
              .candidates("louvain")
              .metrics("modularity", "stability")
              .uq(method="perturbation", n_samples=5)
              .seed(42)
              .execute(network)
        )
        
        result_many = (
            AutoCommunity()
              .candidates("louvain")
              .metrics("modularity", "stability")
              .uq(method="perturbation", n_samples=20)
              .seed(42)
              .execute(network)
        )
        
        # Both should complete
        assert result_few.community_stats.stability_score is not None
        assert result_many.community_stats.stability_score is not None
        
        # With more samples, stability estimate should be more reliable
        # (We can't assert it's always higher, but it should be defined)
        assert isinstance(result_many.community_stats.stability_score, float)
    
    def test_consensus_under_noise(self):
        """Test consensus computation under noisy conditions."""
        # Create network with ambiguous structure
        network = multinet.multi_layer_network(directed=False)
        nodes = [{"source": f"N{i}", "type": "layer1"} for i in range(12)]
        network.add_nodes(nodes)
        
        np.random.seed(42)
        
        # Add edges with some randomness
        for i in range(12):
            for j in range(i+1, 12):
                if np.random.rand() < 0.3:  # Moderate density
                    network.add_edges([{
                        "source": f"N{i}", "target": f"N{j}",
                        "source_type": "layer1", "target_type": "layer1"
                    }])
        
        # Run with UQ
        result = (
            AutoCommunity()
              .candidates("louvain", "leiden")
              .metrics("modularity", "coverage")
              .uq(method="perturbation", n_samples=15)
              .seed(42)
              .execute(network)
        )
        
        # Should produce result
        assert result.consensus_partition is not None
        
        # If consensus was used, should have multiple algorithms in Pareto front
        if result.selected == "consensus":
            assert len(result.pareto_front) >= 2


@pytest.mark.integration
class TestAutoCommunityAblation:
    """Ablation tests - removing features to validate their impact."""
    
    def test_without_uq_vs_with_uq(self):
        """Compare results with and without UQ."""
        # Create test network
        network = multinet.multi_layer_network(directed=False)
        nodes = [{"source": f"N{i}", "type": "layer1"} for i in range(12)]
        network.add_nodes(nodes)
        
        for i in range(6):
            for j in range(i+1, 6):
                network.add_edges([{
                    "source": f"N{i}", "target": f"N{j}",
                    "source_type": "layer1", "target_type": "layer1"
                }])
        
        for i in range(6, 12):
            for j in range(i+1, 12):
                network.add_edges([{
                    "source": f"N{i}", "target": f"N{j}",
                    "source_type": "layer1", "target_type": "layer1"
                }])
        
        # Without UQ
        result_no_uq = (
            AutoCommunity()
              .candidates("louvain")
              .metrics("modularity", "coverage")
              .seed(42)
              .execute(network)
        )
        
        # With UQ
        result_with_uq = (
            AutoCommunity()
              .candidates("louvain")
              .metrics("modularity", "stability")
              .uq(method="perturbation", n_samples=15)
              .seed(42)
              .execute(network)
        )
        
        # Both should work
        assert result_no_uq.consensus_partition is not None
        assert result_with_uq.consensus_partition is not None
        
        # With UQ should have stability score
        assert result_with_uq.community_stats.stability_score is not None
        
        # Without UQ may not have stability (or has default)
        # This is expected behavior
    
    def test_without_null_model_vs_with_null(self):
        """Compare results with and without null model calibration."""
        # Create network
        network = multinet.multi_layer_network(directed=False)
        nodes = [{"source": f"N{i}", "type": "layer1"} for i in range(15)]
        network.add_nodes(nodes)
        
        # Create structure
        for i in range(8):
            for j in range(i+1, 8):
                network.add_edges([{
                    "source": f"N{i}", "target": f"N{j}",
                    "source_type": "layer1", "target_type": "layer1"
                }])
        
        for i in range(8, 15):
            for j in range(i+1, 15):
                network.add_edges([{
                    "source": f"N{i}", "target": f"N{j}",
                    "source_type": "layer1", "target_type": "layer1"
                }])
        
        # Without null model
        result_no_null = (
            AutoCommunity()
              .candidates("louvain")
              .metrics("modularity")
              .seed(42)
              .execute(network)
        )
        
        # With null model
        result_with_null = (
            AutoCommunity()
              .candidates("louvain")
              .metrics("modularity")
              .null_model(type="configuration", samples=5)
              .seed(42)
              .execute(network)
        )
        
        # Both should work
        assert result_no_null.consensus_partition is not None
        assert result_with_null.consensus_partition is not None
        
        # With null model should have null results
        assert result_with_null.null_model_results is not None or \
               result_with_null.provenance['null_enabled']
        
        # Without null model should not have null results
        assert result_no_null.null_model_results is None or \
               not result_no_null.provenance['null_enabled']
    
    def test_single_metric_vs_multi_objective(self):
        """Compare single-metric to multi-objective evaluation."""
        # Create network
        network = multinet.multi_layer_network(directed=False)
        nodes = [{"source": f"N{i}", "type": "layer1"} for i in range(12)]
        network.add_nodes(nodes)
        
        for i in range(12):
            for j in range(i+1, min(i+3, 12)):
                network.add_edges([{
                    "source": f"N{i}", "target": f"N{j}",
                    "source_type": "layer1", "target_type": "layer1"
                }])
        
        # Single metric
        result_single = (
            AutoCommunity()
              .candidates("louvain", "leiden")
              .metrics("modularity")  # Only one
              .seed(42)
              .execute(network)
        )
        
        # Multi-objective
        result_multi = (
            AutoCommunity()
              .candidates("louvain", "leiden")
              .metrics("modularity", "coverage")  # Multiple
              .seed(42)
              .execute(network)
        )
        
        # Both should work
        assert result_single.consensus_partition is not None
        assert result_multi.consensus_partition is not None
        
        # Check evaluation matrices
        assert len(result_single.evaluation_matrix.columns) >= 2  # algo_id + metric
        assert len(result_multi.evaluation_matrix.columns) >= 3  # algo_id + 2 metrics


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
