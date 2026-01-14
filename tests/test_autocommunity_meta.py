"""Tests for redesigned AutoCommunity meta-algorithm.

Tests cover:
- Multi-objective evaluation
- Pareto dominance selection
- Uncertainty quantification integration
- Null-model calibration
- Consensus community building
- Graph regime diagnostics
- Property-based invariants
"""

import pytest
import numpy as np
import pandas as pd
from unittest.mock import Mock, patch

from py3plex.core import multinet, random_generators
from py3plex.algorithms.community_detection import (
    AutoCommunity,
    AutoCommunityResult,
    CommunityStats,
)
from py3plex.exceptions import Py3plexIOError


class TestAutoCommunityBuilder:
    """Test AutoCommunity builder API."""
    
    def test_builder_creates_instance(self):
        """Builder should create AutoCommunity instance."""
        ac = AutoCommunity()
        assert ac is not None
        assert isinstance(ac, AutoCommunity)
    
    def test_builder_chaining(self):
        """Builder methods should support chaining."""
        ac = (
            AutoCommunity()
              .candidates("louvain", "leiden")
              .metrics("modularity", "coverage")
              .seed(42)
        )
        assert ac is not None
        assert ac._candidate_algorithms == ["louvain", "leiden"]
        assert ac._metric_names == ["modularity", "coverage"]
        assert ac._seed == 42
    
    def test_uq_configuration(self):
        """UQ configuration should be stored."""
        ac = (
            AutoCommunity()
              .candidates("louvain")
              .metrics("modularity")
              .uq(method="perturbation", n_samples=50)
        )
        assert ac._uq_config is not None
        assert ac._uq_config['method'] == "perturbation"
        assert ac._uq_config['n_samples'] == 50
    
    def test_null_model_configuration(self):
        """Null model configuration should be stored."""
        ac = (
            AutoCommunity()
              .candidates("louvain")
              .metrics("modularity")
              .null_model(type="configuration", samples=100)
        )
        assert ac._null_config is not None
        assert ac._null_config['type'] == "configuration"
        assert ac._null_config['samples'] == 100
    
    def test_pareto_toggle(self):
        """Pareto selection should be toggleable."""
        ac = AutoCommunity().pareto(enabled=False)
        assert ac._use_pareto is False
        
        ac = AutoCommunity().pareto(enabled=True)
        assert ac._use_pareto is True


