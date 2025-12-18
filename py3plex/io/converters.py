"""
Library converters for multilayer graphs.

Provides bidirectional conversion between MultiLayerGraph and popular graph libraries:
- NetworkX (multiplex projection modes: union, intersection, multiplex)
- igraph (with attribute preservation)
- graph-tool (using property maps)
"""

from typing import Any, Dict, Literal

from py3plex.exceptions import ConversionError

from .schema import Edge, Layer, MultiLayerGraph, Node

# Optional formal verification support
try:
    from icontract import ensure, require

    ICONTRACT_AVAILABLE = True
except ImportError:
    # Create no-op decorators when icontract is not available
    def require(*args, **kwargs):
        def decorator(func):
            return func

        return decorator

    def ensure(*args, **kwargs):
        def decorator(func):
            return func

        return decorator

    ICONTRACT_AVAILABLE = False

# Type hints for projection modes
ProjectionMode = Literal["union", "intersection", "multiplex"]


@require(lambda graph: graph is not None, "graph must not be None")
@require(
    lambda graph: isinstance(graph, MultiLayerGraph), "graph must be a MultiLayerGraph"
)
@require(
    lambda mode: mode in ("union", "intersection", "multiplex"),
    "mode must be 'union', 'intersection', or 'multiplex'",
)
@ensure(lambda result: result is not None, "result must not be None")
def to_networkx(
    graph: MultiLayerGraph,
    mode: ProjectionMode = "union",
) -> Any:
    """
    Convert MultiLayerGraph to NetworkX graph.

    Args:
        graph: MultiLayerGraph to convert
        mode: Projection mode for handling multilayer structure:
            - "union": Merge all layers into single graph (node ID only)
            - "intersection": Keep only edges present in ALL layers
            - "multiplex": Preserve layer info as (node, layer) tuples

    Returns:
        NetworkX graph (MultiGraph or MultiDiGraph)

    Raises:
        ImportError: If NetworkX is not installed

    Contracts:
        - Precondition: graph must not be None and must be a MultiLayerGraph
        - Precondition: mode must be a valid projection mode
        - Postcondition: returns a non-None NetworkX graph
    """
    try:
        import networkx as nx
    except ImportError:
        raise ImportError(
            "NetworkX is required for to_networkx(). Install with: pip install networkx"
        )

    # Create appropriate NetworkX graph type
    if graph.directed:
        G = nx.MultiDiGraph()
    else:
        G = nx.MultiGraph()

    # Add graph attributes
    G.graph.update(graph.attributes)

    def _pair_signature(src: Any, dst: Any) -> tuple:
        if graph.directed:
            return (src, dst)
        # For undirected graphs, normalize the signature to avoid losing edges when
        # the same undirected edge is represented as (u, v) vs (v, u).
        return tuple(sorted((src, dst), key=str))

    if mode == "union":
        # Merge all layers - use only node IDs
        # Add nodes with merged attributes
        for node_id, node in graph.nodes.items():
            G.add_node(node_id, **node.attributes)

        # Add edges, merging from all layers
        edge_counts: Dict[tuple, int] = {}  # Track parallel edges
        for edge in graph.edges:
            # Create edge key for tracking parallel edges
            edge_key = _pair_signature(edge.src, edge.dst)
            key = edge_counts.get(edge_key, 0)
            edge_counts[edge_key] = key + 1

            # Add layer info to edge attributes
            attrs = edge.attributes.copy()
            attrs["src_layer"] = edge.src_layer
            attrs["dst_layer"] = edge.dst_layer

            G.add_edge(edge.src, edge.dst, key=key, **attrs)

    elif mode == "intersection":
        # Keep only edges that exist in ALL layers
        # First, identify edges that appear in all layers
        layer_ids = set(graph.layers.keys())
        edge_signatures: Dict[tuple, set] = {}  # (src, dst) -> set of layers

        for edge in graph.edges:
            # Only consider intra-layer edges for intersection
            if edge.src_layer == edge.dst_layer:
                sig = _pair_signature(edge.src, edge.dst)
                if sig not in edge_signatures:
                    edge_signatures[sig] = set()
                edge_signatures[sig].add(edge.src_layer)

        # Find edges in all layers
        common_edges = {
            sig for sig, layers in edge_signatures.items() if layers == layer_ids
        }

        # Add nodes
        for node_id, node in graph.nodes.items():
            G.add_node(node_id, **node.attributes)

        # Add only common edges (one representative edge per undirected/directed pair)
        added = set()
        for edge in graph.edges:
            if edge.src_layer == edge.dst_layer:  # Only intra-layer
                sig = _pair_signature(edge.src, edge.dst)
                if sig in common_edges and sig not in added:
                    attrs = edge.attributes.copy()
                    G.add_edge(edge.src, edge.dst, key=edge.key, **attrs)
                    added.add(sig)

    elif mode == "multiplex":
        # Preserve full multilayer structure using (node, layer) tuples
        # Add nodes as (node_id, layer_id) tuples
        for node_id, node in graph.nodes.items():
            for layer_id, layer in graph.layers.items():
                node_tuple = (node_id, layer_id)
                attrs = node.attributes.copy()
                attrs["layer"] = layer_id
                attrs["layer_attrs"] = layer.attributes
                G.add_node(node_tuple, **attrs)

        # Add edges between (node, layer) tuples
        for edge in graph.edges:
            src_tuple = (edge.src, edge.src_layer)
            dst_tuple = (edge.dst, edge.dst_layer)
            G.add_edge(src_tuple, dst_tuple, key=edge.key, **edge.attributes)

    else:
        raise ConversionError(
            f"Unknown mode: '{mode}'. Must be 'union', 'intersection', or 'multiplex'. "
            f"Use 'union' to merge all layers, 'intersection' for common edges, "
            f"or 'multiplex' to preserve layer information in node tuples."
        )

    return G


