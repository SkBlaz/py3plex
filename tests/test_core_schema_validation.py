"""
Tests for py3plex.core.schema_validation module.

This module tests schema validation functionality for multilayer networks.
"""

import pytest
from py3plex.core.schema_validation import (
    FieldValidator,
    ValidationError,
)


class TestFieldValidator:
    """Test the FieldValidator class."""

    def test_basic_type_validation(self):
        """Test basic type validation."""
        validator = FieldValidator(str)
        
        # Valid string
        assert validator.validate("hello", "test_field") == "hello"
        
        # Invalid type should raise
        with pytest.raises(ValidationError, match="must be of type"):
            validator.validate(123, "test_field")

    def test_required_field_validation(self):
        """Test required field validation."""
        validator = FieldValidator(str, required=True)
        
        # Missing value (None) should raise
        with pytest.raises(ValidationError, match="Required field"):
            validator.validate(None, "test_field")
        
        # Present value should pass
        assert validator.validate("value", "test_field") == "value"

    def test_optional_field_with_default(self):
        """Test optional field returns default when missing."""
        validator = FieldValidator(str, required=False, default="default_value")
        
        # Missing value should return default
        assert validator.validate(None, "test_field") == "default_value"
        
        # Present value should override default
        assert validator.validate("custom", "test_field") == "custom"

    def test_choices_validation(self):
        """Test validation with restricted choices."""
        validator = FieldValidator(str, choices=['A', 'B', 'C'])
        
        # Valid choice
        assert validator.validate('A', "test_field") == 'A'
        
        # Invalid choice should raise
        with pytest.raises(ValidationError, match="must be one of"):
            validator.validate('D', "test_field")

    def test_numeric_range_validation(self):
        """Test min/max value validation for numeric fields."""
        validator = FieldValidator(int, min_value=0, max_value=100)
        
        # Valid range
        assert validator.validate(50, "test_field") == 50
        assert validator.validate(0, "test_field") == 0
        assert validator.validate(100, "test_field") == 100
        
        # Below minimum
        with pytest.raises(ValidationError, match="must be >="):
            validator.validate(-1, "test_field")
        
        # Above maximum
        with pytest.raises(ValidationError, match="must be <="):
            validator.validate(101, "test_field")

    def test_custom_validator_function(self):
        """Test custom validation function."""
        def is_even(value):
            return value % 2 == 0
        
        validator = FieldValidator(int, custom_validator=is_even)
        
        # Even number should pass
        assert validator.validate(4, "test_field") == 4
        
        # Odd number should fail
        with pytest.raises(ValidationError, match="failed custom validation"):
            validator.validate(3, "test_field")

    def test_float_type_validation(self):
        """Test validation for float type."""
        validator = FieldValidator(float, min_value=0.0, max_value=1.0)
        
        # Valid float
        assert validator.validate(0.5, "test_field") == 0.5
        
        # Out of range
        with pytest.raises(ValidationError):
            validator.validate(1.5, "test_field")

    def test_list_type_validation(self):
        """Test validation for list type."""
        validator = FieldValidator(list, required=True)
        
        # Valid list
        assert validator.validate([1, 2, 3], "test_field") == [1, 2, 3]
        
        # Invalid type
        with pytest.raises(ValidationError):
            validator.validate("not a list", "test_field")

    def test_combined_constraints(self):
        """Test multiple constraints together."""
        validator = FieldValidator(
            int,
            required=True,
            choices=[1, 2, 3, 4, 5],
            min_value=1,
            max_value=5
        )
        
        # Valid value satisfying all constraints
        assert validator.validate(3, "test_field") == 3
        
        # Fails choice constraint
        with pytest.raises(ValidationError):
            validator.validate(6, "test_field")
        
        # Missing required field
        with pytest.raises(ValidationError):
            validator.validate(None, "test_field")


class TestValidationError:
    """Test the ValidationError exception."""

    def test_validation_error_message(self):
        """Test that ValidationError carries the correct message."""
        try:
            raise ValidationError("Test error message")
        except ValidationError as e:
            assert str(e) == "Test error message"

    def test_validation_error_inheritance(self):
        """Test that ValidationError extends Exception."""
        assert issubclass(ValidationError, Exception)


class TestFieldValidatorEdgeCases:
    """Test edge cases and special scenarios."""

    def test_none_as_valid_value_when_not_required(self):
        """Test None is accepted when field is not required and no default."""
        validator = FieldValidator(str, required=False)
        # Should not raise
        result = validator.validate(None, "test_field")
        assert result is None

    def test_zero_as_valid_value(self):
        """Test that zero is a valid value (not treated as None)."""
        validator = FieldValidator(int, required=True)
        assert validator.validate(0, "test_field") == 0

    def test_empty_string_as_valid_value(self):
        """Test that empty string is valid (not treated as missing)."""
        validator = FieldValidator(str, required=True)
        assert validator.validate("", "test_field") == ""

    def test_empty_list_as_valid_value(self):
        """Test that empty list is valid."""
        validator = FieldValidator(list, required=True)
        assert validator.validate([], "test_field") == []

    def test_boolean_type_validation(self):
        """Test validation for boolean type."""
        validator = FieldValidator(bool, required=True)
        
        assert validator.validate(True, "test_field") is True
        assert validator.validate(False, "test_field") is False
        
        # Invalid type
        with pytest.raises(ValidationError):
            validator.validate("true", "test_field")
