#!/usr/bin/env python3
"""Property-based tests for the semiring module.

This module tests algebraic laws and invariants of semiring operations
using hypothesis for property-based testing.

Key properties tested:
- Associativity of addition and multiplication
- Identity elements
- Distributivity
- Absorption
- Idempotency (when applicable)
- Commutativity (when applicable)
"""

import pytest
import math
from hypothesis import given, settings, assume, HealthCheck, strategies as st
from hypothesis import note

# Import semiring module
try:
    from py3plex.semiring import (
        SemiringSpec,
        SemiringValidationError,
        register_semiring,
        get_semiring,
        list_semirings,
    )
    SEMIRING_AVAILABLE = True
except ImportError:
    SEMIRING_AVAILABLE = False
    pytest.skip("Semiring module not available", allow_module_level=True)


# ============================================================================
# Helper Strategies
# ============================================================================

@st.composite
def finite_floats(draw, min_value=0.0, max_value=1000.0):
    """Generate finite floats for testing."""
    return draw(st.floats(
        min_value=min_value,
        max_value=max_value,
        allow_nan=False,
        allow_infinity=False
    ))


@st.composite
def semiring_elements(draw, semiring_name="min_plus"):
    """Generate valid elements for a specific semiring."""
    if semiring_name == "min_plus":
        # Min-plus semiring: non-negative reals + infinity
        return draw(st.one_of(
            st.just(math.inf),
            st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False)
        ))
    elif semiring_name == "boolean":
        return draw(st.booleans())
    elif semiring_name == "max_times":
        # Max-times: [0, 1] interval
        return draw(st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False))
    else:
        # Default: small positive floats
        return draw(st.floats(min_value=0.0, max_value=10.0, allow_nan=False, allow_infinity=False))


# ============================================================================
# Property Tests: Semiring Registration
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(
    name=st.text(min_size=1, max_size=20, alphabet=st.characters(min_codepoint=97, max_codepoint=122))
)
def test_semiring_spec_requires_name(name):
    """Property: SemiringSpec requires a non-empty name."""
    spec = SemiringSpec(
        name=name,
        zero=0.0,
        one=1.0,
        plus=lambda a, b: a + b,
        times=lambda a, b: a * b,
    )
    assert spec.name == name
    assert len(spec.name) > 0


@pytest.mark.property
def test_semiring_registry_persistence():
    """Property: Registered semirings persist and can be retrieved."""
    # Get list of semirings before
    initial_semirings = set(list_semirings())
    
    # All initial semirings should be retrievable
    for name in initial_semirings:
        spec = get_semiring(name)
        assert spec.name == name
        assert spec.zero is not None
        assert spec.one is not None
        assert callable(spec.plus)
        assert callable(spec.times)


@pytest.mark.property
def test_semiring_list_is_sorted():
    """Property: list_semirings() returns sorted names."""
    names = list_semirings()
    assert names == sorted(names), "Semiring names should be sorted"


# ============================================================================
# Property Tests: Algebraic Laws for Min-Plus Semiring
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=50)
@given(
    a=semiring_elements("min_plus"),
    b=semiring_elements("min_plus"),
    c=semiring_elements("min_plus")
)
def test_min_plus_associativity_plus(a, b, c):
    """Property: (a ⊕ b) ⊕ c = a ⊕ (b ⊕ c) for min-plus."""
    spec = get_semiring("min_plus")
    
    left = spec.plus(spec.plus(a, b), c)
    right = spec.plus(a, spec.plus(b, c))
    
    # Use approximate equality for floats
    if math.isinf(left) and math.isinf(right):
        assert True  # Both infinity
    elif math.isinf(left) or math.isinf(right):
        assert False, f"One side infinite: {left} != {right}"
    else:
        assert math.isclose(left, right, rel_tol=1e-9), \
            f"Associativity failed: ({a} ⊕ {b}) ⊕ {c} = {left} != {right}"


@pytest.mark.property
@settings(deadline=None, max_examples=50)
@given(
    a=semiring_elements("min_plus"),
    b=semiring_elements("min_plus"),
    c=semiring_elements("min_plus")
)
def test_min_plus_associativity_times(a, b, c):
    """Property: (a ⊗ b) ⊗ c = a ⊗ (b ⊗ c) for min-plus."""
    spec = get_semiring("min_plus")
    
    left = spec.times(spec.times(a, b), c)
    right = spec.times(a, spec.times(b, c))
    
    if math.isinf(left) and math.isinf(right):
        assert True
    elif math.isinf(left) or math.isinf(right):
        assert False, f"One side infinite: {left} != {right}"
    else:
        assert math.isclose(left, right, rel_tol=1e-9), \
            f"Associativity failed: ({a} ⊗ {b}) ⊗ {c} = {left} != {right}"


