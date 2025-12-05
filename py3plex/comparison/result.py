"""Comparison result container.

This module provides a rich result object for network comparison operations.
"""

from typing import Any, Dict, List, Optional, Union


class ComparisonResult:
    """Result container for multilayer network comparison.
    
    Attributes:
        metric_name: Name of the comparison metric used
        network_a_name: Name/key of the first network
        network_b_name: Name/key of the second network
        global_distance: Overall distance/similarity score
        layerwise_distance: Per-layer distance values (if computed)
        per_node_difference: Node-level differences (if computed)
        meta: Additional metadata about the comparison
    """
    
    def __init__(
        self,
        metric_name: str,
        network_a_name: str,
        network_b_name: str,
        global_distance: Optional[float] = None,
        layerwise_distance: Optional[Dict[str, float]] = None,
        per_node_difference: Optional[Dict[Any, float]] = None,
        meta: Optional[Dict[str, Any]] = None,
    ):
        """Initialize ComparisonResult.
        
        Args:
            metric_name: Name of the comparison metric used
            network_a_name: Name/key of the first network
            network_b_name: Name/key of the second network
            global_distance: Overall distance/similarity score
            layerwise_distance: Per-layer distance values
            per_node_difference: Node-level differences
            meta: Additional metadata
        """
        self.metric_name = metric_name
        self.network_a_name = network_a_name
        self.network_b_name = network_b_name
        self.global_distance = global_distance
        self.layerwise_distance = layerwise_distance or {}
        self.per_node_difference = per_node_difference or {}
        self.meta = meta or {}
    
    def to_pandas(self):
        """Export results to pandas DataFrame.
        
        Returns:
            pandas.DataFrame with comparison results
        """
        try:
            import pandas as pd
        except ImportError:
            raise ImportError("pandas is required for to_pandas(). Install with: pip install pandas")
        
        # Build dataframe based on available data
        data = {
            "metric": [self.metric_name],
            "network_a": [self.network_a_name],
            "network_b": [self.network_b_name],
            "global_distance": [self.global_distance],
        }
        
        return pd.DataFrame(data)
    
    def to_pandas_layerwise(self):
        """Export layerwise distances to pandas DataFrame.
        
        Returns:
            pandas.DataFrame with per-layer comparison results
        """
        try:
            import pandas as pd
        except ImportError:
            raise ImportError("pandas is required for to_pandas_layerwise(). Install with: pip install pandas")
        
        if not self.layerwise_distance:
            return pd.DataFrame(columns=["layer", "distance"])
        
        data = {
            "layer": list(self.layerwise_distance.keys()),
            "distance": list(self.layerwise_distance.values()),
        }
        
        return pd.DataFrame(data)
    
    def to_pandas_nodes(self):
        """Export per-node differences to pandas DataFrame.
        
        Returns:
            pandas.DataFrame with per-node comparison results
        """
        try:
            import pandas as pd
        except ImportError:
            raise ImportError("pandas is required for to_pandas_nodes(). Install with: pip install pandas")
        
        if not self.per_node_difference:
            return pd.DataFrame(columns=["node", "difference"])
        
        data = {
            "node": list(self.per_node_difference.keys()),
            "difference": list(self.per_node_difference.values()),
        }
        
        return pd.DataFrame(data)
    
    def to_dict(self) -> Dict[str, Any]:
        """Export results as a dictionary.
        
        Returns:
            Dictionary with all comparison results
        """
        return {
            "metric_name": self.metric_name,
            "network_a": self.network_a_name,
            "network_b": self.network_b_name,
            "global_distance": self.global_distance,
            "layerwise_distance": self.layerwise_distance,
            "per_node_difference": self.per_node_difference,
            "meta": self.meta,
        }
    
    def to_json(self) -> str:
        """Export results as JSON string.
        
        Returns:
            JSON string representation
        """
        import json
        
        # Convert node keys to strings for JSON compatibility
        result = self.to_dict()
        if result["per_node_difference"]:
            result["per_node_difference"] = {
                str(k): v for k, v in result["per_node_difference"].items()
            }
        
        return json.dumps(result, indent=2)
    
    def __repr__(self) -> str:
        return (
            f"ComparisonResult(metric='{self.metric_name}', "
            f"networks=['{self.network_a_name}', '{self.network_b_name}'], "
            f"global_distance={self.global_distance})"
        )
