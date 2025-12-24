"""Tests for DSL Query Zoo examples.

This test module ensures that all Query Zoo examples:
- Execute without errors
- Return expected data structures
- Produce outputs with expected properties

Tests are fast and suitable for CI.
"""

import pytest
import pandas as pd
import numpy as np

from examples.dsl_query_zoo.datasets import (
    create_social_work_network,
    create_communication_network,
    create_transport_network,
    get_dataset,
)
from examples.dsl_query_zoo.queries import (
    query_basic_exploration,
    query_cross_layer_hubs,
    query_layer_similarity,
    query_community_structure,
    query_multiplex_pagerank,
    query_robustness_analysis,
    query_advanced_centrality_comparison,
    query_edge_grouping_and_coverage,
    query_null_model_comparison,
    query_bootstrap_confidence_intervals,
    query_uncertainty_aware_ranking,
)


def _extract_layer_names(network):
    """Helper to extract layer names from network.
    
    Args:
        network: A multi_layer_network instance
        
    Returns:
        List of layer names
    """
    layers_data = network.get_layers()
    if isinstance(layers_data, tuple):
        return layers_data[0]
    return list(layers_data)


# Fixtures for networks
@pytest.fixture
def social_work_network():
    """Fixture for social-work network."""
    return create_social_work_network(seed=42)


@pytest.fixture
def communication_network():
    """Fixture for communication network."""
    return create_communication_network(seed=42)


@pytest.fixture
def transport_network():
    """Fixture for transport network."""
    return create_transport_network(seed=42)


# Dataset tests
class TestDatasets:
    """Test dataset generation functions."""
    
    def test_social_work_network_creation(self):
        """Test social-work network is created with expected properties."""
        net = create_social_work_network(seed=42)
        assert net is not None
        layers = _extract_layer_names(net)
        assert len(layers) == 3
        assert 'social' in layers
        assert 'work' in layers
        assert 'family' in layers
    
    def test_communication_network_creation(self):
        """Test communication network is created with expected properties."""
        net = create_communication_network(seed=42)
        assert net is not None
        layers = _extract_layer_names(net)
        assert len(layers) == 3
        assert 'email' in layers
        assert 'chat' in layers
        assert 'phone' in layers
    
    def test_transport_network_creation(self):
        """Test transport network is created with expected properties."""
        net = create_transport_network(seed=42)
        assert net is not None
        layers = _extract_layer_names(net)
        assert len(layers) == 3
        assert 'bus' in layers
        assert 'metro' in layers
        assert 'walking' in layers
    
    def test_get_dataset_function(self):
        """Test get_dataset retrieves networks correctly."""
        net1 = get_dataset('social_work', seed=42)
        net2 = get_dataset('communication', seed=42)
        net3 = get_dataset('transport', seed=42)
        
        assert net1 is not None
        assert net2 is not None
        assert net3 is not None
    
    def test_get_dataset_invalid_name(self):
        """Test get_dataset raises error for invalid name."""
        with pytest.raises(ValueError, match="Unknown dataset"):
            get_dataset('invalid_dataset_name')
    
    def test_reproducibility_with_seeds(self):
        """Test that same seed produces same network."""
        net1 = create_social_work_network(seed=42)
        net2 = create_social_work_network(seed=42)
        
        layers1 = net1.get_layers()[0]
        layers2 = net2.get_layers()[0]
        
        assert layers1 == layers2


# Query tests
class TestBasicExploration:
    """Test basic exploration query."""
    
    def test_returns_dataframe(self, social_work_network):
        """Test query returns a DataFrame."""
        result = query_basic_exploration(social_work_network)
        assert isinstance(result, pd.DataFrame)
    
    def test_has_expected_columns(self, social_work_network):
        """Test DataFrame has expected columns."""
        result = query_basic_exploration(social_work_network)
        expected_cols = ['layer', 'n_nodes', 'n_edges', 'avg_degree']
        assert list(result.columns) == expected_cols
    
    def test_has_all_layers(self, social_work_network):
        """Test result includes all layers."""
        result = query_basic_exploration(social_work_network)
        assert len(result) == 3  # social, work, family
        assert set(result['layer']) == {'social', 'work', 'family'}
    
    def test_positive_metrics(self, social_work_network):
        """Test metrics are positive."""
        result = query_basic_exploration(social_work_network)
        assert (result['n_nodes'] > 0).all()
        assert (result['n_edges'] >= 0).all()
        assert (result['avg_degree'] >= 0).all()


