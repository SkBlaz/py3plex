"""
Embedding visualization tools for py3plex.

This module provides tools for visualizing network embeddings using
dimensionality reduction techniques (t-SNE, UMAP, etc.).

Common imports:
    from py3plex.visualization.embedding_visualization import embedding_tools
    from py3plex.visualization.embedding_visualization import embedding_visualization
"""

from . import embedding_tools
from . import embedding_visualization

__all__ = [
    "embedding_tools",
    "embedding_visualization",
]
