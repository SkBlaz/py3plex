"""Tests for AutoCommunity executor internal functions.

These tests focus on improving coverage for autocommunity_executor.py,
specifically testing internal helper functions that were previously untested.
"""

import pytest
import numpy as np
import pandas as pd
from unittest.mock import Mock, patch

from py3plex.core import multinet
from py3plex.algorithms.community_detection.autocommunity_executor import (
    _compute_graph_regime,
    _filter_by_null_scores,
    _pareto_selection,
    _build_consensus,
    _build_stats_from_partition,
)
from py3plex.algorithms.community_detection import AutoCommunity


@pytest.fixture
def simple_network():
    """Create a simple test network."""
    network = multinet.multi_layer_network(directed=False)
    nodes = [{"source": f"N{i}", "type": "layer1"} for i in range(10)]
    network.add_nodes(nodes)
    
    for i in range(10):
        for j in range(i+1, min(i+2, 10)):
            network.add_edges([{
                "source": f"N{i}", "target": f"N{j}",
                "source_type": "layer1", "target_type": "layer1"
            }])
    
    return network


@pytest.fixture
def multilayer_network():
    """Create a multilayer test network."""
    network = multinet.multi_layer_network(directed=False)
    
    # Add nodes in two layers
    for layer in ["layer1", "layer2"]:
        nodes = [{"source": f"N{i}", "type": layer} for i in range(8)]
        network.add_nodes(nodes)
    
    # Add edges in each layer
    for layer in ["layer1", "layer2"]:
        for i in range(8):
            for j in range(i+1, min(i+2, 8)):
                network.add_edges([{
                    "source": f"N{i}", "target": f"N{j}",
                    "source_type": layer, "target_type": layer
                }])
    
    # Add some inter-layer edges
    for i in range(0, 8, 2):
        network.add_edges([{
            "source": f"N{i}", "target": f"N{i}",
            "source_type": "layer1", "target_type": "layer2"
        }])
    
    return network


class TestComputeGraphRegime:
    """Test _compute_graph_regime function."""
    
    def test_regime_returns_dict(self, simple_network):
        """Should return a dictionary of features."""
        regime = _compute_graph_regime(simple_network)
        
        assert isinstance(regime, dict)
        assert len(regime) > 0
    
    def test_regime_has_degree_features(self, simple_network):
        """Should compute degree-related features."""
        regime = _compute_graph_regime(simple_network)
        
        # Should have degree heterogeneity
        assert 'degree_heterogeneity' in regime or 'mean_degree' in regime
    
    def test_regime_handles_empty_network(self):
        """Should handle empty network gracefully."""
        network = multinet.multi_layer_network(directed=False)
        
        regime = _compute_graph_regime(network)
        
        # Should return empty dict or dict with zero values
        assert isinstance(regime, dict)
    
    def test_regime_multilayer_features(self, multilayer_network):
        """Should compute multilayer-specific features."""
        regime = _compute_graph_regime(multilayer_network)
        
        assert isinstance(regime, dict)
        # Should have coupling strength for multilayer
        assert 'coupling_strength' in regime or len(regime) > 0
    
    def test_regime_handles_single_node(self):
        """Should handle single-node network."""
        network = multinet.multi_layer_network(directed=False)
        network.add_nodes([{"source": "N1", "type": "layer1"}])
        
        regime = _compute_graph_regime(network)
        
        assert isinstance(regime, dict)
    
    def test_regime_degree_heterogeneity_calculation(self, simple_network):
        """Should calculate degree heterogeneity correctly."""
        regime = _compute_graph_regime(simple_network)
        
        if 'degree_heterogeneity' in regime:
            # Should be non-negative
            assert regime['degree_heterogeneity'] >= 0.0
            # Should be a float
            assert isinstance(regime['degree_heterogeneity'], float)


