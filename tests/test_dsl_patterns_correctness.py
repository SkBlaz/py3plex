"""Correctness tests for the DSL pattern matching subsystem."""

import networkx as nx
import pytest

from py3plex.core import multinet
from py3plex.dsl import Q
from py3plex.dsl.errors import DslSyntaxError
from py3plex.dsl.patterns import compile_pattern, match_pattern


class StubNetwork:
    """Minimal network stub for testing pattern matching."""

    def __init__(self, graph):
        self.core_network = graph

    def get_nodes(self):
        return list(self.core_network.nodes())


LAYER = "l"


def node(name, layer=LAYER):
    return (name, layer)


def make_graph(edges, directed=False, multigraph=False, node_attrs=None, edge_attrs=None):
    if multigraph and directed:
        graph = nx.MultiDiGraph()
    elif multigraph:
        graph = nx.MultiGraph()
    elif directed:
        graph = nx.DiGraph()
    else:
        graph = nx.Graph()

    node_attrs = node_attrs or {}
    for name, attrs in node_attrs.items():
        graph.add_node(node(name), **attrs)

    for edge in edges:
        if len(edge) == 2:
            src, dst = edge
            attrs = {}
        else:
            src, dst, attrs = edge
        graph.add_node(node(src), **node_attrs.get(src, {}))
        graph.add_node(node(dst), **node_attrs.get(dst, {}))
        graph.add_edge(node(src), node(dst), **attrs)

    if edge_attrs:
        for (src, dst), attrs in edge_attrs.items():
            if graph.has_edge(node(src), node(dst)):
                if graph.is_multigraph():
                    first_key = next(iter(graph[node(src)][node(dst)]))
                    graph[node(src)][node(dst)][first_key].update(attrs)
                else:
                    graph[node(src)][node(dst)].update(attrs)

    return StubNetwork(graph)


def test_triangle_on_path_returns_zero():
    network = make_graph([("A", "B"), ("B", "C")])
    result = Q.pattern().triangle("a", "b", "c").execute(network)
    assert result.count == 0



def test_triangle_on_triangle_returns_expected():
    network = make_graph([("A", "B"), ("B", "C"), ("A", "C")])
    result = Q.pattern().triangle("a", "b", "c").execute(network)
    assert result.count == 6



def test_c4_on_p4_returns_zero():
    network = make_graph([("A", "B"), ("B", "C"), ("C", "D")])
    pattern = Q.pattern().path(["a", "b", "c", "d"]).edge("d", "a")
    result = pattern.execute(network)
    assert result.count == 0



def test_directed_edge_with_selective_dst():
    network = make_graph(
        [("1", "2"), ("3", "2")],
        directed=True,
        node_attrs={
            "1": {"kind": "src"},
            "2": {"kind": "dst"},
            "3": {"kind": "src"},
            "4": {"kind": "other"},
        },
    )
    result = (
        Q.pattern()
        .node("x")
        .node("y").where(kind="dst")
        .edge("x", "y", directed=True)
        .execute(network)
    )
    assert result.count == 2
    assert {match["x"][0] for match in result.matches} == {"1", "3"}
    assert {match["y"][0] for match in result.matches} == {"2"}



def test_cross_component_edge_verified():
    network = make_graph([("A", "B"), ("C", "D")])
    result = (
        Q.pattern()
        .edge("a", "b")
        .edge("c", "d")
        .edge("b", "c")
        .execute(network)
    )
    assert result.count == 0



def test_injective_default_no_same_node():
    network = make_graph([("A", "B"), ("B", "C"), ("A", "C")])
    result = Q.pattern().triangle("a", "b", "c").execute(network)
    assert result.count == 6
    for match in result.matches:
        assert len(set(match.bindings.values())) == 3



def test_injective_false_allows_homomorphism():
    network = make_graph([("A", "B")])
    result = Q.pattern().path(["a", "b", "c"]).execute(network, injective=False)
    assert result.count == 2
    assert any(match["a"] == match["c"] for match in result.matches)



def test_string_constraint_a_neq_b():
    network = make_graph([("A", "B")])
    result = Q.pattern().edge("a", "b").constraint("a != b").execute(network)
    assert result.count == 2
    for match in result.matches:
        assert match["a"] != match["b"]



def test_malformed_constraint_raises():
    with pytest.raises(DslSyntaxError):
        Q.pattern().constraint("definitely not a supported constraint")



def test_all_distinct_prunes_early():
    network = make_graph([("A", "B")])
    result = (
        Q.pattern()
        .path(["a", "b", "c"])
        .constraint("all_distinct(a, b, c)")
        .execute(network, injective=False)
    )
    assert result.count == 0



def test_parallel_edge_weight_filter_matches_once():
    network = make_graph(
        [
            ("A", "B", {"weight": 0.1}),
            ("A", "B", {"weight": 0.9}),
        ],
        directed=True,
        multigraph=True,
    )
    result = Q.pattern().edge("a", "b", directed=True).where(weight__gt=0.5).execute(network)
    assert result.count == 1



def test_parallel_edge_weight_filter_matches_zero():
    network = make_graph(
        [
            ("A", "B", {"weight": 0.1}),
            ("A", "B", {"weight": 0.2}),
        ],
        directed=True,
        multigraph=True,
    )
    result = Q.pattern().edge("a", "b", directed=True).where(weight__gt=0.5).execute(network)
    assert result.count == 0



def test_per_edge_predicate_conjunction():
    network = make_graph(
        [
            ("A", "B", {"weight": 0.9, "tag": 1}),
            ("A", "B", {"weight": 0.1, "tag": 2}),
        ],
        directed=True,
        multigraph=True,
    )
    result = (
        Q.pattern()
        .edge("a", "b", directed=True)
        .where(weight__gt=0.5, tag=2)
        .execute(network)
    )
    assert result.count == 0



def test_limit_one_returns_exactly_one():
    network = make_graph([("A", "B"), ("B", "C"), ("A", "C")])
    result = Q.pattern().edge("a", "b").limit(1).execute(network)
    assert result.count == 1



def test_integration_with_multinet():
    network = multinet.multi_layer_network(directed=False)
    network.add_nodes(
        [
            {"source": "A", "type": "social"},
            {"source": "B", "type": "social"},
            {"source": "C", "type": "social"},
        ]
    )
    network.add_edges(
        [
            {"source": "A", "target": "B", "source_type": "social", "target_type": "social"},
            {"source": "B", "target": "C", "source_type": "social", "target_type": "social"},
            {"source": "A", "target": "C", "source_type": "social", "target_type": "social"},
        ]
    )

    result = (
        Q.pattern()
        .node("a").where(layer="social", layer_degree__gt=1)
        .node("b").where(layer="social")
        .edge("a", "b")
        .execute(network)
    )
    assert result.count > 0
    assert all(match["a"][1] == "social" and match["b"][1] == "social" for match in result.matches)
