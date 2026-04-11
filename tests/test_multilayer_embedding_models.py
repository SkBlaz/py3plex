"""Tests for multilayer embedding models and utilities."""

from __future__ import annotations

import numpy as np
import pytest

from py3plex.core.multinet import multi_layer_network
from py3plex.exceptions import EmbeddingError
from py3plex.ml.embedding import (
    MELLEmbedding,
    MNEEmbedding,
    NodeLayerIndexer,
    SupraNetMFEmbedding,
    SupraNode2VecEmbedding,
)
from py3plex.ml.embedding.evaluation import (
    evaluate_link_prediction_embeddings,
    evaluate_node_classification_report,
)


def _aligned_multiplex_net() -> multi_layer_network:
    net = multi_layer_network(directed=False, network_type="multilayer")
    net.add_nodes(
        [
            {"source": "A", "type": "social"},
            {"source": "B", "type": "social"},
            {"source": "C", "type": "social"},
            {"source": "A", "type": "work"},
            {"source": "B", "type": "work"},
            {"source": "C", "type": "work"},
        ]
    )
    net.add_edges(
        [
            {
                "source": "A",
                "target": "B",
                "source_type": "social",
                "target_type": "social",
            },
            {
                "source": "B",
                "target": "C",
                "source_type": "social",
                "target_type": "social",
            },
            {
                "source": "A",
                "target": "C",
                "source_type": "work",
                "target_type": "work",
            },
            {
                "source": "A",
                "target": "A",
                "source_type": "social",
                "target_type": "work",
            },
            {
                "source": "B",
                "target": "B",
                "source_type": "social",
                "target_type": "work",
            },
        ]
    )
    return net


def _non_aligned_multilayer_net() -> multi_layer_network:
    net = multi_layer_network(directed=False, network_type="multilayer")
    net.add_edges(
        [
            {
                "source": "A",
                "target": "B",
                "source_type": "social",
                "target_type": "social",
            },
            {
                "source": "A",
                "target": "A",
                "source_type": "social",
                "target_type": "work",
            },
            {
                "source": "A",
                "target": "C",
                "source_type": "work",
                "target_type": "work",
            },
        ]
    )
    return net


def test_node_layer_indexer_round_trip_and_ordering() -> None:
    indexer = NodeLayerIndexer.from_nodes([("B", "work"), ("A", "social"), ("A", "work")])
    assert indexer.state_nodes == [("A", "social"), ("A", "work"), ("B", "work")]
    idx = indexer.index_of(("A", "work"))
    assert indexer.state_of(idx) == ("A", "work")


def test_supra_node2vec_complete_state_embeddings() -> None:
    net = _aligned_multiplex_net()
    result = net.embed(
        method="supra_node2vec",
        dimensions=8,
        walk_length=8,
        num_walks=3,
        seed=42,
    )
    assert result.to_numpy().shape == (len(list(net.get_nodes())), 8)
    assert all(isinstance(node, tuple) and len(node) == 2 for node in result.nodes)
    assert "isolated_nodes" in result.meta


def test_supra_spectral_shape_and_determinism() -> None:
    net = _aligned_multiplex_net()
    emb_a = net.embed(method="supra_spectral", dimensions=4, seed=7)
    emb_b = net.embed(method="supra_spectral", dimensions=4, seed=7)
    assert emb_a.to_numpy().shape == (len(list(net.get_nodes())), 4)
    np.testing.assert_allclose(
        np.abs(emb_a.to_numpy()),
        np.abs(emb_b.to_numpy()),
        atol=1e-6,
    )


def test_supra_netmf_shape_and_determinism() -> None:
    net = _aligned_multiplex_net()
    model = SupraNetMFEmbedding(dimensions=5, seed=11)
    emb_a = model.fit_transform(net)
    emb_b = SupraNetMFEmbedding(dimensions=5, seed=11).fit_transform(net)
    assert emb_a.to_numpy().shape[1] == 5
    np.testing.assert_allclose(emb_a.to_numpy(), emb_b.to_numpy())


def test_mne_parameter_shapes() -> None:
    net = _aligned_multiplex_net()
    model = MNEEmbedding(
        dimensions_common=6,
        dimensions_relation=3,
        epochs=2,
        seed=5,
    )
    result = model.fit_transform(net)
    assert result.to_numpy().shape[1] == 6
    assert model._common_vectors is not None
    assert model._relation_vectors is not None
    assert model._layer_transforms is not None
    assert model._common_vectors.shape[1] == 6
    assert model._relation_vectors.shape[1] == 3
    assert model._layer_transforms.shape[1:] == (3, 6)


def test_mell_training_numerical_sanity() -> None:
    net = _aligned_multiplex_net()
    model = MELLEmbedding(dimensions=6, epochs=4, lr=1e-2, seed=3)
    result = model.fit_transform(net)
    assert result.to_numpy().shape[1] == 6
    assert model.loss_history_
    assert np.isfinite(np.asarray(model.loss_history_)).all()
    assert np.isfinite(result.to_numpy()).all()


def test_state_to_node_aggregation_for_target_both() -> None:
    net = _aligned_multiplex_net()
    model = SupraNode2VecEmbedding(
        dimensions=4,
        walk_length=6,
        num_walks=2,
        seed=9,
        target="both",
        node_reduce="mean",
    )
    state_result = model.fit_transform(net)
    node_result = model.node_embeddings()
    assert state_result.n_items == len(list(net.get_nodes()))
    assert node_result is not None
    assert node_result.n_items == 3
    assert set(node_result.nodes) == {"A", "B", "C"}


def test_mne_raises_on_non_aligned_layers() -> None:
    net = _non_aligned_multilayer_net()
    with pytest.raises(EmbeddingError, match="aligned multiplex replicas"):
        MNEEmbedding(dimensions_common=4, dimensions_relation=2, seed=1).fit(net)


def test_embedding_result_exports_for_supra_models() -> None:
    net = _aligned_multiplex_net()
    emb = net.embed(method="supra_node2vec", dimensions=4, walk_length=6, num_walks=2, seed=2)
    df = emb.to_pandas()
    assert {"node", "layer", "embedding", "embedding_dim", "method"}.issubset(df.columns)
    assert emb.info()["dimension"] == 4


def test_reproducibility_fixed_seed() -> None:
    net = _aligned_multiplex_net()
    emb_a = net.embed(method="supra_node2vec", dimensions=4, walk_length=6, num_walks=2, seed=22)
    emb_b = net.embed(method="supra_node2vec", dimensions=4, walk_length=6, num_walks=2, seed=22)
    np.testing.assert_allclose(emb_a.to_numpy(), emb_b.to_numpy())


def test_evaluation_utilities_on_tiny_graph() -> None:
    net = _aligned_multiplex_net()
    emb = net.embed(method="supra_node2vec", dimensions=4, walk_length=6, num_walks=2, seed=42)
    pos = [(("A", "social"), ("B", "social")), (("A", "work"), ("C", "work"))]
    neg = [(("A", "social"), ("C", "social")), (("B", "work"), ("C", "work"))]
    link_metrics = evaluate_link_prediction_embeddings(emb, pos, neg, operator="hadamard", random_state=1)
    assert {"roc_auc", "average_precision"} == set(link_metrics)
    assert 0.0 <= link_metrics["roc_auc"] <= 1.0
    X = emb.to_numpy()
    y = [0, 1, 2, 0, 1, 2]
    report = evaluate_node_classification_report(X, y, random_state=0)
    assert {"accuracy", "micro_f1", "macro_f1"} == set(report)
