"""
Bridge between multi_layer_network and MultiLayerGraph schema.

This module provides conversion functions between py3plex's main network class
(multi_layer_network) and the I/O schema class (MultiLayerGraph).
"""

import json
import numpy as np
from typing import Any, Dict, List

import py3plex
from py3plex.core.multinet import multi_layer_network
from py3plex.exceptions import ConversionError

from .schema import Edge, Layer, MultiLayerGraph, Node


def _encode_attribute(value: Any, track_type: bool = False) -> Any:
    """
    Encode a single attribute value for JSON serialization.
    
    Handles numpy arrays, complex types, etc.
    
    Args:
        value: Attribute value to encode
        track_type: If True, return (encoded_value, needs_json_encoding)
        
    Returns:
        If track_type=False: encoded value
        If track_type=True: tuple of (encoded value, bool indicating if JSON encoding was used)
    """
    needs_json = False
    
    if value is None or isinstance(value, (int, float, bool, str)):
        encoded = value
    elif isinstance(value, (np.ndarray, np.generic)):
        # Convert numpy array to list
        encoded = value.tolist()
        needs_json = True
    elif isinstance(value, (dict, list, tuple, set)):
        # Convert complex types to JSON string
        encoded = json.dumps(value, sort_keys=True, default=_json_default)
        needs_json = True
    else:
        # Try to convert to string as fallback
        encoded = str(value)
    
    if track_type:
        return encoded, needs_json
    return encoded


def _json_default(obj):
    """JSON encoder for non-standard types."""
    if isinstance(obj, (np.ndarray, np.generic)):
        return obj.tolist()
    elif isinstance(obj, set):
        return list(obj)
    else:
        return str(obj)


