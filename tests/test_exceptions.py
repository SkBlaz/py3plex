"""
Tests for custom exception classes.

This module tests that all custom exception types can be properly raised,
caught, and provide meaningful error messages.
"""
import pytest

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
    Py3plexFormatError,
    Py3plexIOError,
    Py3plexLayoutError,
    Py3plexMatrixError,
    VisualizationError,
)


class TestExceptionHierarchy:
    """Test exception inheritance hierarchy."""

    def test_base_exception_is_exception(self):
        """Test that Py3plexException inherits from Exception."""
        assert issubclass(Py3plexException, Exception)

    @pytest.mark.parametrize("exc_class", [
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
        Py3plexIOError,
        Py3plexFormatError,
        Py3plexLayoutError,
    ])
    def test_all_custom_exceptions_inherit_from_base(self, exc_class):
        """Test that all custom exceptions inherit from Py3plexException."""
        assert issubclass(exc_class, Py3plexException), (
            f"{exc_class.__name__} should inherit from Py3plexException"
        )

    @pytest.mark.parametrize("exc_class", [
        CommunityDetectionError,
        CentralityComputationError,
        DecompositionError,
        EmbeddingError,
    ])
    def test_algorithm_subexceptions_inherit_from_algorithm_error(self, exc_class):
        """Test that algorithm-specific exceptions inherit from AlgorithmError."""
        assert issubclass(exc_class, AlgorithmError), (
            f"{exc_class.__name__} should inherit from AlgorithmError"
        )
        assert issubclass(exc_class, Py3plexException), (
            f"{exc_class.__name__} should inherit from Py3plexException"
        )


class TestExceptionRaising:
    """Test that exceptions can be properly raised and caught."""

    def test_raise_base_exception(self):
        """Test raising and catching base Py3plexException."""
        with pytest.raises(Py3plexException) as exc_info:
            raise Py3plexException("Test error message")
        assert str(exc_info.value) == "Test error message"

    @pytest.mark.parametrize("exc_class,error_msg", [
        (NetworkConstructionError, "Failed to construct network"),
        (InvalidLayerError, "Layer 'invalid' does not exist"),
        (InvalidNodeError, "Node 'unknown' not found"),
        (InvalidEdgeError, "Edge (1, 2) is invalid"),
        (ParsingError, "Failed to parse input file"),
        (VisualizationError, "Visualization failed"),
        (AlgorithmError, "Algorithm execution failed"),
        (CommunityDetectionError, "Community detection failed"),
        (CentralityComputationError, "Centrality computation failed"),
        (DecompositionError, "Network decomposition failed"),
        (EmbeddingError, "Embedding generation failed"),
        (ConversionError, "Format conversion failed"),
        (IncompatibleNetworkError, "Network format incompatible"),
        (Py3plexMatrixError, "Matrix operation failed"),
        (Py3plexIOError, "Failed to read file"),
        (Py3plexFormatError, "Invalid input format"),
        (Py3plexLayoutError, "Layout computation failed"),
    ])
    def test_raise_specific_exceptions(self, exc_class, error_msg):
        """Test raising specific exception types with error messages."""
        with pytest.raises(exc_class) as exc_info:
            raise exc_class(error_msg)
        assert error_msg in str(exc_info.value)


class TestExceptionCatching:
    """Test that exceptions can be caught at different levels of hierarchy."""

    def test_catch_specific_exception_with_base(self):
        """Test that specific exceptions can be caught by base exception."""
        with pytest.raises(Py3plexException):
            raise NetworkConstructionError("Test error")

    def test_catch_algorithm_subexception_with_algorithm_error(self):
        """Test that algorithm subexceptions can be caught by AlgorithmError."""
        with pytest.raises(AlgorithmError):
            raise CommunityDetectionError("Test error")

    def test_catch_algorithm_error_with_base(self):
        """Test that AlgorithmError can be caught by base exception."""
        with pytest.raises(Py3plexException):
            raise AlgorithmError("Test error")

    def test_exception_message_preserved(self):
        """Test that error messages are preserved through exception hierarchy."""
        # Use NetworkConstructionError which doesn't have special __init__
        error_message = "This is a detailed error message"
        with pytest.raises(Py3plexException) as exc_info:
            raise NetworkConstructionError(error_message)
        # The first positional arg should be preserved in args
        assert error_message in str(exc_info.value)


class TestExceptionUseCases:
    """Test realistic exception use cases."""

    @pytest.mark.parametrize("operation_type,expected_exception", [
        ("network", NetworkConstructionError),
        ("algorithm", AlgorithmError),
        ("parsing", ParsingError),
    ])
    def test_multiple_exception_types_in_try_except(self, operation_type, expected_exception):
        """Test handling multiple exception types."""
        def risky_operation(op_type):
            if op_type == "network":
                raise NetworkConstructionError("Network failed")
            elif op_type == "algorithm":
                raise AlgorithmError("Algorithm failed")
            elif op_type == "parsing":
                raise ParsingError("Parsing failed")

        with pytest.raises(expected_exception):
            risky_operation(operation_type)

    def test_catch_with_base_exception(self):
        """Test catching specific exception with base exception class."""
        def risky_operation():
            raise ParsingError("Parsing failed")
        
        with pytest.raises(Py3plexException) as exc_info:
            risky_operation()
        assert isinstance(exc_info.value, ParsingError)

    def test_exception_with_detailed_context(self):
        """Test exceptions with detailed context information."""
        layer_name = "social_network"
        error_msg = f"Layer '{layer_name}' not found in multilayer network"

        with pytest.raises(InvalidLayerError) as exc_info:
            raise InvalidLayerError(error_msg)

        assert layer_name in str(exc_info.value), (
            f"Layer name '{layer_name}' should be in error message"
        )
        assert "not found" in str(exc_info.value), (
            "'not found' should be in error message"
        )
