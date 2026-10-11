"""Approximation sample counts must not silently activate metric UQ."""

import networkx as nx
import pytest

from py3plex.core.multinet import multi_layer_network
from py3plex.dsl import Q
from py3plex.dsl.errors import DslExecutionError
from py3plex.dsl.uq_resolution import resolve_uq_config


@pytest.mark.parametrize("directed", [False, True])
@pytest.mark.parametrize("seed", [0, 42])
def test_approximation_returns_scalars_without_unrequested_uq(directed, seed):
    network = multi_layer_network(directed=directed)
    network.core_network = nx.path_graph(
        [(str(i), "L") for i in range(6)], create_using=nx.DiGraph if directed else nx.Graph
    )
    query = Q.nodes().compute("betweenness_centrality", approx=True, n_samples=2, seed=seed)
    result = query.execute(network)
    assert all(isinstance(value, (int, float)) for value in result.attributes["betweenness_centrality"].values())
    assert result.meta["approximation"]["measures"][0]["parameters"]["n_samples"] == 2


@pytest.mark.parametrize("alias_kwargs", [{}, {"alias": "bc"}, {"aliases": {"betweenness_centrality": "bc"}}])
def test_approximation_budget_does_not_request_uq(alias_kwargs):
    item = Q.nodes().compute(
        "betweenness_centrality", approx=True, n_samples=2, seed=42, **alias_kwargs
    ).to_ast().select.compute[0]
    assert item.approx.params["n_samples"] == 2
    assert resolve_uq_config(item, None, item.name) is None


@pytest.mark.parametrize("uq_first", [True, False])
def test_query_uq_and_approximation_keep_separate_sample_budgets(uq_first):
    query = Q.nodes()
    if uq_first:
        query.uq(method="perturbation", n_samples=7, seed=42)
    query.compute("betweenness_centrality", approx=True, n_samples=2, seed=42)
    if not uq_first:
        query.uq(method="perturbation", n_samples=7, seed=42)
    ast = query.to_ast()
    item = ast.select.compute[0]
    assert item.approx.params["n_samples"] == 2
    assert resolve_uq_config(item, ast.select.uq_config, item.name).n_samples == 7


def test_explicit_metric_uq_keeps_shared_sample_budget():
    item = Q.nodes().compute(
        "betweenness_centrality", approx=True, uncertainty=True,
        method="perturbation", n_samples=2, random_state=42, seed=42,
    ).to_ast().select.compute[0]
    assert item.approx.params["n_samples"] == 2
    assert resolve_uq_config(item, None, item.name).n_samples == 2


@pytest.mark.parametrize("budget", [0, -1])
def test_invalid_approximation_budget_is_rejected(budget):
    with pytest.raises(DslExecutionError, match="n_samples.*positive integer"):
        Q.nodes().compute("betweenness_centrality", approx=True, n_samples=budget)


def test_exact_metric_still_supports_metric_uq_sample_budget():
    item = Q.nodes().compute("degree", n_samples=2, random_state=42).to_ast().select.compute[0]
    assert resolve_uq_config(item, None, item.name).n_samples == 2
