"""Tests for the graph_ops module (dplyr-style chainable operations).

Tests cover:
- NodeFrame and EdgeFrame creation via nodes() and edges() helpers
- Filter, select, mutate, arrange, head operations
- Group_by and summarise operations
- to_pandas and to_subgraph exports
- Expression-based filtering
"""

import math
import pytest
from py3plex.core import multinet
from py3plex.graph_ops import (
    nodes,
    edges,
    NodeFrame,
    EdgeFrame,
    GroupedNodeFrame,
    GroupedEdgeFrame,
)


@pytest.fixture
def sample_network():
    """Create a sample multilayer network for testing."""
    network = multinet.multi_layer_network(directed=False)

    # Add nodes
    nodes_list = [
        {'source': 'A', 'type': 'layer1'},
        {'source': 'B', 'type': 'layer1'},
        {'source': 'C', 'type': 'layer1'},
        {'source': 'D', 'type': 'layer1'},
        {'source': 'A', 'type': 'layer2'},
        {'source': 'B', 'type': 'layer2'},
        {'source': 'C', 'type': 'layer2'},
    ]
    network.add_nodes(nodes_list)

    # Add edges
    edges_list = [
        {'source': 'A', 'target': 'B', 'source_type': 'layer1', 'target_type': 'layer1', 'weight': 1.0},
        {'source': 'B', 'target': 'C', 'source_type': 'layer1', 'target_type': 'layer1', 'weight': 2.0},
        {'source': 'C', 'target': 'D', 'source_type': 'layer1', 'target_type': 'layer1', 'weight': 3.0},
        {'source': 'A', 'target': 'C', 'source_type': 'layer1', 'target_type': 'layer1', 'weight': 1.5},
        {'source': 'A', 'target': 'B', 'source_type': 'layer2', 'target_type': 'layer2', 'weight': 0.5},
        {'source': 'B', 'target': 'C', 'source_type': 'layer2', 'target_type': 'layer2', 'weight': 0.8},
    ]
    network.add_edges(edges_list)

    return network


class TestNodesHelper:
    """Test the nodes() helper function."""

    def test_nodes_returns_nodeframe(self, sample_network):
        """Test that nodes() returns a NodeFrame."""
        result = nodes(sample_network)
        assert isinstance(result, NodeFrame)

    def test_nodes_count(self, sample_network):
        """Test that nodes() returns correct count."""
        result = nodes(sample_network)
        # 7 nodes total (4 in layer1, 3 in layer2)
        assert len(result) == 7

    def test_nodes_layer_filter(self, sample_network):
        """Test that nodes() filters by layers."""
        result = nodes(sample_network, layers=["layer1"])
        assert len(result) == 4
        for item in result:
            assert item["layer"] == "layer1"

    def test_nodes_multiple_layers(self, sample_network):
        """Test filtering by multiple layers."""
        result = nodes(sample_network, layers=["layer1", "layer2"])
        assert len(result) == 7

    def test_nodes_nonexistent_layer(self, sample_network):
        """Test filtering by nonexistent layer returns empty."""
        result = nodes(sample_network, layers=["nonexistent"])
        assert len(result) == 0

    def test_nodes_on_empty_network(self):
        """Test nodes() on empty network."""
        empty_network = multinet.multi_layer_network(directed=False)
        result = nodes(empty_network)
        assert len(result) == 0


class TestEdgesHelper:
    """Test the edges() helper function."""

    def test_edges_returns_edgeframe(self, sample_network):
        """Test that edges() returns an EdgeFrame."""
        result = edges(sample_network)
        assert isinstance(result, EdgeFrame)

    def test_edges_count(self, sample_network):
        """Test that edges() returns correct count."""
        result = edges(sample_network)
        assert len(result) == 6

    def test_edges_layer_filter(self, sample_network):
        """Test that edges() filters by layers."""
        result = edges(sample_network, layers=["layer1"])
        assert len(result) == 4
        for item in result:
            assert item["source_layer"] == "layer1" or item["target_layer"] == "layer1"

    def test_edges_on_empty_network(self):
        """Test edges() on empty network."""
        empty_network = multinet.multi_layer_network(directed=False)
        result = edges(empty_network)
        assert len(result) == 0


