"""Regression coverage for cache, replay, prediction, and multiplex correctness."""

import networkx as nx
import numpy as np
import pytest

from py3plex.core.multinet import multi_layer_network
from py3plex.dsl import Q
from py3plex.dsl.errors import SplitStrategyError
from py3plex.dsl.program.cache import get_global_cache, graph_fingerprint
from py3plex.embeddings.cache import cache_stats, clear_cache
from py3plex.provenance import replay_from_bundle
from py3plex.provenance.capture import (
    NetworkCapture,
    capture_network,
    restore_network,
)
from py3plex.temporal_view import TemporalMultinetView
from py3plex.uncertainty.resampling_graph import (
    bootstrap_network_edges,
    perturb_network_edges,
)


def _network(edges, nodes=(), *, directed=False, multiplex=False):
    graph = nx.MultiDiGraph() if directed else nx.MultiGraph()
    graph.add_nodes_from(nodes)
    graph.add_edges_from(edges)
    return multi_layer_network.from_networkx(
        graph, network_type="multiplex" if multiplex else "multilayer"
    )


def test_program_cache_distinguishes_graphs_and_attribute_mutations():
    first = _network([], [(("a", "L"), {"score": 7})])
    second = _network([], [(("b", "L"), {"score": 7})])
    # Exercise ordinary two-field edges as well as node attribute changes.
    first.core_network.add_edge(("a", "L"), ("c", "L"))
    second.core_network.add_edge(("b", "L"), ("c", "L"))
    program = Q.nodes().where(score__gt=5).to_program()
    cache = get_global_cache()
    cache.clear()
    try:
        assert program.execute(first, seed=9).items == [("a", "L")]
        assert program.execute(second, seed=9).items == [("b", "L")]
        first.core_network.nodes[("a", "L")]["score"] = 2
        assert program.execute(first, seed=9).items == []
        first.core_network.graph["unsupported"] = object()
        assert program.execute(first, seed=9).items == []
        assert cache.size() == 3
    finally:
        cache.clear()


@pytest.mark.parametrize(
    "split", ["random_holdout", "by_layer_holdout", "temporal_holdout"]
)
def test_prediction_holdouts_keep_endpoint_pairs_and_labels_disjoint(split):
    a, b, c, d, e, f = [(node, "L") for node in "abcdef"]
    network = _network(
        [
            (a, b, {"t": 1}),
            (b, c, {"t": 2}),
            (a, b, {"t": 7}),
            (c, d, {"t": 3}),
            (d, e, {"t": 4}),
        ],
        [a, b, c, d, e, f],
    )
    query = Q.predict.links()
    if split == "temporal_holdout":
        query.temporal_holdout(0.5)
    else:
        getattr(query, split)(0.5, seed=42)
    result = (
        query.model("common_neighbors")
        .negative_sampling(strategy="uniform", ratio=1.0, seed=1)
        .eval(["roc_auc"])
        .execute(network)
    )
    records = result.meta["split_records"]
    positives = [row for row in records if row["label"] == 1]
    negatives = [row for row in records if row["label"] == 0]
    assert len(positives) == len({row["edge"] for row in positives}) == 4
    assert not {row["edge"] for row in positives} & {row["edge"] for row in negatives}
    if split == "temporal_holdout":
        assert next(row for row in positives if row["edge"] == (a, b))["edge_time"] == 1


def test_snapshot_replay_preserves_attribute_filters_and_keyed_multiplex_edges(
    tmp_path,
):
    a = (("a", 1), "L")
    b, a_other = ("b", "L"), (("a", 1), "M")
    network = _network(
        [
            (a, b, ("k", 1), {"weight": 7, "kind": "observed"}),
            (a, b, "other", {"weight": 3}),
            (a, a_other, "coupling", {"weight": 9, "type": "coupling"}),
        ],
        [(a, {"score": 10, "source": "attribute"})],
        multiplex=True,
    )
    network.coupling_weight = 9
    snapshot = capture_network(network)
    clone = restore_network(snapshot)
    assert clone.network_type == "multiplex"
    assert clone.coupling_weight == 9
    assert list(clone.core_network.nodes(data=True)) == list(
        network.core_network.nodes(data=True)
    )
    assert list(clone.core_network.edges(keys=True, data=True)) == list(
        network.core_network.edges(keys=True, data=True)
    )

    multilayer = multi_layer_network.from_networkx(network.core_network)
    result = (
        Q.edges()
        .where(weight__gt=5, kind="observed")
        .provenance(mode="replayable", capture="snapshot")
        .execute(multilayer)
    )
    assert result.count == 1
    assert result.replay().items == result.items
    bundle = tmp_path / "replay.json.gz"
    result.export_bundle(bundle)
    assert replay_from_bundle(bundle).items == result.items


