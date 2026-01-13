"""Safe path handling utilities for MCP server.

Implements security-first path validation and output directory management.
"""

import os
from pathlib import Path
from typing import Optional

from py3plex_mcp.errors import PathAccessError

# Default safe output directory
DEFAULT_OUTPUT_DIR = Path.home() / ".py3plex_mcp" / "out"

# Forbidden paths (system locations)
FORBIDDEN_PATHS = {
    "/etc",
    "/sys",
    "/proc",
    "/dev",
    "/boot",
    "/root",
    "/var/root",
    "C:\\Windows",
    "C:\\Windows\\System32",
}


def resolve_read_path(path: str) -> Path:
    """Resolve and validate read path.

    Args:
        path: Path to read from

    Returns:
        Resolved absolute Path

    Raises:
        PathAccessError: If path is not allowed
    """
    resolved = Path(path).resolve()

    # Check if file/directory exists
    if not resolved.exists():
        raise PathAccessError(
            str(resolved),
            f"Path does not exist: {resolved}",
        )

    # Reject globbing patterns
    if "*" in str(path) or "?" in str(path):
        raise PathAccessError(
            path,
            "Globbing patterns not allowed for security",
        )

    # Check against forbidden paths
    for forbidden in FORBIDDEN_PATHS:
        forbidden_path = Path(forbidden).resolve()
        try:
            resolved.relative_to(forbidden_path)
            raise PathAccessError(
                str(resolved),
                f"Access to system location {forbidden} is forbidden",
            )
        except ValueError:
            # Not a subpath, continue
            pass

    return resolved


def resolve_out_dir(out_dir: Optional[str] = None) -> Path:
    """Resolve and create output directory.

    Args:
        out_dir: Optional output directory. If None, uses default.

    Returns:
        Resolved output directory Path

    Raises:
        PathAccessError: If directory is not allowed
    """
    if out_dir is None:
        target = DEFAULT_OUTPUT_DIR
    else:
        target = Path(out_dir).resolve()

        # Check against forbidden paths
        for forbidden in FORBIDDEN_PATHS:
            forbidden_path = Path(forbidden).resolve()
            try:
                target.relative_to(forbidden_path)
                raise PathAccessError(
                    str(target),
                    f"Writing to system location {forbidden} is forbidden",
                )
            except ValueError:
                # Not a subpath, continue
                pass

    # Create directory if it doesn't exist
    target.mkdir(parents=True, exist_ok=True)

    return target


def make_unique_filename(out_dir: Path, base_name: str, extension: str) -> Path:
    """Generate unique filename by adding suffix if needed.

    Args:
        out_dir: Output directory
        base_name: Base filename without extension
        extension: File extension (with or without dot)

    Returns:
        Unique file path
    """
    if not extension.startswith("."):
        extension = f".{extension}"

    # Try base name first
    candidate = out_dir / f"{base_name}{extension}"
    if not candidate.exists():
        return candidate

    # Add suffix
    counter = 1
    while True:
        candidate = out_dir / f"{base_name}_{counter}{extension}"
        if not candidate.exists():
            return candidate
        counter += 1
