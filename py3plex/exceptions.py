"""
Custom exception types for the py3plex library.

This module defines domain-specific exceptions to provide clear error messages
and enable better error handling throughout the library.

Py3plex follows Rust's approach to error messages:
- Clear, descriptive error messages
- Error codes (e.g., PX101, PX201)
- Helpful suggestions for fixing issues
- "Did you mean?" suggestions for typos
- Context showing the relevant location in files

Example usage:
    >>> from py3plex.exceptions import InvalidLayerError
    >>> raise InvalidLayerError(
    ...     "social",
    ...     available_layers=["work", "family", "social_media"],
    ...     suggestion="Did you mean 'social_media'?"
    ... )
"""

from typing import Any, Dict, List, Optional


class Py3plexException(Exception):
    """Base exception class for all py3plex-specific exceptions.

    Attributes:
        code: Error code (e.g., "PX001")
        suggestions: List of suggestions for fixing the error
        notes: Additional context/notes
        did_you_mean: Suggested correction for typos
    """

    # Default error code - subclasses should override
    default_code: str = "PX001"

    def __init__(
        self,
        message: str,
        *,
        code: Optional[str] = None,
        suggestions: Optional[List[str]] = None,
        notes: Optional[List[str]] = None,
        did_you_mean: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        """Initialize exception with rich error information.

        Args:
            message: The error message
            code: Error code (defaults to class's default_code)
            suggestions: List of suggestions for fixing the error
            notes: Additional context/notes
            did_you_mean: Suggested correction for typos
            context: Additional context dictionary
        """
        super().__init__(message)
        self.code = code or self.default_code
        self.suggestions = suggestions or []
        self.notes = notes or []
        self.did_you_mean = did_you_mean
        self.context = context or {}

    def format_message(self, use_color: bool = True) -> str:
        """Format the exception with Rust-style error formatting.

        Args:
            use_color: Whether to use ANSI colors

        Returns:
            Formatted error message string
        """
        try:
            from py3plex.errors import ErrorMessage, Note, Severity, Suggestion

            error = ErrorMessage(
                code=self.code,
                severity=Severity.ERROR,
                title=type(self).__name__.replace("Error", " error").lower().strip(),
                message=str(self.args[0]) if self.args else "",
                suggestions=[Suggestion(message=s) for s in self.suggestions],
                notes=[Note(message=n) for n in self.notes],
                did_you_mean=self.did_you_mean,
            )
            return error.format(use_color=use_color)
        except ImportError:
            # Fallback if errors module not available
            return str(self)

    def __str__(self) -> str:
        """Return formatted error message."""
        # Only use rich formatting if we have additional metadata
        if self.suggestions or self.notes or self.did_you_mean:
            return self.format_message(use_color=True)
        return super().__str__()


class NetworkConstructionError(Py3plexException):
    """Exception raised when network construction fails.

    Error code: PX208
    """

    default_code = "PX208"


class InvalidLayerError(Py3plexException):
    """Exception raised when an invalid layer is specified.

    Error code: PX201

    Example:
        >>> raise InvalidLayerError(
        ...     "social",
        ...     available_layers=["work", "family"],
        ... )
    """

    default_code = "PX201"

    def __init__(
        self,
        layer_name: str,
        *,
        available_layers: Optional[List[str]] = None,
        **kwargs,
    ):
        """Initialize InvalidLayerError.

        Args:
            layer_name: The invalid layer name
            available_layers: List of valid layer names
            **kwargs: Additional arguments for Py3plexException
        """
        # Find similar layer names for "did you mean"
        did_you_mean = kwargs.pop("did_you_mean", None)
        if available_layers and not did_you_mean:
            try:
                from py3plex.errors import find_similar
                did_you_mean = find_similar(layer_name, available_layers)
            except ImportError:
                pass

        message = f"Layer '{layer_name}' does not exist in the network"

        suggestions = kwargs.pop("suggestions", [])
        if available_layers:
            suggestions.append(f"available layers: {', '.join(sorted(available_layers)[:5])}")

        super().__init__(
            message,
            suggestions=suggestions,
            did_you_mean=did_you_mean,
            **kwargs,
        )


class InvalidNodeError(Py3plexException):
    """Exception raised when an invalid node is specified.

    Error code: PX202
    """

    default_code = "PX202"

    def __init__(
        self,
        node_id: str,
        *,
        available_nodes: Optional[List[str]] = None,
        **kwargs,
    ):
        """Initialize InvalidNodeError.

        Args:
            node_id: The invalid node identifier
            available_nodes: Optional list of valid nodes for suggestions
            **kwargs: Additional arguments for Py3plexException
        """
        did_you_mean = kwargs.pop("did_you_mean", None)
        if available_nodes and not did_you_mean:
            try:
                from py3plex.errors import find_similar
                # Only suggest if there are not too many nodes
                if len(available_nodes) < 100:
                    did_you_mean = find_similar(str(node_id), [str(n) for n in available_nodes])
            except ImportError:
                pass

        message = f"Node '{node_id}' not found in the network"
        super().__init__(message, did_you_mean=did_you_mean, **kwargs)


class InvalidEdgeError(Py3plexException):
    """Exception raised when an invalid edge is specified.

    Error code: PX203
    """

    default_code = "PX203"


class ParsingError(Py3plexException):
    """Exception raised when parsing input data fails.

    Error code: PX105
    """

    default_code = "PX105"

    def __init__(
        self,
        message: str,
        *,
        file_path: Optional[str] = None,
        line_number: Optional[int] = None,
        expected: Optional[str] = None,
        got: Optional[str] = None,
        **kwargs,
    ):
        """Initialize ParsingError.

        Args:
            message: The error message
            file_path: Path to the file being parsed
            line_number: Line number where error occurred
            expected: What was expected
            got: What was found
            **kwargs: Additional arguments for Py3plexException
        """
        notes = kwargs.pop("notes", [])
        if expected and got:
            notes.append(f"expected {expected}, found {got}")

        context = kwargs.pop("context", {})
        if file_path:
            context["file_path"] = file_path
        if line_number:
            context["line_number"] = line_number

        super().__init__(message, notes=notes, context=context, **kwargs)


class VisualizationError(Py3plexException):
    """Exception raised when visualization operations fail.

    Error code: PX401
    """

    default_code = "PX401"


class AlgorithmError(Py3plexException):
    """Exception raised when an algorithm execution fails.

    Error code: PX301
    """

    default_code = "PX301"

    def __init__(
        self,
        message: str,
        *,
        algorithm_name: Optional[str] = None,
        valid_algorithms: Optional[List[str]] = None,
        **kwargs,
    ):
        """Initialize AlgorithmError.

        Args:
            message: The error message
            algorithm_name: Name of the algorithm that failed
            valid_algorithms: List of valid algorithm names
            **kwargs: Additional arguments for Py3plexException
        """
        did_you_mean = kwargs.pop("did_you_mean", None)
        if algorithm_name and valid_algorithms and not did_you_mean:
            try:
                from py3plex.errors import find_similar
                did_you_mean = find_similar(algorithm_name, valid_algorithms)
            except ImportError:
                pass

        suggestions = kwargs.pop("suggestions", [])
        if valid_algorithms:
            suggestions.append(f"available algorithms: {', '.join(sorted(valid_algorithms)[:5])}")

        super().__init__(message, suggestions=suggestions, did_you_mean=did_you_mean, **kwargs)


class CommunityDetectionError(AlgorithmError):
    """Exception raised when community detection fails.

    Error code: PX301
    """

    default_code = "PX301"


class CentralityComputationError(AlgorithmError):
    """Exception raised when centrality computation fails.

    Error code: PX301
    """

    default_code = "PX301"


class DecompositionError(AlgorithmError):
    """Exception raised when network decomposition fails.

    Error code: PX301
    """

    default_code = "PX301"


class EmbeddingError(AlgorithmError):
    """Exception raised when embedding generation fails.

    Error code: PX301
    """

    default_code = "PX301"


class ConversionError(Py3plexException):
    """Exception raised when format conversion fails.

    Error code: PX501
    """

    default_code = "PX501"


class IncompatibleNetworkError(Py3plexException):
    """Exception raised when network format is incompatible with an operation.

    Error code: PX304
    """

    default_code = "PX304"


class Py3plexMatrixError(Py3plexException):
    """Exception raised when matrix operations fail or matrix is invalid.

    Error code: PX001
    """

    default_code = "PX001"


class ExternalToolError(Py3plexException):
    """Exception raised when external tool execution fails.

    Error code: PX001
    """

    default_code = "PX001"


class Py3plexIOError(Py3plexException):
    """Exception raised when I/O operations fail (file reading, writing, etc.).

    Error code: PX101
    """

    default_code = "PX101"


class Py3plexFormatError(Py3plexException):
    """Exception raised when input format is invalid or cannot be parsed.

    Error code: PX103
    """

    default_code = "PX103"

    def __init__(
        self,
        message: str,
        *,
        valid_formats: Optional[List[str]] = None,
        input_format: Optional[str] = None,
        **kwargs,
    ):
        """Initialize Py3plexFormatError.

        Args:
            message: The error message
            valid_formats: List of valid format names
            input_format: The invalid format that was provided
            **kwargs: Additional arguments for Py3plexException
        """
        did_you_mean = kwargs.pop("did_you_mean", None)
        if input_format and valid_formats and not did_you_mean:
            try:
                from py3plex.errors import find_similar
                did_you_mean = find_similar(input_format, valid_formats)
            except ImportError:
                pass

        suggestions = kwargs.pop("suggestions", [])
        if valid_formats:
            suggestions.append(f"valid formats: {', '.join(sorted(valid_formats))}")

        super().__init__(message, suggestions=suggestions, did_you_mean=did_you_mean, **kwargs)


class Py3plexLayoutError(Py3plexException):
    """Exception raised when layout computation or visualization positioning fails.

    Error code: PX402
    """

    default_code = "PX402"
