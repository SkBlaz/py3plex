"""
igraph converter (optional dependency).

This converter requires python-igraph to be installed.
Install with: pip install python-igraph
"""

from typing import Any

from ..exceptions import ConversionNotSupportedError
from ..ir import GraphIR

# Try to import igraph
try:
    import igraph as ig
    
    IGRAPH_AVAILABLE = True
except ImportError:
    IGRAPH_AVAILABLE = False


def to_igraph_from_ir(ir: GraphIR, *, strict: bool = True, **kwargs) -> Any:
    """
    Convert GraphIR to igraph graph.
    
    Args:
        ir: GraphIR to convert
        strict: If True, raise on incompatibilities
        **kwargs: Additional arguments
    
    Returns:
        igraph Graph object
    
    Raises:
        ConversionNotSupportedError: If igraph is not installed
    """
    if not IGRAPH_AVAILABLE:
        raise ConversionNotSupportedError(
            "igraph conversion requires python-igraph. "
            "Install with: pip install python-igraph"
        )
    
    # Create igraph
    g = ig.Graph(directed=ir.meta.directed)
    
    # Add vertices with original node IDs stored
    g.add_vertices(len(ir.nodes.node_id))
    g.vs["_py3plex_id"] = ir.nodes.node_id
    g.vs["_py3plex_order"] = ir.nodes.node_order
    
    # Add node attributes
    if ir.nodes.attrs is not None:
        for col in ir.nodes.attrs.columns:
            g.vs[col] = ir.nodes.attrs[col].tolist()
    
    # Build node ID to index mapping
    node_to_idx = {node_id: idx for idx, node_id in enumerate(ir.nodes.node_id)}
    
    # Add edges
    edge_list = []
    for idx in range(len(ir.edges.edge_id)):
        src_idx = node_to_idx[ir.edges.src[idx]]
        dst_idx = node_to_idx[ir.edges.dst[idx]]
        edge_list.append((src_idx, dst_idx))
    
    g.add_edges(edge_list)
    
    # Add edge attributes
    g.es["_py3plex_edge_id"] = ir.edges.edge_id
    g.es["_py3plex_order"] = ir.edges.edge_order
    
    if ir.edges.attrs is not None:
        for col in ir.edges.attrs.columns:
            g.es[col] = ir.edges.attrs[col].tolist()
    
    # Add layer information if present
    if ir.edges.src_layer:
        g.es["_py3plex_src_layer"] = ir.edges.src_layer
    if ir.edges.dst_layer:
        g.es["_py3plex_dst_layer"] = ir.edges.dst_layer
    
    # Add graph attributes
    for key, value in ir.meta.global_attrs.items():
        g[key] = value
    
    return g


def from_igraph_to_ir(g: Any) -> GraphIR:
    """
    Convert igraph graph to GraphIR.
    
    Args:
        g: igraph Graph object
    
    Returns:
        GraphIR representation
    
    Raises:
        ConversionNotSupportedError: If igraph is not installed
    """
    if not IGRAPH_AVAILABLE:
        raise ConversionNotSupportedError(
            "igraph conversion requires python-igraph. "
            "Install with: pip install python-igraph"
        )
    
    import pandas as pd
    
    from ..ir import EdgeTable, GraphMeta, NodeTable
    
    # Extract nodes
    if "_py3plex_id" in g.vs.attributes():
        node_id_list = g.vs["_py3plex_id"]
    else:
        node_id_list = list(range(g.vcount()))
    
    if "_py3plex_order" in g.vs.attributes():
        node_order_list = g.vs["_py3plex_order"]
    else:
        node_order_list = list(range(len(node_id_list)))
    
    # Extract node attributes
    node_attr_names = [
        name
        for name in g.vs.attributes()
        if not name.startswith("_py3plex_") and name != "name"
    ]
    node_attrs_records = []
    for v in g.vs:
        attrs = {name: v[name] for name in node_attr_names}
        node_attrs_records.append(attrs)
    
    node_attrs_df = pd.DataFrame(node_attrs_records) if node_attrs_records else None
    
    # Extract edges
    if "_py3plex_edge_id" in g.es.attributes():
        edge_id_list = g.es["_py3plex_edge_id"]
    else:
        edge_id_list = [f"e{i}" for i in range(g.ecount())]
    
    if "_py3plex_order" in g.es.attributes():
        edge_order_list = g.es["_py3plex_order"]
    else:
        edge_order_list = list(range(len(edge_id_list)))
    
    src_list = [node_id_list[e.source] for e in g.es]
    dst_list = [node_id_list[e.target] for e in g.es]
    
    # Extract edge attributes
    edge_attr_names = [
        name
        for name in g.es.attributes()
        if not name.startswith("_py3plex_") and name != "name"
    ]
    edge_attrs_records = []
    for e in g.es:
        attrs = {name: e[name] for name in edge_attr_names}
        edge_attrs_records.append(attrs)
    
    edge_attrs_df = pd.DataFrame(edge_attrs_records) if edge_attrs_records else None
    
    # Extract layer information
    src_layer_list = (
        g.es["_py3plex_src_layer"] if "_py3plex_src_layer" in g.es.attributes() else None
    )
    dst_layer_list = (
        g.es["_py3plex_dst_layer"] if "_py3plex_dst_layer" in g.es.attributes() else None
    )
    
    # Build tables
    nodes = NodeTable(
        node_id=node_id_list,
        node_order=node_order_list,
        attrs=node_attrs_df,
    )
    
    edges = EdgeTable(
        edge_id=edge_id_list,
        src=src_list,
        dst=dst_list,
        edge_order=edge_order_list,
        attrs=edge_attrs_df,
        src_layer=src_layer_list,
        dst_layer=dst_layer_list,
    )
    
    # Extract graph attributes
    global_attrs = {key: g[key] for key in g.attributes() if not key.startswith("_py3plex_")}
    
    meta = GraphMeta(
        directed=g.is_directed(),
        multi=False,  # igraph doesn't support true multigraphs
        global_attrs=global_attrs,
    )
    
    return GraphIR(nodes=nodes, edges=edges, meta=meta)