def test_embedding_cache_tracks_graph_selection_order_and_hits():
    a, b, c, d = [(node, "L") for node in "abcd"]
    network = _network([(a, b), (b, c), (c, a), (d, a)])
    other = _network([(a, b), (a, c), (a, d), (c, d)])

    def run(graph, limit, *, sort_by_degree=False, cache=True):
        query = Q.nodes()
        if sort_by_degree:
            query = query.compute("degree").order_by("degree")
        return (
            query.limit(limit)
            .embed(method="netmf", dim=2, seed=42, cache=cache)
            .execute(graph)
        )

    clear_cache()
    try:
        assert run(network, 1).embeddings["node"].shape == (1, 2)
        assert run(network, 4).embeddings["node"].shape == (4, 2)
        for graph, sort_by_degree in [(network, True), (other, False)]:
            expected = run(graph, 4, sort_by_degree=sort_by_degree, cache=False)
            actual = run(graph, 4, sort_by_degree=sort_by_degree)
            assert actual.items == expected.items
            np.testing.assert_allclose(
                actual.embeddings["node"], expected.embeddings["node"]
            )
        run(network, 4)
        assert cache_stats() == {"hits": 1, "misses": 4}
    finally:
        clear_cache()


def test_edge_resampling_preserves_replicas_weights_and_multiplex_coupling():
    a, b, isolate = ("a", "L"), ("b", "L"), ("isolate", "L")
    other = ("a", "M")
    network = _network(
        [
            (a, b, 0, {"weight": 7, "label": "first"}),
            (a, b, 1, {"weight": 3, "label": "second"}),
            (a, other, "fixed", {"type": "coupling", "weight": 9}),
        ],
        [(isolate, {"score": 5})],
        directed=True,
        multiplex=True,
    )
    original = list(network.core_network.edges(keys=True, data=True))
    perturbed = perturb_network_edges(network, edge_drop_p=0, seed=2)
    assert perturbed.directed and perturbed.network_type == "multiplex"
    assert dict(perturbed.core_network.nodes(data=True)) == dict(
        network.core_network.nodes(data=True)
    )
    assert {(u, v, key): attrs for u, v, key, attrs in original} == {
        (u, v, key): attrs
        for u, v, key, attrs in perturbed.core_network.edges(keys=True, data=True)
    }
    dropped = perturb_network_edges(network, edge_drop_p=1, seed=2)
    assert list(dropped.get_edges()) == []
    assert dict(dropped.core_network.nodes(data=True)) == dict(
        network.core_network.nodes(data=True)
    )
    # Seed zero selects the second edge twice, so both draws must survive.
    bootstrapped = bootstrap_network_edges(network, seed=0)
    interactions = list(bootstrapped.get_edges(data=True))
    assert len(interactions) == 2
    assert {attrs["weight"] for _, _, _, attrs in interactions} == {3}
    assert bootstrapped.core_network.edges[a, other, "fixed"]["weight"] == 9
    assert list(network.core_network.edges(keys=True, data=True)) == original


