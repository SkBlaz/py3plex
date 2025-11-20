"""
Ricci-flow-based visualization functions for multilayer networks.

This module provides high-level visualization functions that leverage Ricci flow
to create informative layouts for multilayer networks. Three main visualization
styles are supported:

1. Core (aggregated) visualization: Shows the aggregated network after Ricci flow
2. Per-layer visualization: Shows each layer with shared or independent layouts
3. Supra-graph visualization: Shows the full multilayer structure including inter-layer edges
"""

from typing import Any, Dict, List, Optional, Tuple, Union

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np

from py3plex.algorithms.curvature.ollivier_ricci_multilayer import (
    RicciBackendNotAvailable,
    GRAPHRICCICURVATURE_AVAILABLE,
)
from py3plex.logging_config import get_logger
from py3plex.visualization.ricci_layout import ricci_flow_layout_single

logger = get_logger(__name__)


def _extract_layers_from_core(core_network, directed=False):
    """
    Extract individual layer graphs from a multilayer core network.

    Args:
        core_network: NetworkX graph with nodes as (node_id, layer_id) tuples
        directed: Whether to create directed layer graphs

    Returns:
        Dictionary mapping layer_id to NetworkX graph
    """
    layers = {}

    # Extract layers
    for node in core_network.nodes():
        if isinstance(node, tuple) and len(node) == 2:
            node_id, layer_id = node
            if layer_id not in layers:
                layers[layer_id] = nx.DiGraph() if directed else nx.Graph()
            layers[layer_id].add_node(node_id)

    # Add edges
    for u, v, data in core_network.edges(data=True):
        if isinstance(u, tuple) and isinstance(v, tuple):
            u_id, u_layer = u
            v_id, v_layer = v
            if u_layer == v_layer:  # intra-layer edge only
                layers[u_layer].add_edge(u_id, v_id, **data)

    return layers


