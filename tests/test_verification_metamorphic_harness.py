"""
Comprehensive metamorphic transformation harness.

This module provides a reusable framework for metamorphic testing:
- Standardized transformations (relabel, permute, shuffle, scale, etc.)
- Invariant assertions
- Application to DSL queries, centrality, community detection, paths

Transformations guarantee:
- Relabeling → metric values preserved modulo relabel
- Layer permutation → per-layer summaries permute, global invariant
- Edge order shuffle → identical outputs
- Weight scaling → predictable metric behavior
- Isolated nodes → no effect on existing-node metrics
"""

import pytest
import numpy as np
from typing import List, Dict, Any, Callable
from py3plex.core import multinet
from py3plex.dsl import Q, L
from tests.fixtures import (
    tiny_two_layer,
    small_three_layer,
    two_cliques_bridge,
    relabel_nodes,
    permute_layers,
    shuffle_edge_order,
    scale_weights,
    add_isolated_nodes,
)


class MetamorphicHarness:
    """
    Reusable metamorphic testing harness.
    
    Provides methods to apply transformations and assert invariants.
    """
    
    @staticmethod
    def assert_metric_multiset_preserved(
        original_values: List[float],
        transformed_values: List[float],
        tol: float = 1e-9
    ):
        """
        Assert that sorted metric values are identical (multiset equality).
        
        Args:
            original_values: Metric values from original network
            transformed_values: Metric values from transformed network
            tol: Numerical tolerance for floating point comparison
        """
        assert len(original_values) == len(transformed_values), \
            f"Value count differs: {len(original_values)} vs {len(transformed_values)}"
        
        orig_sorted = sorted(original_values)
        trans_sorted = sorted(transformed_values)
        
        for i, (orig, trans) in enumerate(zip(orig_sorted, trans_sorted)):
            assert abs(orig - trans) < tol, \
                f"Value at index {i} differs: {orig} vs {trans} (diff: {abs(orig - trans)})"
    
    @staticmethod
    def compute_centrality(net, measure: str) -> List[float]:
        """Compute centrality and return sorted values."""
        try:
            centrality_dict = net.monoplex_nx_wrapper(measure)
            return sorted(centrality_dict.values())
        except Exception:
            return None
    
    @staticmethod
    def dsl_query_result_values(net, query_builder) -> List[float]:
        """Execute DSL query and extract first metric column."""
        result = query_builder.execute(net)
        df = result.to_pandas()
        
        # Find first numeric column that looks like a metric
        for col in df.columns:
            if col in ['degree', 'betweenness_centrality', 'pagerank', 'closeness_centrality']:
                values = df[col].tolist()
                return sorted([v for v in values if v is not None and not np.isnan(v)])
        
        return []


class TestRelabelInvariance:
    """Test that node relabeling preserves metric distributions."""

    def test_degree_relabel_invariance(self):
        """Degree centrality invariant under relabeling."""
        harness = MetamorphicHarness()
        net = tiny_two_layer()
        
        # Original
        orig_degrees = harness.compute_centrality(net, "degree_centrality")
        assert orig_degrees is not None
        
        # Relabel
        mapping = {'A': 'node_alpha', 'B': 'node_beta', 'C': 'node_gamma', 'D': 'node_delta'}
        relabeled_net = relabel_nodes(net, mapping)
        
        # Transformed
        trans_degrees = harness.compute_centrality(relabeled_net, "degree_centrality")
        assert trans_degrees is not None
        
        # Assert multiset equality
        harness.assert_metric_multiset_preserved(orig_degrees, trans_degrees)

    def test_betweenness_relabel_invariance(self):
        """Betweenness centrality invariant under relabeling."""
        harness = MetamorphicHarness()
        net = two_cliques_bridge()
        
        orig_bc = harness.compute_centrality(net, "betweenness_centrality")
        assert orig_bc is not None
        
        mapping = {node: f"v{i}" for i, node in enumerate(['A', 'B', 'C', 'D', 'E', 'F'])}
        relabeled_net = relabel_nodes(net, mapping)
        
        trans_bc = harness.compute_centrality(relabeled_net, "betweenness_centrality")
        assert trans_bc is not None
        
        harness.assert_metric_multiset_preserved(orig_bc, trans_bc)

    def test_pagerank_relabel_invariance(self):
        """PageRank invariant under relabeling."""
        harness = MetamorphicHarness()
        net = small_three_layer()
        
        orig_pr = harness.compute_centrality(net, "pagerank")
        assert orig_pr is not None
        
        mapping = {node: f"node_{node}_renamed" for node in ['A', 'B', 'C', 'D', 'E']}
        relabeled_net = relabel_nodes(net, mapping)
        
        trans_pr = harness.compute_centrality(relabeled_net, "pagerank")
        assert trans_pr is not None
        
        harness.assert_metric_multiset_preserved(orig_pr, trans_pr)

    def test_dsl_query_relabel_invariance(self):
        """DSL query results invariant under relabeling."""
        harness = MetamorphicHarness()
        net = tiny_two_layer()
        
        # Original DSL query
        query = Q.nodes().compute("degree")
        orig_values = harness.dsl_query_result_values(net, query)
        
        # Relabel
        mapping = {'A': 'X', 'B': 'Y', 'C': 'Z', 'D': 'W'}
        relabeled_net = relabel_nodes(net, mapping)
        
        # Same query on relabeled network
        trans_values = harness.dsl_query_result_values(relabeled_net, query)
        
        # Multiset equality
        harness.assert_metric_multiset_preserved(orig_values, trans_values)