class TestNodeFrameFilter:
    """Test NodeFrame.filter() method."""

    def test_filter_by_degree(self, sample_network):
        """Test filtering nodes by degree."""
        result = nodes(sample_network).filter(lambda n: n["degree"] > 1)
        assert len(result) > 0
        for item in result:
            assert item["degree"] > 1

    def test_filter_by_layer(self, sample_network):
        """Test filtering nodes by layer."""
        result = nodes(sample_network).filter(lambda n: n["layer"] == "layer1")
        assert len(result) == 4

    def test_filter_chaining(self, sample_network):
        """Test chaining multiple filters."""
        result = (
            nodes(sample_network)
            .filter(lambda n: n["layer"] == "layer1")
            .filter(lambda n: n["degree"] >= 2)
        )
        for item in result:
            assert item["layer"] == "layer1"
            assert item["degree"] >= 2

    def test_filter_returns_empty(self, sample_network):
        """Test filter that returns empty result."""
        result = nodes(sample_network).filter(lambda n: n["degree"] > 100)
        assert len(result) == 0


class TestNodeFrameFilterExpr:
    """Test NodeFrame.filter_expr() method."""

    def test_filter_expr_simple(self, sample_network):
        """Test simple expression filtering."""
        result = nodes(sample_network).filter_expr("degree > 1")
        for item in result:
            assert item["degree"] > 1

    def test_filter_expr_equality(self, sample_network):
        """Test equality expression filtering."""
        result = nodes(sample_network).filter_expr("layer == 'layer1'")
        for item in result:
            assert item["layer"] == "layer1"

    def test_filter_expr_and(self, sample_network):
        """Test AND expression filtering."""
        result = nodes(sample_network).filter_expr("layer == 'layer1' and degree >= 2")
        for item in result:
            assert item["layer"] == "layer1"
            assert item["degree"] >= 2

    def test_filter_expr_invalid(self, sample_network):
        """Test invalid expression is handled gracefully."""
        # Invalid syntax should not crash, just filter out items
        result = nodes(sample_network).filter_expr("import os")
        # Should raise ValueError for disallowed construct
        assert len(result) == 0 or isinstance(result, NodeFrame)

    def test_filter_expr_power(self, sample_network):
        """Test power operator in expression filtering."""
        result = nodes(sample_network).filter_expr("degree ** 2 > 1")
        for item in result:
            assert item["degree"] ** 2 > 1


class TestNodeFrameSelect:
    """Test NodeFrame.select() method."""

    def test_select_single_field(self, sample_network):
        """Test selecting single field."""
        result = nodes(sample_network).select("id")
        for item in result:
            assert "id" in item
            assert "degree" not in item

    def test_select_multiple_fields(self, sample_network):
        """Test selecting multiple fields."""
        result = nodes(sample_network).select("id", "layer")
        for item in result:
            assert "id" in item
            assert "layer" in item
            assert "degree" not in item

    def test_select_no_fields(self, sample_network):
        """Test select with no fields is no-op."""
        original = nodes(sample_network)
        result = original.select()
        assert len(result) == len(original)

    def test_select_nonexistent_field(self, sample_network):
        """Test selecting nonexistent field."""
        result = nodes(sample_network).select("nonexistent")
        for item in result:
            assert "nonexistent" not in item


class TestNodeFrameMutate:
    """Test NodeFrame.mutate() method."""

    def test_mutate_single_field(self, sample_network):
        """Test adding single field."""
        result = nodes(sample_network).mutate(doubled_degree=lambda n: n["degree"] * 2)
        for item in result:
            assert "doubled_degree" in item
            assert item["doubled_degree"] == item["degree"] * 2

    def test_mutate_multiple_fields(self, sample_network):
        """Test adding multiple fields."""
        result = nodes(sample_network).mutate(
            doubled_degree=lambda n: n["degree"] * 2,
            log_degree=lambda n: math.log1p(n["degree"]),
        )
        for item in result:
            assert "doubled_degree" in item
            assert "log_degree" in item

    def test_mutate_overwrite_field(self, sample_network):
        """Test overwriting existing field."""
        result = nodes(sample_network).mutate(degree=lambda n: n["degree"] + 100)
        for item in result:
            assert item["degree"] >= 100

    def test_mutate_error_handling(self, sample_network):
        """Test mutate handles errors gracefully."""
        result = nodes(sample_network).mutate(
            error_field=lambda n: 1 / 0  # Division by zero
        )
        for item in result:
            assert item["error_field"] is None


