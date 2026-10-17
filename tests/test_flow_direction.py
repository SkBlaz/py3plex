"""Maximum flow must respect directed arcs and their individual capacities."""

import networkx as nx
import pytest

from py3plex.core.multinet import multi_layer_network
from py3plex.dsl import P
from py3plex.paths import find_paths, multilayer_flow


@pytest.mark.parametrize(
    "graph_type", [nx.Graph, nx.MultiGraph, nx.DiGraph, nx.MultiDiGraph]
)
@pytest.mark.parametrize("reverse", [False, True])
def test_one_way_flow_only_has_reverse_capacity_for_undirected_graphs(
    graph_type, reverse
):
    graph = graph_type()
    graph.add_edge("s", "t", weight=3)
    source, target = ("t", "s") if reverse else ("s", "t")
    result = multilayer_flow(graph, source, target)
    expected = 0 if reverse and graph.is_directed() else 3
    assert result["flow_value"] == expected
    assert result["flow_values"] == ({(source, target): 3} if expected else {})


@pytest.mark.parametrize("graph_type", [nx.DiGraph, nx.MultiDiGraph])
@pytest.mark.parametrize("reverse_insertion", [False, True])
def test_reciprocal_arcs_keep_their_individual_capacities(
    graph_type, reverse_insertion
):
    graph = graph_type()
    edges = [("s", "t", 3), ("t", "s", 7)]
    graph.add_weighted_edges_from(edges[::-1] if reverse_insertion else edges)
    original_edges = list(graph.edges(data=True))
    for source, target in [("s", "t"), ("t", "s")]:
        result = multilayer_flow(graph, source, target)
        expected = nx.maximum_flow_value(
            nx.DiGraph(graph), source, target, capacity="weight"
        )
        assert result["flow_value"] == expected
        assert result["flow_values"] == {(source, target): expected}
    assert list(graph.edges(data=True)) == original_edges


@pytest.mark.parametrize("directed", [False, True])
@pytest.mark.parametrize("frontend", ["function", "executor", "dsl"])
def test_multilayer_flow_frontends_respect_direction_and_custom_capacity(
    directed, frontend
):
    network = multi_layer_network(directed=directed, verbose=False)
    source, target = ("s", "social"), ("t", "work")
    network.add_edges(
        [
            {
                "source": "s",
                "source_type": "social",
                "target": "t",
                "target_type": "work",
                "capacity": 4,
                "weight": 99,
            }
        ]
    )
    if frontend == "function":
        result = multilayer_flow(network, target, source, capacity_attr="capacity")
        value, flows = result["flow_value"], result["flow_values"]
    else:
        if frontend == "executor":
            result = find_paths(
                network, target, source, path_type="flow", capacity_attr="capacity"
            )
        else:
            result = (
                P.flow(target, source)
                .with_params(capacity_attr="capacity")
                .execute(network)
            )
        value, flows = result.meta["flow_value"], result.flow_values
    assert value == (0 if directed else 4)
    assert flows == ({} if directed else {(target, source): 4})
    assert network.core_network.number_of_edges() == 1
    assert network.core_network[source][target][0]["capacity"] == 4


def test_reverse_arcs_cannot_bypass_a_directed_bottleneck():
    graph = nx.DiGraph()
    graph.add_weighted_edges_from(
        [("s", "a", 4), ("a", "t", 1), ("t", "b", 4), ("b", "s", 4)]
    )
    result = multilayer_flow(graph, "s", "t")
    assert (
        result["flow_value"]
        == nx.maximum_flow_value(graph, "s", "t", capacity="weight")
        == 1
    )
    for (source, target), value in result["flow_values"].items():
        assert graph.has_edge(source, target)
        assert value <= graph[source][target]["weight"]