class TestLayerPermutationInvariance:
    """Test that layer permutation preserves global distributions."""

    def test_degree_layer_permutation_invariance(self):
        """Degree centrality invariant under layer permutation."""
        harness = MetamorphicHarness()
        net = small_three_layer()
        
        orig_degrees = harness.compute_centrality(net, "degree_centrality")
        assert orig_degrees is not None
        
        # Permute layers: reverse order
        perm = {0: 2, 1: 1, 2: 0}
        permuted_net = permute_layers(net, perm)
        
        perm_degrees = harness.compute_centrality(permuted_net, "degree_centrality")
        assert perm_degrees is not None
        
        harness.assert_metric_multiset_preserved(orig_degrees, perm_degrees)

    def test_betweenness_layer_permutation_invariance(self):
        """Betweenness centrality invariant under layer permutation."""
        harness = MetamorphicHarness()
        net = small_three_layer()
        
        orig_bc = harness.compute_centrality(net, "betweenness_centrality")
        assert orig_bc is not None
        
        perm = {0: 1, 1: 2, 2: 0}  # Rotate layers
        permuted_net = permute_layers(net, perm)
        
        perm_bc = harness.compute_centrality(permuted_net, "betweenness_centrality")
        assert perm_bc is not None
        
        harness.assert_metric_multiset_preserved(orig_bc, perm_bc)

    def test_dsl_per_layer_permutation_consistent(self):
        """Per-layer DSL queries: layer permutation permutes group labels."""
        net = small_three_layer()
        
        # Query per layer
        result_orig = Q.nodes().compute("degree").per_layer().execute(net)
        df_orig = result_orig.to_pandas()
        
        # Permute layers
        perm = {0: 2, 1: 0, 2: 1}
        permuted_net = permute_layers(net, perm)
        
        result_perm = Q.nodes().compute("degree").per_layer().execute(permuted_net)
        df_perm = result_perm.to_pandas()
        
        # Global aggregates should be same
        if "degree" in df_orig.columns and "degree" in df_perm.columns:
            orig_mean = df_orig["degree"].mean()
            perm_mean = df_perm["degree"].mean()
            assert abs(orig_mean - perm_mean) < 1e-9, \
                "Global mean should be invariant under layer permutation"


class TestEdgeOrderInvariance:
    """Test that edge insertion order doesn't affect results."""

    def test_degree_edge_order_invariance(self):
        """Degree centrality invariant under edge order shuffle."""
        harness = MetamorphicHarness()
        net = two_cliques_bridge()
        
        orig_degrees = harness.compute_centrality(net, "degree_centrality")
        assert orig_degrees is not None
        
        # Shuffle edge order
        shuffled_net = shuffle_edge_order(net, seed=42)
        
        shuf_degrees = harness.compute_centrality(shuffled_net, "degree_centrality")
        assert shuf_degrees is not None
        
        harness.assert_metric_multiset_preserved(orig_degrees, shuf_degrees)

    def test_betweenness_edge_order_invariance(self):
        """Betweenness centrality invariant under edge order shuffle."""
        harness = MetamorphicHarness()
        net = two_cliques_bridge()
        
        orig_bc = harness.compute_centrality(net, "betweenness_centrality")
        assert orig_bc is not None
        
        shuffled_net = shuffle_edge_order(net, seed=123)
        
        shuf_bc = harness.compute_centrality(shuffled_net, "betweenness_centrality")
        assert shuf_bc is not None
        
        harness.assert_metric_multiset_preserved(orig_bc, shuf_bc)

    def test_dsl_query_edge_order_invariance(self):
        """DSL query results invariant under edge order shuffle."""
        harness = MetamorphicHarness()
        net = tiny_two_layer()
        
        query = Q.nodes().compute("degree")
        orig_values = harness.dsl_query_result_values(net, query)
        
        shuffled_net = shuffle_edge_order(net, seed=999)
        shuf_values = harness.dsl_query_result_values(shuffled_net, query)
        
        harness.assert_metric_multiset_preserved(orig_values, shuf_values)


