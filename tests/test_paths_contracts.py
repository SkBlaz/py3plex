"""Contract-focused tests for py3plex.paths algorithms."""

import networkx as nx

from py3plex.core import multinet
from py3plex.paths import find_paths
from py3plex.paths.algorithms import (
    random_walk,
    shortest_path,
    multilayer_flow,
)
from py3plex.paths.result import PathResult


def test_shortest_path_respects_layer_filter():
    """Layer filters should prevent paths from using other layers."""
    net = multinet.multi_layer_network(directed=False, verbose=False)
    net.add_edges(
        [
            ["s", "L1", "m", "L1", 1.0],
            ["m", "L1", "t", "L1", 1.0],
        ],
        input_type="list",
    )
    net.add_nodes(
        [
            {"source": "s", "type": "L2"},
            {"source": "m", "type": "L2"},
            {"source": "t", "type": "L2"},
        ]
    )

    result = shortest_path(net, source="s", target="t", layers=["L2"])

    assert result["paths"] == []


def test_random_walk_zero_steps_reports_source_only():
    """Zero-step random walks should not record any visits but keep the start node."""
    G = nx.Graph()
    G.add_edge("s", "t")

    result = random_walk(G, source="s", steps=0, seed=0)

    assert result["visit_frequency"] == {}
    assert result["paths"] == [["s"]]


def test_random_walk_with_full_teleport_stays_at_source():
    """With teleport=1.0 the walk should never leave the starting node."""
    G = nx.Graph()
    G.add_edge("s", "t")

    result = random_walk(G, source="s", steps=5, teleport=1.0, seed=42)

    assert set(result["visit_frequency"].keys()) == {"s"}
    assert set(result["paths"][0]) == {"s"}


def test_multilayer_flow_matches_reference_max_flow():
    """Flow values should agree with a reference NetworkX computation."""
    G = nx.Graph()
    G.add_edge("s", "a", weight=2.0)
    G.add_edge("a", "t", weight=2.0)
    G.add_edge("s", "b", weight=1.0)
    G.add_edge("b", "t", weight=1.0)

    result = multilayer_flow(G, source="s", target="t", capacity_attr="weight")

    expected_flow = nx.maximum_flow_value(
        nx.DiGraph(
            list(
                (u, v, {"capacity": data.get("weight", 1.0)})
                for u, v, data in G.edges(data=True)
            )
            + list(
                (v, u, {"capacity": data.get("weight", 1.0)})
                for u, v, data in G.edges(data=True)
            )
        ),
        "s",
        "t",
        capacity="capacity",
    )

    assert result["flow_value"] == expected_flow
    assert (
        sum(flow for (u, _), flow in result["flow_values"].items() if u == "s")
        == expected_flow
    )


def test_multilayer_flow_layer_filter_without_edges_returns_zero():
    """Flow on a layer with no edges should report zero flow."""
    net = multinet.multi_layer_network(directed=False, verbose=False)
    net.add_edges([["s", "L1", "t", "L1", 1.0]], input_type="list")
    net.add_nodes([{"source": "s", "type": "L2"}, {"source": "t", "type": "L2"}])

    result = multilayer_flow(net, source="s", target="t", layers=["L2"])

    assert result["flow_value"] == 0
    assert result["flow_values"] == {}


def test_find_paths_preserves_all_paths_metadata():
    """find_paths should keep extra metadata returned by algorithms."""
    net = multinet.multi_layer_network(directed=False, verbose=False)
    net.add_edges(
        [
            ["n1", "L", "n2", "L", 1.0],
            ["n2", "L", "n3", "L", 1.0],
        ],
        input_type="list",
    )

    raw = shortest_path(net, source="n1", target="n3")
    result = find_paths(net, source="n1", target="n3", path_type="shortest")

    assert "all_paths" in result.meta
    assert result.meta["all_paths"] == raw.get("all_paths")


def test_path_result_to_dict_stringifies_nodes_and_keys():
    """to_dict should stringify path nodes and visit_frequency keys."""
    paths = [[("a", "L1"), ("b", "L1")]]
    visit_frequency = {("a", "L1"): 0.6, ("b", "L1"): 0.4}

    result = PathResult(
        path_type="random_walk",
        source="a",
        target="b",
        paths=paths,
        visit_frequency=visit_frequency,
    )

    data = result.to_dict()

    assert all(isinstance(node, str) for node in data["paths"][0])
    assert set(data["visit_frequency"].keys()) == {
        str(("a", "L1")),
        str(("b", "L1")),
    }


def test_shortest_path_rejects_cross_layer_edges_when_disabled():
    """cross_layer=False should forbid paths that require switching layers."""
    net = multinet.multi_layer_network(directed=False, verbose=False)
    net.add_edges(
        [
            ["a", "L1", "a", "L2", 1.0],
            ["a", "L2", "b", "L1", 1.0],
            ["b", "L1", "b", "L2", 1.0],
        ],
        input_type="list",
    )

    enabled = shortest_path(net, source="a", target="b", layers=["L1", "L2"], cross_layer=True)
    disabled = shortest_path(net, source="a", target="b", layers=["L1", "L2"], cross_layer=False)

    assert enabled["paths"]
    assert disabled["paths"] == []


def test_shortest_path_layer_filter_applies_to_intermediate_nodes_regression():
    """Layer filters should prevent paths from traversing nodes in other layers."""
    net = multinet.multi_layer_network(directed=False, verbose=False)
    net.add_edges(
        [
            ["s", "L2", "s", "L1", 1.0],
            ["s", "L1", "t", "L1", 1.0],
            ["t", "L1", "t", "L2", 1.0],
        ],
        input_type="list",
    )

    result = shortest_path(net, source="s", target="t", layers=["L2"], cross_layer=True)

    assert result["paths"] == []


def test_shortest_path_accepts_tuple_node_identifiers():
    """Tuple inputs should select the exact (node, layer) rather than base-name matches."""
    net = multinet.multi_layer_network(directed=False, verbose=False)
    net.add_edges(
        [
            ["s", "L1", "t", "L1", 1.0],
            ["s", "L2", "m", "L2", 1.0],
            ["m", "L2", "t", "L2", 1.0],
        ],
        input_type="list",
    )

    result = shortest_path(net, source=("s", "L2"), target=("t", "L2"))

    assert result["paths"] == [[("s", "L2"), ("m", "L2"), ("t", "L2")]]


def test_random_walk_blocks_cross_layer_moves_without_layer_filter():
    """cross_layer=False should prevent moving across layers even without layers=[...]."""
    G = nx.Graph()
    source = ("A", "L1")
    other = ("B", "L2")
    G.add_edge(source, other)

    result = random_walk(G, source="A", steps=5, cross_layer=False, seed=123)

    assert set(result["visit_frequency"]) == {source}
    assert set(result["paths"][0]) == {source}


def test_find_paths_unknown_algorithm_raises():
    net = multinet.multi_layer_network(directed=False, verbose=False)
    net.add_edges([["n1", "L", "n2", "L", 1.0]], input_type="list")

    try:
        find_paths(net, source="n1", target="n2", path_type="does_not_exist")
    except ValueError as exc:
        assert "Unknown path algorithm" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("Expected ValueError for unknown algorithm name")
