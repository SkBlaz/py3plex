"""
NetworkX converter for lossless bidirectional conversion.

This converter preserves:
- Graph semantics (directed/undirected, simple/multigraph)
- Node and edge identities
- All node and edge attributes
- Multigraph edge keys mapped to edge_id
"""

import warnings
from typing import Any, Dict, Optional

import networkx as nx
import pandas as pd

from ..exceptions import CompatibilityError
from ..ir import EdgeTable, GraphIR, GraphMeta, NodeTable


def to_networkx_from_ir(
    ir: GraphIR,
    *,
    strict: bool = True,
    preserve_layers: bool = True,
    **kwargs,
) -> nx.Graph:
    """
    Convert GraphIR to NetworkX graph.
    
    Args:
        ir: GraphIR to convert
        strict: If True, raise exception on incompatibilities (currently always succeeds)
        preserve_layers: If True, preserve layer information in node/edge attributes
        **kwargs: Additional keyword arguments (unused)
    
    Returns:
        NetworkX graph (Graph, DiGraph, MultiGraph, or MultiDiGraph)
    
    Raises:
        CompatibilityError: In strict mode, if conversion would lose data (rare)
    """
    # Create appropriate graph type
    if ir.meta.directed and ir.meta.multi:
        G = nx.MultiDiGraph()
    elif ir.meta.directed:
        G = nx.DiGraph()
    elif ir.meta.multi:
        G = nx.MultiGraph()
    else:
        G = nx.Graph()
    
    # Set graph attributes
    G.graph.update(ir.meta.global_attrs)
    if ir.meta.name:
        G.graph["name"] = ir.meta.name
    
    # Add metadata for roundtrip
    G.graph["_py3plex_schema_version"] = ir.meta.schema_version
    if ir.meta.layers and preserve_layers:
        G.graph["_py3plex_layers"] = ir.meta.layers
    
    # Add nodes with attributes
    for idx in range(len(ir.nodes.node_id)):
        node_id = ir.nodes.node_id[idx]
        attrs = {}
        
        if ir.nodes.attrs is not None:
            # Convert DataFrame row to dict, handling NaN
            row_dict = ir.nodes.attrs.iloc[idx].to_dict()
            attrs = {k: v for k, v in row_dict.items() if pd.notna(v)}
        
        # Preserve node order for determinism
        attrs["_py3plex_node_order"] = ir.nodes.node_order[idx]
        
        # Preserve layer info if present
        if ir.nodes.layer and ir.nodes.layer[idx] is not None and preserve_layers:
            attrs["_py3plex_layer"] = ir.nodes.layer[idx]
        
        G.add_node(node_id, **attrs)
    
    # Add edges with attributes
    # Track edge keys per (src, dst) pair to ensure uniqueness in NetworkX
    edge_key_counter = {}
    
    for idx in range(len(ir.edges.edge_id)):
        src = ir.edges.src[idx]
        dst = ir.edges.dst[idx]
        edge_id = ir.edges.edge_id[idx]
        
        attrs = {}
        if ir.edges.attrs is not None:
            # Convert DataFrame row to dict, handling NaN
            row_dict = ir.edges.attrs.iloc[idx].to_dict()
            attrs = {k: v for k, v in row_dict.items() if pd.notna(v)}
        
        # Preserve edge order and ID for determinism and roundtrip
        attrs["_py3plex_edge_order"] = ir.edges.edge_order[idx]
        attrs["_py3plex_edge_id"] = edge_id
        
        # Preserve layer info if present
        if ir.edges.src_layer and ir.edges.src_layer[idx] is not None and preserve_layers:
            attrs["_py3plex_src_layer"] = ir.edges.src_layer[idx]
        if ir.edges.dst_layer and ir.edges.dst_layer[idx] is not None and preserve_layers:
            attrs["_py3plex_dst_layer"] = ir.edges.dst_layer[idx]
        
        # Preserve original key from MultiLayerGraph
        original_key = ir.edges.key[idx] if ir.edges.key else 0
        attrs["_py3plex_key"] = original_key
        
        if ir.meta.multi:
            # For multigraphs, ensure unique NetworkX keys even if original keys collide
            # Track how many edges we've seen for each (src, dst, original_key) combination
            # For undirected graphs, normalize edge pair to avoid (u,v) and (v,u) collisions
            if not ir.meta.directed:
                # Normalize: always use (min, max) order for undirected edges
                edge_pair = (min(src, dst), max(src, dst), original_key)
            else:
                edge_pair = (src, dst, original_key)
            
            if edge_pair not in edge_key_counter:
                edge_key_counter[edge_pair] = 0
            else:
                edge_key_counter[edge_pair] += 1
            
            # Use counter to create unique NetworkX key
            nx_key = edge_key_counter[edge_pair]
            G.add_edge(src, dst, key=nx_key, **attrs)
        else:
            G.add_edge(src, dst, **attrs)
    
    return G