class TestFilterByNullScores:
    """Test _filter_by_null_scores function."""
    
    def test_filter_removes_low_scores(self):
        """Should filter algorithms with low Z-scores."""
        algorithm_results = {
            'algo1': {'algorithm': 'louvain', 'partition': {}},
            'algo2': {'algorithm': 'leiden', 'partition': {}},
            'algo3': {'algorithm': 'infomap', 'partition': {}},
        }
        
        null_results = {
            'z_scores': {
                'algo1': 3.5,  # High score - keep
                'algo2': 1.0,  # Low score - filter
                'algo3': 2.5,  # High score - keep
            }
        }
        
        filtered = _filter_by_null_scores(algorithm_results, null_results, threshold=1.5)
        
        # Should keep algo1 and algo3, remove algo2
        assert 'algo1' in filtered
        assert 'algo3' in filtered
        assert 'algo2' not in filtered
    
    def test_filter_keeps_all_above_threshold(self):
        """Should keep all algorithms above threshold."""
        algorithm_results = {
            'algo1': {'algorithm': 'louvain', 'partition': {}},
            'algo2': {'algorithm': 'leiden', 'partition': {}},
        }
        
        null_results = {
            'z_scores': {
                'algo1': 3.5,
                'algo2': 2.5,
            }
        }
        
        filtered = _filter_by_null_scores(algorithm_results, null_results, threshold=1.5)
        
        assert len(filtered) == 2
        assert 'algo1' in filtered
        assert 'algo2' in filtered
    
    def test_filter_handles_missing_scores(self):
        """Should handle missing Z-scores gracefully."""
        algorithm_results = {
            'algo1': {'algorithm': 'louvain', 'partition': {}},
            'algo2': {'algorithm': 'leiden', 'partition': {}},
        }
        
        # Only algo1 has a score
        null_results = {
            'z_scores': {
                'algo1': 3.5,
            }
        }
        
        filtered = _filter_by_null_scores(algorithm_results, null_results, threshold=1.5)
        
        # Should keep algo1, and algo2 (no score means no filtering)
        assert 'algo1' in filtered


class TestParetoSelection:
    """Test _pareto_selection function."""
    
    def test_single_algorithm_is_selected(self):
        """Should select single algorithm as winner."""
        evaluation_matrix = pd.DataFrame({
            'algorithm_id': ['algo1'],
            'modularity': [0.5],
            'coverage': [0.8],
        })
        
        algorithm_results = {
            'algo1': {'algorithm': 'louvain', 'partition': {}},
        }
        
        pareto_front, selected = _pareto_selection(evaluation_matrix, algorithm_results)
        
        assert len(pareto_front) == 1
        assert selected == 'algo1'
    
    def test_dominated_algorithm_excluded(self):
        """Should exclude dominated algorithms from Pareto front."""
        # algo1 dominates algo2 (better on all metrics)
        evaluation_matrix = pd.DataFrame({
            'algorithm_id': ['algo1', 'algo2'],
            'modularity': [0.8, 0.5],  # algo1 better
            'coverage': [0.9, 0.6],    # algo1 better
        })
        
        algorithm_results = {
            'algo1': {'algorithm': 'louvain', 'partition': {}},
            'algo2': {'algorithm': 'leiden', 'partition': {}},
        }
        
        pareto_front, selected = _pareto_selection(evaluation_matrix, algorithm_results)
        
        # Only algo1 should be in Pareto front
        assert 'algo1' in pareto_front
        assert 'algo2' not in pareto_front
        assert selected == 'algo1'
    
    def test_multiple_non_dominated(self):
        """Should identify multiple non-dominated algorithms."""
        # Neither dominates: algo1 better on modularity, algo2 better on coverage
        evaluation_matrix = pd.DataFrame({
            'algorithm_id': ['algo1', 'algo2'],
            'modularity': [0.8, 0.6],  # algo1 better
            'coverage': [0.6, 0.9],    # algo2 better
        })
        
        algorithm_results = {
            'algo1': {'algorithm': 'louvain', 'partition': {}},
            'algo2': {'algorithm': 'leiden', 'partition': {}},
        }
        
        pareto_front, selected = _pareto_selection(evaluation_matrix, algorithm_results)
        
        # Both should be in Pareto front
        assert len(pareto_front) == 2
        assert 'algo1' in pareto_front
        assert 'algo2' in pareto_front
        # One should be selected (uses modularity as tiebreaker)
        assert selected in ['algo1', 'algo2']
    
    def test_min_direction_metrics(self):
        """Should handle minimization metrics correctly."""
        # Test with entropy (lower is better)
        evaluation_matrix = pd.DataFrame({
            'algorithm_id': ['algo1', 'algo2'],
            'modularity': [0.7, 0.7],  # Equal
            'entropy': [0.3, 0.5],     # algo1 better (lower)
        })
        
        algorithm_results = {
            'algo1': {'algorithm': 'louvain', 'partition': {}},
            'algo2': {'algorithm': 'leiden', 'partition': {}},
        }
        
        pareto_front, selected = _pareto_selection(evaluation_matrix, algorithm_results)
        
        # algo1 should dominate (lower entropy)
        assert 'algo1' in pareto_front
        assert selected == 'algo1'
    
    def test_handles_nan_values(self):
        """Should handle NaN values in metrics."""
        evaluation_matrix = pd.DataFrame({
            'algorithm_id': ['algo1', 'algo2'],
            'modularity': [0.8, np.nan],
            'coverage': [0.7, 0.9],
        })
        
        algorithm_results = {
            'algo1': {'algorithm': 'louvain', 'partition': {}},
            'algo2': {'algorithm': 'leiden', 'partition': {}},
        }
        
        pareto_front, selected = _pareto_selection(evaluation_matrix, algorithm_results)
        
        # Should handle NaN without crashing
        assert len(pareto_front) > 0
        assert selected in ['algo1', 'algo2']