@require(lambda G: G is not None, "G must not be None")
@require(
    lambda mode: mode in ("union", "multiplex"), "mode must be 'union' or 'multiplex'"
)
@require(
    lambda default_layer: isinstance(default_layer, str),
    "default_layer must be a string",
)
@require(
    lambda default_layer: len(default_layer) > 0, "default_layer must not be empty"
)
@ensure(lambda result: result is not None, "result must not be None")
@ensure(
    lambda result: isinstance(result, MultiLayerGraph),
    "result must be a MultiLayerGraph",
)
def from_networkx(
    G: Any,
    mode: ProjectionMode = "multiplex",
    default_layer: str = "default",
) -> MultiLayerGraph:
    """
    Convert NetworkX graph to MultiLayerGraph.

    Args:
        G: NetworkX graph
        mode: Interpretation mode:
            - "union": All nodes/edges go to a single default layer
            - "multiplex": Expect (node, layer) tuples as node IDs
            - "intersection": Not supported for conversion (ambiguous)
        default_layer: Layer ID to use for "union" mode

    Returns:
        MultiLayerGraph instance

    Raises:
        ImportError: If NetworkX is not installed
        ValueError: If mode is invalid or graph structure is incompatible

    Contracts:
        - Precondition: G must not be None
        - Precondition: mode must be 'union' or 'multiplex'
        - Precondition: default_layer must be a non-empty string
        - Postcondition: returns a MultiLayerGraph
    """
    try:
        import networkx as nx
    except ImportError:
        raise ImportError(
            "NetworkX is required for from_networkx(). Install with: pip install networkx"
        )

    # Create empty graph
    graph = MultiLayerGraph(directed=G.is_directed())

    # Copy graph attributes
    if hasattr(G, "graph"):
        graph.attributes.update(G.graph)

    if mode == "union":
        # Single layer interpretation
        graph.add_layer(Layer(id=default_layer))

        # Add all nodes
        for node_id, attrs in G.nodes(data=True):
            graph.add_node(Node(id=node_id, attributes=dict(attrs)))

        # Add all edges
        if isinstance(G, (nx.MultiGraph, nx.MultiDiGraph)):
            for src, dst, key, attrs in G.edges(keys=True, data=True):
                edge = Edge(
                    src=src,
                    dst=dst,
                    src_layer=default_layer,
                    dst_layer=default_layer,
                    key=key,
                    attributes=dict(attrs),
                )
                graph.add_edge(edge)
        else:
            for src, dst, attrs in G.edges(data=True):
                edge = Edge(
                    src=src,
                    dst=dst,
                    src_layer=default_layer,
                    dst_layer=default_layer,
                    attributes=dict(attrs),
                )
                graph.add_edge(edge)

    elif mode == "multiplex":
        # Expect (node, layer) tuples
        # First pass: collect layers and nodes
        layers_seen = set()
        nodes_seen = set()

        for node_tuple in G.nodes():
            if not isinstance(node_tuple, tuple) or len(node_tuple) != 2:
                raise ConversionError(
                    f"In 'multiplex' mode, node IDs must be (node_id, layer_id) tuples. "
                    f"Got: {node_tuple}. Please ensure your NetworkX graph uses proper node tuples."
                )
            node_id, layer_id = node_tuple
            nodes_seen.add(node_id)
            layers_seen.add(layer_id)

        # Add layers
        for layer_id in layers_seen:
            graph.add_layer(Layer(id=layer_id))

        # Add nodes
        for node_id in nodes_seen:
            # Get attributes from first occurrence (merge across layers if needed)
            attrs = {}
            for node_tuple in G.nodes():
                if node_tuple[0] == node_id:
                    node_attrs = G.nodes[node_tuple]
                    # Extract non-layer attributes
                    attrs = {
                        k: v
                        for k, v in node_attrs.items()
                        if k not in {"layer", "layer_attrs"}
                    }
                    break
            graph.add_node(Node(id=node_id, attributes=attrs))

        # Add edges
        if isinstance(G, (nx.MultiGraph, nx.MultiDiGraph)):
            for src_tuple, dst_tuple, key, attrs in G.edges(keys=True, data=True):
                src_id, src_layer = src_tuple
                dst_id, dst_layer = dst_tuple
                edge = Edge(
                    src=src_id,
                    dst=dst_id,
                    src_layer=src_layer,
                    dst_layer=dst_layer,
                    key=key,
                    attributes=dict(attrs),
                )
                graph.add_edge(edge)
        else:
            for src_tuple, dst_tuple, attrs in G.edges(data=True):
                src_id, src_layer = src_tuple
                dst_id, dst_layer = dst_tuple
                edge = Edge(
                    src=src_id,
                    dst=dst_id,
                    src_layer=src_layer,
                    dst_layer=dst_layer,
                    attributes=dict(attrs),
                )
                graph.add_edge(edge)

    elif mode == "intersection":
        raise ConversionError(
            "Mode 'intersection' is not supported for from_networkx() conversion - it's ambiguous. "
            "Please use 'union' to merge all edges or 'multiplex' to create layer-specific nodes."
        )

    else:
        raise ConversionError(
            f"Unknown mode: '{mode}'. Must be 'union' or 'multiplex'. "
            f"Use 'union' to treat the graph as a single layer, "
            f"or 'multiplex' to infer layers from node attributes."
        )

    return graph


