"""Semiring algebra layer for py3plex.

This package provides a comprehensive semiring/algebra framework for multilayer
network analysis, integrated with DSL v2.

Core components:
- Semiring protocol and built-in semirings (boolean, min_plus, max_plus, max_times)
- Registry for semiring management
- Weight lifting specifications for edge attribute extraction
- Generic path solvers (SSSP, APSP) powered by semiring algebra
- Kleene star / transitive closure operations
- Fixed-point iteration engine
- Backend dispatch (graph-based, matrix placeholder)
- Witness tracking for path reconstruction

Integration points:
- DSL v2 builder API (S namespace)
- Layer algebra (L[...] expressions)
- QueryResult + provenance
- Uncertainty quantification (UQ)
- Backward compatibility with P.shortest
"""

from .semiring import (
    Semiring,
    BooleanSemiring,
    MinPlusSemiring,
    MaxPlusSemiring,
    MaxTimesSemiring,
)

from .registry import (
    register_semiring,
    get_semiring,
    list_semirings,
    semiring_registry,
)

from .lift import (
    WeightLiftSpec,
    lift_edge_value,
)

__all__ = [
    # Semiring protocol
    "Semiring",
    # Built-in semirings
    "BooleanSemiring",
    "MinPlusSemiring",
    "MaxPlusSemiring",
    "MaxTimesSemiring",
    # Registry
    "register_semiring",
    "get_semiring",
    "list_semirings",
    "semiring_registry",
    # Weight lifting
    "WeightLiftSpec",
    "lift_edge_value",
]