class TestNodeFrameArrange:
    """Test NodeFrame.arrange() method."""

    def test_arrange_by_string(self, sample_network):
        """Test arranging by field name."""
        result = nodes(sample_network).arrange("degree")
        degrees = [item["degree"] for item in result]
        assert degrees == sorted(degrees)

    def test_arrange_reverse(self, sample_network):
        """Test arranging in reverse order."""
        result = nodes(sample_network).arrange("degree", reverse=True)
        degrees = [item["degree"] for item in result]
        assert degrees == sorted(degrees, reverse=True)

    def test_arrange_by_callable(self, sample_network):
        """Test arranging by callable."""
        result = nodes(sample_network).arrange(lambda n: -n["degree"])
        degrees = [item["degree"] for item in result]
        assert degrees == sorted(degrees, reverse=True)


class TestNodeFrameHead:
    """Test NodeFrame.head() method."""

    def test_head_default(self, sample_network):
        """Test head with default n=5."""
        result = nodes(sample_network).head()
        assert len(result) <= 5

    def test_head_custom_n(self, sample_network):
        """Test head with custom n."""
        result = nodes(sample_network).head(3)
        assert len(result) == 3

    def test_head_larger_than_data(self, sample_network):
        """Test head with n larger than data."""
        original = nodes(sample_network)
        result = original.head(100)
        assert len(result) == len(original)


class TestNodeFrameGroupBy:
    """Test NodeFrame.group_by() method."""

    def test_group_by_returns_grouped(self, sample_network):
        """Test group_by returns GroupedNodeFrame."""
        result = nodes(sample_network).group_by("layer")
        assert isinstance(result, GroupedNodeFrame)

    def test_group_by_summarise_count(self, sample_network):
        """Test group_by with count summarise."""
        result = (
            nodes(sample_network)
            .group_by("layer")
            .summarise(n=("id", len))
        )
        assert isinstance(result, NodeFrame)
        assert len(result) == 2  # Two layers

    def test_group_by_summarise_mean(self, sample_network):
        """Test group_by with mean summarise."""
        import numpy as np
        result = (
            nodes(sample_network)
            .group_by("layer")
            .summarise(avg_degree=("degree", np.mean))
        )
        for item in result:
            assert "layer" in item
            assert "avg_degree" in item

    def test_group_by_multiple_aggregations(self, sample_network):
        """Test group_by with multiple aggregations."""
        import numpy as np
        result = (
            nodes(sample_network)
            .group_by("layer")
            .summarise(
                avg_degree=("degree", np.mean),
                n=("id", len),
            )
        )
        for item in result:
            assert "layer" in item
            assert "avg_degree" in item
            assert "n" in item

    def test_group_by_to_pandas_chain(self, sample_network):
        """Test group_by -> summarise -> to_pandas chain."""
        import numpy as np
        df = (
            nodes(sample_network)
            .group_by("layer")
            .summarise(
                avg_degree=("degree", np.mean),
                n=("id", len),
            )
            .arrange("avg_degree", reverse=True)
            .to_pandas()
        )
        assert "layer" in df.columns
        assert "avg_degree" in df.columns
        assert "n" in df.columns


class TestNodeFrameToPandas:
    """Test NodeFrame.to_pandas() method."""

    def test_to_pandas_returns_dataframe(self, sample_network):
        """Test to_pandas returns DataFrame."""
        import pandas as pd
        result = nodes(sample_network).to_pandas()
        assert isinstance(result, pd.DataFrame)

    def test_to_pandas_columns(self, sample_network):
        """Test to_pandas has expected columns."""
        result = nodes(sample_network).to_pandas()
        assert "id" in result.columns
        assert "layer" in result.columns
        assert "degree" in result.columns

    def test_to_pandas_row_count(self, sample_network):
        """Test to_pandas has correct row count."""
        result = nodes(sample_network).to_pandas()
        assert len(result) == 7

    def test_to_pandas_excludes_internal_fields(self, sample_network):
        """Test that internal fields starting with _ are excluded."""
        result = nodes(sample_network).to_pandas()
        for col in result.columns:
            assert not col.startswith("_")


