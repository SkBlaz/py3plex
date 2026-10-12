"""Approximation dispatch must use configured numerical parameters."""

import networkx as nx
import pytest

from py3plex.algorithms.centrality.approx_betweenness import approximate_betweenness_sampling
from py3plex.algorithms.centrality.approx_closeness import approximate_closeness_landmarks
from py3plex.core.multinet import multi_layer_network
from py3plex.dsl import Q
from py3plex.dsl.ast import ApproximationSpec, ComputeItem
from py3plex.dsl.executor import _get_measure_function, execute_ast
from py3plex.dsl.registry import measure_registry


@pytest.mark.parametrize("directed", [False, True])
@pytest.mark.parametrize("seed", [0, 42])
def test_approximate_ast_matches_configured_sampling_algorithm(directed, seed):
    network = multi_layer_network(directed=directed)
    network.core_network = nx.path_graph(
        [(str(i), "L") for i in range(6)], create_using=nx.DiGraph if directed else nx.Graph
    )
    ast = Q.nodes().to_ast()
    ast.select.compute = [ComputeItem(
        name="betweenness_centrality", approx=ApproximationSpec(
            enabled=True, method="sampling", params={"n_samples": 2, "seed": seed},
        ),
    )]
    result = execute_ast(network, ast)
    expected, _ = approximate_betweenness_sampling(network.core_network, n_samples=2, seed=seed)
    assert result.attributes["betweenness_centrality"] == pytest.approx(expected)
    assert execute_ast(network, ast).attributes == result.attributes


@pytest.mark.parametrize("seed", [0, 42])
def test_closeness_dispatch_honors_landmarks_and_seed(seed):
    graph = nx.path_graph(8)
    item = ComputeItem(name="closeness_centrality", approx=ApproximationSpec(
        enabled=True, method="landmarks", params={"n_landmarks": 2, "seed": seed},
    ))
    function, metadata, fast_path = _get_measure_function(item)
    actual, _ = function(graph, list(graph))
    expected, _ = approximate_closeness_landmarks(graph, n_landmarks=2, seed=seed)
    assert actual == pytest.approx(expected)
    assert function(graph, list(graph))[0] == actual
    assert metadata["parameters"] == item.approx.params
    assert fast_path is True


@pytest.mark.parametrize("diagnostics", [False, True])
def test_dispatch_forwards_parameters_and_diagnostics(monkeypatch, diagnostics):
    calls = []

    def approximate(graph, nodes, **kwargs):
        calls.append(kwargs)
        return {node: 1 / len(nodes) for node in nodes}, None

    monkeypatch.setattr(measure_registry, "get_approx", lambda name, method: approximate)
    params = {"tol": 1e-8, "max_iter": 5, "alpha": 0.5}
    item = ComputeItem(name="pagerank", approx=ApproximationSpec(
        enabled=True, method="power_iteration", params=params, diagnostics=diagnostics,
    ))
    function, _, _ = _get_measure_function(item)
    graph = nx.path_graph(3)
    function(graph, list(graph))
    assert calls == [{**params, "diagnostics": diagnostics}]
