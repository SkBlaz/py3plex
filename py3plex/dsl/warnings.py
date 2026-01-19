"""Performance and semantic warning system for DSL v2.

This module provides non-blocking warnings for expensive operations,
multilayer semantic issues, and other common pitfalls.

Warnings are:
- Non-blocking (never raise exceptions)
- Suppressible (via context manager or config)
- Actionable (suggest alternatives)
- Context-aware (only trigger when ambiguity is high)
"""

import warnings
import logging
from typing import Any, Dict, List, Optional, Set
from contextlib import contextmanager

logger = logging.getLogger(__name__)


# Global warning suppression state
_SUPPRESSED_WARNINGS: Set[str] = set()


class Py3plexWarning(UserWarning):
    """Base class for py3plex DSL warnings."""
    pass


class PerformanceWarning(Py3plexWarning):
    """Warning for potentially expensive operations."""
    pass


class MultilayerSemanticWarning(Py3plexWarning):
    """Warning for multilayer network semantic issues."""
    pass


@contextmanager
def suppress_warnings(*warning_types: str):
    """Context manager to suppress specific warning types.
    
    Args:
        *warning_types: Warning type names to suppress
            (e.g., "expensive_centrality", "high_uq_samples")
    
    Example:
        >>> from py3plex.dsl.warnings import suppress_warnings
        >>> with suppress_warnings("expensive_centrality"):
        ...     result = Q.nodes().compute("betweenness_centrality").execute(net)
    """
    global _SUPPRESSED_WARNINGS
    old_suppressed = _SUPPRESSED_WARNINGS.copy()
    _SUPPRESSED_WARNINGS.update(warning_types)
    try:
        yield
    finally:
        _SUPPRESSED_WARNINGS = old_suppressed


def is_suppressed(warning_type: str) -> bool:
    """Check if a warning type is currently suppressed.
    
    Args:
        warning_type: Warning type name
        
    Returns:
        True if warning is suppressed
    """
    return warning_type in _SUPPRESSED_WARNINGS


def warn_expensive_centrality(
    measure: str,
    n_nodes: int,
    n_layers: int,
    has_layer_filter: bool,
    suggest_per_layer: bool = True
) -> None:
    """Warn about expensive centrality computation on large multilayer graphs.
    
    Args:
        measure: The centrality measure being computed
        n_nodes: Number of nodes in the network
        n_layers: Number of layers
        has_layer_filter: Whether layers are filtered
        suggest_per_layer: Whether to suggest per-layer computation
    """
    if is_suppressed("expensive_centrality"):
        return
    
    # Estimate cost qualitatively
    if n_nodes * n_layers > 10000:  # Threshold for "large"
        cost_estimate = "VERY EXPENSIVE"
        time_estimate = "minutes to hours"
    elif n_nodes * n_layers > 1000:
        cost_estimate = "EXPENSIVE"
        time_estimate = "seconds to minutes"
    else:
        return  # Not worth warning about
    
    message = (
        f"\n[WARNING]  Performance Warning: {cost_estimate} operation\n"
        f"   Computing '{measure}' on multilayer graph with ~{n_nodes * n_layers} node replicas\n"
        f"   (≈{n_nodes} nodes × {n_layers} layers)\n"
        f"   Estimated time: {time_estimate}\n"
    )
    
    if not has_layer_filter and suggest_per_layer:
        message += (
            f"\n[TIP] Faster alternatives:\n"
            f"   1. Compute per-layer: .per_layer().compute('{measure}').end_grouping()\n"
            f"   2. Filter to specific layers: .from_layers(L['social']).compute('{measure}')\n"
            f"   3. Sample nodes: .where(...filter...).compute('{measure}')\n"
        )
    
    message += "\n[SUPPRESS] To suppress: from py3plex.dsl.warnings import suppress_warnings; with suppress_warnings('expensive_centrality'): ..."
    
    warnings.warn(message, PerformanceWarning, stacklevel=3)