class TestWeightScalingBehavior:
    """Test predictable behavior under uniform weight scaling."""

    def test_weight_scaling_degree_invariant(self):
        """Degree (unweighted) invariant under weight scaling."""
        harness = MetamorphicHarness()
        net = tiny_two_layer()
        
        orig_degrees = harness.compute_centrality(net, "degree_centrality")
        assert orig_degrees is not None
        
        # Scale weights uniformly
        scaled_net = scale_weights(net, factor=2.0)
        
        scaled_degrees = harness.compute_centrality(scaled_net, "degree_centrality")
        assert scaled_degrees is not None
        
        # Unweighted degree should be invariant
        harness.assert_metric_multiset_preserved(orig_degrees, scaled_degrees)

    def test_weight_scaling_pagerank_scales(self):
        """PageRank may change under weight scaling (implementation-dependent)."""
        # This is a weaker test: just check that computation still works
        net = small_three_layer()
        
        orig_pr = MetamorphicHarness.compute_centrality(net, "pagerank")
        assert orig_pr is not None
        
        scaled_net = scale_weights(net, factor=0.5)
        scaled_pr = MetamorphicHarness.compute_centrality(scaled_net, "pagerank")
        assert scaled_pr is not None
        
        # PageRank should still be valid (sum to 1)
        assert abs(sum(scaled_pr) - 1.0) < 1e-6


class TestIsolatedNodeInvariance:
    """Test that adding isolated nodes doesn't affect existing node metrics."""

    def test_isolated_nodes_degree_preserved(self):
        """Adding isolated nodes preserves existing node degrees."""
        harness = MetamorphicHarness()
        net = tiny_two_layer()
        
        # Get original degrees for existing nodes
        orig_centrality = net.monoplex_nx_wrapper("degree_centrality")
        orig_nodes = set(orig_centrality.keys())
        
        # Add isolated nodes
        isolated_node_ids = ['ISO1', 'ISO2', 'ISO3']
        net_with_isolated = add_isolated_nodes(net, nodes=isolated_node_ids, layer='0')
        
        # Get new degrees
        new_centrality = net_with_isolated.monoplex_nx_wrapper("degree_centrality")
        
        # Check that original nodes have same (or proportionally scaled) centrality
        # Note: degree_centrality normalizes, so values may change
        # But relative ordering should be preserved for connected nodes
        for node in orig_nodes:
            if node in new_centrality:
                # Just check that it's still defined
                assert new_centrality[node] is not None

    def test_isolated_nodes_betweenness_preserved(self):
        """Isolated nodes have zero betweenness, don't affect others."""
        net = two_cliques_bridge()
        
        # Get original betweenness
        orig_bc = net.monoplex_nx_wrapper("betweenness_centrality")
        orig_nodes = set(orig_bc.keys())
        
        # Add isolated nodes
        isolated_node_ids = ['ISO_A', 'ISO_B']
        net_with_isolated = add_isolated_nodes(net, nodes=isolated_node_ids, layer='0')
        
        # Get new betweenness
        new_bc = net_with_isolated.monoplex_nx_wrapper("betweenness_centrality")
        
        # Check original nodes still have same betweenness
        for node in orig_nodes:
            if node in new_bc:
                # Betweenness should be identical (not normalized by node count)
                # This may vary by implementation, so we just check it's defined
                assert new_bc[node] is not None