@require(lambda graph: graph is not None, "graph must not be None")
@require(
    lambda graph: isinstance(graph, MultiLayerGraph), "graph must be a MultiLayerGraph"
)
@require(
    lambda mode: mode in ("union", "intersection", "multiplex"),
    "mode must be 'union', 'intersection', or 'multiplex'",
)
@ensure(lambda result: result is not None, "result must not be None")
def to_igraph(graph: MultiLayerGraph, mode: ProjectionMode = "multiplex") -> Any:
    """
    Convert MultiLayerGraph to igraph graph.

    Args:
        graph: MultiLayerGraph to convert
        mode: Projection mode (same as to_networkx)

    Returns:
        igraph.Graph instance

    Raises:
        ImportError: If igraph is not installed

    Contracts:
        - Precondition: graph must not be None and must be a MultiLayerGraph
        - Precondition: mode must be a valid projection mode
        - Postcondition: returns a non-None igraph graph
    """
    try:
        import igraph as ig
    except ImportError:
        raise ImportError(
            "igraph is required for to_igraph(). Install with: pip install python-igraph"
        )

    # Create igraph graph
    g = ig.Graph(directed=graph.directed)

    if mode == "multiplex":
        # Create vertex name mapping
        vertex_map: Dict[tuple, int] = {}  # (node_id, layer_id) -> vertex_index

        # Add vertices for each (node, layer) combination
        for node_id, node in graph.nodes.items():
            for layer_id in graph.layers.keys():
                vertex_tuple = (node_id, layer_id)
                vertex_idx = g.vcount()
                g.add_vertex(
                    name=str(vertex_tuple),
                    node_id=node_id,
                    layer_id=layer_id,
                    **node.attributes,
                )
                vertex_map[vertex_tuple] = vertex_idx

        # Add edges
        edge_list = []
        edge_attrs: Dict[str, list] = {}

        for edge in graph.edges:
            src_tuple = (edge.src, edge.src_layer)
            dst_tuple = (edge.dst, edge.dst_layer)

            src_idx = vertex_map[src_tuple]
            dst_idx = vertex_map[dst_tuple]

            edge_list.append((src_idx, dst_idx))

            # Collect edge attributes
            for key, value in edge.attributes.items():
                if key not in edge_attrs:
                    edge_attrs[key] = []
                edge_attrs[key].append(value)

            # Add edge key
            if "key" not in edge_attrs:
                edge_attrs["key"] = []
            edge_attrs["key"].append(edge.key)

        g.add_edges(edge_list)

        # Set edge attributes
        for key, values in edge_attrs.items():
            g.es[key] = values

    elif mode == "union":
        # Add vertices
        vertex_map_union: Dict[Any, int] = {}
        for node_id, node in graph.nodes.items():
            vertex_idx = g.vcount()
            g.add_vertex(name=str(node_id), node_id=node_id, **node.attributes)
            vertex_map_union[node_id] = vertex_idx

        # Add edges
        edge_list = []
        edge_attrs_union: Dict[str, list] = {}

        for edge in graph.edges:
            src_idx = vertex_map_union[edge.src]
            dst_idx = vertex_map_union[edge.dst]

            edge_list.append((src_idx, dst_idx))

            # Collect edge attributes (including layer info)
            attrs = edge.attributes.copy()
            attrs["src_layer"] = edge.src_layer
            attrs["dst_layer"] = edge.dst_layer

            for key, value in attrs.items():
                if key not in edge_attrs_union:
                    edge_attrs_union[key] = []
                edge_attrs_union[key].append(value)

        g.add_edges(edge_list)

        # Set edge attributes
        for key, values in edge_attrs_union.items():
            g.es[key] = values

    else:
        raise ConversionError(
            f"Mode '{mode}' not implemented for igraph conversion. "
            f"Supported modes: 'union', 'multiplex'."
        )

    return g


