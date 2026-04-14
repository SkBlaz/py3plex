"""Direct unit tests for py3plex.embeddings submodules."""

from __future__ import annotations

import numpy as np
import pytest
import scipy.sparse as sp

from py3plex.embeddings import cache as cache_mod
from py3plex.embeddings.base import EmbeddingResult
from py3plex.embeddings.cache import (
    cache_get,
    cache_put,
    cache_stats,
    clear_cache,
    make_cache_key,
    make_embed_config_hash,
)
from py3plex.embeddings.link_ops import LINK_OPS, apply_link_op
from py3plex.embeddings.netmf import (
    NetMFEmbedder,
    _build_supra_adjacency,
    _build_union_adjacency,
    _netmf_embed,
)
from py3plex.exceptions import EmbeddingError


class _StubNetwork:
    def __init__(self, edges):
        self._edges = list(edges)

    def get_edges(self):
        return list(self._edges)

    def get_nodes(self):
        nodes = []
        for edge in self._edges:
            if len(edge) >= 2:
                nodes.extend([edge[0], edge[1]])
        return list(dict.fromkeys(nodes))

    def get_layers(self):
        layers = []
        for edge in self._edges:
            if len(edge) >= 4:
                layers.extend([edge[2], edge[3]])
        return list(dict.fromkeys(layers))


def _sample_embedding_result() -> EmbeddingResult:
    return EmbeddingResult(
        matrix=np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float32),
        item_ids=["A", "B"],
        method="test",
    )


def test_build_union_adjacency_merges_physical_nodes_and_weights() -> None:
    network = _StubNetwork(
        [
            ("A", "B", "social", "social", 2.0),
            ("A", "B", "work", "work", 1.0),
            ("A", "A", "social", "work", 0.5),
        ]
    )
    node_ids = [("A", "social"), ("A", "work"), ("B", "social")]

    adj, ordered_ids = _build_union_adjacency(network, node_ids)

    assert ordered_ids == ["A", "B"]
    dense = adj.toarray()
    np.testing.assert_allclose(dense[0, 1], 3.0)
    np.testing.assert_allclose(dense[1, 0], 3.0)
    np.testing.assert_allclose(dense[0, 0], 0.5)


def test_build_supra_adjacency_adds_gamma_coupling() -> None:
    network = _StubNetwork(
        [
            ("A", "B", "social", "social", 1.0),
            ("A", "A", "social", "work", 2.0),
        ]
    )
    node_ids = [("A", "social"), ("A", "work"), ("B", "social")]

    adj, ordered_ids = _build_supra_adjacency(network, node_ids, gamma=0.7)
    idx = {nid: i for i, nid in enumerate(ordered_ids)}
    dense = adj.toarray()

    np.testing.assert_allclose(
        dense[idx[("A", "social")], idx[("A", "work")]],
        2.7,
        atol=1e-6,
    )
    np.testing.assert_allclose(
        dense[idx[("A", "social")], idx[("B", "social")]],
        1.0,
        atol=1e-6,
    )


def test_netmf_embed_rejects_too_small_graph() -> None:
    adj = sp.csr_matrix(np.array([[0.0]], dtype=np.float32))
    with pytest.raises(EmbeddingError, match="only 1 node"):
        _netmf_embed(
            adj,
            dim=2,
            window=2,
            negative=1.0,
            approx="eigsh",
            seed=7,
        )


def test_netmf_embed_rejects_invalid_dim_for_small_graph() -> None:
    adj = sp.csr_matrix(np.array([[0.0, 1.0], [1.0, 0.0]], dtype=np.float32))
    with pytest.raises(EmbeddingError, match="too large"):
        _netmf_embed(
            adj,
            dim=2,
            window=2,
            negative=1.0,
            approx="eigsh",
            seed=7,
        )


