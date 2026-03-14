"""Similarity helpers for embedding vectors."""

from __future__ import annotations

import numpy as np


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Compute cosine similarity."""
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    return float(np.dot(a, b) / max(denom, 1e-12))


def euclidean_distance(a: np.ndarray, b: np.ndarray) -> float:
    """Compute Euclidean distance."""
    return float(np.linalg.norm(a - b))


def dot_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Compute dot-product similarity."""
    return float(np.dot(a, b))