def visualize_multilayer_ricci_core(
    net,
    alpha: float = 0.5,
    iterations: int = 10,
    layout_type: str = "mds",
    dim: int = 2,
    curvature_attr: str = "ricciCurvature",
    weight_attr: str = "weight",
    node_color_by: str = "layer_overlap",
    edge_color_by: str = "curvature",
    node_size: Union[int, str] = 100,
    edge_width_scale: float = 2.0,
    figsize: Tuple[float, float] = (10, 8),
    ax: Optional[plt.Axes] = None,
    cmap_nodes: str = "viridis",
    cmap_edges: str = "RdBu_r",
    show_colorbar: bool = True,
    compute_if_missing: bool = True,
    **kwargs,
) -> Tuple[plt.Figure, plt.Axes, Dict[Any, np.ndarray]]:
    """
    Visualize the aggregated core network using Ricci-flow-based layout.

    This function emphasizes the global geometric structure across all layers
    combined. It uses Ricci flow to enhance the visibility of communities and
    bottleneck edges.

    Args:
        net: A multi_layer_network instance.
        alpha: Ollivier-Ricci parameter for flow computation. Default: 0.5.
        iterations: Number of Ricci flow iterations. Default: 10.
        layout_type: Layout algorithm ("mds", "spring", "spectral"). Default: "mds".
        dim: Dimensionality of layout (2 or 3). Default: 2.
        curvature_attr: Edge attribute name for curvature. Default: "ricciCurvature".
        weight_attr: Edge attribute name for weights. Default: "weight".
        node_color_by: Node coloring scheme:
            - "layer_overlap": Number of layers each node appears in
            - "degree": Node degree
            - "curvature": Mean incident edge curvature
            Default: "layer_overlap".
        edge_color_by: Edge coloring scheme:
            - "curvature": Edge curvature (red=negative, blue=positive)
            - "weight": Edge weight after flow
            Default: "curvature".
        node_size: Node size. Can be an integer or "degree" for degree-based sizing.
            Default: 100.
        edge_width_scale: Scaling factor for edge widths. Default: 2.0.
        figsize: Figure size as (width, height). Default: (10, 8).
        ax: Matplotlib axes to plot on. If None, creates new figure. Default: None.
        cmap_nodes: Colormap for nodes. Default: "viridis".
        cmap_edges: Colormap for edges. Default: "RdBu_r".
        show_colorbar: Whether to show colorbars. Default: True.
        compute_if_missing: If True, automatically compute Ricci flow if not
            already computed. If False, raise an error. Default: True.
        **kwargs: Additional keyword arguments for layout function.

    Returns:
        Tuple of (figure, axes, positions_dict) where positions_dict maps
        nodes to their coordinates.

    Raises:
        RicciBackendNotAvailable: If GraphRicciCurvature is not installed.
        ValueError: If the network has no core_network or other validation errors.

    Examples:
        >>> from py3plex.core import multinet
        >>> net = multinet.multi_layer_network()
        >>> net.add_edges([
        ...     ['A', 'layer1', 'B', 'layer1', 1],
        ...     ['B', 'layer1', 'C', 'layer1', 1],
        ... ], input_type="list")
        >>> fig, ax, pos = visualize_multilayer_ricci_core(net)
        >>> plt.show()
    """
    if not GRAPHRICCICURVATURE_AVAILABLE:
        raise RicciBackendNotAvailable()

    if net.core_network is None or net.core_network.number_of_nodes() == 0:
        raise ValueError("Network has no core_network or it is empty.")

    # Check if Ricci flow has been computed
    G = net.core_network
    has_curvature = any(curvature_attr in data for _, _, data in G.edges(data=True))

    if not has_curvature and compute_if_missing:
        logger.info("Ricci flow not detected. Computing Ricci flow on core network...")
        result = net.compute_ollivier_ricci_flow(
            mode="core",
            alpha=alpha,
            iterations=iterations,
            weight_attr=weight_attr,
            curvature_attr=curvature_attr,
            inplace=True,
        )
        G = result["core"]
    elif not has_curvature:
        raise ValueError(
            f"Ricci flow has not been computed on the core network. "
            f"Call net.compute_ollivier_ricci_flow(mode='core') first or "
            f"set compute_if_missing=True."
        )

    # Compute layout using Ricci-flow weights
    positions = ricci_flow_layout_single(
        G,
        dim=dim,
        use_geodesic_distances=(layout_type == "mds"),
        weight_attr=weight_attr,
        layout_type=layout_type,
        **kwargs,
    )

    # Create figure if needed
    if ax is None:
        if dim == 3:
            fig = plt.figure(figsize=figsize)
            ax = fig.add_subplot(111, projection="3d")
        else:
            fig, ax = plt.subplots(figsize=figsize)
    else:
        fig = ax.figure

    # Compute node colors
    node_colors = _compute_node_colors(net, G, node_color_by, curvature_attr)

    # Compute node sizes
    node_sizes = _compute_node_sizes(G, node_size)

    # Compute edge colors and widths
    edge_colors = _compute_edge_colors(G, edge_color_by, curvature_attr, weight_attr)
    edge_widths = _compute_edge_widths(G, weight_attr, edge_width_scale)

    # Draw the network
    if dim == 2:
        _draw_2d_network(
            G,
            positions,
            node_colors,
            node_sizes,
            edge_colors,
            edge_widths,
            ax,
            cmap_nodes,
            cmap_edges,
            show_colorbar,
        )
    else:
        _draw_3d_network(
            G,
            positions,
            node_colors,
            node_sizes,
            edge_colors,
            edge_widths,
            ax,
            cmap_nodes,
            cmap_edges,
        )

    ax.set_title(
        f"Ricci Flow Visualization - Core Network\n"
        f"(α={alpha}, iterations={iterations})",
        fontsize=12,
    )
    ax.axis("off")

    return fig, ax, positions


def _compute_node_colors(net, G, color_by, curvature_attr):
    """Compute node colors based on the specified scheme."""
    nodes = list(G.nodes())

    if color_by == "layer_overlap":
        # Count number of layers each node appears in
        # Extract layers from core network
        layers = _extract_layers_from_core(net.core_network, net.directed)

        colors = []
        for node in nodes:
            # Handle nodes that may be tuples (node_id, layer_id)
            if isinstance(node, tuple) and len(node) == 2:
                node_id, _ = node
            else:
                node_id = node

            count = sum(
                1
                for layer_id, layer_graph in layers.items()
                if node_id in layer_graph.nodes()
            )
            colors.append(count)
        return np.array(colors)

    elif color_by == "degree":
        return np.array([G.degree(node) for node in nodes])

    elif color_by == "curvature":
        # Mean incident edge curvature
        colors = []
        for node in nodes:
            curvatures = [
                G[node][neighbor].get(curvature_attr, 0)
                for neighbor in G.neighbors(node)
            ]
            colors.append(np.mean(curvatures) if curvatures else 0)
        return np.array(colors)

    else:
        # Default to uniform color
        return np.ones(len(nodes))


