"""Regression coverage for paths, exports, and multilayer analysis semantics."""

import json
from pathlib import Path

import networkx as nx
import numpy as np
import pytest

from py3plex.algorithms.community_detection.flow_hierarchy import (
    _build_transition_matrix,
)
from py3plex.core.multinet import multi_layer_network
from py3plex.dsl import L, Q, S, LayerSet
from py3plex.dsl.program.cache import ProgramCache
from py3plex.exceptions import AlgorithmError, Py3plexIOError
from py3plex.io import load_network_from_parquet, save_network_to_parquet
from py3plex.nullmodels.models import edge_swap_model


def _network(edges, *, directed=False, multiplex=False, nodes=()):
    graph = nx.MultiDiGraph() if directed else nx.MultiGraph()
    graph.add_nodes_from(nodes)
    graph.add_edges_from(edges)
    return multi_layer_network.from_networkx(
        graph, network_type="multiplex" if multiplex else "multilayer"
    )


def _paths(network, source, target, *, crossing="allowed", layers=None):
    query = (
        S.paths()
        .from_node(source)
        .to_node(target)
        .semiring("min_plus")
        .lift(attr="weight")
        .crossing_layers(mode=crossing)
        .witness(True)
    )
    if layers is not None:
        query.from_layers(layers)
    return {row["node"]: row for row in query.execute(network).items}


@pytest.mark.parametrize("multiplex", [False, True])
def test_semiring_paths_preserve_undirected_and_parallel_edges(multiplex):
    a, b = ("A", "L"), ("B", "L")
    network = _network(
        [(a, b, "long", {"weight": 9}), (a, b, "short", {"weight": 3})],
        multiplex=multiplex,
    )
    assert _paths(network, "B", "A")["A"] == {
        "node": "A",
        "value": 3.0,
        "path": ["B", "A"],
    }
    assert _paths(network, "A", "B")["B"]["value"] == 3


@pytest.mark.parametrize("multiplex", [False, True])
def test_semiring_paths_and_closure_require_real_replica_transitions(multiplex):
    a, b, other_b, c = ("A", "L"), ("B", "L"), ("B", "M"), ("C", "M")
    network = _network([(a, b), (other_b, c)], directed=True, multiplex=multiplex)
    assert _paths(network, "A", "C", crossing="forbidden")["C"]["value"] == float("inf")
    assert _paths(network, "A", "C")["C"]["path"] is None

    closure = S.closure().semiring("boolean").lift(default=True)
    result = closure.execute(network)
    assert not any(
        row["source"] == "A" and row["target"] == "C" and row["value"]
        for row in result.items
    )

    network.core_network.add_edge(b, other_b, type="coupling", weight=2)
    assert _paths(network, "A", "C")["C"]["value"] == 4
    assert _paths(network, "C", "A")["A"]["path"] is None
    assert _paths(network, "A", "C", crossing="forbidden")["C"]["path"] is None
    assert any(
        row["source"] == "A" and row["target"] == "C" and row["value"]
        for row in closure.execute(network).items
    )


def test_semiring_path_to_explicit_replica_keeps_other_replicas_out_of_result():
    a, b, other_b = ("A", "L"), ("B", "L"), ("B", "M")
    network = _network([(a, b)], nodes=[other_b], directed=True)
    assert _paths(network, a, "B")["B"]["value"] == 1
    assert _paths(network, a, other_b)["B"]["value"] == float("inf")


def test_semiring_expands_wildcards_and_evaluates_layer_difference():
    a, b = ("A", "L"), ("B", "L")
    network = _network([(a, b), (("B", "M"), ("C", "M"))], directed=True)
    assert _paths(network, "A", "B", layers=L["*"])["B"]["value"] == 1
    selected = _paths(network, "A", "B", layers=L["*"] - L["M"])
    assert "C" not in selected
    assert selected["B"]["value"] == 1


def test_graph_program_cache_tracks_nested_named_layer_groups(monkeypatch):
    group_names = {"outer": LayerSet("inner"), "inner": LayerSet("L")}
    monkeypatch.setattr("py3plex.dsl.layers._LAYER_GROUPS", group_names)
    cache = ProgramCache()
    monkeypatch.setattr("py3plex.dsl.program.cache._global_cache", cache)
    a, b = ("A", "L"), ("A", "M")
    network = _network([], nodes=[a, b])
    program = Q.nodes().from_layers(LayerSet("outer")).to_program()
    assert program.execute(network, seed=9).items == [a]
    assert program.execute(network, seed=9).items == [a]
    assert cache.statistics()["hits"] == 1
    LayerSet.define_group("inner", LayerSet("M"))
    assert program.execute(network, seed=9).items == [b]
    assert cache.size() == 2


def test_layer_reduction_uses_shared_degree_support_and_exact_cluster_count():
    a, b = ("A", "L"), ("B", "L")
    other_a, other_b = ("A", "M"), ("B", "M")
    network = _network([(a, b)] + [(other_a, other_b)] * 4)
    result = Q.reduce.layers().target_k(1).execute(network)
    assert result.similarity_matrix[0, 1] == pytest.approx(1 - np.log(2))

    tied = _network([(a, b), (other_a, other_b), (("A", "N"), ("B", "N"))])
    for count in (2, 3):
        result = Q.reduce.layers().target_k(count).execute(tied)
        assert len(set(result.layer_mapping.values())) == count
        assert result.network.layer_count == count


