"""Pattern-matching DSL primitives for motif, path, and constraint queries.

This package contains the IR, builder API, compiler, and execution engine for
py3plex pattern matching.
"""

from .ir import (
    AllDistinctConstraint,
    EdgeLayerConstraint,
    LayerConstraint,
    MatchRow,
    NotEqualConstraint,
    PatternEdge,
    PatternGraph,
    PatternNode,
    Predicate,
)
from .builder import PatternEdgeBuilder, PatternNodeBuilder, PatternQueryBuilder
from .result import PatternQueryResult
from .compiler import PatternPlan, compile_pattern
from .engine import match_pattern

__all__ = [
    "PatternNode",
    "PatternEdge",
    "PatternGraph",
    "MatchRow",
    "LayerConstraint",
    "EdgeLayerConstraint",
    "Predicate",
    "NotEqualConstraint",
    "AllDistinctConstraint",
    "PatternQueryBuilder",
    "PatternNodeBuilder",
    "PatternEdgeBuilder",
    "PatternQueryResult",
    "PatternPlan",
    "compile_pattern",
    "match_pattern",
]
