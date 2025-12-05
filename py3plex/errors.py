"""
Rust-style error messages with helpful suggestions for py3plex.

This module provides rich, user-friendly error messages similar to Rust's
excellent error reporting, including:

- Error codes (e.g., PX001, PX002)
- Color-coded output for terminal
- "Help" suggestions with specific fixes
- "Did you mean?" suggestions for typos
- Context showing relevant code snippets
"""

import difflib
import os
import sys
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple


class Severity(Enum):
    """Severity level for error messages."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    HELP = "help"
    NOTE = "note"


# ANSI color codes for terminal output
class Colors:
    """ANSI color codes for terminal output."""

    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    MAGENTA = "\033[95m"
    WHITE = "\033[97m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    RESET = "\033[0m"

    @classmethod
    def supports_color(cls) -> bool:
        """Check if the terminal supports color output."""
        # Check for NO_COLOR environment variable (https://no-color.org/)
        if os.environ.get("NO_COLOR"):
            return False
        # Check if stdout is a TTY
        if not hasattr(sys.stdout, "isatty"):
            return False
        if not sys.stdout.isatty():
            return False
        # Check TERM environment variable
        term = os.environ.get("TERM", "")
        if term == "dumb":
            return False
        return True

    @classmethod
    def colorize(cls, text: str, color: str) -> str:
        """Apply color to text if terminal supports it."""
        if cls.supports_color():
            return f"{color}{text}{cls.RESET}"
        return text


# Error codes for py3plex
# Format: PX[Category][Number]
# Categories:
#   0 = General
#   1 = Parsing/IO
#   2 = Network construction
#   3 = Algorithm
#   4 = Visualization
#   5 = Conversion

ERROR_CODES: Dict[str, Tuple[str, str]] = {
    # General errors
    "PX001": ("invalid_argument", "Invalid argument provided"),
    "PX002": ("missing_argument", "Required argument is missing"),
    "PX003": ("type_mismatch", "Type mismatch in argument"),
    # Parsing/IO errors
    "PX101": ("file_not_found", "File not found"),
    "PX102": ("permission_denied", "Permission denied when accessing file"),
    "PX103": ("invalid_format", "Invalid file format"),
    "PX104": ("empty_file", "File is empty"),
    "PX105": ("parse_error", "Failed to parse file content"),
    "PX106": ("missing_column", "Required column is missing"),
    "PX107": ("invalid_value", "Invalid value in data"),
    "PX108": ("unknown_format", "Unknown or unsupported file format"),
    # Network construction errors
    "PX201": ("invalid_layer", "Invalid or unknown layer"),
    "PX202": ("invalid_node", "Invalid or unknown node"),
    "PX203": ("invalid_edge", "Invalid edge specification"),
    "PX204": ("duplicate_node", "Duplicate node detected"),
    "PX205": ("duplicate_edge", "Duplicate edge detected"),
    "PX206": ("self_loop", "Self-loop detected"),
    "PX207": ("empty_network", "Network is empty"),
    "PX208": ("network_construction", "Failed to construct network"),
    # Algorithm errors
    "PX301": ("algorithm_failed", "Algorithm execution failed"),
    "PX302": ("convergence_failed", "Algorithm did not converge"),
    "PX303": ("invalid_parameter", "Invalid algorithm parameter"),
    "PX304": ("unsupported_network", "Network type not supported by algorithm"),
    # Visualization errors
    "PX401": ("visualization_failed", "Visualization failed"),
    "PX402": ("invalid_layout", "Invalid layout algorithm"),
    "PX403": ("rendering_error", "Failed to render visualization"),
    # Conversion errors
    "PX501": ("conversion_failed", "Format conversion failed"),
    "PX502": ("incompatible_format", "Incompatible format for conversion"),
}


@dataclass
class Span:
    """Represents a location in source content."""

    line: int  # 1-indexed line number
    column: int = 1  # 1-indexed column number
    length: int = 0  # Length of the span
    end_line: Optional[int] = None  # End line for multi-line spans


@dataclass
class SourceContext:
    """Context from source file for error display."""

    file_path: Optional[str] = None
    lines: List[str] = field(default_factory=list)
    span: Optional[Span] = None

    @classmethod
    def from_file(
        cls,
        file_path: str,
        line_number: int,
        column: int = 1,
        length: int = 0,
        context_lines: int = 2,
    ) -> "SourceContext":
        """Create source context from a file.

        Args:
            file_path: Path to the source file
            line_number: Line number (1-indexed)
            column: Column number (1-indexed)
            length: Length of the span to highlight
            context_lines: Number of context lines before/after

        Returns:
            SourceContext instance
        """
        try:
            with open(file_path) as f:
                all_lines = f.readlines()
        except OSError:
            return cls(file_path=file_path)

        # Calculate range of lines to include
        start = max(0, line_number - 1 - context_lines)
        end = min(len(all_lines), line_number + context_lines)

        lines = [line.rstrip("\n\r") for line in all_lines[start:end]]

        return cls(
            file_path=file_path,
            lines=lines,
            span=Span(
                line=line_number,
                column=column,
                length=length,
            ),
        )


@dataclass
class Suggestion:
    """A suggestion for fixing an error."""

    message: str
    replacement: Optional[str] = None
    span: Optional[Span] = None


@dataclass
class Note:
    """An additional note providing context."""

    message: str


@dataclass
class ErrorMessage:
    """A rich error message with Rust-like formatting."""

    code: str
    severity: Severity
    title: str
    message: str
    context: Optional[SourceContext] = None
    suggestions: List[Suggestion] = field(default_factory=list)
    notes: List[Note] = field(default_factory=list)
    did_you_mean: Optional[str] = None

    def format(self, use_color: bool = True) -> str:
        """Format the error message for display.

        Args:
            use_color: Whether to use ANSI colors

        Returns:
            Formatted error message string
        """
        lines = []

        # Header line: severity[code]: title
        severity_colors = {
            Severity.ERROR: Colors.RED,
            Severity.WARNING: Colors.YELLOW,
            Severity.INFO: Colors.BLUE,
            Severity.HELP: Colors.CYAN,
            Severity.NOTE: Colors.GREEN,
        }

        color = severity_colors.get(self.severity, Colors.WHITE)
        severity_str = self.severity.value

        if use_color and Colors.supports_color():
            header = (
                f"{Colors.BOLD}{color}{severity_str}"
                f"{Colors.RESET}{Colors.BOLD}[{self.code}]{Colors.RESET}: "
                f"{Colors.BOLD}{self.title}{Colors.RESET}"
            )
        else:
            header = f"{severity_str}[{self.code}]: {self.title}"

        lines.append(header)

        # Location line if context is available
        if self.context and self.context.file_path and self.context.span:
            span = self.context.span
            if use_color and Colors.supports_color():
                location = (
                    f"  {Colors.BLUE}-->{Colors.RESET} "
                    f"{self.context.file_path}:{span.line}:{span.column}"
                )
            else:
                location = f"  --> {self.context.file_path}:{span.line}:{span.column}"
            lines.append(location)

        # Separator
        if use_color and Colors.supports_color():
            lines.append(f"   {Colors.BLUE}|{Colors.RESET}")
        else:
            lines.append("   |")

        # Source code context with highlighting
        if self.context and self.context.lines and self.context.span:
            span = self.context.span
            start_line = max(1, span.line - len(self.context.lines) // 2)

            for i, line_content in enumerate(self.context.lines):
                current_line = start_line + i
                line_num_str = str(current_line).rjust(3)

                if use_color and Colors.supports_color():
                    if current_line == span.line:
                        # This is the error line
                        lines.append(
                            f"{Colors.BLUE}{line_num_str} |{Colors.RESET} {line_content}"
                        )
                        # Add underline
                        underline = " " * (span.column - 1) + "^" * max(1, span.length)
                        lines.append(
                            f"   {Colors.BLUE}|{Colors.RESET} {color}{underline}{Colors.RESET}"
                        )
                    else:
                        lines.append(
                            f"{Colors.BLUE}{line_num_str} |{Colors.RESET} {line_content}"
                        )
                else:
                    if current_line == span.line:
                        lines.append(f"{line_num_str} | {line_content}")
                        underline = " " * (span.column - 1) + "^" * max(1, span.length)
                        lines.append(f"   | {underline}")
                    else:
                        lines.append(f"{line_num_str} | {line_content}")

        # Message
        if self.message:
            if use_color and Colors.supports_color():
                lines.append(f"   {Colors.BLUE}|{Colors.RESET}")
                lines.append(
                    f"   {Colors.BLUE}={Colors.RESET} {self.message}"
                )
            else:
                lines.append("   |")
                lines.append(f"   = {self.message}")

        # "Did you mean?" suggestion
        if self.did_you_mean:
            if use_color and Colors.supports_color():
                lines.append("")
                lines.append(
                    f"{Colors.CYAN}help{Colors.RESET}: did you mean `{self.did_you_mean}`?"
                )
            else:
                lines.append("")
                lines.append(f"help: did you mean `{self.did_you_mean}`?")

        # Suggestions
        for suggestion in self.suggestions:
            if use_color and Colors.supports_color():
                lines.append("")
                lines.append(f"{Colors.CYAN}help{Colors.RESET}: {suggestion.message}")
                if suggestion.replacement:
                    lines.append(
                        f"      {Colors.GREEN}{suggestion.replacement}{Colors.RESET}"
                    )
            else:
                lines.append("")
                lines.append(f"help: {suggestion.message}")
                if suggestion.replacement:
                    lines.append(f"      {suggestion.replacement}")

        # Notes
        for note in self.notes:
            if use_color and Colors.supports_color():
                lines.append("")
                lines.append(f"{Colors.GREEN}note{Colors.RESET}: {note.message}")
            else:
                lines.append("")
                lines.append(f"note: {note.message}")

        return "\n".join(lines)

    def __str__(self) -> str:
        """Return formatted error message."""
        return self.format(use_color=True)


def find_similar(needle: str, haystack: List[str], cutoff: float = 0.6) -> Optional[str]:
    """Find the most similar string from a list of candidates.

    Uses difflib to find close matches, similar to Rust's "did you mean" feature.

    Args:
        needle: The string to match
        haystack: List of candidate strings
        cutoff: Minimum similarity ratio (0.0 to 1.0)

    Returns:
        The most similar string, or None if no close match found
    """
    if not haystack:
        return None

    matches = difflib.get_close_matches(needle, haystack, n=1, cutoff=cutoff)
    return matches[0] if matches else None


# Pre-built error message builders for common cases


def file_not_found_error(
    file_path: str,
    similar_files: Optional[List[str]] = None,
) -> ErrorMessage:
    """Create error message for file not found.

    Args:
        file_path: Path to the file that was not found
        similar_files: Optional list of similar file paths for suggestions

    Returns:
        ErrorMessage instance
    """
    suggestions = [
        Suggestion(message="Check that the file path is correct"),
        Suggestion(message="Ensure the file exists and you have read permission"),
    ]

    did_you_mean = None
    if similar_files:
        import os

        basename = os.path.basename(file_path)
        similar_basenames = [os.path.basename(f) for f in similar_files]
        match = find_similar(basename, similar_basenames)
        if match:
            # Find the full path for the match
            idx = similar_basenames.index(match)
            did_you_mean = similar_files[idx]

    return ErrorMessage(
        code="PX101",
        severity=Severity.ERROR,
        title="file not found",
        message=f"could not find file `{file_path}`",
        suggestions=suggestions,
        did_you_mean=did_you_mean,
    )


def invalid_input_type_error(
    input_type: str,
    valid_types: List[str],
) -> ErrorMessage:
    """Create error message for invalid input type.

    Args:
        input_type: The invalid input type provided
        valid_types: List of valid input types

    Returns:
        ErrorMessage instance
    """
    did_you_mean = find_similar(input_type, valid_types)

    suggestions = [
        Suggestion(
            message=f"valid input types are: {', '.join(sorted(valid_types)[:5])}..."
            if len(valid_types) > 5
            else f"valid input types are: {', '.join(sorted(valid_types))}"
        ),
    ]

    notes = []
    # Add common format hints
    if any(t in valid_types for t in ["edgelist", "multiedgelist"]):
        notes.append(
            Note(
                message="for multilayer networks, use 'multiedgelist' format: "
                "node1 layer1 node2 layer2 [weight]"
            )
        )
        notes.append(
            Note(
                message="for simple networks, use 'edgelist' format: "
                "node1 node2 [weight]"
            )
        )

    return ErrorMessage(
        code="PX108",
        severity=Severity.ERROR,
        title="unknown input type",
        message=f"input type `{input_type}` is not recognized",
        suggestions=suggestions,
        notes=notes,
        did_you_mean=did_you_mean,
    )


def missing_column_error(
    file_path: str,
    missing_columns: List[str],
    found_columns: List[str],
    line_number: int = 1,
) -> ErrorMessage:
    """Create error message for missing CSV columns.

    Args:
        file_path: Path to the CSV file
        missing_columns: List of missing column names
        found_columns: List of columns that were found
        line_number: Line number of the header row

    Returns:
        ErrorMessage instance
    """
    context = SourceContext.from_file(
        file_path,
        line_number=line_number,
        column=1,
        length=0,
    )

    suggestions = []

    # Check if any found column is similar to missing columns
    for missing in missing_columns:
        similar = find_similar(missing, found_columns)
        if similar:
            suggestions.append(
                Suggestion(
                    message=f"column `{similar}` looks similar to required `{missing}`",
                    replacement=f"rename `{similar}` to `{missing}`",
                )
            )

    suggestions.append(
        Suggestion(
            message=f"required columns: {', '.join(missing_columns)}"
        )
    )

    return ErrorMessage(
        code="PX106",
        severity=Severity.ERROR,
        title="missing required column(s)",
        message=f"could not find column(s): {', '.join(missing_columns)}",
        context=context,
        suggestions=suggestions,
        notes=[
            Note(message=f"found columns: {', '.join(found_columns)}"),
        ],
    )


def invalid_layer_error(
    layer_name: str,
    available_layers: List[str],
    file_path: Optional[str] = None,
    line_number: Optional[int] = None,
) -> ErrorMessage:
    """Create error message for invalid layer name.

    Args:
        layer_name: The invalid layer name
        available_layers: List of available layer names
        file_path: Optional file path for context
        line_number: Optional line number for context

    Returns:
        ErrorMessage instance
    """
    did_you_mean = find_similar(layer_name, available_layers)

    context = None
    if file_path and line_number:
        context = SourceContext.from_file(file_path, line_number)

    suggestions = []
    if available_layers:
        suggestions.append(
            Suggestion(
                message=f"available layers: {', '.join(sorted(available_layers)[:5])}"
            )
        )

    return ErrorMessage(
        code="PX201",
        severity=Severity.ERROR,
        title="invalid layer",
        message=f"layer `{layer_name}` does not exist in the network",
        context=context,
        suggestions=suggestions,
        did_you_mean=did_you_mean,
    )


def parse_error(
    file_path: str,
    line_number: int,
    message: str,
    expected: Optional[str] = None,
    got: Optional[str] = None,
) -> ErrorMessage:
    """Create error message for parsing errors.

    Args:
        file_path: Path to the file being parsed
        line_number: Line number where error occurred
        message: Error message
        expected: What was expected (optional)
        got: What was found (optional)

    Returns:
        ErrorMessage instance
    """
    context = SourceContext.from_file(file_path, line_number)

    suggestions = []
    notes = []

    if expected and got:
        notes.append(Note(message=f"expected {expected}, found {got}"))

    return ErrorMessage(
        code="PX105",
        severity=Severity.ERROR,
        title="parse error",
        message=message,
        context=context,
        suggestions=suggestions,
        notes=notes,
    )


def invalid_algorithm_error(
    algorithm_name: str,
    valid_algorithms: List[str],
    operation: str = "operation",
) -> ErrorMessage:
    """Create error message for invalid algorithm name.

    Args:
        algorithm_name: The invalid algorithm name
        valid_algorithms: List of valid algorithm names
        operation: Description of the operation (e.g., "community detection")

    Returns:
        ErrorMessage instance
    """
    did_you_mean = find_similar(algorithm_name, valid_algorithms)

    return ErrorMessage(
        code="PX301",
        severity=Severity.ERROR,
        title="unknown algorithm",
        message=f"algorithm `{algorithm_name}` is not available for {operation}",
        suggestions=[
            Suggestion(
                message=f"available algorithms: {', '.join(sorted(valid_algorithms))}"
            )
        ],
        did_you_mean=did_you_mean,
    )


def self_loop_warning(
    node: str,
    layer: Optional[str] = None,
    file_path: Optional[str] = None,
    line_number: Optional[int] = None,
) -> ErrorMessage:
    """Create warning message for self-loop.

    Args:
        node: Node with self-loop
        layer: Optional layer name
        file_path: Optional file path for context
        line_number: Optional line number for context

    Returns:
        ErrorMessage instance
    """
    context = None
    if file_path and line_number:
        context = SourceContext.from_file(file_path, line_number)

    location = f"node `{node}`" if not layer else f"node `{node}` in layer `{layer}`"

    return ErrorMessage(
        code="PX206",
        severity=Severity.WARNING,
        title="self-loop detected",
        message=f"edge from {location} to itself",
        context=context,
        notes=[
            Note(message="self-loops may cause issues with some algorithms"),
        ],
    )


def duplicate_edge_warning(
    source: str,
    target: str,
    layer: Optional[str] = None,
    file_path: Optional[str] = None,
    line_number: Optional[int] = None,
) -> ErrorMessage:
    """Create warning message for duplicate edge.

    Args:
        source: Source node
        target: Target node
        layer: Optional layer name
        file_path: Optional file path for context
        line_number: Optional line number for context

    Returns:
        ErrorMessage instance
    """
    context = None
    if file_path and line_number:
        context = SourceContext.from_file(file_path, line_number)

    edge_str = (
        f"`{source}` -> `{target}`"
        if not layer
        else f"`{source}` -> `{target}` in layer `{layer}`"
    )

    return ErrorMessage(
        code="PX205",
        severity=Severity.WARNING,
        title="duplicate edge",
        message=f"edge {edge_str} appears multiple times",
        context=context,
        suggestions=[
            Suggestion(
                message="consider using edge weights to combine duplicate edges"
            ),
        ],
    )


def format_exception(
    exc: Exception,
    code: Optional[str] = None,
    suggestions: Optional[List[str]] = None,
    notes: Optional[List[str]] = None,
) -> str:
    """Format an exception with Rust-style error formatting.

    This is a convenience function to wrap existing exceptions
    with rich error formatting.

    Args:
        exc: The exception to format
        code: Optional error code (defaults based on exception type)
        suggestions: Optional list of suggestion strings
        notes: Optional list of note strings

    Returns:
        Formatted error message string
    """
    from py3plex.exceptions import (
        AlgorithmError,
        ConversionError,
        InvalidEdgeError,
        InvalidLayerError,
        InvalidNodeError,
        NetworkConstructionError,
        ParsingError,
        Py3plexFormatError,
        Py3plexIOError,
        VisualizationError,
    )

    # Map exception types to error codes
    exception_codes = {
        Py3plexIOError: "PX101",
        ParsingError: "PX105",
        Py3plexFormatError: "PX103",
        InvalidLayerError: "PX201",
        InvalidNodeError: "PX202",
        InvalidEdgeError: "PX203",
        NetworkConstructionError: "PX208",
        AlgorithmError: "PX301",
        VisualizationError: "PX401",
        ConversionError: "PX501",
    }

    # Determine error code
    if code is None:
        for exc_type, exc_code in exception_codes.items():
            if isinstance(exc, exc_type):
                code = exc_code
                break
        else:
            code = "PX001"  # Default to general error

    # Build error message
    error = ErrorMessage(
        code=code,
        severity=Severity.ERROR,
        title=type(exc).__name__,
        message=str(exc),
        suggestions=[Suggestion(message=s) for s in (suggestions or [])],
        notes=[Note(message=n) for n in (notes or [])],
    )

    return error.format()
