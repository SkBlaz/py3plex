"""
Tests for the utils module.

This module tests utility functions used across the py3plex library.
"""
import unittest
import warnings

import numpy as np

from py3plex.exceptions import NetworkConstructionError
from py3plex.utils import (
    deprecated,
    get_rng,
    validate_multilayer_input,
    warn_if_deprecated,
)


class TestGetRng(unittest.TestCase):
    """Test random number generator utilities."""

    def test_get_rng_none(self):
        """Test RNG with no seed."""
        rng = get_rng(None)
        
        self.assertIsInstance(rng, np.random.Generator)

    def test_get_rng_with_seed(self):
        """Test RNG with integer seed."""
        rng = get_rng(42)
        
        self.assertIsInstance(rng, np.random.Generator)

    def test_get_rng_reproducibility(self):
        """Test that same seed produces same random numbers."""
        rng1 = get_rng(42)
        rng2 = get_rng(42)
        
        # Same seed should give same first random number
        val1 = rng1.random()
        val2 = rng2.random()
        self.assertEqual(val1, val2)

    def test_get_rng_pass_through_generator(self):
        """Test passing an existing generator."""
        existing_rng = np.random.default_rng(123)
        rng = get_rng(existing_rng)
        
        # Should return the same generator
        self.assertIs(rng, existing_rng)

    def test_get_rng_different_seeds(self):
        """Test that different seeds produce different random numbers."""
        rng1 = get_rng(42)
        rng2 = get_rng(123)
        
        val1 = rng1.random()
        val2 = rng2.random()
        # Different seeds should give different random numbers
        self.assertNotEqual(val1, val2)

    def test_get_rng_consistent_sequence(self):
        """Test that seeded RNG produces consistent sequence."""
        rng1 = get_rng(42)
        sequence1 = [rng1.random() for _ in range(10)]
        
        rng2 = get_rng(42)
        sequence2 = [rng2.random() for _ in range(10)]
        
        self.assertEqual(sequence1, sequence2)


class TestDeprecated(unittest.TestCase):
    """Test deprecation decorator."""

    def test_deprecated_basic(self):
        """Test basic deprecation warning."""
        @deprecated(reason="Test reason")
        def old_function():
            return "result"
        
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = old_function()
            
            self.assertEqual(result, "result")
            self.assertEqual(len(w), 1)
            self.assertTrue(issubclass(w[0].category, DeprecationWarning))
            self.assertIn("old_function is deprecated", str(w[0].message))
            self.assertIn("Test reason", str(w[0].message))

    def test_deprecated_with_version(self):
        """Test deprecation with version number."""
        @deprecated(reason="Test reason", version="1.0.0")
        def old_function():
            return "result"
        
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            old_function()
            
            self.assertEqual(len(w), 1)
            self.assertIn("since version 1.0.0", str(w[0].message))

    def test_deprecated_with_alternative(self):
        """Test deprecation with suggested alternative."""
        @deprecated(
            reason="Test reason",
            version="1.0.0",
            alternative="new_function()"
        )
        def old_function():
            return "result"
        
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            old_function()
            
            self.assertEqual(len(w), 1)
            self.assertIn("Use new_function() instead", str(w[0].message))

    def test_deprecated_preserves_function_name(self):
        """Test that decorator preserves function name."""
        @deprecated(reason="Test")
        def my_function():
            pass
        
        self.assertEqual(my_function.__name__, "my_function")

    def test_deprecated_with_arguments(self):
        """Test deprecated function with arguments."""
        @deprecated(reason="Test reason")
        def old_function(a, b, c=10):
            return a + b + c
        
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = old_function(1, 2, c=3)
            
            self.assertEqual(result, 6)
            self.assertEqual(len(w), 1)


class TestWarnIfDeprecated(unittest.TestCase):
    """Test deprecation warning utility."""

    def test_warn_if_deprecated_basic(self):
        """Test basic deprecation warning."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            warn_if_deprecated("old_param", "No longer used")
            
            self.assertEqual(len(w), 1)
            self.assertTrue(issubclass(w[0].category, DeprecationWarning))
            self.assertIn("old_param is deprecated", str(w[0].message))
            self.assertIn("No longer used", str(w[0].message))

    def test_warn_if_deprecated_with_alternative(self):
        """Test deprecation warning with alternative."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            warn_if_deprecated(
                "old_param",
                "No longer used",
                alternative="new_param"
            )
            
            self.assertEqual(len(w), 1)
            self.assertIn("Use new_param instead", str(w[0].message))

    def test_warn_if_deprecated_multiple_calls(self):
        """Test multiple deprecation warnings."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            warn_if_deprecated("param1", "Reason 1")
            warn_if_deprecated("param2", "Reason 2")
            
            self.assertEqual(len(w), 2)
            self.assertIn("param1", str(w[0].message))
            self.assertIn("param2", str(w[1].message))


class TestValidateMultilayerInput(unittest.TestCase):
    """Test multilayer input validation."""

    def test_validate_multilayer_input_valid(self):
        """Test validation with valid input."""
        # Should not raise exception for non-None input
        validate_multilayer_input("some_data")
        validate_multilayer_input([1, 2, 3])
        validate_multilayer_input({"key": "value"})

    def test_validate_multilayer_input_none(self):
        """Test validation with None input."""
        with self.assertRaises(NetworkConstructionError) as ctx:
            validate_multilayer_input(None)
        
        self.assertIn("cannot be None", str(ctx.exception))

    def test_validate_multilayer_input_empty_dict(self):
        """Test validation with empty dict."""
        # Empty dict is valid (not None)
        validate_multilayer_input({})

    def test_validate_multilayer_input_empty_list(self):
        """Test validation with empty list."""
        # Empty list is valid (not None)
        validate_multilayer_input([])

    def test_validate_multilayer_input_zero(self):
        """Test validation with zero."""
        # Zero is valid (not None)
        validate_multilayer_input(0)

    def test_validate_multilayer_input_false(self):
        """Test validation with False."""
        # False is valid (not None)
        validate_multilayer_input(False)


if __name__ == "__main__":
    unittest.main()
