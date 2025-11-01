"""
Tests for custom exception classes.

This module tests that all custom exception types can be properly raised,
caught, and provide meaningful error messages.
"""
import unittest

from py3plex.exceptions import (
    AlgorithmError,
    CentralityComputationError,
    CommunityDetectionError,
    ConversionError,
    DecompositionError,
    EmbeddingError,
    IncompatibleNetworkError,
    InvalidEdgeError,
    InvalidLayerError,
    InvalidNodeError,
    NetworkConstructionError,
    ParsingError,
    Py3plexException,
    Py3plexMatrixError,
    VisualizationError,
)


class TestExceptionHierarchy(unittest.TestCase):
    """Test exception inheritance hierarchy."""

    def test_base_exception_is_exception(self):
        """Test that Py3plexException inherits from Exception."""
        self.assertTrue(issubclass(Py3plexException, Exception))

    def test_all_custom_exceptions_inherit_from_base(self):
        """Test that all custom exceptions inherit from Py3plexException."""
        custom_exceptions = [
            NetworkConstructionError,
            InvalidLayerError,
            InvalidNodeError,
            InvalidEdgeError,
            ParsingError,
            VisualizationError,
            AlgorithmError,
            ConversionError,
            IncompatibleNetworkError,
            Py3plexMatrixError,
        ]
        for exc_class in custom_exceptions:
            with self.subTest(exception=exc_class.__name__):
                self.assertTrue(issubclass(exc_class, Py3plexException))

    def test_algorithm_subexceptions_inherit_from_algorithm_error(self):
        """Test that algorithm-specific exceptions inherit from AlgorithmError."""
        algorithm_exceptions = [
            CommunityDetectionError,
            CentralityComputationError,
            DecompositionError,
            EmbeddingError,
        ]
        for exc_class in algorithm_exceptions:
            with self.subTest(exception=exc_class.__name__):
                self.assertTrue(issubclass(exc_class, AlgorithmError))
                self.assertTrue(issubclass(exc_class, Py3plexException))


class TestExceptionRaising(unittest.TestCase):
    """Test that exceptions can be properly raised and caught."""

    def test_raise_base_exception(self):
        """Test raising and catching base Py3plexException."""
        with self.assertRaises(Py3plexException) as context:
            raise Py3plexException("Test error message")
        self.assertEqual(str(context.exception), "Test error message")

    def test_raise_network_construction_error(self):
        """Test raising NetworkConstructionError."""
        with self.assertRaises(NetworkConstructionError):
            raise NetworkConstructionError("Failed to construct network")

    def test_raise_invalid_layer_error(self):
        """Test raising InvalidLayerError."""
        with self.assertRaises(InvalidLayerError):
            raise InvalidLayerError("Layer 'invalid' does not exist")

    def test_raise_invalid_node_error(self):
        """Test raising InvalidNodeError."""
        with self.assertRaises(InvalidNodeError):
            raise InvalidNodeError("Node 'unknown' not found")

    def test_raise_invalid_edge_error(self):
        """Test raising InvalidEdgeError."""
        with self.assertRaises(InvalidEdgeError):
            raise InvalidEdgeError("Edge (1, 2) is invalid")

    def test_raise_parsing_error(self):
        """Test raising ParsingError."""
        with self.assertRaises(ParsingError):
            raise ParsingError("Failed to parse input file")

    def test_raise_visualization_error(self):
        """Test raising VisualizationError."""
        with self.assertRaises(VisualizationError):
            raise VisualizationError("Visualization failed")

    def test_raise_algorithm_error(self):
        """Test raising AlgorithmError."""
        with self.assertRaises(AlgorithmError):
            raise AlgorithmError("Algorithm execution failed")

    def test_raise_community_detection_error(self):
        """Test raising CommunityDetectionError."""
        with self.assertRaises(CommunityDetectionError):
            raise CommunityDetectionError("Community detection failed")

    def test_raise_centrality_computation_error(self):
        """Test raising CentralityComputationError."""
        with self.assertRaises(CentralityComputationError):
            raise CentralityComputationError("Centrality computation failed")

    def test_raise_decomposition_error(self):
        """Test raising DecompositionError."""
        with self.assertRaises(DecompositionError):
            raise DecompositionError("Network decomposition failed")

    def test_raise_embedding_error(self):
        """Test raising EmbeddingError."""
        with self.assertRaises(EmbeddingError):
            raise EmbeddingError("Embedding generation failed")

    def test_raise_conversion_error(self):
        """Test raising ConversionError."""
        with self.assertRaises(ConversionError):
            raise ConversionError("Format conversion failed")

    def test_raise_incompatible_network_error(self):
        """Test raising IncompatibleNetworkError."""
        with self.assertRaises(IncompatibleNetworkError):
            raise IncompatibleNetworkError("Network format incompatible")

    def test_raise_matrix_error(self):
        """Test raising Py3plexMatrixError."""
        with self.assertRaises(Py3plexMatrixError):
            raise Py3plexMatrixError("Matrix operation failed")


class TestExceptionCatching(unittest.TestCase):
    """Test that exceptions can be caught at different levels of hierarchy."""

    def test_catch_specific_exception_with_base(self):
        """Test that specific exceptions can be caught by base exception."""
        with self.assertRaises(Py3plexException):
            raise NetworkConstructionError("Test error")

    def test_catch_algorithm_subexception_with_algorithm_error(self):
        """Test that algorithm subexceptions can be caught by AlgorithmError."""
        with self.assertRaises(AlgorithmError):
            raise CommunityDetectionError("Test error")

    def test_catch_algorithm_error_with_base(self):
        """Test that AlgorithmError can be caught by base exception."""
        with self.assertRaises(Py3plexException):
            raise AlgorithmError("Test error")

    def test_exception_message_preserved(self):
        """Test that error messages are preserved through exception hierarchy."""
        error_message = "This is a detailed error message"
        with self.assertRaises(Py3plexException) as context:
            raise InvalidLayerError(error_message)
        self.assertEqual(str(context.exception), error_message)


class TestExceptionUseCases(unittest.TestCase):
    """Test realistic exception use cases."""

    def test_multiple_exception_types_in_try_except(self):
        """Test handling multiple exception types."""

        def risky_operation(operation_type):
            if operation_type == "network":
                raise NetworkConstructionError("Network failed")
            elif operation_type == "algorithm":
                raise AlgorithmError("Algorithm failed")
            elif operation_type == "parsing":
                raise ParsingError("Parsing failed")

        # Test catching specific exceptions
        with self.assertRaises(NetworkConstructionError):
            risky_operation("network")

        with self.assertRaises(AlgorithmError):
            risky_operation("algorithm")

        # Test catching with base exception
        try:
            risky_operation("parsing")
        except Py3plexException as e:
            self.assertIsInstance(e, ParsingError)

    def test_exception_with_detailed_context(self):
        """Test exceptions with detailed context information."""
        layer_name = "social_network"
        error_msg = f"Layer '{layer_name}' not found in multilayer network"

        with self.assertRaises(InvalidLayerError) as context:
            raise InvalidLayerError(error_msg)

        self.assertIn(layer_name, str(context.exception))
        self.assertIn("not found", str(context.exception))


if __name__ == "__main__":
    unittest.main()
