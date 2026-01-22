"""
Tests for py3plex.compat.exceptions module.

This module tests compatibility exception classes.
"""

import pytest
from py3plex.compat.exceptions import (
    CompatibilityError,
    ConversionNotSupportedError,
    SchemaError,
)


class TestCompatibilityError:
    """Test the CompatibilityError exception."""

    def test_basic_compatibility_error(self):
        """Test basic CompatibilityError creation and message."""
        error = CompatibilityError("Test error message")
        
        assert str(error) == "Test error message"
        assert error.reason is None
        assert error.suggestions == []

    def test_compatibility_error_with_reason(self):
        """Test CompatibilityError with reason."""
        error = CompatibilityError(
            "Cannot convert multigraph",
            reason="Target format only supports simple graphs"
        )
        
        error_str = str(error)
        assert "Cannot convert multigraph" in error_str
        assert "Reason: Target format only supports simple graphs" in error_str

    def test_compatibility_error_with_suggestions(self):
        """Test CompatibilityError with suggestions."""
        suggestions = [
            "Use 'combine_edges' to merge parallel edges",
            "Use a different target format that supports multigraphs"
        ]
        error = CompatibilityError(
            "Multigraph not supported",
            suggestions=suggestions
        )
        
        error_str = str(error)
        assert "Multigraph not supported" in error_str
        assert "Suggestions:" in error_str
        assert "combine_edges" in error_str
        assert "different target format" in error_str

    def test_compatibility_error_with_all_fields(self):
        """Test CompatibilityError with all fields populated."""
        error = CompatibilityError(
            "Format mismatch",
            reason="Temporal network cannot be converted to static",
            suggestions=["Export temporal snapshots separately", "Use temporal format"]
        )
        
        error_str = str(error)
        assert "Format mismatch" in error_str
        assert "Reason: Temporal network" in error_str
        assert "Suggestions:" in error_str
        assert "Export temporal snapshots" in error_str
        assert "Use temporal format" in error_str

    def test_compatibility_error_suggestions_default_empty(self):
        """Test that suggestions default to empty list."""
        error = CompatibilityError("Test", reason="Test reason")
        assert isinstance(error.suggestions, list)
        assert len(error.suggestions) == 0

    def test_compatibility_error_is_exception(self):
        """Test that CompatibilityError extends Exception."""
        assert issubclass(CompatibilityError, Exception)
        
        error = CompatibilityError("Test")
        assert isinstance(error, Exception)

    def test_compatibility_error_can_be_raised(self):
        """Test that CompatibilityError can be raised and caught."""
        with pytest.raises(CompatibilityError) as exc_info:
            raise CompatibilityError("Test error", reason="Test reason")
        
        assert "Test error" in str(exc_info.value)
        assert exc_info.value.reason == "Test reason"


class TestSchemaError:
    """Test the SchemaError exception."""

    def test_basic_schema_error(self):
        """Test basic SchemaError creation and message."""
        error = SchemaError("Schema validation failed")
        
        assert str(error) == "Schema validation failed"
        assert error.field is None
        assert error.expected is None
        assert error.actual is None

    def test_schema_error_with_field(self):
        """Test SchemaError with field name."""
        error = SchemaError(
            "Type mismatch",
            field="node_weight"
        )
        
        error_str = str(error)
        assert "Type mismatch" in error_str
        assert "Field: node_weight" in error_str

    def test_schema_error_with_types(self):
        """Test SchemaError with expected and actual types."""
        error = SchemaError(
            "Invalid type",
            expected=int,
            actual=str
        )
        
        error_str = str(error)
        assert "Invalid type" in error_str
        assert "Expected:" in error_str
        assert "int" in error_str
        assert "Actual:" in error_str
        assert "str" in error_str

    def test_schema_error_with_all_fields(self):
        """Test SchemaError with all fields populated."""
        error = SchemaError(
            "Attribute type mismatch",
            field="edge_weight",
            expected=float,
            actual=str
        )
        
        error_str = str(error)
        assert "Attribute type mismatch" in error_str
        assert "Field: edge_weight" in error_str
        assert "Expected:" in error_str
        assert "float" in error_str
        assert "Actual:" in error_str
        assert "str" in error_str

    def test_schema_error_with_value_types(self):
        """Test SchemaError with specific values instead of types."""
        error = SchemaError(
            "Value out of range",
            field="probability",
            expected="value between 0 and 1",
            actual=1.5
        )
        
        error_str = str(error)
        assert "Value out of range" in error_str
        assert "probability" in error_str
        assert "between 0 and 1" in error_str
        assert "1.5" in error_str

    def test_schema_error_is_exception(self):
        """Test that SchemaError extends Exception."""
        assert issubclass(SchemaError, Exception)
        
        error = SchemaError("Test")
        assert isinstance(error, Exception)

    def test_schema_error_can_be_raised(self):
        """Test that SchemaError can be raised and caught."""
        with pytest.raises(SchemaError) as exc_info:
            raise SchemaError("Invalid schema", field="test_field")
        
        assert "Invalid schema" in str(exc_info.value)
        assert exc_info.value.field == "test_field"


class TestConversionNotSupportedError:
    """Test the ConversionNotSupportedError exception."""

    def test_basic_conversion_not_supported_error(self):
        """Test basic ConversionNotSupportedError creation."""
        error = ConversionNotSupportedError("Format not supported")
        
        assert str(error) == "Format not supported"

    def test_conversion_not_supported_is_exception(self):
        """Test that ConversionNotSupportedError extends Exception."""
        assert issubclass(ConversionNotSupportedError, Exception)
        
        error = ConversionNotSupportedError("Test")
        assert isinstance(error, Exception)

    def test_conversion_not_supported_can_be_raised(self):
        """Test that ConversionNotSupportedError can be raised and caught."""
        with pytest.raises(ConversionNotSupportedError) as exc_info:
            raise ConversionNotSupportedError("GraphML not supported")
        
        assert "GraphML not supported" in str(exc_info.value)

    def test_conversion_not_supported_message(self):
        """Test ConversionNotSupportedError with descriptive message."""
        message = "Conversion to 'exotic_format' is not implemented"
        error = ConversionNotSupportedError(message)
        
        assert str(error) == message


class TestExceptionHierarchy:
    """Test the exception hierarchy and relationships."""

    def test_all_exceptions_inherit_from_exception(self):
        """Test that all custom exceptions inherit from Exception."""
        assert issubclass(CompatibilityError, Exception)
        assert issubclass(SchemaError, Exception)
        assert issubclass(ConversionNotSupportedError, Exception)

    def test_exceptions_are_distinct(self):
        """Test that exceptions are distinct types."""
        assert CompatibilityError != SchemaError
        assert SchemaError != ConversionNotSupportedError
        assert CompatibilityError != ConversionNotSupportedError

    def test_can_catch_specific_exceptions(self):
        """Test that specific exceptions can be caught individually."""
        # CompatibilityError
        with pytest.raises(CompatibilityError):
            raise CompatibilityError("Test")
        
        # SchemaError
        with pytest.raises(SchemaError):
            raise SchemaError("Test")
        
        # ConversionNotSupportedError
        with pytest.raises(ConversionNotSupportedError):
            raise ConversionNotSupportedError("Test")

    def test_can_catch_as_generic_exception(self):
        """Test that custom exceptions can be caught as Exception."""
        with pytest.raises(Exception):
            raise CompatibilityError("Test")
        
        with pytest.raises(Exception):
            raise SchemaError("Test")
        
        with pytest.raises(Exception):
            raise ConversionNotSupportedError("Test")
