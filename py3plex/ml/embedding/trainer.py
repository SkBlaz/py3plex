"""Reusable embedding training utilities."""

from __future__ import annotations

from typing import Any, List, Optional, Sequence

import numpy as np

from py3plex.embeddings.base import EmbeddingResult

from .utils import (
    build_graph_from_network,
    cooccurrence_matrix,
    node2vec_walk,
    random_walk,
    truncated_svd_embedding,
)


class EmbeddingTrainer:
    """Utility class for random-walk + skipgram-style training."""

    def __init__(
        self,
        *,
        backend: str = "numpy",
        seed: Optional[int] = None,
    ) -> None:
        self.backend = backend
        self.seed = seed
        self.rng = np.random.default_rng(seed)

    def generate_walks(
        self,
        network: Any,
        *,
        nodes: Optional[Sequence[Any]] = None,
        walk_length: int = 40,
        num_walks: int = 10,
        p: float = 1.0,
        q: float = 1.0,
        biased: bool = False,
    ) -> List[List[Any]]:
        """Generate random walks over graph nodes."""
        G = build_graph_from_network(network=network, nodes=nodes, directed=False)
        start_nodes = list(G.nodes())
        walks: List[List[Any]] = []
        if not start_nodes:
            return walks
        for _ in range(max(0, num_walks)):
            self.rng.shuffle(start_nodes)
            for node in start_nodes:
                if biased:
                    walk = node2vec_walk(
                        G, node, walk_length=walk_length, p=p, q=q, rng=self.rng
                    )
                else:
                    walk = random_walk(
                        G, node, walk_length=walk_length, rng=self.rng
                    )
                walks.append(walk)
        return walks

    def train_skipgram(
        self,
        walks: Sequence[Sequence[Any]],
        *,
        dimensions: int = 128,
        window_size: int = 10,
        method: str = "skipgram",
        item_ids: Optional[List[Any]] = None,
    ) -> EmbeddingResult:
        """Train a lightweight skipgram proxy via co-occurrence + SVD."""
        if item_ids is None:
            uniq = set()
            for walk in walks:
                for node in walk:
                    uniq.add(node)
            item_ids = list(uniq)

        node_to_idx = {n: i for i, n in enumerate(item_ids)}
        cooc = cooccurrence_matrix(
            walks=walks, node_to_idx=node_to_idx, window_size=window_size
        )
        emb = truncated_svd_embedding(cooc, dim=dimensions)
        return EmbeddingResult(
            matrix=emb,
            item_ids=item_ids,
            method=method,
            meta={"backend": self.backend, "window_size": window_size},
        )

    def optimize_embeddings(
        self,
        network: Any,
        *,
        dimensions: int = 128,
        walk_length: int = 40,
        num_walks: int = 10,
        window_size: int = 10,
        p: float = 1.0,
        q: float = 1.0,
        biased: bool = False,
        item_ids: Optional[List[Any]] = None,
        method: str = "skipgram",
    ) -> EmbeddingResult:
        """End-to-end train embeddings."""
        walks = self.generate_walks(
            network=network,
            nodes=item_ids,
            walk_length=walk_length,
            num_walks=num_walks,
            p=p,
            q=q,
            biased=biased,
        )
        return self.train_skipgram(
            walks,
            dimensions=dimensions,
            window_size=window_size,
            method=method,
            item_ids=item_ids,
        )


def generate_walks(network: Any, **kwargs) -> List[List[Any]]:
    """Functional helper around :class:`EmbeddingTrainer.generate_walks`."""
    trainer = EmbeddingTrainer(
        backend=str(kwargs.pop("backend", "numpy")),
        seed=kwargs.pop("seed", None),
    )
    return trainer.generate_walks(network, **kwargs)


def train_skipgram(walks: Sequence[Sequence[Any]], **kwargs) -> EmbeddingResult:
    """Functional helper around :class:`EmbeddingTrainer.train_skipgram`."""
    trainer = EmbeddingTrainer(
        backend=str(kwargs.pop("backend", "numpy")),
        seed=kwargs.pop("seed", None),
    )
    return trainer.train_skipgram(walks, **kwargs)
