"""Query Algebra for compositional reasoning over queries and results.

This module implements algebraic operations on queries and query results,
enabling compositional network analysis workflows.

Query algebra operates at two levels:
1. Pre-compute: Logical composition of filters and scopes (queries not yet executed)
2. Post-compute: Combining annotated results (executed queries with attributes)

Key Features:
- Set operations: union (|), intersection (&), difference (-), symmetric difference (^)
- Type safety: Only compatible query targets can combine
- Attribute awareness: Conflict detection and resolution strategies
- Uncertainty propagation: Correct handling of UQ through algebraic operations
- Identity semantics: Explicit control over node identity (by_id vs by_replica)
- Provenance tracking: Full audit trail of algebraic operations

Example:
    >>> from py3plex.dsl import Q, L
    >>> 
    >>> # Pre-compute algebra: logical filter composition
    >>> social_hubs = Q.nodes().from_layers(L["social"]).where(degree__gt=5)
    >>> work_hubs = Q.nodes().from_layers(L["work"]).where(degree__gt=5)
    >>> all_hubs = social_hubs | work_hubs  # Union of queries
    >>> 
    >>> # Post-compute algebra: combining executed results
    >>> result1 = social_hubs.execute(net)
    >>> result2 = work_hubs.execute(net)
    >>> combined = result1 | result2  # Union of results
"""

from typing import Any, Dict, List, Optional, Set, Union, Callable
from dataclasses import dataclass
from enum import Enum


class IdentityStrategy(Enum):
    """Strategy for determining node identity in algebra operations.
    
    - BY_ID: Compare nodes by physical ID only (ignore layer)
    - BY_REPLICA: Compare nodes by (ID, layer) tuple (strict replica equality)
    """
    BY_ID = "by_id"
    BY_REPLICA = "by_replica"


class ConflictResolution(Enum):
    """Strategy for resolving attribute conflicts in algebra operations.
    
    - ERROR: Raise error on conflicts (safe default)
    - PREFER_LEFT: Keep value from left operand
    - PREFER_RIGHT: Keep value from right operand
    - MEAN: Average numeric values
    - MAX: Take maximum numeric value
    - MIN: Take minimum numeric value
    - KEEP_BOTH: Keep both with namespaced keys
    """
    ERROR = "error"
    PREFER_LEFT = "prefer_left"
    PREFER_RIGHT = "prefer_right"
    MEAN = "mean"
    MAX = "max"
    MIN = "min"
    KEEP_BOTH = "keep_both"


@dataclass
class AlgebraConfig:
    """Configuration for query algebra operations.
    
    Attributes:
        identity_strategy: How to compare nodes/edges (by_id or by_replica)
        conflict_resolution: How to handle attribute conflicts
        preserve_uncertainty: Whether to preserve UQ information
    """
    identity_strategy: IdentityStrategy = IdentityStrategy.BY_REPLICA
    conflict_resolution: ConflictResolution = ConflictResolution.ERROR
    preserve_uncertainty: bool = True


class AlgebraError(Exception):
    """Base exception for query algebra errors."""
    pass


class IncompatibleQueryError(AlgebraError):
    """Raised when trying to combine incompatible queries."""
    pass


class AttributeConflictError(AlgebraError):
    """Raised when attribute conflicts cannot be resolved."""
    pass


class AmbiguousIdentityError(AlgebraError):
    """Raised when identity strategy is ambiguous and not explicitly specified."""
    pass


def check_query_compatibility(q1: "QueryBuilder", q2: "QueryBuilder") -> None:
    """Check if two queries can be combined algebraically.
    
    Args:
        q1: First query
        q2: Second query
        
    Raises:
        IncompatibleQueryError: If queries have incompatible targets
    """
    from .builder import QueryBuilder
    from .ast import Target
    
    if not isinstance(q1, QueryBuilder) or not isinstance(q2, QueryBuilder):
        raise IncompatibleQueryError(
            f"Can only combine QueryBuilder instances, got {type(q1)} and {type(q2)}"
        )
    
    target1 = q1._select.target
    target2 = q2._select.target
    
    if target1 != target2:
        raise IncompatibleQueryError(
            f"Cannot combine queries with different targets: "
            f"{target1.name} vs {target2.name}. "
            f"Only nodes with nodes, edges with edges, etc."
        )


def check_result_compatibility(r1: "QueryResult", r2: "QueryResult") -> None:
    """Check if two results can be combined algebraically.
    
    Args:
        r1: First result
        r2: Second result
        
    Raises:
        IncompatibleQueryError: If results have incompatible targets
    """
    from .result import QueryResult
    
    if not isinstance(r1, QueryResult) or not isinstance(r2, QueryResult):
        raise IncompatibleQueryError(
            f"Can only combine QueryResult instances, got {type(r1)} and {type(r2)}"
        )
    
    if r1.target != r2.target:
        raise IncompatibleQueryError(
            f"Cannot combine results with different targets: "
            f"{r1.target} vs {r2.target}. "
            f"Only nodes with nodes, edges with edges, etc."
        )


def detect_identity_ambiguity(r1: "QueryResult", r2: "QueryResult") -> bool:
    """Check if identity strategy is ambiguous for given results.
    
    Ambiguity exists when:
    - Both results have multilayer data (multiple layers represented)
    - No explicit identity strategy is specified
    
    Args:
        r1: First result
        r2: Second result
        
    Returns:
        True if ambiguity exists
    """
    # Check if results have multilayer data
    # A result is multilayer if items contain tuples with layer information
    def has_multilayer_items(result: "QueryResult") -> bool:
        if not result.items:
            return False
        # Check if items are tuples (node_id, layer)
        sample = result.items[0]
        return isinstance(sample, tuple) and len(sample) >= 2
    
    return has_multilayer_items(r1) and has_multilayer_items(r2)


