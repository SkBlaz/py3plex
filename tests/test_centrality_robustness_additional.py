"""Additional tests for robustness-focused centrality utilities."""

import math
import numpy as np
import pytest

from py3plex.centrality import robustness_centrality
from py3plex.centrality.robustness import (
    _compute_avg_shortest_path,
    _compute_metric,
    _remove_layer,
    _remove_node,
)
from py3plex.core import multinet


def _chain_network() -> multinet.multi_layer_network:
    net = multinet.multi_layer_network(directed=False, verbose=False)
    net.add_edges(
        [
            ["a", "L0", "b", "L0", 1.0],
            ["b", "L0", "c", "L0", 1.0],
        ],
        input_type="list",
    )
    return net


def test_remove_node_preserves_isolates_and_other_edges():
    """Removing a node should not delete unrelated edges or isolates."""
    net = multinet.multi_layer_network(directed=False, verbose=False)
    net.add_edges(
        [
            ["a", "L0", "b", "L0", 1.0],
            ["d", "L0", "e", "L0", 1.0],
        ],
        input_type="list",
    )
    net.add_nodes([{"source": "z", "type": "L1"}])

    pruned = _remove_node(net, ("a", "L0"))

    assert ("a", "L0") in net.core_network  # original unchanged
    assert ("a", "L0") not in pruned.core_network
    assert ("d", "L0") in pruned.core_network and ("e", "L0") in pruned.core_network
    assert ("z", "L1") in pruned.core_network  # isolate preserved
    assert pruned.core_network.has_edge(("d", "L0"), ("e", "L0"))


def test_remove_layer_preserves_other_layers_and_isolates():
    """Removing a layer should keep nodes from remaining layers, including isolates."""
    net = multinet.multi_layer_network(directed=False, verbose=False)
    net.add_edges(
        [
            ["a", "L0", "b", "L0", 1.0],
            ["c", "L1", "d", "L1", 1.0],
        ],
        input_type="list",
    )
    net.add_nodes([{"source": "e", "type": "L2"}])

    pruned = _remove_layer(net, "L0")

    assert ("a", "L0") in net.core_network  # original unchanged
    assert all(node[1] != "L0" for node in pruned.core_network.nodes)
    assert pruned.core_network.has_edge(("c", "L1"), ("d", "L1"))
    assert ("e", "L2") in pruned.core_network  # isolate in other layer kept


def test_avg_shortest_path_leaf_removal_improves_metric():
    """Leaf removal on a chain should reduce average path length (negative robustness)."""
    net = _chain_network()

    scores = robustness_centrality(net, target="node", metric="avg_shortest_path", seed=7)

    assert scores[("a", "L0")] < 0  # removing a leaf makes paths shorter
    assert scores[("c", "L0")] < 0


def test_avg_shortest_path_large_component_skips_with_warning():
    """Large components (>1000 nodes) should be skipped with a warning and yield inf."""
    net = multinet.multi_layer_network(directed=False, verbose=False)
    edges = []
    for idx in range(1000):
        edges.append([f"n{idx}", "L0", f"n{idx+1}", "L0", 1.0])
    net.add_edges(edges, input_type="list")

    with pytest.warns(RuntimeWarning, match="Skipping large component"):
        avg_len = _compute_avg_shortest_path(net)

    assert math.isinf(avg_len)


def test_compute_metric_invalid_choice_raises():
    """_compute_metric should raise ValueError on unsupported metrics."""
    net = _chain_network()
    rng = np.random.default_rng(0)

    with pytest.raises(ValueError):
        _compute_metric(net, "not_a_metric", {}, rng)


def test_avg_shortest_path_disconnected_nodes_has_zero_impact():
    """When paths are infinite before and after removal, robustness should be 0 not NaN."""
    net = multinet.multi_layer_network(directed=False, verbose=False)
    net.add_nodes(
        [
            {"source": "x", "type": "L0"},
            {"source": "y", "type": "L0"},
        ]
    )

    scores = robustness_centrality(
        net,
        target="node",
        metric="avg_shortest_path",
        sample_nodes=list(net.get_nodes()),
        seed=1,
    )

    assert all(score == 0.0 for score in scores.values())


def test_avg_shortest_path_bridge_removal_yields_infinite_impact():
    """Removing a bridge that disconnects the graph should give infinite impact."""
    net = _chain_network()

    scores = robustness_centrality(
        net, target="node", metric="avg_shortest_path", seed=0
    )

    assert math.isinf(scores[("b", "L0")])
    assert math.isfinite(scores[("a", "L0")])
    assert math.isfinite(scores[("c", "L0")])


def test_missing_layer_in_sample_yields_zero_impact():
    """Sampling a non-existent layer should return zero impact without error."""
    net = _chain_network()

    scores = robustness_centrality(
        net,
        target="layer",
        metric="giant_component",
        sample_layers=["L0", "L_missing"],
        seed=3,
    )

    assert scores["L_missing"] == 0.0
