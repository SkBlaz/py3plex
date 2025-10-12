"""
Tests for py3plex.utils module.
"""

import pytest
import numpy as np
from py3plex.utils import get_rng


def test_get_rng_with_int_seed():
    """Test get_rng with integer seed returns Generator."""
    rng = get_rng(42)
    assert isinstance(rng, np.random.Generator)
    
    # Test reproducibility
    rng1 = get_rng(42)
    rng2 = get_rng(42)
    val1 = rng1.random()
    val2 = rng2.random()
    assert val1 == val2, "Same seed should produce same values"


def test_get_rng_with_none_seed():
    """Test get_rng with None seed returns Generator."""
    rng = get_rng(None)
    assert isinstance(rng, np.random.Generator)
    
    # Should produce different values on different calls
    val1 = rng.random()
    val2 = rng.random()
    assert val1 != val2, "Sequential calls should produce different values"


def test_get_rng_with_generator():
    """Test get_rng with existing Generator passes through."""
    original_rng = np.random.default_rng(123)
    returned_rng = get_rng(original_rng)
    
    # Should be the same object
    assert returned_rng is original_rng
    
    # Should produce same values
    test_rng = np.random.default_rng(123)
    assert returned_rng.random() == test_rng.random()


def test_get_rng_reproducibility():
    """Test that get_rng produces reproducible sequences."""
    seed = 12345
    
    rng1 = get_rng(seed)
    sequence1 = [rng1.random() for _ in range(10)]
    
    rng2 = get_rng(seed)
    sequence2 = [rng2.random() for _ in range(10)]
    
    assert sequence1 == sequence2, "Same seed should produce identical sequences"


def test_get_rng_different_seeds():
    """Test that different seeds produce different values."""
    rng1 = get_rng(1)
    rng2 = get_rng(2)
    
    val1 = rng1.random()
    val2 = rng2.random()
    
    assert val1 != val2, "Different seeds should produce different values"


def test_get_rng_random_array():
    """Test get_rng works with array generation."""
    rng = get_rng(999)
    arr = rng.random(5)
    
    assert len(arr) == 5
    assert all(0 <= x <= 1 for x in arr), "All values should be in [0, 1]"
    
    # Test reproducibility with arrays
    rng1 = get_rng(999)
    rng2 = get_rng(999)
    arr1 = rng1.random(5)
    arr2 = rng2.random(5)
    
    np.testing.assert_array_equal(arr1, arr2)
