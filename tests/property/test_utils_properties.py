#!/usr/bin/env python3
"""
Property-based tests for utils module.

Tests random number generator utilities and dataset path resolution.
"""

import numpy as np
import pytest
from hypothesis import given, settings, assume, strategies as st
from hypothesis import HealthCheck

# Import utils module
try:
    from py3plex.utils import get_rng
    UTILS_AVAILABLE = True
except ImportError:
    UTILS_AVAILABLE = False
    pytest.skip("Utils module not available", allow_module_level=True)


# ============================================================================
# Property Tests: Random Number Generator
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(seed=st.integers(min_value=0, max_value=2**31-1))
def test_get_rng_returns_generator(seed):
    """Test that get_rng returns a numpy Generator."""
    rng = get_rng(seed)
    
    # Should return a Generator object
    assert isinstance(rng, np.random.Generator), \
        f"Should return np.random.Generator, got {type(rng)}"


@pytest.mark.property
@settings(deadline=None, max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
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
@settings(deadline=None, max_examples=15, suppress_health_check=[HealthCheck.function_scoped_fixture])
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
@settings(deadline=None, max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
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
@settings(deadline=None, max_examples=15, suppress_health_check=[HealthCheck.function_scoped_fixture])
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
@settings(deadline=None, max_examples=15, suppress_health_check=[HealthCheck.function_scoped_fixture])
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
@settings(deadline=None, max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
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
@settings(deadline=None, max_examples=15, suppress_health_check=[HealthCheck.function_scoped_fixture])
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
@settings(deadline=None, max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(seed=st.integers(min_value=0, max_value=2**31-1))
def test_get_rng_zero_seed_valid(seed):
    """Test that seed=0 is valid and produces deterministic results."""
    rng1 = get_rng(0)
    rng2 = get_rng(0)
    
    # Should be identical
    assert rng1.random() == rng2.random(), \
        "Seed 0 should be valid and produce deterministic results"


@pytest.mark.property
@settings(deadline=None, max_examples=15, suppress_health_check=[HealthCheck.function_scoped_fixture])
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
@settings(deadline=None, max_examples=15, suppress_health_check=[HealthCheck.function_scoped_fixture])
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
@settings(deadline=None, max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(seed=st.integers(min_value=0, max_value=100))
def test_get_rng_small_seeds_valid(seed):
    """Test that small seed values work correctly."""
    rng = get_rng(seed)
    
    # Should work and generate valid random numbers
    random_nums = rng.random(5)
    assert all(0 <= x <= 1 for x in random_nums), \
        "Should generate valid random numbers with small seeds"


@pytest.mark.property
@settings(deadline=None, max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(seed=st.integers(min_value=2**30, max_value=2**31-1))
def test_get_rng_large_seeds_valid(seed):
    """Test that large seed values work correctly."""
    rng = get_rng(seed)
    
    # Should work and generate valid random numbers
    random_nums = rng.random(5)
    assert all(0 <= x <= 1 for x in random_nums), \
        "Should generate valid random numbers with large seeds"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-m', 'property'])