def extract_item_identity(item: Any, strategy: IdentityStrategy) -> Any:
    """Extract identity key from item based on strategy.
    
    Args:
        item: Node or edge item
        strategy: Identity strategy
        
    Returns:
        Identity key for comparison
    """
    if strategy == IdentityStrategy.BY_ID:
        # For nodes: (node_id, layer) -> node_id
        # For edges: (src, dst, src_layer, dst_layer) -> (src, dst)
        if isinstance(item, tuple):
            if len(item) == 2:
                # Node: (node_id, layer)
                return item[0]
            elif len(item) >= 4:
                # Edge: (src, dst, src_layer, dst_layer, ...)
                return (item[0], item[1])
        return item
    else:
        # BY_REPLICA: use full item as identity
        return item


def detect_attribute_conflicts(
    attrs1: Dict[str, Any],
    attrs2: Dict[str, Any],
    shared_items: Set[Any]
) -> Set[str]:
    """Detect which attributes have conflicting values for shared items.
    
    Args:
        attrs1: Attributes from first result
        attrs2: Attributes from second result
        shared_items: Items present in both results
        
    Returns:
        Set of attribute names with conflicts
    """
    conflicts = set()
    
    # Find attributes present in both
    common_attrs = set(attrs1.keys()) & set(attrs2.keys())
    
    for attr in common_attrs:
        values1 = attrs1[attr]
        values2 = attrs2[attr]
        
        # Check if any shared item has different values
        for item in shared_items:
            val1 = values1.get(item) if isinstance(values1, dict) else None
            val2 = values2.get(item) if isinstance(values2, dict) else None
            
            if val1 is not None and val2 is not None and val1 != val2:
                conflicts.add(attr)
                break
    
    return conflicts


def resolve_attribute_conflict(
    attr_name: str,
    val1: Any,
    val2: Any,
    strategy: ConflictResolution
) -> Any:
    """Resolve a single attribute conflict using specified strategy.
    
    Args:
        attr_name: Name of conflicting attribute
        val1: Value from first result
        val2: Value from second result
        strategy: Resolution strategy
        
    Returns:
        Resolved value
        
    Raises:
        AttributeConflictError: If conflict cannot be resolved with ERROR strategy
    """
    if strategy == ConflictResolution.ERROR:
        raise AttributeConflictError(
            f"Attribute conflict for '{attr_name}': {val1} vs {val2}. "
            f"Use .resolve(conflicts=...) to specify resolution strategy."
        )
    elif strategy == ConflictResolution.PREFER_LEFT:
        return val1
    elif strategy == ConflictResolution.PREFER_RIGHT:
        return val2
    elif strategy == ConflictResolution.MEAN:
        # For UQ values, average the means
        if isinstance(val1, dict) and isinstance(val2, dict):
            if "mean" in val1 and "mean" in val2:
                # Combine UQ values (simplified - full implementation needs proper variance combination)
                return {
                    "mean": (val1["mean"] + val2["mean"]) / 2,
                    "std": ((val1.get("std", 0)**2 + val2.get("std", 0)**2) ** 0.5) / 2,
                }
        # For numeric scalars
        try:
            return (float(val1) + float(val2)) / 2
        except (TypeError, ValueError):
            raise AttributeConflictError(
                f"Cannot compute mean for non-numeric values: {val1}, {val2}"
            )
    elif strategy == ConflictResolution.MAX:
        try:
            # For UQ, compare means
            v1 = val1["mean"] if isinstance(val1, dict) and "mean" in val1 else val1
            v2 = val2["mean"] if isinstance(val2, dict) and "mean" in val2 else val2
            return val1 if v1 >= v2 else val2
        except (TypeError, KeyError):
            raise AttributeConflictError(
                f"Cannot compute max for values: {val1}, {val2}"
            )
    elif strategy == ConflictResolution.MIN:
        try:
            # For UQ, compare means
            v1 = val1["mean"] if isinstance(val1, dict) and "mean" in val1 else val1
            v2 = val2["mean"] if isinstance(val2, dict) and "mean" in val2 else val2
            return val1 if v1 <= v2 else val2
        except (TypeError, KeyError):
            raise AttributeConflictError(
                f"Cannot compute min for values: {val1}, {val2}"
            )
    elif strategy == ConflictResolution.KEEP_BOTH:
        # Return dict with both values
        return {"left": val1, "right": val2}
    else:
        raise ValueError(f"Unknown conflict resolution strategy: {strategy}")


def merge_uncertainty_info(
    uq1: Optional[Dict[str, Any]],
    uq2: Optional[Dict[str, Any]]
) -> Optional[Dict[str, Any]]:
    """Merge uncertainty information from two results.
    
    When combining results with UQ, we need to properly track:
    - Methods used
    - Sample sizes
    - Seeds (if applicable)
    
    Args:
        uq1: UQ info from first result
        uq2: UQ info from second result
        
    Returns:
        Merged UQ information
    """
    if uq1 is None and uq2 is None:
        return None
    
    if uq1 is None:
        return uq2.copy()
    if uq2 is None:
        return uq1.copy()
    
    # Both have UQ - merge
    merged = {
        "combined": True,
        "methods": list(set([uq1.get("method", "unknown"), uq2.get("method", "unknown")])),
        "n_samples": [uq1.get("n_samples"), uq2.get("n_samples")],
    }
    
    # Track seeds if both are present and identical
    seed1 = uq1.get("seed")
    seed2 = uq2.get("seed")
    if seed1 is not None and seed2 is not None and seed1 == seed2:
        merged["seed"] = seed1
    
    return merged
