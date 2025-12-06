"""Property-based tests for the graph_ops module.

This module tests invariants and properties of the dplyr-style chainable
graph operations API including NodeFrame, EdgeFrame, and GroupedNodeFrame.
"""

import numpy as np
import pytest
from hypothesis import given, strategies as st, assume, settings

from py3plex.core import multinet
from py3plex.graph_ops import nodes, edges, NodeFrame


# ============================================================================
# Helper functions
# ============================================================================


def build_test_network(
    num_nodes: int = 6,
    num_layers: int = 2,
    edges_per_layer: int = 5,
) -> multinet.multi_layer_network:
    """Build a test multilayer network."""
    net = multinet.multi_layer_network(directed=False, verbose=False)
    edge_list = []
    layers = [f"L{i}" for i in range(num_layers)]

    for layer in layers:
        for i in range(min(edges_per_layer, num_nodes - 1)):
            edge_list.append([f"n{i}", layer, f"n{i+1}", layer, 1.0])

    if edge_list:
        net.add_edges(edge_list, input_type="list")
    return net


def count_nodes(net: multinet.multi_layer_network) -> int:
    """Count nodes in a network."""
    return sum(1 for _ in net.get_nodes())


# ============================================================================
# NodeFrame Creation Properties
# ============================================================================


class TestNodeFrameCreationProperties:
    """Property-based tests for creating NodeFrames."""

    def test_nodes_returns_nodeframe(self):
        """nodes() should return a NodeFrame."""
        net = build_test_network()
        frame = nodes(net)
        assert isinstance(frame, NodeFrame)

    def test_nodes_count_matches_network(self):
        """NodeFrame count should match network node count."""
        net = build_test_network()
        frame = nodes(net)
        assert frame.count() == count_nodes(net)

    @given(st.integers(min_value=1, max_value=4))
    @settings(max_examples=10)
    def test_nodes_with_layer_filter(self, num_layers: int):
        """nodes() with layers filter should only include those layers."""
        net = build_test_network(num_layers=num_layers)
        
        # Filter to first layer only
        frame = nodes(net, layers=["L0"])
        
        for node_dict in frame.collect():
            assert node_dict.get("layer") == "L0"


# ============================================================================
# NodeFrame Filter Properties
# ============================================================================


class TestNodeFrameFilterProperties:
    """Property-based tests for NodeFrame.filter()."""

    def test_filter_true_preserves_all(self):
        """Filtering with always-true should preserve all nodes."""
        net = build_test_network()
        frame = nodes(net)
        original_count = frame.count()
        
        filtered = frame.filter(lambda n: True)
        assert filtered.count() == original_count

    def test_filter_false_removes_all(self):
        """Filtering with always-false should remove all nodes."""
        net = build_test_network()
        frame = nodes(net)
        
        filtered = frame.filter(lambda n: False)
        assert filtered.count() == 0

    def test_filter_idempotent(self):
        """Filtering twice with same predicate is idempotent."""
        net = build_test_network()
        frame = nodes(net)
        
        # Filter once
        filtered1 = frame.filter(lambda n: n.get("degree", 0) > 0)
        count1 = filtered1.count()
        
        # Filter again with same predicate
        filtered2 = filtered1.filter(lambda n: n.get("degree", 0) > 0)
        count2 = filtered2.count()
        
        assert count1 == count2

    def test_filter_returns_new_frame(self):
        """filter() should return a new NodeFrame, not mutate the original."""
        net = build_test_network()
        frame = nodes(net)
        original_count = frame.count()
        
        _ = frame.filter(lambda n: n.get("degree", 0) > 100)
        
        # Original should be unchanged
        assert frame.count() == original_count

    @given(st.integers(min_value=-5, max_value=10))
    @settings(max_examples=15)
    def test_filter_degree_threshold(self, threshold: int):
        """Filtering by degree threshold should only include matching nodes."""
        net = build_test_network()
        frame = nodes(net)
        
        filtered = frame.filter(lambda n: n.get("degree", 0) > threshold)
        
        for node_dict in filtered.collect():
            assert node_dict.get("degree", 0) > threshold


# ============================================================================
# NodeFrame Select Properties
# ============================================================================