def test_layer_reduction_drops_original_interlayer_edges_before_remapping():
    a, b = ("A", "L"), ("B", "L")
    network = _network(
        [(a, b, {"weight": 1}), (a, ("A", "M"), {"weight": 9})],
        directed=True,
    )
    result = Q.reduce.layers().target_k(1).preserve_interlayer(False).execute(network)
    assert [attrs["weight"] for _, _, attrs in result.network.get_edges(data=True)] == [
        1
    ]
    kept = Q.reduce.layers().target_k(1).preserve_interlayer(True).execute(network)
    assert sorted(
        attrs["weight"] for _, _, attrs in kept.network.get_edges(data=True)
    ) == [1, 9]


@pytest.mark.parametrize("multiplex", [False, True])
def test_flow_alpha_controls_weighted_interlayer_transitions(multiplex):
    a, b, other = ("A", "L"), ("B", "L"), ("A", "M")
    network = _network(
        [(a, b, {"weight": 4}), (a, other, {"type": "coupling", "weight": 2})],
        multiplex=multiplex,
    )
    for alpha, expected in ((0, [0, 1]), (0.5, [2 / 3, 1 / 3]), (1, [1, 0])):
        transition, _, indices = _build_transition_matrix(network, alpha=alpha)
        np.testing.assert_allclose(
            transition.toarray()[indices[a], [indices[b], indices[other]]], expected
        )


@pytest.mark.parametrize("multigraph", [False, True])
def test_directed_swap_preserves_degree_sequences_and_changes_topology(multigraph):
    nodes = [(node, "L") for node in "ABCDEF"]
    original = nx.MultiDiGraph() if multigraph else nx.DiGraph()
    for index, (src, dst) in enumerate(zip(nodes[::2], nodes[1::2])):
        original.add_edge(src, dst, weight=index + 1)
    network = multi_layer_network.from_networkx(original)
    first = edge_swap_model(network, num_swaps=1, seed=42).core_network
    again = edge_swap_model(network, num_swaps=1, seed=42).core_network
    assert set(first.edges()) != set(original.edges())
    assert list(first.edges(data=True)) == list(again.edges(data=True))
    assert dict(first.in_degree()) == dict(original.in_degree())
    assert dict(first.out_degree()) == dict(original.out_degree())
    assert sorted(attrs["weight"] for _, _, attrs in first.edges(data=True)) == [
        1,
        2,
        3,
    ]
    assert nx.utils.graphs_equal(original, network.core_network)


def test_impossible_directed_swap_reports_failure():
    network = _network([(("A", "L"), ("B", "L"))], directed=True)
    with pytest.raises(AlgorithmError, match="completed 0 of 1"):
        edge_swap_model(network, num_swaps=1, seed=42)


def test_parquet_round_trips_keys_and_attributes_absent_from_the_first_row(tmp_path):
    pytest.importorskip("pyarrow")
    a, b, c = ("A", "L"), ("B", 2), ("C", "L")
    network = _network(
        [
            (a, b, "first", {"weight": 3}),
            (a, b, ("second", 1), {"weight": 5, "later": True}),
            (b, c, 2, {"weight": 7}),
        ],
        nodes=[(a, {"common": 1}), (b, {"only_later": "saved"})],
    )
    path = tmp_path / "nested" / "network"
    save_network_to_parquet(network, path)
    restored = load_network_from_parquet(path).core_network
    assert restored.edges[a, b, "first"] == {"weight": 3}
    assert restored.edges[a, b, ("second", 1)] == {"weight": 5, "later": True}
    assert restored.nodes[b]["only_later"] == "saved"


def test_parquet_replacement_restores_previous_export_on_rename_error(
    tmp_path, monkeypatch
):
    pytest.importorskip("pyarrow")
    a, b = ("A", "L"), ("B", "L")
    path = tmp_path / "network"
    save_network_to_parquet(_network([(a, b, {"weight": 3})]), path)
    old = load_network_from_parquet(path)
    replacement = _network([(a, b, {"weight": 7})])
    with monkeypatch.context() as patch:

        def fail_rename(self, destination):
            raise OSError("simulated rename failure")

        patch.setattr(Path, "rename", fail_rename)
        with pytest.raises(Py3plexIOError, match="simulated rename failure"):
            save_network_to_parquet(replacement, path)
    assert nx.utils.graphs_equal(
        old.core_network, load_network_from_parquet(path).core_network
    )
    assert list(tmp_path.iterdir()) == [path]
    save_network_to_parquet(replacement, path)
    assert load_network_from_parquet(path).core_network.edges[a, b, 0]["weight"] == 7


def test_load_legacy_parquet_directory(tmp_path):
    pa = pytest.importorskip("pyarrow")
    pq = pytest.importorskip("pyarrow.parquet")
    pq.write_table(
        pa.Table.from_pylist([{"node": "A@@@L"}, {"node": "B@@@L"}]),
        tmp_path / "nodes.parquet",
    )
    pq.write_table(
        pa.Table.from_pylist(
            [
                {
                    "source": "A@@@L",
                    "target": "B@@@L",
                    "source_layer": "L",
                    "target_layer": "L",
                    "weight": 4,
                }
            ]
        ),
        tmp_path / "edges.parquet",
    )
    (tmp_path / "metadata.json").write_text(
        json.dumps({"directed": False, "layers": ["L"]})
    )
    restored = load_network_from_parquet(tmp_path).core_network
    assert restored.edges[("A", "L"), ("B", "L"), 0]["weight"] == 4
