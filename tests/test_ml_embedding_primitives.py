"""Tests for first-class embedding primitives."""

from __future__ import annotations

import importlib.util
import numpy as np
import pytest

from py3plex.core.multinet import multi_layer_network
from py3plex.dsl import Q
from py3plex.graph_ops import nodes
from py3plex.pipeline import NodeEmbedding, Pipeline, PipelineStep


def _toy_network() -> multi_layer_network:
    net = multi_layer_network(directed=False, network_type="multilayer")
    net.add_edges(
        [
            {
                "source": "Alice",
                "target": "Bob",
                "source_type": "social",
                "target_type": "social",
            },
            {
                "source": "Bob",
                "target": "Carol",
                "source_type": "social",
                "target_type": "social",
            },
            {
                "source": "Alice",
                "target": "Alice",
                "source_type": "social",
                "target_type": "work",
            },
            {
                "source": "Alice",
                "target": "Carol",
                "source_type": "work",
                "target_type": "work",
            },
        ]
    )
    return net


def test_node2vec_embedding():
    net = _toy_network()
    emb = net.embed(method="node2vec", dimensions=8, walk_length=8, num_walks=3, seed=42)
    assert emb.dimension == 8
    assert len(emb.nodes) == len(list(net.get_nodes()))
    assert emb.to_numpy().shape[1] == 8


def test_deepwalk_embedding():
    net = _toy_network()
    emb = net.embed(method="deepwalk", dimensions=6, walk_length=6, num_walks=2, seed=7)
    assert emb.to_numpy().shape == (len(list(net.get_nodes())), 6)


def test_netmf_embedding():
    net = _toy_network()
    emb = net.embed(method="netmf", dimensions=5, seed=1)
    assert emb.to_numpy().shape == (len(list(net.get_nodes())), 5)
    df = emb.to_pandas()
    assert {"node", "layer", "embedding"}.issubset(df.columns)


def test_embedding_similarity():
    net = _toy_network()
    emb = net.embed(method="node2vec", dimensions=8, walk_length=8, num_walks=2, seed=12)
    node_ids = emb.nodes
    sim = emb.similarity(node_ids[0], node_ids[1])
    assert np.isfinite(sim)
    neighbors = emb.most_similar(node_ids[0], k=2)
    assert len(neighbors) <= 2


def test_node2vec_embedding_deterministic_seed():
    net = _toy_network()
    emb_a = net.embed(method="node2vec", dimensions=8, walk_length=8, num_walks=2, seed=123)
    emb_b = net.embed(method="node2vec", dimensions=8, walk_length=8, num_walks=2, seed=123)
    np.testing.assert_allclose(emb_a.to_numpy(), emb_b.to_numpy())


def test_layer_regularized_embedding():
    # `dimensions` must not exceed the number of distinct physical nodes (3:
    # Alice/Bob/Carol), since union mode collapses layers and its rank is
    # capped by that count.
    net = _toy_network()
    emb = net.embed(method="layer_regularized", dimensions=2, seed=3)
    assert emb.to_numpy().shape == (len(list(net.get_nodes())), 2)


def test_dsl_embed_integration_layer_regularized():
    net = _toy_network()
    result = Q.nodes().embed("layer_regularized", dim=2, seed=3).execute(net)
    mat = result.to_numpy("embedding")
    assert mat.shape[1] == 2


def test_multiplex_walks():
    net = _toy_network()
    emb = net.embed(
        method="multiplex_node2vec",
        dimensions=4,
        walk_length=6,
        num_walks=2,
        seed=5,
    )
    assert emb.to_numpy().shape[1] == 4
    assert all(isinstance(n, tuple) and len(n) == 2 for n in emb.nodes)


class _LoadToyNetwork(PipelineStep):
    def transform(self, data):
        assert data is None
        return _toy_network()


def test_embedding_pipeline():
    pipe = Pipeline(
        [
            ("load", _LoadToyNetwork()),
            ("embed", NodeEmbedding(method="node2vec", dimensions=8, seed=42)),
        ]
    )
    out = pipe.run()
    assert "embedding" in out
    assert out["embedding"].to_numpy().shape[1] == 8