class TestNodeFrameSelectProperties:
    """Property-based tests for NodeFrame.select()."""

    def test_select_preserves_count(self):
        """select() should preserve the number of nodes."""
        net = build_test_network()
        frame = nodes(net)
        original_count = frame.count()
        
        selected = frame.select("id", "layer")
        assert selected.count() == original_count

    def test_select_limits_fields(self):
        """select() should limit fields to those requested."""
        net = build_test_network()
        frame = nodes(net)
        
        selected = frame.select("id", "layer")
        
        for node_dict in selected.collect():
            # Should only have selected fields (and nothing else non-internal)
            non_internal_keys = {k for k in node_dict.keys() if not k.startswith("_")}
            assert non_internal_keys.issubset({"id", "layer"})

    def test_select_empty_returns_copy(self):
        """select() with no args should return a copy."""
        net = build_test_network()
        frame = nodes(net)
        
        selected = frame.select()
        assert selected.count() == frame.count()


# ============================================================================
# NodeFrame Mutate Properties
# ============================================================================


class TestNodeFrameMutateProperties:
    """Property-based tests for NodeFrame.mutate()."""

    def test_mutate_preserves_count(self):
        """mutate() should preserve the number of nodes."""
        net = build_test_network()
        frame = nodes(net)
        original_count = frame.count()
        
        mutated = frame.mutate(new_field=lambda n: 42)
        assert mutated.count() == original_count

    def test_mutate_adds_field(self):
        """mutate() should add the new field."""
        net = build_test_network()
        frame = nodes(net)
        
        mutated = frame.mutate(my_value=lambda n: n.get("degree", 0) * 2)
        
        for node_dict in mutated.collect():
            assert "my_value" in node_dict

    @given(st.floats(min_value=0.1, max_value=10.0, allow_nan=False))
    @settings(max_examples=10)
    def test_mutate_computes_correctly(self, multiplier: float):
        """mutate() should compute values correctly."""
        net = build_test_network()
        frame = nodes(net)
        
        mutated = frame.mutate(scaled=lambda n: n.get("degree", 0) * multiplier)
        
        for node_dict in mutated.collect():
            expected = node_dict.get("degree", 0) * multiplier
            assert abs(node_dict["scaled"] - expected) < 1e-9

    def test_mutate_returns_new_frame(self):
        """mutate() should return a new NodeFrame, not mutate the original."""
        net = build_test_network()
        frame = nodes(net)
        
        mutated = frame.mutate(new_field=lambda n: 42)
        
        # Original should not have the new field
        for node_dict in frame.collect():
            assert "new_field" not in node_dict


# ============================================================================
# NodeFrame Arrange Properties
# ============================================================================


class TestNodeFrameArrangeProperties:
    """Property-based tests for NodeFrame.arrange()."""

    def test_arrange_preserves_count(self):
        """arrange() should preserve the number of nodes."""
        net = build_test_network()
        frame = nodes(net)
        original_count = frame.count()
        
        arranged = frame.arrange("degree")
        assert arranged.count() == original_count

    def test_arrange_ascending_order(self):
        """arrange() with reverse=False should sort ascending."""
        net = build_test_network()
        frame = nodes(net)
        
        arranged = frame.arrange("degree", reverse=False)
        degrees = arranged.pluck("degree")
        
        # Check that degrees are non-decreasing
        for i in range(len(degrees) - 1):
            assert degrees[i] <= degrees[i + 1]

    def test_arrange_descending_order(self):
        """arrange() with reverse=True should sort descending."""
        net = build_test_network()
        frame = nodes(net)
        
        arranged = frame.arrange("degree", reverse=True)
        degrees = arranged.pluck("degree")
        
        # Check that degrees are non-increasing
        for i in range(len(degrees) - 1):
            assert degrees[i] >= degrees[i + 1]


# ============================================================================
# NodeFrame Head/Tail Properties
# ============================================================================


