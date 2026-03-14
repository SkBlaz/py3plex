"""NetMF embedding wrapper."""

from __future__ import annotations

from typing import Any, List, Optional

import numpy as np

from py3plex.embeddings.base import BaseEmbedding, EmbeddingResult
from py3plex.embeddings.netmf import NetMFEmbedder


class NetMFEmbedding(BaseEmbedding):
    """Spectral DeepWalk approximation using NetMF."""

    name = "netmf"

    def __init__(
        self,
        dimensions: int = 128,
        window: int = 10,
        negative: float = 1.0,
        multilayer: str = "supra",
        gamma: float = 1.0,
        approx: str = "randomized_svd",
        seed: Optional[int] = None,
    ) -> None:
        self.dimensions = dimensions
        self.window = window
        self.negative = negative
        self.multilayer = multilayer
        self.gamma = gamma
        self.approx = approx
        self.seed = seed
        self._result: Optional[EmbeddingResult] = None

    def fit(self, network: Any) -> "NetMFEmbedding":
        item_ids = list(network.get_nodes())
        embedder = NetMFEmbedder(
            dim=self.dimensions,
            multilayer=self.multilayer,
            window=self.window,
            negative=self.negative,
            approx=self.approx,
            gamma=self.gamma,
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

