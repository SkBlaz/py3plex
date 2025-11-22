"""
Ricci-flow-based layout algorithms for network visualization.

This module provides layout functions that use Ricci flow edge weights as
geometric signals for node placement. The key idea is that Ricci flow updates
edge weights to approximate a "geometric" metric, which can be used to produce
layouts that highlight geometric structure and community organization.

The layouts are designed to work with graphs that have had Ricci flow applied,
using the updated edge weights to inform node positioning.
"""

from typing import Any, Dict, Optional
import warnings

import networkx as nx
import numpy as np
from sklearn.manifold import MDS

from py3plex.exceptions import Py3plexLayoutError
from py3plex.logging_config import get_logger

logger = get_logger(__name__)


def ricci_flow_layout_single(
    G: nx.Graph,
    dim: int = 2,
    use_geodesic_distances: bool = True,
    weight_attr: str = "weight",
    random_state: Optional[int] = None,
    layout_type: str = "mds",
    **kwargs,
) -> Dict[Any, np.ndarray]:
    """
    Compute a layout for a single graph using Ricci flow edge weights.

    This function uses edge weights updated by Ricci flow to position nodes
    in a geometric space. The resulting layout emphasizes the geometric
    structure revealed by Ricci flow, making communities and bottlenecks
    more visually apparent.

    Args:
        G: NetworkX graph whose edge weights have been updated by Ricci flow.
            The graph should have edge weights in the `weight_attr` attribute.
        dim: Dimensionality of the layout (2 or 3). Default: 2.
        use_geodesic_distances: If True, compute shortest path distances using
            edge weights and use MDS for layout. If False, use force-directed
            or spectral layouts based on edge weights. Default: True.
        weight_attr: Name of the edge attribute containing edge weights.
            Default: "weight".
        random_state: Random seed for reproducibility. Default: None.
        layout_type: Type of layout algorithm to use. Options:
            - "mds": Classical multidimensional scaling (requires use_geodesic_distances=True)
            - "spring": Weighted spring layout (force-directed)
            - "spectral": Spectral layout adapted to weighted adjacency
            Default: "mds".
        **kwargs: Additional keyword arguments passed to the layout algorithm.

    Returns:
        Dictionary mapping nodes to position arrays of shape (dim,).
        For example: {node: np.array([x, y])} or {node: np.array([x, y, z])}.

    Raises:
        ValueError: If the graph has no nodes, invalid layout_type, or
            incompatible parameter combinations.

    Examples:
        >>> import networkx as nx
        >>> from py3plex.algorithms.curvature import compute_ollivier_ricci_flow_single_graph
        >>> from py3plex.visualization.ricci_layout import ricci_flow_layout_single
        >>>
        >>> # Create a graph and apply Ricci flow
        >>> G = nx.karate_club_graph()
        >>> G_flow = compute_ollivier_ricci_flow_single_graph(G, alpha=0.5, iterations=10)
        >>>
        >>> # Compute Ricci-flow-based layout
        >>> positions = ricci_flow_layout_single(G_flow, dim=2, layout_type="mds")
        >>>
        >>> # positions is a dict: {node: np.array([x, y])}

    Notes:
        - MDS layout is recommended for distance-based layouts and works best
          with use_geodesic_distances=True.
        - Spring layout is useful for visualizing local structure and edge
          strength relationships.
        - For graphs with disconnected components, geodesic distances may be
          infinite; in such cases, the function uses a large finite value.
    """
    if G.number_of_nodes() == 0:
        raise Py3plexLayoutError(
            "Cannot compute layout for graph with no nodes. "
            "Please provide a non-empty graph."
        )

    if dim not in [2, 3]:
        raise Py3plexLayoutError(
            f"Invalid dimension: dim must be 2 or 3, got {dim}. "
            "2D layouts are suitable for most visualizations, 3D for specialized cases."
        )

    if layout_type not in ["mds", "spring", "spectral"]:
        raise Py3plexLayoutError(
            f"Invalid layout_type: '{layout_type}'. "
            "Must be 'mds', 'spring', or 'spectral'. "
            "Use 'mds' for distance-based layouts, 'spring' for force-directed layouts, "
            "or 'spectral' for graph spectral layouts."
        )

    if layout_type == "mds" and not use_geodesic_distances:
        warnings.warn(
            "MDS layout typically works best with use_geodesic_distances=True. "
            "Consider setting use_geodesic_distances=True or using a different layout_type.",
            UserWarning,
            stacklevel=2
        )

    # Handle single-node graph
    if G.number_of_nodes() == 1:
        node = list(G.nodes())[0]
        return {node: np.zeros(dim)}

    # Ensure all edges have weights
    _ensure_edge_weights(G, weight_attr)

    if layout_type == "mds":
        return _compute_mds_layout(
            G, dim, use_geodesic_distances, weight_attr, random_state, **kwargs
        )
    elif layout_type == "spring":
        return _compute_spring_layout(G, dim, weight_attr, random_state, **kwargs)
    elif layout_type == "spectral":
        return _compute_spectral_layout(G, dim, weight_attr, **kwargs)