class TestCrossLayerHubs:
    """Test cross-layer hubs query."""
    
    def test_returns_dataframe(self, social_work_network):
        """Test query returns a DataFrame."""
        result = query_cross_layer_hubs(social_work_network, k=5)
        assert isinstance(result, pd.DataFrame)
    
    def test_has_expected_columns(self, social_work_network):
        """Test DataFrame has expected columns."""
        result = query_cross_layer_hubs(social_work_network, k=5)
        expected_cols = ['node', 'layer', 'degree', 'betweenness_centrality', 'layer_count']
        assert list(result.columns) == expected_cols
    
    def test_respects_k_parameter(self, social_work_network):
        """Test that k parameter limits results per layer."""
        k = 3
        result = query_cross_layer_hubs(social_work_network, k=k)
        # Each layer should have at most k nodes
        for layer in result['layer'].unique():
            layer_count = len(result[result['layer'] == layer])
            assert layer_count <= k
    
    def test_layer_count_valid(self, social_work_network):
        """Test layer_count is between 1 and num_layers."""
        result = query_cross_layer_hubs(social_work_network, k=5)
        assert (result['layer_count'] >= 1).all()
        assert (result['layer_count'] <= 3).all()  # 3 layers in network


class TestLayerSimilarity:
    """Test layer similarity query."""
    
    def test_returns_dataframe(self, social_work_network):
        """Test query returns a DataFrame."""
        result = query_layer_similarity(social_work_network)
        assert isinstance(result, pd.DataFrame)
    
    def test_is_square_matrix(self, social_work_network):
        """Test result is a square correlation matrix."""
        result = query_layer_similarity(social_work_network)
        assert result.shape[0] == result.shape[1]
    
    def test_diagonal_is_one(self, social_work_network):
        """Test diagonal elements are 1 (self-correlation)."""
        result = query_layer_similarity(social_work_network)
        for i in range(len(result)):
            assert result.iloc[i, i] == pytest.approx(1.0, abs=0.01)
    
    def test_symmetric_matrix(self, social_work_network):
        """Test correlation matrix is symmetric."""
        result = query_layer_similarity(social_work_network)
        assert np.allclose(result.values, result.values.T, atol=0.01)
    
    def test_correlations_in_valid_range(self, social_work_network):
        """Test correlations are between -1 and 1."""
        result = query_layer_similarity(social_work_network)
        assert (result.values >= -1.01).all()
        assert (result.values <= 1.01).all()


class TestCommunityStructure:
    """Test community structure query."""
    
    def test_returns_dataframe(self, communication_network):
        """Test query returns a DataFrame."""
        result = query_community_structure(communication_network)
        assert isinstance(result, pd.DataFrame)
    
    def test_has_expected_columns(self, communication_network):
        """Test DataFrame has expected columns."""
        result = query_community_structure(communication_network)
        expected_cols = ['community_id', 'layer', 'size', 'avg_degree', 'dominant_layer']
        assert list(result.columns) == expected_cols
    
    def test_positive_sizes(self, communication_network):
        """Test community sizes are positive."""
        result = query_community_structure(communication_network)
        if len(result) > 0:
            assert (result['size'] > 0).all()
    
    def test_valid_community_ids(self, communication_network):
        """Test community IDs are non-negative integers."""
        result = query_community_structure(communication_network)
        if len(result) > 0:
            assert (result['community_id'] >= 0).all()


class TestMultiplexPageRank:
    """Test multiplex PageRank query."""
    
    def test_returns_dataframe(self, transport_network):
        """Test query returns a DataFrame."""
        result = query_multiplex_pagerank(transport_network)
        assert isinstance(result, pd.DataFrame)
    
    def test_has_node_column(self, transport_network):
        """Test DataFrame has node column."""
        result = query_multiplex_pagerank(transport_network)
        assert 'node' in result.columns
    
    def test_has_multiplex_pagerank(self, transport_network):
        """Test DataFrame has multiplex_pagerank column."""
        result = query_multiplex_pagerank(transport_network)
        assert 'multiplex_pagerank' in result.columns
    
    def test_pagerank_positive(self, transport_network):
        """Test PageRank values are positive."""
        result = query_multiplex_pagerank(transport_network)
        assert (result['multiplex_pagerank'] > 0).all()
    
    def test_pagerank_normalized(self, transport_network):
        """Test PageRank values roughly sum to number of nodes."""
        result = query_multiplex_pagerank(transport_network)
        pr_sum = result['multiplex_pagerank'].sum()
        # Should be approximately 1.0 (average across layers)
        # Can be less if not all nodes appear in all layers
        assert 0.3 < pr_sum < 2.0  # Loose bounds for robustness


