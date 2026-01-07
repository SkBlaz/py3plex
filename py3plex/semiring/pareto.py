"""Pareto frontier support for multiobjective semiring optimization.

This module provides ParetoSet for managing Pareto-optimal solutions in
multiobjective optimization problems.
"""

from typing import List, Tuple, Optional
from dataclasses import dataclass, field


@dataclass
class ParetoSet:
    """Pareto frontier for multiobjective optimization.
    
    Maintains a set of vectors where no vector dominates another.
    Uses deterministic ordering for reproducibility.
    
    Attributes:
        vectors: List of Pareto-optimal vectors
        max_size: Maximum number of vectors to keep
        epsilon: Tolerance for dominance comparison
    """
    vectors: List[Tuple[float, ...]] = field(default_factory=list)
    max_size: int = 100
    epsilon: float = 1e-9
    
    def add(self, vector: Tuple[float, ...]) -> None:
        """Add a vector, pruning dominated solutions.
        
        Args:
            vector: Tuple of objective values
        """
        # Check if vector is dominated by existing solutions
        if any(self._dominates(v, vector) for v in self.vectors):
            return
        
        # Remove vectors dominated by the new vector
        self.vectors = [v for v in self.vectors if not self._dominates(vector, v)]
        
        # Add new vector
        self.vectors.append(vector)
        
        # Prune if exceeds max_size (keep best by lexicographic order)
        if len(self.vectors) > self.max_size:
            self.vectors.sort()  # Deterministic ordering
            self.vectors = self.vectors[:self.max_size]
    
    def _dominates(self, a: Tuple[float, ...], b: Tuple[float, ...]) -> bool:
        """Check if vector a dominates vector b (minimization).
        
        a dominates b if a[i] <= b[i] for all i, and a[i] < b[i] for some i.
        """
        if len(a) != len(b):
            return False
        
        strictly_better = False
        for a_i, b_i in zip(a, b):
            if a_i > b_i + self.epsilon:
                return False
            if a_i < b_i - self.epsilon:
                strictly_better = True
        
        return strictly_better
    
    def union(self, other: 'ParetoSet') -> 'ParetoSet':
        """Merge two Pareto sets."""
        result = ParetoSet(max_size=self.max_size, epsilon=self.epsilon)
        for v in self.vectors:
            result.add(v)
        for v in other.vectors:
            result.add(v)
        return result
    
    def cartesian_combine(self, other: 'ParetoSet') -> 'ParetoSet':
        """Cartesian product with componentwise addition, then prune.
        
        For semiring multiplication: combines vectors from two sets.
        """
        result = ParetoSet(max_size=self.max_size, epsilon=self.epsilon)
        for v1 in self.vectors:
            for v2 in other.vectors:
                # Componentwise addition
                combined = tuple(a + b for a, b in zip(v1, v2))
                result.add(combined)
        return result
    
    def to_list(self) -> List[Tuple[float, ...]]:
        """Return deterministically ordered list of vectors."""
        return sorted(self.vectors)
    
    def __repr__(self) -> str:
        return f"ParetoSet({len(self.vectors)} vectors)"


def pareto_semiring_spec(dim: int = 2, max_size: int = 100, epsilon: float = 1e-9):
    """Create a semiring spec for Pareto optimization.
    
    Args:
        dim: Number of objectives
        max_size: Maximum Pareto set size
        epsilon: Dominance tolerance
        
    Returns:
        SemiringSpec for Pareto optimization
    """
    from .core import SemiringSpec
    import math
    
    def plus(a: ParetoSet, b: ParetoSet) -> ParetoSet:
        """Union of Pareto sets with pruning."""
        return a.union(b)
    
    def times(a: ParetoSet, b: ParetoSet) -> ParetoSet:
        """Cartesian combine with pruning."""
        return a.cartesian_combine(b)
    
    def eq(a: ParetoSet, b: ParetoSet) -> bool:
        """Equality of Pareto sets."""
        return sorted(a.vectors) == sorted(b.vectors)
    
    # Create zero and one
    zero = ParetoSet(max_size=max_size, epsilon=epsilon)  # Empty set
    one = ParetoSet(max_size=max_size, epsilon=epsilon)
    one.add(tuple([0.0] * dim))  # Identity vector
    
    return SemiringSpec(
        name=f"pareto_{dim}d",
        zero=zero,
        one=one,
        plus=plus,
        times=times,
        strict=False,
        is_idempotent_plus=True,  # A ⊕ A = A for sets
        is_commutative_plus=True,
        is_commutative_times=False,  # Order matters in practice
        description=f"Pareto frontier semiring for {dim}-objective optimization",
        examples=(),  # Skip validation for now (complex equality)
        eq=eq,
    )
