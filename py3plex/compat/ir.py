"""
Intermediate Representation (IR) for lossless graph conversion.

This module provides a canonical interchange format for graph data that preserves
all information needed for lossless roundtrip conversion between different formats.

The IR is designed to:
- Preserve graph semantics (directed/undirected, simple/multi)
- Preserve node and edge identities with deterministic ordering
- Preserve all attributes (node, edge, and graph-level)
- Support both simple and multilayer network structures
"""

import warnings
from dataclasses import dataclass, field
from typing import Any, Dict, Hashable, List, Optional, Set, Tuple

import numpy as np
import pandas as pd

from py3plex.exceptions import Py3plexException

from .exceptions import SchemaError


@dataclass
class NodeTable:
    """
    Tabular representation of nodes with deterministic ordering.
    
    Attributes:
        node_id: List of node identifiers (hashable)
        node_order: List of integer indices for deterministic ordering
        attrs: DataFrame of node attributes (or dict mapping node_id to attrs)
        layer: Optional layer assignment for multilayer networks
    """
    
    node_id: List[Hashable]
    node_order: List[int]
    attrs: Optional[pd.DataFrame] = None
    layer: Optional[List[str]] = None
    
    def __post_init__(self):
        """Validate node table after initialization."""
        if len(self.node_id) != len(self.node_order):
            raise SchemaError(
                "node_id and node_order must have the same length",
                field="node_table",
                expected=f"length {len(self.node_id)}",
                actual=f"length {len(self.node_order)}",
            )
        
        if self.attrs is not None:
            if isinstance(self.attrs, pd.DataFrame):
                if len(self.attrs) != len(self.node_id):
                    raise SchemaError(
                        "attrs DataFrame must have same length as node_id",
                        field="attrs",
                        expected=f"length {len(self.node_id)}",
                        actual=f"length {len(self.attrs)}",
                    )
        
        if self.layer is not None and len(self.layer) != len(self.node_id):
            raise SchemaError(
                "layer list must have same length as node_id",
                field="layer",
                expected=f"length {len(self.node_id)}",
                actual=f"length {len(self.layer)}",
            )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        result = {
            "node_id": self.node_id,
            "node_order": self.node_order,
        }
        if self.attrs is not None:
            if isinstance(self.attrs, pd.DataFrame):
                result["attrs"] = self.attrs.to_dict(orient="records")
            else:
                result["attrs"] = self.attrs
        if self.layer is not None:
            result["layer"] = self.layer
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NodeTable":
        """Create NodeTable from dictionary."""
        attrs = data.get("attrs")
        if attrs is not None and isinstance(attrs, list):
            attrs = pd.DataFrame(attrs)
        
        return cls(
            node_id=data["node_id"],
            node_order=data["node_order"],
            attrs=attrs,
            layer=data.get("layer"),
        )


