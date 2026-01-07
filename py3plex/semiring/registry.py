"""Semiring registry for managing and discovering semirings.

This module provides a global registry for semiring specifications,
with built-in semirings registered at import time.
"""

import math
from typing import Dict, List
from .core import SemiringSpec, SemiringValidationError


# Global registry dictionary
_semiring_registry: Dict[str, SemiringSpec] = {}


def register_semiring(spec: SemiringSpec, *, overwrite: bool = False) -> None:
    """Register a semiring in the global registry.
    
    Args:
        spec: SemiringSpec to register
        overwrite: If False, raises error if name already exists
        
    Raises:
        SemiringValidationError: If semiring validation fails or name conflicts
    """
    # Validate the spec before registering
    spec.validate()
    
    if spec.name in _semiring_registry and not overwrite:
        raise SemiringValidationError(
            f"Semiring '{spec.name}' already registered. Use overwrite=True to replace."
        )
    
    _semiring_registry[spec.name] = spec


def get_semiring(name: str) -> SemiringSpec:
    """Get a semiring from the global registry.
    
    Args:
        name: Semiring identifier
        
    Returns:
        SemiringSpec instance
        
    Raises:
        SemiringValidationError: If semiring not found
    """
    if name not in _semiring_registry:
        available = ", ".join(sorted(_semiring_registry.keys()))
        raise SemiringValidationError(
            f"Unknown semiring: '{name}'. Available semirings: {available}"
        )
    return _semiring_registry[name]


def list_semirings() -> List[str]:
    """List all registered semirings in deterministic order.
    
    Returns:
        Sorted list of semiring names
    """
    return sorted(_semiring_registry.keys())


# ============================================================================
# Built-in Semirings
# ============================================================================

def _register_builtins():
    """Register built-in semirings."""
    
    # Min-plus (tropical) semiring for shortest paths
    min_plus = SemiringSpec(
        name="min_plus",
        zero=math.inf,
        one=0.0,
        plus=lambda a, b: min(a, b),
        times=lambda a, b: math.inf if math.isinf(a) or math.isinf(b) else a + b,
        strict=True,
        is_idempotent_plus=True,
        is_commutative_plus=True,
        is_commutative_times=True,
        description="Min-plus (tropical) semiring for shortest paths",
        examples=(0.0, 1.0, 2.0, 5.0, 10.0, math.inf),
        leq=lambda a, b: a <= b,
    )
    register_semiring(min_plus, overwrite=False)
    
    # Boolean semiring for reachability
    boolean = SemiringSpec(
        name="boolean",
        zero=False,
        one=True,
        plus=lambda a, b: a or b,
        times=lambda a, b: a and b,
        strict=True,
        is_idempotent_plus=True,
        is_commutative_plus=True,
        is_commutative_times=True,
        description="Boolean semiring for reachability",
        examples=(True, False),
        eq=lambda a, b: a == b,
        leq=lambda a, b: (not a) or b,  # False <= True
    )
    register_semiring(boolean, overwrite=False)
    
    # Max-times semiring for reliability
    max_times = SemiringSpec(
        name="max_times",
        zero=0.0,
        one=1.0,
        plus=lambda a, b: max(a, b),
        times=lambda a, b: a * b,
        strict=True,
        is_idempotent_plus=True,
        is_commutative_plus=True,
        is_commutative_times=True,
        description="Max-times semiring for most reliable paths",
        examples=(0.0, 0.1, 0.5, 0.9, 1.0),
        leq=lambda a, b: a <= b,
    )
    register_semiring(max_times, overwrite=False)
    
    # Tropical lexicographic semiring
    def tropical_lex_plus(a, b):
        """Lexicographic min: compare first by cost, then by switches."""
        cost_a, switches_a = a
        cost_b, switches_b = b
        if cost_a < cost_b:
            return a
        elif cost_a > cost_b:
            return b
        else:
            # Equal cost: prefer fewer switches
            return a if switches_a <= switches_b else b
    
    def tropical_lex_times(a, b):
        """Componentwise addition."""
        return (a[0] + b[0], a[1] + b[1])
    
    def tropical_lex_eq(a, b):
        """Tuple equality."""
        return a[0] == b[0] and a[1] == b[1]
    
    def tropical_lex_leq(a, b):
        """Lexicographic order."""
        if a[0] < b[0]:
            return True
        elif a[0] > b[0]:
            return False
        else:
            return a[1] <= b[1]
    
    tropical_lex = SemiringSpec(
        name="tropical_lex",
        zero=(math.inf, math.inf),
        one=(0.0, 0),
        plus=tropical_lex_plus,
        times=tropical_lex_times,
        strict=False,  # ⊕ is commutative but we won't enforce in strict mode
        is_idempotent_plus=False,
        is_commutative_plus=True,
        is_commutative_times=True,
        description="Tropical lexicographic semiring with (cost, layer_switches)",
        examples=(
            (0.0, 0), (1.0, 0), (2.0, 1), (5.0, 2), (10.0, 5), (math.inf, math.inf)
        ),
        eq=tropical_lex_eq,
        leq=tropical_lex_leq,
    )
    register_semiring(tropical_lex, overwrite=False)


# Register built-ins on module import
_register_builtins()
