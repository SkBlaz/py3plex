"""Deterministic oracle/regression tests for py3plex.uncertainty.

These tests focus on correctness properties that should hold exactly (or nearly
exactly) under specific resampling/null-model modes, rather than only checking
output shapes/keys.
"""

from __future__ import annotations

import numpy as np
import pytest

from py3plex.core import multinet
from py3plex.uncertainty import bootstrap_metric, null_model_metric
from py3plex.uncertainty import bootstrap as bootstrap_impl
from py3plex.uncertainty import null_models as null_models_impl


def _tiny_single_layer_net() -> multinet.multi_layer_network:
    net = multinet.multi_layer_network(directed=False, verbose=False)
    net.add_edges([["a", "L0", "b", "L0", 1.0]], input_type="list")
    return net


def _degree_metric(network: multinet.multi_layer_network):
    if not hasattr(network, "core_network") or network.core_network is None:
        return {}
    return {n: float(network.core_network.degree(n)) for n in network.get_nodes()}


def test_resample_nodes_permute_preserves_edges_and_nodes():
    """Permuting nodes should keep the induced subgraph identical."""
    net = _tiny_single_layer_net()
    rng = np.random.default_rng(0)

    boot_net = bootstrap_impl._resample_nodes(net, mode="permute", rng=rng)

    assert set(boot_net.get_nodes()) == set(net.get_nodes())
    assert len(list(boot_net.get_edges())) == len(list(net.get_edges()))


def test_bootstrap_nodes_permute_is_invariant_for_degree_metric():
    """Under unit=nodes + mode=permute, the graph structure is unchanged."""
    net = _tiny_single_layer_net()
    observed = _degree_metric(net)

    result = bootstrap_metric(
        net,
        _degree_metric,
        n_boot=5,
        unit="nodes",
        mode="permute",
        random_state=123,
    )

    idx = result["index"]
    assert idx == sorted(observed.keys(), key=lambda x: str(x))
    np.testing.assert_allclose(result["mean"], np.array([observed[k] for k in idx]))
    assert np.all(result["std"] == 0)
    np.testing.assert_allclose(result["ci_low"], result["mean"])
    np.testing.assert_allclose(result["ci_high"], result["mean"])


def test_bootstrap_n_boot_1_std_is_finite_and_zero_for_deterministic_case():
    """With a single replicate, bootstrap std should not be NaN."""
    net = _tiny_single_layer_net()
    result = bootstrap_metric(
        net,
        _degree_metric,
        n_boot=1,
        unit="edges",
        mode="permute",
        random_state=0,
    )
    assert np.isfinite(result["std"]).all()
    assert np.all(result["std"] == 0)


def test_null_model_n_null_1_produces_finite_zscores():
    """With a single null replicate, std/zscore should not become NaN."""
    net = _tiny_single_layer_net()
    result = null_model_metric(
        net,
        _degree_metric,
        n_null=1,
        model="degree_preserving",
        random_state=0,
    )
    assert np.isfinite(result["std_null"]).all()
    assert np.isfinite(result["zscore"]).all()
    assert np.all(result["pvalue"] >= 0)
    assert np.all(result["pvalue"] <= 1)


def test_erdos_renyi_null_does_not_create_nested_tuple_nodes():
    """ER null should not create nodes like ((id, layer), new_layer)."""
    net = _tiny_single_layer_net()
    rng = np.random.default_rng(0)

    null_net = null_models_impl._generate_erdos_renyi_null(net, rng)
    nodes = list(null_net.get_nodes())
    # In py3plex core, nodes are tuples (node_id, layer)
    assert nodes, "Expected at least one node in ER null model"
    assert all(isinstance(n, tuple) and len(n) == 2 for n in nodes)
    assert all(isinstance(n[0], str) for n in nodes)
    assert all(isinstance(n[1], str) for n in nodes)


def test_configuration_null_does_not_create_nested_tuple_nodes():
    """Configuration null should preserve node typing without nesting tuples."""
    net = _tiny_single_layer_net()
    rng = np.random.default_rng(0)

    null_net = null_models_impl._generate_configuration_null(net, rng)
    nodes = list(null_net.get_nodes())
    # For tiny graphs it should still produce a graph on the same node type.
    if nodes:
        assert all(isinstance(n, tuple) and len(n) == 2 for n in nodes)
        assert all(isinstance(n[0], str) for n in nodes)
        assert all(isinstance(n[1], str) for n in nodes)