@dataclass
class EdgeTable:
    """
    Tabular representation of edges with deterministic ordering.
    
    Attributes:
        edge_id: List of edge identifiers for multigraph support
        src: List of source node IDs
        dst: List of destination node IDs
        edge_order: List of integer indices for deterministic ordering
        attrs: DataFrame of edge attributes (or dict mapping edge_id to attrs)
        src_layer: Optional source layer for multilayer networks
        dst_layer: Optional destination layer for multilayer networks
        key: Optional list of edge keys for multigraph support (default: 0 for each edge)
    """
    
    edge_id: List[Hashable]
    src: List[Hashable]
    dst: List[Hashable]
    edge_order: List[int]
    attrs: Optional[pd.DataFrame] = None
    src_layer: Optional[List[str]] = None
    dst_layer: Optional[List[str]] = None
    key: Optional[List[int]] = None
    
    def __post_init__(self):
        """Validate edge table after initialization."""
        if not (len(self.edge_id) == len(self.src) == len(self.dst) == len(self.edge_order)):
            raise SchemaError(
                "edge_id, src, dst, and edge_order must have the same length",
                field="edge_table",
            )
        
        if self.attrs is not None:
            if isinstance(self.attrs, pd.DataFrame):
                if len(self.attrs) != len(self.edge_id):
                    raise SchemaError(
                        "attrs DataFrame must have same length as edge_id",
                        field="attrs",
                        expected=f"length {len(self.edge_id)}",
                        actual=f"length {len(self.attrs)}",
                    )
        
        if self.src_layer is not None and len(self.src_layer) != len(self.edge_id):
            raise SchemaError(
                "src_layer must have same length as edge_id",
                field="src_layer",
            )
        
        if self.dst_layer is not None and len(self.dst_layer) != len(self.edge_id):
            raise SchemaError(
                "dst_layer must have same length as edge_id",
                field="dst_layer",
            )
        
        if self.key is not None and len(self.key) != len(self.edge_id):
            raise SchemaError(
                "key must have same length as edge_id",
                field="key",
            )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        result = {
            "edge_id": self.edge_id,
            "src": self.src,
            "dst": self.dst,
            "edge_order": self.edge_order,
        }
        if self.attrs is not None:
            if isinstance(self.attrs, pd.DataFrame):
                result["attrs"] = self.attrs.to_dict(orient="records")
            else:
                result["attrs"] = self.attrs
        if self.src_layer is not None:
            result["src_layer"] = self.src_layer
        if self.dst_layer is not None:
            result["dst_layer"] = self.dst_layer
        if self.key is not None:
            result["key"] = self.key
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EdgeTable":
        """Create EdgeTable from dictionary."""
        attrs = data.get("attrs")
        if attrs is not None and isinstance(attrs, list):
            attrs = pd.DataFrame(attrs)
        
        return cls(
            edge_id=data["edge_id"],
            src=data["src"],
            dst=data["dst"],
            edge_order=data["edge_order"],
            attrs=attrs,
            src_layer=data.get("src_layer"),
            dst_layer=data.get("dst_layer"),
            key=data.get("key"),
        )


