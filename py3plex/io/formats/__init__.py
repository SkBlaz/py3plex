"""
Format implementations for multilayer graphs.
"""

from .csv_format import read_csv, write_csv
from .json_format import read_json, read_jsonl, write_json, write_jsonl

# Optional Apache Arrow format (requires pyarrow)
try:
    from .arrow_format import read_arrow, write_arrow

    ARROW_AVAILABLE = True
except ImportError:
    ARROW_AVAILABLE = False

__all__ = [
    "read_json",
    "write_json",
    "read_jsonl",
    "write_jsonl",
    "read_csv",
    "write_csv",
]

# Add Arrow functions to __all__ if available
if ARROW_AVAILABLE:
    __all__.extend(["read_arrow", "write_arrow"])
