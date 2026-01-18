"""
Test fixtures and utilities for py3plex verification testing.

This module provides:
- Canonical small graph fixtures for deterministic testing
- Metamorphic transformation utilities
- Certificate validators
"""

from tests.fixtures.canonical_graphs import (
    tiny_two_layer,
    small_three_layer,
    two_cliques_bridge,
    path_graph_multilayer,
)
from tests.fixtures.transformations import (
    relabel_nodes,
    permute_layers,
    shuffle_edge_order,
    scale_weights,
    add_isolated_nodes,
    perturb_edges,
)

__all__ = [
    # Canonical graphs
    "tiny_two_layer",
    "small_three_layer",
    "two_cliques_bridge",
    "path_graph_multilayer",
    # Transformations
    "relabel_nodes",
    "permute_layers",
    "shuffle_edge_order",
    "scale_weights",
    "add_isolated_nodes",
    "perturb_edges",
]
