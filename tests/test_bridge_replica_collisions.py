"""Distinct replicas must remain distinct when their display strings collide."""

import networkx as nx
import pytest

from py3plex.core.multinet import multi_layer_network
from py3plex.io.multinet_bridge import (
    multilayergraph_to_multinet,
    multinet_to_multilayergraph,
)


@pytest.mark.parametrize(
    "replicas",
    [
        [(1, "L"), ("1", "L"), ("1", "L@@@1")],
        [("a@@@b", "c"), ("a", "b@@@c")],
        [("a", 1), ("a", "1")],
    ],
)
@pytest.mark.parametrize("reverse", [False, True])
@pytest.mark.parametrize("directed", [False, True])
def test_export_roundtrip_keeps_colliding_replicas(replicas, reverse, directed):
    ordered = list(reversed(replicas)) if reverse else replicas
    net = multi_layer_network(directed=directed, verbose=False)
    net.core_network = nx.MultiDiGraph() if directed else nx.MultiGraph()
    for index, replica in enumerate(ordered):
        net.core_network.add_node(replica, identity=index)
    # Parallel edges between the colliding replicas must use their actual IDs.
    for index, replica in enumerate(ordered[1:], 1):
        net.core_network.add_edge(ordered[0], replica, key="first", weight=index)
        net.core_network.add_edge(ordered[0], replica, key="second", weight=index + 10)

    exported = multinet_to_multilayergraph(net)
    assert len(exported.nodes) == len(ordered)
    assert exported == multinet_to_multilayergraph(net)
    restored = multilayergraph_to_multinet(exported)

    assert restored.directed == directed
    assert nx.utils.graphs_equal(restored.core_network, net.core_network)