@dataclass
class GraphMeta:
    """
    Graph-level metadata.
    
    Attributes:
        directed: Whether the graph is directed
        multi: Whether the graph is a multigraph (parallel edges allowed)
        name: Optional graph name
        created_by: Tool/library that created the graph
        py3plex_version: Version of py3plex used
        schema_version: IR schema version
        global_attrs: Additional graph-level attributes
        layers: List of layer identifiers for multilayer networks
    """
    
    directed: bool = False
    multi: bool = False
    name: Optional[str] = None
    created_by: str = "py3plex"
    py3plex_version: Optional[str] = None
    schema_version: str = "1.0"
    global_attrs: Dict[str, Any] = field(default_factory=dict)
    layers: Optional[List[str]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "directed": self.directed,
            "multi": self.multi,
            "name": self.name,
            "created_by": self.created_by,
            "py3plex_version": self.py3plex_version,
            "schema_version": self.schema_version,
            "global_attrs": self.global_attrs,
            "layers": self.layers,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GraphMeta":
        """Create GraphMeta from dictionary."""
        return cls(**data)


@dataclass
class GraphIR:
    """
    Intermediate Representation for graph data.
    
    This is the canonical format used by all converters to ensure
    lossless roundtrip conversion.
    
    Attributes:
        nodes: Node table with IDs, ordering, and attributes
        edges: Edge table with IDs, ordering, and attributes
        meta: Graph-level metadata
    """
    
    nodes: NodeTable
    edges: EdgeTable
    meta: GraphMeta
    
    def __post_init__(self):
        """Validate GraphIR after initialization."""
        # Check that all edge endpoints exist in node table
        node_id_set = set(self.nodes.node_id)
        for src, dst in zip(self.edges.src, self.edges.dst):
            if src not in node_id_set:
                raise SchemaError(
                    f"Edge source node '{src}' not found in node table",
                    field="edges.src",
                )
            if dst not in node_id_set:
                raise SchemaError(
                    f"Edge destination node '{dst}' not found in node table",
                    field="edges.dst",
                )
        
        # Check layer consistency for multilayer networks
        if self.meta.layers is not None:
            layer_set = set(self.meta.layers)
            if self.nodes.layer is not None:
                for layer in self.nodes.layer:
                    if layer not in layer_set:
                        warnings.warn(
                            f"Node layer '{layer}' not in meta.layers",
                            UserWarning,
                        )
            if self.edges.src_layer is not None:
                for layer in self.edges.src_layer:
                    if layer not in layer_set:
                        warnings.warn(
                            f"Edge source layer '{layer}' not in meta.layers",
                            UserWarning,
                        )
            if self.edges.dst_layer is not None:
                for layer in self.edges.dst_layer:
                    if layer not in layer_set:
                        warnings.warn(
                            f"Edge destination layer '{layer}' not in meta.layers",
                            UserWarning,
                        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "nodes": self.nodes.to_dict(),
            "edges": self.edges.to_dict(),
            "meta": self.meta.to_dict(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GraphIR":
        """Create GraphIR from dictionary."""
        return cls(
            nodes=NodeTable.from_dict(data["nodes"]),
            edges=EdgeTable.from_dict(data["edges"]),
            meta=GraphMeta.from_dict(data["meta"]),
        )


def to_ir(graph: Any) -> GraphIR:
    """
    Convert a py3plex graph to Intermediate Representation.
    
    Args:
        graph: A py3plex graph object (MultiLayerGraph or multi_layer_network)
    
    Returns:
        GraphIR: Intermediate representation of the graph
    
    Raises:
        TypeError: If graph type is not supported
    """
    # Import here to avoid circular dependencies
    from py3plex.io.schema import MultiLayerGraph
    
    if isinstance(graph, MultiLayerGraph):
        return _multilayer_graph_to_ir(graph)
    else:
        # Try to handle multi_layer_network from core
        if hasattr(graph, "get_nodes") and hasattr(graph, "get_edges"):
            return _multinet_to_ir(graph)
        else:
            raise TypeError(
                f"Cannot convert graph of type {type(graph)} to IR. "
                "Supported types: MultiLayerGraph, multi_layer_network"
            )


def _multilayer_graph_to_ir(graph) -> GraphIR:
    """Convert MultiLayerGraph to GraphIR."""
    from py3plex.io.schema import MultiLayerGraph
    
    # Extract nodes - graph.nodes is Dict[NodeID, Node], iterate over .values()
    node_id_list = [node.id for node in graph.nodes.values()]
    node_order_list = list(range(len(node_id_list)))
    
    # Build node attributes DataFrame
    if graph.nodes:
        node_attrs_records = []
        node_layers = []
        for node in graph.nodes.values():  # Iterate over Node objects, not keys
            node_attrs_records.append(node.attributes.copy() if node.attributes else {})
            # For MultiLayerGraph, nodes can be in multiple layers
            # We'll track the primary layer if available
            node_layers.append(None)  # Could be enhanced with layer info
        
        node_attrs_df = pd.DataFrame(node_attrs_records) if node_attrs_records else None
    else:
        node_attrs_df = None
        node_layers = None
    
    # Extract edges
    edge_id_list = []
    src_list = []
    dst_list = []
    edge_order_list = []
    src_layer_list = []
    dst_layer_list = []
    key_list = []
    edge_attrs_records = []
    
    for idx, edge in enumerate(graph.edges):
        edge_id_list.append(f"e{idx}")  # Generate edge IDs
        src_list.append(edge.src)
        dst_list.append(edge.dst)
        edge_order_list.append(idx)
        src_layer_list.append(edge.src_layer)
        dst_layer_list.append(edge.dst_layer)
        key_list.append(edge.key)  # Preserve the edge key
        edge_attrs_records.append(edge.attributes.copy() if edge.attributes else {})
    
    edge_attrs_df = pd.DataFrame(edge_attrs_records) if edge_attrs_records else None
    
    # Build node table
    nodes = NodeTable(
        node_id=node_id_list,
        node_order=node_order_list,
        attrs=node_attrs_df,
        layer=node_layers,
    )
    
    # Build edge table
    edges = EdgeTable(
        edge_id=edge_id_list,
        src=src_list,
        dst=dst_list,
        edge_order=edge_order_list,
        attrs=edge_attrs_df,
        src_layer=src_layer_list if src_layer_list else None,
        dst_layer=dst_layer_list if dst_layer_list else None,
        key=key_list if key_list else None,  # Include key list
    )
    
    # Extract layers - graph.layers is Dict[LayerID, Layer], iterate over .values()
    layers = [layer.id for layer in graph.layers.values()] if graph.layers else None
    
    # Build metadata
    meta = GraphMeta(
        directed=graph.directed,
        multi=True,  # MultiLayerGraph supports multi-edges
        name=None,
        global_attrs=graph.attributes.copy() if graph.attributes else {},
        layers=layers,
    )
    
    return GraphIR(nodes=nodes, edges=edges, meta=meta)


def _multinet_to_ir(graph) -> GraphIR:
    """Convert multi_layer_network to GraphIR."""
    # This handles the core.multinet.multi_layer_network class
    # Get NetworkX graph from the multi_layer_network
    import networkx as nx
    
    if hasattr(graph, "network"):
        G = graph.network
    else:
        raise AttributeError("multi_layer_network object has no 'network' attribute")
    
    # Determine if directed
    directed = G.is_directed() if hasattr(G, "is_directed") else False
    multi = G.is_multigraph() if hasattr(G, "is_multigraph") else False
    
    # Extract nodes
    node_list = list(G.nodes())
    node_id_list = node_list
    node_order_list = list(range(len(node_id_list)))
    
    # Extract node attributes
    node_attrs_records = []
    for node in node_list:
        attrs = G.nodes[node].copy() if node in G.nodes else {}
        node_attrs_records.append(attrs)
    
    node_attrs_df = pd.DataFrame(node_attrs_records) if node_attrs_records else None
    
    # Extract edges
    edge_id_list = []
    src_list = []
    dst_list = []
    edge_order_list = []
    edge_attrs_records = []
    src_layer_list = []
    dst_layer_list = []
    
    if multi:
        # MultiGraph/MultiDiGraph
        for idx, (u, v, key, data) in enumerate(G.edges(keys=True, data=True)):
            edge_id_list.append(f"{u}_{v}_{key}")
            src_list.append(u)
            dst_list.append(v)
            edge_order_list.append(idx)
            edge_attrs_records.append(data.copy() if data else {})
            # Extract layer info if available
            src_layer_list.append(data.get("source_type") or data.get("src_layer"))
            dst_layer_list.append(data.get("target_type") or data.get("dst_layer"))
    else:
        # Simple Graph/DiGraph
        for idx, (u, v, data) in enumerate(G.edges(data=True)):
            edge_id_list.append(f"{u}_{v}")
            src_list.append(u)
            dst_list.append(v)
            edge_order_list.append(idx)
            edge_attrs_records.append(data.copy() if data else {})
            src_layer_list.append(data.get("source_type") or data.get("src_layer"))
            dst_layer_list.append(data.get("target_type") or data.get("dst_layer"))
    
    edge_attrs_df = pd.DataFrame(edge_attrs_records) if edge_attrs_records else None
    
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
        src_layer=src_layer_list if any(src_layer_list) else None,
        dst_layer=dst_layer_list if any(dst_layer_list) else None,
    )
    
    # Extract graph attributes
    global_attrs = G.graph.copy() if hasattr(G, "graph") else {}
    
    meta = GraphMeta(
        directed=directed,
        multi=multi,
        name=global_attrs.get("name"),
        global_attrs=global_attrs,
    )
    
    return GraphIR(nodes=nodes, edges=edges, meta=meta)


def from_ir(ir: GraphIR, target_type: str = "multilayer_graph") -> Any:
    """
    Convert Intermediate Representation to a py3plex graph.
    
    Args:
        ir: GraphIR intermediate representation
        target_type: Type of graph to create ("multilayer_graph" or "multi_layer_network")
    
    Returns:
        A py3plex graph object
    
    Raises:
        ValueError: If target_type is not supported
    """
    if target_type == "multilayer_graph":
        return _ir_to_multilayer_graph(ir)
    elif target_type == "multi_layer_network":
        return _ir_to_multinet(ir)
    else:
        raise ValueError(
            f"Unsupported target_type: {target_type}. "
            "Supported: 'multilayer_graph', 'multi_layer_network'"
        )


def _ir_to_multilayer_graph(ir: GraphIR):
    """Convert GraphIR to MultiLayerGraph."""
    from py3plex.io.schema import Edge, Layer, MultiLayerGraph, Node
    
    graph = MultiLayerGraph(directed=ir.meta.directed)
    
    # Set graph attributes
    if ir.meta.global_attrs:
        graph.attributes = ir.meta.global_attrs.copy()
    if ir.meta.name:
        graph.attributes["name"] = ir.meta.name
    
    # Add layers
    if ir.meta.layers:
        for layer_id in ir.meta.layers:
            graph.add_layer(Layer(id=layer_id))
    
    # Add nodes
    for idx in range(len(ir.nodes.node_id)):
        node_id = ir.nodes.node_id[idx]
        attrs = {}
        if ir.nodes.attrs is not None:
            attrs = ir.nodes.attrs.iloc[idx].to_dict()
        graph.add_node(Node(id=node_id, attributes=attrs))
    
    # Add edges
    for idx in range(len(ir.edges.edge_id)):
        src = ir.edges.src[idx]
        dst = ir.edges.dst[idx]
        attrs = {}
        if ir.edges.attrs is not None:
            attrs = ir.edges.attrs.iloc[idx].to_dict()
        
        src_layer = ir.edges.src_layer[idx] if ir.edges.src_layer else "default"
        dst_layer = ir.edges.dst_layer[idx] if ir.edges.dst_layer else "default"
        key = ir.edges.key[idx] if ir.edges.key else 0  # Use stored key or default to 0
        
        graph.add_edge(
            Edge(
                src=src,
                dst=dst,
                src_layer=src_layer,
                dst_layer=dst_layer,
                key=key,  # Pass the key parameter
                attributes=attrs,
            )
        )
    
    return graph


def _ir_to_multinet(ir: GraphIR):
    """Convert GraphIR to multi_layer_network."""
    from py3plex.core.multinet import multi_layer_network
    import networkx as nx
    
    # Create the appropriate NetworkX graph type
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
    
    # Add nodes with attributes
    for idx in range(len(ir.nodes.node_id)):
        node_id = ir.nodes.node_id[idx]
        attrs = {}
        if ir.nodes.attrs is not None:
            attrs = ir.nodes.attrs.iloc[idx].to_dict()
        G.add_node(node_id, **attrs)
    
    # Add edges with attributes
    for idx in range(len(ir.edges.edge_id)):
        src = ir.edges.src[idx]
        dst = ir.edges.dst[idx]
        attrs = {}
        if ir.edges.attrs is not None:
            attrs = ir.edges.attrs.iloc[idx].to_dict()
        
        # Add layer information to edge attributes
        if ir.edges.src_layer and ir.edges.src_layer[idx]:
            attrs["source_type"] = ir.edges.src_layer[idx]
        if ir.edges.dst_layer and ir.edges.dst_layer[idx]:
            attrs["target_type"] = ir.edges.dst_layer[idx]
        
        G.add_edge(src, dst, **attrs)
    
    # Create multi_layer_network wrapper
    net = multi_layer_network()
    net.network = G
    
    return net