def _compute_node_sizes(G, node_size):
    """Compute node sizes."""
    if isinstance(node_size, int):
        return [node_size] * G.number_of_nodes()
    elif node_size == "degree":
        degrees = dict(G.degree())
        max_degree = max(degrees.values()) if degrees else 1
        return [50 + 200 * (degrees[node] / max_degree) for node in G.nodes()]
    else:
        return [100] * G.number_of_nodes()


def _compute_edge_colors(G, color_by, curvature_attr, weight_attr):
    """Compute edge colors based on the specified scheme."""
    if color_by == "curvature":
        return [G[u][v].get(curvature_attr, 0) for u, v in G.edges()]
    elif color_by == "weight":
        return [G[u][v].get(weight_attr, 1.0) for u, v in G.edges()]
    else:
        return [0.5] * G.number_of_edges()


def _compute_edge_widths(G, weight_attr, scale):
    """Compute edge widths based on weights."""
    weights = [G[u][v].get(weight_attr, 1.0) for u, v in G.edges()]
    if not weights:
        return []

    min_w, max_w = min(weights), max(weights)
    if max_w > min_w:
        normalized = [(w - min_w) / (max_w - min_w) for w in weights]
        return [0.5 + scale * w for w in normalized]
    else:
        return [1.0] * len(weights)


def _draw_2d_network(
    G,
    positions,
    node_colors,
    node_sizes,
    edge_colors,
    edge_widths,
    ax,
    cmap_nodes,
    cmap_edges,
    show_colorbar,
):
    """Draw 2D network visualization."""
    # Draw edges
    if G.number_of_edges() > 0:
        edge_collection = nx.draw_networkx_edges(
            G,
            positions,
            ax=ax,
            width=edge_widths,
            edge_color=edge_colors,
            edge_cmap=plt.get_cmap(cmap_edges),
            edge_vmin=min(edge_colors) if edge_colors else 0,
            edge_vmax=max(edge_colors) if edge_colors else 1,
            alpha=0.6,
        )

        if show_colorbar and edge_colors:
            plt.colorbar(edge_collection, ax=ax, label="Edge Curvature")

    # Draw nodes
    if G.number_of_nodes() > 0:
        node_collection = nx.draw_networkx_nodes(
            G,
            positions,
            ax=ax,
            node_size=node_sizes,
            node_color=node_colors,
            cmap=plt.get_cmap(cmap_nodes),
            vmin=min(node_colors) if len(node_colors) > 0 else 0,
            vmax=max(node_colors) if len(node_colors) > 0 else 1,
            alpha=0.8,
        )

        if show_colorbar and len(node_colors) > 0:
            plt.colorbar(node_collection, ax=ax, label="Node Color")

    # Draw labels for small networks
    if G.number_of_nodes() < 50:
        nx.draw_networkx_labels(G, positions, ax=ax, font_size=8)


def _draw_3d_network(
    G,
    positions,
    node_colors,
    node_sizes,
    edge_colors,
    edge_widths,
    ax,
    cmap_nodes,
    cmap_edges,
):
    """Draw 3D network visualization."""
    # Extract 3D coordinates
    xs = [positions[node][0] for node in G.nodes()]
    ys = [positions[node][1] for node in G.nodes()]
    zs = [positions[node][2] for node in G.nodes()]

    # Draw nodes
    ax.scatter(xs, ys, zs, c=node_colors, s=node_sizes, cmap=cmap_nodes, alpha=0.8)

    # Draw edges
    for (u, v), color, width in zip(G.edges(), edge_colors, edge_widths):
        x_line = [positions[u][0], positions[v][0]]
        y_line = [positions[u][1], positions[v][1]]
        z_line = [positions[u][2], positions[v][2]]
        ax.plot(x_line, y_line, z_line, color="gray", linewidth=width, alpha=0.3)


