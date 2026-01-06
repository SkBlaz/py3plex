"""Network capture and restoration for provenance replay.

This module handles capturing network state in a canonical, serializable form
and restoring networks from captured snapshots.
"""

import hashlib
import json
from typing import Any, Dict, List, Optional, Tuple


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


def capture_network(network: Any, include_attributes: bool = True) -> NetworkCapture:
    """Capture network state in canonical form.
    
    Args:
        network: Multilayer network object
        include_attributes: Whether to include node/edge attributes
        
    Returns:
        NetworkCapture instance
    """
    nodes = []
    edges = []
    
    # Capture nodes
    if hasattr(network, 'get_nodes'):
        for node in network.get_nodes():
            node_dict = {}
            
            # Extract node ID and layer
            if isinstance(node, tuple) and len(node) >= 2:
                node_dict['id'] = node[0]
                node_dict['layer'] = node[1]
            else:
                node_dict['id'] = node
                node_dict['layer'] = None
            
            # Get node attributes if requested
            if include_attributes and hasattr(network, 'core_network'):
                try:
                    attrs = network.core_network.nodes.get(node, {})
                    if attrs:
                        node_dict['attributes'] = dict(attrs)
                except Exception:
                    pass
            
            nodes.append(node_dict)
    
    # Sort nodes for stable ordering
    nodes.sort(key=lambda n: (str(n.get('layer', '')), str(n['id'])))
    
    # Capture edges
    if hasattr(network, 'get_edges'):
        for edge in network.get_edges():
            edge_dict = {}
            
            # Extract edge endpoints
            if isinstance(edge, tuple) and len(edge) >= 2:
                source, target = edge[0], edge[1]
                
                # Extract source info
                if isinstance(source, tuple) and len(source) >= 2:
                    edge_dict['source'] = source[0]
                    edge_dict['source_layer'] = source[1]
                else:
                    edge_dict['source'] = source
                    edge_dict['source_layer'] = None
                
                # Extract target info
                if isinstance(target, tuple) and len(target) >= 2:
                    edge_dict['target'] = target[0]
                    edge_dict['target_layer'] = target[1]
                else:
                    edge_dict['target'] = target
                    edge_dict['target_layer'] = None
                
                # Get edge attributes
                if len(edge) >= 3 and isinstance(edge[2], dict):
                    if include_attributes:
                        edge_dict['attributes'] = dict(edge[2])
                    # Always preserve weight
                    edge_dict['weight'] = edge[2].get('weight', 1.0)
                else:
                    edge_dict['weight'] = 1.0
            
            edges.append(edge_dict)
    
    # Sort edges for stable ordering
    edges.sort(key=lambda e: (
        str(e.get('source_layer', '')),
        str(e['source']),
        str(e.get('target_layer', '')),
        str(e['target'])
    ))
    
    # Determine if network is directed
    directed = False
    if hasattr(network, 'directed'):
        directed = network.directed
    elif hasattr(network, 'core_network'):
        try:
            import networkx as nx
            directed = isinstance(network.core_network, (nx.DiGraph, nx.MultiDiGraph))
        except Exception:
            pass
    
    # Capture network-level metadata
    metadata = {}
    if hasattr(network, 'layers'):
        try:
            metadata['layers'] = sorted([str(layer) for layer in network.layers])
        except Exception:
            pass
    
    return NetworkCapture(
        nodes=nodes,
        edges=edges,
        directed=directed,
        metadata=metadata
    )


def restore_network(capture: NetworkCapture) -> Any:
    """Restore network from capture.
    
    Args:
        capture: NetworkCapture instance
        
    Returns:
        Multilayer network object
    """
    from py3plex.core import multinet
    
    # Create new network
    network = multinet.multi_layer_network(directed=capture.directed)
    
    # Add nodes
    node_dicts = []
    for node in capture.nodes:
        node_dict = {
            'source': node['id'],
            'type': node.get('layer', 'default')
        }
        # Add attributes if present
        if 'attributes' in node:
            node_dict.update(node['attributes'])
        node_dicts.append(node_dict)
    
    if node_dicts:
        network.add_nodes(node_dicts)
    
    # Add edges
    edge_dicts = []
    for edge in capture.edges:
        edge_dict = {
            'source': edge['source'],
            'target': edge['target'],
            'source_type': edge.get('source_layer', 'default'),
            'target_type': edge.get('target_layer', 'default'),
            'weight': edge.get('weight', 1.0)
        }
        # Add attributes if present
        if 'attributes' in edge:
            for k, v in edge['attributes'].items():
                if k != 'weight':  # Weight already handled
                    edge_dict[k] = v
        edge_dicts.append(edge_dict)
    
    if edge_dicts:
        network.add_edges(edge_dicts)
    
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
