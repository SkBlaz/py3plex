"""
File linter for py3plex graph data files.

Validates data format, detects potential issues, and provides Rust-style
error messages with helpful suggestions for fixing issues.

Example output:
    error[PX105]: parse error
      --> network.csv:3:1
       |
     2 | A,B,1.0
     3 | C,D,invalid
       | ^
       |
       = Invalid weight value 'invalid' (not a number)

    help: weights must be numeric values
          Use a floating-point number like 1.0 or 0.5

For graph data files (CSV, edgelist, multiedgelist formats).
"""

import csv
from pathlib import Path
from typing import List, Optional, Set, Tuple

from py3plex.logging_config import get_logger

logger = get_logger(__name__)


# Error codes for linting issues
LINT_ERROR_CODES = {
    "file_not_found": "PX101",
    "permission_denied": "PX102",
    "invalid_format": "PX103",
    "parse_error": "PX105",
    "missing_column": "PX106",
    "invalid_value": "PX107",
    "self_loop": "PX206",
    "duplicate_edge": "PX205",
}


class LintIssue:
    """Represents a linting issue found in a graph data file.

    Provides Rust-style error formatting with:
    - Error codes (e.g., PX105)
    - Clear error messages
    - Helpful suggestions
    - Source context with line highlighting
    """

    SEVERITY_ERROR = "ERROR"
    SEVERITY_WARNING = "WARNING"
    SEVERITY_INFO = "INFO"

    def __init__(
        self,
        severity: str,
        message: str,
        line_number: Optional[int] = None,
        suggestion: Optional[str] = None,
        code: Optional[str] = None,
        line_content: Optional[str] = None,
        column: Optional[int] = None,
        file_path: Optional[str] = None,
    ):
        """
        Initialize a lint issue.

        Args:
            severity: Issue severity (ERROR, WARNING, INFO)
            message: Description of the issue
            line_number: Optional line number where issue was found
            suggestion: Optional suggestion for fixing the issue
            code: Optional error code (e.g., "PX105")
            line_content: Optional content of the line with the issue
            column: Optional column number (1-indexed)
            file_path: Optional path to the file
        """
        self.severity = severity
        self.message = message
        self.line_number = line_number
        self.suggestion = suggestion
        self.code = code or self._default_code()
        self.line_content = line_content
        self.column = column or 1
        self.file_path = file_path

    def _default_code(self) -> str:
        """Get default error code based on severity."""
        if self.severity == self.SEVERITY_ERROR:
            return "PX105"
        elif self.severity == self.SEVERITY_WARNING:
            return "PX107"
        return "PX001"

    def format(self, use_color: bool = True) -> str:
        """Format the lint issue with Rust-style error formatting.

        Args:
            use_color: Whether to use ANSI colors

        Returns:
            Formatted error message string
        """
        try:
            from py3plex.errors import ErrorMessage, Severity, Suggestion

            severity_map = {
                self.SEVERITY_ERROR: Severity.ERROR,
                self.SEVERITY_WARNING: Severity.WARNING,
                self.SEVERITY_INFO: Severity.INFO,
            }

            # Create source context if we have line info
            context = None
            if self.file_path and self.line_number and self.line_content:
                from py3plex.errors import SourceContext, Span

                context = SourceContext(
                    file_path=self.file_path,
                    lines=[self.line_content],
                    span=Span(
                        line=self.line_number,
                        column=self.column,
                        length=len(self.line_content) if self.line_content else 1,
                    ),
                )

            suggestions = []
            if self.suggestion:
                suggestions.append(Suggestion(message=self.suggestion))

            error = ErrorMessage(
                code=self.code,
                severity=severity_map.get(self.severity, Severity.ERROR),
                title=self._get_title(),
                message=self.message,
                context=context,
                suggestions=suggestions,
            )
            return error.format(use_color=use_color)
        except ImportError:
            # Fallback to simple formatting
            return self._simple_format()

    def _get_title(self) -> str:
        """Get a short title based on the error code."""
        titles = {
            "PX101": "file not found",
            "PX102": "permission denied",
            "PX103": "invalid format",
            "PX105": "parse error",
            "PX106": "missing column",
            "PX107": "invalid value",
            "PX205": "duplicate edge",
            "PX206": "self-loop",
        }
        return titles.get(self.code, "lint issue")

    def _simple_format(self) -> str:
        """Simple fallback formatting."""
        result = f"[{self.severity}]"
        if self.line_number is not None:
            result += f" Line {self.line_number}:"
        result += f" {self.message}"
        if self.suggestion:
            result += f"\n  → Suggestion: {self.suggestion}"
        return result

    def __str__(self) -> str:
        """String representation of the lint issue."""
        return self.format(use_color=True)