class TestNodeFrameHeadTailProperties:
    """Property-based tests for NodeFrame.head() and tail()."""

    @given(st.integers(min_value=0, max_value=20))
    @settings(max_examples=15)
    def test_head_limits_count(self, n: int):
        """head(n) should return at most n nodes."""
        net = build_test_network()
        frame = nodes(net)
        
        result = frame.head(n)
        assert result.count() <= n

    @given(st.integers(min_value=0, max_value=20))
    @settings(max_examples=15)
    def test_tail_limits_count(self, n: int):
        """tail(n) should return at most n nodes."""
        net = build_test_network()
        frame = nodes(net)
        
        result = frame.tail(n)
        assert result.count() <= n

    def test_head_preserves_order(self):
        """head() should preserve the order from the beginning."""
        net = build_test_network()
        frame = nodes(net)
        all_nodes = frame.collect()
        
        if len(all_nodes) >= 3:
            result = frame.head(3)
            result_nodes = result.collect()
            
            for i in range(3):
                assert result_nodes[i]["id"] == all_nodes[i]["id"]

    def test_tail_preserves_order(self):
        """tail() should preserve the order from the end."""
        net = build_test_network()
        frame = nodes(net)
        all_nodes = frame.collect()
        
        if len(all_nodes) >= 3:
            result = frame.tail(3)
            result_nodes = result.collect()
            
            for i in range(3):
                assert result_nodes[i]["id"] == all_nodes[-3 + i]["id"]


# ============================================================================
# NodeFrame Chaining Properties
# ============================================================================


class TestNodeFrameChainingProperties:
    """Property-based tests for method chaining."""

    def test_chaining_operations(self):
        """Chained operations should work correctly."""
        net = build_test_network()
        
        result = (
            nodes(net)
            .filter(lambda n: n.get("degree", 0) >= 0)
            .mutate(double_degree=lambda n: n.get("degree", 0) * 2)
            .arrange("degree", reverse=True)
            .head(5)
        )
        
        assert result.count() <= 5
        
        for node_dict in result.collect():
            assert "double_degree" in node_dict
            assert node_dict["double_degree"] == node_dict.get("degree", 0) * 2

    def test_filter_then_filter_subset(self):
        """Filtering twice should be equivalent to AND of predicates."""
        net = build_test_network()
        frame = nodes(net)
        
        # Method 1: Chain two filters
        result1 = frame.filter(lambda n: n.get("degree", 0) >= 1).filter(
            lambda n: n.get("layer") == "L0"
        )
        
        # Method 2: Single combined filter
        result2 = frame.filter(
            lambda n: n.get("degree", 0) >= 1 and n.get("layer") == "L0"
        )
        
        assert result1.count() == result2.count()


# ============================================================================
# NodeFrame Terminal Operations Properties
# ============================================================================


class TestNodeFrameTerminalProperties:
    """Property-based tests for terminal operations."""

    def test_count_non_negative(self):
        """count() should return a non-negative integer."""
        net = build_test_network()
        frame = nodes(net)
        
        assert frame.count() >= 0

    def test_collect_returns_list(self):
        """collect() should return a list."""
        net = build_test_network()
        frame = nodes(net)
        
        result = frame.collect()
        assert isinstance(result, list)

    def test_first_returns_first_item(self):
        """first() should return the first item or None."""
        net = build_test_network()
        frame = nodes(net)
        
        first = frame.first()
        if frame.count() > 0:
            assert first is not None
            assert first == frame.collect()[0]
        else:
            assert first is None

    def test_last_returns_last_item(self):
        """last() should return the last item or None."""
        net = build_test_network()
        frame = nodes(net)
        
        last = frame.last()
        if frame.count() > 0:
            assert last is not None
            assert last == frame.collect()[-1]
        else:
            assert last is None

    def test_pluck_extracts_values(self):
        """pluck() should extract values for the specified field."""
        net = build_test_network()
        frame = nodes(net)
        
        ids = frame.pluck("id")
        
        assert isinstance(ids, list)
        assert len(ids) == frame.count()


# ============================================================================
# NodeFrame Distinct Properties
# ============================================================================


class TestNodeFrameDistinctProperties:
    """Property-based tests for NodeFrame.distinct()."""

    def test_distinct_preserves_or_reduces_count(self):
        """distinct() should preserve or reduce count."""
        net = build_test_network()
        frame = nodes(net)
        original_count = frame.count()
        
        result = frame.distinct("id")
        assert result.count() <= original_count

    def test_distinct_idempotent(self):
        """Calling distinct() twice should be idempotent."""
        net = build_test_network()
        frame = nodes(net)
        
        result1 = frame.distinct("id")
        result2 = result1.distinct("id")
        
        assert result1.count() == result2.count()


# ============================================================================
# NodeFrame Sample Properties
# ============================================================================


