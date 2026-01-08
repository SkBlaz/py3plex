"""Internal types for PartitionUQ.

This module defines the PartitionOutput type used to represent community
detection results internally before reduction into PartitionUQ summaries.
"""

from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class PartitionOutput:
    """Internal representation of a partition (community assignment).
    
    This is the unified output format returned by base_callable that gets
    fed into reducers for uncertainty quantification.
    
    PartitionOutput is a thin adapter that wraps community detection results
    into a standard format. Community algorithms return node → community
    assignments, and this class normalizes that representation.
    
    Attributes
    ----------
    labels : dict[node_id, community_id]
        Mapping from node IDs to community IDs.
        Node IDs can be any hashable type (str, int, tuple).
        Community IDs are typically integers but can be any hashable type.
        
    Examples
    --------
    >>> # From a community detection algorithm
    >>> partition = PartitionOutput(labels={
    ...     'A': 0, 'B': 0, 'C': 1, 'D': 1
    ... })
    >>> 
    >>> # Check assignment
    >>> partition.labels['A']
    0
    
    Notes
    -----
    - Community algorithms MUST be adapted to return PartitionOutput
    - This adaptation can be done in executor glue code
    - DO NOT modify algorithms to return PartitionOutput directly
    """
    
    labels: Dict[Any, Any]
    
    def __post_init__(self):
        """Validate partition output."""
        if not isinstance(self.labels, dict):
            raise TypeError(f"labels must be dict, got {type(self.labels)}")
        
        if not self.labels:
            raise ValueError("labels dictionary cannot be empty")
