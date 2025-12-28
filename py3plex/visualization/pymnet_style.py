"""
Pymnet style multilayer network visualization.

This module provides pymnet style visualization for multilayer networks,
inspired by the pymnet library's visualization approach. The implementation
is native to py3plex and renders using Matplotlib.

Reference:
    Kivelä, M., Arenas, A., Barthelemy, M., Gleeson, J. P., Moreno, Y., & Porter, M. A. (2014).
    Multilayer networks. Journal of complex networks, 2(3), 203-271.
    
    Pymnet library: https://github.com/bolozna/Multilayer-networks-library

Key features:
- Deterministic layouts with seed control
- Clean stacked layer visualization
- Shared node positions across layers
- Configurable node and edge styling
- Support for multiple input formats

Example:
    >>> from py3plex.core import multinet
    >>> from py3plex.visualization.pymnet_style import draw_multilayer_pymnet
    >>> 
    >>> # Create multilayer network
    >>> net = multinet.multi_layer_network(directed=False)
    >>> # ... add nodes and edges ...
    >>> 
    >>> # Draw pymnet style visualization
    >>> fig, ax, handles, positions = draw_multilayer_pymnet(
    ...     net,
    ...     layout="spring",
    ...     seed=42,
    ...     layer_gap=2.5
    ... )
    >>> fig.savefig("multilayer_pymnet.png")
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union
import warnings

import matplotlib.pyplot as plt
import matplotlib as mpl
import networkx as nx
import numpy as np

from py3plex.exceptions import VisualizationError, Py3plexFormatError
from py3plex.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class MultilayerGraph:
    """
    Internal normalized structure for multilayer graphs.
    
    This structure represents a multilayer network with explicit layer separation.
    
    Attributes:
        layers: Ordered list of layer names
        nodes: Dict mapping layer name to set of node identifiers in that layer
        intra_edges: Dict mapping layer name to list of edge tuples (u, v) within that layer
        inter_edges: List of inter-layer edge tuples (u, layer_u, v, layer_v)
    """
    layers: List[str]
    nodes: Dict[str, Set[Any]] = field(default_factory=dict)
    intra_edges: Dict[str, List[Tuple[Any, Any]]] = field(default_factory=dict)
    inter_edges: List[Tuple[Any, str, Any, str]] = field(default_factory=list)


def to_multilayer_graph(obj: Any) -> MultilayerGraph:
    """
    Convert various input formats to MultilayerGraph.
    
    Supported formats:
    - MultilayerGraph: Pass-through
    - dict[str, nx.Graph]: Dictionary mapping layer names to NetworkX graphs
    - nx.Graph with 'layer' node attribute: Single graph with layer info in nodes
    - list of tuples: Edge list format [(u, layer_u, v, layer_v), ...]
    - py3plex multi_layer_network: Native py3plex format
    
    Args:
        obj: Input object in one of the supported formats
        
    Returns:
        MultilayerGraph: Normalized multilayer graph structure
        
    Raises:
        Py3plexFormatError: If the input format is not recognized or invalid
        
    Example:
        >>> # From dict of NetworkX graphs
        >>> layers = {'A': nx.karate_club_graph(), 'B': nx.erdos_renyi_graph(10, 0.3)}
        >>> mlg = to_multilayer_graph(layers)
        >>> 
        >>> # From edge list
        >>> edges = [('n1', 'A', 'n2', 'A'), ('n1', 'A', 'n1', 'B')]
        >>> mlg = to_multilayer_graph(edges)
    """
    # Already a MultilayerGraph
    if isinstance(obj, MultilayerGraph):
        return obj
    
    # Dictionary of NetworkX graphs (layer -> graph)
    if isinstance(obj, dict) and all(isinstance(v, nx.Graph) for v in obj.values()):
        return _from_dict_of_graphs(obj)
    
    # Single NetworkX graph with 'layer' attribute
    if isinstance(obj, nx.Graph):
        return _from_nx_graph_with_layers(obj)
    
    # Edge list format
    if isinstance(obj, (list, tuple)) and len(obj) > 0:
        if isinstance(obj[0], (list, tuple)) and len(obj[0]) == 4:
            return _from_edge_list(obj)
    
    # Try py3plex multi_layer_network
    if hasattr(obj, 'get_layers'):
        return _from_py3plex_network(obj)
    
    raise Py3plexFormatError(
        f"Unsupported input format: {type(obj).__name__}",
        suggestions=[
            "Use dict[str, nx.Graph] for layer -> graph mapping",
            "Use nx.Graph with 'layer' node attribute",
            "Use edge list format: [(u, layer_u, v, layer_v), ...]",
            "Use py3plex.core.multinet.multi_layer_network",
        ]
    )


def _from_dict_of_graphs(layer_graphs: Dict[str, nx.Graph]) -> MultilayerGraph:
    """Convert dictionary of NetworkX graphs to MultilayerGraph."""
    mlg = MultilayerGraph(layers=sorted(layer_graphs.keys()))
    
    for layer_name, graph in layer_graphs.items():
        # Extract nodes
        mlg.nodes[layer_name] = set(graph.nodes())
        
        # Extract intra-layer edges
        mlg.intra_edges[layer_name] = list(graph.edges())
    
    return mlg


def _from_nx_graph_with_layers(graph: nx.Graph) -> MultilayerGraph:
    """Convert NetworkX graph with 'layer' attribute to MultilayerGraph."""
    mlg = MultilayerGraph(layers=[])
    layer_set = set()
    
    # Collect nodes by layer
    for node, data in graph.nodes(data=True):
        if 'layer' not in data:
            raise Py3plexFormatError(
                "NetworkX graph missing 'layer' attribute on nodes",
                suggestions=["Ensure all nodes have a 'layer' attribute"]
            )
        layer = data['layer']
        layer_set.add(layer)
        
        if layer not in mlg.nodes:
            mlg.nodes[layer] = set()
            mlg.intra_edges[layer] = []
        
        mlg.nodes[layer].add(node)
    
    mlg.layers = sorted(layer_set)
    
    # Classify edges as intra or inter
    for u, v, data in graph.edges(data=True):
        u_layer = graph.nodes[u].get('layer')
        v_layer = graph.nodes[v].get('layer')
        
        if u_layer == v_layer:
            # Intra-layer edge
            mlg.intra_edges[u_layer].append((u, v))
        else:
            # Inter-layer edge
            mlg.inter_edges.append((u, u_layer, v, v_layer))
    
    return mlg


def _from_edge_list(edges: List[Tuple[Any, str, Any, str]]) -> MultilayerGraph:
    """Convert edge list to MultilayerGraph."""
    mlg = MultilayerGraph(layers=[])
    layer_set = set()
    
    # Process all edges
    for edge in edges:
        if len(edge) != 4:
            raise Py3plexFormatError(
                f"Invalid edge format: {edge}. Expected (u, layer_u, v, layer_v)",
                suggestions=["Ensure all edges are 4-tuples: (u, layer_u, v, layer_v)"]
            )
        
        u, layer_u, v, layer_v = edge
        layer_set.add(layer_u)
        layer_set.add(layer_v)
        
        # Ensure layer structures exist
        if layer_u not in mlg.nodes:
            mlg.nodes[layer_u] = set()
            mlg.intra_edges[layer_u] = []
        if layer_v not in mlg.nodes:
            mlg.nodes[layer_v] = set()
            mlg.intra_edges[layer_v] = []
        
        # Add nodes
        mlg.nodes[layer_u].add(u)
        mlg.nodes[layer_v].add(v)
        
        # Classify edge
        if layer_u == layer_v:
            mlg.intra_edges[layer_u].append((u, v))
        else:
            mlg.inter_edges.append((u, layer_u, v, layer_v))
    
    mlg.layers = sorted(layer_set)
    return mlg


def _from_py3plex_network(network: Any) -> MultilayerGraph:
    """Convert py3plex multi_layer_network to MultilayerGraph."""
    mlg = MultilayerGraph(layers=[])
    
    try:
        # Get layers from py3plex network
        labels, graphs, multilinks = network.get_layers("diagonal")
        
        mlg.layers = list(labels)
        
        # Process each layer
        for layer_name, graph in zip(labels, graphs):
            mlg.nodes[layer_name] = set(graph.nodes())
            mlg.intra_edges[layer_name] = list(graph.edges())
        
        # Process inter-layer edges
        for edge_type, edges in multilinks.items():
            for edge in edges:
                # Edge format in py3plex: (source, target, source_layer, target_layer)
                if len(edge) == 4:
                    u, v, layer_u, layer_v = edge
                    if layer_u != layer_v:
                        mlg.inter_edges.append((u, layer_u, v, layer_v))
        
        return mlg
        
    except Exception as e:
        raise Py3plexFormatError(
            f"Failed to convert py3plex network: {str(e)}",
            suggestions=["Ensure the network is a valid py3plex multi_layer_network"]
        )


def _compute_layout(
    mlg: MultilayerGraph,
    layout: Union[str, Callable],
    seed: Optional[int] = 42
) -> Dict[Any, Tuple[float, float]]:
    """
    Compute 2D layout for nodes based on aggregated graph.
    
    This function creates a single aggregated graph from all layers and
    computes a shared layout that will be used across all layers.
    
    Args:
        mlg: MultilayerGraph structure
        layout: Layout algorithm name or callable
        seed: Random seed for deterministic layouts
        
    Returns:
        Dictionary mapping node IDs to (x, y) positions
        
    Raises:
        VisualizationError: If layout computation fails
    """
    # Create aggregated graph with all unique nodes
    agg_graph = nx.Graph()
    
    # Add all nodes from all layers
    all_nodes = set()
    for layer_nodes in mlg.nodes.values():
        all_nodes.update(layer_nodes)
    agg_graph.add_nodes_from(all_nodes)
    
    # Add all intra-layer edges (aggregated)
    for edges in mlg.intra_edges.values():
        agg_graph.add_edges_from(edges)
    
    # Add inter-layer edges (using just node IDs)
    for u, _, v, _ in mlg.inter_edges:
        agg_graph.add_edge(u, v)
    
    # Compute layout
    if callable(layout):
        # Custom layout function
        try:
            positions = layout(agg_graph)
        except Exception as e:
            raise VisualizationError(
                f"Custom layout function failed: {str(e)}",
                suggestions=["Ensure layout function accepts nx.Graph and returns dict[node, (x,y)]"]
            )
    elif layout == "spring":
        positions = nx.spring_layout(agg_graph, seed=seed)
    elif layout == "kamada_kawai":
        if len(agg_graph.nodes()) > 0 and nx.number_connected_components(agg_graph) == 1:
            positions = nx.kamada_kawai_layout(agg_graph)
        else:
            # Fallback for disconnected graphs
            positions = nx.spring_layout(agg_graph, seed=seed)
    elif layout == "circular":
        positions = nx.circular_layout(agg_graph)
    elif layout == "spectral":
        if len(agg_graph.edges()) > 0:
            positions = nx.spectral_layout(agg_graph)
        else:
            positions = nx.circular_layout(agg_graph)
    else:
        raise VisualizationError(
            f"Unknown layout algorithm: {layout}",
            suggestions=["Use 'spring', 'kamada_kawai', 'circular', 'spectral', or provide a callable"]
        )
    
    return positions


def _get_node_colors(
    mlg: MultilayerGraph,
    node_color_by: Union[str, Callable],
    positions: Dict[Any, Tuple[float, float]]
) -> Dict[str, Dict[Any, str]]:
    """
    Compute node colors for each layer.
    
    Args:
        mlg: MultilayerGraph structure
        node_color_by: Coloring strategy ("layer", "degree", "community", or callable)
        positions: Node positions (used for degree calculation)
        
    Returns:
        Dict mapping layer name to dict mapping node to color
    """
    colors = {}
    
    if node_color_by == "layer":
        # Color by layer using matplotlib tab palette
        cmap = plt.cm.get_cmap('tab10')
        layer_colors = {layer: mpl.colors.rgb2hex(cmap(i % 10)) 
                       for i, layer in enumerate(mlg.layers)}
        
        for layer in mlg.layers:
            colors[layer] = {node: layer_colors[layer] for node in mlg.nodes[layer]}
            
    elif node_color_by == "degree":
        # Color by degree in aggregated graph
        # Build aggregated degree
        degree_map = {}
        for layer in mlg.layers:
            for u, v in mlg.intra_edges[layer]:
                degree_map[u] = degree_map.get(u, 0) + 1
                degree_map[v] = degree_map.get(v, 0) + 1
        
        for u, _, v, _ in mlg.inter_edges:
            degree_map[u] = degree_map.get(u, 0) + 1
            degree_map[v] = degree_map.get(v, 0) + 1
        
        # Normalize degrees and map to colors
        if degree_map:
            max_degree = max(degree_map.values())
            min_degree = min(degree_map.values())
            degree_range = max_degree - min_degree if max_degree > min_degree else 1
            
            cmap = plt.cm.get_cmap('viridis')
            
            for layer in mlg.layers:
                colors[layer] = {}
                for node in mlg.nodes[layer]:
                    deg = degree_map.get(node, 0)
                    normalized = (deg - min_degree) / degree_range
                    colors[layer][node] = mpl.colors.rgb2hex(cmap(normalized))
        else:
            # No edges, use default color
            for layer in mlg.layers:
                colors[layer] = {node: '#1f77b4' for node in mlg.nodes[layer]}
                
    elif callable(node_color_by):
        # Custom coloring function
        for layer in mlg.layers:
            colors[layer] = {}
            for node in mlg.nodes[layer]:
                try:
                    color = node_color_by(node, layer)
                    colors[layer][node] = color
                except Exception as e:
                    logger.warning(f"Custom color function failed for node {node} in layer {layer}: {e}")
                    colors[layer][node] = '#1f77b4'
    else:
        # Default: use layer colors
        cmap = plt.cm.get_cmap('tab10')
        layer_colors = {layer: mpl.colors.rgb2hex(cmap(i % 10)) 
                       for i, layer in enumerate(mlg.layers)}
        
        for layer in mlg.layers:
            colors[layer] = {node: layer_colors[layer] for node in mlg.nodes[layer]}
    
    return colors


def _get_edge_colors(
    mlg: MultilayerGraph,
    edge_color_by: Union[str, Callable]
) -> Tuple[str, str]:
    """
    Get edge colors for intra and inter-layer edges.
    
    Args:
        mlg: MultilayerGraph structure
        edge_color_by: Coloring strategy ("type" or callable)
        
    Returns:
        Tuple of (intra_color, inter_color)
    """
    if edge_color_by == "type":
        # Default colors for edge types
        return '#333333', '#888888'  # intra: dark gray, inter: light gray
    elif callable(edge_color_by):
        # Callable returns colors for each edge
        # For simplicity, we use default here and let caller handle per-edge coloring
        return '#333333', '#888888'
    else:
        return '#333333', '#888888'


def draw_multilayer_pymnet(
    ml_graph: Any,
    *,
    layer_order: Optional[List[str]] = None,
    node_order: Optional[List[Any]] = None,
    layout: Union[str, Callable] = "spring",
    seed: int = 42,
    layer_gap: float = 2.5,
    node_size: float = 80,
    node_alpha: float = 0.9,
    intra_edge_alpha: float = 0.25,
    inter_edge_alpha: float = 0.15,
    intra_edge_width: float = 0.8,
    inter_edge_width: float = 0.6,
    show_node_labels: bool = False,
    show_layer_labels: bool = True,
    node_color_by: Union[str, Callable] = "layer",
    edge_color_by: Union[str, Callable] = "type",
    ax: Optional[plt.Axes] = None,
    figsize: Tuple[float, float] = (10, 6),
) -> Tuple[plt.Figure, plt.Axes, Dict[str, Any], Dict[Any, Tuple[float, float]]]:
    """
    Draw a pymnet style multilayer network visualization.
    
    This function creates a visualization inspired by the pymnet library, with
    layers stacked along a vertical axis and nodes positioned consistently across
    layers using a shared 2D layout.
    
    Reference:
        Pymnet: https://github.com/bolozna/Multilayer-networks-library
        Kivelä et al. (2014). Multilayer networks. Journal of complex networks.
    
    Args:
        ml_graph: Input multilayer graph in one of the supported formats:
            - MultilayerGraph
            - dict[str, nx.Graph]: layer name -> NetworkX graph
            - nx.Graph with 'layer' node attribute
            - Edge list: [(u, layer_u, v, layer_v), ...]
            - py3plex multi_layer_network
        layer_order: Optional explicit ordering of layers (default: sorted alphabetically)
        node_order: Optional explicit ordering of nodes (default: automatic)
        layout: Layout algorithm name or callable function:
            - "spring": Force-directed layout (default)
            - "kamada_kawai": Kamada-Kawai layout
            - "circular": Circular layout
            - "spectral": Spectral layout
            - Callable: Custom function (graph) -> dict[node, (x, y)]
        seed: Random seed for deterministic layouts (default: 42)
        layer_gap: Vertical spacing between layers (default: 2.5)
        node_size: Size of nodes in points^2 (default: 80)
        node_alpha: Node opacity (default: 0.9)
        intra_edge_alpha: Intra-layer edge opacity (default: 0.25)
        inter_edge_alpha: Inter-layer edge opacity (default: 0.15)
        intra_edge_width: Intra-layer edge width (default: 0.8)
        inter_edge_width: Inter-layer edge width (default: 0.6)
        show_node_labels: Whether to show node labels (default: False)
        show_layer_labels: Whether to show layer labels (default: True)
        node_color_by: Node coloring strategy:
            - "layer": Color by layer (default)
            - "degree": Color by degree
            - "community": Color by community (not implemented)
            - Callable: Custom function (node, layer) -> color
        edge_color_by: Edge coloring strategy:
            - "type": Color by edge type (intra vs inter)
            - Callable: Custom function (edge) -> color
        ax: Optional Matplotlib Axes to draw on (default: create new)
        figsize: Figure size as (width, height) in inches (default: (10, 6))
        
    Returns:
        Tuple of (fig, ax, artist_handles, positions):
            - fig: Matplotlib Figure
            - ax: Matplotlib Axes
            - artist_handles: Dict of artist handles for legend/manipulation
            - positions: Dict of final 3D positions for all nodes
            
    Raises:
        VisualizationError: If visualization fails
        Py3plexFormatError: If input format is invalid
        
    Example:
        >>> from py3plex.core import multinet
        >>> from py3plex.visualization.pymnet_style import draw_multilayer_pymnet
        >>> 
        >>> # Create multilayer network
        >>> net = multinet.multi_layer_network(directed=False)
        >>> net.add_nodes([{'source': 'A', 'type': 'layer1'}], input_type='dict')
        >>> net.add_nodes([{'source': 'A', 'type': 'layer2'}], input_type='dict')
        >>> net.add_edges([
        ...     {'source': 'A', 'target': 'B', 'source_type': 'layer1', 'target_type': 'layer1'}
        ... ], input_type='dict')
        >>> 
        >>> # Draw with pymnet style
        >>> fig, ax, handles, pos = draw_multilayer_pymnet(
        ...     net,
        ...     layout="spring",
        ...     seed=42,
        ...     layer_gap=2.0,
        ...     show_layer_labels=True
        ... )
        >>> fig.savefig("pymnet_visualization.png", dpi=150, bbox_inches='tight')
        >>> fig.savefig("pymnet_visualization.svg", bbox_inches='tight')
    """
    # Convert to MultilayerGraph
    mlg = to_multilayer_graph(ml_graph)
    
    # Apply layer ordering
    if layer_order is not None:
        # Validate layer order
        if set(layer_order) != set(mlg.layers):
            raise VisualizationError(
                f"layer_order does not match available layers",
                suggestions=[f"Available layers: {', '.join(mlg.layers)}"]
            )
        mlg.layers = layer_order
    
    # Compute 2D layout on aggregated graph
    base_positions = _compute_layout(mlg, layout, seed)
    
    # Get node colors
    node_colors = _get_node_colors(mlg, node_color_by, base_positions)
    
    # Get edge colors
    intra_color, inter_color = _get_edge_colors(mlg, edge_color_by)
    
    # Create figure and axes if not provided
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
    else:
        fig = ax.figure
    
    # Track artist handles and final positions
    artist_handles = {
        'nodes': {},
        'intra_edges': {},
        'inter_edges': [],
        'labels': {}
    }
    final_positions = {}
    
    # Draw each layer
    for layer_idx, layer in enumerate(mlg.layers):
        layer_y_offset = layer_idx * layer_gap
        
        # Draw intra-layer edges
        for u, v in mlg.intra_edges[layer]:
            if u in base_positions and v in base_positions:
                x_coords = [base_positions[u][0], base_positions[v][0]]
                y_coords = [base_positions[u][1] + layer_y_offset, 
                           base_positions[v][1] + layer_y_offset]
                
                line = ax.plot(x_coords, y_coords,
                              color=intra_color,
                              alpha=intra_edge_alpha,
                              linewidth=intra_edge_width,
                              zorder=1)[0]
                
                if layer not in artist_handles['intra_edges']:
                    artist_handles['intra_edges'][layer] = []
                artist_handles['intra_edges'][layer].append(line)
        
        # Draw nodes
        for node in mlg.nodes[layer]:
            if node in base_positions:
                x, y = base_positions[node]
                y_final = y + layer_y_offset
                
                color = node_colors[layer].get(node, '#1f77b4')
                
                scatter = ax.scatter([x], [y_final],
                                   s=node_size,
                                   c=[color],
                                   alpha=node_alpha,
                                   zorder=3,
                                   edgecolors='white',
                                   linewidths=0.5)
                
                if layer not in artist_handles['nodes']:
                    artist_handles['nodes'][layer] = []
                artist_handles['nodes'][layer].append(scatter)
                
                # Store final position
                final_positions[(node, layer)] = (x, y_final)
                
                # Add node labels if requested
                if show_node_labels:
                    text = ax.text(x, y_final, str(node),
                                 fontsize=8,
                                 ha='center',
                                 va='center',
                                 zorder=4)
                    if layer not in artist_handles['labels']:
                        artist_handles['labels'][layer] = []
                    artist_handles['labels'][layer].append(text)
        
        # Add layer label if requested
        if show_layer_labels and len(base_positions) > 0:
            # Position label to the left of the layer
            x_min = min(pos[0] for pos in base_positions.values())
            label_text = ax.text(x_min - 0.5, layer_y_offset,
                               layer,
                               fontsize=12,
                               ha='right',
                               va='center',
                               fontweight='bold',
                               zorder=5)
            if 'layer_labels' not in artist_handles:
                artist_handles['layer_labels'] = []
            artist_handles['layer_labels'].append(label_text)
    
    # Draw inter-layer edges
    for u, layer_u, v, layer_v in mlg.inter_edges:
        if u in base_positions and v in base_positions:
            u_layer_idx = mlg.layers.index(layer_u)
            v_layer_idx = mlg.layers.index(layer_v)
            
            x_coords = [base_positions[u][0], base_positions[v][0]]
            y_coords = [base_positions[u][1] + u_layer_idx * layer_gap,
                       base_positions[v][1] + v_layer_idx * layer_gap]
            
            line = ax.plot(x_coords, y_coords,
                          color=inter_color,
                          alpha=inter_edge_alpha,
                          linewidth=inter_edge_width,
                          linestyle='--',
                          zorder=2)[0]
            
            artist_handles['inter_edges'].append(line)
    
    # Set axis properties
    ax.set_aspect('equal')
    ax.axis('off')
    
    # Auto-scale to fit content with padding
    if len(base_positions) > 0:
        x_coords = [pos[0] for pos in base_positions.values()]
        y_min = 0 - 0.5
        y_max = (len(mlg.layers) - 1) * layer_gap + 0.5
        x_min = min(x_coords) - 0.5
        x_max = max(x_coords) + 0.5
        
        ax.set_xlim(x_min, x_max)
        ax.set_ylim(y_min, y_max)
    
    fig.tight_layout()
    
    return fig, ax, artist_handles, final_positions


# Convenience aliases for backend identification
BACKEND_NAME = "pymnet"
STYLE_NAME = "pymnet"
