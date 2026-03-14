"""Multiplex-aware embedding variants."""

from __future__ import annotations

from typing import Any, List, Optional

import numpy as np

from py3plex.embeddings.base import EmbeddingResult

from .node2vec import Node2VecEmbedding
from .netmf import NetMFEmbedding


class MultiplexNode2Vec(Node2VecEmbedding):
    """Node2Vec variant optimized for (node, layer) state walks."""

    name = "multiplex_node2vec"

    def __init__(self, *args, layer_weight: float = 1.0, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.layer_weight = layer_weight

    def fit(self, network: Any) -> "MultiplexNode2Vec":
        super().fit(network)
        if self._result is not None:
            self._result.meta["layer_weight"] = self.layer_weight
        return self


class SupraAdjacencyEmbedding(NetMFEmbedding):
    """NetMF over a supra-adjacency representation."""

    name = "supra_adjacency"

    def __init__(self, *args, gamma: float = 1.0, **kwargs) -> None:
        super().__init__(*args, multilayer="supra", gamma=gamma, **kwargs)


class LayerRegularizedEmbedding(NetMFEmbedding):
    """Layer-regularized embedding that blends per-layer and supra vectors."""

    name = "layer_regularized"

    def __init__(
        self,
        dimensions: int = 128,
        alpha: float = 0.5,
        seed: Optional[int] = None,
    ) -> None:
        super().__init__(
            dimensions=dimensions,
            multilayer="supra",
            gamma=1.0,
            seed=seed,
        )
        self.alpha = alpha

    def fit(self, network: Any) -> "LayerRegularizedEmbedding":
        supra = NetMFEmbedding(
            dimensions=self.dimensions,
            multilayer="supra",
            gamma=self.gamma,
            window=self.window,
            negative=self.negative,
            approx=self.approx,
            seed=self.seed,
        ).fit_transform(network)
        union = NetMFEmbedding(
            dimensions=self.dimensions,
            multilayer="union",
            gamma=self.gamma,
            window=self.window,
            negative=self.negative,
            approx=self.approx,
            seed=self.seed,
        ).fit_transform(network)

        union_aligned = union.reorder(supra.item_ids)
        blended = self.alpha * supra.matrix + (1.0 - self.alpha) * union_aligned.matrix
        self._result = EmbeddingResult(
            matrix=blended.astype(np.float32),
            item_ids=supra.item_ids,
            method=self.name,
            meta={"alpha": self.alpha},
        )
        return self

