"""Error handling for MCP server.

Provides typed errors and consistent JSON error payloads.
"""

from typing import Any, Dict, Optional


class MCPError(Exception):
    """Base exception for MCP server errors."""

    def __init__(
        self,
        message: str,
        error_type: str = "MCPError",
        hint: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.error_type = error_type
        self.hint = hint
        self.details = details or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict."""
        result = {
            "type": self.error_type,
            "message": self.message,
        }
        if self.hint:
            result["hint"] = self.hint
        if self.details:
            result["details"] = self.details
        return result


class NetworkNotFoundError(MCPError):
    """Network handle not found in registry."""

    def __init__(self, net_id: str):
        super().__init__(
            message=f"Network '{net_id}' not found",
            error_type="NetworkNotFoundError",
            hint="Use py3plex.list_handles to see available networks",
        )


class UnsupportedFormatError(MCPError):
    """Unsupported input format."""

    def __init__(self, format_name: str, supported: list):
        super().__init__(
            message=f"Unsupported format: {format_name}",
            error_type="UnsupportedFormatError",
            hint=f"Supported formats: {', '.join(supported)}",
            details={"supported_formats": supported},
        )


class QueryParseError(MCPError):
    """Query parsing failed."""

    def __init__(self, query: str, error: str):
        super().__init__(
            message=f"Failed to parse query: {error}",
            error_type="QueryParseError",
            hint="Check query syntax. Use py3plex://help/dsl for reference.",
            details={"query": query, "parse_error": error},
        )


class UnsupportedAlgorithmError(MCPError):
    """Community detection algorithm not supported."""

    def __init__(self, algorithm: str, supported: list):
        super().__init__(
            message=f"Unsupported algorithm: {algorithm}",
            error_type="UnsupportedAlgorithmError",
            hint=f"Supported algorithms: {', '.join(supported)}",
            details={"supported_algorithms": supported},
        )


class PathAccessError(MCPError):
    """Path access denied."""

    def __init__(self, path: str, reason: str):
        super().__init__(
            message=f"Path access denied: {path}",
            error_type="PathAccessError",
            hint=reason,
        )


def make_error_response(error: Exception) -> Dict[str, Any]:
    """Create standardized error response from exception.

    Args:
        error: Exception to convert

    Returns:
        Dict with ok=False and error details
    """
    if isinstance(error, MCPError):
        error_dict = error.to_dict()
    else:
        error_dict = {
            "type": type(error).__name__,
            "message": str(error),
        }

    return {
        "ok": False,
        "error": error_dict,
    }