def from_networkx_to_ir(G: nx.Graph) -> GraphIR:
    """
    Convert NetworkX graph to GraphIR.
    
    Args:
        G: NetworkX graph
    
    Returns:
        GraphIR representation
    """
    # Determine graph properties
    directed = G.is_directed()
    multi = G.is_multigraph()
    
    # Extract nodes
    node_list = list(G.nodes())
    node_id_list = node_list
    
    # Extract node order (if present) or create it
    node_order_list = []
    node_attrs_records = []
    node_layers = []
    has_layer_info = False
    
    for node in node_list:
        attrs = G.nodes[node].copy() if node in G.nodes else {}
        
        # Extract and remove metadata
        node_order = attrs.pop("_py3plex_node_order", None)
        layer = attrs.pop("_py3plex_layer", None)
        
        if node_order is None:
            # Generate order if not present
            node_order = len(node_order_list)
        node_order_list.append(node_order)
        
        if layer is not None:
            has_layer_info = True
        node_layers.append(layer)
        
        node_attrs_records.append(attrs)
    
    # Create node attributes DataFrame
    node_attrs_df = pd.DataFrame(node_attrs_records) if node_attrs_records else None
    
    # Extract edges
    edge_id_list = []
    src_list = []
    dst_list = []
    edge_order_list = []
    edge_attrs_records = []
    src_layer_list = []
    dst_layer_list = []
    key_list = []
    has_edge_layer_info = False
    
    if multi:
        # MultiGraph: edges have keys
        for u, v, key, data in G.edges(keys=True, data=True):
            # Extract edge ID (or use key)
            edge_id = data.pop("_py3plex_edge_id", f"{u}_{v}_{key}")
            edge_order = data.pop("_py3plex_edge_order", len(edge_id_list))
            src_layer = data.pop("_py3plex_src_layer", None)
            dst_layer = data.pop("_py3plex_dst_layer", None)
            stored_key = data.pop("_py3plex_key", key)  # Extract and preserve key
            
            if src_layer or dst_layer:
                has_edge_layer_info = True
            
            edge_id_list.append(edge_id)
            src_list.append(u)
            dst_list.append(v)
            edge_order_list.append(edge_order)
            src_layer_list.append(src_layer)
            dst_layer_list.append(dst_layer)
            key_list.append(stored_key)
            edge_attrs_records.append(data.copy() if data else {})
    else:
        # Simple graph
        for u, v, data in G.edges(data=True):
            edge_id = data.pop("_py3plex_edge_id", f"{u}_{v}")
            edge_order = data.pop("_py3plex_edge_order", len(edge_id_list))
            src_layer = data.pop("_py3plex_src_layer", None)
            dst_layer = data.pop("_py3plex_dst_layer", None)
            stored_key = data.pop("_py3plex_key", 0)  # Default key for simple graphs
            
            if src_layer or dst_layer:
                has_edge_layer_info = True
            
            edge_id_list.append(edge_id)
            src_list.append(u)
            dst_list.append(v)
            edge_order_list.append(edge_order)
            src_layer_list.append(src_layer)
            dst_layer_list.append(dst_layer)
            key_list.append(stored_key)
            edge_attrs_records.append(data.copy() if data else {})
    
    edge_attrs_df = pd.DataFrame(edge_attrs_records) if edge_attrs_records else None
    
    # Build node table
    nodes = NodeTable(
        node_id=node_id_list,
        node_order=node_order_list,
        attrs=node_attrs_df,
        layer=node_layers if has_layer_info else None,
    )
    
    # Build edge table
    edges = EdgeTable(
        edge_id=edge_id_list,
        src=src_list,
        dst=dst_list,
        edge_order=edge_order_list,
        attrs=edge_attrs_df,
        src_layer=src_layer_list if has_edge_layer_info else None,
        dst_layer=dst_layer_list if has_edge_layer_info else None,
        key=key_list if key_list else None,  # Include key list
    )
    
    # Extract graph attributes
    global_attrs = G.graph.copy()
    name = global_attrs.pop("name", None)
    schema_version = global_attrs.pop("_py3plex_schema_version", "1.0")
    layers = global_attrs.pop("_py3plex_layers", None)
    
    # Build metadata
    meta = GraphMeta(
        directed=directed,
        multi=multi,
        name=name,
        schema_version=schema_version,
        global_attrs=global_attrs,
        layers=layers,
    )
    
    return GraphIR(nodes=nodes, edges=edges, meta=meta)