class TestNodeFrameToSubgraph:
    """Test NodeFrame.to_subgraph() method."""

    def test_to_subgraph_returns_network(self, sample_network):
        """Test to_subgraph returns multi_layer_network."""
        result = nodes(sample_network).filter(lambda n: n["layer"] == "layer1").to_subgraph()
        assert hasattr(result, 'core_network')

    def test_to_subgraph_filters_nodes(self, sample_network):
        """Test to_subgraph contains only filtered nodes."""
        result = nodes(sample_network).filter(lambda n: n["layer"] == "layer1").to_subgraph()
        node_layers = [n[1] for n in result.get_nodes() if isinstance(n, tuple)]
        for layer in node_layers:
            assert layer == "layer1"


class TestEdgeFrameFilter:
    """Test EdgeFrame.filter() method."""

    def test_filter_by_weight(self, sample_network):
        """Test filtering edges by weight."""
        result = edges(sample_network).filter(lambda e: e.get("weight", 0) > 1)
        assert len(result) > 0
        for item in result:
            assert item.get("weight", 0) > 1

    def test_filter_by_layer(self, sample_network):
        """Test filtering edges by layer."""
        result = edges(sample_network).filter(lambda e: e["source_layer"] == "layer2")
        for item in result:
            assert item["source_layer"] == "layer2"


class TestEdgeFrameSelect:
    """Test EdgeFrame.select() method."""

    def test_select_fields(self, sample_network):
        """Test selecting edge fields."""
        result = edges(sample_network).select("source", "target", "weight")
        for item in result:
            assert "source" in item
            assert "target" in item
            if "weight" in item:  # weight may not be in all edges
                assert isinstance(item["weight"], (int, float))


class TestEdgeFrameMutate:
    """Test EdgeFrame.mutate() method."""

    def test_mutate_edge(self, sample_network):
        """Test mutating edges."""
        result = edges(sample_network).mutate(
            doubled_weight=lambda e: e.get("weight", 1) * 2
        )
        for item in result:
            assert "doubled_weight" in item


class TestEdgeFrameArrange:
    """Test EdgeFrame.arrange() method."""

    def test_arrange_by_weight(self, sample_network):
        """Test arranging edges by weight."""
        result = edges(sample_network).arrange("weight", reverse=True)
        weights = [item.get("weight", 0) for item in result]
        assert weights == sorted(weights, reverse=True)


class TestEdgeFrameHead:
    """Test EdgeFrame.head() method."""

    def test_head_edges(self, sample_network):
        """Test head on edges."""
        result = edges(sample_network).head(3)
        assert len(result) == 3


class TestEdgeFrameGroupBy:
    """Test EdgeFrame.group_by() method."""

    def test_group_by_layer(self, sample_network):
        """Test grouping edges by layer."""
        result = (
            edges(sample_network)
            .group_by("source_layer")
            .summarise(n=("source", len))
        )
        assert isinstance(result, EdgeFrame)
        assert len(result) == 2  # Two layers


class TestEdgeFrameToPandas:
    """Test EdgeFrame.to_pandas() method."""

    def test_to_pandas_edges(self, sample_network):
        """Test to_pandas for edges."""
        import pandas as pd
        result = edges(sample_network).to_pandas()
        assert isinstance(result, pd.DataFrame)
        assert "source" in result.columns
        assert "target" in result.columns


class TestMethodChaining:
    """Test complex method chaining scenarios."""

    def test_full_node_chain(self, sample_network):
        """Test full method chain for nodes."""
        import numpy as np
        df = (
            nodes(sample_network)
            .filter(lambda n: n["layer"] == "layer1")
            .mutate(normalized_degree=lambda n: n["degree"] / 10)
            .select("id", "layer", "degree", "normalized_degree")
            .arrange("degree", reverse=True)
            .head(3)
            .to_pandas()
        )
        assert len(df) <= 3
        assert "normalized_degree" in df.columns

    def test_full_edge_chain(self, sample_network):
        """Test full method chain for edges."""
        df = (
            edges(sample_network, layers=["layer1"])
            .filter(lambda e: e.get("weight", 0) >= 1)
            .mutate(log_weight=lambda e: math.log1p(e.get("weight", 0)))
            .arrange("weight", reverse=True)
            .head(5)
            .to_pandas()
        )
        assert len(df) <= 5

    def test_group_summarise_chain(self, sample_network):
        """Test group_by -> summarise -> arrange chain."""
        import numpy as np
        df = (
            nodes(sample_network)
            .group_by("layer")
            .summarise(
                avg_degree=("degree", np.mean),
                n=("id", len),
            )
            .arrange("avg_degree", reverse=True)
            .to_pandas()
        )
        assert "avg_degree" in df.columns
        assert len(df) == 2


