"""Query result container for DSL v2.

This module provides a rich result object that supports multiple export formats
and includes metadata about the query execution.
"""

from typing import Any, Dict, List, Optional, Union


class QueryResult:
    """Rich result object from DSL query execution.
    
    Provides access to query results with multiple export formats and
    execution metadata.
    
    Attributes:
        target: 'nodes' or 'edges'
        items: Sequence of node/edge identifiers
        attributes: Dictionary of computed attributes (column -> values or dict)
        meta: Metadata about the query execution
        computed_metrics: Set of metrics that were computed during query execution
    """
    
    def __init__(self, target: str, items: List[Any],
                 attributes: Optional[Dict[str, Union[List[Any], Dict[Any, Any]]]] = None,
                 meta: Optional[Dict[str, Any]] = None,
                 computed_metrics: Optional[set] = None):
        """Initialize QueryResult.
        
        Args:
            target: 'nodes' or 'edges'
            items: List of node/edge identifiers
            attributes: Dictionary mapping attribute names to value lists
            meta: Optional metadata dictionary
            computed_metrics: Optional set of metrics computed during execution
        """
        self.target = target
        self.items = items
        self.attributes = attributes or {}
        self.meta = meta or {}
        self.computed_metrics = computed_metrics or set()
    
    @property
    def nodes(self) -> List[Any]:
        """Get nodes (raises if target is not 'nodes')."""
        if self.target != "nodes":
            raise ValueError(f"Cannot access nodes - target is '{self.target}'")
        return self.items
    
    @property
    def edges(self) -> List[Any]:
        """Get edges (raises if target is not 'edges')."""
        if self.target != "edges":
            raise ValueError(f"Cannot access edges - target is '{self.target}'")
        return self.items
    
    @property
    def count(self) -> int:
        """Get number of items in result."""
        return len(self.items)
    
    def __len__(self) -> int:
        """Return number of items."""
        return len(self.items)
    
    def __iter__(self):
        """Iterate over items."""
        return iter(self.items)
    
    def to_pandas(self):
        """Export results to pandas DataFrame.
        
        For node queries: Returns DataFrame with 'id' column plus computed attributes
        For edge queries: Returns DataFrame with 'source', 'target', 'source_layer', 
                         'target_layer', 'weight' columns plus computed attributes
        
        Returns:
            pandas.DataFrame with items and computed attributes
            
        Raises:
            ImportError: If pandas is not available
        """
        try:
            import pandas as pd
        except ImportError:
            raise ImportError("pandas is required for to_pandas(). Install with: pip install pandas")
        
        if self.target == "edges":
            # Build edge dataframe with standard columns
            rows = []
            for edge in self.items:
                if isinstance(edge, tuple) and len(edge) >= 2:
                    source, target = edge[0], edge[1]
                    row = {}
                    
                    # Extract source and target info
                    if isinstance(source, tuple) and len(source) >= 2:
                        row['source'] = source[0]
                        row['source_layer'] = source[1]
                    else:
                        row['source'] = source
                        row['source_layer'] = None
                    
                    if isinstance(target, tuple) and len(target) >= 2:
                        row['target'] = target[0]
                        row['target_layer'] = target[1]
                    else:
                        row['target'] = target
                        row['target_layer'] = None
                    
                    # Extract weight from edge data
                    if len(edge) >= 3 and isinstance(edge[2], dict):
                        row['weight'] = edge[2].get('weight', 1.0)
                    else:
                        row['weight'] = 1.0
                    
                    # Add computed attributes
                    # Use hashable edge key (u, v) for lookup
                    edge_key = (source, target)
                    for attr_name, values in self.attributes.items():
                        if isinstance(values, dict):
                            # Use simplified key for lookup
                            if edge_key in values:
                                row[attr_name] = values[edge_key]
                            else:
                                row[attr_name] = None
                        else:
                            # If values is a list, use index
                            idx = self.items.index(edge)
                            if idx < len(values):
                                row[attr_name] = values[idx]
                            else:
                                row[attr_name] = None
                    
                    rows.append(row)
            
            return pd.DataFrame(rows)
        
        else:
            # Node dataframe
            rows = []
            for node_item in self.items:
                row = {}
                
                # Extract node info - nodes are (node_id, layer) tuples
                if isinstance(node_item, tuple) and len(node_item) >= 2:
                    row['id'] = node_item[0]
                    row['layer'] = node_item[1]
                else:
                    row['id'] = node_item
                    row['layer'] = None
                
                # Add computed attributes
                for attr_name, values in self.attributes.items():
                    if isinstance(values, dict):
                        # Use node_item (full tuple) as key
                        if node_item in values:
                            row[attr_name] = values[node_item]
                        else:
                            row[attr_name] = None
                    else:
                        # If values is a list, use index
                        idx = self.items.index(node_item)
                        if idx < len(values):
                            row[attr_name] = values[idx]
                        else:
                            row[attr_name] = None
                
                rows.append(row)
            
            # Create DataFrame with proper columns even if empty
            if rows:
                return pd.DataFrame(rows)
            else:
                # Return empty DataFrame with expected columns
                columns = ['id', 'layer'] + list(self.attributes.keys())
                return pd.DataFrame(columns=columns)
    
    def to_networkx(self, network: Optional[Any] = None):
        """Export results to NetworkX graph.
        
        For node queries: Returns subgraph containing the selected nodes
        For edge queries: Returns subgraph containing the selected edges and their endpoints
        
        Args:
            network: Optional source network to extract subgraph from
            
        Returns:
            networkx.Graph subgraph containing result items
            
        Raises:
            ImportError: If networkx is not available
        """
        import networkx as nx
        
        if network is not None and hasattr(network, 'core_network'):
            G = network.core_network
        else:
            # Create new graph with just the items
            G = nx.Graph()
            if self.target == "nodes":
                G.add_nodes_from(self.items)
            else:
                # For edges, add edges with their attributes
                for edge in self.items:
                    if isinstance(edge, tuple) and len(edge) >= 2:
                        u, v = edge[0], edge[1]
                        attrs = edge[2] if len(edge) >= 3 and isinstance(edge[2], dict) else {}
                        G.add_edge(u, v, **attrs)
        
        # Create subgraph with result items
        if self.target == "nodes":
            subgraph = G.subgraph(self.items).copy()
            
            # Attach computed attributes to nodes
            for attr_name, values in self.attributes.items():
                if isinstance(values, dict):
                    for node, val in values.items():
                        if node in subgraph:
                            subgraph.nodes[node][attr_name] = val
                elif len(values) == len(self.items):
                    for item, val in zip(self.items, values):
                        if item in subgraph:
                            subgraph.nodes[item][attr_name] = val
        else:
            # For edges, create a graph with the selected edges
            # First, collect all nodes involved in selected edges
            nodes_in_edges = set()
            edge_list = []
            
            for edge in self.items:
                if isinstance(edge, tuple) and len(edge) >= 2:
                    u, v = edge[0], edge[1]
                    nodes_in_edges.add(u)
                    nodes_in_edges.add(v)
                    
                    # Get edge data from original graph or from edge tuple
                    edge_data = {}
                    if G.has_edge(u, v):
                        # For multigraphs, get_edge_data needs special handling
                        if isinstance(G, nx.MultiGraph):
                            # Get first edge data (multigraphs have multiple edges)
                            all_edge_data = G.get_edge_data(u, v)
                            if all_edge_data:
                                # Get first edge's data
                                first_key = list(all_edge_data.keys())[0]
                                edge_data = all_edge_data[first_key].copy()
                        else:
                            edge_data = G.get_edge_data(u, v, {})
                            if isinstance(edge_data, dict):
                                edge_data = edge_data.copy()
                    elif len(edge) >= 3 and isinstance(edge[2], dict):
                        edge_data = edge[2].copy()
                    
                    edge_list.append((u, v, edge_data))
            
            # Create new graph with selected edges
            if isinstance(G, nx.MultiGraph):
                subgraph = nx.MultiGraph()
            elif isinstance(G, nx.DiGraph):
                subgraph = nx.DiGraph()
            else:
                subgraph = nx.Graph()
            
            # Add nodes with their attributes
            for node in nodes_in_edges:
                if node in G:
                    subgraph.add_node(node, **G.nodes[node])
                else:
                    subgraph.add_node(node)
            
            # Add edges with their attributes
            for u, v, data in edge_list:
                subgraph.add_edge(u, v, **data)
            
            # Attach computed edge attributes
            for attr_name, values in self.attributes.items():
                if isinstance(values, dict):
                    for edge, val in values.items():
                        if isinstance(edge, tuple) and len(edge) >= 2:
                            u, v = edge[0], edge[1]
                            if subgraph.has_edge(u, v):
                                subgraph[u][v][attr_name] = val
        
        return subgraph
    
    def to_arrow(self):
        """Export results to Apache Arrow table.
        
        Returns:
            pyarrow.Table with items and computed attributes
            
        Raises:
            ImportError: If pyarrow is not available
        """
        try:
            import pyarrow as pa
        except ImportError:
            raise ImportError("pyarrow is required for to_arrow(). Install with: pip install pyarrow")
        
        # Convert items to strings for Arrow compatibility
        data = {"id": [str(item) for item in self.items]}
        
        for attr_name, values in self.attributes.items():
            if isinstance(values, dict):
                data[attr_name] = [values.get(item, None) for item in self.items]
            elif len(values) == len(self.items):
                data[attr_name] = list(values)
            else:
                data[attr_name] = list(values) + [None] * (len(self.items) - len(values))
        
        return pa.table(data)
    
    def to_dict(self) -> Dict[str, Any]:
        """Export results as a dictionary.
        
        Returns:
            Dictionary with target, items, attributes, and metadata
        """
        return {
            "target": self.target,
            self.target: self.items,
            "count": len(self.items),
            "computed": self.attributes,
            "meta": self.meta,
        }
    
    def __repr__(self) -> str:
        return f"QueryResult(target='{self.target}', count={len(self.items)}, attributes={list(self.attributes.keys())})"
