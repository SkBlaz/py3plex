"""Oracle- and invariant-based correctness tests for py3plex.datasets.

These tests avoid network/GUI and focus on deterministic properties of the
bundled dataset loaders and the synthetic dataset generators.
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path

import networkx as nx
import numpy as np
import pytest

from py3plex.datasets import (
    get_data_dir,
    load_aarhus_cs,
    load_synthetic_multilayer,
    make_random_multilayer,
    make_random_multiplex,
    make_social_network,
)


def _edge_endpoint_multiset(multigraph: nx.MultiGraph | nx.MultiDiGraph):
    # Normalize undirected endpoints so tests are stable regardless of ordering.
    counts: Counter[frozenset] = Counter()
    for u, v in multigraph.edges():
        counts[frozenset((u, v))] += 1
    return counts


def _parse_multiedgelist_layers(path: Path) -> set[str]:
    layers: set[str] = set()
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            src, src_layer, dst, dst_layer, _w = line.split()
            layers.add(src_layer)
            layers.add(dst_layer)
    return layers


def test_make_random_multilayer_matches_networkx_oracle_for_seed():
    n_nodes, n_layers, p, seed = 12, 4, 0.25, 123
    net = make_random_multilayer(
        n_nodes=n_nodes, n_layers=n_layers, p=p, directed=False, random_state=seed
    )

    # Oracle: reproduce the generator's logic exactly.
    base = nx.gnp_random_graph(n_nodes, p, seed=seed, directed=False)
    np.random.seed(seed)

    layers = {i: i for i in range(n_layers)}
    for i in range(n_layers, n_nodes):
        layers[i] = int(np.random.randint(n_layers))

    oracle = nx.MultiGraph()
    for node in base.nodes():
        oracle.add_node((node, layers[node]), type="default")
    for u, v in base.edges():
        oracle.add_edge((u, layers[u]), (v, layers[v]), type="default")

    assert set(net.core_network.nodes()) == set(oracle.nodes())
    assert _edge_endpoint_multiset(net.core_network) == _edge_endpoint_multiset(oracle)
    for node, data in net.core_network.nodes(data=True):
        assert data.get("type") == "default"
    for u, v, data in net.core_network.edges(data=True):
        assert data.get("type") == "default"


def test_make_random_multiplex_p_extremes_node_and_edge_counts():
    n_nodes, n_layers = 6, 3

    net_empty = make_random_multiplex(
        n_nodes=n_nodes, n_layers=n_layers, p=0.0, random_state=0
    )
    assert net_empty.core_network.number_of_nodes() == n_nodes * n_layers
    assert len(list(net_empty.get_edges())) == 0

    net_full = make_random_multiplex(
        n_nodes=n_nodes, n_layers=n_layers, p=1.0, random_state=0
    )
    expected_edges_per_layer = n_nodes * (n_nodes - 1) // 2
    assert net_full.core_network.number_of_nodes() == n_nodes * n_layers
    assert len(list(net_full.get_edges())) == n_layers * expected_edges_per_layer


def test_make_social_network_includes_all_nodes_in_all_layers_and_no_cross_layer_edges():
    n_people, seed = 17, 7
    net = make_social_network(n_people=n_people, random_state=seed)
    nodes = set(net.get_nodes())

    expected_nodes = {(p, layer) for p in range(n_people) for layer in (0, 1, 2)}
    assert nodes == expected_nodes

    type_by_layer = {0: "friendship", 1: "work", 2: "family"}
    for u, v, data in net.core_network.edges(data=True):
        if data.get("type") == "coupling":
            continue
        assert u[1] == v[1]
        assert data.get("type") == type_by_layer[u[1]]


@pytest.mark.parametrize(
    "loader,filename",
    [
        (load_aarhus_cs, "aarhus_cs.edges"),
        (load_synthetic_multilayer, "synthetic_multilayer.edges"),
    ],
)
def test_bundled_loaders_preserve_layer_names(loader, filename):
    data_dir = Path(get_data_dir())
    expected_layers = _parse_multiedgelist_layers(data_dir / filename)

    net = loader()
    observed_layers = {layer for _node, layer in net.get_nodes()}
    assert observed_layers == expected_layers


def test_property_make_random_multiplex_edges_match_complete_or_empty_graph():
    hypothesis = pytest.importorskip("hypothesis")
    strategies = pytest.importorskip("hypothesis.strategies")

    @hypothesis.given(
        n_nodes=strategies.integers(min_value=1, max_value=7),
        n_layers=strategies.integers(min_value=1, max_value=4),
        p=strategies.sampled_from([0.0, 1.0]),
        seed=strategies.integers(min_value=0, max_value=10),
    )
    def check(n_nodes, n_layers, p, seed):
        net = make_random_multiplex(
            n_nodes=n_nodes, n_layers=n_layers, p=p, random_state=seed
        )
        assert net.core_network.number_of_nodes() == n_nodes * n_layers

        expected_edges_per_layer = 0 if p == 0.0 else n_nodes * (n_nodes - 1) // 2
        assert len(list(net.get_edges())) == n_layers * expected_edges_per_layer

    check()
