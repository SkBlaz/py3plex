"""DeepWalk embedding model."""

from __future__ import annotations

from typing import Optional

from .node2vec import Node2VecEmbedding


class DeepWalkEmbedding(Node2VecEmbedding):
    """DeepWalk implementation as an unbiased Node2Vec variant."""

    name = "deepwalk"

    def __init__(
        self,
        dimensions: int = 128,
        walk_length: int = 80,
        num_walks: int = 10,
        window_size: int = 10,
        negative_samples: int = 5,
        workers: int = 1,
        backend: str = "numpy",
        seed: Optional[int] = None,
    ) -> None:
        super().__init__(
            dimensions=dimensions,
            walk_length=walk_length,
            num_walks=num_walks,
            p=1.0,
            q=1.0,
            window_size=window_size,
            negative_samples=negative_samples,
            workers=workers,
            backend=backend,
            seed=seed,
        )
