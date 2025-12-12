"""Pattern Query Result Container.

This module provides the PatternQueryResult class that wraps pattern matching
results and provides convenient projection methods.
"""

from typing import Any, Dict, List, Optional, Set, Tuple, Union

from .ir import PatternGraph, MatchRow


class PatternQueryResult:
    """Result container for pattern matching queries.
    
    Provides access to matches with multiple export formats and projections.
    
    Attributes:
        pattern: Original pattern graph
        matches: List of MatchRow objects
        meta: Metadata about the query execution
    """
    
    def __init__(
        self,
        pattern: PatternGraph,
        matches: List[MatchRow],
        meta: Optional[Dict[str, Any]] = None,
    ):
        """Initialize pattern query result.
        
        Args:
            pattern: Original pattern graph
            matches: List of MatchRow objects
            meta: Optional metadata dictionary
        """
        self.pattern = pattern
        self.matches = matches
        self.meta = meta or {}
        self._rows_cache: Optional[List[Dict[str, Any]]] = None
    
    @property
    def rows(self) -> List[Dict[str, Any]]:
        """Get matches as list of dictionaries.
        
        Returns:
            List of dictionaries mapping variable names to node IDs
        """
        if self._rows_cache is None:
            self._rows_cache = [match.to_dict() for match in self.matches]
        return self._rows_cache
    
    @property
    def count(self) -> int:
        """Get number of matches.
        
        Returns:
            Number of matches
        """
        return len(self.matches)
    
    def __len__(self) -> int:
        """Return number of matches."""
        return len(self.matches)
    
    def __iter__(self):
        """Iterate over match rows."""
        return iter(self.matches)
    
    def to_pandas(self, include_meta: bool = False):
        """Export matches to pandas DataFrame.
        
        Args:
            include_meta: If True, include metadata columns
            
        Returns:
            pandas.DataFrame with matches
            
        Raises:
            ImportError: If pandas is not available
        """
        try:
            import pandas as pd
        except ImportError:
            raise ImportError("pandas is required for to_pandas(). Install with: pip install pandas")
        
        if not self.matches:
            # Return empty DataFrame with columns from pattern
            columns = self.pattern.get_return_vars()
            return pd.DataFrame(columns=columns)
        
        # Convert matches to DataFrame
        df = pd.DataFrame(self.rows)
        
        # Filter edge bindings if present
        if '_edges' in df.columns:
            df = df.drop(columns=['_edges'])
        
        # Add metadata if requested
        if include_meta:
            for key, value in self.meta.items():
                if isinstance(value, (str, int, float, bool)):
                    df[f'_meta_{key}'] = value
        
        return df
    
    def to_nodes(self, vars: Optional[List[str]] = None, unique: bool = True) -> Union[List[Any], Set[Any]]:
        """Extract node IDs from matches.
        
        Args:
            vars: Optional list of variables to include (defaults to all)
            unique: If True, return unique nodes as a set
            
        Returns:
            List or set of node IDs
        """
        if vars is None:
            vars = self.pattern.get_return_vars()
        
        nodes = []
        for match in self.matches:
            for var in vars:
                if var in match.bindings:
                    nodes.append(match.bindings[var])
        
        if unique:
            return set(nodes)
        return nodes
    
    def to_edges(self, var_pairs: Optional[List[Tuple[str, str]]] = None) -> List[Tuple[Any, Any]]:
        """Extract edges from matches.
        
        Infers edges from pairs of node variables in the pattern.
        
        Args:
            var_pairs: Optional list of (src_var, dst_var) tuples to extract
                      If None, uses pattern edges
            
        Returns:
            List of (src_node, dst_node) tuples
        """
        if var_pairs is None:
            # Use pattern edges to determine pairs
            var_pairs = [(edge.src, edge.dst) for edge in self.pattern.edges]
        
        edges = []
        for match in self.matches:
            for src_var, dst_var in var_pairs:
                if src_var in match.bindings and dst_var in match.bindings:
                    src = match.bindings[src_var]
                    dst = match.bindings[dst_var]
                    edges.append((src, dst))
        
        return edges
    
    def to_subgraph(self, network: Any, per_match: bool = False) -> Any:
        """Extract induced subgraph(s) from matches.
        
        Args:
            network: Original network object
            per_match: If True, return list of subgraphs (one per match)
                      If False, return single subgraph with all matched nodes
            
        Returns:
            NetworkX graph or list of graphs
        """
        import networkx as nx
        
        if per_match:
            # Create one subgraph per match
            subgraphs = []
            for match in self.matches:
                nodes = list(match.bindings.values())
                if hasattr(network, 'core_network'):
                    subgraph = network.core_network.subgraph(nodes).copy()
                else:
                    subgraph = nx.Graph()
                    subgraph.add_nodes_from(nodes)
                subgraphs.append(subgraph)
            return subgraphs
        else:
            # Create single subgraph with all matched nodes
            all_nodes = self.to_nodes(unique=True)
            if hasattr(network, 'core_network'):
                return network.core_network.subgraph(all_nodes).copy()
            else:
                subgraph = nx.Graph()
                subgraph.add_nodes_from(all_nodes)
                return subgraph
    
    def filter(self, predicate) -> "PatternQueryResult":
        """Filter matches using a predicate function.
        
        Args:
            predicate: Function that takes a MatchRow and returns bool
            
        Returns:
            New PatternQueryResult with filtered matches
        """
        filtered_matches = [match for match in self.matches if predicate(match)]
        return PatternQueryResult(
            pattern=self.pattern,
            matches=filtered_matches,
            meta=self.meta.copy(),
        )
    
    def limit(self, n: int) -> "PatternQueryResult":
        """Limit the number of matches.
        
        Args:
            n: Maximum number of matches
            
        Returns:
            New PatternQueryResult with limited matches
        """
        return PatternQueryResult(
            pattern=self.pattern,
            matches=self.matches[:n],
            meta=self.meta.copy(),
        )
    
    def __repr__(self) -> str:
        """Return string representation."""
        return f"PatternQueryResult(matches={len(self.matches)}, vars={self.pattern.get_return_vars()})"
