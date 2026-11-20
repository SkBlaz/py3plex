"""Network capture and restoration for provenance replay.

This module handles capturing network state in a canonical, serializable form
and restoring networks from captured snapshots.
"""

import hashlib
import json
from copy import deepcopy
from typing import Any, Dict, List, Optional


class NetworkCapture:
    """Canonical network snapshot for provenance."""
    
    def __init__(
        self,
        nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]],
        directed: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Initialize network capture.
        
        Args:
            nodes: List of node dicts with (id, layer, attributes)
            edges: List of edge dicts with (source, target, source_layer, target_layer, attributes)
            directed: Whether network is directed
            metadata: Optional network-level metadata
        """
        self.nodes = nodes
        self.edges = edges
        self.directed = directed
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "nodes": self.nodes,
            "edges": self.edges,
            "directed": self.directed,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NetworkCapture":
        """Create from dictionary."""
        return cls(
            nodes=data["nodes"],
            edges=data["edges"],
            directed=data.get("directed", False),
            metadata=data.get("metadata", {}),
        )
    
    def compute_hash(self) -> str:
        """Compute stable hash of network content.
        
        Returns:
            Hex string of SHA256 hash (first 16 chars)
        """
        # Create canonical JSON representation
        canonical = json.dumps(self.to_dict(), sort_keys=True, default=str)
        hasher = hashlib.sha256()
        hasher.update(canonical.encode('utf-8'))
        return hasher.hexdigest()[:16]


def _replica_parts(node):
    if isinstance(node, tuple) and len(node) == 2:
        return node
    return node, None


def _restore_identity(value):
    """Recover tuple identifiers after a JSON bundle round trip."""
    if isinstance(value, list):
        return tuple(_restore_identity(part) for part in value)
    return value


def capture_network(network: Any, include_attributes: bool = True) -> NetworkCapture:
    """Capture graph topology, replica order, and data for replay."""
    from py3plex.core.multinet import multi_layer_network

    graph = network.core_network
    is_multigraph = graph is None or graph.is_multigraph()
    metadata = {
        "network_type": getattr(network, "network_type", "multilayer"),
        "coupling_weight": getattr(network, "coupling_weight", 1),
        "multigraph": is_multigraph,
        "layers": list(network.layers),
    }
    nodes = []
    edges = []
    if graph is not None:
        if include_attributes:
            metadata["graph_attributes"] = deepcopy(graph.graph)
        for replica, attrs in graph.nodes(data=True):
            node_id, layer = _replica_parts(replica)
            node = {"id": node_id, "layer": layer, "replica": replica}
            if include_attributes:
                node["attributes"] = deepcopy(attrs)
            nodes.append(node)

        if type(network) is multi_layer_network:
            if is_multigraph:
                edge_records = graph.edges(keys=True, data=True)
            else:
                edge_records = graph.edges(data=True)
        else:
            edge_records = network.get_edges(data=True, multiplex_edges=True)

        for record in edge_records:
            source, target, attrs = record[0], record[1], record[-1]
            src_id, src_layer = _replica_parts(source)
            dst_id, dst_layer = _replica_parts(target)
            edge = {
                "source": src_id, "source_layer": src_layer,
                "target": dst_id, "target_layer": dst_layer,
                "source_replica": source, "target_replica": target,
            }
            if "weight" in attrs:
                edge["weight"] = deepcopy(attrs["weight"])
            if len(record) == 4:
                edge["key"] = record[2]
            if include_attributes:
                edge["attributes"] = deepcopy(attrs)
            elif metadata["network_type"] == "multiplex" and attrs.get("type") == "coupling":
                edge["attributes"] = {"type": "coupling"}
            edges.append(edge)

    directed = graph.is_directed() if graph is not None else network.directed
    return NetworkCapture(nodes, edges, directed, metadata)


def restore_network(capture: NetworkCapture) -> Any:
    """Restore a graph snapshot, including snapshots from older bundles."""
    from py3plex.core import multinet

    metadata = capture.metadata
    network = multinet.multi_layer_network(
        directed=capture.directed,
        network_type=metadata.get("network_type", "multilayer"),
        coupling_weight=metadata.get("coupling_weight", 1),
    )
    graph = network._create_graph(multi=metadata.get("multigraph", True))
    graph.graph.update(deepcopy(metadata.get("graph_attributes", {})))
    for node in capture.nodes:
        replica = _restore_identity(node.get("replica", [node["id"], node.get("layer", "default")]))
        graph.add_node(replica)
        graph.nodes[replica].update(deepcopy(node.get("attributes", {})))

    for edge in capture.edges:
        source = _restore_identity(edge.get(
            "source_replica", [edge["source"], edge.get("source_layer", "default")]
        ))
        target = _restore_identity(edge.get(
            "target_replica", [edge["target"], edge.get("target_layer", "default")]
        ))
        if graph.is_multigraph():
            key = graph.add_edge(source, target, key=_restore_identity(edge.get("key")))
            attrs = graph.edges[source, target, key]
        else:
            graph.add_edge(source, target)
            attrs = graph.edges[source, target]
        attrs.update(deepcopy(edge.get("attributes", {})))
        if "weight" in edge:
            attrs["weight"] = deepcopy(edge["weight"])

    network.core_network = graph
    return network


def estimate_capture_size(capture: NetworkCapture) -> int:
    """Estimate size of a network capture in bytes.
    
    Args:
        capture: NetworkCapture instance
        
    Returns:
        Estimated size in bytes
    """
    try:
        json_str = json.dumps(capture.to_dict(), default=str)
        return len(json_str.encode('utf-8'))
    except Exception:
        # Fallback: rough estimate
        node_bytes = len(capture.nodes) * 100  # ~100 bytes per node
        edge_bytes = len(capture.edges) * 150  # ~150 bytes per edge
        return node_bytes + edge_bytes


def compress_snapshot(snapshot_dict: Dict[str, Any]) -> bytes:
    """Compress snapshot using gzip.
    
    Args:
        snapshot_dict: Snapshot dictionary
        
    Returns:
        Compressed bytes
    """
    import gzip
    json_str = json.dumps(snapshot_dict, default=str)
    json_bytes = json_str.encode('utf-8')
    return gzip.compress(json_bytes)


def decompress_snapshot(compressed_bytes: bytes) -> Dict[str, Any]:
    """Decompress snapshot from gzip.
    
    Args:
        compressed_bytes: Compressed bytes
        
    Returns:
        Snapshot dictionary
    """
    import gzip
    json_bytes = gzip.decompress(compressed_bytes)
    json_str = json_bytes.decode('utf-8')
    return json.loads(json_str)