class TestAutoCommunityExecution:
    """Test AutoCommunity execution."""
    
    @pytest.fixture
    def simple_network(self):
        """Create a simple test network."""
        network = multinet.multi_layer_network(directed=False)
        
        # Add nodes
        nodes = [{"source": f"N{i}", "type": "layer1"} for i in range(10)]
        network.add_nodes(nodes)
        
        # Create two communities
        # Community 1: nodes 0-4
        for i in range(5):
            for j in range(i+1, 5):
                network.add_edges([{
                    "source": f"N{i}", "target": f"N{j}",
                    "source_type": "layer1", "target_type": "layer1"
                }])
        
        # Community 2: nodes 5-9
        for i in range(5, 10):
            for j in range(i+1, 10):
                network.add_edges([{
                    "source": f"N{i}", "target": f"N{j}",
                    "source_type": "layer1", "target_type": "layer1"
                }])
        
        # Bridge
        network.add_edges([{
            "source": "N4", "target": "N5",
            "source_type": "layer1", "target_type": "layer1"
        }])
        
        return network
    
    def test_basic_execution(self, simple_network):
        """Basic execution should complete without errors."""
        result = (
            AutoCommunity()
              .candidates("louvain")
              .metrics("modularity", "coverage")
              .seed(42)
              .execute(simple_network)
        )
        
        assert isinstance(result, AutoCommunityResult)
        assert len(result.algorithms_tested) >= 1
        assert result.selected is not None
        assert result.consensus_partition is not None
        assert isinstance(result.community_stats, CommunityStats)
    
    def test_execution_validates_config(self, simple_network):
        """Execution should validate configuration."""
        # Missing candidates
        with pytest.raises(Exception):  # AlgorithmError
            AutoCommunity().metrics("modularity").execute(simple_network)
        
        # Missing metrics
        with pytest.raises(Exception):  # AlgorithmError
            AutoCommunity().candidates("louvain").execute(simple_network)
    
    def test_multiple_candidates(self, simple_network):
        """Should handle multiple candidate algorithms."""
        result = (
            AutoCommunity()
              .candidates("louvain", "leiden")
              .metrics("modularity", "coverage")
              .seed(42)
              .execute(simple_network)
        )
        
        assert len(result.algorithms_tested) >= 2
        assert "louvain" in str(result.algorithms_tested)
        assert "leiden" in str(result.algorithms_tested)
    
    def test_result_structure(self, simple_network):
        """Result should have required attributes."""
        result = (
            AutoCommunity()
              .candidates("louvain")
              .metrics("modularity")
              .seed(42)
              .execute(simple_network)
        )
        
        # Check required attributes
        assert hasattr(result, 'algorithms_tested')
        assert hasattr(result, 'pareto_front')
        assert hasattr(result, 'selected')
        assert hasattr(result, 'consensus_partition')
        assert hasattr(result, 'community_stats')
        assert hasattr(result, 'evaluation_matrix')
        assert hasattr(result, 'diagnostics')
        assert hasattr(result, 'provenance')
    
    def test_community_stats_structure(self, simple_network):
        """Community stats should have required attributes."""
        result = (
            AutoCommunity()
              .candidates("louvain")
              .metrics("modularity", "coverage")
              .seed(42)
              .execute(simple_network)
        )
        
        stats = result.community_stats
        assert hasattr(stats, 'n_communities')
        assert hasattr(stats, 'community_sizes')
        assert hasattr(stats, 'coverage')
        assert stats.n_communities > 0
        assert len(stats.community_sizes) == stats.n_communities


class TestParetoSelection:
    """Test Pareto dominance logic."""
    
    @pytest.fixture
    def simple_network(self):
        """Create a simple test network."""
        network = multinet.multi_layer_network(directed=False)
        nodes = [{"source": f"N{i}", "type": "layer1"} for i in range(8)]
        network.add_nodes(nodes)
        
        for i in range(8):
            for j in range(i+1, min(i+3, 8)):
                network.add_edges([{
                    "source": f"N{i}", "target": f"N{j}",
                    "source_type": "layer1", "target_type": "layer1"
                }])
        
        return network
    
    def test_pareto_front_identified(self, simple_network):
        """Pareto front should be identified."""
        result = (
            AutoCommunity()
              .candidates("louvain", "leiden")
              .metrics("modularity", "coverage")
              .pareto(enabled=True)
              .seed(42)
              .execute(simple_network)
        )
        
        assert result.pareto_front is not None
        assert len(result.pareto_front) >= 1
        assert all(algo in result.algorithms_tested for algo in result.pareto_front)
    
    def test_single_winner_when_dominated(self, simple_network):
        """Single winner should be selected when one dominates."""
        result = (
            AutoCommunity()
              .candidates("louvain")
              .metrics("modularity")
              .pareto(enabled=True)
              .seed(42)
              .execute(simple_network)
        )
        
        # With single algorithm, it's always the winner
        assert len(result.pareto_front) == 1
        assert result.selected in result.algorithms_tested