def warn_high_uq_samples(
    n_samples: int,
    measure: str,
    n_nodes: int,
    suggest_fast_path: bool = True
) -> None:
    """Warn about high UQ n_samples on large networks.
    
    Args:
        n_samples: Number of UQ samples
        measure: The measure being computed with UQ
        n_nodes: Number of nodes
        suggest_fast_path: Whether to suggest reducing samples
    """
    if is_suppressed("high_uq_samples"):
        return
    
    # Heuristic: warn if n_samples * n_nodes > threshold
    computational_cost = n_samples * n_nodes
    
    if computational_cost > 100000:  # High cost
        cost_estimate = "VERY HIGH"
        time_estimate = "many minutes"
    elif computational_cost > 10000:
        cost_estimate = "HIGH"
        time_estimate = "several minutes"
    else:
        return  # Acceptable
    
    message = (
        f"\n[WARNING]  Performance Warning: {cost_estimate} UQ cost\n"
        f"   Computing '{measure}' with n_samples={n_samples} on {n_nodes} nodes\n"
        f"   Computational cost: ~{computational_cost} measure evaluations\n"
        f"   Estimated time: {time_estimate}\n"
    )
    
    if suggest_fast_path:
        message += (
            f"\n[TIP] Faster alternatives:\n"
            f"   1. Reduce samples: .uq(method='bootstrap', n_samples=30)\n"
            f"   2. Use faster method: .uq(method='seed', n_samples=10)\n"
            f"   3. Sample nodes first: .where(...).compute('{measure}').uq(...)\n"
        )
    
    message += "\n[SUPPRESS] To suppress: with suppress_warnings('high_uq_samples'): ..."
    
    warnings.warn(message, PerformanceWarning, stacklevel=3)


def warn_global_multilayer_stats(
    operation: str,
    n_layers: int,
    suggest_per_layer: bool = True
) -> None:
    """Warn about global statistics on multilayer networks without layer filtering.
    
    Args:
        operation: The operation being performed (e.g., "community_detection")
        n_layers: Number of layers in the network
        suggest_per_layer: Whether to suggest per-layer analysis
    """
    if is_suppressed("global_multilayer_stats"):
        return
    
    if n_layers < 2:
        return  # Not a multilayer network
    
    message = (
        f"\n[WARNING]  Multilayer Semantic Warning: Global {operation} on multilayer network\n"
        f"   Operating on {n_layers} layers simultaneously without layer filtering\n"
        f"   This may not be what you want - results mix all layers\n"
    )
    
    if suggest_per_layer:
        message += (
            f"\n[TIP] Consider layer-aware analysis:\n"
            f"   1. Per-layer: .per_layer().{operation}().end_grouping()\n"
            f"   2. Specific layers: .from_layers(L['social'] + L['work']).{operation}()\n"
            f"   3. Aggregate first: use aggregation utilities to merge layers\n"
        )
    
    message += "\n[SUPPRESS] To suppress: with suppress_warnings('global_multilayer_stats'): ..."
    
    warnings.warn(message, MultilayerSemanticWarning, stacklevel=3)


def warn_node_replica_confusion(
    operation: str,
    context: Optional[str] = None
) -> None:
    """Warn about node replica vs physical node confusion.
    
    Args:
        operation: The operation that may be affected
        context: Additional context about the confusion
    """
    if is_suppressed("node_replica_confusion"):
        return
    
    message = (
        f"\n[WARNING]  Multilayer Semantic Warning: Node replica vs physical node\n"
        f"   Operation '{operation}' works on node REPLICAS (node + layer pairs)\n"
        f"   In multilayer networks, the same physical node appears in multiple layers\n"
    )
    
    if context:
        message += f"\n   Context: {context}\n"
    
    message += (
        f"\n[CONCEPT] Multilayer concept:\n"
        f"   - Physical node: A unique entity (e.g., 'Alice')\n"
        f"   - Node replica: (physical_node, layer) pair (e.g., ('Alice', 'social'))\n"
        f"   - Most operations work on replicas, not physical nodes\n"
        f"\n[TIP] To work with physical nodes:\n"
        f"   1. Aggregate across layers: result.to_pandas().groupby('id').mean()\n"
        f"   2. Use supra-graph view: aggregation utilities\n"
        f"   3. Filter to single layer: .from_layers(L['social'])\n"
    )
    
    message += "\n[SUPPRESS] To suppress: with suppress_warnings('node_replica_confusion'): ..."
    
    warnings.warn(message, MultilayerSemanticWarning, stacklevel=3)


