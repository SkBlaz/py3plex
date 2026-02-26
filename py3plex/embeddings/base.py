"""Base classes for embedding backends."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable

import numpy as np


class EmbeddingResult:
    """Container for node or edge embedding vectors.

    Attributes:
        matrix: Float32 array of shape (n_items, dim).
        item_ids: List of item identifiers aligned with matrix rows.
        method: Embedding method name (e.g. "netmf").
        meta: Arbitrary metadata (method params, backend, cache_hit, etc.).
    """

    def __init__(
        self,
        matrix: np.ndarray,
        item_ids: List[Any],
        method: str,
        meta: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialise an EmbeddingResult.

        Args:
            matrix: Float32 array of shape (n_items, dim).
            item_ids: Identifiers corresponding to each row.
            method: Name of the embedding method used.
            meta: Optional metadata dict (backend, params, cache_hit, …).
        """
        if matrix.ndim != 2:
            raise ValueError(
                f"Embedding matrix must be 2-D, got shape {matrix.shape}"
            )
        if len(item_ids) != matrix.shape[0]:
            raise ValueError(
                f"item_ids length ({len(item_ids)}) must match matrix rows ({matrix.shape[0]})"
            )
        self.matrix = matrix.astype(np.float32, copy=False)
        self.item_ids = list(item_ids)
        self.method = method
        self.meta: Dict[str, Any] = meta or {}

    @property
    def dim(self) -> int:
        """Embedding dimensionality."""
        return self.matrix.shape[1]

    @property
    def n_items(self) -> int:
        """Number of embedded items."""
        return self.matrix.shape[0]

    def norms(self) -> np.ndarray:
        """L2 norms of each row vector."""
        return np.linalg.norm(self.matrix, axis=1)

    def reorder(self, ids: List[Any]) -> "EmbeddingResult":
        """Return a new EmbeddingResult with rows reordered to match *ids*.

        Args:
            ids: Desired ordering of item identifiers.  Must be a subset or
                 equal set of ``self.item_ids``.

        Returns:
            New EmbeddingResult aligned to *ids*.

        Raises:
            KeyError: If any id in *ids* is missing from this result.
        """
        id_to_idx = {iid: i for i, iid in enumerate(self.item_ids)}
        try:
            indices = [id_to_idx[iid] for iid in ids]
        except KeyError as exc:
            raise KeyError(f"Item {exc} not found in embedding") from exc
        return EmbeddingResult(
            matrix=self.matrix[indices],
            item_ids=ids,
            method=self.method,
            meta=dict(self.meta),
        )


@runtime_checkable
class Embedder(Protocol):
    """Protocol for embedding backends."""

    def fit_transform(
        self,
        graph: Any,
        *,
        item_ids: List[Any],
        dim: int,
        seed: Optional[int],
    ) -> EmbeddingResult:
        """Compute embeddings and return an EmbeddingResult."""
        ...
