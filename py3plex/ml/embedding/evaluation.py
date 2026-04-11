"""Embedding evaluation utilities."""

from __future__ import annotations

from typing import Any, Dict, List, Sequence

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    adjusted_rand_score,
    average_precision_score,
    f1_score,
    normalized_mutual_info_score,
    accuracy_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split

from py3plex.embeddings.base import EmbeddingResult


def edge_operator(u: np.ndarray, v: np.ndarray, operator: str = "hadamard") -> np.ndarray:
    """Combine two node embeddings into an edge feature vector."""
    op = operator.lower()
    if op == "hadamard":
        return u * v
    if op == "average":
        return (u + v) * 0.5
    if op == "weighted_l1":
        return np.abs(u - v)
    if op == "weighted_l2":
        return (u - v) ** 2
    if op == "cosine":
        denom = max(float(np.linalg.norm(u) * np.linalg.norm(v)), 1e-12)
        return np.asarray([float(np.dot(u, v) / denom)], dtype=np.float32)
    raise ValueError(
        f"Unknown edge operator '{operator}'. Expected one of: "
        "hadamard, average, weighted_l1, weighted_l2, cosine."
    )


def build_edge_features(
    embedding: EmbeddingResult,
    edges: Sequence[tuple[Any, Any]],
    operator: str = "hadamard",
) -> np.ndarray:
    """Build edge feature matrix from an embedding and edge list."""
    rows: List[np.ndarray] = []
    for src, dst in edges:
        rows.append(edge_operator(embedding.get_embedding(src), embedding.get_embedding(dst), operator=operator))
    if not rows:
        dim = 1 if operator.lower() == "cosine" else embedding.dim
        return np.empty((0, dim), dtype=np.float32)
    return np.vstack(rows).astype(np.float32, copy=False)


def evaluate_link_prediction_embeddings(
    embedding: EmbeddingResult,
    positive_edges: Sequence[tuple[Any, Any]],
    negative_edges: Sequence[tuple[Any, Any]],
    operator: str = "hadamard",
    random_state: int = 42,
) -> Dict[str, float]:
    """Evaluate link prediction with logistic probe on edge features."""
    pos_X = build_edge_features(embedding, positive_edges, operator=operator)
    neg_X = build_edge_features(embedding, negative_edges, operator=operator)
    X = np.vstack([pos_X, neg_X]).astype(np.float32, copy=False)
    y = np.concatenate(
        [
            np.ones(len(pos_X), dtype=np.int32),
            np.zeros(len(neg_X), dtype=np.int32),
        ]
    )
    if len(np.unique(y)) < 2:
        raise ValueError("Both positive and negative edges are required for evaluation.")
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.3,
        random_state=random_state,
        stratify=y,
    )
    clf = LogisticRegression(max_iter=1000, random_state=random_state)
    clf.fit(X_train, y_train)
    y_score = clf.predict_proba(X_test)[:, 1]
    return {
        "roc_auc": float(roc_auc_score(y_test, y_score)),
        "average_precision": float(average_precision_score(y_test, y_score)),
    }


def evaluate_link_prediction(
    y_true: Sequence[int],
    y_score: Sequence[float],
) -> float:
    """Evaluate link prediction with ROC-AUC."""
    return float(roc_auc_score(y_true, y_score))


def evaluate_node_classification(
    X: np.ndarray,
    y: Sequence[int],
    test_size: float = 0.3,
    random_state: int = 42,
) -> float:
    """Evaluate node classification with macro-F1."""
    report = evaluate_node_classification_report(
        X,
        y,
        test_size=test_size,
        random_state=random_state,
    )
    return float(report["macro_f1"])


def evaluate_node_classification_report(
    X: np.ndarray,
    y: Sequence[int],
    test_size: float = 0.3,
    random_state: int = 42,
) -> Dict[str, float]:
    """Evaluate node classification with linear probe metrics."""
    try:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state, stratify=y
        )
    except ValueError:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state, stratify=None
        )
    clf = LogisticRegression(max_iter=1000, random_state=random_state)
    clf.fit(X_train, y_train)
    pred = clf.predict(X_test)
    return {
        "accuracy": float(accuracy_score(y_test, pred)),
        "micro_f1": float(f1_score(y_test, pred, average="micro")),
        "macro_f1": float(f1_score(y_test, pred, average="macro")),
    }


def evaluate_clustering(
    y_true: Sequence[int],
    y_pred: Sequence[int],
) -> dict:
    """Evaluate clustering with NMI and ARI."""
    return {
        "NMI": float(normalized_mutual_info_score(y_true, y_pred)),
        "ARI": float(adjusted_rand_score(y_true, y_pred)),
    }