def warn_degree_ambiguity(
    degree_type: Optional[str] = None,
    has_layer_filter: bool = False
) -> None:
    """Warn about degree meaning ambiguity in multilayer networks.
    
    Args:
        degree_type: The specific degree type if known
        has_layer_filter: Whether layers are filtered
    """
    if is_suppressed("degree_ambiguity"):
        return
    
    if has_layer_filter:
        return  # Less ambiguous with layer filtering
    
    message = (
        f"\n[WARNING]  Multilayer Semantic Warning: Degree ambiguity\n"
        f"   'degree' in multilayer networks can mean:\n"
        f"   - Intra-layer degree: edges within the same layer\n"
        f"   - Inter-layer degree: edges to other layers\n"
        f"   - Aggregate degree: total degree across all layer connections\n"
        f"\n   By default, py3plex computes AGGREGATE degree (most common)\n"
    )
    
    if degree_type:
        message += f"\n   Current computation: {degree_type} degree\n"
    
    message += (
        f"\n[TIP] To be explicit:\n"
        f"   1. Intra-layer only: .per_layer().compute('degree')\n"
        f"   2. Specific layer: .from_layers(L['social']).compute('degree')\n"
        f"   3. Check documentation: help(Q.nodes().compute)\n"
    )
    
    message += "\n[SUPPRESS] To suppress: with suppress_warnings('degree_ambiguity'): ..."
    
    warnings.warn(message, MultilayerSemanticWarning, stacklevel=3)


def warn_coverage_side_effects(
    mode: str,
    n_groups: int,
    n_initial_items: int,
    n_filtered_items: int
) -> None:
    """Warn about coverage filters removing expected nodes.
    
    Args:
        mode: Coverage mode (all, any, at_least, etc.)
        n_groups: Number of groups
        n_initial_items: Number of items before coverage filter
        n_filtered_items: Number of items after coverage filter
    """
    if is_suppressed("coverage_side_effects"):
        return
    
    # Only warn if significant filtering occurred
    if n_initial_items == 0:
        return
    
    pct_removed = (n_initial_items - n_filtered_items) / n_initial_items
    
    if pct_removed > 0.5:  # More than 50% removed
        message = (
            f"\n[WARNING]  Coverage Filter Warning: Significant filtering\n"
            f"   coverage(mode='{mode}') removed {n_initial_items - n_filtered_items} "
            f"of {n_initial_items} items ({pct_removed:.1%})\n"
            f"   across {n_groups} groups\n"
        )
        
        if mode == "all":
            message += (
                f"\n[TIP] mode='all' is STRICT - only keeps items present in ALL {n_groups} groups\n"
                f"   Consider:\n"
                f"   - mode='any': items in at least 1 group\n"
                f"   - mode='at_least', k=2: items in at least 2 groups\n"
                f"   - mode='fraction', p=0.5: items in at least 50% of groups\n"
            )
        
        message += "\n[SUPPRESS] To suppress: with suppress_warnings('coverage_side_effects'): ..."
        
        warnings.warn(message, MultilayerSemanticWarning, stacklevel=3)


def warn_global_community_detection(
    n_layers: int,
    method: str = "leiden"
) -> None:
    """Warn about global vs per-layer community detection.
    
    Args:
        n_layers: Number of layers
        method: Community detection method
    """
    if is_suppressed("global_community_detection"):
        return
    
    if n_layers < 2:
        return
    
    message = (
        f"\n[WARNING]  Multilayer Semantic Warning: Global community detection\n"
        f"   Running '{method}' on {n_layers}-layer network globally\n"
        f"   This finds communities spanning multiple layers simultaneously\n"
        f"   Communities will NOT respect layer boundaries\n"
    )
    
    message += (
        f"\n[CONCEPT] Multilayer community detection:\n"
        f"   - Global: Communities span layers (current behavior)\n"
        f"   - Per-layer: Independent communities per layer\n"
        f"   - Consensus: Combine per-layer results\n"
        f"\n[TIP] Alternatives:\n"
        f"   1. Per-layer: .per_layer().community(method='{method}').end_grouping()\n"
        f"   2. Specific layer: .from_layers(L['social']).community(method='{method}')\n"
        f"   3. If global is intended: explicitly set omega parameter for coupling strength\n"
    )
    
    message += "\n[SUPPRESS] To suppress: with suppress_warnings('global_community_detection'): ..."
    
    warnings.warn(message, MultilayerSemanticWarning, stacklevel=3)