class TestRobustnessAnalysis:
    """Test robustness analysis query."""
    
    def test_returns_dataframe(self, transport_network):
        """Test query returns a DataFrame."""
        result = query_robustness_analysis(transport_network)
        assert isinstance(result, pd.DataFrame)
    
    def test_has_expected_columns(self, transport_network):
        """Test DataFrame has expected columns."""
        result = query_robustness_analysis(transport_network)
        expected_cols = ['scenario', 'n_nodes', 'avg_degree', 'total_edges', 'connectivity_loss']
        assert list(result.columns) == expected_cols
    
    def test_includes_baseline(self, transport_network):
        """Test result includes baseline scenario."""
        result = query_robustness_analysis(transport_network)
        assert any('baseline' in scenario.lower() for scenario in result['scenario'])
    
    def test_baseline_has_zero_loss(self, transport_network):
        """Test baseline scenario has 0% connectivity loss."""
        result = query_robustness_analysis(transport_network)
        baseline = result[result['scenario'].str.contains('baseline', case=False)]
        assert (baseline['connectivity_loss'] == 0.0).all()
    
    def test_connectivity_loss_in_valid_range(self, transport_network):
        """Test connectivity loss is between 0 and 100%."""
        result = query_robustness_analysis(transport_network)
        assert (result['connectivity_loss'] >= 0).all()
        assert (result['connectivity_loss'] <= 100).all()
    
    def test_removal_scenarios(self, transport_network):
        """Test that each layer has a removal scenario."""
        result = query_robustness_analysis(transport_network)
        layers = ['bus', 'metro', 'walking']
        for layer in layers:
            assert any(f'without {layer}' in scenario for scenario in result['scenario'])


class TestAdvancedCentralityComparison:
    """Test advanced centrality comparison query."""
    
    def test_returns_dataframe(self, communication_network):
        """Test query returns a DataFrame."""
        result = query_advanced_centrality_comparison(communication_network)
        assert isinstance(result, pd.DataFrame)
    
    def test_has_expected_columns(self, communication_network):
        """Test DataFrame has expected columns."""
        result = query_advanced_centrality_comparison(communication_network)
        expected_cols = ['node', 'degree', 'betweenness_centrality', 'closeness_centrality',
                         'pagerank', 'versatility', 'hub_type']
        assert list(result.columns) == expected_cols
    
    def test_versatility_in_valid_range(self, communication_network):
        """Test versatility is between 0 and number of centralities."""
        result = query_advanced_centrality_comparison(communication_network)
        assert (result['versatility'] >= 0).all()
        assert (result['versatility'] <= 4).all()  # 4 centrality measures
    
    def test_hub_types_valid(self, communication_network):
        """Test hub_type values are from expected set."""
        result = query_advanced_centrality_comparison(communication_network)
        valid_types = {'versatile_hub', 'specialized_hub', 'peripheral'}
        assert set(result['hub_type'].unique()).issubset(valid_types)
    
    def test_centralities_positive(self, communication_network):
        """Test all centrality values are non-negative."""
        result = query_advanced_centrality_comparison(communication_network)
        assert (result['degree'] >= 0).all()
        assert (result['betweenness_centrality'] >= 0).all()
        assert (result['closeness_centrality'] >= 0).all()
        assert (result['pagerank'] > 0).all()


class TestEdgeGroupingAndCoverage:
    """Tests for edge grouping and coverage query."""
    
    def test_returns_expected_structure(self, social_work_network):
        """Test result has expected dictionary structure."""
        result = query_edge_grouping_and_coverage(social_work_network, k=3)
        
        assert isinstance(result, dict)
        assert 'edges_by_pair' in result
        assert 'summary' in result
        
        # All should be DataFrames
        assert isinstance(result['edges_by_pair'], pd.DataFrame)
        assert isinstance(result['summary'], pd.DataFrame)
    
    def test_edges_has_expected_columns(self, social_work_network):
        """Test edges DataFrame has expected columns."""
        result = query_edge_grouping_and_coverage(social_work_network, k=3)
        df = result['edges_by_pair']
        
        if len(df) > 0:
            assert 'source' in df.columns
            assert 'target' in df.columns
            assert 'source_layer' in df.columns
            assert 'target_layer' in df.columns
    
    def test_summary_has_grouping_info(self, social_work_network):
        """Test summary has src_layer and dst_layer columns."""
        result = query_edge_grouping_and_coverage(social_work_network, k=3)
        summary = result['summary']
        
        if len(summary) > 0:
            assert 'src_layer' in summary.columns
            assert 'dst_layer' in summary.columns
            assert 'n_items' in summary.columns
    
    def test_top_k_parameter(self, social_work_network):
        """Test that k parameter affects number of edges per group."""
        result = query_edge_grouping_and_coverage(social_work_network, k=2)
        summary = result['summary']
        
        # Each group should have at most k edges
        if len(summary) > 0:
            assert all(summary['n_items'] <= 2)


