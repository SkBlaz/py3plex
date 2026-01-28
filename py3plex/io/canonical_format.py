"""
Canonical table format for zero-loss multilayer network interchange.

This module implements the canonical schema for lossless roundtrip:
- NODES table: node (ID), layer (string), plus optional attributes
- EDGES table: source, target, source_layer, target_layer, plus optional attributes
"""

import json
import numpy as np
import pandas as pd
from typing import Tuple, Any, Dict
import py3plex

from py3plex.core.multinet import multi_layer_network
from py3plex.exceptions import Py3plexIOError


class ConversionError(Py3plexIOError):
    """Error during network conversion."""
    pass


def _encode_attribute(value: Any) -> Any:
    """
    Encode a single attribute value for serialization.
    
    Handles:
    - numpy arrays → list
    - numpy scalars → Python scalars
    - complex types (dict/list/set/tuple) → JSON string
    - scalars → unchanged
    """
    # Handle numpy types
    if isinstance(value, np.ndarray):
        return value.tolist()
    elif isinstance(value, (np.integer, np.floating)):
        return value.item()
    elif isinstance(value, np.bool_):
        return bool(value)
    
    # Handle complex types with JSON encoding
    elif isinstance(value, (dict, list, set, tuple)):
        if isinstance(value, set):
            value = list(value)
        return json.dumps(value, sort_keys=True, ensure_ascii=False)
    
    # Scalars pass through
    return value


def _decode_attribute(value: Any) -> Any:
    """
    Decode an attribute value from serialization.
    
    Attempts to parse JSON strings back to original types.
    """
    if isinstance(value, str):
        # Try to parse as JSON
        if value.startswith(('[', '{', '"')):
            try:
                return json.loads(value)
            except (json.JSONDecodeError, ValueError):
                pass
    return value


def _encode_attributes(attrs: Dict[str, Any]) -> Dict[str, Any]:
    """Encode all attributes in a dictionary."""
    return {k: _encode_attribute(v) for k, v in attrs.items()}


def _decode_attributes(attrs: Dict[str, Any]) -> Dict[str, Any]:
    """Decode all attributes in a dictionary."""
    return {k: _decode_attribute(v) for k, v in attrs.items()}


def network_to_tables(net: multi_layer_network) -> Tuple[pd.DataFrame, pd.DataFrame, dict]:
    """
    Convert multi_layer_network to canonical table format.
    
    Returns NODES and EDGES tables with all multilayer identity preserved.
    
    Canonical Schema:
    - NODES: node (ID), layer (string), plus optional attributes
    - EDGES: source, target, source_layer, target_layer, plus optional attributes
    
    Args:
        net: multi_layer_network instance
        
    Returns:
        Tuple of (nodes_df, edges_df, metadata_dict)
        
    Raises:
        ConversionError: If conversion fails
    """
    try:
        # Build nodes table
        nodes_data = []
        for node_tuple in net.get_nodes():
            if isinstance(node_tuple, tuple) and len(node_tuple) >= 2:
                node_id, layer = node_tuple[0], node_tuple[1]
            else:
                # Single-layer network
                node_id = node_tuple
                layer = 'default'
            
            # Get node attributes if they exist
            node_attrs = {}
            if net.core_network.has_node((node_id, layer)):
                node_attrs = dict(net.core_network.nodes[(node_id, layer)])
                # Encode attributes to handle numpy arrays and complex types
                node_attrs = _encode_attributes(node_attrs)
            
            # Create row with node, layer, and attributes
            row = {'node': node_id, 'layer': layer}
            row.update(node_attrs)
            nodes_data.append(row)
        
        nodes_df = pd.DataFrame(nodes_data) if nodes_data else pd.DataFrame(columns=['node', 'layer'])
        
        # Build edges table
        edges_data = []
        for edge_tuple in net.get_edges():
            if len(edge_tuple) >= 2:
                src_tuple, dst_tuple = edge_tuple[0], edge_tuple[1]
                
                # Extract node IDs and layers
                if isinstance(src_tuple, tuple) and len(src_tuple) >= 2:
                    src, src_layer = src_tuple[0], src_tuple[1]
                else:
                    src = src_tuple
                    src_layer = 'default'
                    
                if isinstance(dst_tuple, tuple) and len(dst_tuple) >= 2:
                    dst, dst_layer = dst_tuple[0], dst_tuple[1]
                else:
                    dst = dst_tuple
                    dst_layer = 'default'
                
                # Get edge attributes
                edge_attrs = {}
                if net.core_network.has_edge((src, src_layer), (dst, dst_layer)):
                    # MultiGraph may have multiple edges
                    edge_data = net.core_network.get_edge_data((src, src_layer), (dst, dst_layer))
                    if edge_data:
                        edge_attrs = dict(edge_data.get(0, {}))
                        edge_attrs = _encode_attributes(edge_attrs)
                
                # Create row
                row = {
                    'source': src,
                    'target': dst,
                    'source_layer': src_layer,
                    'target_layer': dst_layer
                }
                row.update(edge_attrs)
                edges_data.append(row)
        
        edges_df = pd.DataFrame(edges_data) if edges_data else pd.DataFrame(
            columns=['source', 'target', 'source_layer', 'target_layer']
        )
        
        # Build metadata
        metadata = {
            'schema_version': '1.0',
            'py3plex_version': py3plex.__version__,
            'network_type': getattr(net, 'network_type', 'multilayer'),
            'directed': net.directed,
            'coupling_weight': getattr(net, 'coupling_weight', 1),
            'node_count': len(nodes_df),
            'edge_count': len(edges_df),
            'layer_count': len(nodes_df['layer'].unique()) if not nodes_df.empty else 0,
            'layers': sorted(nodes_df['layer'].unique().tolist()) if not nodes_df.empty else []
        }
        
        return nodes_df, edges_df, metadata
        
    except Exception as e:
        raise ConversionError(
            f"Failed to convert multi_layer_network to tables: {e}"
        )


