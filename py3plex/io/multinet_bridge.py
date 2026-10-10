"""
Bridge between multi_layer_network and MultiLayerGraph schema.

This module provides conversion functions between py3plex's main network class
(multi_layer_network) and the I/O schema class (MultiLayerGraph).
"""

import json
import numpy as np
from typing import Any, Dict, Iterator, Tuple

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


def _iter_replica_edges(
    net: multi_layer_network,
) -> Iterator[Tuple[Any, Any, Any, Dict[str, Any]]]:
    """Yield each stored edge with its own key and data, including coupling."""
    graph = net.core_network
    if graph.is_multigraph():
        yield from graph.edges(keys=True, data=True)
    else:
        for source, target, data in graph.edges(data=True):
            yield source, target, 0, data


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
        
        # An uninitialized network is a valid empty export. Discover layers
        # directly from replicas: get_layers() also computes visualization layouts.
        if net.core_network is None:
            return graph

        layers = dict.fromkeys(layer for _, layer in net.get_nodes())
        for layer_id in layers:
            graph.add_layer(Layer(id=layer_id, attributes={}))

        # Get all node replicas (node_id, layer) with attributes
        # Store each (node, layer) pair as a separate node with layer in attributes
        replica_ids = {}
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
            
            # Keep familiar display IDs when unique, but disambiguate scalar
            # types and delimiter combinations with identical string forms.
            base_id = f"{node_id}@@@{layer}"
            composite_id = base_id
            suffix = len(graph.nodes)
            while composite_id in graph.nodes:
                composite_id = f"{base_id}@@@{suffix}"
                suffix += 1
            replica_ids[(node, layer)] = composite_id
            graph.add_node(Node(id=composite_id, attributes=node_attrs))
        
        # Read each individual edge rather than looking up the first edge
        # between two endpoints, which loses parallel-edge keys and attributes.
        for (src, src_layer), (dst, dst_layer), key, data in _iter_replica_edges(net):
            edge_attrs = dict(data)

            # Remove internal NetworkX attributes
            edge_attrs.pop('_edge_id', None)
            
            # Encode attributes to handle numpy arrays and complex types
            edge_attrs = _encode_attributes(edge_attrs)
            
            # Create composite IDs that match how we created nodes
            src_composite = replica_ids[(src, src_layer)]
            dst_composite = replica_ids[(dst, dst_layer)]
            
            graph.add_edge(Edge(
                src=src_composite,
                dst=dst_composite,
                src_layer=src_layer,
                dst_layer=dst_layer,
                key=key,
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
        node_ids = {}
        stored_layers = {}
        
        for node in graph.nodes.values():
            # Metadata contains the original scalar identity. Do not JSON-decode
            # strings such as "null" or "[1,2]", which are valid node names.
            if isinstance(node.id, str) and '@@@' in node.id:
                fallback_id, fallback_layer = node.id.split('@@@', 1)
            else:
                fallback_id, fallback_layer = node.id, 'default'
            node_id = node.attributes.get('__node_id__', fallback_id)
            layer = node.attributes.get('__layer__', fallback_layer)
            node_ids[node.id] = node_id
            if '__layer__' in node.attributes:
                stored_layers[node.id] = layer

            node_dict = {
                'source': node_id,
                'type': layer
            }
            
            # Add node attributes (excluding internal attributes)
            for key, value in node.attributes.items():
                if key not in ['__layer__', '__node_id__']:
                    node_dict[key] = _decode_attribute(value)
            
            nodes_to_add.append(node_dict)
        
        if nodes_to_add:
            net.add_nodes(nodes_to_add)
        
        # Add edges
        edges_to_add = []
        for edge in graph.edges:
            # Resolve endpoints through the same identities used for nodes.
            # Splitting composite strings creates extra string-valued replicas
            # for numeric IDs and truncates IDs containing the delimiter.
            edge_dict = {
                'source': node_ids[edge.src],
                'target': node_ids[edge.dst],
                'source_type': stored_layers.get(edge.src, edge.src_layer),
                'target_type': stored_layers.get(edge.dst, edge.dst_layer)
            }
            # Add edge attributes
            edge_dict.update(
                {
                    key: _decode_attribute(value)
                    for key, value in edge.attributes.items()
                }
            )
            # Preserve the schema's edge identity independently of attributes.
            edge_dict['key'] = edge.key
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
    metadata = {
        "py3plex_schema_version": "1.0",
        "py3plex_version": getattr(py3plex, "__version__", "unknown"),
        "network_type": net.network_type,
        "directed": net.directed,
        "attribute_type_manifest": {},
        "json_encoded_columns": [],
    }

    if hasattr(net, "coupling_weight"):
        metadata["coupling_weight"] = net.coupling_weight

    json_encoded = set()

    try:
        graph = multinet_to_multilayergraph(net)

        if net.core_network is None:
            return graph, metadata

        for node, layer in net.get_nodes():
            if not net.core_network.has_node((node, layer)):
                continue
            raw_attrs = dict(net.core_network.nodes[(node, layer)])
            for key, value in raw_attrs.items():
                _, needs_json = _encode_attribute(value, track_type=True)
                if needs_json:
                    json_encoded.add(f"node_{key}")
                manifest_key = f"node_{key}"
                metadata["attribute_type_manifest"].setdefault(
                    manifest_key, type(value).__name__
                )

        for _, _, _, data in _iter_replica_edges(net):
            raw_attrs = dict(data)
            raw_attrs.pop("_edge_id", None)
            for key, value in raw_attrs.items():
                _, needs_json = _encode_attribute(value, track_type=True)
                if needs_json:
                    json_encoded.add(f"edge_{key}")
                manifest_key = f"edge_{key}"
                metadata["attribute_type_manifest"].setdefault(
                    manifest_key, type(value).__name__
                )

        metadata["json_encoded_columns"] = sorted(json_encoded)
        return graph, metadata

    except Exception as e:
        raise ConversionError(
            f"Failed to convert multi_layer_network to MultiLayerGraph with metadata: {e}"
        )
