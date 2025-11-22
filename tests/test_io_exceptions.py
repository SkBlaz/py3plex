"""
Tests for I/O exception classes.

This module tests the custom exceptions defined in the I/O module,
including SchemaValidationError, ReferentialIntegrityError, and 
FormatUnsupportedError.
"""
import pytest

from py3plex.exceptions import Py3plexException, Py3plexIOError
from py3plex.io.exceptions import (
    FormatUnsupportedError,
    ReferentialIntegrityError,
    SchemaValidationError,
)


class TestIOExceptionHierarchy:
    """Test IO exception inheritance hierarchy."""

    def test_schema_validation_error_inherits_from_base(self):
        """Test that SchemaValidationError inherits from Py3plexIOError."""
        assert issubclass(SchemaValidationError, Py3plexIOError)
        assert issubclass(SchemaValidationError, Py3plexException)

    def test_referential_integrity_error_inherits_from_schema_error(self):
        """Test that ReferentialIntegrityError inherits from SchemaValidationError."""
        assert issubclass(ReferentialIntegrityError, SchemaValidationError)
        assert issubclass(ReferentialIntegrityError, Py3plexIOError)
        assert issubclass(ReferentialIntegrityError, Py3plexException)

    def test_format_unsupported_error_inherits_from_base(self):
        """Test that FormatUnsupportedError inherits from Py3plexIOError."""
        assert issubclass(FormatUnsupportedError, Py3plexIOError)
        assert issubclass(FormatUnsupportedError, Py3plexException)


class TestSchemaValidationError:
    """Test SchemaValidationError functionality."""

    def test_raise_schema_validation_error(self):
        """Test raising SchemaValidationError with message."""
        with pytest.raises(SchemaValidationError) as exc_info:
            raise SchemaValidationError("Schema validation failed")
        assert str(exc_info.value) == "Schema validation failed"

    def test_catch_with_base_exception(self):
        """Test that SchemaValidationError can be caught by Py3plexIOError and base exception."""
        with pytest.raises(Py3plexIOError):
            raise SchemaValidationError("Test error")
        
        with pytest.raises(Py3plexException):
            raise SchemaValidationError("Test error")


class TestReferentialIntegrityError:
    """Test ReferentialIntegrityError functionality."""

    def test_raise_referential_integrity_error(self):
        """Test raising ReferentialIntegrityError."""
        with pytest.raises(ReferentialIntegrityError) as exc_info:
            raise ReferentialIntegrityError("Node reference not found")
        assert str(exc_info.value) == "Node reference not found"

    def test_catch_with_schema_validation_error(self):
        """Test that ReferentialIntegrityError can be caught by SchemaValidationError."""
        with pytest.raises(SchemaValidationError):
            raise ReferentialIntegrityError("Test error")

    def test_catch_with_base_exception(self):
        """Test that ReferentialIntegrityError can be caught by Py3plexIOError and base exception."""
        with pytest.raises(Py3plexIOError):
            raise ReferentialIntegrityError("Test error")
        
        with pytest.raises(Py3plexException):
            raise ReferentialIntegrityError("Test error")


