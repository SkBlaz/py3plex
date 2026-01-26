"""
Bridge between multi_layer_network and MultiLayerGraph schema.

This module provides conversion functions between py3plex's main network class
(multi_layer_network) and the I/O schema class (MultiLayerGraph).
"""

import json
import numpy as np
from typing import Any, Dict, List

from py3plex.core.multinet import multi_layer_network
from py3plex.exceptions import ConversionError

from .schema import Edge, Layer, MultiLayerGraph, Node


def _encode_attribute(value: Any) -> Any:
    """
    Encode a single attribute value for JSON serialization.
    
    Handles numpy arrays, complex types, etc.
    """
    if value is None or isinstance(value, (int, float, bool, str)):
        return value
    elif isinstance(value, (np.ndarray, np.generic)):
        # Convert numpy array to list
        return value.tolist()
    elif isinstance(value, (dict, list, tuple, set)):
        # Convert complex types to JSON string
        return json.dumps(value, sort_keys=True, default=_json_default)
    else:
        # Try to convert to string as fallback
        return str(value)


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


def multinet_to_multilayergraph(net: multi_layer_network) -> MultiLayerGraph:
    """
    Convert multi_layer_network to MultiLayerGraph schema.
    
    Preserves:
    - Node replicas (node_id, layer) with attributes
    - Edge replicas with attributes
    - Directedness
    - Network type (multilayer vs multiplex)
    - Coupling information
    
    Args:
        net: multi_layer_network instance
        
    Returns:
        MultiLayerGraph instance
        
    Raises:
        ConversionError: If conversion fails
    """
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
        nodes_seen = set()
        for node, layer in net.get_nodes():
            node_id = node
            # Get node attributes if available
            node_attrs = {}
            if net.core_network.has_node((node, layer)):
                node_attrs = dict(net.core_network.nodes[(node, layer)])
                # Encode attributes to handle numpy arrays and complex types
                node_attrs = _encode_attributes(node_attrs)
                
            # MultiLayerGraph uses node id only, not (node, layer)
            # We need to create separate node instances for each replica
            # Create a unique key for this node (not layer-specific in MultiLayerGraph)
            if node_id not in nodes_seen:
                # First time seeing this node, add it with attributes
                graph.add_node(Node(id=node_id, attributes=node_attrs))
                nodes_seen.add(node_id)
        
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
            
            graph.add_edge(Edge(
                src=src,
                dst=dst,
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
        # In MultiLayerGraph, nodes don't have layer info directly
        # We need to infer from edges which layers each node appears in
        node_layers: Dict[Any, List[Any]] = {}
        
        # Collect layer information from edges
        for edge in graph.edges:
            if edge.src not in node_layers:
                node_layers[edge.src] = []
            if edge.src_layer not in node_layers[edge.src]:
                node_layers[edge.src].append(edge.src_layer)
                
            if edge.dst not in node_layers:
                node_layers[edge.dst] = []
            if edge.dst_layer not in node_layers[edge.dst]:
                node_layers[edge.dst].append(edge.dst_layer)
        
        # Also add nodes that might not have edges
        for node in graph.nodes.values():
            if node.id not in node_layers:
                # Node with no edges - need to assign to at least one layer
                # Use first available layer or create a default one
                if graph.layers:
                    node_layers[node.id] = [next(iter(graph.layers.keys()))]
                else:
                    # No layers defined, create a default one
                    node_layers[node.id] = ['default']
        
        # Add node replicas
        nodes_to_add = []
        for node_id, layers in node_layers.items():
            for layer_id in layers:
                node_dict = {
                    'source': node_id,
                    'type': layer_id
                }
                # Add node attributes if available
                if node_id in graph.nodes:
                    node_dict.update(graph.nodes[node_id].attributes)
                nodes_to_add.append(node_dict)
        
        if nodes_to_add:
            net.add_nodes(nodes_to_add)
        
        # Add edges
        edges_to_add = []
        for edge in graph.edges:
            edge_dict = {
                'source': edge.src,
                'target': edge.dst,
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
