"""Internal types for SelectionUQ.

This module defines the SelectionOutput type used to represent query results
internally before reduction into SelectionUQ summaries.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class SelectionOutput:
    """Internal representation of a selection query result.
    
    This is the unified output format returned by base_callable that gets
    fed into reducers for uncertainty quantification.
    
    Attributes
    ----------
    items : list
        Selected item IDs (node IDs or edge tuples)
    scores : dict, optional
        Scores per item if ranked query (e.g., centrality values)
    ranks : dict, optional
        Exact rank per item if ranking is defined (1-indexed)
    k : int, optional
        Top-k parameter if relevant
    target : str
        Type of items: "nodes" or "edges"
    group_key : tuple, optional
        Grouping key for per_layer/per_layer_pair queries
        
    Notes
    -----
    If .top_k(k, ...) was used, ranks must be defined for returned items.
    If only filtering (no ordering), scores/ranks may be None.
    """
    
    items: List[Any]
    scores: Optional[Dict[Any, float]] = None
    ranks: Optional[Dict[Any, int]] = None
    k: Optional[int] = None
    target: str = "nodes"
    group_key: Optional[Tuple] = None
    
    def __post_init__(self):
        """Validate internal consistency."""
        if self.k is not None and self.ranks is None:
            raise ValueError("If k is specified, ranks must be provided")
        
        if self.ranks is not None:
            # Validate all returned items have ranks
            missing_ranks = [item for item in self.items if item not in self.ranks]
            if missing_ranks:
                raise ValueError(
                    f"Items missing ranks: {missing_ranks[:5]}..."
                    if len(missing_ranks) > 5 
                    else f"Items missing ranks: {missing_ranks}"
                )
