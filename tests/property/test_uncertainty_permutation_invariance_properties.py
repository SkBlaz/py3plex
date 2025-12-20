"""Property-based tests for invariants of bootstrap/null-model modes."""

from __future__ import annotations

import numpy as np
import pytest

hypothesis = pytest.importorskip("hypothesis")
from hypothesis import given, settings, strategies as st, assume  # noqa: E402
from hypothesis import HealthCheck  # noqa: E402

from py3plex.core import multinet  # noqa: E402
from py3plex.uncertainty import bootstrap_metric  # noqa: E402


@st.composite
def _simple_single_layer_graph(draw):
    n = draw(st.integers(min_value=2, max_value=6))
    layer = "L0"
    all_pairs = [(i, j) for i in range(n) for j in range(i + 1, n)]
    edges_idx = draw(st.sets(st.sampled_from(all_pairs), min_size=1, max_size=len(all_pairs)))
    edges = [[f"n{i}", layer, f"n{j}", layer, 1.0] for (i, j) in edges_idx]
    return n, edges


def _degree_metric(network: multinet.multi_layer_network):
    if not hasattr(network, "core_network") or network.core_network is None:
        return {}
    return {n: float(network.core_network.degree(n)) for n in network.get_nodes()}


@given(_simple_single_layer_graph())
@settings(max_examples=40, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_bootstrap_edge_permutation_keeps_degree_exactly(graph_data):
    """Edge permutation should not change degree distribution, so std=0."""
    _, edges = graph_data
    net = multinet.multi_layer_network(directed=False, verbose=False)
    net.add_edges(edges, input_type="list")

    observed = _degree_metric(net)
    assume(observed)  # guard against pathological empty core_network

    result = bootstrap_metric(
        net,
        _degree_metric,
        n_boot=5,
        unit="edges",
        mode="permute",
        random_state=123,
    )

    idx = result["index"]
    np.testing.assert_allclose(result["mean"], np.array([observed[k] for k in idx]))
    assert np.all(result["std"] == 0)

