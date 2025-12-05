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
    """
    
    def __init__(self, target: str, items: List[Any],
                 attributes: Optional[Dict[str, Union[List[Any], Dict[Any, Any]]]] = None,
                 meta: Optional[Dict[str, Any]] = None):
        """Initialize QueryResult.
        
        Args:
            target: 'nodes' or 'edges'
            items: List of node/edge identifiers
            attributes: Dictionary mapping attribute names to value lists
            meta: Optional metadata dictionary
        """
        self.target = target
        self.items = items
        self.attributes = attributes or {}
        self.meta = meta or {}
    
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
        
        Returns:
            pandas.DataFrame with items and computed attributes
            
        Raises:
            ImportError: If pandas is not available
        """
        try:
            import pandas as pd
        except ImportError:
            raise ImportError("pandas is required for to_pandas(). Install with: pip install pandas")
        
        # Build dataframe
        data = {"id": self.items}
        
        # Add attributes - ensure they're aligned with items
        for attr_name, values in self.attributes.items():
            if isinstance(values, dict):
                # Convert dict to aligned list
                data[attr_name] = [values.get(item, None) for item in self.items]
            elif len(values) == len(self.items):
                data[attr_name] = values
            else:
                # Pad or truncate
                data[attr_name] = list(values) + [None] * (len(self.items) - len(values))
        
        return pd.DataFrame(data)
    
    def to_networkx(self, network: Optional[Any] = None):
        """Export results to NetworkX graph.
        
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
                G.add_edges_from(self.items)
        
        # Create subgraph with result items
        if self.target == "nodes":
            subgraph = G.subgraph(self.items).copy()
        else:
            edge_set = set()
            for edge in self.items:
                if len(edge) >= 2:
                    edge_set.add((edge[0], edge[1]))
            subgraph = nx.Graph()
            for u, v in edge_set:
                if G.has_edge(u, v):
                    subgraph.add_edge(u, v, **G.get_edge_data(u, v, {}))
        
        # Attach computed attributes
        for attr_name, values in self.attributes.items():
            if isinstance(values, dict):
                if self.target == "nodes":
                    for node, val in values.items():
                        if node in subgraph:
                            subgraph.nodes[node][attr_name] = val
            elif len(values) == len(self.items):
                if self.target == "nodes":
                    for item, val in zip(self.items, values):
                        if item in subgraph:
                            subgraph.nodes[item][attr_name] = val
        
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
