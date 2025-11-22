"""
Custom exceptions for the I/O module.
"""

from py3plex.exceptions import Py3plexException, Py3plexIOError


class SchemaValidationError(Py3plexIOError):
    """Exception raised when schema validation fails."""

    pass


class ReferentialIntegrityError(SchemaValidationError):
    """Exception raised when referential integrity constraints are violated."""

    pass


class FormatUnsupportedError(Py3plexIOError):
    """Exception raised when an unsupported format is requested."""

    def __init__(self, format_name: str, operation: str = "read"):
        """
        Initialize the exception.

        Args:
            format_name: The unsupported format name
            operation: The operation attempted ('read' or 'write')
        """
        self.format_name = format_name
        self.operation = operation
        super().__init__(
            f"Format '{format_name}' is not supported for {operation} operations. "
            f"Use supported_formats({operation}=True) to see available formats."
        )
