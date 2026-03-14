"""LINE embedding model."""

from __future__ import annotations

from typing import Any, List, Optional

import numpy as np

from py3plex.embeddings.base import BaseEmbedding, EmbeddingResult

from .utils import build_graph_from_network, truncated_svd_embedding


class LINEEmbedding(BaseEmbedding):
    """Lightweight LINE approximation via sparse adjacency factorization."""

    name = "line"

    def __init__(
        self,
        dimensions: int = 128,
        order: int = 2,
        negative_samples: int = 5,
        lr: float = 0.025,
        epochs: int = 5,
        seed: Optional[int] = None,
    ) -> None:
        self.dimensions = dimensions
        self.order = order
        self.negative_samples = negative_samples
        self.lr = lr
        self.epochs = epochs
        self.seed = seed
        self._result: Optional[EmbeddingResult] = None

    def fit(self, network: Any) -> "LINEEmbedding":
        item_ids = list(network.get_nodes())
        G = build_graph_from_network(network, nodes=item_ids, directed=False)
        idx = {n: i for i, n in enumerate(item_ids)}
        adj = np.zeros((len(item_ids), len(item_ids)), dtype=np.float32)
        for u, v, data in G.edges(data=True):
            i, j = idx[u], idx[v]
            w = float(data.get("weight", 1.0))
            adj[i, j] += w
            adj[j, i] += w

        if self.order == 1:
            matrix = adj
        else:
            deg = np.maximum(adj.sum(axis=1, keepdims=True), 1e-12)
            matrix = (adj / deg) @ (adj / deg).T

        emb = truncated_svd_embedding(matrix, dim=self.dimensions)
        self._result = EmbeddingResult(
            matrix=emb,
            item_ids=item_ids,
            method=self.name,
            meta={
                "order": self.order,
                "negative_samples": self.negative_samples,
                "lr": self.lr,
                "epochs": self.epochs,
            },
        )
        return self

    def transform(self, nodes: Optional[List[Any]] = None) -> EmbeddingResult:
        if self._result is None:
            raise ValueError("Model is not fitted. Call fit() first.")
        if nodes is None:
            return self._result
        return self._result.reorder(nodes)

    def fit_transform(self, network: Any) -> EmbeddingResult:
        self.fit(network)
        return self.transform()

    def get_embedding(self, node: Any) -> np.ndarray:
        return self.transform().get_embedding(node)

    def to_pandas(self):
        return self.transform().to_pandas()

    def to_numpy(self) -> np.ndarray:
        return self.transform().to_numpy()

