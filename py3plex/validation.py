"""Input validation utilities for Py3plex.

This module provides pre-validation functions to catch common input errors
early and provide clear, actionable error messages to users.
"""

import os
from typing import List, Optional, Set

import pandas as pd

from py3plex.exceptions import ParsingError
from py3plex.logging_config import get_logger

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

logger = get_logger(__name__)


@require(lambda file_path: isinstance(file_path, str), "file_path must be a string")
@require(lambda file_path: len(file_path) > 0, "file_path must not be empty")
def validate_file_exists(file_path: str) -> None:
    """Validate that a file exists and is readable.

    Args:
        file_path: Path to file to validate

    Raises:
        ParsingError: If file doesn't exist or isn't readable

    Contracts:
        - Precondition: file_path must be a non-empty string
    """
    if not os.path.exists(file_path):
        raise ParsingError(
            f"File not found: '{file_path}'\n"
            f"Please check:\n"
            f"  1. The file path is correct\n"
            f"  2. The file exists in the specified location\n"
            f"  3. You have permission to read the file"
        )

    if not os.path.isfile(file_path):
        raise ParsingError(
            f"Path exists but is not a file: '{file_path}'\n"
            f"Expected a file, got a directory or other file type."
        )

    if not os.access(file_path, os.R_OK):
        raise ParsingError(
            f"File exists but is not readable: '{file_path}'\n"
            f"Check file permissions and try again."
        )


@require(lambda file_path: isinstance(file_path, str), "file_path must be a string")
@require(lambda file_path: len(file_path) > 0, "file_path must not be empty")
@require(
    lambda required_columns: isinstance(required_columns, list),
    "required_columns must be a list",
)
@require(
    lambda required_columns: len(required_columns) > 0,
    "required_columns must not be empty",
)
@require(
    lambda required_columns: all(isinstance(col, str) for col in required_columns),
    "all required_columns must be strings",
)
def validate_csv_columns(
    file_path: str,
    required_columns: List[str],
    optional_columns: Optional[List[str]] = None,
) -> None:
    """Validate that a CSV file has required columns.

    Args:
        file_path: Path to CSV file
        required_columns: List of column names that must be present
        optional_columns: List of column names that are optional

    Raises:
        ParsingError: If required columns are missing

    Contracts:
        - Precondition: file_path must be a non-empty string
        - Precondition: required_columns must be a non-empty list of strings
    """
    try:
        # Read just the first row to check columns
        df = pd.read_csv(file_path, nrows=0)
        actual_columns = set(df.columns)
        required_set = set(required_columns)

        missing_columns = required_set - actual_columns

        if missing_columns:
            all_expected = required_columns + (optional_columns or [])
            raise ParsingError(
                f"Input CSV missing required column(s): {', '.join(sorted(missing_columns))}\n"
                f"\n"
                f"Expected columns: {', '.join(all_expected)}\n"
                f"Found columns: {', '.join(sorted(actual_columns))}\n"
                f"\n"
                f"Please ensure your CSV file has the following structure:\n"
                f"  {', '.join(all_expected)}\n"
                f"\n"
                f"Example CSV format:\n"
                f"  {','.join(required_columns + ['weight'])}\n"
                f"  A,B,layer1,1.0\n"
                f"  B,C,layer1,1.0\n"
            )

    except pd.errors.EmptyDataError:
        raise ParsingError(
            f"CSV file is empty: '{file_path}'\n"
            f"Please provide a CSV file with data."
        )
    except pd.errors.ParserError as e:
        raise ParsingError(
            f"Failed to parse CSV file: '{file_path}'\n"
            f"Parser error: {str(e)}\n"
            f"\n"
            f"Common issues:\n"
            f"  1. Inconsistent number of columns\n"
            f"  2. Invalid quoting or delimiter\n"
            f"  3. Corrupted file\n"
            f"\n"
            f"Try opening the file in a text editor to check format."
        )


@require(lambda file_path: isinstance(file_path, str), "file_path must be a string")
@require(lambda file_path: len(file_path) > 0, "file_path must not be empty")
@require(
    lambda delimiter: delimiter is None or isinstance(delimiter, str),
    "delimiter must be None or a string",
)
def validate_multiedgelist_format(file_path: str, delimiter: str = None) -> None:
    """Validate multiedgelist file format (source target layer weight).

    Args:
        file_path: Path to multiedgelist file
        delimiter: Optional delimiter (default: whitespace)

    Raises:
        ParsingError: If file format is invalid

    Contracts:
        - Precondition: file_path must be a non-empty string
        - Precondition: delimiter must be None or a string
    """
    validate_file_exists(file_path)

    # Check if it looks like a CSV
    with open(file_path) as f:
        first_line = f.readline().strip()

        # Check for CSV header
        if "," in first_line:
            # Likely a CSV file
            validate_csv_columns(
                file_path,
                required_columns=["source", "target", "layer"],
                optional_columns=["weight"],
            )
            return

    # Check space-delimited format
    with open(file_path) as f:
        line_num = 0
        for line in f:
            line_num += 1
            line = line.strip()

            if not line or line.startswith("#"):
                continue

            parts = line.split(delimiter) if delimiter else line.split()

            if len(parts) not in [4, 5]:
                raise ParsingError(
                    f"Invalid multiedgelist format at line {line_num} in '{file_path}'\n"
                    f"Line content: {line}\n"
                    f"\n"
                    f"Expected format (space-separated):\n"
                    f"  source_node layer1 target_node layer2 [weight]\n"
                    f"\n"
                    f"Got {len(parts)} fields, expected 4 or 5.\n"
                    f"\n"
                    f"OR use CSV format with header:\n"
                    f"  source,target,layer,weight\n"
                    f"  A,B,layer1,1.0\n"
                )

            # Only check first few non-comment lines
            if line_num > 10:
                break