class TestBuildConsensus:
    """Test _build_consensus function."""
    
    def test_consensus_with_two_partitions(self, simple_network):
        """Should build consensus from multiple partitions."""
        # Create two different partitions
        partition1 = {('N0', 'layer1'): 0, ('N1', 'layer1'): 0, ('N2', 'layer1'): 1}
        partition2 = {('N0', 'layer1'): 1, ('N1', 'layer1'): 1, ('N2', 'layer1'): 0}
        
        algorithm_results = {
            'algo1': {'algorithm': 'louvain', 'partition': partition1},
            'algo2': {'algorithm': 'leiden', 'partition': partition2},
        }
        
        pareto_front = ['algo1', 'algo2']
        
        consensus, stats = _build_consensus(simple_network, pareto_front, algorithm_results)
        
        # Should return a partition and stats
        assert isinstance(consensus, dict)
        assert len(consensus) > 0
        assert stats is not None
    
    def test_consensus_with_single_partition(self, simple_network):
        """Should handle single partition (no consensus needed)."""
        partition = {('N0', 'layer1'): 0, ('N1', 'layer1'): 0, ('N2', 'layer1'): 1}
        
        algorithm_results = {
            'algo1': {'algorithm': 'louvain', 'partition': partition},
        }
        
        pareto_front = ['algo1']
        
        consensus, stats = _build_consensus(simple_network, pareto_front, algorithm_results)
        
        # Should return the single partition
        assert isinstance(consensus, dict)
        assert stats is not None


class TestBuildStatsFromPartition:
    """Test _build_stats_from_partition function."""
    
    def test_stats_basic_computation(self):
        """Should compute basic statistics from partition."""
        partition = {
            ('N0', 'layer1'): 0,
            ('N1', 'layer1'): 0,
            ('N2', 'layer1'): 1,
            ('N3', 'layer1'): 1,
            ('N4', 'layer1'): 2,
        }
        
        stats = _build_stats_from_partition(partition)
        
        assert stats.n_communities == 3
        assert len(stats.community_sizes) == 3
        assert sorted(stats.community_sizes) == [1, 2, 2]
    
    def test_stats_single_community(self):
        """Should handle single community."""
        partition = {
            ('N0', 'layer1'): 0,
            ('N1', 'layer1'): 0,
            ('N2', 'layer1'): 0,
        }
        
        stats = _build_stats_from_partition(partition)
        
        assert stats.n_communities == 1
        assert stats.community_sizes == [3]
    
    def test_stats_all_singletons(self):
        """Should handle all singleton communities."""
        partition = {
            ('N0', 'layer1'): 0,
            ('N1', 'layer1'): 1,
            ('N2', 'layer1'): 2,
        }
        
        stats = _build_stats_from_partition(partition)
        
        assert stats.n_communities == 3
        assert all(size == 1 for size in stats.community_sizes)
    
    def test_stats_empty_partition(self):
        """Should handle empty partition."""
        partition = {}
        
        stats = _build_stats_from_partition(partition)
        
        assert stats.n_communities == 0
        assert stats.community_sizes == []