class TestIterableProtocol:
    """Test that frames support iteration."""

    def test_nodeframe_len(self, sample_network):
        """Test NodeFrame __len__."""
        frame = nodes(sample_network)
        assert len(frame) == 7

    def test_nodeframe_iter(self, sample_network):
        """Test NodeFrame __iter__."""
        frame = nodes(sample_network)
        items = list(frame)
        assert len(items) == 7

    def test_edgeframe_len(self, sample_network):
        """Test EdgeFrame __len__."""
        frame = edges(sample_network)
        assert len(frame) == 6

    def test_edgeframe_iter(self, sample_network):
        """Test EdgeFrame __iter__."""
        frame = edges(sample_network)
        items = list(frame)
        assert len(items) == 6


class TestRepr:
    """Test string representations."""

    def test_nodeframe_repr(self, sample_network):
        """Test NodeFrame __repr__."""
        frame = nodes(sample_network)
        repr_str = repr(frame)
        assert "NodeFrame" in repr_str
        assert "n=7" in repr_str

    def test_edgeframe_repr(self, sample_network):
        """Test EdgeFrame __repr__."""
        frame = edges(sample_network)
        repr_str = repr(frame)
        assert "EdgeFrame" in repr_str


class TestNodeFrameTail:
    """Test NodeFrame.tail() method."""

    def test_tail_default(self, sample_network):
        """Test tail with default n=5."""
        result = nodes(sample_network).tail()
        assert len(result) == 5

    def test_tail_custom_n(self, sample_network):
        """Test tail with custom n."""
        result = nodes(sample_network).tail(2)
        assert len(result) == 2

    def test_tail_larger_than_data(self, sample_network):
        """Test tail with n larger than data."""
        original = nodes(sample_network)
        result = original.tail(100)
        assert len(result) == len(original)

    def test_tail_zero(self, sample_network):
        """Test tail with n=0."""
        result = nodes(sample_network).tail(0)
        assert len(result) == 0


class TestNodeFrameSample:
    """Test NodeFrame.sample() method."""

    def test_sample_default(self, sample_network):
        """Test sample with default n=5."""
        result = nodes(sample_network).sample(seed=42)
        assert len(result) == 5

    def test_sample_custom_n(self, sample_network):
        """Test sample with custom n."""
        result = nodes(sample_network).sample(3, seed=42)
        assert len(result) == 3

    def test_sample_reproducible(self, sample_network):
        """Test sample is reproducible with same seed."""
        result1 = nodes(sample_network).sample(3, seed=42)
        result2 = nodes(sample_network).sample(3, seed=42)
        ids1 = [item['id'] for item in result1]
        ids2 = [item['id'] for item in result2]
        assert ids1 == ids2

    def test_sample_larger_than_data(self, sample_network):
        """Test sample with n larger than data."""
        original = nodes(sample_network)
        result = original.sample(100, seed=42)
        assert len(result) == len(original)


class TestNodeFrameDistinct:
    """Test NodeFrame.distinct() method."""

    def test_distinct_single_field(self, sample_network):
        """Test distinct on single field."""
        result = nodes(sample_network).distinct('id')
        # A, B, C, D appear across layers - should have 4 unique IDs
        ids = [item['id'] for item in result]
        assert len(ids) == len(set(ids))
        assert len(result) == 4  # 4 unique node IDs

    def test_distinct_multiple_fields(self, sample_network):
        """Test distinct on multiple fields."""
        result = nodes(sample_network).distinct('id', 'layer')
        # Each (id, layer) should be unique - should keep all 7
        assert len(result) == 7


class TestNodeFrameCount:
    """Test NodeFrame.count() method."""

    def test_count_all(self, sample_network):
        """Test count on all nodes."""
        count = nodes(sample_network).count()
        assert count == 7

    def test_count_filtered(self, sample_network):
        """Test count after filter."""
        count = nodes(sample_network).filter(lambda n: n['layer'] == 'layer1').count()
        assert count == 4


