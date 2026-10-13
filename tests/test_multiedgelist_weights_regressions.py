"""Weighted multilayer exports must survive the public save/load round trip."""

from collections import Counter

import networkx as nx
import pytest

from py3plex.core import multinet


@pytest.mark.parametrize('directed', [False, True])
@pytest.mark.parametrize('encoded', [False, True])
def test_multiedgelist_preserves_edge_weights(tmp_path, directed, encoded):
    graph = nx.MultiDiGraph() if directed else nx.MultiGraph()
    graph.add_edge(('alice', 'social'), ('bob', 'social'), weight=2.75)
    graph.add_edge(('alice', 'social'), ('bob', 'social'), weight=0.0)
    graph.add_edge(('bob', 'social'), ('alice', 'work'), weight=-3.5)
    graph.add_edge(('alice', 'work'), ('alice', 'work'))
    if directed:
        graph.add_edge(('bob', 'social'), ('alice', 'social'), weight=9.25)
    network = multinet.multi_layer_network(directed=directed)
    network.core_network = graph
    path = tmp_path / 'weighted.txt'
    output_type = 'multiedgelist_encoded' if encoded else 'multiedgelist'
    network.save_network(str(path), output_type=output_type)
    loaded = multinet.multi_layer_network(directed=directed)
    loaded.load_network(str(path), input_type='multiedgelist', directed=directed)

    def edge_records(graph, remap=False):
        records = []
        for source, target, data in graph.edges(data=True):
            if remap:
                source = (network.node_map[source[0]], network.layer_map[source[1]])
                target = (network.node_map[target[0]], network.layer_map[target[1]])
            endpoints = (source, target) if directed else frozenset((source, target))
            records.append((endpoints, float(data.get('weight', 1))))
        return Counter(records)

    assert loaded.core_network.is_directed() == directed
    assert edge_records(loaded.core_network) == edge_records(graph, remap=encoded)
    assert graph.number_of_edges() == loaded.core_network.number_of_edges()
