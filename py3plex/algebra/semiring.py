"""Semiring protocol and built-in semiring implementations.

A semiring is an algebraic structure (S, ⊕, ⊗, 0, 1) where:
- ⊕ (add) is an associative, commutative binary operation with identity 0
- ⊗ (mul) is an associative binary operation with identity 1
- ⊗ distributes over ⊕
- 0 is an annihilator for ⊗: 0 ⊗ a = a ⊗ 0 = 0

Semirings power generic path algorithms:
- Boolean: reachability (path existence)
- Min-plus (tropical): shortest paths
- Max-plus: longest/best paths
- Max-times: most reliable paths (product of probabilities)
"""

import math
from typing import Any, Dict, Optional, Protocol
from dataclasses import dataclass, field


class Semiring(Protocol):
    """Protocol defining the semiring interface.
    
    All semirings must implement add, mul, zero, and one operations.
    Optional: better() for ordering elements, props for metadata.
    """
    
    name: str
    
    def add(self, a: Any, b: Any) -> Any:
        """Semiring addition (⊕)."""
        ...
    
    def mul(self, a: Any, b: Any) -> Any:
        """Semiring multiplication (⊗)."""
        ...
    
    def zero(self) -> Any:
        """Additive identity."""
        ...
    
    def one(self) -> Any:
        """Multiplicative identity."""
        ...
    
    def better(self, a: Any, b: Any) -> bool:
        """Return True if a is "better" than b for ordering (optional).
        
        Used for:
        - Priority queue ordering in Dijkstra-like algorithms
        - Tie-breaking in k-best path finding
        
        Semantics:
        - min_plus: smaller is better (a < b)
        - max_plus/max_times: larger is better (a > b)
        - boolean: any consistent ordering
        """
        ...
    
    @property
    def props(self) -> Dict[str, Any]:
        """Metadata properties for algorithm selection (optional).
        
        Common properties:
        - commutative_add: bool (is ⊕ commutative? usually True)
        - idempotent_add: bool (does a ⊕ a = a?)
        - monotone: bool (does a ⊕ b >= a and a ⊕ b >= b in some order?)
        - complete: bool (do all sequences converge?)
        - closed: bool (is Kleene star well-defined?)
        - supports_k_best: bool (can we enumerate k distinct paths?)
        """
        ...


@dataclass
class BooleanSemiring:
    """Boolean semiring for reachability.
    
    - add = OR (∨)
    - mul = AND (∧)
    - zero = False
    - one = True
    
    Properties:
    - idempotent_add: True (a ∨ a = a)
    - commutative_add: True
    - closed: True
    """
    
    name: str = "boolean"
    _props: Dict[str, Any] = field(default_factory=lambda: {
        "commutative_add": True,
        "idempotent_add": True,
        "monotone": True,
        "complete": True,
        "closed": True,
        "supports_k_best": False,
    })
    
    def add(self, a: bool, b: bool) -> bool:
        """Boolean OR."""
        return a or b
    
    def mul(self, a: bool, b: bool) -> bool:
        """Boolean AND."""
        return a and b
    
    def zero(self) -> bool:
        """False (no path)."""
        return False
    
    def one(self) -> bool:
        """True (empty/zero-length path)."""
        return True
    
    def better(self, a: bool, b: bool) -> bool:
        """True is better than False."""
        return a and not b
    
    @property
    def props(self) -> Dict[str, Any]:
        return self._props


@dataclass
class MinPlusSemiring:
    """Min-plus (tropical) semiring for shortest paths.
    
    - add = min
    - mul = + (addition)
    - zero = +∞
    - one = 0
    
    Properties:
    - idempotent_add: True (min(a, a) = a)
    - monotone: True (min(a, b) <= a and min(a, b) <= b)
    - supports Dijkstra with non-negative weights
    """
    
    name: str = "min_plus"
    _props: Dict[str, Any] = field(default_factory=lambda: {
        "commutative_add": True,
        "idempotent_add": True,
        "monotone": True,
        "complete": True,
        "closed": False,  # Negative cycles can cause issues
        "supports_k_best": True,
    })
    
    def add(self, a: float, b: float) -> float:
        """Min operation."""
        return min(a, b)
    
    def mul(self, a: float, b: float) -> float:
        """Addition."""
        if math.isinf(a) or math.isinf(b):
            return math.inf
        return a + b
    
    def zero(self) -> float:
        """+∞ (infinite distance)."""
        return math.inf
    
    def one(self) -> float:
        """0 (zero distance)."""
        return 0.0
    
    def better(self, a: float, b: float) -> bool:
        """Smaller is better."""
        return a < b
    
    @property
    def props(self) -> Dict[str, Any]:
        return self._props


@dataclass
class MaxPlusSemiring:
    """Max-plus semiring for longest/best paths.
    
    - add = max
    - mul = + (addition)
    - zero = -∞
    - one = 0
    
    Useful for:
    - Longest paths
    - Optimization problems
    """
    
    name: str = "max_plus"
    _props: Dict[str, Any] = field(default_factory=lambda: {
        "commutative_add": True,
        "idempotent_add": True,
        "monotone": True,
        "complete": True,
        "closed": False,  # Positive cycles can cause issues
        "supports_k_best": True,
    })
    
    def add(self, a: float, b: float) -> float:
        """Max operation."""
        return max(a, b)
    
    def mul(self, a: float, b: float) -> float:
        """Addition."""
        if math.isinf(a) and a < 0:
            return a
        if math.isinf(b) and b < 0:
            return b
        return a + b
    
    def zero(self) -> float:
        """-∞."""
        return -math.inf
    
    def one(self) -> float:
        """0."""
        return 0.0
    
    def better(self, a: float, b: float) -> bool:
        """Larger is better."""
        return a > b
    
    @property
    def props(self) -> Dict[str, Any]:
        return self._props


@dataclass
class MaxTimesSemiring:
    """Max-times semiring for most reliable paths.
    
    - add = max
    - mul = * (multiplication)
    - zero = 0
    - one = 1
    
    Useful for:
    - Reliability analysis (edge weights as probabilities)
    - Finding most reliable path (product of edge probabilities)
    """
    
    name: str = "max_times"
    _props: Dict[str, Any] = field(default_factory=lambda: {
        "commutative_add": True,
        "idempotent_add": True,
        "monotone": True,
        "complete": True,
        "closed": True,
        "supports_k_best": True,
    })
    
    def add(self, a: float, b: float) -> float:
        """Max operation."""
        return max(a, b)
    
    def mul(self, a: float, b: float) -> float:
        """Multiplication."""
        return a * b
    
    def zero(self) -> float:
        """0 (no reliability)."""
        return 0.0
    
    def one(self) -> float:
        """1 (perfect reliability)."""
        return 1.0
    
    def better(self, a: float, b: float) -> bool:
        """Larger is better."""
        return a > b
    
    @property
    def props(self) -> Dict[str, Any]:
        return self._props
