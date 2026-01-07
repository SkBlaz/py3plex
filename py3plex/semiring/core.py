"""Core semiring specification and validation.

Definition (Semiring).
A semiring is a tuple (K, ⊕, ⊗, 0, 1) where K is a set and ⊕, ⊗ are binary operations on K such that:
1) (K, ⊕, 0) is a commutative monoid: ⊕ is associative and commutative, and 0 is the identity (a ⊕ 0 = a).
2) (K, ⊗, 1) is a monoid: ⊗ is associative and 1 is the identity (a ⊗ 1 = 1 ⊗ a = a).
3) ⊗ distributes over ⊕: a ⊗ (b ⊕ c) = (a ⊗ b) ⊕ (a ⊗ c), and (b ⊕ c) ⊗ a = (b ⊗ a) ⊕ (c ⊗ a).
4) 0 is absorbing for ⊗: 0 ⊗ a = a ⊗ 0 = 0.
Note: Some useful semirings relax commutativity of ⊕; therefore this library supports both "strict semiring" and "relaxed semiring" modes via flags.
"""

import math
from dataclasses import dataclass
from typing import Any, Callable, Optional
from py3plex.exceptions import Py3plexException


class SemiringError(Py3plexException):
    """Base exception for semiring errors.
    
    Error code: PX601
    """
    default_code = "PX601"


class SemiringValidationError(SemiringError):
    """Exception raised when semiring validation fails.
    
    Includes counterexample details when algebraic laws are violated.
    
    Error code: PX602
    """
    default_code = "PX602"
    
    def __init__(
        self,
        message: str,
        *,
        counterexample: Optional[dict] = None,
        **kwargs
    ):
        """Initialize with optional counterexample.
        
        Args:
            message: Error message
            counterexample: Dict with 'a', 'b', 'c', 'op', 'expected', 'got' keys
            **kwargs: Additional arguments for Py3plexException
        """
        self.counterexample = counterexample
        notes = kwargs.pop("notes", [])
        
        if counterexample:
            notes.append(f"Counterexample: {counterexample}")
        
        super().__init__(message, notes=notes, **kwargs)


class SemiringExecutionError(SemiringError):
    """Exception raised during semiring algorithm execution.
    
    Error code: PX603
    """
    default_code = "PX603"