def test_dsl_embed_integration_node2vec():
    net = _toy_network()
    result = Q.nodes().embed("node2vec", dim=8, walk_length=8, num_walks=2, seed=42).execute(net)
    mat = result.to_numpy("embedding")
    assert mat.shape[1] == 8


def test_dsl_embed_integration_dimensions_alias():
    net = _toy_network()
    result = (
        Q.nodes()
        .embed("node2vec", dimensions=6, walk_length=8, num_walks=2, seed=42)
        .execute(net)
    )
    mat = result.to_numpy("embedding")
    assert mat.shape[1] == 6


def test_dsl_embed_edges_link_op_recorded_in_spec():
    builder = (
        Q.edges()
        .embed(
            "node2vec",
            dim=8,
            walk_length=8,
            num_walks=2,
            link_op="l1",
            seed=42,
        )
    )
    spec = builder.to_ast().select.embedding_spec
    assert spec is not None
    assert spec.link_op == "l1"
    assert spec.dim == 8


def test_dsl_embed_to_numpy_invalid_kind_raises():
    net = _toy_network()
    result = Q.nodes().embed("node2vec", dim=8, walk_length=8, num_walks=2, seed=42).execute(net)
    with pytest.raises(
        ValueError, match="Currently only 'embedding' is supported"
    ):
        result.to_numpy("not-supported")


def test_dsl_embed_to_pandas_expand_embeddings_prefix():
    net = _toy_network()
    result = Q.nodes().embed("node2vec", dim=4, walk_length=8, num_walks=2, seed=42).execute(net)
    df = result.to_pandas(expand_embeddings=True, embedding_prefix="vec_")
    expected_cols = {f"vec_{i}" for i in range(4)}
    assert expected_cols.issubset(df.columns)


def test_graph_ops_embed_column():
    net = _toy_network()
    frame = nodes(net).embed(method="node2vec", dim=8, walk_length=8, num_walks=2, seed=42)
    df = frame.to_pandas()
    assert "embedding" in df.columns


def test_embedding_schema_metadata_and_info():
    net = _toy_network()
    emb = net.embed(method="node2vec", dimensions=8, walk_length=8, num_walks=2, seed=42)
    df = emb.to_pandas()
    assert {"node", "layer", "embedding", "embedding_dim", "method", "timestamp"}.issubset(
        df.columns
    )
    assert set(df["embedding_dim"]) == {8}
    assert set(df["method"]) == {"node2vec"}
    info = emb.info()
    assert info["method"] == "node2vec"
    assert info["dimension"] == 8


def test_embedding_utilities_similarity_matrix_subset_validate():
    net = _toy_network()
    emb = net.embed(method="node2vec", dimensions=8, walk_length=8, num_walks=2, seed=7)
    nodes_subset = emb.nodes[:2]
    subset = emb.subset(nodes_subset)
    assert subset.to_numpy().shape[0] == 2
    assert len(emb.flatten_nodes()) == emb.n_items
    assert len(emb.expand_layers()) == emb.n_items
    assert isinstance(emb.group_by_node(), dict)
    assert isinstance(emb.group_by_layer(), dict)
    sim = emb.similarity_matrix(nodes_subset)
    assert sim.shape == (2, 2)
    assert np.isfinite(emb.distance(nodes_subset[0], nodes_subset[1], metric="euclidean"))
    checks = emb.validate(network=net)
    assert checks["dimension_consistency"] is True
    assert checks["node_count_match"] is True
    assert checks["layer_alignment"] is True


def test_embedding_normalize_reduce_and_index():
    net = _toy_network()
    emb = net.embed(method="node2vec", dimensions=8, walk_length=8, num_walks=2, seed=12)
    normalized = emb.normalize()
    norms = np.linalg.norm(normalized.to_numpy(), axis=1)
    np.testing.assert_allclose(norms, np.ones_like(norms), atol=1e-5)
    reduced = emb.reduce(method="pca", dim=2)
    assert reduced.to_numpy().shape[1] == 2
    emb.build_index(method="hnsw")
    neighbors = emb.knn(emb.nodes[0], k=2)
    assert len(neighbors) <= 2