class TestNullModelComparison:
    """Test null model comparison query."""
    
    def test_returns_dataframe(self, social_work_network):
        """Test query returns a DataFrame."""
        result = query_null_model_comparison(social_work_network)
        assert isinstance(result, pd.DataFrame)
    
    def test_has_expected_columns(self, social_work_network):
        """Test DataFrame has expected columns."""
        result = query_null_model_comparison(social_work_network)
        expected_cols = ['id', 'layer', 'degree', 'expected_degree', 'z_score', 'is_significant']
        assert list(result.columns) == expected_cols
    
    def test_z_scores_are_numeric(self, social_work_network):
        """Test z_scores are numeric values."""
        result = query_null_model_comparison(social_work_network)
        assert pd.api.types.is_numeric_dtype(result['z_score'])
    
    def test_is_significant_is_boolean(self, social_work_network):
        """Test is_significant is boolean."""
        result = query_null_model_comparison(social_work_network)
        assert result['is_significant'].dtype == bool


class TestBootstrapConfidenceIntervals:
    """Test bootstrap confidence intervals query."""
    
    def test_returns_dataframe(self, communication_network):
        """Test query returns a DataFrame."""
        result = query_bootstrap_confidence_intervals(communication_network)
        assert isinstance(result, pd.DataFrame)
    
    def test_has_expected_columns(self, communication_network):
        """Test DataFrame has expected columns."""
        result = query_bootstrap_confidence_intervals(communication_network)
        assert 'id' in result.columns
        assert 'mean' in result.columns
        assert 'std' in result.columns
        assert 'relative_variability' in result.columns
    
    def test_variability_positive(self, communication_network):
        """Test variability metrics are non-negative."""
        result = query_bootstrap_confidence_intervals(communication_network)
        assert (result['relative_variability'] >= 0).all()


class TestUncertaintyAwareRanking:
    """Test uncertainty-aware ranking query."""
    
    def test_returns_dataframe(self, transport_network):
        """Test query returns a DataFrame."""
        result = query_uncertainty_aware_ranking(transport_network)
        assert isinstance(result, pd.DataFrame)
    
    def test_has_ranking_columns(self, transport_network):
        """Test DataFrame has ranking columns."""
        result = query_uncertainty_aware_ranking(transport_network)
        assert 'rank_by_max' in result.columns
        assert 'rank_by_mean' in result.columns
        assert 'rank_by_consistency' in result.columns
    
    def test_ranks_are_positive(self, transport_network):
        """Test rank values are positive integers."""
        result = query_uncertainty_aware_ranking(transport_network)
        assert (result['rank_by_mean'] > 0).all()


# Integration test
class TestQueryZooIntegration:
    """Integration tests for the full Query Zoo."""
    
    def test_all_queries_run_on_all_datasets(self):
        """Test that all queries can run on all datasets without errors."""
        datasets = {
            'social_work': create_social_work_network(seed=42),
            'communication': create_communication_network(seed=42),
            'transport': create_transport_network(seed=42),
        }
        
        queries = [
            query_basic_exploration,
            lambda net: query_cross_layer_hubs(net, k=3),
            query_layer_similarity,
            query_community_structure,
            query_multiplex_pagerank,
            query_robustness_analysis,
            query_advanced_centrality_comparison,
            lambda net: query_edge_grouping_and_coverage(net, k=3),
            query_null_model_comparison,
            query_bootstrap_confidence_intervals,
            query_uncertainty_aware_ranking,
        ]
        
        for dataset_name, network in datasets.items():
            for query_func in queries:
                try:
                    result = query_func(network)
                    assert result is not None
                    # Most queries return DataFrames, except edge_grouping which returns dict
                    if query_func.__name__ == '<lambda>' and 'edge_grouping' in str(query_func):
                        assert isinstance(result, dict)
                    else:
                        assert isinstance(result, (pd.DataFrame, dict))
                except Exception as e:
                    pytest.fail(f"Query {query_func.__name__} failed on {dataset_name}: {e}")
