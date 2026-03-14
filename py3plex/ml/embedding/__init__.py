"""First-class node/edge embedding API."""

from .base import BaseEmbedding, EmbeddingResult
from .node2vec import Node2VecEmbedding
from .deepwalk import DeepWalkEmbedding
from .netmf import NetMFEmbedding
from .line import LINEEmbedding
from .metapath2vec import MetaPath2VecEmbedding
from .multiplex import (
    MultiplexNode2Vec,
    SupraAdjacencyEmbedding,
    LayerRegularizedEmbedding,
)

__all__ = [
    "BaseEmbedding",
    "EmbeddingResult",
    "Node2VecEmbedding",
    "DeepWalkEmbedding",
    "NetMFEmbedding",
    "LINEEmbedding",
    "MetaPath2VecEmbedding",
    "MultiplexNode2Vec",
    "SupraAdjacencyEmbedding",
    "LayerRegularizedEmbedding",
]