@pytest.mark.property
@settings(deadline=None, max_examples=50)
@given(a=semiring_elements("min_plus"))
def test_min_plus_identity_plus(a):
    """Property: a ⊕ 0 = 0 ⊕ a = a for min-plus."""
    spec = get_semiring("min_plus")
    zero = spec.zero
    
    left = spec.plus(a, zero)
    right = spec.plus(zero, a)
    
    # For min-plus, zero is infinity, so min(a, inf) = a
    if math.isinf(a):
        assert math.isinf(left) and math.isinf(right)
    else:
        assert math.isclose(left, a, rel_tol=1e-9), f"{a} ⊕ inf != {a}"
        assert math.isclose(right, a, rel_tol=1e-9), f"inf ⊕ {a} != {a}"


@pytest.mark.property
@settings(deadline=None, max_examples=50)
@given(a=semiring_elements("min_plus"))
def test_min_plus_identity_times(a):
    """Property: a ⊗ 1 = 1 ⊗ a = a for min-plus."""
    spec = get_semiring("min_plus")
    one = spec.one  # For min-plus, one = 0
    
    left = spec.times(a, one)
    right = spec.times(one, a)
    
    if math.isinf(a):
        assert math.isinf(left) and math.isinf(right)
    else:
        # a ⊗ 0 = a + 0 = a
        assert math.isclose(left, a, rel_tol=1e-9), f"{a} ⊗ 0 != {a}"
        assert math.isclose(right, a, rel_tol=1e-9), f"0 ⊗ {a} != {a}"


@pytest.mark.property
@settings(deadline=None, max_examples=30)
@given(a=semiring_elements("min_plus"))
def test_min_plus_absorption(a):
    """Property: 0 ⊗ a = a ⊗ 0 = 0 for min-plus."""
    spec = get_semiring("min_plus")
    zero = spec.zero  # infinity
    
    left = spec.times(zero, a)
    right = spec.times(a, zero)
    
    # inf ⊗ anything = inf (absorption)
    assert math.isinf(left), f"inf ⊗ {a} should be inf"
    assert math.isinf(right), f"{a} ⊗ inf should be inf"


@pytest.mark.property
@settings(deadline=None, max_examples=50, suppress_health_check=[HealthCheck.filter_too_much])
@given(
    a=semiring_elements("min_plus"),
    b=semiring_elements("min_plus"),
    c=semiring_elements("min_plus")
)
def test_min_plus_distributivity_left(a, b, c):
    """Property: a ⊗ (b ⊕ c) = (a ⊗ b) ⊕ (a ⊗ c) for min-plus."""
    spec = get_semiring("min_plus")
    
    # Filter out inf combinations that cause arithmetic issues
    if math.isinf(a) or math.isinf(b) or math.isinf(c):
        assume(False)  # Skip infinite cases for distributivity
    
    left = spec.times(a, spec.plus(b, c))
    right = spec.plus(spec.times(a, b), spec.times(a, c))
    
    assert math.isclose(left, right, rel_tol=1e-9), \
        f"Distributivity failed: {a} ⊗ ({b} ⊕ {c}) = {left} != {right}"


@pytest.mark.property
@settings(deadline=None, max_examples=50)
@given(a=semiring_elements("min_plus"), b=semiring_elements("min_plus"))
def test_min_plus_commutativity_plus(a, b):
    """Property: a ⊕ b = b ⊕ a for min-plus (should be commutative)."""
    spec = get_semiring("min_plus")
    
    left = spec.plus(a, b)
    right = spec.plus(b, a)
    
    if math.isinf(left) and math.isinf(right):
        assert True
    elif math.isinf(left) or math.isinf(right):
        assert False, f"Commutativity failed: {a} ⊕ {b} = {left} != {right}"
    else:
        assert math.isclose(left, right, rel_tol=1e-9), \
            f"Commutativity failed: {a} ⊕ {b} = {left} != {right}"


# ============================================================================
# Property Tests: Boolean Semiring
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=50)
@given(a=st.booleans(), b=st.booleans(), c=st.booleans())
def test_boolean_associativity_plus(a, b, c):
    """Property: (a ⊕ b) ⊕ c = a ⊕ (b ⊕ c) for boolean semiring."""
    spec = get_semiring("boolean")
    
    left = spec.plus(spec.plus(a, b), c)
    right = spec.plus(a, spec.plus(b, c))
    
    assert left == right, f"Associativity failed: ({a} OR {b}) OR {c} != {a} OR ({b} OR {c})"


@pytest.mark.property
@settings(deadline=None, max_examples=50)
@given(a=st.booleans(), b=st.booleans(), c=st.booleans())
def test_boolean_associativity_times(a, b, c):
    """Property: (a ⊗ b) ⊗ c = a ⊗ (b ⊗ c) for boolean semiring."""
    spec = get_semiring("boolean")
    
    left = spec.times(spec.times(a, b), c)
    right = spec.times(a, spec.times(b, c))
    
    assert left == right, f"Associativity failed: ({a} AND {b}) AND {c} != {a} AND ({b} AND {c})"


