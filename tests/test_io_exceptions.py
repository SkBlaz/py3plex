"""
Tests for I/O exception classes.

This module tests the custom exceptions defined in the I/O module,
including SchemaValidationError, ReferentialIntegrityError, and 
FormatUnsupportedError.
"""
import unittest

from py3plex.exceptions import Py3plexException
from py3plex.io.exceptions import (
    FormatUnsupportedError,
    ReferentialIntegrityError,
    SchemaValidationError,
)


class TestIOExceptionHierarchy(unittest.TestCase):
    """Test IO exception inheritance hierarchy."""

    def test_schema_validation_error_inherits_from_base(self):
        """Test that SchemaValidationError inherits from Py3plexException."""
        self.assertTrue(issubclass(SchemaValidationError, Py3plexException))

    def test_referential_integrity_error_inherits_from_schema_error(self):
        """Test that ReferentialIntegrityError inherits from SchemaValidationError."""
        self.assertTrue(issubclass(ReferentialIntegrityError, SchemaValidationError))
        self.assertTrue(issubclass(ReferentialIntegrityError, Py3plexException))

    def test_format_unsupported_error_inherits_from_base(self):
        """Test that FormatUnsupportedError inherits from Py3plexException."""
        self.assertTrue(issubclass(FormatUnsupportedError, Py3plexException))


class TestSchemaValidationError(unittest.TestCase):
    """Test SchemaValidationError functionality."""

    def test_raise_schema_validation_error(self):
        """Test raising SchemaValidationError with message."""
        with self.assertRaises(SchemaValidationError) as context:
            raise SchemaValidationError("Schema validation failed")
        self.assertEqual(str(context.exception), "Schema validation failed")

    def test_catch_with_base_exception(self):
        """Test that SchemaValidationError can be caught by base exception."""
        with self.assertRaises(Py3plexException):
            raise SchemaValidationError("Test error")


class TestReferentialIntegrityError(unittest.TestCase):
    """Test ReferentialIntegrityError functionality."""

    def test_raise_referential_integrity_error(self):
        """Test raising ReferentialIntegrityError."""
        with self.assertRaises(ReferentialIntegrityError) as context:
            raise ReferentialIntegrityError("Node reference not found")
        self.assertEqual(str(context.exception), "Node reference not found")

    def test_catch_with_schema_validation_error(self):
        """Test that ReferentialIntegrityError can be caught by SchemaValidationError."""
        with self.assertRaises(SchemaValidationError):
            raise ReferentialIntegrityError("Test error")

    def test_catch_with_base_exception(self):
        """Test that ReferentialIntegrityError can be caught by base exception."""
        with self.assertRaises(Py3plexException):
            raise ReferentialIntegrityError("Test error")


class TestFormatUnsupportedError(unittest.TestCase):
    """Test FormatUnsupportedError functionality."""

    def test_raise_with_format_name_read_operation(self):
        """Test raising FormatUnsupportedError for read operation."""
        with self.assertRaises(FormatUnsupportedError) as context:
            raise FormatUnsupportedError("xml", "read")

        exception = context.exception
        self.assertEqual(exception.format_name, "xml")
        self.assertEqual(exception.operation, "read")
        self.assertIn("xml", str(exception))
        self.assertIn("read", str(exception))
        self.assertIn("not supported", str(exception))

    def test_raise_with_format_name_write_operation(self):
        """Test raising FormatUnsupportedError for write operation."""
        with self.assertRaises(FormatUnsupportedError) as context:
            raise FormatUnsupportedError("binary", "write")

        exception = context.exception
        self.assertEqual(exception.format_name, "binary")
        self.assertEqual(exception.operation, "write")
        self.assertIn("binary", str(exception))
        self.assertIn("write", str(exception))

    def test_default_operation_is_read(self):
        """Test that default operation is 'read'."""
        with self.assertRaises(FormatUnsupportedError) as context:
            raise FormatUnsupportedError("unknown")

        exception = context.exception
        self.assertEqual(exception.operation, "read")
        self.assertIn("read", str(exception))

    def test_error_message_includes_supported_formats_hint(self):
        """Test that error message suggests using supported_formats()."""
        with self.assertRaises(FormatUnsupportedError) as context:
            raise FormatUnsupportedError("custom", "read")

        self.assertIn("supported_formats", str(context.exception))

    def test_catch_with_base_exception(self):
        """Test that FormatUnsupportedError can be caught by base exception."""
        with self.assertRaises(Py3plexException):
            raise FormatUnsupportedError("test_format")


class TestIOExceptionUseCases(unittest.TestCase):
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
        with self.assertRaises(SchemaValidationError):
            validate_network_schema([], edges)

        # Test referential integrity violation
        invalid_edges = [{"source": "A", "target": "C"}]  # C doesn't exist
        with self.assertRaises(ReferentialIntegrityError):
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
        self.assertTrue(load_network("data.csv", "csv"))

        # Test unsupported format
        with self.assertRaises(FormatUnsupportedError) as context:
            load_network("data.xml", "xml")

        self.assertEqual(context.exception.format_name, "xml")

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
        try:
            process_data("integrity")
            self.fail("Should have raised exception")
        except ReferentialIntegrityError as e:
            self.assertIsInstance(e, SchemaValidationError)
            self.assertIsInstance(e, Py3plexException)

        # Catch at schema level
        try:
            process_data("integrity")
            self.fail("Should have raised exception")
        except SchemaValidationError:
            pass  # Successfully caught

        # Catch all at base level
        exceptions_caught = []
        for op in ["schema", "integrity", "format"]:
            try:
                process_data(op)
            except Py3plexException as e:
                exceptions_caught.append(type(e).__name__)

        self.assertEqual(len(exceptions_caught), 3)
        self.assertIn("SchemaValidationError", exceptions_caught)
        self.assertIn("ReferentialIntegrityError", exceptions_caught)
        self.assertIn("FormatUnsupportedError", exceptions_caught)


if __name__ == "__main__":
    unittest.main()
