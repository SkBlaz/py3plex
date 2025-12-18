"""Additional correctness tests for comparison metrics and executor."""

import math
import networkx as nx
import pytest

from py3plex.comparison import executor, metrics
from py3plex.dsl.ast import CompareStmt, LayerExpr, LayerTerm


class _SimpleNetwork:
    """Minimal network wrapper exposing the interface used by comparison metrics."""

    def __init__(self, edges):
        self.core_network = nx.Graph()
        self.core_network.add_edges_from(edges)

    def get_nodes(self):
        return self.core_network.nodes()


def test_multiplex_jaccard_respects_layer_filter_for_global_distance():
    """Global Jaccard should ignore edges outside the requested layers."""
    net_a = _SimpleNetwork(
        [
            (("u", "L1"), ("v", "L1")),  # shared edge in selected layer
            (("u", "L2"), ("v", "L2")),  # edge in ignored layer
        ]
    )
    net_b = _SimpleNetwork(
        [
            (("u", "L1"), ("v", "L1")),  # only layer L1 present
        ]
    )

    result = metrics.multiplex_jaccard(net_a, net_b, layers=["L1"])

    assert result["global_distance"] == 0.0
    assert result["layerwise_distance"] == {"L1": 0.0}


def test_multiplex_jaccard_empty_networks_have_zero_distance():
    """Two empty networks should be identical (distance 0)."""
    net_a = _SimpleNetwork([])
    net_b = _SimpleNetwork([])

    result = metrics.multiplex_jaccard(net_a, net_b)

    assert result["global_distance"] == 0.0
    assert result["layerwise_distance"] == {}


def test_layer_edge_overlap_filters_to_requested_layers():
    """Only layers intersecting the filter should be averaged."""
    net_a = _SimpleNetwork(
        [
            (("a", "L1"), ("b", "L1")),
            (("c", "L2"), ("d", "L2")),  # only in L2 for net_a
        ]
    )
    net_b = _SimpleNetwork(
        [
            (("a", "L1"), ("b", "L1")),
        ]
    )

    result = metrics.layer_edge_overlap(net_a, net_b, layers=["L2", "L_missing"])

    assert result["global_distance"] == 1.0  # only L2 contributes
    assert result["layerwise_distance"] == {"L2": 1.0}


def test_degree_correlation_uses_absolute_value_for_distance():
    """Perfect negative correlation should still yield zero distance."""
    # Degrees in network_a: (0, 1, 2, 1)
    net_a = _SimpleNetwork(
        [
            (("b", "L"), ("c", "L")),
            (("c", "L"), ("d", "L")),
        ]
    )
    # Degrees in network_b: (2, 1, 0, 1)
    net_b = _SimpleNetwork(
        [
            (("a", "L"), ("b", "L")),
            (("a", "L"), ("d", "L")),
        ]
    )

    result = metrics.degree_correlation(net_a, net_b)

    assert result["shared_nodes"] == 4
    assert math.isclose(result["correlation"], -1.0)
    assert result["global_distance"] == 0.0


def test_degree_change_respects_layer_filter_and_shared_nodes_only():
    """Layer filtering should drop nodes outside the requested layers."""
    net_a = _SimpleNetwork(
        [
            (("a", "L1"), ("b", "L1")),
            (("c", "L2"), ("d", "L2")),
        ]
    )
    net_b = _SimpleNetwork(
        [
            (("a", "L1"), ("b", "L1")),  # same as net_a but filtered out
            (("c", "L2"), ("d", "L2")),
            (("c", "L2"), ("extra", "L2")),  # increases degree of c in L2 only
        ]
    )

    result = metrics.degree_change(net_a, net_b, layers=["L2"])

    assert result["per_node_difference"] == {("c", "L2"): 1, ("d", "L2"): 0}
    assert result["global_distance"] == 0.5  # mean absolute change across included nodes


def test_execute_compare_stmt_honors_layer_expression_and_measures():
    """execute_compare_stmt should forward layer filters and selected measures."""
    net_a = _SimpleNetwork(
        [
            (("a", "L1"), ("b", "L1")),
            (("c", "L2"), ("d", "L2")),
        ]
    )
    net_b = _SimpleNetwork(
        [
            (("a", "L1"), ("b", "L1")),
        ]
    )
    stmt = CompareStmt(
        network_a="base",
        network_b="variant",
        metric_name="layer_edge_overlap",
        layer_expr=LayerExpr(terms=[LayerTerm(name="L2")]),
        measures=["layerwise_distance"],
    )

    result = executor.execute_compare_stmt({"base": net_a, "variant": net_b}, stmt)

    assert result.global_distance is None  # not requested
    assert result.layerwise_distance == {"L2": 1.0}
    assert result.meta["layers"] == ["L2"]
    assert result.meta["metric"] == "layer_edge_overlap"


def test_execute_compare_stmt_missing_network_raises():
    """Missing network names should raise an informative ValueError."""
    stmt = CompareStmt(
        network_a="missing",
        network_b="present",
        metric_name="multiplex_jaccard",
    )

    with pytest.raises(ValueError, match="Network 'missing' not found"):
        executor.execute_compare_stmt({"present": _SimpleNetwork([])}, stmt)


def test_multiplex_jaccard_symmetry_property():
    """Symmetry holds for multiplex_jaccard across random small graphs."""
    hypothesis = pytest.importorskip("hypothesis")
    strategies = pytest.importorskip("hypothesis.strategies")

    @hypothesis.given(
        strategies.sets(
            strategies.tuples(
                strategies.integers(min_value=0, max_value=4),
                strategies.integers(min_value=0, max_value=4),
            ),
            max_size=6,
        ),
        strategies.sets(
            strategies.tuples(
                strategies.integers(min_value=0, max_value=4),
                strategies.integers(min_value=0, max_value=4),
            ),
            max_size=6,
        ),
    )
    def check_symmetry(edges_a, edges_b):
        # Remove self-loops and enforce undirected uniqueness
        normalized_a = {tuple(sorted(edge)) for edge in edges_a if edge[0] != edge[1]}
        normalized_b = {tuple(sorted(edge)) for edge in edges_b if edge[0] != edge[1]}

        net_a = _SimpleNetwork(list(normalized_a))
        net_b = _SimpleNetwork(list(normalized_b))

        forward = metrics.multiplex_jaccard(net_a, net_b)["global_distance"]
        backward = metrics.multiplex_jaccard(net_b, net_a)["global_distance"]

        assert 0.0 <= forward <= 1.0
        assert forward == backward

    check_symmetry()