def visualize_multilayer_ricci_layers(
    net,
    layers: Optional[List[Any]] = None,
    alpha: float = 0.5,
    iterations: int = 10,
    layout_type: str = "mds",
    dim: int = 2,
    arrangement: str = "grid",
    curvature_attr: str = "ricciCurvature",
    weight_attr: str = "weight",
    share_layout: bool = True,
    figsize: Tuple[float, float] = (12, 8),
    node_size: int = 100,
    edge_width_scale: float = 2.0,
    cmap_edges: str = "RdBu_r",
    compute_if_missing: bool = True,
    **kwargs,
) -> Tuple[plt.Figure, Dict[Any, Dict[Any, np.ndarray]]]:
    """
    Visualize individual layers using Ricci-flow-based layouts.

    This function allows comparison of layer structures using shared or
    independent coordinate systems derived from Ricci flow.

    Args:
        net: A multi_layer_network instance.
        layers: List of layer identifiers to visualize. If None, uses all layers.
        alpha: Ollivier-Ricci parameter. Default: 0.5.
        iterations: Number of Ricci flow iterations. Default: 10.
        layout_type: Layout algorithm. Default: "mds".
        dim: Dimensionality of layout (must be 2 for grid arrangement). Default: 2.
        arrangement: How to arrange layers:
            - "grid": Separate subplots in a grid
            - "stacked": Overlaid on same axes
            Default: "grid".
        curvature_attr: Edge attribute for curvature. Default: "ricciCurvature".
        weight_attr: Edge attribute for weights. Default: "weight".
        share_layout: If True, use shared coordinates across layers. Default: True.
        figsize: Figure size. Default: (12, 8).
        node_size: Size of nodes. Default: 100.
        edge_width_scale: Scaling for edge widths. Default: 2.0.
        cmap_edges: Colormap for edges. Default: "RdBu_r".
        compute_if_missing: Auto-compute Ricci flow if missing. Default: True.
        **kwargs: Additional layout arguments.

    Returns:
        Tuple of (figure, layer_positions_dict) where layer_positions_dict
        maps layer IDs to position dictionaries.

    Raises:
        RicciBackendNotAvailable: If GraphRicciCurvature is not installed.

    Examples:
        >>> fig, pos_dict = visualize_multilayer_ricci_layers(
        ...     net, arrangement="grid", share_layout=True
        ... )
        >>> plt.show()
    """
    if not GRAPHRICCICURVATURE_AVAILABLE:
        raise RicciBackendNotAvailable()

    if dim != 2 and arrangement == "grid":
        raise ValueError("Grid arrangement only supports dim=2.")

    # Determine which layers to visualize
    if layers is None:
        # Extract layer IDs from core network
        extracted_layers = _extract_layers_from_core(net.core_network, net.directed)
        layers = list(extracted_layers.keys())

    if len(layers) == 0:
        raise ValueError("No layers to visualize.")

    # Compute or verify Ricci flow
    if share_layout:
        # Use core network for shared layout
        if compute_if_missing:
            net.compute_ollivier_ricci_flow(
                mode="core", alpha=alpha, iterations=iterations, inplace=True
            )

        # Compute shared layout from core network
        shared_pos = ricci_flow_layout_single(
            net.core_network,
            dim=dim,
            layout_type=layout_type,
            weight_attr=weight_attr,
            **kwargs,
        )
    else:
        shared_pos = None
        # Compute Ricci flow per layer if needed
        if compute_if_missing:
            net.compute_ollivier_ricci_flow(
                mode="layers",
                layers=layers,
                alpha=alpha,
                iterations=iterations,
                inplace=True,
            )

    # Create figure
    if arrangement == "grid":
        n_layers = len(layers)
        n_cols = int(np.ceil(np.sqrt(n_layers)))
        n_rows = int(np.ceil(n_layers / n_cols))
        fig, axes = plt.subplots(n_rows, n_cols, figsize=figsize)
        if n_layers == 1:
            axes = np.array([axes])
        axes = axes.flatten()
    else:
        fig, ax = plt.subplots(figsize=figsize)
        axes = [ax] * len(layers)

    layer_positions = {}

    # Extract layers from core network
    extracted_layers = _extract_layers_from_core(net.core_network, net.directed)

    for idx, layer_id in enumerate(layers):
        layer_graph = extracted_layers.get(layer_id)
        if layer_graph is None or layer_graph.number_of_nodes() == 0:
            logger.warning(f"Layer {layer_id} is empty or missing. Skipping.")
            continue

        # Get positions for this layer
        if share_layout:
            # Filter shared positions to nodes in this layer
            layer_pos = {
                node: shared_pos[node]
                for node in layer_graph.nodes()
                if node in shared_pos
            }
        else:
            # Compute independent layout for this layer
            layer_pos = ricci_flow_layout_single(
                layer_graph,
                dim=dim,
                layout_type=layout_type,
                weight_attr=weight_attr,
                **kwargs,
            )

        layer_positions[layer_id] = layer_pos

        # Draw this layer
        ax_current = axes[idx]
        _draw_single_layer(
            layer_graph,
            layer_pos,
            layer_id,
            ax_current,
            node_size,
            edge_width_scale,
            weight_attr,
            curvature_attr,
            cmap_edges,
        )

    # Hide unused subplots
    if arrangement == "grid":
        for idx in range(len(layers), len(axes)):
            axes[idx].axis("off")

    fig.suptitle(
        f"Ricci Flow Per-Layer Visualization\n"
        f"(α={alpha}, iterations={iterations}, share_layout={share_layout})",
        fontsize=14,
    )
    plt.tight_layout()

    return fig, layer_positions