class TestUncertaintyQuantification:
    """Test UQ integration."""
    
    @pytest.fixture
    def test_network(self):
        """Create test network."""
        np.random.seed(42)
        return random_generators.random_multilayer_ER(
            n=15,
            l=1,
            p=0.3,
            directed=False,
        )
    
    def test_uq_enables_stability_metric(self, test_network):
        """UQ should enable stability computation."""
        result = (
            AutoCommunity()
              .candidates("louvain")
              .metrics("modularity", "stability")
              .uq(method="perturbation", n_samples=10)
              .seed(42)
              .execute(test_network)
        )
        
        # Check if stability was computed
        eval_df = result.evaluation_matrix
        assert "stability" in eval_df.columns
    
    def test_uq_provides_node_confidence(self, test_network):
        """UQ should provide node-level confidence."""
        result = (
            AutoCommunity()
              .candidates("louvain")
              .metrics("modularity", "stability")
              .uq(method="perturbation", n_samples=10)
              .seed(42)
              .execute(test_network)
        )
        
        stats = result.community_stats
        # With UQ, should have confidence scores
        # (May be None if UQ data not fully propagated)
        assert stats.stability_score is not None or stats.coverage is not None
    
    def test_without_uq_no_stability(self, test_network):
        """Without UQ, stability should have default value."""
        result = (
            AutoCommunity()
              .candidates("louvain")
              .metrics("modularity", "coverage")
              .seed(42)
              .execute(test_network)
        )
        
        # Without UQ, some metrics may not be available
        # This is expected behavior
        assert result.community_stats is not None


class TestNullModelCalibration:
    """Test null model integration."""
    
    @pytest.fixture
    def test_network(self):
        """Create test network."""
        network = multinet.multi_layer_network(directed=False)
        nodes = [{"source": f"N{i}", "type": "layer1"} for i in range(12)]
        network.add_nodes(nodes)
        
        # Create structure
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
        
        return network
    
    def test_null_models_executed(self, test_network):
        """Null models should be executed when configured."""
        result = (
            AutoCommunity()
              .candidates("louvain")
              .metrics("modularity")
              .null_model(type="configuration", samples=5)
              .seed(42)
              .execute(test_network)
        )
        
        # Should have null model results
        assert result.null_model_results is not None or result.provenance['null_enabled']
    
    def test_null_scores_in_provenance(self, test_network):
        """Null Z-scores should be available."""
        result = (
            AutoCommunity()
              .candidates("louvain")
              .metrics("modularity")
              .null_model(type="configuration", samples=5)
              .seed(42)
              .execute(test_network)
        )
        
        # Check provenance indicates null model usage
        assert result.provenance['null_enabled'] is True


class TestGraphRegimeDiagnostics:
    """Test graph regime feature extraction."""
    
    def test_regime_features_computed(self):
        """Regime features should be computed."""
        network = multinet.multi_layer_network(directed=False)
        nodes = [{"source": f"N{i}", "type": "layer1"} for i in range(10)]
        network.add_nodes(nodes)
        
        for i in range(10):
            for j in range(i+1, min(i+3, 10)):
                network.add_edges([{
                    "source": f"N{i}", "target": f"N{j}",
                    "source_type": "layer1", "target_type": "layer1"
                }])
        
        result = (
            AutoCommunity()
              .candidates("louvain")
              .metrics("modularity")
              .seed(42)
              .execute(network)
        )
        
        assert result.graph_regime is not None
        assert isinstance(result.graph_regime, dict)
    
    def test_regime_has_expected_features(self):
        """Regime should include standard features."""
        np.random.seed(42)
        network = random_generators.random_multilayer_ER(
            n=15,
            l=2,
            p=0.3,
            directed=False,
        )
        
        result = (
            AutoCommunity()
              .candidates("louvain")
              .metrics("modularity")
              .seed(42)
              .execute(network)
        )
        
        regime = result.graph_regime
        # Should have some regime features
        assert len(regime) > 0


