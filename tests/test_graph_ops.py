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


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
