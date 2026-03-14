"""MetaPath2Vec embedding wrapper."""

from __future__ import annotations

from typing import Any, List, Optional

import numpy as np

from py3plex.embeddings.base import BaseEmbedding, EmbeddingResult
from py3plex.embeddings.metapath2vec import MetaPath2VecEmbedder


class MetaPath2VecEmbedding(BaseEmbedding):
    """Meta-path guided embedding for multilayer networks."""

    name = "metapath2vec"

    def __init__(
        self,
        metapaths: List[List[str]],
        dimensions: int = 128,
        walk_length: int = 40,
        num_walks: int = 10,
        window_size: int = 10,
        negative_samples: int = 5,
        epochs: int = 5,
        seed: Optional[int] = None,
    ) -> None:
        self.metapaths = metapaths
        self.dimensions = dimensions
        self.walk_length = walk_length
        self.num_walks = num_walks
        self.window_size = window_size
        self.negative_samples = negative_samples
        self.epochs = epochs
        self.seed = seed
        self._result: Optional[EmbeddingResult] = None

    def fit(self, network: Any) -> "MetaPath2VecEmbedding":
        item_ids = list(network.get_nodes())
        embedder = MetaPath2VecEmbedder(
            metapaths=self.metapaths,
            dim=self.dimensions,
            walk_length=self.walk_length,
            num_walks=self.num_walks,
            window_size=self.window_size,
            negative_samples=self.negative_samples,
            epochs=self.epochs,
            seed=self.seed,
        )
        self._result = embedder.fit_transform(network=network, item_ids=item_ids)
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

