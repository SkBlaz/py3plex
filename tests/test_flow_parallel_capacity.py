"""Parallel flow channels contribute their combined available capacity."""

import copy

import networkx as nx
import pytest

from py3plex.core.multinet import multi_layer_network
from py3plex.dsl import P
from py3plex.paths import find_paths, multilayer_flow


@pytest.mark.parametrize("graph_type", [nx.MultiGraph, nx.MultiDiGraph])
@pytest.mark.parametrize("capacity_attr", ["weight", "capacity"])
@pytest.mark.parametrize("reverse_insertion", [False, True])
def test_parallel_capacities_include_all_channels_and_ignore_insertion_order(
    graph_type, capacity_attr, reverse_insertion
):
    graph = graph_type()
    capacities = [2, 3, 0]
    for index, value in enumerate(
        capacities[::-1] if reverse_insertion else capacities
    ):
        graph.add_edge("s", "t", key=str(index), **{capacity_attr: value})
    graph.add_edge("s", "s", **{capacity_attr: 13})
    before = copy.deepcopy(graph)
    result = multilayer_flow(graph, "s", "t", capacity_attr=capacity_attr)
    assert result["flow_value"] == 5
    assert result["flow_values"] == {("s", "t"): 5}
    assert nx.utils.graphs_equal(graph, before)


def expanded_channel_reference(graph, source, target):
    # Give each channel its own intermediate node: no edge aggregation in this oracle.
    expanded = nx.DiGraph()
    for u, v, data in graph.edges(data=True):
        channel = object()
        capacity = data.get("weight", 1.0)
        expanded.add_edge(u, channel, capacity=capacity)
        expanded.add_edge(channel, v, capacity=capacity)
        if not graph.is_directed():
            expanded.add_edge(v, channel, capacity=capacity)
            expanded.add_edge(channel, u, capacity=capacity)
    return nx.maximum_flow_value(expanded, source, target, capacity="capacity")


@pytest.mark.parametrize("graph_type", [nx.MultiGraph, nx.MultiDiGraph])
def test_parallel_bottleneck_matches_independent_channel_expansion(graph_type):
    graph = graph_type()
    source, target = ("s", "contacts"), ("t", "work")
    graph.add_edge(source, 42, weight=2)
    graph.add_edge(source, 42, weight=3)
    graph.add_edge(42, target, weight=7)
    graph.add_edge(source, target, weight=1)
    if graph.is_directed():
        graph.add_edge(target, source, weight=11)
    for src, dst in [(source, target), (target, source)]:
        result = multilayer_flow(graph, src, dst)
        assert result["flow_value"] == expanded_channel_reference(graph, src, dst)
        for (u, v), amount in result["flow_values"].items():
            assert graph.has_edge(u, v)
            assert amount <= sum(d.get("weight", 1.0) for d in graph[u][v].values())


@pytest.mark.parametrize("directed", [False, True])
@pytest.mark.parametrize("frontend", ["function", "executor", "dsl"])
def test_multilayer_parallel_channels_and_custom_capacity_frontends(directed, frontend):
    network = multi_layer_network(directed=directed, verbose=False)
    source, target = ("s", "contacts"), ("t", "work")
    network.add_edges(
        [
            {
                "source": "s",
                "source_type": "contacts",
                "target": "t",
                "target_type": "work",
                "capacity": value,
                "weight": 99,
            }
            for value in [2, 3]
        ]
    )
    before = copy.deepcopy(network.core_network)
    if frontend == "function":
        result = multilayer_flow(network, source, target, capacity_attr="capacity")
        value, flows = result["flow_value"], result["flow_values"]
    else:
        if frontend == "executor":
            result = find_paths(
                network, source, target, path_type="flow", capacity_attr="capacity"
            )
        else:
            result = (
                P.flow(source, target)
                .with_params(capacity_attr="capacity")
                .execute(network)
            )
        value, flows = result.meta["flow_value"], result.flow_values
    assert value == 5
    assert flows == {(source, target): 5}
    assert nx.utils.graphs_equal(network.core_network, before)


@pytest.mark.parametrize("graph_type", [nx.MultiGraph, nx.MultiDiGraph])
def test_missing_capacity_defaults_apply_to_each_parallel_edge(graph_type):
    graph = graph_type()
    graph.add_edge("s", "t")
    graph.add_edge("s", "t")
    assert multilayer_flow(graph, "s", "t")["flow_value"] == 2
