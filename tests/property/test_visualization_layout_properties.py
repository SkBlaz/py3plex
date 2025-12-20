from __future__ import annotations

import numpy as np
import pytest

hypothesis = pytest.importorskip("hypothesis")
from hypothesis import given, settings, strategies as st  # noqa: E402
from hypothesis import HealthCheck  # noqa: E402

import networkx as nx  # noqa: E402

from py3plex.visualization.layout_algorithms import compute_random_layout  # noqa: E402


@st.composite
def _small_graph(draw):
    n = draw(st.integers(min_value=1, max_value=12))
    nodes = list(range(n))
    # Any subset of undirected edges (no self-loops)
    all_edges = [(i, j) for i in nodes for j in range(i + 1, n)]
    if all_edges:
        edge_subset = draw(st.sets(st.sampled_from(all_edges), max_size=len(all_edges)))
    else:
        edge_subset = set()
    g = nx.Graph()
    g.add_nodes_from(nodes)
    g.add_edges_from(edge_subset)
    return g


@given(_small_graph())
@settings(max_examples=40, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_compute_random_layout_produces_unit_square_positions(g):
    pos = compute_random_layout(g, seed=0)

    assert set(pos.keys()) == set(g.nodes())
    for p in pos.values():
        arr = np.asarray(p)
        assert arr.shape == (2,)
        assert np.all(arr >= 0.0)
        assert np.all(arr < 1.0)