def _draw_single_layer(
    layer_graph,
    positions,
    layer_id,
    ax,
    node_size,
    edge_width_scale,
    weight_attr,
    curvature_attr,
    cmap_edges,
):
    """Draw a single layer on the given axes."""
    # Compute edge colors and widths
    edge_colors = [
        layer_graph[u][v].get(curvature_attr, 0) for u, v in layer_graph.edges()
    ]
    edge_widths = _compute_edge_widths(layer_graph, weight_attr, edge_width_scale)

    # Draw edges
    if layer_graph.number_of_edges() > 0:
        nx.draw_networkx_edges(
            layer_graph,
            positions,
            ax=ax,
            width=edge_widths,
            edge_color=edge_colors,
            edge_cmap=plt.get_cmap(cmap_edges),
            alpha=0.6,
        )

    # Draw nodes
    nx.draw_networkx_nodes(
        layer_graph,
        positions,
        ax=ax,
        node_size=node_size,
        node_color="lightblue",
        alpha=0.8,
    )

    # Draw labels for small networks
    if layer_graph.number_of_nodes() < 30:
        nx.draw_networkx_labels(layer_graph, positions, ax=ax, font_size=7)

    ax.set_title(f"Layer: {layer_id}", fontsize=10)
    ax.axis("off")