@pytest.mark.property
@settings(deadline=None, max_examples=50)
@given(a=st.booleans())
def test_boolean_identity_elements(a):
    """Property: Identity elements work correctly for boolean semiring."""
    spec = get_semiring("boolean")
    
    # Identity for plus (OR): False
    assert spec.plus(a, spec.zero) == a
    assert spec.plus(spec.zero, a) == a
    
    # Identity for times (AND): True
    assert spec.times(a, spec.one) == a
    assert spec.times(spec.one, a) == a


@pytest.mark.property
@settings(deadline=None, max_examples=50)
@given(a=st.booleans())
def test_boolean_absorption(a):
    """Property: Zero is absorbing for times in boolean semiring."""
    spec = get_semiring("boolean")
    
    # False AND anything = False
    assert spec.times(spec.zero, a) == spec.zero
    assert spec.times(a, spec.zero) == spec.zero


@pytest.mark.property
@settings(deadline=None, max_examples=50)
@given(a=st.booleans(), b=st.booleans(), c=st.booleans())
def test_boolean_distributivity(a, b, c):
    """Property: Distributivity holds for boolean semiring."""
    spec = get_semiring("boolean")
    
    # a ⊗ (b ⊕ c) = (a ⊗ b) ⊕ (a ⊗ c)
    left = spec.times(a, spec.plus(b, c))
    right = spec.plus(spec.times(a, b), spec.times(a, c))
    
    assert left == right, f"Distributivity failed"


@pytest.mark.property
@settings(deadline=None, max_examples=50)
@given(a=st.booleans())
def test_boolean_idempotence(a):
    """Property: Boolean semiring is idempotent for plus."""
    spec = get_semiring("boolean")
    
    # a ⊕ a = a (idempotence)
    assert spec.plus(a, a) == a, f"{a} OR {a} should equal {a}"


# ============================================================================
# Property Tests: Semiring Validation
# ============================================================================

@pytest.mark.property
def test_invalid_semiring_without_zero():
    """Property: SemiringSpec validation fails without zero."""
    with pytest.raises(SemiringValidationError, match="zero must be provided"):
        spec = SemiringSpec(
            name="invalid",
            zero=None,  # Invalid!
            one=1.0,
            plus=lambda a, b: a + b,
            times=lambda a, b: a * b,
        )
        spec.validate()


@pytest.mark.property
def test_invalid_semiring_without_one():
    """Property: SemiringSpec validation fails without one."""
    with pytest.raises(SemiringValidationError, match="one must be provided"):
        spec = SemiringSpec(
            name="invalid",
            zero=0.0,
            one=None,  # Invalid!
            plus=lambda a, b: a + b,
            times=lambda a, b: a * b,
        )
        spec.validate()


@pytest.mark.property
def test_invalid_semiring_without_callables():
    """Property: SemiringSpec validation fails if plus/times are not callable."""
    with pytest.raises(SemiringValidationError, match="plus must be callable"):
        spec = SemiringSpec(
            name="invalid",
            zero=0.0,
            one=1.0,
            plus=42,  # Not callable!
            times=lambda a, b: a * b,
        )
        spec.validate()


# ============================================================================
# Property Tests: Custom Semiring Registration
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=5)
@given(
    name=st.text(
        min_size=1,
        max_size=15,
        alphabet=st.characters(min_codepoint=97, max_codepoint=122)
    ).filter(lambda x: x not in list_semirings())  # Avoid conflicts
)
def test_custom_semiring_registration(name):
    """Property: Custom semirings can be registered and retrieved."""
    # Create a simple additive semiring (natural numbers + 0)
    spec = SemiringSpec(
        name=name,
        zero=0,
        one=1,
        plus=lambda a, b: a + b,
        times=lambda a, b: a * b,
        examples=(0, 1, 2, 3),
    )
    
    # Register it
    register_semiring(spec, overwrite=True)
    
    # Retrieve it
    retrieved = get_semiring(name)
    assert retrieved.name == name
    assert retrieved.zero == 0
    assert retrieved.one == 1
    
    # Verify operations work
    assert retrieved.plus(2, 3) == 5
    assert retrieved.times(2, 3) == 6


@pytest.mark.property
def test_semiring_overwrite_protection():
    """Property: Cannot overwrite existing semiring without flag."""
    # Try to register min_plus again (should fail)
    spec = SemiringSpec(
        name="min_plus",
        zero=0,
        one=1,
        plus=lambda a, b: a + b,
        times=lambda a, b: a * b,
    )
    
    with pytest.raises(SemiringValidationError, match="already registered"):
        register_semiring(spec, overwrite=False)
