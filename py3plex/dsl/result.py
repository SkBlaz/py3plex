"""Query result container for DSL v2.

This module provides a rich result object that supports multiple export formats
and includes metadata about the query execution.
"""

from typing import Any, Dict, List, Optional, Union
import math


# Tolerance for matching quantile keys when finding CI bounds
_QUANTILE_TOLERANCE = 0.01


def _expand_uncertainty_value(attr_name: str, value: Any, ci_level: float = 0.95) -> Dict[str, Any]:
    """Expand an uncertainty value into multiple columns.
    
    Args:
        attr_name: Base attribute name (e.g., "degree")
        value: The value (may be dict with uncertainty info or scalar)
        ci_level: Confidence interval level (default: 0.95)
        
    Returns:
        Dictionary with expanded columns
    """
    result = {}
    
    # Always include the point estimate
    if isinstance(value, dict) and 'mean' in value:
        result[attr_name] = value['mean']
        
        # Add std if available
        if 'std' in value:
            result[f"{attr_name}_std"] = value['std']
        else:
            result[f"{attr_name}_std"] = None
        
        # Add CI bounds if quantiles are available
        quantiles = value.get('quantiles', {})
        if quantiles:
            # Calculate quantile keys for the CI level
            lower_q = (1 - ci_level) / 2
            upper_q = 1 - (1 - ci_level) / 2
            
            # Find closest available quantiles
            ci_low = quantiles.get(lower_q)
            ci_high = quantiles.get(upper_q)
            
            # If exact quantiles not found, try to find closest
            if ci_low is None or ci_high is None:
                sorted_qs = sorted(quantiles.keys())
                if sorted_qs:
                    # Find closest lower quantile (within tolerance)
                    lower_candidates = [q for q in sorted_qs if q <= lower_q + _QUANTILE_TOLERANCE]
                    if lower_candidates:
                        ci_low = quantiles[lower_candidates[-1]]
                    
                    # Find closest upper quantile (within tolerance)
                    upper_candidates = [q for q in sorted_qs if q >= upper_q - _QUANTILE_TOLERANCE]
                    if upper_candidates:
                        ci_high = quantiles[upper_candidates[0]]
            
            # Convert CI level to percentage for column names (e.g., 0.95 -> ci95)
            ci_pct = int(ci_level * 100)
            
            result[f"{attr_name}_ci{ci_pct}_low"] = ci_low
            result[f"{attr_name}_ci{ci_pct}_high"] = ci_high
            
            # Calculate width if both bounds available
            if ci_low is not None and ci_high is not None:
                result[f"{attr_name}_ci{ci_pct}_width"] = ci_high - ci_low
            else:
                result[f"{attr_name}_ci{ci_pct}_width"] = None
        else:
            # No quantiles - set CI columns to None
            ci_pct = int(ci_level * 100)
            result[f"{attr_name}_ci{ci_pct}_low"] = None
            result[f"{attr_name}_ci{ci_pct}_high"] = None
            result[f"{attr_name}_ci{ci_pct}_width"] = None
    else:
        # Deterministic value - just use as-is
        result[attr_name] = value
        # Set uncertainty columns to None or 0
        ci_pct = int(ci_level * 100)
        result[f"{attr_name}_std"] = 0.0 if value is not None else None
        result[f"{attr_name}_ci{ci_pct}_low"] = value
        result[f"{attr_name}_ci{ci_pct}_high"] = value
        result[f"{attr_name}_ci{ci_pct}_width"] = 0.0 if value is not None else None
    
    return result


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
    
    def to_pandas(self, multiindex: bool = False, include_grouping: bool = True,
                  expand_uncertainty: bool = False):
        """Export results to pandas DataFrame.
        
        For node queries: Returns DataFrame with 'id' column plus computed attributes
        For edge queries: Returns DataFrame with 'source', 'target', 'source_layer', 
                         'target_layer', 'weight' columns plus computed attributes
        
        Args:
            multiindex: If True and grouping metadata is present, set DataFrame index
                       to the grouping keys (e.g., ["layer"] or ["src_layer", "dst_layer"])
            include_grouping: If True and grouping metadata is present, ensure grouping
                            key columns are included in the DataFrame
            expand_uncertainty: If True, expand uncertainty metrics into multiple columns:
                              - metric (point estimate/mean)
                              - metric_std (standard deviation)
                              - metric_ci95_low (95% CI lower bound)
                              - metric_ci95_high (95% CI upper bound)
                              - metric_ci95_width (CI width)
        
        Returns:
            pandas.DataFrame with items and computed attributes
            
        Raises:
            ImportError: If pandas is not available
            
        Example:
            >>> result = Q.nodes().uq(UQ.fast()).compute("degree").execute(net)
            >>> df = result.to_pandas(expand_uncertainty=True)
            >>> # df now has columns: id, layer, degree, degree_std, degree_ci95_low, degree_ci95_high, degree_ci95_width
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
                                value = values[edge_key]
                                
                                if expand_uncertainty:
                                    # Expand uncertainty into multiple columns
                                    expanded = _expand_uncertainty_value(attr_name, value)
                                    row.update(expanded)
                                else:
                                    # Preserve uncertainty dictionaries unless explicitly expanded.
                                    row[attr_name] = value
                            else:
                                if expand_uncertainty:
                                    # Add None for all expanded columns
                                    ci_pct = 95  # Default CI level
                                    row[attr_name] = None
                                    row[f"{attr_name}_std"] = None
                                    row[f"{attr_name}_ci{ci_pct}_low"] = None
                                    row[f"{attr_name}_ci{ci_pct}_high"] = None
                                    row[f"{attr_name}_ci{ci_pct}_width"] = None
                                else:
                                    row[attr_name] = None
                        else:
                            # If values is a list, use index
                            idx = self.items.index(edge)
                            if idx < len(values):
                                value = values[idx]
                                
                                if expand_uncertainty:
                                    # Expand uncertainty into multiple columns
                                    expanded = _expand_uncertainty_value(attr_name, value)
                                    row.update(expanded)
                                else:
                                    # Preserve uncertainty dictionaries unless explicitly expanded.
                                    row[attr_name] = value
                            else:
                                if expand_uncertainty:
                                    # Add None for all expanded columns
                                    ci_pct = 95  # Default CI level
                                    row[attr_name] = None
                                    row[f"{attr_name}_std"] = None
                                    row[f"{attr_name}_ci{ci_pct}_low"] = None
                                    row[f"{attr_name}_ci{ci_pct}_high"] = None
                                    row[f"{attr_name}_ci{ci_pct}_width"] = None
                                else:
                                    row[attr_name] = None
                    
                    rows.append(row)
            
            df = pd.DataFrame(rows)
            
            # Apply grouping metadata if present
            if include_grouping and "grouping" in self.meta:
                grouping_info = self.meta["grouping"]
                if multiindex and grouping_info.get("keys"):
                    # Set multiindex using grouping keys
                    index_cols = grouping_info["keys"]
                    # Only set index if all keys exist in the dataframe
                    if all(col in df.columns for col in index_cols):
                        df = df.set_index(index_cols)
            
            return df
        
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
                            value = values[node_item]
                            
                            if expand_uncertainty:
                                # Expand uncertainty into multiple columns
                                expanded = _expand_uncertainty_value(attr_name, value)
                                row.update(expanded)
                            else:
                                # Preserve uncertainty dictionaries unless explicitly expanded.
                                row[attr_name] = value
                        else:
                            if expand_uncertainty:
                                # Add None for all expanded columns
                                ci_pct = 95  # Default CI level
                                row[attr_name] = None
                                row[f"{attr_name}_std"] = None
                                row[f"{attr_name}_ci{ci_pct}_low"] = None
                                row[f"{attr_name}_ci{ci_pct}_high"] = None
                                row[f"{attr_name}_ci{ci_pct}_width"] = None
                            else:
                                row[attr_name] = None
                    else:
                        # If values is a list, use index
                        idx = self.items.index(node_item)
                        if idx < len(values):
                            value = values[idx]
                            
                            if expand_uncertainty:
                                # Expand uncertainty into multiple columns
                                expanded = _expand_uncertainty_value(attr_name, value)
                                row.update(expanded)
                            else:
                                # Preserve uncertainty dictionaries unless explicitly expanded.
                                row[attr_name] = value
                        else:
                            if expand_uncertainty:
                                # Add None for all expanded columns
                                ci_pct = 95  # Default CI level
                                row[attr_name] = None
                                row[f"{attr_name}_std"] = None
                                row[f"{attr_name}_ci{ci_pct}_low"] = None
                                row[f"{attr_name}_ci{ci_pct}_high"] = None
                                row[f"{attr_name}_ci{ci_pct}_width"] = None
                            else:
                                row[attr_name] = None
                
                rows.append(row)
            
            # Create DataFrame with proper columns even if empty
            if rows:
                df = pd.DataFrame(rows)
            else:
                # Return empty DataFrame with expected columns
                columns = ['id', 'layer'] + list(self.attributes.keys())
                df = pd.DataFrame(columns=columns)
            
            # Apply grouping metadata if present
            if include_grouping and "grouping" in self.meta:
                grouping_info = self.meta["grouping"]
                if multiindex and grouping_info.get("keys"):
                    # Set multiindex using grouping keys
                    index_cols = grouping_info["keys"]
                    # Only set index if all keys exist in the dataframe
                    if all(col in df.columns for col in index_cols):
                        df = df.set_index(index_cols)
            
            return df
    
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
    
    def group_summary(self):
        """Return a summary DataFrame with one row per group.
        
        Returns a pandas DataFrame containing:
        - Grouping key columns (e.g., "layer", "src_layer", "dst_layer")
        - n_items: Number of items (nodes/edges) in each group
        - Any group-level coverage metrics if available
        
        This method only uses information already present in the result and
        does not recompute expensive measures.
        
        Returns:
            pandas.DataFrame with one row per group
            
        Raises:
            ImportError: If pandas is not available
            ValueError: If result does not have grouping metadata
        """
        try:
            import pandas as pd
        except ImportError:
            raise ImportError("pandas is required for group_summary(). Install with: pip install pandas")
        
        # Check that grouping metadata exists
        if "grouping" not in self.meta:
            from .errors import GroupingError
            raise GroupingError(
                "group_summary() is only defined for grouped results. "
                "Use .per_layer() or .per_layer_pair() to create a grouped query."
            )
        
        grouping_info = self.meta["grouping"]
        groups = grouping_info.get("groups", [])
        
        # Build rows from group metadata
        rows = []
        for group_meta in groups:
            row = {}
            
            # Add grouping key columns
            key_dict = group_meta.get("key", {})
            row.update(key_dict)
            
            # Add n_items
            row["n_items"] = group_meta.get("n_items", 0)
            
            # Add any additional metadata (e.g., coverage metrics)
            for k, v in group_meta.items():
                if k not in ("key", "n_items"):
                    row[k] = v
            
            rows.append(row)
        
        return pd.DataFrame(rows)
    
    def __repr__(self) -> str:
        return f"QueryResult(target='{self.target}', count={len(self.items)}, attributes={list(self.attributes.keys())})"