@require(lambda file_path: isinstance(file_path, str), "file_path must be a string")
@require(lambda file_path: len(file_path) > 0, "file_path must not be empty")
@require(
    lambda delimiter: delimiter is None or isinstance(delimiter, str),
    "delimiter must be None or a string",
)
def validate_edgelist_format(file_path: str, delimiter: str = None) -> None:
    """Validate simple edgelist file format (source target weight).

    Args:
        file_path: Path to edgelist file
        delimiter: Optional delimiter (default: whitespace)

    Raises:
        ParsingError: If file format is invalid

    Contracts:
        - Precondition: file_path must be a non-empty string
        - Precondition: delimiter must be None or a string
    """
    validate_file_exists(file_path)

    # Check if it looks like a CSV
    with open(file_path) as f:
        first_line = f.readline().strip()

        # Check for CSV header
        if "," in first_line:
            # Likely a CSV file
            validate_csv_columns(
                file_path,
                required_columns=["source", "target"],
                optional_columns=["weight"],
            )
            return

    # Check space-delimited format
    with open(file_path) as f:
        line_num = 0
        for line in f:
            line_num += 1
            line = line.strip()

            if not line or line.startswith("#"):
                continue

            parts = line.split(delimiter) if delimiter else line.split()

            if len(parts) not in [2, 3]:
                raise ParsingError(
                    f"Invalid edgelist format at line {line_num} in '{file_path}'\n"
                    f"Line content: {line}\n"
                    f"\n"
                    f"Expected format (space-separated):\n"
                    f"  source_node target_node [weight]\n"
                    f"\n"
                    f"Got {len(parts)} fields, expected 2 or 3.\n"
                    f"\n"
                    f"OR use CSV format with header:\n"
                    f"  source,target,weight\n"
                    f"  A,B,1.0\n"
                )

            # Only check first few non-comment lines
            if line_num > 10:
                break


@require(lambda input_type: isinstance(input_type, str), "input_type must be a string")
@require(lambda input_type: len(input_type) > 0, "input_type must not be empty")
@require(
    lambda valid_types: valid_types is None or isinstance(valid_types, set),
    "valid_types must be None or a set",
)
def validate_input_type(
    input_type: str, valid_types: Optional[Set[str]] = None
) -> None:
    """Validate that input_type is recognized.

    Args:
        input_type: The input type string to validate
        valid_types: Optional set of valid types (uses default if None)

    Raises:
        ParsingError: If input_type is not valid

    Contracts:
        - Precondition: input_type must be a non-empty string
        - Precondition: valid_types must be None or a set
    """
    if valid_types is None:
        valid_types = {
            "gml",
            "nx",
            "multiplex_folder",
            "sparse",
            "sparse_network",
            "gpickle_biomine",
            "gpickle",
            "multiedgelist",
            "detangler_json",
            "edgelist",
            "edgelist_spin",
            "edgelist_with_edge_types",
            "multiedge_tuple_list",
            "multiplex_edges",
            "graphml",
        }

    if input_type not in valid_types:
        raise ParsingError(
            f"Invalid input_type: '{input_type}'\n"
            f"\n"
            f"Valid input types:\n" +
            "\n".join(f"  - {t}" for t in sorted(valid_types)) +
            "\n\n"
            "Most common formats:\n"
            "  - 'multiedgelist': Multilayer edge list (source target layer weight)\n"
            "  - 'edgelist': Simple edge list (source target weight)\n"
            "  - 'graphml': GraphML XML format\n"
            "  - 'gml': Graph Modeling Language\n"
            "  - 'gpickle': NetworkX pickle format\n"
        )


@require(lambda file_path: isinstance(file_path, str), "file_path must be a string")
@require(lambda input_type: isinstance(input_type, str), "input_type must be a string")
@require(lambda input_type: len(input_type) > 0, "input_type must not be empty")
def validate_network_data(file_path: str, input_type: str) -> None:
    """Validate network data before parsing.

    This is the main entry point for validation. It performs appropriate
    validation based on the input type.

    Args:
        file_path: Path to network file
        input_type: Type of input file

    Raises:
        ParsingError: If validation fails

    Contracts:
        - Precondition: file_path must be a string
        - Precondition: input_type must be a non-empty string
    """
    # Validate input type
    validate_input_type(input_type)

    # Validate file exists (for file-based inputs)
    if input_type not in ["nx", "multiedge_tuple_list"]:
        validate_file_exists(file_path)

    # Format-specific validation
    if input_type == "multiedgelist":
        try:
            validate_multiedgelist_format(file_path)
        except ParsingError:
            # Re-raise with additional context
            raise
        except Exception as e:
            raise ParsingError(
                f"Unexpected error validating multiedgelist format: {str(e)}\n"
                f"File: '{file_path}'"
            )

    elif input_type == "edgelist":
        try:
            validate_edgelist_format(file_path)
        except ParsingError:
            raise
        except Exception as e:
            raise ParsingError(
                f"Unexpected error validating edgelist format: {str(e)}\n"
                f"File: '{file_path}'"
            )

    logger.info(f"Validation passed for {input_type} file: {file_path}")


# Export main validation function
__all__ = [
    "validate_network_data",
    "validate_file_exists",
    "validate_csv_columns",
    "validate_multiedgelist_format",
    "validate_edgelist_format",
    "validate_input_type",
]
