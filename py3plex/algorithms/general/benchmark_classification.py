"""
Benchmark algorithms for node classification performance evaluation.

This module provides algorithms for benchmarking node classification
performance, including oracle-based F1 score evaluation.
"""

from typing import List

import numpy as np
import scipy.sparse as sp
from sklearn.metrics import f1_score


def evaluate_oracle_F1(probs: np.ndarray, Y_real: np.ndarray) -> tuple[float, float]:
    """
    Evaluate oracle F1 scores for multi-label classification.

    This function computes micro and macro F1 scores by selecting the top-k
    predictions for each sample, where k is determined by the ground truth
    number of labels.

    Args:
        probs: Predicted probability matrix of shape (n_samples, n_labels).
        Y_real: Ground truth binary label matrix of shape (n_samples, n_labels).

    Returns:
        A tuple containing:
            - micro: Micro-averaged F1 score
            - macro: Macro-averaged F1 score

    Example:
        >>> probs = np.array([[0.9, 0.1, 0.2], [0.1, 0.8, 0.7]])
        >>> Y_real = np.array([[1, 0, 0], [0, 1, 1]])
        >>> micro, macro = evaluate_oracle_F1(probs, Y_real)
    """
    y_test: List[List[int]] = [[] for _ in range(Y_real.shape[0])]
    cy = sp.csr_matrix(Y_real).tocoo()
    for i, b in zip(cy.row, cy.col):
        y_test[i].append(b)
    top_k_list = [len(l) for l in y_test]
    assert Y_real.shape[0] == len(top_k_list)
    predictions = []
    for i, k in enumerate(top_k_list):
        probs_ = probs[i, :]
        a = np.zeros(probs.shape[1])
        labels_tmp = probs_.argsort()[-k:]
        a[labels_tmp] = 1
        predictions.append(a)
    predictions = np.matrix(predictions)

    micro = f1_score(Y_real, predictions, average="micro")
    macro = f1_score(Y_real, predictions, average="macro")
    return (micro, macro)