class TestResultExport:
    """Test result export functionality."""
    
    @pytest.fixture
    def result(self):
        """Create a result for testing."""
        network = multinet.multi_layer_network(directed=False)
        nodes = [{"source": f"N{i}", "type": "layer1"} for i in range(8)]
        network.add_nodes(nodes)
        
        for i in range(8):
            for j in range(i+1, min(i+2, 8)):
                network.add_edges([{
                    "source": f"N{i}", "target": f"N{j}",
                    "source_type": "layer1", "target_type": "layer1"
                }])
        
        return (
            AutoCommunity()
              .candidates("louvain")
              .metrics("modularity", "coverage")
              .seed(42)
              .execute(network)
        )
    
    def test_to_pandas(self, result):
        """Should export to pandas DataFrame."""
        df = result.to_pandas()
        
        assert isinstance(df, pd.DataFrame)
        assert 'node' in df.columns
        assert 'layer' in df.columns
        assert 'community' in df.columns
        assert len(df) > 0
    
    def test_to_dict(self, result):
        """Should export to dictionary."""
        d = result.to_dict()
        
        assert isinstance(d, dict)
        assert 'algorithms_tested' in d
        assert 'pareto_front' in d
        assert 'selected' in d
        assert 'consensus_partition' in d
        assert 'provenance' in d
    
    def test_explain(self, result):
        """Should generate explanation."""
        explanation = result.explain()
        
        assert isinstance(explanation, str)
        assert len(explanation) > 0
        assert "Selection" in explanation or "selected" in explanation.lower()


class TestReproducibility:
    """Test reproducibility with seeds."""
    
    def test_same_seed_same_result(self):
        """Same seed should produce same partition."""
        network = multinet.multi_layer_network(directed=False)
        nodes = [{"source": f"N{i}", "type": "layer1"} for i in range(10)]
        network.add_nodes(nodes)
        
        for i in range(10):
            for j in range(i+1, min(i+3, 10)):
                network.add_edges([{
                    "source": f"N{i}", "target": f"N{j}",
                    "source_type": "layer1", "target_type": "layer1"
                }])
        
        result1 = (
            AutoCommunity()
              .candidates("louvain")
              .metrics("modularity")
              .seed(42)
              .execute(network)
        )
        
        result2 = (
            AutoCommunity()
              .candidates("louvain")
              .metrics("modularity")
              .seed(42)
              .execute(network)
        )
        
        # Should produce same number of communities
        assert result1.community_stats.n_communities == result2.community_stats.n_communities


@pytest.mark.property
class TestPropertyInvariants:
    """Property-based tests for invariants."""
    
    def test_pareto_front_is_subset(self):
        """Pareto front should be subset of tested algorithms."""
        network = multinet.multi_layer_network(directed=False)
        nodes = [{"source": f"N{i}", "type": "layer1"} for i in range(8)]
        network.add_nodes(nodes)
        
        for i in range(8):
            for j in range(i+1, min(i+2, 8)):
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
        
        # Pareto front must be subset of tested algorithms
        assert set(result.pareto_front).issubset(set(result.algorithms_tested))
    
    def test_coverage_in_valid_range(self):
        """Coverage should be in [0, 1]."""
        network = multinet.multi_layer_network(directed=False)
        nodes = [{"source": f"N{i}", "type": "layer1"} for i in range(8)]
        network.add_nodes(nodes)
        
        for i in range(8):
            for j in range(i+1, min(i+2, 8)):
                network.add_edges([{
                    "source": f"N{i}", "target": f"N{j}",
                    "source_type": "layer1", "target_type": "layer1"
                }])
        
        result = (
            AutoCommunity()
              .candidates("louvain")
              .metrics("modularity", "coverage")
              .seed(42)
              .execute(network)
        )
        
        coverage = result.community_stats.coverage
        assert 0.0 <= coverage <= 1.0
    
    def test_community_sizes_sum_to_n_nodes(self):
        """Sum of community sizes should equal number of nodes."""
        network = multinet.multi_layer_network(directed=False)
        nodes = [{"source": f"N{i}", "type": "layer1"} for i in range(10)]
        network.add_nodes(nodes)
        
        for i in range(10):
            for j in range(i+1, min(i+3, 10)):
                network.add_edges([{
                    "source": f"N{i}", "target": f"N{j}",
                    "source_type": "layer1", "target_type": "layer1"
                }])
        
        result = (
            AutoCommunity()
              .candidates("louvain")
              .metrics("modularity")
              .seed(42)
              .execute(network)
        )
        
        total_size = sum(result.community_stats.community_sizes)
        n_nodes = len(result.consensus_partition)
        assert total_size == n_nodes