class TestNodeFrameSampleProperties:
    """Property-based tests for NodeFrame.sample()."""

    @given(st.integers(min_value=1, max_value=20))
    @settings(max_examples=10)
    def test_sample_limits_count(self, n: int):
        """sample(n) should return at most n nodes."""
        net = build_test_network()
        frame = nodes(net)
        
        result = frame.sample(n)
        assert result.count() <= n
        assert result.count() <= frame.count()

    @given(st.integers(min_value=0, max_value=2**31 - 1))
    @settings(max_examples=10)
    def test_sample_reproducibility(self, seed: int):
        """sample() with same seed should return same results."""
        net = build_test_network()
        frame = nodes(net)
        
        result1 = frame.sample(3, seed=seed)
        result2 = frame.sample(3, seed=seed)
        
        ids1 = result1.pluck("id")
        ids2 = result2.pluck("id")
        
        assert ids1 == ids2


# ============================================================================
# NodeFrame Rename and Drop Properties
# ============================================================================


class TestNodeFrameRenameDropProperties:
    """Property-based tests for rename() and drop()."""

    def test_rename_changes_field_name(self):
        """rename() should change field names."""
        net = build_test_network()
        frame = nodes(net)
        
        result = frame.rename(id="node_id")
        
        for node_dict in result.collect():
            assert "node_id" in node_dict
            assert "id" not in node_dict

    def test_drop_removes_field(self):
        """drop() should remove specified fields."""
        net = build_test_network()
        frame = nodes(net)
        
        result = frame.drop("degree")
        
        for node_dict in result.collect():
            assert "degree" not in node_dict


# ============================================================================
# GroupedNodeFrame Properties
# ============================================================================


class TestGroupedNodeFrameProperties:
    """Property-based tests for GroupedNodeFrame."""

    def test_group_by_returns_grouped_frame(self):
        """group_by() should return a GroupedNodeFrame."""
        net = build_test_network()
        frame = nodes(net)
        
        grouped = frame.group_by("layer")
        
        # GroupedNodeFrame should have summarise method
        assert hasattr(grouped, "summarise")

    def test_summarise_returns_nodeframe(self):
        """summarise() should return a NodeFrame."""
        net = build_test_network()
        frame = nodes(net)
        
        result = frame.group_by("layer").summarise(
            count=("id", len),
        )
        
        assert isinstance(result, NodeFrame)

    def test_summarise_aggregates_correctly(self):
        """summarise() should compute aggregations correctly."""
        net = build_test_network(num_layers=2)
        frame = nodes(net)
        
        result = frame.group_by("layer").summarise(
            count=("id", len),
        )
        
        # Should have one row per layer
        layer_count = len(set(frame.pluck("layer")))
        assert result.count() == layer_count


# ============================================================================
# EdgeFrame Properties
# ============================================================================


class TestEdgeFrameProperties:
    """Property-based tests for EdgeFrame."""

    def test_edges_returns_edgeframe(self):
        """edges() should return an EdgeFrame."""
        net = build_test_network()
        edge_frame = edges(net)
        
        # EdgeFrame should have similar methods to NodeFrame
        assert hasattr(edge_frame, "filter")
        assert hasattr(edge_frame, "head")
        assert hasattr(edge_frame, "collect")

    def test_edges_count_matches_network(self):
        """EdgeFrame count should match network edge count."""
        net = build_test_network()
        edge_frame = edges(net)
        
        # Count edges in the network
        network_edge_count = sum(1 for _ in net.get_edges())
        
        assert edge_frame.count() == network_edge_count


# ============================================================================
# to_pandas Properties
# ============================================================================


class TestToPandasProperties:
    """Property-based tests for to_pandas() conversion."""

    def test_to_pandas_returns_dataframe(self):
        """to_pandas() should return a pandas DataFrame."""
        import pandas as pd
        
        net = build_test_network()
        frame = nodes(net)
        
        df = frame.to_pandas()
        
        assert isinstance(df, pd.DataFrame)

    def test_to_pandas_row_count_matches(self):
        """to_pandas() row count should match NodeFrame count."""
        net = build_test_network()
        frame = nodes(net)
        
        df = frame.to_pandas()
        
        assert len(df) == frame.count()

    def test_to_pandas_excludes_internal_fields(self):
        """to_pandas() should exclude internal fields (starting with _)."""
        net = build_test_network()
        frame = nodes(net)
        
        df = frame.to_pandas()
        
        for col in df.columns:
            assert not col.startswith("_")

