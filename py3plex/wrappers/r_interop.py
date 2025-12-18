"""
R interoperability module for py3plex.

This module provides R-friendly functions for working with py3plex multilayer
networks via the reticulate package. It enables seamless integration between
py3plex (Python) and R packages like igraph and MLnet.

Key Features:
    - Convert py3plex graphs to igraph format (compatible with R's igraph)
    - Export graph data structures in R-friendly formats
    - Simplified API optimized for reticulate usage
    - Support for both directed and undirected multilayer networks

R Usage Example (via reticulate):
    ```R
    library(reticulate)
    library(igraph)

    # Import py3plex
    py3plex <- import("py3plex")
    r_interop <- import("py3plex.wrappers.r_interop")

    # Create a multilayer network in Python
    net <- py3plex$multi_layer_network()
    net$add_nodes(list(list(source='A', type='layer1')))
    net$add_edges(list(list(source='A', target='B',
                             source_type='layer1', target_type='layer1')))

    # Convert to igraph for R
    g <- r_interop$to_igraph_for_r(net, mode='union')

    # Now use R's igraph functions
    degree(g)
    plot(g)
    ```

Alternative Export Formats:
    ```R
    # Export as edge list
    edges <- r_interop$export_edgelist(net)

    # Export as adjacency matrix
    adj <- r_interop$export_adjacency(net)

    # Export comprehensive graph data
    graph_data <- r_interop$export_graph_data(net)
    ```
"""

from typing import Any, Dict, List, Literal, Optional, Union

import networkx as nx

from py3plex.core.multinet import multi_layer_network
from py3plex.exceptions import ConversionError

# Try to import optional dependencies
try:
    from py3plex.io import MultiLayerGraph, to_igraph

    NEW_IO_AVAILABLE = True
except ImportError:
    NEW_IO_AVAILABLE = False

try:
    import igraph as ig  # noqa: F401

    IGRAPH_AVAILABLE = True
except ImportError:
    IGRAPH_AVAILABLE = False

# Type aliases for clarity
ProjectionMode = Literal["union", "intersection", "multiplex"]


def to_igraph_for_r(
    network: Union[multi_layer_network, Any],
    mode: ProjectionMode = "union",
    layer: Optional[str] = None,
) -> Any:
    """
    Convert py3plex network to igraph format optimized for R usage.

    This function is specifically designed for R users accessing py3plex
    via reticulate. It handles the conversion from py3plex's internal
    representation to igraph, which can then be used with R's igraph package.

    Args:
        network: py3plex multi_layer_network or MultiLayerGraph instance
        mode: How to handle multiple layers:
            - "union": Merge all layers into a single graph (recommended for R)
            - "intersection": Keep only edges present in all layers
            - "multiplex": Preserve layer structure (advanced usage)
        layer: Optional specific layer to extract. If specified, only this
               layer is converted. Overrides mode parameter.

    Returns:
        igraph.Graph instance compatible with R's igraph package

    Raises:
        ImportError: If igraph is not installed
        ConversionError: If conversion fails

    R Usage Example:
        ```R
        library(reticulate)
        library(igraph)

        # Import and create network
        py3plex <- import("py3plex")
        r_interop <- import("py3plex.wrappers.r_interop")

        net <- py3plex$multi_layer_network()
        # ... add nodes and edges ...

        # Convert to igraph (union mode - simplest)
        g <- r_interop$to_igraph_for_r(net, mode='union')

        # Use R igraph functions
        V(g)  # Vertices
        E(g)  # Edges
        degree(g)  # Degree distribution
        plot(g)  # Visualization
        ```

    Note:
        For most R users, 'union' mode is recommended as it creates a standard
        igraph object that works with all R igraph functions. The 'multiplex'
        mode preserves full multilayer structure but creates a more complex
        object with tuple-based vertex names.
    """
    if not IGRAPH_AVAILABLE:
        raise ImportError(
            "python-igraph is required for R interop. "
            "Install with: pip install python-igraph"
        )

    # Handle layer-specific extraction
    if layer is not None:
        return _extract_layer_to_igraph(network, layer)

    # Handle new I/O system (MultiLayerGraph)
    if NEW_IO_AVAILABLE and hasattr(network, "__class__"):
        if network.__class__.__name__ == "MultiLayerGraph":
            return to_igraph(network, mode=mode)

    # Handle legacy multi_layer_network
    if isinstance(network, multi_layer_network):
        # Convert to NetworkX first, then to igraph
        nx_graph = network.core_network

        if nx_graph is None:
            # Handle empty network - create empty igraph
            import igraph as ig

            return ig.Graph(directed=False)

        # Use NetworkX to igraph conversion
        if not isinstance(
            nx_graph, (nx.Graph, nx.DiGraph, nx.MultiGraph, nx.MultiDiGraph)
        ):
            raise ConversionError(
                f"core_network must be a NetworkX graph, got {type(nx_graph)}"
            )

        # Convert NetworkX to igraph using NetworkX's built-in method
        # This is the most reliable approach for legacy networks
        try:
            import igraph as ig

            # Get basic structure
            if nx_graph.is_directed():
                g = ig.Graph(directed=True)
            else:
                g = ig.Graph(directed=False)

            # Add vertices
            node_to_idx = {}
            for idx, node in enumerate(nx_graph.nodes()):
                g.add_vertex(name=str(node))
                node_to_idx[node] = idx
                # Add node attributes
                for attr, value in nx_graph.nodes[node].items():
                    if attr not in g.vs[idx].attributes():
                        try:
                            g.vs[idx][attr] = value
                        except (TypeError, ValueError):
                            # Skip non-serializable attributes
                            pass

            # Add edges
            edge_list = []
            for src, dst in nx_graph.edges():
                edge_list.append((node_to_idx[src], node_to_idx[dst]))

            g.add_edges(edge_list)

            # Add edge attributes if available
            edge_idx = 0
            for src, dst, data in nx_graph.edges(data=True):
                for attr, value in data.items():
                    try:
                        g.es[edge_idx][attr] = value
                    except (TypeError, ValueError):
                        # Skip non-serializable attributes
                        pass
                edge_idx += 1

            return g

        except Exception as e:
            raise ConversionError(f"Failed to convert network to igraph: {e}")

    raise ConversionError(
        f"Unsupported network type: {type(network)}. "
        "Expected multi_layer_network or MultiLayerGraph."
    )