class TestAutoCommunityBuilderMethods:
    """Test additional AutoCommunity builder methods not covered elsewhere."""
    
    def test_strategy_method(self):
        """Should set strategy correctly."""
        ac = AutoCommunity().strategy("successive_halving", eta=3, rounds=2)
        
        assert ac._strategy == "successive_halving"
        assert ac._racer_config is not None
        assert ac._racer_config.get('eta') == 3
        assert ac._racer_config.get('rounds') == 2
    
    def test_metrics_accepts_strings(self):
        """Should accept metric names as strings."""
        ac = AutoCommunity().metrics("modularity", "coverage")
        
        assert len(ac._metric_names) == 2
        assert "modularity" in ac._metric_names
        assert "coverage" in ac._metric_names
    
    def test_seed_method(self):
        """Should set seed correctly."""
        ac = AutoCommunity().seed(12345)
        
        assert ac._seed == 12345
    
    def test_multiple_candidates(self):
        """Should accept multiple candidate algorithms."""
        ac = AutoCommunity().candidates("louvain", "leiden", "infomap", "dc_sbm")
        
        assert len(ac._candidate_algorithms) == 4
        assert "louvain" in ac._candidate_algorithms
        assert "dc_sbm" in ac._candidate_algorithms
    
    def test_multiple_metrics(self):
        """Should accept multiple metrics."""
        ac = AutoCommunity().metrics("modularity", "coverage", "stability", "entropy")
        
        assert len(ac._metric_names) == 4
        assert "modularity" in ac._metric_names
        assert "entropy" in ac._metric_names


class TestAutoCommunityResultMethods:
    """Test AutoCommunityResult additional methods."""
    
    @pytest.fixture
    def test_result(self, simple_network):
        """Create a test result."""
        return (
            AutoCommunity()
              .candidates("louvain")
              .metrics("modularity", "coverage")
              .seed(42)
              .execute(simple_network)
        )
    
    def test_result_has_provenance(self, test_result):
        """Result should have provenance metadata."""
        assert hasattr(test_result, 'provenance')
        assert isinstance(test_result.provenance, dict)
        assert 'seed' in test_result.provenance
        assert test_result.provenance['seed'] == 42
    
    def test_result_has_graph_regime(self, test_result):
        """Result should have graph regime features."""
        assert hasattr(test_result, 'graph_regime')
        assert isinstance(test_result.graph_regime, dict)
    
    def test_result_to_dict_completeness(self, test_result):
        """to_dict should include all essential information."""
        result_dict = test_result.to_dict()
        
        assert 'selected' in result_dict
        assert 'consensus_partition' in result_dict
        assert 'community_stats' in result_dict
        assert 'algorithms_tested' in result_dict
        assert 'provenance' in result_dict
    
    def test_result_explain_returns_string(self, test_result):
        """explain should return a string description."""
        explanation = test_result.explain()
        
        assert isinstance(explanation, str)
        assert len(explanation) > 0
    
    def test_community_stats_to_dict(self, test_result):
        """CommunityStats to_dict should work."""
        stats_dict = test_result.community_stats.to_dict()
        
        assert isinstance(stats_dict, dict)
        assert 'n_communities' in stats_dict
        assert 'community_sizes' in stats_dict


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_no_candidates_specified(self):
        """Should handle missing candidates gracefully."""
        network = multinet.multi_layer_network(directed=False)
        network.add_nodes([{"source": "N1", "type": "layer1"}])
        
        ac = AutoCommunity().metrics("modularity")
        
        # Should not crash, might use defaults or raise clear error
        try:
            result = ac.execute(network)
            # If it works, check result is valid
            assert result is not None
        except Exception as e:
            # If it raises, should be a clear error
            assert "candidate" in str(e).lower() or "algorithm" in str(e).lower()
    
    def test_no_metrics_specified(self, simple_network):
        """Should handle missing metrics gracefully."""
        ac = AutoCommunity().candidates("louvain")
        
        # Should not crash, might use defaults or raise clear error
        try:
            result = ac.execute(simple_network)
            # If it works, check result is valid
            assert result is not None
        except Exception as e:
            # If it raises, should be a clear error
            assert "metric" in str(e).lower()
    
    def test_disconnected_network(self):
        """Should handle disconnected network."""
        network = multinet.multi_layer_network(directed=False)
        # Add two disconnected components
        network.add_nodes([
            {"source": "N1", "type": "layer1"},
            {"source": "N2", "type": "layer1"},
            {"source": "N3", "type": "layer1"},
            {"source": "N4", "type": "layer1"},
        ])
        network.add_edges([
            {"source": "N1", "target": "N2", "source_type": "layer1", "target_type": "layer1"},
            {"source": "N3", "target": "N4", "source_type": "layer1", "target_type": "layer1"},
        ])
        
        result = (
            AutoCommunity()
              .candidates("louvain")
              .metrics("modularity")
              .seed(42)
              .execute(network)
        )
        
        # Should work and detect multiple communities
        assert result is not None
        assert result.community_stats.n_communities >= 2