@pytest.mark.parametrize("directed", [False, True])
def test_multiplex_supra_adjacency_matches_weighted_graph_and_replica_order(directed):
    a, b, other_b, other_a, extra = (
        ("a", "L"),
        ("b", "L"),
        ("b", "M"),
        ("a", "M"),
        ("x", 2),
    )
    network = _network(
        [
            (a, b, {"weight": 2}),
            (other_b, other_a, {"weight": 3}),
            (a, other_a, {"weight": 9, "type": "coupling"}),
            (a, other_a, {"weight": 4, "type": "coupling"}),
            (b, extra, {"weight": 5}),
        ],
        [a, b, other_b, other_a, extra],
        directed=directed,
        multiplex=True,
    )
    actual = network.get_supra_adjacency_matrix().toarray()
    order = network.node_order_in_matrix
    assert order == [a, b, other_b, other_a, extra]
    expected = nx.to_numpy_array(network.core_network, nodelist=order)
    np.testing.assert_array_equal(actual, expected)
    assert actual[order.index(a), order.index(other_a)] == 13


def test_program_cache_tracks_edge_weights_with_equal_topology():
    a, b = ("a", "L"), ("b", "L")
    network = _network([(a, b, {"weight": 7})])
    program = Q.edges().where(weight__gt=5).to_program()
    cache = get_global_cache()
    cache.clear()
    try:
        assert program.execute(network, seed=5).count == 1
        network.core_network.edges[a, b, 0]["weight"] = 3
        assert program.execute(network, seed=5).count == 0
        assert cache.size() == 2
    finally:
        cache.clear()


@pytest.mark.parametrize("bad_time", [None, "unknown", float("inf"), float("nan")])
def test_temporal_holdout_rejects_invalid_observations(bad_time):
    a, b, c = [(node, "L") for node in "abc"]
    network = _network([(a, b, {"t": 1}), (b, c, {"t": bad_time})])
    with pytest.raises(SplitStrategyError, match="finite temporal edge attributes"):
        Q.predict.links().temporal_holdout(0.5).execute(network)


def test_prediction_distinguishes_reciprocal_arcs():
    a, b, c, d = [(node, "L") for node in "abcd"]
    network = _network([(a, b), (b, a), (a, b), (c, d)], directed=True)
    result = (
        Q.predict.links()
        .random_holdout(0.5, seed=1)
        .negative_sampling(strategy="uniform", ratio=1, seed=2)
        .execute(network)
    )
    positives = [r["edge"] for r in result.meta["split_records"] if r["label"]]
    assert len(positives) == 3
    assert set(positives) == {(a, b), (b, a), (c, d)}


def test_restore_legacy_snapshot_without_replica_or_key_fields():
    capture = NetworkCapture.from_dict(
        {
            "nodes": [{"id": "a", "layer": "L"}, {"id": "b", "layer": "L"}],
            "edges": [
                {
                    "source": "a",
                    "target": "b",
                    "source_layer": "L",
                    "target_layer": "L",
                    "weight": 4,
                }
            ],
            "directed": True,
        }
    )
    graph = restore_network(capture).core_network
    assert graph.is_directed() and graph.is_multigraph()
    assert list(graph.edges(data="weight")) == [(("a", "L"), ("b", "L"), 4)]


def test_snapshot_without_attributes_retains_weights_and_coupling():
    a, b = ("a", "L"), ("a", "M")
    network = _network(
        [(a, b, "coupling", {"weight": 4, "type": "coupling", "extra": True})],
        [(a, {"score": 7})],
        multiplex=True,
    )
    clone = restore_network(capture_network(network, include_attributes=False))
    assert dict(clone.core_network.nodes[a]) == {}
    assert clone.core_network.edges[a, b, "coupling"] == {
        "weight": 4,
        "type": "coupling",
    }


def test_edge_embedding_cache_handles_records_with_attributes():
    a, b, c, d = [(node, "L") for node in "abcd"]
    network = _network([(a, b), (b, c), (c, d), (d, a)])
    clear_cache()
    try:

        def run(limit):
            return Q.edges().limit(limit).embed(dim=2, seed=42).execute(network)

        expected = run(2).embeddings["edge"]
        assert run(1).embeddings["edge"].shape == (1, 2)
        np.testing.assert_array_equal(run(2).embeddings["edge"], expected)
        assert cache_stats() == {"hits": 1, "misses": 2}
    finally:
        clear_cache()


