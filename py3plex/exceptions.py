"""
Custom exception types for the py3plex library.

This module defines domain-specific exceptions to provide clear error messages
and enable better error handling throughout the library.
"""


class Py3plexException(Exception):
    """Base exception class for all py3plex-specific exceptions."""

    pass


class NetworkConstructionError(Py3plexException):
    """Exception raised when network construction fails."""

    pass


class InvalidLayerError(Py3plexException):
    """Exception raised when an invalid layer is specified."""

    pass


class InvalidNodeError(Py3plexException):
    """Exception raised when an invalid node is specified."""

    pass


class InvalidEdgeError(Py3plexException):
    """Exception raised when an invalid edge is specified."""

    pass


class ParsingError(Py3plexException):
    """Exception raised when parsing input data fails."""

    pass


class VisualizationError(Py3plexException):
    """Exception raised when visualization operations fail."""

    pass


class AlgorithmError(Py3plexException):
    """Exception raised when an algorithm execution fails."""

    pass


class CommunityDetectionError(AlgorithmError):
    """Exception raised when community detection fails."""

    pass


class CentralityComputationError(AlgorithmError):
    """Exception raised when centrality computation fails."""

    pass


class DecompositionError(AlgorithmError):
    """Exception raised when network decomposition fails."""

    pass


class EmbeddingError(AlgorithmError):
    """Exception raised when embedding generation fails."""

    pass


class ConversionError(Py3plexException):
    """Exception raised when format conversion fails."""

    pass


class IncompatibleNetworkError(Py3plexException):
    """Exception raised when network format is incompatible with an operation."""

    pass


class Py3plexMatrixError(Py3plexException):
    """Exception raised when matrix operations fail or matrix is invalid."""

    pass


class ExternalToolError(Py3plexException):
    """Exception raised when external tool execution fails."""

    pass


class Py3plexIOError(Py3plexException):
    """Exception raised when I/O operations fail (file reading, writing, etc.)."""

    pass


class Py3plexFormatError(Py3plexException):
    """Exception raised when input format is invalid or cannot be parsed."""

    pass


class Py3plexLayoutError(Py3plexException):
    """Exception raised when layout computation or visualization positioning fails."""

    pass
