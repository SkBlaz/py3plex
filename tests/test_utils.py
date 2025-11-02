"""
Tests for py3plex.utils module.

This module tests utility functions including random number generator
initialization and other helper functions.
"""

import pytest
import numpy as np
from py3plex.utils import get_rng


class TestGetRNG:
    """Test the get_rng utility function for random number generation."""

    def test_get_rng_with_int_seed(self):
        """Test get_rng with integer seed returns Generator."""
        rng = get_rng(42)
        assert isinstance(rng, np.random.Generator), (
            "get_rng should return a numpy Generator instance"
        )
        
        # Test reproducibility
        rng1 = get_rng(42)
        rng2 = get_rng(42)
        val1 = rng1.random()
        val2 = rng2.random()
        assert val1 == val2, "Same seed should produce same values"

    def test_get_rng_with_none_seed(self):
        """Test get_rng with None seed returns Generator with random state."""
        rng = get_rng(None)
        assert isinstance(rng, np.random.Generator), (
            "get_rng should return a numpy Generator instance"
        )
        
        # Should produce different values on different calls
        val1 = rng.random()
        val2 = rng.random()
        assert val1 != val2, "Sequential calls should produce different values"

    def test_get_rng_with_generator(self):
        """Test get_rng with existing Generator passes through unchanged."""
        original_rng = np.random.default_rng(123)
        returned_rng = get_rng(original_rng)
        
        # Should be the same object
        assert returned_rng is original_rng, (
            "get_rng should return the same Generator object when passed one"
        )
        
        # Should produce same values
        test_rng = np.random.default_rng(123)
        assert returned_rng.random() == test_rng.random()

    def test_get_rng_reproducibility(self):
        """Test that get_rng produces reproducible sequences with same seed."""
        seed = 12345
        
        rng1 = get_rng(seed)
        sequence1 = [rng1.random() for _ in range(10)]
        
        rng2 = get_rng(seed)
        sequence2 = [rng2.random() for _ in range(10)]
        
        assert sequence1 == sequence2, (
            "Same seed should produce identical sequences"
        )

    @pytest.mark.parametrize("seed1,seed2", [
        (1, 2),
        (0, 1),
        (42, 43),
        (100, 200),
    ])
    def test_get_rng_different_seeds(self, seed1, seed2):
        """Test that different seeds produce different values."""
        rng1 = get_rng(seed1)
        rng2 = get_rng(seed2)
        
        val1 = rng1.random()
        val2 = rng2.random()
        
        assert val1 != val2, (
            f"Different seeds ({seed1}, {seed2}) should produce different values"
        )

    def test_get_rng_random_array(self):
        """Test get_rng works with array generation."""
        rng = get_rng(999)
        arr = rng.random(5)
        
        assert len(arr) == 5, "Array should have requested length"
        assert all(0 <= x <= 1 for x in arr), "All values should be in [0, 1]"
        
        # Test reproducibility with arrays
        rng1 = get_rng(999)
        rng2 = get_rng(999)
        arr1 = rng1.random(5)
        arr2 = rng2.random(5)
        
        np.testing.assert_array_equal(arr1, arr2, 
            err_msg="Same seed should produce identical arrays")

    @pytest.mark.parametrize("seed", [0, 1, 42, 99999, 2**31 - 1])
    def test_get_rng_with_various_seeds(self, seed):
        """Test get_rng works with various valid seed values."""
        rng = get_rng(seed)
        assert isinstance(rng, np.random.Generator)
        
        # Verify it produces valid random numbers
        value = rng.random()
        assert 0 <= value <= 1, f"Random value {value} should be in [0, 1]"

    def test_get_rng_negative_seed(self):
        """Test get_rng behavior with negative seed values.
        
        Note: NumPy Generator accepts negative seeds and converts them.
        """
        rng = get_rng(-1)
        assert isinstance(rng, np.random.Generator)
        
        # Should still produce valid random numbers
        value = rng.random()
        assert 0 <= value <= 1

    def test_get_rng_large_seed(self):
        """Test get_rng with very large seed values."""
        large_seed = 2**63 - 1  # Maximum value for 64-bit integer
        rng = get_rng(large_seed)
        assert isinstance(rng, np.random.Generator)
        
        value = rng.random()
        assert 0 <= value <= 1

    def test_get_rng_produces_uniform_distribution(self):
        """Test that get_rng produces uniformly distributed values (statistical test)."""
        rng = get_rng(12345)
        samples = rng.random(10000)
        
        # Check that samples are roughly uniformly distributed
        mean = np.mean(samples)
        assert 0.48 < mean < 0.52, (
            f"Mean of 10000 samples ({mean}) should be close to 0.5"
        )
        
        # Check that samples cover the full range
        assert np.min(samples) < 0.1, "Minimum should be close to 0"
        assert np.max(samples) > 0.9, "Maximum should be close to 1"

    def test_get_rng_state_independence(self):
        """Test that multiple RNGs with same seed are independent after creation."""
        rng1 = get_rng(100)
        rng2 = get_rng(100)
        
        # Draw from rng1
        _ = rng1.random()
        
        # rng2 should still start from the same state
        val1 = get_rng(100).random()
        val2 = rng2.random()
        
        assert val1 == val2, "Independent RNGs should not affect each other"
