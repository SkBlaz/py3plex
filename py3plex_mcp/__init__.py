"""py3plex MCP Server - Model Context Protocol integration for py3plex.

This package provides a production-ready MCP server that exposes py3plex functionality
as tools and resources for AI coding assistants via the Model Context Protocol.

Usage:
    pip install py3plex[mcp]
    py3plex-mcp

Version: 1.1.3
"""

__version__ = "1.1.3"

__all__ = [
    "__version__",
]

# Import main only when accessed to avoid import errors without MCP SDK
def __getattr__(name):
    if name == "main":
        from py3plex_mcp.server import main
        return main
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
