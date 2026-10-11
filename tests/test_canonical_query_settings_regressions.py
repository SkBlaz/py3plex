"""Canonical provenance must retain execution-changing query settings."""

from copy import deepcopy

import pytest

from py3plex.dsl import Q
from py3plex.dsl.ast import (
    ApproximationSpec,
    EmbeddingSpec,
    canonicalize_ast,
)
from py3plex.dsl.provenance import ast_fingerprint


def configured_ast(setting):
    query = Q.nodes().compute("betweenness_centrality", "degree").uq(
        method="perturbation", n_samples=4, seed=42
    ).to_ast()
    metric = query.select.compute[0 if setting == "approx" else 1]
    if setting == "approx":
        metric.approx = ApproximationSpec(
            enabled=True, method="sampling", params={"n_samples": 2, "seed": 7}
        )
    elif setting == "kind":
        metric.kind = "in"
    elif setting == "uncertainty_explicit":
        metric.uncertainty_explicit = False
    elif setting == "mode":
        query.select.uq_config.mode = "propagate"
    elif setting == "keep_samples":
        query.select.uq_config.keep_samples = True
    elif setting == "reduce":
        query.select.uq_config.reduce = "gaussian"
    elif setting == "embedding_spec":
        query.select.embedding_spec = EmbeddingSpec(dim=2, seed=7)
    return query


SETTINGS = [
    "approx", "kind", "uncertainty_explicit", "mode", "keep_samples", "reduce",
    "embedding_spec",
]


@pytest.mark.parametrize("setting", SETTINGS)
def test_canonicalization_retains_execution_settings(setting):
    original = configured_ast(setting)
    before = deepcopy(original)
    canonical = canonicalize_ast(original)
    assert canonical.select.compute == original.select.compute
    assert canonical.select.uq_config == original.select.uq_config
    assert canonical.select.embedding_spec == original.select.embedding_spec
    assert original == before


@pytest.mark.parametrize("setting", SETTINGS)
def test_execution_settings_do_not_collide_in_provenance(setting):
    default = configured_ast("default")
    configured = configured_ast(setting)
    assert ast_fingerprint(default) != ast_fingerprint(configured)


def test_approximation_seed_changes_provenance():
    first = configured_ast("approx")
    second = deepcopy(first)
    second.select.compute[0].approx.params["seed"] = 9
    assert ast_fingerprint(first) != ast_fingerprint(second)


def test_canonical_query_preserves_explicit_metric_uq_opt_out():
    import networkx as nx

    from py3plex.core.multinet import multi_layer_network
    from py3plex.dsl.executor import execute_ast

    network = multi_layer_network(directed=False)
    network.core_network = nx.path_graph([("a", "L"), ("b", "L"), ("c", "L")])
    query = Q.nodes().compute("degree", uncertainty=False).uq(
        method="perturbation", n_samples=4, seed=42
    ).to_ast()
    expected = execute_ast(network, query)
    actual = execute_ast(network, canonicalize_ast(query))
    assert actual.items == expected.items
    assert actual.attributes == expected.attributes
