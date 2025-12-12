"""Pattern Matching API for py3plex DSL.

This module provides a first-class pattern matching Builder API that enables
users to express graph motifs and paths (optionally multilayer-aware) and
execute them efficiently.

Example:
    >>> from py3plex.dsl import Q
    >>> 
    >>> # Simple edge pattern
    >>> pq = (
    ...     Q.pattern()
    ...      .node("a").where(layer="social", degree__gt=3)
    ...      .node("b").where(layer="social")
    ...      .edge("a", "b", directed=False).where(weight__gt=0.2)
    ...      .returning("a", "b")
    ... )
    >>> 
    >>> matches = pq.execute(network)
    >>> df = matches.to_pandas()
    >>> nodes = matches.to_nodes()
"""

from .ir import (
    PatternNode,
    PatternEdge,
    PatternGraph,
    MatchRow,
    LayerConstraint,
    EdgeLayerConstraint,
    Predicate,
)

from .builder import (
    PatternQueryBuilder,
    PatternNodeBuilder,
    PatternEdgeBuilder,
)

from .result import PatternQueryResult

from .compiler import PatternPlan, compile_pattern

from .engine import match_pattern

__all__ = [
    # IR
    "PatternNode",
    "PatternEdge",
    "PatternGraph",
    "MatchRow",
    "LayerConstraint",
    "EdgeLayerConstraint",
    "Predicate",
    # Builder
    "PatternQueryBuilder",
    "PatternNodeBuilder",
    "PatternEdgeBuilder",
    # Result
    "PatternQueryResult",
    # Compiler
    "PatternPlan",
    "compile_pattern",
    # Engine
    "match_pattern",
]
