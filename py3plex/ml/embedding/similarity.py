"""Similarity helpers for embedding vectors."""

from __future__ import annotations

import numpy as np

_EPSILON = 1e-8


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Compute cosine similarity."""
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    if denom < _EPSILON:
        return 0.0
    return float(np.dot(a, b) / denom)


def euclidean_distance(a: np.ndarray, b: np.ndarray) -> float:
    """Compute Euclidean distance."""
    return float(np.linalg.norm(a - b))


def dot_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Compute dot-product similarity."""
    return float(np.dot(a, b))