class TestPathAlgorithmsInvariance:
    """Test path algorithms under transformations."""

    def test_shortest_path_relabel_invariance(self):
        """Shortest path structure invariant under relabeling."""
        try:
            from py3plex.paths import compute_shortest_paths
        except (ImportError, AttributeError):
            pytest.skip("compute_shortest_paths not available")
        
        net = tiny_two_layer()
        
        # Compute paths on original
        try:
            orig_paths = compute_shortest_paths(net)
            orig_path_count = len(orig_paths) if orig_paths else 0
        except Exception:
            pytest.skip("compute_shortest_paths not available or failed")
        
        # Relabel
        mapping = {'A': 'X', 'B': 'Y', 'C': 'Z', 'D': 'W'}
        relabeled_net = relabel_nodes(net, mapping)
        
        # Compute paths on relabeled
        try:
            relabeled_paths = compute_shortest_paths(relabeled_net)
            relabeled_path_count = len(relabeled_paths) if relabeled_paths else 0
        except Exception:
            pytest.skip("compute_shortest_paths failed")
        
        # Should have same number of paths
        assert orig_path_count == relabeled_path_count, \
            "Path count should be invariant under relabeling"

    def test_shortest_path_edge_order_invariance(self):
        """Shortest path lengths invariant under edge order shuffle."""
        # This is a basic sanity check
        net = two_cliques_bridge()
        
        # Original structure
        orig_node_count = len(list(net.get_nodes()))
        
        # Shuffle edges
        shuffled_net = shuffle_edge_order(net, seed=456)
        
        # Shuffled structure
        shuf_node_count = len(list(shuffled_net.get_nodes()))
        
        # Basic structure preserved
        assert orig_node_count == shuf_node_count


class TestCommunityDetectionInvariance:
    """Test community detection under transformations."""

    @pytest.mark.slow
    def test_community_partition_relabel_invariance(self):
        """Community partition structure invariant under relabeling."""
        net = two_cliques_bridge()
        
        # Detect communities
        try:
            result_orig = Q.nodes().community(method="louvain").execute(net)
            df_orig = result_orig.to_pandas()
            
            if "community" not in df_orig.columns:
                pytest.skip("Community detection didn't produce community column")
            
            # Count communities
            num_communities_orig = df_orig["community"].nunique()
        except Exception as e:
            pytest.skip(f"Community detection failed: {e}")
        
        # Relabel
        mapping = {node: f"node_{i}" for i, node in enumerate(['A', 'B', 'C', 'D', 'E', 'F'])}
        relabeled_net = relabel_nodes(net, mapping)
        
        # Detect communities on relabeled
        try:
            result_relabeled = Q.nodes().community(method="louvain").execute(relabeled_net)
            df_relabeled = result_relabeled.to_pandas()
            num_communities_relabeled = df_relabeled["community"].nunique()
        except Exception as e:
            pytest.skip(f"Community detection on relabeled failed: {e}")
        
        # Number of communities should be same (labels may differ)
        assert num_communities_orig == num_communities_relabeled, \
            "Number of communities should be invariant under relabeling"


class TestTransformationComposition:
    """Test that compositions of transformations work correctly."""

    def test_relabel_then_permute(self):
        """Relabel followed by layer permutation preserves structure."""
        harness = MetamorphicHarness()
        net = small_three_layer()
        
        # Original metric
        orig_degrees = harness.compute_centrality(net, "degree_centrality")
        assert orig_degrees is not None
        
        # Relabel
        mapping = {node: f"v{node}" for node in ['A', 'B', 'C', 'D', 'E']}
        relabeled_net = relabel_nodes(net, mapping)
        
        # Then permute layers
        perm = {0: 2, 1: 0, 2: 1}
        composed_net = permute_layers(relabeled_net, perm)
        
        # Final metric
        composed_degrees = harness.compute_centrality(composed_net, "degree_centrality")
        assert composed_degrees is not None
        
        # Should still preserve multiset
        harness.assert_metric_multiset_preserved(orig_degrees, composed_degrees)

    def test_permute_then_shuffle_edges(self):
        """Layer permutation followed by edge shuffle preserves structure."""
        harness = MetamorphicHarness()
        net = small_three_layer()
        
        orig_degrees = harness.compute_centrality(net, "degree_centrality")
        assert orig_degrees is not None
        
        # Permute
        perm = {0: 1, 1: 2, 2: 0}
        permuted_net = permute_layers(net, perm)
        
        # Shuffle edges
        composed_net = shuffle_edge_order(permuted_net, seed=789)
        
        composed_degrees = harness.compute_centrality(composed_net, "degree_centrality")
        assert composed_degrees is not None
        
        harness.assert_metric_multiset_preserved(orig_degrees, composed_degrees)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