def test_embedding_cache_and_reproduce(tmp_path):
    net = _toy_network()
    emb1 = net.embed(
        method="node2vec",
        dimensions=8,
        walk_length=8,
        num_walks=2,
        seed=123,
        cache=True,
        cache_dir=str(tmp_path),
    )
    emb2 = net.embed(
        method="node2vec",
        dimensions=8,
        walk_length=8,
        num_walks=2,
        seed=123,
        cache=True,
        cache_dir=str(tmp_path),
    )
    assert emb1.meta["cache_hit"] is False
    assert emb2.meta["cache_hit"] is True
    parquet_files = list(tmp_path.glob("embedding_*.parquet"))
    npz_files = list(tmp_path.glob("embedding_*.npz"))
    if importlib.util.find_spec("pyarrow") is not None:
        assert len(parquet_files) > 0
    else:
        assert len(npz_files) > 0
    replay = emb2.reproduce(net)
    np.testing.assert_allclose(replay.to_numpy(), emb1.to_numpy())


def test_line_embedding_order_variants():
    net = _toy_network()
    emb_order1 = net.embed(method="line", dimensions=6, order=1, seed=42)
    emb_order2 = net.embed(method="line", dimensions=6, order=2, seed=42)
    assert emb_order1.to_numpy().shape[1] == 6
    assert emb_order2.to_numpy().shape[1] == 6
    assert emb_order1.meta["order"] == 1
    assert emb_order2.meta["order"] == 2
    assert not np.allclose(emb_order1.to_numpy(), emb_order2.to_numpy())


def test_metapath2vec_embedding_via_network_embed():
    net = _toy_network()
    emb = net.embed(
        method="metapath2vec",
        dimensions=4,
        walk_length=6,
        num_walks=2,
        metapaths=[["social", "social"], ["work", "work"]],
        seed=42,
    )
    assert emb.to_numpy().shape == (len(list(net.get_nodes())), 4)
    assert emb.method == "metapath2vec"


def test_embedding_vectors_getitem_and_norms():
    net = _toy_network()
    emb = net.embed(method="node2vec", dimensions=8, walk_length=8, num_walks=2, seed=9)
    vectors = emb.vectors
    assert len(vectors) == emb.n_items
    first = emb.nodes[0]
    np.testing.assert_array_equal(vectors[first], emb[first])
    np.testing.assert_allclose(emb.norms(), np.linalg.norm(emb.to_numpy(), axis=1))


def test_embedding_similarity_metrics_dot_and_euclidean():
    net = _toy_network()
    emb = net.embed(method="node2vec", dimensions=8, walk_length=8, num_walks=2, seed=13)
    node_a, node_b = emb.nodes[0], emb.nodes[1]
    dot = emb.similarity(node_a, node_b, metric="dot")
    euc = emb.similarity(node_a, node_b, metric="euclidean")
    assert np.isfinite(dot)
    assert np.isfinite(euc)
    assert euc >= 0


def test_embedding_build_index_sklearn_backend():
    net = _toy_network()
    emb = net.embed(method="node2vec", dimensions=8, walk_length=8, num_walks=2, seed=21)
    emb.build_index(method="sklearn", metric="cosine")
    assert emb._vector_index_backend == "sklearn"
    neighbors = emb.knn(emb.nodes[0], k=2)
    assert len(neighbors) <= 2


def test_embedding_result_save_load_npz(tmp_path):
    net = _toy_network()
    emb = net.embed(method="node2vec", dimensions=6, walk_length=8, num_walks=2, seed=4)
    out_path = tmp_path / "embedding.npz"
    emb.save(str(out_path))
    loaded = type(emb).load(str(out_path))
    np.testing.assert_allclose(loaded.to_numpy(), emb.to_numpy())
    assert loaded.nodes == emb.nodes
    assert loaded.method == emb.method