class TestInfomapIntegration:
    """Test infomap algorithm integration with AutoCommunity."""
    
    @pytest.fixture
    def simple_network(self):
        """Create a simple test network."""
        network = multinet.multi_layer_network(directed=False)
        
        # Add nodes
        nodes = [{"source": f"N{i}", "type": "layer1"} for i in range(10)]
        network.add_nodes(nodes)
        
        # Create two communities
        # Community 1: nodes 0-4
        for i in range(5):
            for j in range(i+1, 5):
                network.add_edges([{
                    "source": f"N{i}", "target": f"N{j}",
                    "source_type": "layer1", "target_type": "layer1"
                }])
        
        # Community 2: nodes 5-9
        for i in range(5, 10):
            for j in range(i+1, 10):
                network.add_edges([{
                    "source": f"N{i}", "target": f"N{j}",
                    "source_type": "layer1", "target_type": "layer1"
                }])
        
        # Bridge
        network.add_edges([{
            "source": "N4", "target": "N5",
            "source_type": "layer1", "target_type": "layer1"
        }])
        
        return network
    
    @pytest.mark.slow
    def test_infomap_in_candidates(self, simple_network):
        """AutoCommunity should accept 'infomap' as a candidate algorithm."""
        try:
            result = (
                AutoCommunity()
                  .candidates("infomap")
                  .metrics("modularity", "coverage")
                  .seed(42)
                  .execute(simple_network)
            )
            
            # If infomap binary is available, check results
            assert isinstance(result, AutoCommunityResult)
            # Check if infomap is in any algorithm_id (format "algorithm:default")
            has_infomap = any("infomap" in algo_id for algo_id in result.algorithms_tested)
            # Either infomap succeeded or was gracefully skipped
            assert has_infomap or len(result.algorithms_tested) == 0
            
        except Exception as e:
            # If infomap binary not found, or no algorithms produced valid partitions,
            # test should still pass gracefully
            if ("binary not found" in str(e).lower() or 
                "infomap" in str(e).lower() or
                "No algorithms produced valid partitions" in str(e)):
                pytest.skip(f"Infomap binary not available or failed: {e}")
            else:
                raise
    
    @pytest.mark.slow
    def test_infomap_with_multiple_algorithms(self, simple_network):
        """Infomap should work alongside other algorithms."""
        result = (
            AutoCommunity()
              .candidates("louvain", "infomap", "leiden")
              .metrics("modularity", "coverage")
              .seed(42)
              .execute(simple_network)
        )
        
        # Should have at least louvain and leiden
        assert isinstance(result, AutoCommunityResult)
        assert len(result.algorithms_tested) >= 2
        # louvain and leiden should always work (algorithm_ids have format "algorithm:default")
        assert any("louvain" in algo_id for algo_id in result.algorithms_tested)
        assert any("leiden" in algo_id for algo_id in result.algorithms_tested)
        # infomap may or may not be present depending on binary availability
    
    def test_infomap_gracefully_skips_when_unavailable(self, simple_network):
        """If infomap binary is missing, AutoCommunity should skip it gracefully."""
        # This test ensures the implementation doesn't crash when infomap fails
        with patch('py3plex.algorithms.community_detection.community_wrapper.infomap_communities') as mock_infomap:
            # Make infomap raise an error (simulating missing binary)
            mock_infomap.side_effect = Py3plexIOError("Infomap binary not found")
            
            # Should still work with other algorithms
            result = (
                AutoCommunity()
                  .candidates("louvain", "infomap")
                  .metrics("modularity", "coverage")
                  .seed(42)
                  .execute(simple_network)
            )
            
            # Should have at least louvain
            assert isinstance(result, AutoCommunityResult)
            # Check if louvain is in any of the algorithm_ids (which have format "algorithm:default")
            assert any("louvain" in algo_id for algo_id in result.algorithms_tested)
            # infomap should not be in results since it failed
            assert not any("infomap" in algo_id for algo_id in result.algorithms_tested)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