def tables_to_network(
    nodes_df: pd.DataFrame,
    edges_df: pd.DataFrame,
    metadata: dict
) -> multi_layer_network:
    """
    Convert canonical tables back to multi_layer_network.
    
    Args:
        nodes_df: DataFrame with columns: node, layer, plus attributes
        edges_df: DataFrame with columns: source, target, source_layer, target_layer, plus attributes
        metadata: Network metadata dict
        
    Returns:
        multi_layer_network instance
        
    Raises:
        ConversionError: If conversion fails
    """
    try:
        # Extract network parameters from metadata
        network_type = metadata.get('network_type', 'multilayer')
        directed = metadata.get('directed', False)
        coupling_weight = metadata.get('coupling_weight', 1)
        
        # Create network
        net = multi_layer_network(
            network_type=network_type,
            directed=directed,
            coupling_weight=coupling_weight
        )
        
        # Add nodes from NODES table
        if not nodes_df.empty:
            nodes_to_add = []
            for _, row in nodes_df.iterrows():
                node_id = row['node']
                layer = row['layer']
                
                # Create node dict
                node_dict = {
                    'source': node_id,
                    'type': layer
                }
                
                # Add attributes (excluding the schema columns)
                for col in nodes_df.columns:
                    if col not in ['node', 'layer']:
                        value = row[col]
                        # Skip NaN values (handle arrays/lists separately)
                        try:
                            is_na = pd.isna(value)
                            # For scalar values, is_na is a boolean
                            if isinstance(is_na, bool):
                                skip = is_na
                            else:
                                # For arrays, check if any element is NA
                                skip = False
                        except (TypeError, ValueError):
                            # For types that don't support pd.isna, assume not NA
                            skip = False
                        
                        if not skip:
                            node_dict[col] = _decode_attribute(value)
                
                nodes_to_add.append(node_dict)
            
            if nodes_to_add:
                net.add_nodes(nodes_to_add)
        
        # Add edges from EDGES table
        if not edges_df.empty:
            edges_to_add = []
            for _, row in edges_df.iterrows():
                edge_dict = {
                    'source': row['source'],
                    'target': row['target'],
                    'source_type': row['source_layer'],
                    'target_type': row['target_layer']
                }
                
                # Add attributes (excluding schema columns)
                for col in edges_df.columns:
                    if col not in ['source', 'target', 'source_layer', 'target_layer']:
                        value = row[col]
                        # Skip NaN values (handle arrays/lists separately)
                        try:
                            is_na = pd.isna(value)
                            # For scalar values, is_na is a boolean
                            if isinstance(is_na, bool):
                                skip = is_na
                            else:
                                # For arrays, check if any element is NA
                                skip = False
                        except (TypeError, ValueError):
                            # For types that don't support pd.isna, assume not NA
                            skip = False
                        
                        if not skip:
                            edge_dict[col] = _decode_attribute(value)
                
                edges_to_add.append(edge_dict)
            
            if edges_to_add:
                net.add_edges(edges_to_add)
        
        return net
        
    except Exception as e:
        raise ConversionError(
            f"Failed to convert tables to multi_layer_network: {e}"
        )