def _ensure_edge_weights(G: nx.Graph, weight_attr: str) -> None:
    """Ensure all edges have the specified weight attribute."""
    for u, v in G.edges():
        if weight_attr not in G[u][v]:
            G[u][v][weight_attr] = 1.0


def _compute_mds_layout(
    G: nx.Graph,
    dim: int,
    use_geodesic_distances: bool,
    weight_attr: str,
    random_state: Optional[int],
    **kwargs,
) -> Dict[Any, np.ndarray]:
    """Compute MDS layout using geodesic or Euclidean distances."""
    nodes = list(G.nodes())
    n = len(nodes)

    if use_geodesic_distances:
        # Compute shortest path distances using edge weights
        # Note: NetworkX treats weights as costs for shortest path
        # Ricci flow increases weights for strong edges, so we may want to
        # invert or transform them. However, the standard interpretation
        # is that weight represents edge length/cost.
        try:
            dist_dict = dict(nx.all_pairs_dijkstra_path_length(G, weight=weight_attr))
        except Exception as e:
            logger.warning(f"Failed to compute shortest paths: {e}. Using fallback.")
            # Fallback: use unweighted distances
            dist_dict = dict(nx.all_pairs_shortest_path_length(G))

        # Build distance matrix
        dist_matrix = np.zeros((n, n))
        max_dist = 0
        for i, u in enumerate(nodes):
            for j, v in enumerate(nodes):
                if u in dist_dict and v in dist_dict[u]:
                    dist_matrix[i, j] = dist_dict[u][v]
                    max_dist = max(max_dist, dist_matrix[i, j])
                elif i != j:
                    # Nodes not connected: use a large distance
                    dist_matrix[i, j] = float("inf")

        # Replace infinite distances with a large finite value
        # Use 2x the maximum observed distance
        large_dist = max_dist * 2 if max_dist > 0 else 100.0
        dist_matrix[np.isinf(dist_matrix)] = large_dist
    else:
        # Use edge weights directly as dissimilarities
        # For this, we need a complete graph or fill in missing edges
        dist_matrix = (
            np.ones((n, n))
            * np.max([G[u][v].get(weight_attr, 1.0) for u, v in G.edges()])
            * 2
        )
        for i, u in enumerate(nodes):
            for j, v in enumerate(nodes):
                if i == j:
                    dist_matrix[i, j] = 0
                elif G.has_edge(u, v):
                    dist_matrix[i, j] = G[u][v].get(weight_attr, 1.0)

    # Apply MDS
    mds = MDS(
        n_components=dim,
        dissimilarity="precomputed",
        random_state=random_state,
        **kwargs,
    )

    try:
        coords = mds.fit_transform(dist_matrix)
    except Exception as e:
        logger.warning(f"MDS failed: {e}. Falling back to spring layout.")
        return _compute_spring_layout(G, dim, weight_attr, random_state)

    # Build position dictionary
    positions = {node: coords[i] for i, node in enumerate(nodes)}
    return positions


def _compute_spring_layout(
    G: nx.Graph, dim: int, weight_attr: str, random_state: Optional[int], **kwargs
) -> Dict[Any, np.ndarray]:
    """Compute weighted spring layout using NetworkX."""
    # NetworkX spring_layout interprets weight as strength (higher = pull closer)
    # Ricci flow increases weights for strong community edges, which is what we want

    # Set random seed if provided
    if random_state is not None:
        np.random.seed(random_state)

    # spring_layout in NetworkX only supports 2D or 3D
    pos = nx.spring_layout(G, dim=dim, weight=weight_attr, seed=random_state, **kwargs)

    # Convert to numpy arrays
    positions = {node: np.array(coords) for node, coords in pos.items()}
    return positions


def _compute_spectral_layout(
    G: nx.Graph, dim: int, weight_attr: str, **kwargs
) -> Dict[Any, np.ndarray]:
    """Compute spectral layout adapted to weighted adjacency."""
    # NetworkX spectral_layout uses Laplacian eigenvectors
    # It respects edge weights

    if dim == 3:
        # spectral_layout only supports 2D in NetworkX
        logger.warning("Spectral layout in NetworkX only supports dim=2. Using dim=2.")
        dim = 2

    try:
        pos = nx.spectral_layout(G, weight=weight_attr, dim=dim, **kwargs)
    except Exception as e:
        logger.warning(f"Spectral layout failed: {e}. Falling back to spring layout.")
        return _compute_spring_layout(G, dim, weight_attr, None)

    # Convert to numpy arrays
    positions = {node: np.array(coords) for node, coords in pos.items()}
    return positions
