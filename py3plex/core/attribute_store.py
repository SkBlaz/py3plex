"""
Attribute store backend for efficient node/edge/metadata storage and querying.

This module provides a high-performance storage backend using Polars DataFrames
to store node attributes, edge attributes, and metadata. This replaces direct
NetworkX graph access for attribute queries, providing faster indexing and filtering.

Requirements:
    - polars >= 0.15.0 (for DataFrame operations and diagonal_relaxed concat)

Note:
    Node IDs are converted to strings for consistent storage. Supported types include
    strings, integers, and any object with a meaningful string representation.
"""

from typing import Any, Dict, List, Optional, Set, Tuple, Union

try:
    import polars as pl
except ImportError:
    raise ImportError(
        "Polars is required for AttributeStore backend. "
        "Install it with: pip install polars"
    )


class AttributeStore:
    """
    High-performance attribute storage backend using Polars DataFrames.
    
    This class manages node attributes, edge attributes, and network metadata
    using Polars DataFrames for efficient querying, filtering, and indexing.
    
    Attributes:
        nodes_df: Polars DataFrame storing node attributes with columns:
            - node_id: Node identifier (Any)
            - layer: Layer identifier (str)
            - attributes: Dict of additional node attributes
        edges_df: Polars DataFrame storing edge attributes with columns:
            - source_id: Source node identifier
            - source_layer: Source layer identifier
            - target_id: Target node identifier
            - target_layer: Target layer identifier
            - weight: Edge weight (float, default 1.0)
            - edge_type: Edge type/label (str, default 'default')
            - attributes: Dict of additional edge attributes
        metadata: Dict storing network-level metadata
    """
    
    def __init__(self):
        """Initialize an empty AttributeStore."""
        # Initialize empty DataFrames with proper schema
        self.nodes_df = pl.DataFrame({
            'node_id': pl.Series([], dtype=pl.String),
            'layer': pl.Series([], dtype=pl.String),
        })
        
        self.edges_df = pl.DataFrame({
            'source_id': pl.Series([], dtype=pl.String),
            'source_layer': pl.Series([], dtype=pl.String),
            'target_id': pl.Series([], dtype=pl.String),
            'target_layer': pl.Series([], dtype=pl.String),
            'weight': pl.Series([], dtype=pl.Float64),
            'edge_type': pl.Series([], dtype=pl.String),
        })
        
        self.metadata: Dict[str, Any] = {}
        
        # Cache for performance
        self._node_cache: Dict[Tuple[str, str], Dict[str, Any]] = {}
        self._edge_cache: Dict[Tuple[Tuple[str, str], Tuple[str, str]], Dict[str, Any]] = {}
        self._cache_valid = True
    
    # =========================================================================
    # Node Operations
    # =========================================================================
    
    def add_node(self, node_id: str, layer: str, **attributes) -> None:
        """
        Add a single node with attributes.
        
        Args:
            node_id: Node identifier (string, int, or any object with string representation)
            layer: Layer identifier
            **attributes: Additional node attributes
            
        Note:
            Node IDs are converted to strings for consistent storage. This works
            for strings, integers, and objects with __str__ methods. Complex objects
            without meaningful string representations may not work as expected.
        """
        # Convert node_id to string for consistent storage
        node_id_str = str(node_id)
        
        # Create row data
        row_data = {
            'node_id': [node_id_str],
            'layer': [layer],
        }
        
        # Add any additional attributes as columns
        for key, value in attributes.items():
            row_data[key] = [value]
        
        # Create new row and append
        new_row = pl.DataFrame(row_data)
        
        # Use diagonal_relaxed concatenation for schema evolution
        # This allows adding new columns dynamically without schema conflicts
        if len(self.nodes_df) == 0:
            self.nodes_df = new_row
        else:
            self.nodes_df = pl.concat([self.nodes_df, new_row], how="diagonal_relaxed")
        self._cache_valid = False
    
    def add_nodes_batch(self, nodes: List[Dict[str, Any]]) -> None:
        """
        Add multiple nodes efficiently in batch.
        
        Args:
            nodes: List of node dictionaries with 'node_id', 'layer', and optional attributes
        """
        if not nodes:
            return
        
        # Convert all node_ids to strings
        for node in nodes:
            node['node_id'] = str(node.get('node_id', node.get('source', '')))
            node['layer'] = str(node.get('layer', node.get('type', '')))
        
        # Create DataFrame from nodes
        new_nodes_df = pl.DataFrame(nodes)
        
        # Ensure required columns exist
        if 'node_id' not in new_nodes_df.columns and 'source' in new_nodes_df.columns:
            new_nodes_df = new_nodes_df.rename({'source': 'node_id'})
        if 'layer' not in new_nodes_df.columns and 'type' in new_nodes_df.columns:
            new_nodes_df = new_nodes_df.rename({'type': 'layer'})
        
        # Align columns using diagonal_relaxed for better schema handling
        if len(self.nodes_df) == 0:
            self.nodes_df = new_nodes_df
        else:
            self.nodes_df = pl.concat([self.nodes_df, new_nodes_df], how="diagonal_relaxed")
        self._cache_valid = False
    
    def remove_node(self, node_id: str, layer: str) -> None:
        """
        Remove a node.
        
        Args:
            node_id: Node identifier
            layer: Layer identifier
        """
        node_id_str = str(node_id)
        self.nodes_df = self.nodes_df.filter(
            ~((pl.col('node_id') == node_id_str) & (pl.col('layer') == layer))
        )
        self._cache_valid = False
    
    def has_node(self, node_id: str, layer: str) -> bool:
        """
        Check if a node exists.
        
        Args:
            node_id: Node identifier
            layer: Layer identifier
            
        Returns:
            True if node exists, False otherwise
        """
        node_id_str = str(node_id)
        result = self.nodes_df.filter(
            (pl.col('node_id') == node_id_str) & (pl.col('layer') == layer)
        )
        return len(result) > 0
    
    def get_node_attributes(self, node_id: str, layer: str) -> Optional[Dict[str, Any]]:
        """
        Get all attributes for a node.
        
        Args:
            node_id: Node identifier
            layer: Layer identifier
            
        Returns:
            Dictionary of node attributes or None if node doesn't exist
        """
        node_id_str = str(node_id)
        result = self.nodes_df.filter(
            (pl.col('node_id') == node_id_str) & (pl.col('layer') == layer)
        )
        
        if len(result) == 0:
            return None
        
        return result.to_dicts()[0]
    
    def get_all_nodes(self) -> List[Tuple[str, str]]:
        """
        Get all nodes as (node_id, layer) tuples.
        
        Returns:
            List of (node_id, layer) tuples
        """
        return [(row['node_id'], row['layer']) 
                for row in self.nodes_df.select(['node_id', 'layer']).to_dicts()]
    
    def get_nodes_in_layer(self, layer: str) -> List[str]:
        """
        Get all node IDs in a specific layer.
        
        Args:
            layer: Layer identifier
            
        Returns:
            List of node IDs
        """
        result = self.nodes_df.filter(pl.col('layer') == layer)
        return result['node_id'].to_list()
    
    def get_unique_layers(self) -> Set[str]:
        """
        Get all unique layer identifiers.
        
        Returns:
            Set of layer identifiers
        """
        return set(self.nodes_df['layer'].unique().to_list())
    
    def get_unique_node_ids(self) -> Set[str]:
        """
        Get all unique node IDs across all layers.
        
        Returns:
            Set of node IDs
        """
        return set(self.nodes_df['node_id'].unique().to_list())
    
    # =========================================================================
    # Edge Operations
    # =========================================================================
    
    def add_edge(self, source_id: str, source_layer: str,
                 target_id: str, target_layer: str,
                 weight: float = 1.0, edge_type: str = 'default',
                 **attributes) -> None:
        """
        Add a single edge with attributes.
        
        Args:
            source_id: Source node identifier
            source_layer: Source layer identifier
            target_id: Target node identifier
            target_layer: Target layer identifier
            weight: Edge weight (default 1.0)
            edge_type: Edge type/label (default 'default')
            **attributes: Additional edge attributes
        """
        # Convert to strings
        source_id_str = str(source_id)
        target_id_str = str(target_id)
        
        row_data = {
            'source_id': [source_id_str],
            'source_layer': [source_layer],
            'target_id': [target_id_str],
            'target_layer': [target_layer],
            'weight': [weight],
            'edge_type': [edge_type],
        }
        
        # Add any additional attributes
        for key, value in attributes.items():
            row_data[key] = [value]
        
        new_row = pl.DataFrame(row_data)
        
        # Align columns using diagonal_relaxed
        if len(self.edges_df) == 0:
            self.edges_df = new_row
        else:
            self.edges_df = pl.concat([self.edges_df, new_row], how="diagonal_relaxed")
        self._cache_valid = False
    
    def add_edges_batch(self, edges: List[Dict[str, Any]]) -> None:
        """
        Add multiple edges efficiently in batch.
        
        Args:
            edges: List of edge dictionaries with source, target, layer info, and optional attributes
        """
        if not edges:
            return
        
        # Normalize edge dictionaries
        normalized_edges = []
        for edge in edges:
            normalized = {
                'source_id': str(edge.get('source_id', edge.get('source', ''))),
                'source_layer': str(edge.get('source_layer', edge.get('source_type', ''))),
                'target_id': str(edge.get('target_id', edge.get('target', ''))),
                'target_layer': str(edge.get('target_layer', edge.get('target_type', ''))),
                'weight': float(edge.get('weight', 1.0)),
                'edge_type': str(edge.get('edge_type', edge.get('type', 'default'))),
            }
            # Add any other attributes
            for key, value in edge.items():
                if key not in ['source', 'target', 'source_type', 'target_type', 
                             'source_id', 'target_id', 'source_layer', 'target_layer',
                             'weight', 'type', 'edge_type']:
                    normalized[key] = value
            normalized_edges.append(normalized)
        
        new_edges_df = pl.DataFrame(normalized_edges)
        
        # Align columns using diagonal_relaxed
        if len(self.edges_df) == 0:
            self.edges_df = new_edges_df
        else:
            self.edges_df = pl.concat([self.edges_df, new_edges_df], how="diagonal_relaxed")
        self._cache_valid = False
    
    def remove_edge(self, source_id: str, source_layer: str,
                   target_id: str, target_layer: str) -> None:
        """
        Remove an edge.
        
        Args:
            source_id: Source node identifier
            source_layer: Source layer identifier
            target_id: Target node identifier
            target_layer: Target layer identifier
        """
        source_id_str = str(source_id)
        target_id_str = str(target_id)
        
        self.edges_df = self.edges_df.filter(
            ~((pl.col('source_id') == source_id_str) & 
              (pl.col('source_layer') == source_layer) &
              (pl.col('target_id') == target_id_str) &
              (pl.col('target_layer') == target_layer))
        )
        self._cache_valid = False
    
    def has_edge(self, source_id: str, source_layer: str,
                 target_id: str, target_layer: str) -> bool:
        """
        Check if an edge exists.
        
        Args:
            source_id: Source node identifier
            source_layer: Source layer identifier
            target_id: Target node identifier
            target_layer: Target layer identifier
            
        Returns:
            True if edge exists, False otherwise
        """
        source_id_str = str(source_id)
        target_id_str = str(target_id)
        
        result = self.edges_df.filter(
            (pl.col('source_id') == source_id_str) & 
            (pl.col('source_layer') == source_layer) &
            (pl.col('target_id') == target_id_str) &
            (pl.col('target_layer') == target_layer)
        )
        return len(result) > 0
    
    def get_edge_attributes(self, source_id: str, source_layer: str,
                           target_id: str, target_layer: str) -> Optional[Dict[str, Any]]:
        """
        Get all attributes for an edge.
        
        Args:
            source_id: Source node identifier
            source_layer: Source layer identifier
            target_id: Target node identifier
            target_layer: Target layer identifier
            
        Returns:
            Dictionary of edge attributes or None if edge doesn't exist
        """
        source_id_str = str(source_id)
        target_id_str = str(target_id)
        
        result = self.edges_df.filter(
            (pl.col('source_id') == source_id_str) & 
            (pl.col('source_layer') == source_layer) &
            (pl.col('target_id') == target_id_str) &
            (pl.col('target_layer') == target_layer)
        )
        
        if len(result) == 0:
            return None
        
        return result.to_dicts()[0]
    
    def get_all_edges(self) -> List[Tuple[Tuple[str, str], Tuple[str, str]]]:
        """
        Get all edges as tuples of ((source_id, source_layer), (target_id, target_layer)).
        
        Returns:
            List of edge tuples
        """
        return [((row['source_id'], row['source_layer']),
                (row['target_id'], row['target_layer']))
                for row in self.edges_df.select(['source_id', 'source_layer', 
                                                'target_id', 'target_layer']).to_dicts()]
    
    def get_neighbors(self, node_id: str, layer: str) -> List[Tuple[str, str]]:
        """
        Get all neighbors of a node.
        
        Args:
            node_id: Node identifier
            layer: Layer identifier
            
        Returns:
            List of (neighbor_id, neighbor_layer) tuples
        """
        node_id_str = str(node_id)
        
        # Find all edges where this node is the source
        outgoing = self.edges_df.filter(
            (pl.col('source_id') == node_id_str) & 
            (pl.col('source_layer') == layer)
        ).select(['target_id', 'target_layer'])
        
        # Find all edges where this node is the target
        incoming = self.edges_df.filter(
            (pl.col('target_id') == node_id_str) & 
            (pl.col('target_layer') == layer)
        ).select(['source_id', 'source_layer'])
        
        neighbors = []
        for row in outgoing.to_dicts():
            neighbors.append((row['target_id'], row['target_layer']))
        for row in incoming.to_dicts():
            neighbors.append((row['source_id'], row['source_layer']))
        
        return list(set(neighbors))
    
    def get_edges_in_layer(self, layer: str) -> List[Tuple[Tuple[str, str], Tuple[str, str]]]:
        """
        Get all edges within a specific layer (intra-layer edges).
        
        Args:
            layer: Layer identifier
            
        Returns:
            List of edge tuples
        """
        result = self.edges_df.filter(
            (pl.col('source_layer') == layer) & 
            (pl.col('target_layer') == layer)
        )
        
        return [((row['source_id'], row['source_layer']),
                (row['target_id'], row['target_layer']))
                for row in result.select(['source_id', 'source_layer', 
                                        'target_id', 'target_layer']).to_dicts()]
    
    def get_interlayer_edges(self) -> List[Tuple[Tuple[str, str], Tuple[str, str]]]:
        """
        Get all inter-layer edges (edges connecting different layers).
        
        Returns:
            List of edge tuples
        """
        result = self.edges_df.filter(
            pl.col('source_layer') != pl.col('target_layer')
        )
        
        return [((row['source_id'], row['source_layer']),
                (row['target_id'], row['target_layer']))
                for row in result.select(['source_id', 'source_layer', 
                                        'target_id', 'target_layer']).to_dicts()]
    
    # =========================================================================
    # Statistics and Queries
    # =========================================================================
    
    def node_count(self) -> int:
        """Get total number of nodes."""
        return len(self.nodes_df)
    
    def edge_count(self) -> int:
        """Get total number of edges."""
        return len(self.edges_df)
    
    def layer_count(self) -> int:
        """Get number of unique layers."""
        return len(self.get_unique_layers())
    
    def degree(self, node_id: str, layer: str) -> int:
        """
        Get degree of a node.
        
        Args:
            node_id: Node identifier
            layer: Layer identifier
            
        Returns:
            Node degree
        """
        return len(self.get_neighbors(node_id, layer))
    
    def clear(self) -> None:
        """Clear all data from the store."""
        self.nodes_df = pl.DataFrame({
            'node_id': pl.Series([], dtype=pl.String),
            'layer': pl.Series([], dtype=pl.String),
        })
        
        self.edges_df = pl.DataFrame({
            'source_id': pl.Series([], dtype=pl.String),
            'source_layer': pl.Series([], dtype=pl.String),
            'target_id': pl.Series([], dtype=pl.String),
            'target_layer': pl.Series([], dtype=pl.String),
            'weight': pl.Series([], dtype=pl.Float64),
            'edge_type': pl.Series([], dtype=pl.String),
        })
        
        self.metadata.clear()
        self._cache_valid = False
    
    def summary(self) -> Dict[str, Any]:
        """
        Get summary statistics of the store.
        
        Returns:
            Dictionary with summary statistics
        """
        return {
            'nodes': self.node_count(),
            'edges': self.edge_count(),
            'layers': self.layer_count(),
            'unique_node_ids': len(self.get_unique_node_ids()),
        }