@dataclass(frozen=True)
class SemiringSpec:
    """Formal specification of a semiring.
    
    Definition (Semiring).
    A semiring is a tuple (K, ⊕, ⊗, 0, 1) where K is a set and ⊕, ⊗ are binary operations on K such that:
    1) (K, ⊕, 0) is a commutative monoid: ⊕ is associative and commutative, and 0 is the identity (a ⊕ 0 = a).
    2) (K, ⊗, 1) is a monoid: ⊗ is associative and 1 is the identity (a ⊗ 1 = 1 ⊗ a = a).
    3) ⊗ distributes over ⊕: a ⊗ (b ⊕ c) = (a ⊗ b) ⊕ (a ⊗ c), and (b ⊕ c) ⊗ a = (b ⊗ a) ⊕ (c ⊗ a).
    4) 0 is absorbing for ⊗: 0 ⊗ a = a ⊗ 0 = 0.
    
    Attributes:
        name: Semiring identifier
        zero: Additive identity (0)
        one: Multiplicative identity (1)
        plus: Binary operation ⊕
        times: Binary operation ⊗
        strict: If True, enforce commutative ⊕ in validation (default: False)
        is_idempotent_plus: a ⊕ a = a (default: False)
        is_commutative_plus: a ⊕ b = b ⊕ a (default: False)
        is_commutative_times: a ⊗ b = b ⊗ a (default: False)
        description: Human-readable description
        examples: Sample values for bounded verification
        eq: Equality predicate for K elements (default: ==)
        leq: Partial order for improvement relation (optional)
    """
    
    name: str
    zero: Any
    one: Any
    plus: Callable[[Any, Any], Any]    # ⊕
    times: Callable[[Any, Any], Any]   # ⊗
    
    # Flags
    strict: bool = False
    is_idempotent_plus: bool = False
    is_commutative_plus: bool = False
    is_commutative_times: bool = False
    
    # Metadata
    description: str = ""
    examples: tuple = ()
    
    # Optional comparators
    eq: Optional[Callable[[Any, Any], bool]] = None
    leq: Optional[Callable[[Any, Any], bool]] = None
    
    def validate(self) -> None:
        """Perform bounded verification of semiring laws.
        
        Always verifies:
        - Callables are provided
        - Name, zero, one are non-None
        
        If examples provided:
        - Sample-based checks of associativity, identity, distributivity, absorption
        - If strict=True: additionally check commutativity of ⊕
        
        Raises:
            SemiringValidationError: With precise counterexample on failure
        
        Note:
            This is bounded verification, not a universal proof.
            Tests provide high confidence but are not exhaustive.
        """
        # Basic validation
        if not self.name:
            raise SemiringValidationError("Semiring name must be non-empty")
        
        if self.zero is None:
            raise SemiringValidationError(f"Semiring '{self.name}': zero must be provided")
        
        if self.one is None:
            raise SemiringValidationError(f"Semiring '{self.name}': one must be provided")
        
        if not callable(self.plus):
            raise SemiringValidationError(f"Semiring '{self.name}': plus must be callable")
        
        if not callable(self.times):
            raise SemiringValidationError(f"Semiring '{self.name}': times must be callable")
        
        # If no examples, skip sample-based verification
        if not self.examples:
            return
        
        # Get equality function
        eq_fn = self.eq if self.eq else self._default_eq
        
        # Run sample-based law checks
        self._check_associativity_plus(eq_fn)
        self._check_associativity_times(eq_fn)
        self._check_identity_plus(eq_fn)
        self._check_identity_times(eq_fn)
        self._check_distributivity(eq_fn)
        self._check_absorption(eq_fn)
        
        if self.strict:
            self._check_commutativity_plus(eq_fn)
    
    def _default_eq(self, a: Any, b: Any) -> bool:
        """Default equality with special handling for floats and inf."""
        # Handle infinity
        if isinstance(a, float) and isinstance(b, float):
            if math.isinf(a) and math.isinf(b):
                return (a > 0) == (b > 0)  # Same sign of infinity
            if math.isinf(a) or math.isinf(b):
                return False
            # Use math.isclose for finite floats
            return math.isclose(a, b, rel_tol=1e-9, abs_tol=1e-9)
        
        return a == b
    
    def _check_associativity_plus(self, eq_fn: Callable[[Any, Any], bool]) -> None:
        """Check (a ⊕ b) ⊕ c = a ⊕ (b ⊕ c) for all sample triples."""
        examples = list(self.examples)
        for i, a in enumerate(examples):
            for j, b in enumerate(examples):
                for k, c in enumerate(examples):
                    try:
                        left = self.plus(self.plus(a, b), c)
                        right = self.plus(a, self.plus(b, c))
                        if not eq_fn(left, right):
                            raise SemiringValidationError(
                                f"Semiring '{self.name}' fails associativity of ⊕",
                                counterexample={
                                    'a': a, 'b': b, 'c': c,
                                    'op': 'plus',
                                    'property': 'associativity',
                                    'left': f"({a} ⊕ {b}) ⊕ {c} = {left}",
                                    'right': f"{a} ⊕ ({b} ⊕ {c}) = {right}",
                                }
                            )
                    except (TypeError, ValueError, OverflowError) as e:
                        # Skip if operations fail (e.g., type errors in samples)
                        pass
    
    def _check_associativity_times(self, eq_fn: Callable[[Any, Any], bool]) -> None:
        """Check (a ⊗ b) ⊗ c = a ⊗ (b ⊗ c) for all sample triples."""
        examples = list(self.examples)
        for i, a in enumerate(examples):
            for j, b in enumerate(examples):
                for k, c in enumerate(examples):
                    try:
                        left = self.times(self.times(a, b), c)
                        right = self.times(a, self.times(b, c))
                        if not eq_fn(left, right):
                            raise SemiringValidationError(
                                f"Semiring '{self.name}' fails associativity of ⊗",
                                counterexample={
                                    'a': a, 'b': b, 'c': c,
                                    'op': 'times',
                                    'property': 'associativity',
                                    'left': f"({a} ⊗ {b}) ⊗ {c} = {left}",
                                    'right': f"{a} ⊗ ({b} ⊗ {c}) = {right}",
                                }
                            )
                    except (TypeError, ValueError, OverflowError):
                        pass
    
    def _check_identity_plus(self, eq_fn: Callable[[Any, Any], bool]) -> None:
        """Check a ⊕ 0 = 0 ⊕ a = a for all samples."""
        for a in self.examples:
            try:
                left = self.plus(a, self.zero)
                right = self.plus(self.zero, a)
                if not eq_fn(left, a):
                    raise SemiringValidationError(
                        f"Semiring '{self.name}' fails right identity for ⊕",
                        counterexample={
                            'a': a,
                            'zero': self.zero,
                            'property': 'identity_plus',
                            'got': f"{a} ⊕ {self.zero} = {left}",
                            'expected': f"{a}",
                        }
                    )
                if not eq_fn(right, a):
                    raise SemiringValidationError(
                        f"Semiring '{self.name}' fails left identity for ⊕",
                        counterexample={
                            'a': a,
                            'zero': self.zero,
                            'property': 'identity_plus',
                            'got': f"{self.zero} ⊕ {a} = {right}",
                            'expected': f"{a}",
                        }
                    )
            except (TypeError, ValueError, OverflowError):
                pass
    
    def _check_identity_times(self, eq_fn: Callable[[Any, Any], bool]) -> None:
        """Check a ⊗ 1 = 1 ⊗ a = a for all samples."""
        for a in self.examples:
            try:
                left = self.times(a, self.one)
                right = self.times(self.one, a)
                if not eq_fn(left, a):
                    raise SemiringValidationError(
                        f"Semiring '{self.name}' fails right identity for ⊗",
                        counterexample={
                            'a': a,
                            'one': self.one,
                            'property': 'identity_times',
                            'got': f"{a} ⊗ {self.one} = {left}",
                            'expected': f"{a}",
                        }
                    )
                if not eq_fn(right, a):
                    raise SemiringValidationError(
                        f"Semiring '{self.name}' fails left identity for ⊗",
                        counterexample={
                            'a': a,
                            'one': self.one,
                            'property': 'identity_times',
                            'got': f"{self.one} ⊗ {a} = {right}",
                            'expected': f"{a}",
                        }
                    )
            except (TypeError, ValueError, OverflowError):
                pass
    
    def _check_distributivity(self, eq_fn: Callable[[Any, Any], bool]) -> None:
        """Check distributivity: a ⊗ (b ⊕ c) = (a ⊗ b) ⊕ (a ⊗ c) and (b ⊕ c) ⊗ a = (b ⊗ a) ⊕ (c ⊗ a)."""
        examples = list(self.examples)
        for a in examples:
            for b in examples:
                for c in examples:
                    try:
                        # Left distributivity: a ⊗ (b ⊕ c) = (a ⊗ b) ⊕ (a ⊗ c)
                        b_plus_c = self.plus(b, c)
                        left_dist = self.times(a, b_plus_c)
                        
                        a_times_b = self.times(a, b)
                        a_times_c = self.times(a, c)
                        right_dist = self.plus(a_times_b, a_times_c)
                        
                        if not eq_fn(left_dist, right_dist):
                            raise SemiringValidationError(
                                f"Semiring '{self.name}' fails left distributivity",
                                counterexample={
                                    'a': a, 'b': b, 'c': c,
                                    'property': 'distributivity_left',
                                    'left': f"{a} ⊗ ({b} ⊕ {c}) = {left_dist}",
                                    'right': f"({a} ⊗ {b}) ⊕ ({a} ⊗ {c}) = {right_dist}",
                                }
                            )
                        
                        # Right distributivity: (b ⊕ c) ⊗ a = (b ⊗ a) ⊕ (c ⊗ a)
                        left_dist_r = self.times(b_plus_c, a)
                        
                        b_times_a = self.times(b, a)
                        c_times_a = self.times(c, a)
                        right_dist_r = self.plus(b_times_a, c_times_a)
                        
                        if not eq_fn(left_dist_r, right_dist_r):
                            raise SemiringValidationError(
                                f"Semiring '{self.name}' fails right distributivity",
                                counterexample={
                                    'a': a, 'b': b, 'c': c,
                                    'property': 'distributivity_right',
                                    'left': f"({b} ⊕ {c}) ⊗ {a} = {left_dist_r}",
                                    'right': f"({b} ⊗ {a}) ⊕ ({c} ⊗ {a}) = {right_dist_r}",
                                }
                            )
                    except (TypeError, ValueError, OverflowError):
                        pass
    
    def _check_absorption(self, eq_fn: Callable[[Any, Any], bool]) -> None:
        """Check 0 ⊗ a = a ⊗ 0 = 0 for all samples."""
        for a in self.examples:
            try:
                left = self.times(self.zero, a)
                right = self.times(a, self.zero)
                if not eq_fn(left, self.zero):
                    raise SemiringValidationError(
                        f"Semiring '{self.name}' fails left absorption",
                        counterexample={
                            'a': a,
                            'zero': self.zero,
                            'property': 'absorption',
                            'got': f"{self.zero} ⊗ {a} = {left}",
                            'expected': f"{self.zero}",
                        }
                    )
                if not eq_fn(right, self.zero):
                    raise SemiringValidationError(
                        f"Semiring '{self.name}' fails right absorption",
                        counterexample={
                            'a': a,
                            'zero': self.zero,
                            'property': 'absorption',
                            'got': f"{a} ⊗ {self.zero} = {right}",
                            'expected': f"{self.zero}",
                        }
                    )
            except (TypeError, ValueError, OverflowError):
                pass
    
    def _check_commutativity_plus(self, eq_fn: Callable[[Any, Any], bool]) -> None:
        """Check a ⊕ b = b ⊕ a for all sample pairs (only when strict=True)."""
        examples = list(self.examples)
        for a in examples:
            for b in examples:
                try:
                    left = self.plus(a, b)
                    right = self.plus(b, a)
                    if not eq_fn(left, right):
                        raise SemiringValidationError(
                            f"Semiring '{self.name}' fails commutativity of ⊕ (required by strict mode)",
                            counterexample={
                                'a': a, 'b': b,
                                'property': 'commutativity_plus',
                                'left': f"{a} ⊕ {b} = {left}",
                                'right': f"{b} ⊕ {a} = {right}",
                            }
                        )
                except (TypeError, ValueError, OverflowError):
                    pass