class GraphFileLinter:
    """Linter for graph data files with Rust-style error messages."""

    def __init__(self, file_path: str):
        """
        Initialize linter for a graph data file.

        Args:
            file_path: Path to the file to lint
        """
        self.file_path = Path(file_path)
        self.issues: List[LintIssue] = []
        self._file_lines: List[str] = []  # Cache file lines for context

    def _read_file_lines(self) -> List[str]:
        """Read and cache file lines for providing context."""
        if not self._file_lines:
            try:
                with open(self.file_path) as f:
                    self._file_lines = [line.rstrip("\n\r") for line in f.readlines()]
            except OSError:
                self._file_lines = []
        return self._file_lines

    def _get_line_content(self, line_number: int) -> Optional[str]:
        """Get content of a specific line (1-indexed)."""
        lines = self._read_file_lines()
        if 0 < line_number <= len(lines):
            return lines[line_number - 1]
        return None

    def _add_issue(
        self,
        severity: str,
        message: str,
        line_number: Optional[int] = None,
        suggestion: Optional[str] = None,
        code: Optional[str] = None,
        column: Optional[int] = None,
    ) -> None:
        """Add an issue with file context.

        Args:
            severity: Issue severity
            message: Issue message
            line_number: Line number (1-indexed)
            suggestion: Suggestion for fixing
            code: Error code
            column: Column number (1-indexed)
        """
        line_content = None
        if line_number:
            line_content = self._get_line_content(line_number)

        self.issues.append(
            LintIssue(
                severity=severity,
                message=message,
                line_number=line_number,
                suggestion=suggestion,
                code=code,
                line_content=line_content,
                column=column,
                file_path=str(self.file_path),
            )
        )

    def lint(self) -> List[LintIssue]:
        """
        Run all linting checks on the file.

        Returns:
            List of issues found
        """
        self.issues = []
        self._file_lines = []  # Reset cache

        # Check file exists
        if not self.file_path.exists():
            self._add_issue(
                LintIssue.SEVERITY_ERROR,
                f"File not found: {self.file_path}",
                suggestion="Check the file path is correct",
                code="PX101",
            )
            return self.issues

        # Check file is readable
        try:
            with open(self.file_path):
                pass
        except PermissionError:
            self._add_issue(
                LintIssue.SEVERITY_ERROR,
                f"File is not readable: {self.file_path}",
                suggestion="Check file permissions",
                code="PX102",
            )
            return self.issues

        # Detect file format and run appropriate checks
        file_format = self._detect_format()
        logger.debug(f"Detected file format: {file_format}")

        if file_format == "csv":
            self._lint_csv()
        elif file_format == "edgelist":
            self._lint_edgelist()
        elif file_format == "multiedgelist":
            self._lint_multiedgelist()
        else:
            self._add_issue(
                LintIssue.SEVERITY_WARNING,
                "Unknown file format, treating as edgelist",
                code="PX108",
            )
            self._lint_edgelist()

        return self.issues

    def _detect_format(self) -> str:
        """
        Detect the format of the graph data file.

        Returns:
            Format string: 'csv', 'edgelist', or 'multiedgelist'
        """
        # Try to detect by reading first few lines
        try:
            with open(self.file_path) as f:
                first_line = f.readline().strip()
                if not first_line:
                    return "edgelist"

                # Count columns
                # Try comma-separated
                if "," in first_line:
                    parts = first_line.split(",")
                    num_cols = len(parts)
                    # Check if first row looks like CSV header
                    if any(
                        header in first_line.lower()
                        for header in ["src", "dst", "source", "target", "node"]
                    ):
                        return "csv"
                    elif num_cols >= 4:
                        return "csv"  # Likely CSV with multiple columns
                    else:
                        return "csv"

                # Try space/tab-separated
                parts = first_line.split()
                num_cols = len(parts)

                if num_cols >= 4:
                    # Likely multiedgelist: node1 layer1 node2 layer2 [weight]
                    return "multiedgelist"
                elif num_cols == 2 or num_cols == 3:
                    # Likely simple edgelist: node1 node2 [weight]
                    return "edgelist"
                else:
                    return "edgelist"

        except Exception as e:
            logger.warning(f"Error detecting format: {e}")
            return "edgelist"

    def _lint_csv(self) -> None:
        """Lint a CSV format file."""
        try:
            with open(self.file_path, newline="") as f:
                # Try to detect delimiter
                sample = f.read(1024)
                f.seek(0)
                sniffer = csv.Sniffer()
                try:
                    dialect = sniffer.sniff(sample)
                    delimiter = dialect.delimiter
                except csv.Error:
                    delimiter = ","

                reader = csv.DictReader(f, delimiter=delimiter)

                # Check for required columns
                if reader.fieldnames is None:
                    self._add_issue(
                        LintIssue.SEVERITY_ERROR,
                        "CSV file has no header row",
                        line_number=1,
                        suggestion="Add a header row with column names like: src,dst,src_layer,dst_layer",
                        code="PX106",
                    )
                    return

                fieldnames = reader.fieldnames
                # Common column name variations
                src_cols = ["src", "source", "from", "node1"]
                dst_cols = ["dst", "destination", "to", "target", "node2"]
                src_layer_cols = ["src_layer", "source_layer", "layer1"]
                dst_layer_cols = ["dst_layer", "destination_layer", "target_layer", "layer2"]

                has_src = any(col in fieldnames for col in src_cols)
                has_dst = any(col in fieldnames for col in dst_cols)

                if not has_src:
                    self._add_issue(
                        LintIssue.SEVERITY_ERROR,
                        f"Missing source node column. Found columns: {', '.join(fieldnames)}",
                        line_number=1,
                        suggestion=f"Add a column named one of: {', '.join(src_cols)}",
                        code="PX106",
                    )

                if not has_dst:
                    self._add_issue(
                        LintIssue.SEVERITY_ERROR,
                        f"Missing destination node column. Found columns: {', '.join(fieldnames)}",
                        line_number=1,
                        suggestion=f"Add a column named one of: {', '.join(dst_cols)}",
                        code="PX106",
                    )

                # Check for multilayer columns
                has_src_layer = any(col in fieldnames for col in src_layer_cols)
                has_dst_layer = any(col in fieldnames for col in dst_layer_cols)

                if not has_src_layer and not has_dst_layer:
                    self._add_issue(
                        LintIssue.SEVERITY_INFO,
                        "No layer columns found - this appears to be a single-layer network",
                        line_number=1,
                    )
                elif has_src_layer and not has_dst_layer:
                    self._add_issue(
                        LintIssue.SEVERITY_WARNING,
                        "Source layer column found but destination layer column is missing",
                        line_number=1,
                        suggestion=f"Add a column named one of: {', '.join(dst_layer_cols)}",
                        code="PX106",
                    )
                elif has_dst_layer and not has_src_layer:
                    self._add_issue(
                        LintIssue.SEVERITY_WARNING,
                        "Destination layer column found but source layer column is missing",
                        line_number=1,
                        suggestion=f"Add a column named one of: {', '.join(src_layer_cols)}",
                        code="PX106",
                    )

                # Validate data rows
                self._validate_csv_rows(reader, fieldnames)

        except Exception as e:
            self._add_issue(
                LintIssue.SEVERITY_ERROR,
                f"Failed to parse CSV file: {str(e)}",
                suggestion="Check that the file is properly formatted CSV",
                code="PX105",
            )

    def _validate_csv_rows(self, reader: csv.DictReader, fieldnames: List[str]) -> None:
        """
        Validate individual CSV rows.

        Args:
            reader: CSV DictReader
            fieldnames: List of column names
        """
        seen_edges: Set[Tuple[str, str, str, str]] = set()
        line_num = 2  # Start at 2 (1 is header)

        for row in reader:
            # Check for empty values in key columns
            src = row.get("src") or row.get("source") or row.get("from") or row.get("node1")
            dst = row.get("dst") or row.get("destination") or row.get("to") or row.get("target") or row.get("node2")

            if not src or not src.strip():
                self._add_issue(
                    LintIssue.SEVERITY_ERROR,
                    "Empty source node",
                    line_number=line_num,
                    suggestion="Provide a valid source node ID",
                    code="PX107",
                )

            if not dst or not dst.strip():
                self._add_issue(
                    LintIssue.SEVERITY_ERROR,
                    "Empty destination node",
                    line_number=line_num,
                    suggestion="Provide a valid destination node ID",
                    code="PX107",
                )

            # Check for self-loops
            if src and dst and src.strip() == dst.strip():
                self._add_issue(
                    LintIssue.SEVERITY_WARNING,
                    f"Self-loop detected: {src} -> {src}",
                    line_number=line_num,
                    suggestion="Self-loops may not be supported by all algorithms",
                    code="PX206",
                )

            # Check weight column if present
            if "weight" in row:
                weight = row["weight"]
                if weight and weight.strip():
                    try:
                        w = float(weight)
                        if w < 0:
                            self._add_issue(
                                LintIssue.SEVERITY_WARNING,
                                f"Negative weight: {w}",
                                line_number=line_num,
                                suggestion="Negative weights may not be supported by all algorithms",
                                code="PX107",
                            )
                    except ValueError:
                        self._add_issue(
                            LintIssue.SEVERITY_ERROR,
                            f"Invalid weight value: '{weight}' (not a number)",
                            line_number=line_num,
                            suggestion="Weights must be numeric values",
                            code="PX107",
                        )

            # Check for duplicate edges
            src_layer = (
                row.get("src_layer")
                or row.get("source_layer")
                or row.get("layer1")
                or "default"
            )
            dst_layer = (
                row.get("dst_layer")
                or row.get("destination_layer")
                or row.get("target_layer")
                or row.get("layer2")
                or "default"
            )

            if src and dst:
                edge_key = (src.strip(), dst.strip(), src_layer, dst_layer)
                if edge_key in seen_edges:
                    self._add_issue(
                        LintIssue.SEVERITY_WARNING,
                        f"Duplicate edge: {src} -> {dst} (layers: {src_layer}, {dst_layer})",
                        line_number=line_num,
                        suggestion="Remove duplicate edges or consolidate with edge weights",
                        code="PX205",
                    )
                seen_edges.add(edge_key)

            line_num += 1

    def _lint_edgelist(self) -> None:
        """Lint a simple edgelist format file (node1 node2 [weight])."""
        seen_edges: Set[Tuple[str, str]] = set()
        line_num = 0

        try:
            with open(self.file_path) as f:
                for line in f:
                    line_num += 1
                    line = line.strip()

                    # Skip empty lines and comments
                    if not line or line.startswith("#"):
                        continue

                    parts = line.split()

                    if len(parts) < 2:
                        self._add_issue(
                            LintIssue.SEVERITY_ERROR,
                            f"Invalid edgelist format: expected at least 2 columns, got {len(parts)}",
                            line_number=line_num,
                            suggestion="Edgelist format: node1 node2 [weight]",
                            code="PX103",
                        )
                        continue

                    src, dst = parts[0], parts[1]

                    # Check for empty nodes
                    if not src or not dst:
                        self._add_issue(
                            LintIssue.SEVERITY_ERROR,
                            "Empty node ID",
                            line_number=line_num,
                            code="PX107",
                        )

                    # Check for self-loops
                    if src == dst:
                        self._add_issue(
                            LintIssue.SEVERITY_WARNING,
                            f"Self-loop detected: {src} -> {src}",
                            line_number=line_num,
                            suggestion="Self-loops may cause issues with some algorithms",
                            code="PX206",
                        )

                    # Check weight if present
                    if len(parts) >= 3:
                        try:
                            w = float(parts[2])
                            if w < 0:
                                self._add_issue(
                                    LintIssue.SEVERITY_WARNING,
                                    f"Negative weight: {w}",
                                    line_number=line_num,
                                    suggestion="Negative weights may not be supported by all algorithms",
                                    code="PX107",
                                )
                        except ValueError:
                            self._add_issue(
                                LintIssue.SEVERITY_ERROR,
                                f"Invalid weight value: '{parts[2]}' (not a number)",
                                line_number=line_num,
                                suggestion="Weights must be numeric values",
                                code="PX107",
                            )

                    # Check for duplicates
                    edge_key = (src, dst)
                    if edge_key in seen_edges:
                        self._add_issue(
                            LintIssue.SEVERITY_WARNING,
                            f"Duplicate edge: {src} -> {dst}",
                            line_number=line_num,
                            suggestion="Remove duplicate edges or use weights",
                            code="PX205",
                        )
                    seen_edges.add(edge_key)

        except Exception as e:
            self._add_issue(
                LintIssue.SEVERITY_ERROR,
                f"Failed to parse edgelist file: {str(e)}",
                code="PX105",
            )

    def _lint_multiedgelist(self) -> None:
        """Lint a multiedgelist format file (node1 layer1 node2 layer2 [weight])."""
        seen_edges: Set[Tuple[str, str, str, str]] = set()
        line_num = 0

        try:
            with open(self.file_path) as f:
                for line in f:
                    line_num += 1
                    line = line.strip()

                    # Skip empty lines and comments
                    if not line or line.startswith("#"):
                        continue

                    parts = line.split()

                    if len(parts) < 4:
                        self._add_issue(
                            LintIssue.SEVERITY_ERROR,
                            f"Invalid multiedgelist format: expected at least 4 columns, got {len(parts)}",
                            line_number=line_num,
                            suggestion="Multiedgelist format: node1 layer1 node2 layer2 [weight]",
                            code="PX103",
                        )
                        continue

                    src, src_layer, dst, dst_layer = parts[0], parts[1], parts[2], parts[3]

                    # Check for empty values
                    if not src or not dst:
                        self._add_issue(
                            LintIssue.SEVERITY_ERROR,
                            "Empty node ID",
                            line_number=line_num,
                            code="PX107",
                        )

                    if not src_layer or not dst_layer:
                        self._add_issue(
                            LintIssue.SEVERITY_ERROR,
                            "Empty layer ID",
                            line_number=line_num,
                            suggestion="Each edge must specify source and destination layers",
                            code="PX107",
                        )

                    # Check for self-loops
                    if src == dst and src_layer == dst_layer:
                        self._add_issue(
                            LintIssue.SEVERITY_WARNING,
                            f"Self-loop detected: ({src}, {src_layer}) -> ({src}, {src_layer})",
                            line_number=line_num,
                            suggestion="Self-loops may cause issues with some algorithms",
                            code="PX206",
                        )

                    # Check weight if present
                    if len(parts) >= 5:
                        try:
                            w = float(parts[4])
                            if w < 0:
                                self._add_issue(
                                    LintIssue.SEVERITY_WARNING,
                                    f"Negative weight: {w}",
                                    line_number=line_num,
                                    suggestion="Negative weights may not be supported by all algorithms",
                                    code="PX107",
                                )
                        except ValueError:
                            self._add_issue(
                                LintIssue.SEVERITY_ERROR,
                                f"Invalid weight value: '{parts[4]}' (not a number)",
                                line_number=line_num,
                                suggestion="Weights must be numeric values",
                                code="PX107",
                            )

                    # Check for duplicates
                    edge_key = (src, src_layer, dst, dst_layer)
                    if edge_key in seen_edges:
                        self._add_issue(
                            LintIssue.SEVERITY_WARNING,
                            f"Duplicate edge: ({src}, {src_layer}) -> ({dst}, {dst_layer})",
                            line_number=line_num,
                            suggestion="Remove duplicate edges or use weights to combine them",
                            code="PX205",
                        )
                    seen_edges.add(edge_key)

        except Exception as e:
            self._add_issue(
                LintIssue.SEVERITY_ERROR,
                f"Failed to parse multiedgelist file: {str(e)}",
                code="PX105",
            )

    def has_errors(self) -> bool:
        """Check if any errors were found."""
        return any(issue.severity == LintIssue.SEVERITY_ERROR for issue in self.issues)

    def has_warnings(self) -> bool:
        """Check if any warnings were found."""
        return any(issue.severity == LintIssue.SEVERITY_WARNING for issue in self.issues)

    def print_summary(self) -> None:
        """Print a summary of linting results."""
        errors = sum(1 for issue in self.issues if issue.severity == LintIssue.SEVERITY_ERROR)
        warnings = sum(1 for issue in self.issues if issue.severity == LintIssue.SEVERITY_WARNING)
        infos = sum(1 for issue in self.issues if issue.severity == LintIssue.SEVERITY_INFO)

        if not self.issues:
            logger.info(f"✓ No issues found in {self.file_path}")
        else:
            logger.info(f"\nLinting results for {self.file_path}:")
            logger.info(f"  Errors: {errors}")
            logger.info(f"  Warnings: {warnings}")
            logger.info(f"  Info: {infos}")