def _extract_layer_to_igraph(
    network: Union[multi_layer_network, Any], layer: str
) -> Any:
    """
    Extract a specific layer and convert to igraph.

    Args:
        network: py3plex network
        layer: Layer identifier to extract

    Returns:
        igraph.Graph of the specified layer
    """
    if not IGRAPH_AVAILABLE:
        raise ImportError("python-igraph is required")

    import igraph as ig

    # For legacy networks
    if isinstance(network, multi_layer_network):
        # Get subgraph for specific layer
        nx_graph = network.core_network
        if nx_graph is None:
            raise ConversionError("Network has no core_network")

        # Filter edges belonging to the layer
        layer_edges = []
        for src, dst, data in nx_graph.edges(data=True):
            # Check if edge belongs to the specified layer
            src_type = data.get("source_type", data.get("src_layer", None))
            dst_type = data.get("target_type", data.get("dst_layer", None))
            if src_type == layer and dst_type == layer:
                layer_edges.append((src, dst, data))

        # Create subgraph
        layer_graph = nx.MultiDiGraph() if nx_graph.is_directed() else nx.MultiGraph()
        for src, dst, data in layer_edges:
            layer_graph.add_edge(src, dst, **data)

        # Convert to igraph
        g = ig.Graph(directed=layer_graph.is_directed())
        node_to_idx = {}
        for idx, node in enumerate(layer_graph.nodes()):
            g.add_vertex(name=str(node))
            node_to_idx[node] = idx

        edge_list = [
            (node_to_idx[src], node_to_idx[dst]) for src, dst in layer_graph.edges()
        ]
        g.add_edges(edge_list)

        return g

    # For new I/O system
    if NEW_IO_AVAILABLE and hasattr(network, "layers"):
        if layer not in network.layers:
            raise ConversionError(f"Layer '{layer}' not found in network")

        # Create filtered graph with only edges from specified layer
        filtered = MultiLayerGraph(directed=network.directed)
        filtered.add_layer(network.layers[layer])

        # Add all nodes
        for node_id, node in network.nodes.items():
            filtered.add_node(node)

        # Add only edges from specified layer
        for edge in network.edges:
            if edge.src_layer == layer and edge.dst_layer == layer:
                filtered.add_edge(edge)

        return to_igraph(filtered, mode="union")

    raise ConversionError(f"Cannot extract layer from {type(network)}")


