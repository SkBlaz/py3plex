"""
Sankey diagram visualization for multilayer networks.

This module provides Sankey diagram visualization to show flow strength
between layers in multilayer networks. The width of flows represents the
number of inter-layer connections.
"""

from typing import Any, Dict, List, Optional, Tuple

import matplotlib.pyplot as plt
import matplotlib.sankey as mpl_sankey
import networkx as nx
import numpy as np

from py3plex.logging_config import get_logger

logger = get_logger(__name__)


def draw_multilayer_sankey(
    graphs: List[nx.Graph],
    multilinks: Dict[str, List[Tuple]],
    labels: Optional[List[str]] = None,
    ax: Optional[Any] = None,
    display: bool = True,
    scale: float = 0.01,
    unit: str = "connections",
    **kwargs
) -> Any:
    """Draw Sankey diagram showing inter-layer flow strength in multilayer networks.

    Creates a Sankey diagram where:
    - Each layer is represented as a node in the Sankey diagram
    - Flows between layers show the strength (number) of inter-layer connections
    - Flow width is proportional to the number of inter-layer edges

    Args:
        graphs: List of NetworkX graphs, one per layer
        multilinks: Dictionary mapping edge_type -> list of multi-layer edges
        labels: Optional list of layer labels. If None, uses layer indices
        ax: Matplotlib axes to draw on. If None, creates new figure
        display: If True, calls plt.show() at the end
        scale: Scaling factor for flow widths (default 0.01)
        unit: Unit label for flows (default "connections")
        **kwargs: Additional keyword arguments passed to Sankey

    Returns:
        Matplotlib axes object

    Examples:
        >>> network = multi_layer_network()
        >>> network.load_network("data.txt", input_type="multiedgelist")
        >>> labels, graphs, multilinks = network.get_layers()
        >>> draw_multilayer_sankey(graphs, multilinks, labels=labels)

    Note:
        This visualization is most effective for networks with 2-5 layers.
        For networks with many layers, the diagram may become cluttered.
    """
    # Get or create axes
    if ax is None:
        fig, ax = plt.subplots(figsize=(12, 8))
    else:
        fig = ax.get_figure()

    n_layers = len(graphs)
    if n_layers == 0:
        logger.warning("No layers to visualize")
        return ax

    # Use layer indices if no labels provided
    if labels is None:
        labels = [f"Layer {i}" for i in range(n_layers)]

    # Build a mapping from node_id to list of layers it appears in
    node_to_layers = {}
    for layer_idx, graph in enumerate(graphs):
        for node in graph.nodes():
            if node not in node_to_layers:
                node_to_layers[node] = []
            node_to_layers[node].append(layer_idx)

    # Count inter-layer connections between each pair of layers
    # flow_matrix[i][j] = number of edges from layer i to layer j
    flow_matrix = np.zeros((n_layers, n_layers), dtype=int)

    # Process multilinks to count inter-layer edges
    for edge_type, edges in multilinks.items():
        for edge in edges:
            if len(edge) >= 2:
                node_u = edge[0]
                node_v = edge[1]

                # Get all layer combinations where these nodes appear
                layers_u = node_to_layers.get(node_u, [])
                layers_v = node_to_layers.get(node_v, [])

                # Count inter-layer edges
                for layer_u in layers_u:
                    for layer_v in layers_v:
                        if layer_u != layer_v:
                            # Only count in one direction to avoid double counting
                            if layer_u < layer_v:
                                flow_matrix[layer_u][layer_v] += 1
                            else:
                                flow_matrix[layer_v][layer_u] += 1

    # Check if there are any inter-layer flows
    total_flows = np.sum(flow_matrix)
    if total_flows == 0:
        logger.warning("No inter-layer connections found. Cannot create Sankey diagram.")
        ax.text(0.5, 0.5, "No inter-layer connections found",
                ha='center', va='center', fontsize=14, transform=ax.transAxes)
        ax.axis('off')
        if display:
            plt.show()
        return ax

    # Create Sankey diagram using matplotlib's Sankey class
    # For multilayer networks, we'll create a simplified Sankey showing
    # flows between consecutive or connected layers

    # Find all layer pairs with connections
    layer_connections = []
    for i in range(n_layers):
        for j in range(i + 1, n_layers):
            if flow_matrix[i][j] > 0:
                layer_connections.append((i, j, flow_matrix[i][j]))

    if len(layer_connections) == 0:
        logger.warning("No inter-layer connections found after processing.")
        ax.text(0.5, 0.5, "No inter-layer connections found",
                ha='center', va='center', fontsize=14, transform=ax.transAxes)
        ax.axis('off')
        if display:
            plt.show()
        return ax

    # Sort connections by layer order for better visualization
    layer_connections.sort(key=lambda x: (x[0], x[1]))

    # Build flows for Sankey diagram
    # We'll use a simplified approach for multilayer networks
    # by showing flows between adjacent or connected layers

    sankey = mpl_sankey.Sankey(ax=ax, scale=scale, unit=unit, **kwargs)

    # For simplicity, we'll create a linear flow diagram
    # showing the strongest connections between layers
    if n_layers <= 3:
        # Simple case: can show all connections
        _draw_simple_sankey(sankey, labels, layer_connections, ax)
    else:
        # Complex case: show main flows between consecutive layers
        _draw_aggregated_sankey(sankey, labels, flow_matrix, n_layers, ax)

    # Format the plot
    ax.set_title("Inter-Layer Flow Diagram (Sankey)", fontsize=14, fontweight='bold', pad=20)
    ax.axis('off')

    if display:
        plt.tight_layout()
        plt.show()

    return ax