def visualize_multilayer_ricci_supra(
    net,
    alpha: float = 0.5,
    iterations: int = 10,
    layout_type: str = "mds",
    dim: int = 2,
    curvature_attr: str = "ricciCurvature",
    weight_attr: str = "weight",
    layer_separation: Optional[float] = None,
    node_color_by: str = "layer",
    edge_color_by: str = "curvature",
    node_size: int = 50,
    edge_width_scale: float = 1.5,
    figsize: Tuple[float, float] = (12, 10),
    ax: Optional[plt.Axes] = None,
    cmap_nodes: str = "tab10",
    cmap_edges: str = "RdBu_r",
    interlayer_alpha: float = 0.3,
    compute_if_missing: bool = True,
    **kwargs,
) -> Tuple[plt.Figure, plt.Axes, Dict[Any, np.ndarray]]:
    """
    Visualize the full supra-graph using Ricci-flow-based layout.

    This function shows the complete multilayer structure including both
    intra-layer edges (within layers) and inter-layer edges (coupling between
    layers).

    Args:
        net: A multi_layer_network instance.
        alpha: Ollivier-Ricci parameter. Default: 0.5.
        iterations: Number of Ricci flow iterations. Default: 10.
        layout_type: Layout algorithm. Default: "mds".
        dim: Dimensionality (2 or 3). Default: 2.
        curvature_attr: Edge attribute for curvature. Default: "ricciCurvature".
        weight_attr: Edge attribute for weights. Default: "weight".
        layer_separation: If not None and dim==3, separates layers along z-axis.
        node_color_by: Node coloring ("layer" or "curvature"). Default: "layer".
        edge_color_by: Edge coloring ("curvature" or "weight"). Default: "curvature".
        node_size: Size of nodes. Default: 50.
        edge_width_scale: Scaling for edge widths. Default: 1.5.
        figsize: Figure size. Default: (12, 10).
        ax: Matplotlib axes. If None, creates new figure.
        cmap_nodes: Colormap for nodes. Default: "tab10".
        cmap_edges: Colormap for edges. Default: "RdBu_r".
        interlayer_alpha: Transparency for inter-layer edges. Default: 0.3.
        compute_if_missing: Auto-compute Ricci flow if missing. Default: True.
        **kwargs: Additional layout arguments.

    Returns:
        Tuple of (figure, axes, positions_dict).

    Raises:
        RicciBackendNotAvailable: If GraphRicciCurvature is not installed.

    Examples:
        >>> fig, ax, pos = visualize_multilayer_ricci_supra(net, dim=3)
        >>> plt.show()
    """
    if not GRAPHRICCICURVATURE_AVAILABLE:
        raise RicciBackendNotAvailable()

    # Compute or verify Ricci flow on supra-graph
    if compute_if_missing:
        result = net.compute_ollivier_ricci_flow(
            mode="supra", alpha=alpha, iterations=iterations, inplace=False
        )
        G_supra = result["supra"]
    else:
        # Build supra-graph (similar to compute_ollivier_ricci)
        G_supra = net._build_supra_graph()
        # Check if it has curvature
        has_curv = any(
            curvature_attr in data for _, _, data in G_supra.edges(data=True)
        )
        if not has_curv:
            raise ValueError(
                "Ricci flow not computed on supra-graph. "
                "Set compute_if_missing=True or call net.compute_ollivier_ricci_flow(mode='supra')."
            )

    # Compute layout
    positions = ricci_flow_layout_single(
        G_supra, dim=dim, layout_type=layout_type, weight_attr=weight_attr, **kwargs
    )

    # Apply layer separation in 3D if requested
    if layer_separation is not None and dim == 3:
        positions = _apply_layer_separation(positions, net, layer_separation)

    # Create figure
    if ax is None:
        if dim == 3:
            fig = plt.figure(figsize=figsize)
            ax = fig.add_subplot(111, projection="3d")
        else:
            fig, ax = plt.subplots(figsize=figsize)
    else:
        fig = ax.figure

    # Separate intra-layer and inter-layer edges
    intra_edges = []
    inter_edges = []
    for u, v in G_supra.edges():
        if isinstance(u, tuple) and isinstance(v, tuple):
            if u[1] == v[1]:  # Same layer
                intra_edges.append((u, v))
            elif u[0] == v[0]:  # Same node, different layers
                inter_edges.append((u, v))

    # Compute colors
    if node_color_by == "layer":
        node_colors = _compute_supra_node_colors_by_layer(G_supra)
    else:
        node_colors = _compute_edge_colors(
            G_supra, edge_color_by, curvature_attr, weight_attr
        )

    edge_colors_intra = [G_supra[u][v].get(curvature_attr, 0) for u, v in intra_edges]
    edge_colors_inter = [G_supra[u][v].get(curvature_attr, 0) for u, v in inter_edges]

    # Draw
    if dim == 2:
        _draw_supra_2d(
            G_supra,
            positions,
            intra_edges,
            inter_edges,
            node_colors,
            edge_colors_intra,
            edge_colors_inter,
            node_size,
            edge_width_scale,
            weight_attr,
            ax,
            cmap_nodes,
            cmap_edges,
            interlayer_alpha,
        )
    else:
        _draw_supra_3d(
            G_supra,
            positions,
            intra_edges,
            inter_edges,
            node_colors,
            node_size,
            ax,
            interlayer_alpha,
        )

    ax.set_title(
        f"Ricci Flow Supra-Graph Visualization\n"
        f"(α={alpha}, iterations={iterations})",
        fontsize=12,
    )
    ax.axis("off")

    return fig, ax, positions