def export_edgelist(
    network: Union[multi_layer_network, Any],
    include_attributes: bool = True,
) -> List[Dict[str, Any]]:
    """
    Export network as edge list in R-friendly format.

    Returns a list of dictionaries representing edges, which can be easily
    converted to an R data frame via reticulate.

    Args:
        network: py3plex network
        include_attributes: Whether to include edge attributes

    Returns:
        List of edge dictionaries with keys: src, dst, src_layer, dst_layer,
        and optionally edge attributes

    R Usage Example:
        ```R
        library(reticulate)

        r_interop <- import("py3plex.wrappers.r_interop")

        # Get edge list
        edges <- r_interop$export_edgelist(net)

        # Convert to R data frame
        df <- as.data.frame(do.call(rbind, lapply(edges, as.data.frame)))

        # Now use R data manipulation
        head(df)
        summary(df)
        ```
    """
    edges = []

    # Handle new I/O system
    if NEW_IO_AVAILABLE and hasattr(network, "edges"):
        if hasattr(network.edges, "__iter__"):
            for edge in network.edges:
                edge_dict = {
                    "src": edge.src,
                    "dst": edge.dst,
                    "src_layer": edge.src_layer,
                    "dst_layer": edge.dst_layer,
                }
                if include_attributes:
                    edge_dict.update(edge.attributes)
                edges.append(edge_dict)
            return edges

    # Handle legacy network
    if isinstance(network, multi_layer_network):
        nx_graph = network.core_network
        if nx_graph is None:
            return []

        for src, dst, data in nx_graph.edges(data=True):
            # Derive layer information from edge attributes when present,
            # otherwise fall back to the layer encoded in the node tuple.
            src_layer = data.get("source_type", data.get("src_layer"))
            if src_layer is None and isinstance(src, tuple) and len(src) >= 2:
                src_layer = src[1]
            if src_layer is None:
                src_layer = "default"

            dst_layer = data.get("target_type", data.get("dst_layer"))
            if dst_layer is None and isinstance(dst, tuple) and len(dst) >= 2:
                dst_layer = dst[1]
            if dst_layer is None:
                dst_layer = "default"

            edge_dict = {
                "src": src,
                "dst": dst,
                "src_layer": src_layer,
                "dst_layer": dst_layer,
            }
            if include_attributes:
                # Add other attributes
                for key, value in data.items():
                    if key not in {
                        "source_type",
                        "target_type",
                        "src_layer",
                        "dst_layer",
                    }:
                        edge_dict[key] = value
            edges.append(edge_dict)

    return edges


def export_nodelist(
    network: Union[multi_layer_network, Any],
    include_attributes: bool = True,
) -> List[Dict[str, Any]]:
    """
    Export network nodes as list in R-friendly format.

    Returns a list of dictionaries representing nodes, which can be easily
    converted to an R data frame via reticulate.

    Args:
        network: py3plex network
        include_attributes: Whether to include node attributes

    Returns:
        List of node dictionaries with keys: id and optionally node attributes

    R Usage Example:
        ```R
        library(reticulate)

        r_interop <- import("py3plex.wrappers.r_interop")

        # Get node list
        nodes <- r_interop$export_nodelist(net)

        # Convert to R data frame
        df <- as.data.frame(do.call(rbind, lapply(nodes, as.data.frame)))
        ```
    """
    nodes = []

    # Handle new I/O system
    if NEW_IO_AVAILABLE and hasattr(network, "nodes"):
        if hasattr(network.nodes, "items"):
            for node_id, node in network.nodes.items():
                node_dict = {"id": node_id}
                if include_attributes and hasattr(node, "attributes"):
                    node_dict.update(node.attributes)
                nodes.append(node_dict)
            return nodes

    # Handle legacy network
    if isinstance(network, multi_layer_network):
        nx_graph = network.core_network
        if nx_graph is None:
            return []

        for node, data in nx_graph.nodes(data=True):
            node_dict = {"id": node}
            if include_attributes:
                node_dict.update(data)
            nodes.append(node_dict)

    return nodes


def export_graph_data(network: Union[multi_layer_network, Any]) -> Dict[str, Any]:
    """
    Export complete graph data in R-friendly format.

    Returns a dictionary containing nodes, edges, layers, and metadata
    that can be easily used in R via reticulate.

    Args:
        network: py3plex network

    Returns:
        Dictionary with keys: nodes, edges, layers, directed, attributes

    R Usage Example:
        ```R
        library(reticulate)

        r_interop <- import("py3plex.wrappers.r_interop")

        # Get complete graph data
        graph_data <- r_interop$export_graph_data(net)

        # Access components
        nodes <- as.data.frame(do.call(rbind, lapply(graph_data$nodes, as.data.frame)))
        edges <- as.data.frame(do.call(rbind, lapply(graph_data$edges, as.data.frame)))
        layers <- graph_data$layers
        is_directed <- graph_data$directed
        ```
    """
    result = {
        "nodes": export_nodelist(network, include_attributes=True),
        "edges": export_edgelist(network, include_attributes=True),
        "layers": [],
        "directed": False,
        "attributes": {},
    }

    # Handle new I/O system
    if NEW_IO_AVAILABLE and hasattr(network, "layers"):
        result["layers"] = list(network.layers.keys())
        result["directed"] = network.directed
        if hasattr(network, "attributes"):
            result["attributes"] = network.attributes

    # Handle legacy network
    elif isinstance(network, multi_layer_network):
        if hasattr(network, "layers"):
            result["layers"] = list(network.layers)
        if network.core_network is not None:
            result["directed"] = network.core_network.is_directed()

    return result