def test_bootstrap_uses_fresh_keys_for_repeated_edges_without_overwriting_originals():
    a, b = ("a", "L"), ("b", "L")
    network = _network(
        [
            (a, b, 1, {"weight": 7}),
            (a, b, 3, {"weight": 3}),
            (a, b, 4, {"weight": 5}),
        ]
    )
    # The sample draws keys 3, 3, and 1. An early automatic key could take key 1.
    graph = bootstrap_network_edges(network, seed=70).core_network
    assert graph.edges[a, b, 1]["weight"] == 7
    assert graph.edges[a, b, 3]["weight"] == 3
    assert sorted(attrs["weight"] for _, _, attrs in graph.edges(data=True)) == [
        3,
        3,
        7,
    ]


def test_simple_graph_sampling_and_replay_preserve_directed_edge_data():
    a, b, c = [(node, "L") for node in "abc"]
    graph = nx.DiGraph()
    graph.add_edge(a, b, weight=7)
    graph.add_node(c, score=3)
    network = multi_layer_network.from_networkx(graph)
    perturbation = perturb_network_edges(network, edge_drop_p=0, seed=5).core_network
    snapshot = restore_network(capture_network(network)).core_network
    bootstrap = bootstrap_network_edges(network, seed=5).core_network
    for output in (perturbation, snapshot, bootstrap):
        assert output.is_directed()
        assert dict(output.nodes(data=True)) == dict(graph.nodes(data=True))
        assert list(output.edges(data=True)) == [(a, b, {"weight": 7})]
    assert not perturbation.is_multigraph()
    assert not snapshot.is_multigraph()
    assert bootstrap.is_multigraph()


def test_empty_multiplex_graph_has_empty_supra_adjacency():
    network = _network([], multiplex=True)
    assert network.get_supra_adjacency_matrix().shape == (0, 0)
    assert network.node_order_in_matrix == []


def test_program_cache_bypasses_temporal_views_of_the_same_base_graph():
    a, b, c = [(node, "L") for node in "abc"]
    network = _network([(a, b, {"t": 1}), (b, c, {"t": 3})])
    view = TemporalMultinetView(network)
    program = Q.edges().to_program()
    cache = get_global_cache()
    cache.clear()
    try:
        first = program.execute(view.with_slice(1, 1), seed=9)
        second = program.execute(view.with_slice(3, 3), seed=9)
        assert [edge[:2] for edge in first.items] == [(a, b)]
        assert [edge[:2] for edge in second.items] == [(b, c)]
        assert cache.size() == 0
    finally:
        cache.clear()


def test_network_fingerprint_includes_named_partitions_and_accepts_networkx():
    a, b = ("a", "L"), ("b", "L")
    graph = nx.Graph([(a, b)])
    assert graph_fingerprint(graph) == graph_fingerprint(graph.copy())

    network = multi_layer_network.from_networkx(graph)
    network.assign_partition({a: 0, b: 0}, name="groups")
    original = graph_fingerprint(network)
    network.assign_partition({a: 0, b: 1}, name="groups")
    assert graph_fingerprint(network) != original


def test_embedding_cache_bypasses_graphs_with_unhashable_metadata():
    a, b, c = [(node, "L") for node in "abc"]
    network = _network([(a, b), (b, c), (c, a)])
    network.core_network.graph["opaque"] = object()
    clear_cache()
    try:
        result = Q.nodes().embed(dim=2, seed=42).execute(network)
        assert result.embeddings["node"].shape == (3, 2)
        assert cache_stats() == {"hits": 0, "misses": 0}
    finally:
        clear_cache()


@pytest.mark.parametrize("initialized", [False, True])
def test_edge_resampling_returns_empty_network_when_no_edges_exist(initialized):
    network = multi_layer_network(network_type="multiplex", directed=True)
    if initialized:
        network.add_nodes([{"source": "a", "type": "L", "score": 5}])
    for sample in (
        perturb_network_edges(network, edge_drop_p=0.5, seed=5),
        bootstrap_network_edges(network, seed=5),
    ):
        assert sample.directed and sample.network_type == "multiplex"
        assert list(sample.get_edges()) == []
        assert dict(sample.get_nodes(data=True)) == (
            {("a", "L"): {"score": 5}} if initialized else {}
        )