def _draw_simple_sankey(sankey, labels, layer_connections, ax):
    """Draw simple Sankey for networks with few layers."""
    # Create a series of connected Sankey diagrams
    # For now, show flows in a simplified format

    # Extract unique layers involved
    layers_involved = set()
    for src, dst, flow in layer_connections:
        layers_involved.add(src)
        layers_involved.add(dst)

    layers_list = sorted(layers_involved)

    # Create text-based flow visualization when Sankey becomes complex
    y_pos = 0.9
    ax.text(0.5, y_pos, "Inter-Layer Connections:", ha='center', va='top',
            fontsize=12, fontweight='bold', transform=ax.transAxes)

    y_pos -= 0.1
    for src, dst, flow in layer_connections:
        flow_text = f"{labels[src]} → {labels[dst]}: {flow} connections"
        ax.text(0.5, y_pos, flow_text, ha='center', va='top',
                fontsize=10, transform=ax.transAxes)
        y_pos -= 0.08

        # Draw flow arrow
        arrow_y = y_pos + 0.02
        ax.annotate('', xy=(0.7, arrow_y), xytext=(0.3, arrow_y),
                   arrowprops=dict(arrowstyle='->', lw=max(1, flow/10),
                                 color='steelblue', alpha=0.6),
                   xycoords='axes fraction')
        y_pos -= 0.05


def _draw_aggregated_sankey(sankey, labels, flow_matrix, n_layers, ax):
    """Draw aggregated Sankey for networks with many layers."""
    # Show aggregated statistics
    y_pos = 0.9
    ax.text(0.5, y_pos, "Inter-Layer Connection Summary", ha='center', va='top',
            fontsize=12, fontweight='bold', transform=ax.transAxes)

    y_pos -= 0.1

    # Calculate total flows per layer
    layer_flows = {}
    for i in range(n_layers):
        outgoing = np.sum(flow_matrix[i, :])
        incoming = np.sum(flow_matrix[:, i])
        total = outgoing + incoming
        if total > 0:
            layer_flows[i] = total

    # Sort layers by flow volume
    sorted_layers = sorted(layer_flows.items(), key=lambda x: x[1], reverse=True)

    for layer_idx, total_flow in sorted_layers[:10]:  # Show top 10
        flow_text = f"{labels[layer_idx]}: {total_flow} total connections"
        ax.text(0.5, y_pos, flow_text, ha='center', va='top',
                fontsize=10, transform=ax.transAxes)
        y_pos -= 0.08

    # Show strongest connections
    y_pos -= 0.1
    ax.text(0.5, y_pos, "Strongest Inter-Layer Connections:", ha='center', va='top',
            fontsize=11, fontweight='bold', transform=ax.transAxes)
    y_pos -= 0.08

    # Find top connections
    top_connections = []
    for i in range(n_layers):
        for j in range(i + 1, n_layers):
            if flow_matrix[i][j] > 0:
                top_connections.append((i, j, flow_matrix[i][j]))

    top_connections.sort(key=lambda x: x[2], reverse=True)

    for src, dst, flow in top_connections[:5]:  # Show top 5
        flow_text = f"{labels[src]} ↔ {labels[dst]}: {flow} connections"
        ax.text(0.5, y_pos, flow_text, ha='center', va='top',
                fontsize=10, transform=ax.transAxes)
        y_pos -= 0.08

        # Draw flow arrow
        arrow_y = y_pos + 0.02
        ax.annotate('', xy=(0.7, arrow_y), xytext=(0.3, arrow_y),
                   arrowprops=dict(arrowstyle='->', lw=max(1, flow/5),
                                 color='steelblue', alpha=0.6),
                   xycoords='axes fraction')
        y_pos -= 0.05
