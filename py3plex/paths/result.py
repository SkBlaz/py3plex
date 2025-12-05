"""Path result container.

This module provides a result object for path query operations.
"""

from typing import Any, Dict, List, Optional, Tuple


class PathResult:
    """Result container for path queries and flow analysis.
    
    Attributes:
        path_type: Type of path query performed
        source: Source node
        target: Target node (if applicable)
        paths: List of paths found (each path is a list of nodes)
        visit_frequency: Node visit frequency (for random walks)
        flow_values: Flow values per edge (for flow analysis)
        meta: Additional metadata about the query
    """
    
    def __init__(
        self,
        path_type: str,
        source: Any,
        target: Optional[Any] = None,
        paths: Optional[List[List[Any]]] = None,
        visit_frequency: Optional[Dict[Any, float]] = None,
        flow_values: Optional[Dict[Tuple[Any, Any], float]] = None,
        meta: Optional[Dict[str, Any]] = None,
    ):
        """Initialize PathResult.
        
        Args:
            path_type: Type of path query performed
            source: Source node
            target: Target node (if applicable)
            paths: List of paths found
            visit_frequency: Node visit frequency (for random walks)
            flow_values: Flow values per edge (for flow analysis)
            meta: Additional metadata
        """
        self.path_type = path_type
        self.source = source
        self.target = target
        self.paths = paths or []
        self.visit_frequency = visit_frequency or {}
        self.flow_values = flow_values or {}
        self.meta = meta or {}
    
    @property
    def num_paths(self) -> int:
        """Get number of paths found."""
        return len(self.paths)
    
    @property
    def shortest_path_length(self) -> Optional[int]:
        """Get length of shortest path found."""
        if not self.paths:
            return None
        return min(len(p) - 1 for p in self.paths)  # -1 for edges count
    
    def __len__(self) -> int:
        """Return number of paths."""
        return len(self.paths)
    
    def __iter__(self):
        """Iterate over paths."""
        return iter(self.paths)
    
    def __getitem__(self, index: int):
        """Get path by index."""
        return self.paths[index]
    
    def to_pandas(self):
        """Export paths to pandas DataFrame.
        
        Returns:
            pandas.DataFrame with paths
        """
        try:
            import pandas as pd
        except ImportError:
            raise ImportError("pandas is required for to_pandas(). Install with: pip install pandas")
        
        if not self.paths:
            return pd.DataFrame(columns=["path_id", "path_length", "path"])
        
        data = {
            "path_id": list(range(len(self.paths))),
            "path_length": [len(p) - 1 for p in self.paths],
            "path": [" -> ".join(str(n) for n in p) for p in self.paths],
        }
        
        return pd.DataFrame(data)
    
    def to_pandas_visit_frequency(self):
        """Export visit frequency to pandas DataFrame.
        
        Returns:
            pandas.DataFrame with node visit frequencies
        """
        try:
            import pandas as pd
        except ImportError:
            raise ImportError("pandas is required. Install with: pip install pandas")
        
        if not self.visit_frequency:
            return pd.DataFrame(columns=["node", "frequency"])
        
        data = {
            "node": list(self.visit_frequency.keys()),
            "frequency": list(self.visit_frequency.values()),
        }
        
        return pd.DataFrame(data)
    
    def to_dict(self) -> Dict[str, Any]:
        """Export results as a dictionary.
        
        Returns:
            Dictionary with path results
        """
        return {
            "path_type": self.path_type,
            "source": self.source,
            "target": self.target,
            "num_paths": self.num_paths,
            "shortest_path_length": self.shortest_path_length,
            "paths": [[str(n) for n in p] for p in self.paths],
            "visit_frequency": {str(k): v for k, v in self.visit_frequency.items()},
            "meta": self.meta,
        }
    
    def __repr__(self) -> str:
        target_str = f" -> {self.target}" if self.target else ""
        return (
            f"PathResult(type='{self.path_type}', "
            f"source={self.source}{target_str}, "
            f"num_paths={self.num_paths})"
        )
