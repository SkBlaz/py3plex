"""
Tests for py3plex.semiring.registry module.

This module tests the semiring registry that manages
built-in and custom semiring definitions.
"""

import pytest
import math
from py3plex.semiring.registry import (
    get_semiring,
    list_semirings,
    register_semiring,
)
from py3plex.semiring.core import SemiringSpec, SemiringValidationError


class TestGetSemiring:
    """Test retrieving semirings from registry."""

    def test_get_min_plus(self):
        """Test retrieving min_plus semiring."""
        sr = get_semiring("min_plus")
        
        assert sr is not None
        assert sr.name == "min_plus"
        assert sr.zero == math.inf
        assert sr.one == 0.0

    def test_get_boolean(self):
        """Test retrieving boolean semiring."""
        sr = get_semiring("boolean")
        
        assert sr is not None
        assert sr.name == "boolean"
        assert sr.zero is False
        assert sr.one is True

    def test_get_max_times(self):
        """Test retrieving max_times semiring."""
        sr = get_semiring("max_times")
        
        assert sr is not None
        assert sr.name == "max_times"
        assert sr.zero == 0.0
        assert sr.one == 1.0

    def test_get_tropical_lex(self):
        """Test retrieving tropical_lex semiring."""
        sr = get_semiring("tropical_lex")
        
        assert sr is not None
        assert sr.name == "tropical_lex"

    def test_get_unknown_semiring(self):
        """Test error when retrieving unknown semiring."""
        with pytest.raises(SemiringValidationError, match="Unknown semiring"):
            get_semiring("nonexistent_semiring")

    def test_get_case_sensitive(self):
        """Test that semiring names are case-sensitive."""
        with pytest.raises(SemiringValidationError):
            get_semiring("MIN_PLUS")  # Should be "min_plus"


class TestListSemirings:
    """Test listing available semirings."""

    def test_list_returns_names(self):
        """Test that list_semirings returns semiring names."""
        names = list_semirings()
        
        assert isinstance(names, list)
        assert len(names) > 0
        assert "min_plus" in names
        assert "boolean" in names
        assert "max_times" in names

    def test_list_alphabetical(self):
        """Test that semirings are listed alphabetically."""
        names = list_semirings()
        
        # Check alphabetical ordering
        sorted_names = sorted(names)
        assert names == sorted_names

    def test_list_no_duplicates(self):
        """Test that list has no duplicates."""
        names = list_semirings()
        
        assert len(names) == len(set(names))


class TestRegisterSemiring:
    """Test registering custom semirings."""

    def test_register_new_semiring(self):
        """Test registering a new custom semiring."""
        custom = SemiringSpec(
            name="custom_test",
            zero=math.inf,
            one=0.0,
            plus=lambda a, b: min(a, b),
            times=lambda a, b: a + b,
            strict=True,
            is_idempotent_plus=True,
            examples=(0.0, 1.0, math.inf),
        )
        
        # Register the semiring
        register_semiring(custom, overwrite=False)
        
        # Verify it's registered
        names = list_semirings()
        assert "custom_test" in names
        
        # Retrieve and check
        retrieved = get_semiring("custom_test")
        assert retrieved.name == "custom_test"
        assert retrieved.zero == math.inf
        
        # Clean up by overwriting with same spec
        register_semiring(custom, overwrite=True)

    def test_register_duplicate_error(self):
        """Test error when registering duplicate without overwrite."""
        custom = SemiringSpec(
            name="boolean",  # Already exists
            zero=False,
            one=True,
            plus=lambda a, b: a or b,
            times=lambda a, b: a and b,
            strict=True,
            is_idempotent_plus=True,
            examples=(False, True),
        )
        
        with pytest.raises(SemiringValidationError, match="already registered"):
            register_semiring(custom, overwrite=False)

    def test_register_with_overwrite(self):
        """Test overwriting existing semiring."""
        # First register a custom semiring
        custom1 = SemiringSpec(
            name="overwrite_test",
            zero=0.0,
            one=1.0,
            plus=lambda a, b: a + b,
            times=lambda a, b: a * b,
            strict=True,
            is_idempotent_plus=False,
            examples=(0.0, 1.0, 2.0),
        )
        register_semiring(custom1, overwrite=False)
        
        # Now overwrite it
        custom2 = SemiringSpec(
            name="overwrite_test",
            zero=math.inf,
            one=0.0,
            plus=lambda a, b: min(a, b),
            times=lambda a, b: a + b,
            strict=True,
            is_idempotent_plus=True,
            examples=(0.0, 1.0, math.inf),
        )
        register_semiring(custom2, overwrite=True)
        
        # Verify it was overwritten
        retrieved = get_semiring("overwrite_test")
        assert retrieved.zero == math.inf  # New value


class TestSemiringCheck:
    """Test checking if semiring is registered."""

    def test_semiring_in_list_true(self):
        """Test that built-in semirings are in the list."""
        names = list_semirings()
        assert "min_plus" in names
        assert "boolean" in names
        assert "max_times" in names

    def test_semiring_not_in_list_false(self):
        """Test that unknown semirings are not in the list."""
        names = list_semirings()
        assert "nonexistent_semiring" not in names
        assert "custom_unregistered" not in names

    def test_list_case_sensitive(self):
        """Test that list is case-sensitive."""
        names = list_semirings()
        assert "min_plus" in names
        assert "MIN_PLUS" not in names


class TestRegistryRobustness:
    """Test registry robustness and edge cases."""

    def test_register_multiple_custom(self):
        """Test registering multiple custom semirings."""
        semirings = []
        for i in range(3):
            custom = SemiringSpec(
                name=f"multi_test_{i}",
                zero=0.0,
                one=1.0,
                plus=lambda a, b: a + b,
                times=lambda a, b: a * b,
                strict=True,
                is_idempotent_plus=False,
                examples=(0.0, 1.0),
            )
            register_semiring(custom, overwrite=False)
            semirings.append(custom.name)
        
        # Verify all are registered
        all_names = list_semirings()
        for name in semirings:
            assert name in all_names
        
        # Clean up by overwriting
        for name in semirings:
            custom = SemiringSpec(
                name=name,
                zero=0.0,
                one=1.0,
                plus=lambda a, b: a + b,
                times=lambda a, b: a * b,
                strict=True,
                is_idempotent_plus=False,
                examples=(0.0, 1.0),
            )
            register_semiring(custom, overwrite=True)