def _encode_attributes(attrs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Encode all attributes in a dictionary for storage.
    """
    if not attrs:
        return {}
    return {key: _encode_attribute(value) for key, value in attrs.items()}


def _decode_attribute(value: Any) -> Any:
    """
    Decode an attribute that was encoded with _encode_attribute.
    Handles JSON-encoded complex types.
    """
    if isinstance(value, str):
        # Try to parse as JSON if it looks like JSON
        if value.startswith(('[', '{', '"')) or value in ('null', 'true', 'false'):
            try:
                return json.loads(value)
            except (json.JSONDecodeError, ValueError):
                pass
    return value


def multinet_to_multilayergraph(net: multi_layer_network) -> MultiLayerGraph:
    """
    Convert multi_layer_network to MultiLayerGraph schema.
    
    Preserves:
    - Node replicas (node_id, layer) with attributes
    - Edge replicas with attributes
    - Directedness
    - Network type (multilayer vs multiplex)
    - Coupling information
    
    Note: Since MultiLayerGraph schema doesn't natively support node replicas with
    per-layer attributes, we store the layer information in a special __layer__ attribute
    and create separate Node instances for each replica.
    
    Args:
        net: multi_layer_network instance
        
    Returns:
        MultiLayerGraph instance
        
    Raises:
        ConversionError: If conversion fails
    """
    try:
        import py3plex
        
        # Create graph with comprehensive metadata
        graph_attrs = {
            'network_type': net.network_type,
            'py3plex_version': py3plex.__version__ if hasattr(py3plex, '__version__') else 'unknown',
            'py3plex_schema_version': '1.0',
        }
        
        # Add coupling weight if it exists
        if hasattr(net, 'coupling_weight'):
            graph_attrs['coupling_weight'] = net.coupling_weight
            
        graph = MultiLayerGraph(
            directed=net.directed,
            attributes=graph_attrs
        )
        
        # Get all layers first
        # get_layers() returns a tuple: (layer_list, graph_list, dict)
        layers_info = net.get_layers()
        if isinstance(layers_info, tuple) and len(layers_info) > 0:
            layers = layers_info[0]  # Extract layer list
        else:
            layers = layers_info
        
        for layer_id in layers:
            # Layer attributes (currently none by default, but structure supports it)
            graph.add_layer(Layer(id=layer_id, attributes={}))
        
        # Get all node replicas (node_id, layer) with attributes
        # Store each (node, layer) pair as a separate node with layer in attributes
        for node, layer in net.get_nodes():
            node_id = node
            # Get node attributes if available
            node_attrs = {}
            if net.core_network.has_node((node, layer)):
                node_attrs = dict(net.core_network.nodes[(node, layer)])
                # Encode attributes to handle numpy arrays and complex types
                node_attrs = _encode_attributes(node_attrs)
            
            # Store original node ID and layer separately in attributes
            node_attrs['__node_id__'] = _encode_attribute(node_id)
            node_attrs['__layer__'] = layer
            
            # Create unique string ID for this replica: "node_id@@@layer"
            # Use @@@ as delimiter (unlikely to appear in real node IDs)
            composite_id = f"{node_id}@@@{layer}"
            graph.add_node(Node(id=composite_id, attributes=node_attrs))
        
        # Get all edges with attributes
        # get_edges() returns generator of tuples: ((src, src_layer), (dst, dst_layer))
        for edge_tuple in net.get_edges():
            (src, src_layer), (dst, dst_layer) = edge_tuple
            
            # Get edge attributes
            edge_attrs = {}
            if net.core_network.has_edge((src, src_layer), (dst, dst_layer)):
                # Get all edge data (there might be multiple edges with different keys)
                edge_data_dict = net.core_network.get_edge_data((src, src_layer), (dst, dst_layer))
                # For multigraphs, get_edge_data returns dict of {key: data}
                if isinstance(edge_data_dict, dict):
                    # Take the first edge's data (key 0)
                    if 0 in edge_data_dict:
                        edge_attrs = dict(edge_data_dict[0])
                    else:
                        # Get first available key
                        first_key = next(iter(edge_data_dict.keys()))
                        edge_attrs = dict(edge_data_dict[first_key])
                else:
                    edge_attrs = dict(edge_data_dict) if edge_data_dict else {}
            
            # Remove internal NetworkX attributes
            edge_attrs.pop('_edge_id', None)
            
            # Encode attributes to handle numpy arrays and complex types
            edge_attrs = _encode_attributes(edge_attrs)
            
            # Create composite IDs that match how we created nodes
            src_composite = f"{src}@@@{src_layer}"
            dst_composite = f"{dst}@@@{dst_layer}"
            
            graph.add_edge(Edge(
                src=src_composite,
                dst=dst_composite,
                src_layer=src_layer,
                dst_layer=dst_layer,
                key=0,
                attributes=edge_attrs
            ))
        
        return graph
        
    except Exception as e:
        raise ConversionError(
            f"Failed to convert multi_layer_network to MultiLayerGraph: {e}"
        )


def multilayergraph_to_multinet(graph: MultiLayerGraph) -> multi_layer_network:
    """
    Convert MultiLayerGraph schema to multi_layer_network.
    
    Reconstructs the network with all attributes preserved.
    
    Args:
        graph: MultiLayerGraph instance
        
    Returns:
        multi_layer_network instance
        
    Raises:
        ConversionError: If conversion fails
    """
    try:
        # Extract network type from attributes
        network_type = graph.attributes.get('network_type', 'multilayer')
        coupling_weight = graph.attributes.get('coupling_weight', 1)
        
        # Create network
        net = multi_layer_network(
            network_type=network_type,
            directed=graph.directed,
            coupling_weight=coupling_weight
        )
        
        # Add nodes
        # Nodes are stored with composite IDs (node_id, layer) and __layer__ attribute
        # We need to extract both the node ID and layer from each node
        nodes_to_add = []
        
        for node in graph.nodes.values():
            # Extract node_id and layer from composite ID
            if isinstance(node.id, str) and '@@@' in node.id:
                # Parse composite ID
                parts = node.id.split('@@@', 1)
                node_id, layer = parts[0], parts[1]
                # Try to decode node_id if it was encoded
                if '__node_id__' in node.attributes:
                    node_id = _decode_attribute(node.attributes['__node_id__'])
            else:
                # Fallback: check for stored attributes
                node_id = _decode_attribute(node.attributes.get('__node_id__', node.id))
                layer = node.attributes.get('__layer__', 'default')
            
            node_dict = {
                'source': node_id,
                'type': layer
            }
            
            # Add node attributes (excluding internal attributes)
            for key, value in node.attributes.items():
                if key not in ['__layer__', '__node_id__']:
                    node_dict[key] = value
            
            nodes_to_add.append(node_dict)
        
        if nodes_to_add:
            net.add_nodes(nodes_to_add)
        
        # Add edges
        edges_to_add = []
        for edge in graph.edges:
            # Extract actual node IDs from composite IDs
            if isinstance(edge.src, str) and '@@@' in edge.src:
                src_id = edge.src.split('@@@', 1)[0]
            else:
                src_id = edge.src
            
            if isinstance(edge.dst, str) and '@@@' in edge.dst:
                dst_id = edge.dst.split('@@@', 1)[0]
            else:
                dst_id = edge.dst
            
            edge_dict = {
                'source': src_id,
                'target': dst_id,
                'source_type': edge.src_layer,
                'target_type': edge.dst_layer
            }
            # Add edge attributes
            edge_dict.update(edge.attributes)
            edges_to_add.append(edge_dict)
        
        if edges_to_add:
            net.add_edges(edges_to_add)
        
        return net
        
    except Exception as e:
        raise ConversionError(
            f"Failed to convert MultiLayerGraph to multi_layer_network: {e}"
        )


def multinet_to_multilayergraph_with_metadata(net: multi_layer_network) -> tuple:
    """
    Convert multi_layer_network to MultiLayerGraph schema with rich metadata.
    
    This version returns both the graph and comprehensive metadata for roundtrip preservation.
    
    Args:
        net: multi_layer_network instance
        
    Returns:
        Tuple of (MultiLayerGraph, metadata_dict)
        
    Metadata includes:
        - py3plex_schema_version: Schema version (currently '1.0')
        - py3plex_version: Library version
        - network_type: 'multilayer' or 'multiplex'
        - directed: Boolean
        - attribute_type_manifest: Dict mapping attr names to original type names
        - json_encoded_columns: List of attribute names that were JSON-encoded
        
    Raises:
        ConversionError: If conversion fails
    """
    # Build metadata
    metadata = {
        'py3plex_schema_version': '1.0',
        'py3plex_version': getattr(py3plex, '__version__', 'unknown'),
        'network_type': net.network_type,
        'directed': net.directed,
        'attribute_type_manifest': {},
        'json_encoded_columns': []
    }
    
    # Track coupling if present
    if hasattr(net, 'coupling_weight'):
        metadata['coupling_weight'] = net.coupling_weight
    
    # Track which attributes were JSON-encoded
    json_encoded = set()
    
    try:
        # Create graph with metadata
        graph_attrs = {
            'network_type': net.network_type,
        }
        
        # Add coupling weight if it exists
        if hasattr(net, 'coupling_weight'):
            graph_attrs['coupling_weight'] = net.coupling_weight
            
        graph = MultiLayerGraph(
            directed=net.directed,
            attributes=graph_attrs
        )
        
        # Handle empty networks
        if net.core_network is None:
            # Empty network - return empty graph
            metadata = {
                "py3plex_schema_version": "1.0",
                "py3plex_version": py3plex.__version__,
                "directed": net.directed,
                "network_type": getattr(net, 'network_type', 'multilayer'),
            }
            return graph, metadata
        
        # Get all layers first
        try:
            layers_info = net.get_layers()
            if isinstance(layers_info, tuple) and len(layers_info) > 0:
                layers = layers_info[0]  # Extract layer list
            else:
                layers = layers_info
        except (AttributeError, TypeError) as e:
            # Fallback: extract layers from nodes if possible
            layers = set()
            for node, layer in net.get_nodes():
                layers.add(layer)
            layers = list(layers)
        
        for layer_id in layers:
            graph.add_layer(Layer(id=layer_id, attributes={}))
        
        # Get all node replicas with attributes
        nodes_seen = set()
        for node, layer in net.get_nodes():
            node_id = node
            node_attrs = {}
            if net.core_network.has_node((node, layer)):
                raw_attrs = dict(net.core_network.nodes[(node, layer)])
                # Encode attributes and track types
                for key, value in raw_attrs.items():
                    encoded, needs_json = _encode_attribute(value, track_type=True)
                    node_attrs[key] = encoded
                    
                    # Track JSON encoding
                    if needs_json:
                        json_encoded.add(f'node_{key}')
                    
                    # Track original type (use full name once)
                    manifest_key = f'node_{key}'
                    if manifest_key not in metadata['attribute_type_manifest']:
                        metadata['attribute_type_manifest'][manifest_key] = type(value).__name__
                
            if node_id not in nodes_seen:
                graph.add_node(Node(id=node_id, attributes=node_attrs))
                nodes_seen.add(node_id)
        
        # Get all edges with attributes
        for edge_tuple in net.get_edges():
            (src, src_layer), (dst, dst_layer) = edge_tuple
            
            edge_attrs = {}
            if net.core_network.has_edge((src, src_layer), (dst, dst_layer)):
                edge_data_dict = net.core_network.get_edge_data((src, src_layer), (dst, dst_layer))
                
                # For multigraphs, get_edge_data returns dict of {key: data}
                if isinstance(edge_data_dict, dict):
                    if 0 in edge_data_dict:
                        raw_attrs = dict(edge_data_dict[0])
                    else:
                        first_key = next(iter(edge_data_dict.keys()))
                        raw_attrs = dict(edge_data_dict[first_key])
                else:
                    raw_attrs = dict(edge_data_dict) if edge_data_dict else {}
                
                # Remove internal NetworkX attributes
                raw_attrs.pop('_edge_id', None)
                
                # Encode attributes and track types
                for key, value in raw_attrs.items():
                    encoded, needs_json = _encode_attribute(value, track_type=True)
                    edge_attrs[key] = encoded
                    
                    # Track JSON encoding
                    if needs_json:
                        json_encoded.add(f'edge_{key}')
                    
                    # Track original type
                    manifest_key = f'edge_{key}'
                    if manifest_key not in metadata['attribute_type_manifest']:
                        metadata['attribute_type_manifest'][manifest_key] = type(value).__name__
            
            graph.add_edge(Edge(
                src=src,
                dst=dst,
                src_layer=src_layer,
                dst_layer=dst_layer,
                key=0,
                attributes=edge_attrs
            ))
        
        metadata['json_encoded_columns'] = sorted(list(json_encoded))
        
        return graph, metadata
        
    except Exception as e:
        raise ConversionError(
            f"Failed to convert multi_layer_network to MultiLayerGraph with metadata: {e}"
        )
