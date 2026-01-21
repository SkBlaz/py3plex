#!/usr/bin/env python3
"""
Property-based tests for utils module.

Tests random number generator utilities and dataset path resolution.
"""

import warnings
import numpy as np
import pytest
from hypothesis import given, settings, assume, strategies as st
from hypothesis import HealthCheck

# Import utils module
try:
    from py3plex.utils import get_rng, deprecated, warn_if_deprecated, validate_multilayer_input
    from py3plex.exceptions import NetworkConstructionError
    UTILS_AVAILABLE = True
except ImportError:
    UTILS_AVAILABLE = False
    pytest.skip("Utils module not available", allow_module_level=True)


# ============================================================================
# Property Tests: Random Number Generator
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(seed=st.integers(min_value=0, max_value=2**31-1))
def test_get_rng_returns_generator(seed):
    """Test that get_rng returns a numpy Generator."""
    rng = get_rng(seed)
    
    # Should return a Generator object
    assert isinstance(rng, np.random.Generator), \
        f"Should return np.random.Generator, got {type(rng)}"


@pytest.mark.property
@settings(deadline=None, max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(seed=st.integers(min_value=0, max_value=2**31-1))
def test_get_rng_reproducible_with_same_seed(seed):
    """Test that same seed produces same random numbers."""
    rng1 = get_rng(seed)
    rng2 = get_rng(seed)
    
    # Generate random numbers
    random1 = rng1.random(10)
    random2 = rng2.random(10)
    
    # Should be identical
    assert np.allclose(random1, random2), \
        "Same seed should produce identical random numbers"


@pytest.mark.property
@settings(deadline=None, max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    seed1=st.integers(min_value=0, max_value=2**31-1),
    seed2=st.integers(min_value=0, max_value=2**31-1)
)
def test_get_rng_different_seeds_different_numbers(seed1, seed2):
    """Test that different seeds produce different random numbers."""
    assume(seed1 != seed2)
    
    rng1 = get_rng(seed1)
    rng2 = get_rng(seed2)
    
    # Generate random numbers
    random1 = rng1.random(10)
    random2 = rng2.random(10)
    
    # Should be different (with very high probability)
    assert not np.allclose(random1, random2), \
        "Different seeds should produce different random numbers"


@pytest.mark.property
def test_get_rng_none_seed_returns_generator():
    """Test that None seed returns a valid generator."""
    rng = get_rng(None)
    
    # Should return a Generator object
    assert isinstance(rng, np.random.Generator), \
        "Should return np.random.Generator even with None seed"
    
    # Should be able to generate random numbers
    random_nums = rng.random(5)
    assert len(random_nums) == 5, "Should generate requested number of random values"
    assert all(0 <= x <= 1 for x in random_nums), "Random numbers should be in [0, 1]"


@pytest.mark.property
@settings(deadline=None, max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(seed=st.integers(min_value=0, max_value=2**31-1))
def test_get_rng_passthrough_existing_generator(seed):
    """Test that passing existing generator returns same object."""
    # Create a generator
    existing_rng = np.random.default_rng(seed)
    
    # Pass it to get_rng
    result_rng = get_rng(existing_rng)
    
    # Should return the same object
    assert result_rng is existing_rng, \
        "Should return the same Generator object when passed existing one"


@pytest.mark.property
@settings(deadline=None, max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(seed=st.integers(min_value=0, max_value=2**31-1))
def test_get_rng_generates_uniform_distribution(seed):
    """Test that generated numbers follow uniform distribution."""
    rng = get_rng(seed)
    
    # Generate many random numbers
    random_nums = rng.random(1000)
    
    # Should be uniformly distributed in [0, 1]
    assert all(0 <= x <= 1 for x in random_nums), "All values should be in [0, 1]"
    
    # Mean should be close to 0.5 for uniform [0, 1]
    mean = np.mean(random_nums)
    assert 0.4 < mean < 0.6, f"Mean should be close to 0.5, got {mean}"


@pytest.mark.property
@settings(deadline=None, max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(seed=st.integers(min_value=0, max_value=2**31-1))
def test_get_rng_supports_various_distributions(seed):
    """Test that generator supports various distribution methods."""
    rng = get_rng(seed)
    
    # Test uniform
    uniform = rng.uniform(0, 10, size=10)
    assert len(uniform) == 10, "Should generate 10 uniform values"
    assert all(0 <= x <= 10 for x in uniform), "Uniform values should be in range"
    
    # Test integers
    integers = rng.integers(0, 100, size=10)
    assert len(integers) == 10, "Should generate 10 integers"
    assert all(0 <= x < 100 for x in integers), "Integers should be in range"
    
    # Test normal
    normal = rng.normal(0, 1, size=10)
    assert len(normal) == 10, "Should generate 10 normal values"


@pytest.mark.property
@settings(deadline=None, max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(seed=st.integers(min_value=0, max_value=2**31-1))
def test_get_rng_state_independence(seed):
    """Test that multiple generators from same seed are independent."""
    rng1 = get_rng(seed)
    rng2 = get_rng(seed)
    
    # Advance rng1
    rng1.random(100)
    
    # rng2 should still start from beginning
    first_from_rng2 = rng2.random()
    
    # Create a fresh generator with same seed
    rng3 = get_rng(seed)
    first_from_rng3 = rng3.random()
    
    # rng2 and rng3 should match (both fresh)
    assert first_from_rng2 == first_from_rng3, \
        "Fresh generators with same seed should produce same first value"


@pytest.mark.property
@settings(deadline=None, max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(seed=st.integers(min_value=0, max_value=2**31-1))
def test_get_rng_deterministic_sequences(seed):
    """Test that sequences are deterministic with same seed."""
    # Generate sequence 1
    rng1 = get_rng(seed)
    sequence1 = [rng1.random() for _ in range(20)]
    
    # Generate sequence 2 with same seed
    rng2 = get_rng(seed)
    sequence2 = [rng2.random() for _ in range(20)]
    
    # Sequences should be identical
    assert len(sequence1) == len(sequence2), "Sequences should have same length"
    for v1, v2 in zip(sequence1, sequence2):
        assert v1 == v2, "Values should be identical at each position"


@pytest.mark.property
@settings(deadline=None, max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(seed=st.integers(min_value=0, max_value=2**31-1))
def test_get_rng_zero_seed_valid(seed):
    """Test that seed=0 is valid and produces deterministic results."""
    rng1 = get_rng(0)
    rng2 = get_rng(0)
    
    # Should be identical
    assert rng1.random() == rng2.random(), \
        "Seed 0 should be valid and produce deterministic results"


@pytest.mark.property
@settings(deadline=None, max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(seed=st.integers(min_value=0, max_value=2**31-1))
def test_get_rng_choice_deterministic(seed):
    """Test that choice operations are deterministic."""
    items = list(range(100))
    
    rng1 = get_rng(seed)
    choice1 = rng1.choice(items, size=10, replace=False)
    
    rng2 = get_rng(seed)
    choice2 = rng2.choice(items, size=10, replace=False)
    
    # Choices should be identical
    assert np.array_equal(choice1, choice2), \
        "Choices with same seed should be identical"


@pytest.mark.property
@settings(deadline=None, max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(seed=st.integers(min_value=0, max_value=2**31-1))
def test_get_rng_shuffle_deterministic(seed):
    """Test that shuffle operations are deterministic."""
    items1 = list(range(50))
    items2 = list(range(50))
    
    rng1 = get_rng(seed)
    rng1.shuffle(items1)
    
    rng2 = get_rng(seed)
    rng2.shuffle(items2)
    
    # Shuffled lists should be identical
    assert items1 == items2, \
        "Shuffles with same seed should be identical"


@pytest.mark.property
@settings(deadline=None, max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(seed=st.integers(min_value=0, max_value=100))
def test_get_rng_small_seeds_valid(seed):
    """Test that small seed values work correctly."""
    rng = get_rng(seed)
    
    # Should work and generate valid random numbers
    random_nums = rng.random(5)
    assert all(0 <= x <= 1 for x in random_nums), \
        "Should generate valid random numbers with small seeds"


@pytest.mark.property
@settings(deadline=None, max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(seed=st.integers(min_value=2**30, max_value=2**31-1))
def test_get_rng_large_seeds_valid(seed):
    """Test that large seed values work correctly."""
    rng = get_rng(seed)
    
    # Should work and generate valid random numbers
    random_nums = rng.random(5)
    assert all(0 <= x <= 1 for x in random_nums), \
        "Should generate valid random numbers with large seeds"


# ============================================================================
# Property Tests: Deprecated Decorator
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(reason=st.text(min_size=1, max_size=100))
def test_deprecated_decorator_with_reason_only(reason):
    """Test that deprecated decorator works with reason only."""
    
    @deprecated(reason=reason)
    def test_func():
        return "result"
    
    # Calling the function should issue a warning
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        result = test_func()
        
        # Should have one warning
        assert len(w) == 1
        assert issubclass(w[0].category, DeprecationWarning)
        assert reason in str(w[0].message)
        assert "test_func is deprecated" in str(w[0].message)
    
    # Function should still work
    assert result == "result"


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    reason=st.text(min_size=1, max_size=50),
    version=st.text(min_size=1, max_size=20)
)
def test_deprecated_decorator_with_version(reason, version):
    """Test that deprecated decorator includes version info."""
    
    @deprecated(reason=reason, version=version)
    def test_func():
        return 42
    
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        result = test_func()
        
        assert len(w) == 1
        assert issubclass(w[0].category, DeprecationWarning)
        assert reason in str(w[0].message)
        assert version in str(w[0].message)
        assert "since version" in str(w[0].message)
    
    assert result == 42


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    reason=st.text(min_size=1, max_size=50),
    alternative=st.text(min_size=1, max_size=50)
)
def test_deprecated_decorator_with_alternative(reason, alternative):
    """Test that deprecated decorator suggests alternative."""
    
    @deprecated(reason=reason, alternative=alternative)
    def test_func():
        return [1, 2, 3]
    
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        result = test_func()
        
        assert len(w) == 1
        assert issubclass(w[0].category, DeprecationWarning)
        assert reason in str(w[0].message)
        assert alternative in str(w[0].message)
        assert "Use" in str(w[0].message)
    
    assert result == [1, 2, 3]


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    reason=st.text(min_size=1, max_size=50),
    version=st.text(min_size=1, max_size=20),
    alternative=st.text(min_size=1, max_size=50)
)
def test_deprecated_decorator_with_all_params(reason, version, alternative):
    """Test deprecated decorator with all parameters."""
    
    @deprecated(reason=reason, version=version, alternative=alternative)
    def test_func(x):
        return x * 2
    
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        result = test_func(5)
        
        assert len(w) == 1
        assert issubclass(w[0].category, DeprecationWarning)
        msg = str(w[0].message)
        assert reason in msg
        assert version in msg
        assert alternative in msg
    
    assert result == 10


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(reason=st.text(min_size=1, max_size=50))
def test_deprecated_decorator_preserves_function_name(reason):
    """Test that deprecated decorator preserves function metadata."""
    
    @deprecated(reason=reason)
    def my_special_function():
        """My docstring."""
        return "value"
    
    # Function name should be preserved
    assert my_special_function.__name__ == "my_special_function"
    # Docstring should be preserved
    assert my_special_function.__doc__ == "My docstring."


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    reason=st.text(min_size=1, max_size=50),
    arg1=st.integers(),
    arg2=st.integers()
)
def test_deprecated_decorator_passes_arguments(reason, arg1, arg2):
    """Test that deprecated decorator passes arguments correctly."""
    
    @deprecated(reason=reason)
    def add_func(a, b):
        return a + b
    
    with warnings.catch_warnings(record=True):
        warnings.simplefilter("always")
        result = add_func(arg1, arg2)
    
    assert result == arg1 + arg2


# ============================================================================
# Property Tests: warn_if_deprecated
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    feature_name=st.text(min_size=1, max_size=50),
    reason=st.text(min_size=1, max_size=100)
)
def test_warn_if_deprecated_basic(feature_name, reason):
    """Test warn_if_deprecated with feature name and reason."""
    
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        warn_if_deprecated(feature_name, reason)
        
        assert len(w) == 1
        assert issubclass(w[0].category, DeprecationWarning)
        assert feature_name in str(w[0].message)
        assert reason in str(w[0].message)


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    feature_name=st.text(min_size=1, max_size=50),
    reason=st.text(min_size=1, max_size=50),
    alternative=st.text(min_size=1, max_size=50)
)
def test_warn_if_deprecated_with_alternative(feature_name, reason, alternative):
    """Test warn_if_deprecated suggests alternative."""
    
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        warn_if_deprecated(feature_name, reason, alternative)
        
        assert len(w) == 1
        assert issubclass(w[0].category, DeprecationWarning)
        msg = str(w[0].message)
        assert feature_name in msg
        assert reason in msg
        assert alternative in msg
        assert "Use" in msg


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    feature_name=st.text(min_size=1, max_size=50),
    reason=st.text(min_size=1, max_size=50)
)
def test_warn_if_deprecated_multiple_calls(feature_name, reason):
    """Test that multiple calls produce multiple warnings."""
    
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        warn_if_deprecated(feature_name, reason)
        warn_if_deprecated(feature_name, reason)
        
        # Should have two warnings
        assert len(w) == 2
        for warning in w:
            assert issubclass(warning.category, DeprecationWarning)


# ============================================================================
# Property Tests: validate_multilayer_input
# ============================================================================

@pytest.mark.property
def test_validate_multilayer_input_rejects_none():
    """Test that validate_multilayer_input rejects None."""
    
    # With icontract, this raises ViolationError
    # Without icontract, this raises NetworkConstructionError
    with pytest.raises((NetworkConstructionError, Exception)):
        validate_multilayer_input(None)


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(data=st.integers())
def test_validate_multilayer_input_accepts_integers(data):
    """Test that validate_multilayer_input accepts integer data."""
    
    # Should not raise an exception
    validate_multilayer_input(data)


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(data=st.text(min_size=1))
def test_validate_multilayer_input_accepts_strings(data):
    """Test that validate_multilayer_input accepts string data."""
    
    # Should not raise an exception
    validate_multilayer_input(data)


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(data=st.lists(st.integers(), min_size=1))
def test_validate_multilayer_input_accepts_lists(data):
    """Test that validate_multilayer_input accepts list data."""
    
    # Should not raise an exception
    validate_multilayer_input(data)


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(data=st.dictionaries(st.text(min_size=1), st.integers(), min_size=1))
def test_validate_multilayer_input_accepts_dicts(data):
    """Test that validate_multilayer_input accepts dict data."""
    
    # Should not raise an exception
    validate_multilayer_input(data)


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(data=st.floats(allow_nan=False, allow_infinity=False))
def test_validate_multilayer_input_accepts_floats(data):
    """Test that validate_multilayer_input accepts float data."""
    
    # Should not raise an exception
    validate_multilayer_input(data)


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-m', 'property'])