def _apply_layer_separation(positions, net, separation):
    """Apply z-axis separation for layers in 3D layout."""
    # Extract layer mapping from node tuples
    layer_to_z = {}
    extracted_layers = _extract_layers_from_core(net.core_network, net.directed)
    layers = list(extracted_layers.keys())
    for idx, layer in enumerate(layers):
        layer_to_z[layer] = idx * separation

    # Update positions
    new_positions = {}
    for node, pos in positions.items():
        if isinstance(node, tuple) and len(node) == 2:
            layer_id = node[1]
            z_offset = layer_to_z.get(layer_id, 0)
            new_positions[node] = np.array([pos[0], pos[1], z_offset])
        else:
            new_positions[node] = pos

    return new_positions


def _compute_supra_node_colors_by_layer(G_supra):
    """Assign colors based on layer ID."""
    node_colors = []
    layer_map = {}
    layer_counter = 0

    for node in G_supra.nodes():
        if isinstance(node, tuple) and len(node) == 2:
            layer_id = node[1]
            if layer_id not in layer_map:
                layer_map[layer_id] = layer_counter
                layer_counter += 1
            node_colors.append(layer_map[layer_id])
        else:
            node_colors.append(0)

    return node_colors


def _draw_supra_2d(
    G_supra,
    positions,
    intra_edges,
    inter_edges,
    node_colors,
    edge_colors_intra,
    edge_colors_inter,
    node_size,
    edge_width_scale,
    weight_attr,
    ax,
    cmap_nodes,
    cmap_edges,
    interlayer_alpha,
):
    """Draw 2D supra-graph."""
    # Draw inter-layer edges (lighter, more transparent)
    if inter_edges:
        inter_widths = [
            0.5 + edge_width_scale * 0.3 * G_supra[u][v].get(weight_attr, 1.0)
            for u, v in inter_edges
        ]
        nx.draw_networkx_edges(
            G_supra,
            positions,
            edgelist=inter_edges,
            ax=ax,
            width=inter_widths,
            edge_color="gray",
            alpha=interlayer_alpha,
            style="dashed",
        )

    # Draw intra-layer edges
    if intra_edges:
        intra_widths = _compute_edge_widths(
            nx.Graph(intra_edges), weight_attr, edge_width_scale
        )
        nx.draw_networkx_edges(
            G_supra,
            positions,
            edgelist=intra_edges,
            ax=ax,
            width=intra_widths,
            edge_color=edge_colors_intra,
            edge_cmap=plt.get_cmap(cmap_edges),
            alpha=0.7,
        )

    # Draw nodes
    nx.draw_networkx_nodes(
        G_supra,
        positions,
        ax=ax,
        node_size=node_size,
        node_color=node_colors,
        cmap=plt.get_cmap(cmap_nodes),
        alpha=0.8,
    )


def _draw_supra_3d(
    G_supra,
    positions,
    intra_edges,
    inter_edges,
    node_colors,
    node_size,
    ax,
    interlayer_alpha,
):
    """Draw 3D supra-graph."""
    # Draw nodes
    xs = [positions[node][0] for node in G_supra.nodes()]
    ys = [positions[node][1] for node in G_supra.nodes()]
    zs = [positions[node][2] for node in G_supra.nodes()]
    ax.scatter(xs, ys, zs, c=node_colors, s=node_size, alpha=0.8)

    # Draw intra-layer edges
    for u, v in intra_edges:
        ax.plot(
            [positions[u][0], positions[v][0]],
            [positions[u][1], positions[v][1]],
            [positions[u][2], positions[v][2]],
            color="blue",
            linewidth=1,
            alpha=0.5,
        )

    # Draw inter-layer edges
    for u, v in inter_edges:
        ax.plot(
            [positions[u][0], positions[v][0]],
            [positions[u][1], positions[v][1]],
            [positions[u][2], positions[v][2]],
            color="gray",
            linewidth=0.5,
            alpha=interlayer_alpha,
            linestyle="--",
        )
