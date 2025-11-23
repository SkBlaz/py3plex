"""
Public API for reading and writing multilayer graphs.

This module provides the main entry points for I/O operations with
format detection and a registry system for extensibility.
"""

from pathlib import Path
from typing import Callable, Dict, List, Optional, Union

# Optional formal verification support
try:
    from icontract import ensure, require

    ICONTRACT_AVAILABLE = True
except ImportError:
    # Create no-op decorators when icontract is not available
    def require(*args, **kwargs):
        def decorator(func):
            return func

        return decorator

    def ensure(*args, **kwargs):
        def decorator(func):
            return func

        return decorator

    ICONTRACT_AVAILABLE = False

from .exceptions import FormatUnsupportedError, Py3plexIOError
from .schema import MultiLayerGraph

# Type aliases
ReaderFunc = Callable[..., MultiLayerGraph]
WriterFunc = Callable[..., None]

# Internal registries
_READERS: Dict[str, ReaderFunc] = {}
_WRITERS: Dict[str, WriterFunc] = {}


@require(
    lambda format_name: isinstance(format_name, str) and len(format_name) > 0,
    "format_name must be a non-empty string",
)
@require(lambda reader_func: callable(reader_func), "reader_func must be callable")
@ensure(
    lambda format_name: format_name.lower() in _READERS,
    "reader must be registered after call",
)
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

    Contracts:
        - Precondition: format_name must be a non-empty string
        - Precondition: reader_func must be callable
        - Postcondition: reader is registered in _READERS
    """
    _READERS[format_name.lower()] = reader_func


@require(
    lambda format_name: isinstance(format_name, str) and len(format_name) > 0,
    "format_name must be a non-empty string",
)
@require(lambda writer_func: callable(writer_func), "writer_func must be callable")
@ensure(
    lambda format_name: format_name.lower() in _WRITERS,
    "writer must be registered after call",
)
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

    Contracts:
        - Precondition: format_name must be a non-empty string
        - Precondition: writer_func must be callable
        - Postcondition: writer is registered in _WRITERS
    """
    _WRITERS[format_name.lower()] = writer_func


@ensure(lambda result: isinstance(result, dict), "result must be a dictionary")
@ensure(
    lambda read, result: not read or "read" in result,
    "result must contain 'read' key when read=True",
)
@ensure(
    lambda write, result: not write or "write" in result,
    "result must contain 'write' key when write=True",
)
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

    Contracts:
        - Postcondition: result is a dictionary
        - Postcondition: result contains 'read' key when read=True
        - Postcondition: result contains 'write' key when write=True
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
        "arrow": "arrow",
        "feather": "feather",
        "parquet": "parquet",
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
        raise Py3plexIOError(
            f"Cannot read file '{filepath}': File does not exist. "
            f"Please check the file path and try again."
        )

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

    # Register Arrow format if pyarrow is available
    try:
        from .formats.arrow_format import read_arrow, write_arrow

        def read_parquet(filepath, **kwargs):
            """Read graph from Parquet format."""
            return read_arrow(filepath, format="parquet", **kwargs)

        def write_parquet(graph, filepath, **kwargs):
            """Write graph to Parquet format."""
            return write_arrow(graph, filepath, format="parquet", **kwargs)

        register_reader("arrow", read_arrow)
        register_writer("arrow", write_arrow)
        register_reader("feather", read_arrow)
        register_writer("feather", write_arrow)
        register_reader("parquet", read_parquet)
        register_writer("parquet", write_parquet)
    except ImportError:
        # pyarrow not installed, Arrow formats not available
        pass


# Register built-in formats on module load
_register_builtin_formats()
