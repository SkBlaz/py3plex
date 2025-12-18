"""Contract tests for py3plex.nullmodels algorithms."""

from collections import Counter, defaultdict

import pytest
from py3plex.core import multinet
from py3plex.nullmodels.models import (
    _copy_network,
    configuration_model,
    edge_swap_model,
    erdos_renyi_model,
    layer_shuffle_model,
)


def _edge_weights(net):
    return {
        (frozenset({u, v}), data.get("weight"))
        for u, v, data in net.core_network.edges(data=True)
    }


def test_copy_network_preserves_weights_and_nodes():
    net = multinet.multi_layer_network(directed=False, verbose=False)
    net.add_edges(
        [
            ["A", "L1", "B", "L1", 2.5],
            ["A", "L1", "A", "L1", 1.0],
        ],
        input_type="list",
    )

    copied = _copy_network(net)

    assert set(net.get_nodes()) == set(copied.get_nodes())
    assert _edge_weights(net) == _edge_weights(copied)


def test_configuration_model_preserves_degrees_for_pair():
    net = multinet.multi_layer_network(directed=False, verbose=False)
    net.add_edges([["U", "L", "V", "L", 1.0]], input_type="list")

    original_degrees = dict(net.core_network.degree())
    randomized = configuration_model(net, seed=7)

    assert set(randomized.get_nodes()) == set(net.get_nodes())
    assert dict(randomized.core_network.degree()) == original_degrees


def test_configuration_model_preserves_degrees_for_complete_graph_regression():
    """Regression: configuration_model must not change degrees when simplifying."""
    net = multinet.multi_layer_network(directed=False, verbose=False)
    nodes = ["A", "B", "C", "D"]
    edges = []
    for i, u in enumerate(nodes):
        for v in nodes[i + 1 :]:
            edges.append([u, "L", v, "L", 1.0])
    net.add_edges(edges, input_type="list")

    original_degrees = dict(net.core_network.degree())
    randomized = configuration_model(net, seed=0)

    assert set(randomized.get_nodes()) == set(net.get_nodes())
    assert dict(randomized.core_network.degree()) == original_degrees


def test_erdos_renyi_complete_graph_stays_complete():
    net = multinet.multi_layer_network(directed=False, verbose=False)
    net.add_edges(
        [
            ["A", "L", "B", "L", 1.0],
            ["A", "L", "C", "L", 1.0],
            ["B", "L", "C", "L", 1.0],
        ],
        input_type="list",
    )

    expected_edges = {
        frozenset({("A", "L"), ("B", "L")}),
        frozenset({("A", "L"), ("C", "L")}),
        frozenset({("B", "L"), ("C", "L")}),
    }

    randomized = erdos_renyi_model(net, seed=0)
    produced_edges = {frozenset({u, v}) for u, v in randomized.core_network.edges()}

    assert produced_edges == expected_edges


def test_edge_swap_preserves_degree_sequence():
    net = multinet.multi_layer_network(directed=False, verbose=False)
    net.add_edges(
        [
            ["A", "L", "B", "L", 1.0],
            ["B", "L", "C", "L", 1.0],
            ["C", "L", "D", "L", 1.0],
            ["D", "L", "A", "L", 1.0],
        ],
        input_type="list",
    )

    original_degrees = dict(net.core_network.degree())
    swapped = edge_swap_model(net, num_swaps=8, seed=2)

    assert dict(swapped.core_network.degree()) == original_degrees
    assert set(swapped.get_nodes()) == set(net.get_nodes())


def test_layer_shuffle_preserves_edge_weights():
    net = multinet.multi_layer_network(directed=False, verbose=False)
    net.add_edges(
        [
            ["A", "L1", "B", "L1", 2.5],
            ["A", "L2", "B", "L2", 3.5],
            ["B", "L2", "C", "L2", 4.5],
        ],
        input_type="list",
    )

    original_weights = Counter(
        data.get("weight") for _, _, data in net.core_network.edges(data=True)
    )
    shuffled = layer_shuffle_model(net, seed=11)
    shuffled_weights = Counter(
        data.get("weight") for _, _, data in shuffled.core_network.edges(data=True)
    )

    assert shuffled_weights == original_weights


def test_generate_null_model_uses_per_sample_seeds_consistently():
    from py3plex.nullmodels.executor import generate_null_model

    net = multinet.multi_layer_network(directed=False, verbose=False)
    net.add_edges(
        [
            ["A", "L", "B", "L", 1.0],
            ["B", "L", "C", "L", 1.0],
            ["C", "L", "D", "L", 1.0],
            ["D", "L", "A", "L", 1.0],
            ["A", "L", "C", "L", 1.0],
        ],
        input_type="list",
    )

    result = generate_null_model(net, model="erdos_renyi", num_samples=3, seed=10)

    for i, sample in enumerate(result.samples):
        reference = erdos_renyi_model(net, seed=10 + i)
        assert set(sample.core_network.edges()) == set(reference.core_network.edges())


def test_layer_shuffle_keeps_layer_groups_intact():
    net = multinet.multi_layer_network(directed=False, verbose=False)
    net.add_edges(
        [
            ["A", "L1", "B", "L1", 1.0],
            ["C", "L2", "D", "L2", 1.0],
        ],
        input_type="list",
    )

    original_nodes = list(net.get_nodes())
    original_layer_sources = defaultdict(set)
    for src, layer in original_nodes:
        original_layer_sources[layer].add(src)

    shuffled = layer_shuffle_model(net, seed=5)
    new_nodes = list(shuffled.get_nodes())
    new_layer_sources = defaultdict(set)
    for src, layer in new_nodes:
        new_layer_sources[layer].add(src)

    assert Counter(layer for _, layer in new_nodes) == Counter(
        layer for _, layer in original_nodes
    )

    for sources in original_layer_sources.values():
        matches = [layer for layer, vals in new_layer_sources.items() if vals == sources]
        assert len(matches) == 1


try:
    from hypothesis import given, settings, strategies as st
except Exception:  # pragma: no cover
    HYPOTHESIS_AVAILABLE = False
else:
    HYPOTHESIS_AVAILABLE = True


def _index_to_pair(n, index):
    pairs = []
    for i in range(n):
        for j in range(i + 1, n):
            pairs.append((i, j))
    return pairs[index]


@pytest.mark.skipif(not HYPOTHESIS_AVAILABLE, reason="hypothesis not installed")
@settings(max_examples=50, deadline=None)
@given(
    n=st.integers(min_value=1, max_value=7),
    edge_indices=st.data(),
)
def test_configuration_model_preserves_degrees_property(n, edge_indices):
    """Configuration model should preserve per-node degrees for any simple graph."""
    max_edges = n * (n - 1) // 2
    if max_edges == 0:
        indices = set()
    else:
        indices = edge_indices.draw(
            st.sets(st.integers(min_value=0, max_value=max_edges - 1))
        )

    net = multinet.multi_layer_network(directed=False, verbose=False)
    net.add_nodes([{"source": f"n{i}", "type": "L"} for i in range(n)])
    edges = []
    for idx in sorted(indices):
        i, j = _index_to_pair(n, idx)
        edges.append([f"n{i}", "L", f"n{j}", "L", 1.0])
    if edges:
        net.add_edges(edges, input_type="list")

    original_degrees = dict(net.core_network.degree())
    randomized = configuration_model(net, seed=0)

    assert set(randomized.get_nodes()) == set(net.get_nodes())
    assert dict(randomized.core_network.degree()) == original_degrees
