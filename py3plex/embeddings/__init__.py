"""First-class embedding primitives for py3plex DSL v2.

Provides NetMF node embeddings, link feature operators, and caching
integrated into the DSL v2 builder/executor pipeline.

Public API::

    from py3plex.embeddings import embed_nodes, EmbeddingResult
    from py3plex.embeddings.link_ops import hadamard, concat, l1, l2
"""

from .base import EmbeddingResult, Embedder
from .netmf import NetMFEmbedder
from .link_ops import apply_link_op, LINK_OPS

__all__ = [
    "EmbeddingResult",
    "Embedder",
    "NetMFEmbedder",
    "apply_link_op",
    "LINK_OPS",
]