def export_adjacency(
    network: Union[multi_layer_network, Any],
    layer: Optional[str] = None,
    mode: ProjectionMode = "union",
) -> List[List[float]]:
    """
    Export adjacency matrix in R-friendly format.

    Returns a 2D list (nested lists) that can be converted to an R matrix.

    Args:
        network: py3plex network
        layer: Optional specific layer to export
        mode: How to handle multiple layers (same as to_igraph_for_r)

    Returns:
        2D list representing adjacency matrix

    R Usage Example:
        ```R
        library(reticulate)

        r_interop <- import("py3plex.wrappers.r_interop")

        # Get adjacency matrix
        adj_list <- r_interop$export_adjacency(net)

        # Convert to R matrix
        adj_matrix <- matrix(unlist(adj_list),
                             nrow=length(adj_list),
                             byrow=TRUE)

        # Use in R
        eigen(adj_matrix)
        ```
    """
    # Convert to igraph first
    g = to_igraph_for_r(network, mode=mode, layer=layer)

    # Get adjacency matrix from igraph
    adj_matrix = g.get_adjacency()

    # Convert to nested list (R-friendly format)
    n = g.vcount()
    result = []
    for i in range(n):
        row = []
        for j in range(n):
            row.append(float(adj_matrix[i, j]))
        result.append(row)

    return result


def get_layer_names(network: Union[multi_layer_network, Any]) -> List[str]:
    """
    Get list of layer names in the network.

    Args:
        network: py3plex network

    Returns:
        List of layer names/identifiers

    R Usage Example:
        ```R
        r_interop <- import("py3plex.wrappers.r_interop")
        layers <- r_interop$get_layer_names(net)
        print(layers)
        ```
    """
    # Handle new I/O system
    if NEW_IO_AVAILABLE and hasattr(network, "layers"):
        try:
            return list(network.layers.keys())
        except AttributeError:
            return list(network.layers)

    # Handle legacy network
    if isinstance(network, multi_layer_network):
        if hasattr(network, "layers"):
            return list(network.layers)

    return []


def get_network_stats(network: Union[multi_layer_network, Any]) -> Dict[str, Any]:
    """
    Get basic network statistics in R-friendly format.

    Args:
        network: py3plex network

    Returns:
        Dictionary with keys: num_nodes, num_edges, num_layers, directed,
        and per-layer statistics if available

    R Usage Example:
        ```R
        r_interop <- import("py3plex.wrappers.r_interop")
        stats <- r_interop$get_network_stats(net)
        print(stats$num_nodes)
        print(stats$num_edges)
        ```
    """
    stats = {
        "num_nodes": 0,
        "num_edges": 0,
        "num_layers": 0,
        "directed": False,
        "layer_stats": {},
    }

    # Handle new I/O system
    if NEW_IO_AVAILABLE and hasattr(network, "nodes"):
        stats["num_nodes"] = len(network.nodes)
        stats["num_edges"] = len(network.edges)
        stats["num_layers"] = len(network.layers)
        stats["directed"] = network.directed

        # Per-layer statistics
        for layer_id in network.layers:
            layer_edges = [
                e
                for e in network.edges
                if e.src_layer == layer_id and e.dst_layer == layer_id
            ]
            stats["layer_stats"][layer_id] = {
                "num_edges": len(layer_edges),
            }

    # Handle legacy network
    elif isinstance(network, multi_layer_network):
        if network.core_network is not None:
            stats["num_nodes"] = network.core_network.number_of_nodes()
            stats["num_edges"] = network.core_network.number_of_edges()
            stats["directed"] = network.core_network.is_directed()
        if hasattr(network, "layers"):
            stats["num_layers"] = len(network.layers)

    return stats


# Convenience aliases for R users
to_r_igraph = to_igraph_for_r  # Shorter alias
