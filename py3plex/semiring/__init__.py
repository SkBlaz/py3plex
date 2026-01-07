"""Semiring algebra subsystem for py3plex.

This package provides first-class, user-extensible semirings with:
- Formal algebraic specifications (SemiringSpec)
- Bounded verification of semiring laws
- Path and closure computations with provable invariants
- DSL v2 integration (S builder)
- Verification-style tests

Definition (Semiring).
A semiring is a tuple (K, ⊕, ⊗, 0, 1) where K is a set and ⊕, ⊗ are binary operations on K such that:
1) (K, ⊕, 0) is a commutative monoid: ⊕ is associative and commutative, and 0 is the identity (a ⊕ 0 = a).
2) (K, ⊗, 1) is a monoid: ⊗ is associative and 1 is the identity (a ⊗ 1 = 1 ⊗ a = a).
3) ⊗ distributes over ⊕: a ⊗ (b ⊕ c) = (a ⊗ b) ⊕ (a ⊗ c), and (b ⊕ c) ⊗ a = (b ⊗ a) ⊕ (c ⊗ a).
4) 0 is absorbing for ⊗: 0 ⊗ a = a ⊗ 0 = 0.
Note: Some useful semirings relax commutativity of ⊕; therefore this library supports both "strict semiring" and "relaxed semiring" modes via flags.

Package structure:
- core: SemiringSpec dataclass with bounded validation
- registry: Semiring registration and discovery
- types: Type aliases and data structures (EdgeView, LiftFn, PathResult)
- engine: Path and closure algorithms
- pareto: Multiobjective/Pareto frontier support
"""

from .core import SemiringSpec
from .registry import (
    register_semiring,
    get_semiring,
    list_semirings,
)
from .types import (
    EdgeView,
    LiftFn,
    PathResult,
)
from .engine import (
    semiring_paths,
    semiring_closure,
)

__all__ = [
    # Core
    "SemiringSpec",
    # Registry
    "register_semiring",
    "get_semiring",
    "list_semirings",
    # Types
    "EdgeView",
    "LiftFn",
    "PathResult",
    # Engines
    "semiring_paths",
    "semiring_closure",
]