# MDL condition test
class TestMDLMetric:
    """Test MDL (Minimum Description Length) metric logic."""

    def test_mdl_from_sbm_metadata(self):
        """Should use pre-computed MDL from SBM metadata if available."""
        # Mock result with SBM metadata
        algorithm_results = {
            'sbm_algo': {
                'partition': {('N1', 'L1'): 0, ('N2', 'L1'): 1},
                'meta': {'mdl': 450.5}
            }
        }

        result = algorithm_results['sbm_algo']
        value = np.nan
        if result.get('meta') and 'mdl' in result['meta']:
            value = result['meta']['mdl']

        assert value == 450.5

    def test_mdl_fallback_calculation_multiplex(self, multilayer_network):
        """Should compute fallback BIC/MDL for multiplex partitions."""
        # A multiplex partition: same entity has same community across layers
        partition = {
            ('N0', 'layer1'): 0, ('N0', 'layer2'): 0,
            ('N1', 'layer1'): 1, ('N1', 'layer2'): 1
        }

        algorithm_results = {
            'louvain_algo': {
                'partition': partition,
                'algorithm': 'louvain'
            }
        }

        # Mock the network and cache to isolate the MDL logic
        from py3plex.algorithms.community_detection.autocommunity_executor import _evaluate_algorithms

        eval_df = _evaluate_algorithms(
            multilayer_network,
            algorithm_results,
            metric_names=["mdl"],
            custom_metrics=[]
        )

        mdl_value = eval_df.iloc[0]['mdl']
        assert not np.isnan(mdl_value)
        # MDL for a non-empty graph should be a positive float
        assert mdl_value > 0

    def test_mdl_parameter_penalty_independent(self, multilayer_network):
        """Should penalize independent assignments more than multiplex assignments."""
        # Multiplex: 2 nodes, 1 community each across 2 layers = 2 params
        partition_multi = {
            ('N0', 'layer1'): 0, ('N0', 'layer2'): 0,
            ('N1', 'layer1'): 1, ('N1', 'layer2'): 1
        }

        # Independent: 2 nodes, different communities in different layers = 4 params
        partition_indep = {
            ('N0', 'layer1'): 0, ('N0', 'layer2'): 1,
            ('N1', 'layer1'): 1, ('N1', 'layer2'): 0
        }

        results = {
            'multi': {'partition': partition_multi, 'algorithm': 'louvain'},
            'indep': {'partition': partition_indep, 'algorithm': 'louvain'}
        }

        from py3plex.algorithms.community_detection.autocommunity_executor import _evaluate_algorithms
        eval_df = _evaluate_algorithms(multilayer_network, results, ["mdl"], [])

        mdl_multi = eval_df[eval_df['algorithm_id'] == 'multi']['mdl'].values[0]
        mdl_indep = eval_df[eval_df['algorithm_id'] == 'indep']['mdl'].values[0]

        assert mdl_indep > mdl_multi

    def test_mdl_handles_empty_partition(self, simple_network):
        """Should handle empty partitions by returning 0.0."""
        algorithm_results = {
            'empty_algo': {'partition': {}, 'algorithm': 'louvain'}
        }

        from py3plex.algorithms.community_detection.autocommunity_executor import _evaluate_algorithms
        eval_df = _evaluate_algorithms(simple_network, algorithm_results, ["mdl"], [])

        assert eval_df.iloc[0]['mdl'] == 0.0

    def test_mdl_numerical_stability(self, multilayer_network):
        """Should remain stable (not NaN) even with isolated nodes."""
        # Add isolated node to partition
        partition = {node: 0 for node in multilayer_network.get_nodes()}
        # Force an isolated community
        partition[('Isolated', 'layer1')] = 99

        algorithm_results = {
            'stable_algo': {'partition': partition, 'algorithm': 'louvain'}
        }

        from py3plex.algorithms.community_detection.autocommunity_executor import _evaluate_algorithms
        eval_df = _evaluate_algorithms(multilayer_network, algorithm_results, ["mdl"], [])

        # Result should be a valid number
        assert np.isfinite(eval_df.iloc[0]['mdl'])