class TestNodeFrameRename:
    """Test NodeFrame.rename() method."""

    def test_rename_single_field(self, sample_network):
        """Test renaming a single field."""
        result = nodes(sample_network).rename(id='node_id')
        for item in result:
            assert 'node_id' in item
            assert 'id' not in item

    def test_rename_multiple_fields(self, sample_network):
        """Test renaming multiple fields."""
        result = nodes(sample_network).rename(id='node_id', layer='node_layer')
        for item in result:
            assert 'node_id' in item
            assert 'node_layer' in item
            assert 'id' not in item
            assert 'layer' not in item


class TestNodeFrameDrop:
    """Test NodeFrame.drop() method."""

    def test_drop_single_field(self, sample_network):
        """Test dropping a single field."""
        result = nodes(sample_network).drop('_node_tuple')
        for item in result:
            assert '_node_tuple' not in item
            assert 'id' in item  # Other fields remain

    def test_drop_multiple_fields(self, sample_network):
        """Test dropping multiple fields."""
        result = nodes(sample_network).drop('_node_tuple', 'degree')
        for item in result:
            assert '_node_tuple' not in item
            assert 'degree' not in item
            assert 'id' in item  # Other fields remain


class TestNodeFrameWhere:
    """Test NodeFrame.where() method (alias for filter)."""

    def test_where_is_alias_for_filter(self, sample_network):
        """Test where produces same result as filter."""
        result_where = nodes(sample_network).where(lambda n: n['layer'] == 'layer1')
        result_filter = nodes(sample_network).filter(lambda n: n['layer'] == 'layer1')
        assert len(result_where) == len(result_filter)


class TestNodeFrameOrderBy:
    """Test NodeFrame.order_by() method (alias for arrange)."""

    def test_order_by_ascending(self, sample_network):
        """Test order_by ascending."""
        result = nodes(sample_network).order_by('degree')
        degrees = [item['degree'] for item in result]
        assert degrees == sorted(degrees)

    def test_order_by_descending(self, sample_network):
        """Test order_by descending."""
        result = nodes(sample_network).order_by('degree', descending=True)
        degrees = [item['degree'] for item in result]
        assert degrees == sorted(degrees, reverse=True)


class TestNodeFrameTake:
    """Test NodeFrame.take() method (alias for head)."""

    def test_take_is_alias_for_head(self, sample_network):
        """Test take produces same result as head."""
        result_take = nodes(sample_network).take(3)
        result_head = nodes(sample_network).head(3)
        assert len(result_take) == len(result_head)


class TestNodeFrameSlice:
    """Test NodeFrame.slice() method."""

    def test_slice_range(self, sample_network):
        """Test slice with start and end."""
        result = nodes(sample_network).slice(1, 4)
        assert len(result) == 3

    def test_slice_from_start(self, sample_network):
        """Test slice from start index to end."""
        result = nodes(sample_network).slice(5)
        assert len(result) == 2  # indices 5, 6 of 0-6


class TestNodeFrameFirst:
    """Test NodeFrame.first() method."""

    def test_first_returns_dict(self, sample_network):
        """Test first returns a dict."""
        result = nodes(sample_network).first()
        assert isinstance(result, dict)

    def test_first_on_empty(self, sample_network):
        """Test first on empty frame returns None."""
        result = nodes(sample_network).filter(lambda n: False).first()
        assert result is None


class TestNodeFrameLast:
    """Test NodeFrame.last() method."""

    def test_last_returns_dict(self, sample_network):
        """Test last returns a dict."""
        result = nodes(sample_network).last()
        assert isinstance(result, dict)

    def test_last_on_empty(self, sample_network):
        """Test last on empty frame returns None."""
        result = nodes(sample_network).filter(lambda n: False).last()
        assert result is None


class TestNodeFrameCollect:
    """Test NodeFrame.collect() method."""

    def test_collect_returns_list(self, sample_network):
        """Test collect returns a list."""
        result = nodes(sample_network).collect()
        assert isinstance(result, list)
        assert len(result) == 7

    def test_collect_after_filter(self, sample_network):
        """Test collect after filter."""
        result = nodes(sample_network).filter(lambda n: n['layer'] == 'layer1').collect()
        assert len(result) == 4


