import pytest


hypothesis = pytest.importorskip("hypothesis")

from hypothesis import given, settings, strategies as st

import networkx as nx

from py3plex.plugins.examples import ExampleNetworkDensity


class _Wrapper:
    def __init__(self, G):
        self.core_network = G


@given(
    n=st.integers(min_value=0, max_value=8),
    edges=st.data(),
)
@settings(max_examples=3, deadline=None)
def test_example_network_density_matches_networkx_density_property(n, edges):
    nodes = list(range(n))
    G = nx.Graph()
    G.add_nodes_from(nodes)

    all_pairs = [(i, j) for i in range(n) for j in range(i + 1, n)]
    if all_pairs:
        chosen = edges.draw(st.sets(st.sampled_from(all_pairs)))
        G.add_edges_from(chosen)

    plugin = ExampleNetworkDensity()
    result = plugin.compute(_Wrapper(G))

    assert result["num_nodes"] == n
    assert result["num_edges"] == G.number_of_edges()
    assert result["density"] == pytest.approx(nx.density(G))

