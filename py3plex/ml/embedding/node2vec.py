"""Node2Vec embedding model."""

from __future__ import annotations

from typing import Any, List, Optional

import numpy as np

from py3plex.embeddings.base import BaseEmbedding, EmbeddingResult

from .trainer import EmbeddingTrainer


class Node2VecEmbedding(BaseEmbedding):
    """Biased random-walk node embedding."""

    name = "node2vec"

    def __init__(
        self,
        dimensions: int = 128,
        walk_length: int = 80,
        num_walks: int = 10,
        p: float = 1.0,
        q: float = 1.0,
        window_size: int = 10,
        negative_samples: int = 5,
        workers: int = 1,
        backend: str = "numpy",
        seed: Optional[int] = None,
    ) -> None:
        self.dimensions = dimensions
        self.walk_length = walk_length
        self.num_walks = num_walks
        self.p = p
        self.q = q
        self.window_size = window_size
        self.negative_samples = negative_samples
        self.workers = workers
        self.backend = backend
        self.seed = seed
        self._result: Optional[EmbeddingResult] = None

    def fit(self, network: Any) -> "Node2VecEmbedding":
        item_ids = list(network.get_nodes())
        trainer = EmbeddingTrainer(backend=self.backend, seed=self.seed)
        result = trainer.optimize_embeddings(
            network=network,
            dimensions=self.dimensions,
            walk_length=self.walk_length,
            num_walks=self.num_walks,
            window_size=self.window_size,
            p=self.p,
            q=self.q,
            biased=True,
            item_ids=item_ids,
            method=self.name,
        )
        result.meta.update(
            {
                "p": self.p,
                "q": self.q,
                "negative_samples": self.negative_samples,
                "workers": self.workers,
            }
        )
        self._result = result
        return self

    def transform(self, nodes: Optional[List[Any]] = None) -> EmbeddingResult:
        if self._result is None:
            raise ValueError(
                f"{self.__class__.__name__} is not fitted. Call fit() first."
            )
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