def test_netmf_embed_eigsh_returns_finite_matrix() -> None:
    adj = sp.csr_matrix(
        np.array(
            [
                [0.0, 1.0, 0.0, 0.0],
                [1.0, 0.0, 1.0, 0.0],
                [0.0, 1.0, 0.0, 1.0],
                [0.0, 0.0, 1.0, 0.0],
            ],
            dtype=np.float32,
        )
    )
    emb = _netmf_embed(
        adj,
        dim=2,
        window=2,
        negative=1.0,
        approx="eigsh",
        seed=7,
    )
    assert emb.shape == (4, 2)
    assert np.isfinite(emb).all()


def test_netmf_embedder_validates_inputs() -> None:
    with pytest.raises(NotImplementedError, match="Supported modes"):
        NetMFEmbedder(multilayer="per_layer")

    embedder = NetMFEmbedder(multilayer="union", approx="eigsh", seed=1)
    with pytest.raises(EmbeddingError, match="empty item set"):
        embedder.fit_transform(_StubNetwork([]), item_ids=[])


def test_apply_link_op_hadamard_with_layer_and_plain_fallback() -> None:
    node_embedding = EmbeddingResult(
        matrix=np.array([[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]], dtype=np.float32),
        item_ids=[("A", "social"), ("B", "social"), "C"],
        method="node2vec",
    )
    edge_ids = [
        ("A", "B", "social", "social"),
        ("C", "A", "unknown", "social"),
    ]

    result = apply_link_op(node_embedding, edge_ids, op="hadamard")
    np.testing.assert_allclose(result.matrix[0], np.array([3.0, 8.0]))
    np.testing.assert_allclose(result.matrix[1], np.array([5.0, 12.0]))
    assert result.item_ids == edge_ids
    assert result.meta["op"] == "hadamard"


def test_apply_link_op_handles_empty_edges_for_concat() -> None:
    node_embedding = EmbeddingResult(
        matrix=np.array([[1.0, 2.0]], dtype=np.float32),
        item_ids=["A"],
        method="node2vec",
    )
    result = apply_link_op(node_embedding, [], op="concat")
    assert result.matrix.shape == (0, 4)


def test_apply_link_op_reports_invalid_operator_and_missing_node() -> None:
    node_embedding = EmbeddingResult(
        matrix=np.array([[1.0, 2.0]], dtype=np.float32),
        item_ids=["A"],
        method="node2vec",
    )
    with pytest.raises(EmbeddingError, match="Unknown link operator"):
        apply_link_op(node_embedding, [("A", "A")], op="does_not_exist")

    with pytest.raises(EmbeddingError, match="Node 'B' not found"):
        apply_link_op(node_embedding, [("A", "B")], op="hadamard")

    assert "hadamard" in LINK_OPS


def test_embed_config_hash_is_order_independent() -> None:
    cfg1 = {"method": "netmf", "dim": 8, "seed": 42}
    cfg2 = {"seed": 42, "dim": 8, "method": "netmf"}
    assert make_embed_config_hash(cfg1) == make_embed_config_hash(cfg2)


def test_make_cache_key_includes_optional_network_version() -> None:
    k1 = make_cache_key("nf", "ast", "emb")
    k2 = make_cache_key("nf", "ast", "emb", network_version=9)
    assert k1 == "nf:ast:emb"
    assert k2 == "nf:ast:emb:9"


def test_local_lru_cache_eviction_and_hit_miss_tracking() -> None:
    cache = cache_mod._LRUCache(maxsize=2)
    emb = _sample_embedding_result()
    cache.put("k1", emb)
    cache.put("k2", emb)
    assert cache.get("k1") is not None  # hit
    cache.put("k3", emb)  # evict k2 (least recently used)
    assert cache.get("k2") is None
    assert cache.hits >= 1
    assert cache.misses >= 1


def test_global_cache_get_put_clear_and_stats() -> None:
    clear_cache()
    emb = _sample_embedding_result()
    key = "nf:ast:emb"

    assert cache_get(key) is None
    cache_put(key, emb)
    assert cache_get(key) is emb
    stats = cache_stats()
    assert stats["hits"] >= 1
    assert stats["misses"] >= 1

    clear_cache()
    assert cache_stats() == {"hits": 0, "misses": 0}
