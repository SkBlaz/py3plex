"""Embedding evaluation utilities."""

from __future__ import annotations

from typing import Iterable, Sequence

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    adjusted_rand_score,
    f1_score,
    normalized_mutual_info_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split


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
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y
    )
    clf = LogisticRegression(max_iter=1000, random_state=random_state)
    clf.fit(X_train, y_train)
    pred = clf.predict(X_test)
    return float(f1_score(y_test, pred, average="macro"))


def evaluate_clustering(
    y_true: Sequence[int],
    y_pred: Sequence[int],
) -> dict:
    """Evaluate clustering with NMI and ARI."""
    return {
        "NMI": float(normalized_mutual_info_score(y_true, y_pred)),
        "ARI": float(adjusted_rand_score(y_true, y_pred)),
    }