class TestFormatUnsupportedError:
    """Test FormatUnsupportedError functionality."""

    @pytest.mark.parametrize("format_name,operation,expected_in_msg", [
        ("xml", "read", ["xml", "read", "not supported"]),
        ("binary", "write", ["binary", "write"]),
    ])
    def test_raise_with_format_and_operation(self, format_name, operation, expected_in_msg):
        """Test raising FormatUnsupportedError with format name and operation."""
        with pytest.raises(FormatUnsupportedError) as exc_info:
            raise FormatUnsupportedError(format_name, operation)

        exception = exc_info.value
        assert exception.format_name == format_name
        assert exception.operation == operation
        for expected_text in expected_in_msg:
            assert expected_text in str(exception), (
                f"Expected '{expected_text}' in error message: {str(exception)}"
            )

    def test_default_operation_is_read(self):
        """Test that default operation is 'read'."""
        with pytest.raises(FormatUnsupportedError) as exc_info:
            raise FormatUnsupportedError("unknown")

        exception = exc_info.value
        assert exception.operation == "read"
        assert "read" in str(exception)

    def test_error_message_includes_supported_formats_hint(self):
        """Test that error message suggests using supported_formats()."""
        with pytest.raises(FormatUnsupportedError) as exc_info:
            raise FormatUnsupportedError("custom", "read")

        assert "supported_formats" in str(exc_info.value)

    def test_catch_with_base_exception(self):
        """Test that FormatUnsupportedError can be caught by Py3plexIOError and base exception."""
        with pytest.raises(Py3plexIOError):
            raise FormatUnsupportedError("test_format")
        
        with pytest.raises(Py3plexException):
            raise FormatUnsupportedError("test_format")


class TestIOExceptionUseCases:
    """Test realistic IO exception use cases."""

    def test_schema_validation_workflow(self):
        """Test a realistic schema validation workflow."""
        def validate_network_schema(nodes, edges):
            # Simulate validation
            if not nodes:
                raise SchemaValidationError("Network must have at least one node")

            # Check referential integrity
            node_ids = {n["id"] for n in nodes}
            for edge in edges:
                if edge["source"] not in node_ids:
                    raise ReferentialIntegrityError(
                        f"Edge source '{edge['source']}' not found in nodes"
                    )
                if edge["target"] not in node_ids:
                    raise ReferentialIntegrityError(
                        f"Edge target '{edge['target']}' not found in nodes"
                    )

        # Test valid data
        nodes = [{"id": "A"}, {"id": "B"}]
        edges = [{"source": "A", "target": "B"}]
        validate_network_schema(nodes, edges)  # Should not raise

        # Test empty nodes
        with pytest.raises(SchemaValidationError):
            validate_network_schema([], edges)

        # Test referential integrity violation
        invalid_edges = [{"source": "A", "target": "C"}]  # C doesn't exist
        with pytest.raises(ReferentialIntegrityError):
            validate_network_schema(nodes, invalid_edges)

    def test_format_detection_workflow(self):
        """Test a realistic format detection workflow."""
        def load_network(file_path, format_name):
            supported_formats = ["csv", "json", "graphml"]
            if format_name not in supported_formats:
                raise FormatUnsupportedError(format_name, "read")
            # Proceed with loading...
            return True

        # Test supported format
        assert load_network("data.csv", "csv") is True

        # Test unsupported format
        with pytest.raises(FormatUnsupportedError) as exc_info:
            load_network("data.xml", "xml")

        assert exc_info.value.format_name == "xml"

    def test_exception_hierarchy_in_error_handling(self):
        """Test handling multiple exception types in a hierarchy."""
        def process_data(operation):
            if operation == "schema":
                raise SchemaValidationError("Schema error")
            elif operation == "integrity":
                raise ReferentialIntegrityError("Integrity error")
            elif operation == "format":
                raise FormatUnsupportedError("unknown")

        # Catch specific exception
        with pytest.raises(ReferentialIntegrityError) as exc_info:
            process_data("integrity")
        
        assert isinstance(exc_info.value, SchemaValidationError)
        assert isinstance(exc_info.value, Py3plexException)

        # Catch at schema level
        with pytest.raises(SchemaValidationError):
            process_data("integrity")

        # Catch all at base level
        exceptions_caught = []
        for op in ["schema", "integrity", "format"]:
            with pytest.raises(Py3plexException) as exc_info:
                process_data(op)
            exceptions_caught.append(type(exc_info.value).__name__)

        assert len(exceptions_caught) == 3
        assert "SchemaValidationError" in exceptions_caught
        assert "ReferentialIntegrityError" in exceptions_caught
        assert "FormatUnsupportedError" in exceptions_caught
