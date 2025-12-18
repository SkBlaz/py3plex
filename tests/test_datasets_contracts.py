"""Additional correctness tests for py3plex.datasets generators/loaders."""

import networkx as nx
import pytest

from py3plex.datasets import (
    fetch_multilayer,
    make_clique_multiplex,
    make_random_multilayer,
    make_random_multiplex,
    make_social_network,
)


def _edges_by_layer(net, layer_idx):
    return [
        (u, v, data)
        for u, v, data in net.core_network.edges(data=True)
        if u[1] == v[1] == layer_idx
    ]


def test_make_random_multilayer_assigns_unique_layers_when_nodes_lt_layers():
    net = make_random_multilayer(n_nodes=2, n_layers=5, p=0.0, random_state=1)
    nodes = set(net.get_nodes())

    assert nodes == {(0, 0), (1, 1)}
    assert len(list(net.get_edges())) == 0


def test_make_random_multiplex_includes_all_nodes_even_without_edges():
    n_nodes, n_layers = 4, 3
    net = make_random_multiplex(
        n_nodes=n_nodes, n_layers=n_layers, p=0.0, random_state=0
    )

    expected_nodes = {(n, layer) for n in range(n_nodes) for layer in range(n_layers)}
    assert set(net.get_nodes()) == expected_nodes
    assert len(list(net.get_edges())) == 0


def test_make_random_multiplex_matches_networkx_with_seed():
    n_nodes, n_layers, p, seed = 5, 2, 0.3, 7
    net = make_random_multiplex(
        n_nodes=n_nodes, n_layers=n_layers, p=p, random_state=seed
    )

    for layer_idx in range(n_layers):
        expected_graph = nx.fast_gnp_random_graph(
            n_nodes, p, seed=seed * 1000 + layer_idx
        )
        expected_edges = {frozenset(edge) for edge in expected_graph.edges()}

        edges = _edges_by_layer(net, layer_idx)
        observed_edges = {frozenset((u[0], v[0])) for u, v, _ in edges}

        assert observed_edges == expected_edges


def test_make_random_multiplex_invalid_probability_raises():
    with pytest.raises(ValueError):
        make_random_multiplex(n_nodes=3, n_layers=2, p=1.5)


def test_make_clique_multiplex_forms_complete_clique_with_weights():
    net = make_clique_multiplex(
        n_nodes=5, n_layers=1, clique_size=3, n_cliques=1, random_state=0
    )
    nodes = set(net.get_nodes())

    # Multiplex generators must include isolated nodes too.
    assert nodes == {(n, 0) for n in range(5)}
    edges = [(u, v, data) for u, v, data in net.core_network.edges(data=True) if data.get("type") != "coupling"]
    assert len(edges) == 3  # complete graph on 3 nodes has 3 edges
    for (u, v, data) in edges:
        assert u[1] == v[1] == 0
        assert data.get("weight") == 1
        assert data.get("type") == "default"


def test_make_social_network_edge_types_follow_layer_mapping():
    net = make_social_network(n_people=12, random_state=0)
    type_by_layer = {0: "friendship", 1: "work", 2: "family"}

    for u, v, data in net.core_network.edges(data=True):
        if data.get("type") == "coupling":
            continue
        assert u[1] == v[1]  # no cross-layer edges
        assert data.get("type") == type_by_layer[u[1]]


def test_fetch_multilayer_human_sets_expected_node_attributes():
    net = fetch_multilayer("human_ppi_gene_disease_drug")

    nodes = list(net.get_nodes())
    assert len(nodes) == 500
    layers = {layer for _, layer in nodes}
    assert layers == {0, 1, 2, 3}

    attrs = net.core_network.nodes
    for node in nodes:
        data = attrs[node]
        assert data["node_type"] == "gene"
        assert isinstance(data["disease_enriched"], bool)
