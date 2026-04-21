"""Focused tests for embedding evaluation helpers."""

from __future__ import annotations

import numpy as np
import pytest

from py3plex.embeddings.base import EmbeddingResult
from py3plex.ml.embedding import evaluation


def _embedding() -> EmbeddingResult:
    matrix = np.array(
        [
            [1.0, 0.0, 0.5],
            [0.9, 0.1, 0.4],
            [0.0, 1.0, 0.2],
            [0.1, 0.9, 0.3],
        ],
        dtype=np.float32,
    )
    return EmbeddingResult(matrix=matrix, item_ids=["a", "b", "c", "d"], method="test")


def test_edge_operator_variants_and_invalid_operator():
    u = np.array([1.0, 2.0], dtype=np.float32)
    v = np.array([3.0, 4.0], dtype=np.float32)

    np.testing.assert_allclose(evaluation.edge_operator(u, v, "hadamard"), np.array([3.0, 8.0]))
    np.testing.assert_allclose(evaluation.edge_operator(u, v, "average"), np.array([2.0, 3.0]))
    np.testing.assert_allclose(
        evaluation.edge_operator(u, v, "weighted_l1"), np.array([2.0, 2.0])
    )
    np.testing.assert_allclose(
        evaluation.edge_operator(u, v, "weighted_l2"), np.array([4.0, 4.0])
    )

    cosine = evaluation.edge_operator(u, v, "cosine")
    assert cosine.shape == (1,)
    assert np.isfinite(cosine[0])

    with pytest.raises(ValueError, match="Unknown edge operator"):
        evaluation.edge_operator(u, v, "invalid")


def test_build_edge_features_handles_empty_input_and_cosine_shape():
    emb = _embedding()

    empty_hadamard = evaluation.build_edge_features(emb, [], operator="hadamard")
    assert empty_hadamard.shape == (0, emb.dim)

    empty_cosine = evaluation.build_edge_features(emb, [], operator="cosine")
    assert empty_cosine.shape == (0, 1)


def test_evaluate_link_prediction_embeddings_success_and_error():
    emb = _embedding()
    positive_edges = [("a", "b"), ("a", "d"), ("c", "d"), ("b", "d")]
    negative_edges = [("a", "c"), ("b", "c"), ("a", "c"), ("b", "c")]

    metrics = evaluation.evaluate_link_prediction_embeddings(
        emb,
        positive_edges,
        negative_edges,
        operator="average",
        random_state=42,
    )
    assert set(metrics) == {"roc_auc", "average_precision"}
    assert 0.0 <= metrics["roc_auc"] <= 1.0
    assert 0.0 <= metrics["average_precision"] <= 1.0

    with pytest.raises(ValueError, match="Both positive and negative edges"):
        evaluation.evaluate_link_prediction_embeddings(
            emb,
            positive_edges,
            [],
            operator="hadamard",
            random_state=42,
        )


def test_evaluate_link_prediction_and_classification_helpers():
    auc = evaluation.evaluate_link_prediction([0, 0, 1, 1], [0.1, 0.2, 0.8, 0.9])
    assert auc == pytest.approx(1.0)

    X = np.array(
        [
            [1.0, 0.0],
            [0.9, 0.1],
            [0.1, 0.9],
            [0.0, 1.0],
            [1.0, 0.1],
            [0.1, 1.0],
        ],
        dtype=np.float32,
    )
    y = [0, 0, 1, 1, 0, 1]

    macro_f1 = evaluation.evaluate_node_classification(X, y, test_size=0.33, random_state=7)
    assert 0.0 <= macro_f1 <= 1.0

    clustering = evaluation.evaluate_clustering([0, 0, 1, 1], [0, 0, 1, 1])
    assert clustering["NMI"] == pytest.approx(1.0)
    assert clustering["ARI"] == pytest.approx(1.0)


def test_evaluate_node_classification_report_fallback_branch(monkeypatch):
    X_train = np.array([[1.0, 0.0], [0.0, 1.0], [0.8, 0.2], [0.2, 0.8]], dtype=np.float32)
    X_test = np.array([[0.9, 0.1], [0.1, 0.9]], dtype=np.float32)
    y_train = np.array([0, 1, 0, 1])
    y_test = np.array([0, 1])

    state = {"calls": 0}

    def _fake_split(*args, **kwargs):
        state["calls"] += 1
        if state["calls"] == 1:
            raise ValueError("forced split failure")
        return X_train, X_test, y_train, y_test

    monkeypatch.setattr(evaluation, "train_test_split", _fake_split)

    report = evaluation.evaluate_node_classification_report(
        np.zeros((6, 2), dtype=np.float32),
        [0, 1, 0, 1, 0, 1],
        random_state=0,
    )

    assert state["calls"] == 2
    assert set(report) == {"accuracy", "micro_f1", "macro_f1"}
    assert 0.0 <= report["accuracy"] <= 1.0