@require(lambda g: g is not None, "g must not be None")
@require(
    lambda mode: mode in ("union", "multiplex"), "mode must be 'union' or 'multiplex'"
)
@require(
    lambda default_layer: isinstance(default_layer, str),
    "default_layer must be a string",
)
@require(
    lambda default_layer: len(default_layer) > 0, "default_layer must not be empty"
)
@ensure(lambda result: result is not None, "result must not be None")
@ensure(
    lambda result: isinstance(result, MultiLayerGraph),
    "result must be a MultiLayerGraph",
)
def from_igraph(
    g: Any,
    mode: ProjectionMode = "multiplex",
    default_layer: str = "default",
) -> MultiLayerGraph:
    """
    Convert igraph graph to MultiLayerGraph.

    Args:
        g: igraph.Graph instance
        mode: Interpretation mode ('union' or 'multiplex')
        default_layer: Layer ID for 'union' mode

    Returns:
        MultiLayerGraph instance

    Raises:
        ImportError: If igraph is not installed

    Contracts:
        - Precondition: g must not be None
        - Precondition: mode must be 'union' or 'multiplex'
        - Precondition: default_layer must be a non-empty string
        - Postcondition: returns a MultiLayerGraph
    """
    try:
        import igraph as ig  # noqa: F401
    except ImportError:
        raise ImportError(
            "igraph is required for from_igraph(). Install with: pip install python-igraph"
        )

    # Create empty graph
    graph = MultiLayerGraph(directed=g.is_directed())

    if mode == "union":
        # Single layer
        graph.add_layer(Layer(id=default_layer))

        # Add nodes
        for v in g.vs:
            node_id = v["node_id"] if "node_id" in v.attributes() else v.index
            attrs = {k: v[k] for k in v.attributes() if k not in {"node_id", "name"}}
            graph.add_node(Node(id=node_id, attributes=attrs))

        # Add edges
        for e in g.es:
            src = (
                g.vs[e.source]["node_id"]
                if "node_id" in g.vs[e.source].attributes()
                else e.source
            )
            dst = (
                g.vs[e.target]["node_id"]
                if "node_id" in g.vs[e.target].attributes()
                else e.target
            )
            attrs = {k: e[k] for k in e.attributes() if k not in {"key"}}
            key = e["key"] if "key" in e.attributes() else 0

            edge = Edge(
                src=src,
                dst=dst,
                src_layer=default_layer,
                dst_layer=default_layer,
                key=key,
                attributes=attrs,
            )
            graph.add_edge(edge)

    elif mode == "multiplex":
        # Expect node_id and layer_id attributes
        # Collect layers and nodes
        layers_seen = set()
        nodes_map = {}

        for v in g.vs:
            if "node_id" not in v.attributes() or "layer_id" not in v.attributes():
                raise ConversionError(
                    "In 'multiplex' mode, vertices must have 'node_id' and 'layer_id' attributes. "
                    "Please ensure your igraph vertices have these required attributes."
                )

            node_id = v["node_id"]
            layer_id = v["layer_id"]

            layers_seen.add(layer_id)

            if node_id not in nodes_map:
                attrs = {
                    k: v[k]
                    for k in v.attributes()
                    if k not in {"node_id", "layer_id", "name"}
                }
                nodes_map[node_id] = attrs

        # Add layers
        for layer_id in layers_seen:
            graph.add_layer(Layer(id=layer_id))

        # Add nodes
        for node_id, attrs in nodes_map.items():
            graph.add_node(Node(id=node_id, attributes=attrs))

        # Add edges
        for e in g.es:
            src_v = g.vs[e.source]
            dst_v = g.vs[e.target]

            src_id = src_v["node_id"]
            dst_id = dst_v["node_id"]
            src_layer = src_v["layer_id"]
            dst_layer = dst_v["layer_id"]

            attrs = {k: e[k] for k in e.attributes() if k not in {"key"}}
            key = e["key"] if "key" in e.attributes() else 0

            edge = Edge(
                src=src_id,
                dst=dst_id,
                src_layer=src_layer,
                dst_layer=dst_layer,
                key=key,
                attributes=attrs,
            )
            graph.add_edge(edge)

    else:
        raise ConversionError(
            f"Unknown mode: '{mode}'. "
            f"Supported modes for graph-tool conversion: 'union', 'multiplex'."
        )

    return graph
