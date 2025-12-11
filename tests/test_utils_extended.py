"""
Tests for the utils module.

This module tests utility functions used across the py3plex library,
including deprecation decorators, RNG utilities, and input validation.
"""
import warnings

import pytest
import numpy as np

from py3plex.exceptions import NetworkConstructionError
from py3plex.utils import (
    deprecated,
    get_rng,
    validate_multilayer_input,
    warn_if_deprecated,
)


class TestGetRng:
    """Test random number generator utilities."""

    def test_get_rng_none(self):
        """Test RNG with no seed returns valid Generator."""
        rng = get_rng(None)
        assert isinstance(rng, np.random.Generator)

    def test_get_rng_with_seed(self):
        """Test RNG with integer seed returns valid Generator."""
        rng = get_rng(42)
        assert isinstance(rng, np.random.Generator)

    def test_get_rng_reproducibility(self):
        """Test that same seed produces same random numbers."""
        rng1 = get_rng(42)
        rng2 = get_rng(42)
        
        # Same seed should give same first random number
        val1 = rng1.random()
        val2 = rng2.random()
        assert val1 == val2

    def test_get_rng_pass_through_generator(self):
        """Test passing an existing generator returns same object."""
        existing_rng = np.random.default_rng(123)
        rng = get_rng(existing_rng)
        
        # Should return the same generator
        assert rng is existing_rng

    def test_get_rng_different_seeds(self):
        """Test that different seeds produce different random numbers."""
        rng1 = get_rng(42)
        rng2 = get_rng(123)
        
        val1 = rng1.random()
        val2 = rng2.random()
        # Different seeds should give different random numbers
        assert val1 != val2

    def test_get_rng_consistent_sequence(self):
        """Test that seeded RNG produces consistent sequence."""
        rng1 = get_rng(42)
        sequence1 = [rng1.random() for _ in range(10)]
        
        rng2 = get_rng(42)
        sequence2 = [rng2.random() for _ in range(10)]
        
        assert sequence1 == sequence2


class TestDeprecated:
    """Test deprecation decorator."""

    def test_deprecated_basic(self):
        """Test basic deprecation warning is raised."""
        @deprecated(reason="Test reason")
        def old_function():
            return "result"
        
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = old_function()
            
            assert result == "result"
            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "old_function is deprecated" in str(w[0].message)
            assert "Test reason" in str(w[0].message)

    def test_deprecated_with_version(self):
        """Test deprecation warning includes version number."""
        @deprecated(reason="Test reason", version="1.0.0")
        def old_function():
            return "result"
        
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            old_function()
            
            assert len(w) == 1
            assert "since version 1.0.0" in str(w[0].message)

    def test_deprecated_with_alternative(self):
        """Test deprecation warning includes suggested alternative."""
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
            
            assert len(w) == 1
            assert "Use new_function() instead" in str(w[0].message)

    def test_deprecated_preserves_function_name(self):
        """Test that decorator preserves function name and metadata."""
        @deprecated(reason="Test")
        def my_function():
            """Original docstring."""
            pass
        
        assert my_function.__name__ == "my_function"

    def test_deprecated_with_arguments(self):
        """Test deprecated function works correctly with arguments."""
        @deprecated(reason="Test reason")
        def old_function(a, b, c=10):
            return a + b + c
        
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = old_function(1, 2, c=3)
            
            assert result == 6
            assert len(w) == 1


class TestWarnIfDeprecated:
    """Test deprecation warning utility."""

    def test_warn_if_deprecated_basic(self):
        """Test basic deprecation warning is issued."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            warn_if_deprecated("old_param", "No longer used")
            
            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "old_param is deprecated" in str(w[0].message)
            assert "No longer used" in str(w[0].message)

    def test_warn_if_deprecated_with_alternative(self):
        """Test deprecation warning includes alternative parameter."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            warn_if_deprecated(
                "old_param",
                "No longer used",
                alternative="new_param"
            )
            
            assert len(w) == 1
            assert "Use new_param instead" in str(w[0].message)

    def test_warn_if_deprecated_multiple_calls(self):
        """Test multiple deprecation warnings are issued correctly."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            warn_if_deprecated("param1", "Reason 1")
            warn_if_deprecated("param2", "Reason 2")
            
            assert len(w) == 2
            assert "param1" in str(w[0].message)
            assert "param2" in str(w[1].message)


class TestValidateMultilayerInput:
    """Test multilayer input validation."""

    @pytest.mark.parametrize("valid_input", [
        "some_data",
        [1, 2, 3],
        {"key": "value"},
        42,
        [[]],  # Even empty nested list is valid (not None)
        {"a": []},  # Empty dict values are valid
    ])
    def test_validate_multilayer_input_valid(self, valid_input):
        """Test validation passes for valid (non-None) inputs."""
        # Should not raise exception for non-None input
        validate_multilayer_input(valid_input)

    def test_validate_multilayer_input_none(self):
        """Test validation fails for None input with clear error message."""
        # With icontract, this raises ViolationError
        # Without icontract, this raises NetworkConstructionError
        with pytest.raises((NetworkConstructionError, Exception)) as exc_info:
            validate_multilayer_input(None)
        
        # Check that the error message mentions None
        assert "None" in str(exc_info.value)

    def test_validate_multilayer_input_empty_dict(self):
        """Test validation with empty dict (valid input)."""
        # Empty dict is valid (not None)
        validate_multilayer_input({})

    def test_validate_multilayer_input_empty_list(self):
        """Test validation with empty list (valid input)."""
        # Empty list is valid (not None)
        validate_multilayer_input([])

    def test_validate_multilayer_input_zero(self):
        """Test validation with zero (valid input)."""
        # Zero is valid (not None)
        validate_multilayer_input(0)

    def test_validate_multilayer_input_false(self):
        """Test validation with False (valid input)."""
        # False is valid (not None)
        validate_multilayer_input(False)