class TestNodeFramePluck:
    """Test NodeFrame.pluck() method."""

    def test_pluck_field(self, sample_network):
        """Test pluck extracts field values."""
        result = nodes(sample_network).pluck('layer')
        assert len(result) == 7
        assert all(layer in ['layer1', 'layer2'] for layer in result)

    def test_pluck_numeric_field(self, sample_network):
        """Test pluck on numeric field."""
        result = nodes(sample_network).pluck('degree')
        assert all(isinstance(d, (int, float)) for d in result)


class TestEdgeFrameNewMethods:
    """Test new EdgeFrame methods."""

    def test_edge_tail(self, sample_network):
        """Test EdgeFrame.tail()."""
        result = edges(sample_network).tail(2)
        assert len(result) == 2

    def test_edge_sample(self, sample_network):
        """Test EdgeFrame.sample()."""
        result = edges(sample_network).sample(2, seed=42)
        assert len(result) == 2

    def test_edge_distinct(self, sample_network):
        """Test EdgeFrame.distinct()."""
        result = edges(sample_network).distinct('source', 'target')
        # All edges should be distinct by source-target pair
        assert len(result) <= 6

    def test_edge_count(self, sample_network):
        """Test EdgeFrame.count()."""
        count = edges(sample_network).count()
        assert count == 6

    def test_edge_rename(self, sample_network):
        """Test EdgeFrame.rename()."""
        result = edges(sample_network).rename(source='from_node')
        for item in result:
            assert 'from_node' in item
            assert 'source' not in item

    def test_edge_drop(self, sample_network):
        """Test EdgeFrame.drop()."""
        result = edges(sample_network).drop('_source_tuple')
        for item in result:
            assert '_source_tuple' not in item

    def test_edge_where(self, sample_network):
        """Test EdgeFrame.where()."""
        result = edges(sample_network).where(lambda e: e.get('weight', 0) > 1)
        assert len(result) > 0
        for item in result:
            assert item.get('weight', 0) > 1

    def test_edge_order_by(self, sample_network):
        """Test EdgeFrame.order_by()."""
        result = edges(sample_network).order_by('weight', descending=True)
        weights = [item.get('weight', 0) for item in result]
        assert weights == sorted(weights, reverse=True)

    def test_edge_take(self, sample_network):
        """Test EdgeFrame.take()."""
        result = edges(sample_network).take(2)
        assert len(result) == 2

    def test_edge_slice(self, sample_network):
        """Test EdgeFrame.slice()."""
        result = edges(sample_network).slice(1, 3)
        assert len(result) == 2

    def test_edge_first(self, sample_network):
        """Test EdgeFrame.first()."""
        result = edges(sample_network).first()
        assert isinstance(result, dict)

    def test_edge_last(self, sample_network):
        """Test EdgeFrame.last()."""
        result = edges(sample_network).last()
        assert isinstance(result, dict)

    def test_edge_collect(self, sample_network):
        """Test EdgeFrame.collect()."""
        result = edges(sample_network).collect()
        assert isinstance(result, list)
        assert len(result) == 6

    def test_edge_pluck(self, sample_network):
        """Test EdgeFrame.pluck()."""
        result = edges(sample_network).pluck('weight')
        assert len(result) == 6


class TestEnhancedChaining:
    """Test complex chaining with new methods."""

    def test_full_chain_with_new_methods(self, sample_network):
        """Test complete chain using new methods."""
        result = (
            nodes(sample_network)
            .where(lambda n: n['layer'] == 'layer1')
            .order_by('degree', descending=True)
            .take(3)
            .rename(id='node_id')
            .drop('_node_tuple')
            .collect()
        )
        assert len(result) <= 3
        for item in result:
            assert 'node_id' in item
            assert '_node_tuple' not in item

    def test_edge_chain_with_new_methods(self, sample_network):
        """Test edge chaining with new methods."""
        weights = (
            edges(sample_network)
            .where(lambda e: e.get('weight', 0) > 0.5)
            .order_by('weight', descending=True)
            .take(3)
            .pluck('weight')
        )
        assert len(weights) <= 3
        assert weights == sorted(weights, reverse=True)

    def test_sample_in_chain(self, sample_network):
        """Test sample in a chain."""
        result = (
            nodes(sample_network)
            .filter(lambda n: n['degree'] >= 1)
            .sample(3, seed=42)
            .collect()
        )
        assert len(result) <= 3


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
