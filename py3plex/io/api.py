"""
Public API for reading and writing multilayer graphs.

This module provides the main entry points for I/O operations with
format detection and a registry system for extensibility.
"""

from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

from .exceptions import FormatUnsupportedError
from .schema import MultiLayerGraph

# Type aliases
ReaderFunc = Callable[..., MultiLayerGraph]
WriterFunc = Callable[..., None]

# Internal registries
_READERS: Dict[str, ReaderFunc] = {}
_WRITERS: Dict[str, WriterFunc] = {}


def register_reader(format_name: str, reader_func: ReaderFunc) -> None:
    """
    Register a reader function for a specific format.

    Args:
        format_name: Name of the format (e.g., 'json', 'csv', 'graphml')
        reader_func: Function that takes (filepath, **kwargs) and returns MultiLayerGraph

    Example:
        >>> def my_reader(filepath, **kwargs):
        ...     # Custom reading logic
        ...     return MultiLayerGraph(...)
        >>> register_reader('myformat', my_reader)
    """
    _READERS[format_name.lower()] = reader_func


def register_writer(format_name: str, writer_func: WriterFunc) -> None:
    """
    Register a writer function for a specific format.

    Args:
        format_name: Name of the format (e.g., 'json', 'csv', 'graphml')
        writer_func: Function that takes (graph, filepath, **kwargs) and writes to file

    Example:
        >>> def my_writer(graph, filepath, **kwargs):
        ...     # Custom writing logic
        ...     pass
        >>> register_writer('myformat', my_writer)
    """
    _WRITERS[format_name.lower()] = writer_func


def supported_formats(read: bool = True, write: bool = True) -> Dict[str, List[str]]:
    """
    Get list of supported formats for read and/or write operations.

    Args:
        read: Include formats that support reading
        write: Include formats that support writing

    Returns:
        Dictionary with 'read' and/or 'write' keys containing lists of format names

    Example:
        >>> formats = supported_formats()
        >>> print(formats)
        {'read': ['json', 'jsonl', 'csv'], 'write': ['json', 'jsonl', 'csv']}
    """
    result = {}
    if read:
        result["read"] = sorted(_READERS.keys())
    if write:
        result["write"] = sorted(_WRITERS.keys())
    return result


def _detect_format(filepath: Union[str, Path]) -> Optional[str]:
    """
    Detect format from file extension.

    Args:
        filepath: Path to the file

    Returns:
        Format name if detected, None otherwise
    """
    path = Path(filepath)

    # Handle compressed files
    if path.suffix == ".gz":
        # Get extension before .gz
        stem = path.stem
        ext = Path(stem).suffix.lower().lstrip(".")
    else:
        ext = path.suffix.lower().lstrip(".")

    # Map extensions to format names
    extension_map = {
        "json": "json",
        "jsonl": "jsonl",
        "csv": "csv",
        "graphml": "graphml",
        "gexf": "gexf",
        "h5": "hdf5",
        "hdf5": "hdf5",
    }

    return extension_map.get(ext)


def read(
    filepath: Union[str, Path], format: Optional[str] = None, **kwargs
) -> MultiLayerGraph:
    """
    Read a multilayer graph from a file.

    Args:
        filepath: Path to the input file
        format: Format name (e.g., 'json', 'csv'). If None, auto-detected from extension
        **kwargs: Additional arguments passed to the format-specific reader

    Returns:
        MultiLayerGraph instance

    Raises:
        FormatUnsupportedError: If format is not supported or cannot be detected
        FileNotFoundError: If file does not exist

    Example:
        >>> graph = read('network.json')
        >>> graph = read('network.csv', format='csv')
    """
    filepath = Path(filepath)

    # Check file exists
    if not filepath.exists():
        raise FileNotFoundError(f"File not found: {filepath}")

    # Auto-detect format if not provided
    if format is None:
        format = _detect_format(filepath)
        if format is None:
            raise FormatUnsupportedError(
                filepath.suffix.lstrip(".") or "unknown", "read"
            )

    format = format.lower()

    # Get reader
    if format not in _READERS:
        raise FormatUnsupportedError(format, "read")

    reader = _READERS[format]
    return reader(filepath, **kwargs)


def write(
    graph: MultiLayerGraph,
    filepath: Union[str, Path],
    format: Optional[str] = None,
    **kwargs,
) -> None:
    """
    Write a multilayer graph to a file.

    Args:
        graph: MultiLayerGraph to write
        filepath: Path to the output file
        format: Format name (e.g., 'json', 'csv'). If None, auto-detected from extension
        **kwargs: Additional arguments passed to the format-specific writer

    Raises:
        FormatUnsupportedError: If format is not supported or cannot be detected

    Example:
        >>> write(graph, 'network.json')
        >>> write(graph, 'network.csv', format='csv', deterministic=True)
    """
    filepath = Path(filepath)

    # Auto-detect format if not provided
    if format is None:
        format = _detect_format(filepath)
        if format is None:
            raise FormatUnsupportedError(
                filepath.suffix.lstrip(".") or "unknown", "write"
            )

    format = format.lower()

    # Get writer
    if format not in _WRITERS:
        raise FormatUnsupportedError(format, "write")

    writer = _WRITERS[format]
    writer(graph, filepath, **kwargs)


def _register_builtin_formats():
    """Register built-in format readers and writers."""
    # Import here to avoid circular imports
    from .formats.csv_format import read_csv, write_csv
    from .formats.json_format import read_json, read_jsonl, write_json, write_jsonl

    # Register JSON formats
    register_reader("json", read_json)
    register_writer("json", write_json)
    register_reader("jsonl", read_jsonl)
    register_writer("jsonl", write_jsonl)

    # Register CSV format
    register_reader("csv", read_csv)
    register_writer("csv", write_csv)


# Register built-in formats on module load
_register_builtin_formats()
