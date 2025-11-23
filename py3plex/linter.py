"""
File linter for py3plex graph data files.

Validates data format, detects potential issues, and suggests fixes for
graph data files (CSV, edgelist, multiedgelist formats).
"""

import csv
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from py3plex.logging_config import get_logger

logger = get_logger(__name__)


class LintIssue:
    """Represents a linting issue found in a graph data file."""

    SEVERITY_ERROR = "ERROR"
    SEVERITY_WARNING = "WARNING"
    SEVERITY_INFO = "INFO"

    def __init__(
        self,
        severity: str,
        message: str,
        line_number: Optional[int] = None,
        suggestion: Optional[str] = None,
    ):
        """
        Initialize a lint issue.

        Args:
            severity: Issue severity (ERROR, WARNING, INFO)
            message: Description of the issue
            line_number: Optional line number where issue was found
            suggestion: Optional suggestion for fixing the issue
        """
        self.severity = severity
        self.message = message
        self.line_number = line_number
        self.suggestion = suggestion

    def __str__(self) -> str:
        """String representation of the lint issue."""
        result = f"[{self.severity}]"
        if self.line_number is not None:
            result += f" Line {self.line_number}:"
        result += f" {self.message}"
        if self.suggestion:
            result += f"\n  → Suggestion: {self.suggestion}"
        return result


class GraphFileLinter:
    """Linter for graph data files."""

    def __init__(self, file_path: str):
        """
        Initialize linter for a graph data file.

        Args:
            file_path: Path to the file to lint
        """
        self.file_path = Path(file_path)
        self.issues: List[LintIssue] = []

    def lint(self) -> List[LintIssue]:
        """
        Run all linting checks on the file.

        Returns:
            List of issues found
        """
        self.issues = []

        # Check file exists
        if not self.file_path.exists():
            self.issues.append(
                LintIssue(
                    LintIssue.SEVERITY_ERROR,
                    f"File not found: {self.file_path}",
                    suggestion="Check the file path is correct",
                )
            )
            return self.issues

        # Check file is readable
        try:
            with open(self.file_path, "r") as f:
                pass
        except PermissionError:
            self.issues.append(
                LintIssue(
                    LintIssue.SEVERITY_ERROR,
                    f"File is not readable: {self.file_path}",
                    suggestion="Check file permissions",
                )
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
            self.issues.append(
                LintIssue(
                    LintIssue.SEVERITY_WARNING,
                    f"Unknown file format, treating as edgelist",
                )
            )
            self._lint_edgelist()

        return self.issues

    def _detect_format(self) -> str:
        """
        Detect the format of the graph data file.

        Returns:
            Format string: 'csv', 'edgelist', or 'multiedgelist'
        """
        # Check file extension
        suffix = self.file_path.suffix.lower()

        # Try to detect by reading first few lines
        try:
            with open(self.file_path, "r") as f:
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
            with open(self.file_path, "r", newline="") as f:
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
                    self.issues.append(
                        LintIssue(
                            LintIssue.SEVERITY_ERROR,
                            "CSV file has no header row",
                            suggestion="Add a header row with column names like: src,dst,src_layer,dst_layer",
                        )
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
                    self.issues.append(
                        LintIssue(
                            LintIssue.SEVERITY_ERROR,
                            f"Missing source node column. Found columns: {', '.join(fieldnames)}",
                            suggestion=f"Add a column named one of: {', '.join(src_cols)}",
                        )
                    )

                if not has_dst:
                    self.issues.append(
                        LintIssue(
                            LintIssue.SEVERITY_ERROR,
                            f"Missing destination node column. Found columns: {', '.join(fieldnames)}",
                            suggestion=f"Add a column named one of: {', '.join(dst_cols)}",
                        )
                    )

                # Check for multilayer columns
                has_src_layer = any(col in fieldnames for col in src_layer_cols)
                has_dst_layer = any(col in fieldnames for col in dst_layer_cols)

                if not has_src_layer and not has_dst_layer:
                    self.issues.append(
                        LintIssue(
                            LintIssue.SEVERITY_INFO,
                            "No layer columns found - this appears to be a single-layer network",
                        )
                    )
                elif has_src_layer and not has_dst_layer:
                    self.issues.append(
                        LintIssue(
                            LintIssue.SEVERITY_WARNING,
                            "Source layer column found but destination layer column is missing",
                            suggestion=f"Add a column named one of: {', '.join(dst_layer_cols)}",
                        )
                    )
                elif has_dst_layer and not has_src_layer:
                    self.issues.append(
                        LintIssue(
                            LintIssue.SEVERITY_WARNING,
                            "Destination layer column found but source layer column is missing",
                            suggestion=f"Add a column named one of: {', '.join(src_layer_cols)}",
                        )
                    )

                # Validate data rows
                self._validate_csv_rows(reader, fieldnames)

        except Exception as e:
            self.issues.append(
                LintIssue(
                    LintIssue.SEVERITY_ERROR,
                    f"Failed to parse CSV file: {str(e)}",
                    suggestion="Check that the file is properly formatted CSV",
                )
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
                self.issues.append(
                    LintIssue(
                        LintIssue.SEVERITY_ERROR,
                        "Empty source node",
                        line_number=line_num,
                        suggestion="Provide a valid source node ID",
                    )
                )

            if not dst or not dst.strip():
                self.issues.append(
                    LintIssue(
                        LintIssue.SEVERITY_ERROR,
                        "Empty destination node",
                        line_number=line_num,
                        suggestion="Provide a valid destination node ID",
                    )
                )

            # Check for self-loops
            if src and dst and src.strip() == dst.strip():
                self.issues.append(
                    LintIssue(
                        LintIssue.SEVERITY_WARNING,
                        f"Self-loop detected: {src} -> {src}",
                        line_number=line_num,
                        suggestion="Self-loops may not be supported by all algorithms",
                    )
                )

            # Check weight column if present
            if "weight" in row:
                weight = row["weight"]
                if weight and weight.strip():
                    try:
                        w = float(weight)
                        if w < 0:
                            self.issues.append(
                                LintIssue(
                                    LintIssue.SEVERITY_WARNING,
                                    f"Negative weight: {w}",
                                    line_number=line_num,
                                    suggestion="Negative weights may not be supported by all algorithms",
                                )
                            )
                    except ValueError:
                        self.issues.append(
                            LintIssue(
                                LintIssue.SEVERITY_ERROR,
                                f"Invalid weight value: '{weight}' (not a number)",
                                line_number=line_num,
                                suggestion="Weights must be numeric values",
                            )
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
                    self.issues.append(
                        LintIssue(
                            LintIssue.SEVERITY_WARNING,
                            f"Duplicate edge: {src} -> {dst} (layers: {src_layer}, {dst_layer})",
                            line_number=line_num,
                            suggestion="Remove duplicate edges or consolidate with edge weights",
                        )
                    )
                seen_edges.add(edge_key)

            line_num += 1

    def _lint_edgelist(self) -> None:
        """Lint a simple edgelist format file (node1 node2 [weight])."""
        seen_edges: Set[Tuple[str, str]] = set()
        line_num = 0

        try:
            with open(self.file_path, "r") as f:
                for line in f:
                    line_num += 1
                    line = line.strip()

                    # Skip empty lines and comments
                    if not line or line.startswith("#"):
                        continue

                    parts = line.split()

                    if len(parts) < 2:
                        self.issues.append(
                            LintIssue(
                                LintIssue.SEVERITY_ERROR,
                                f"Invalid edgelist format: expected at least 2 columns, got {len(parts)}",
                                line_number=line_num,
                                suggestion="Edgelist format: node1 node2 [weight]",
                            )
                        )
                        continue

                    src, dst = parts[0], parts[1]

                    # Check for empty nodes
                    if not src or not dst:
                        self.issues.append(
                            LintIssue(
                                LintIssue.SEVERITY_ERROR,
                                "Empty node ID",
                                line_number=line_num,
                            )
                        )

                    # Check for self-loops
                    if src == dst:
                        self.issues.append(
                            LintIssue(
                                LintIssue.SEVERITY_WARNING,
                                f"Self-loop detected: {src} -> {src}",
                                line_number=line_num,
                            )
                        )

                    # Check weight if present
                    if len(parts) >= 3:
                        try:
                            w = float(parts[2])
                            if w < 0:
                                self.issues.append(
                                    LintIssue(
                                        LintIssue.SEVERITY_WARNING,
                                        f"Negative weight: {w}",
                                        line_number=line_num,
                                    )
                                )
                        except ValueError:
                            self.issues.append(
                                LintIssue(
                                    LintIssue.SEVERITY_ERROR,
                                    f"Invalid weight value: '{parts[2]}' (not a number)",
                                    line_number=line_num,
                                )
                            )

                    # Check for duplicates
                    edge_key = (src, dst)
                    if edge_key in seen_edges:
                        self.issues.append(
                            LintIssue(
                                LintIssue.SEVERITY_WARNING,
                                f"Duplicate edge: {src} -> {dst}",
                                line_number=line_num,
                            )
                        )
                    seen_edges.add(edge_key)

        except Exception as e:
            self.issues.append(
                LintIssue(
                    LintIssue.SEVERITY_ERROR,
                    f"Failed to parse edgelist file: {str(e)}",
                )
            )

    def _lint_multiedgelist(self) -> None:
        """Lint a multiedgelist format file (node1 layer1 node2 layer2 [weight])."""
        seen_edges: Set[Tuple[str, str, str, str]] = set()
        line_num = 0

        try:
            with open(self.file_path, "r") as f:
                for line in f:
                    line_num += 1
                    line = line.strip()

                    # Skip empty lines and comments
                    if not line or line.startswith("#"):
                        continue

                    parts = line.split()

                    if len(parts) < 4:
                        self.issues.append(
                            LintIssue(
                                LintIssue.SEVERITY_ERROR,
                                f"Invalid multiedgelist format: expected at least 4 columns, got {len(parts)}",
                                line_number=line_num,
                                suggestion="Multiedgelist format: node1 layer1 node2 layer2 [weight]",
                            )
                        )
                        continue

                    src, src_layer, dst, dst_layer = parts[0], parts[1], parts[2], parts[3]

                    # Check for empty values
                    if not src or not dst:
                        self.issues.append(
                            LintIssue(
                                LintIssue.SEVERITY_ERROR,
                                "Empty node ID",
                                line_number=line_num,
                            )
                        )

                    if not src_layer or not dst_layer:
                        self.issues.append(
                            LintIssue(
                                LintIssue.SEVERITY_ERROR,
                                "Empty layer ID",
                                line_number=line_num,
                            )
                        )

                    # Check for self-loops
                    if src == dst and src_layer == dst_layer:
                        self.issues.append(
                            LintIssue(
                                LintIssue.SEVERITY_WARNING,
                                f"Self-loop detected: ({src}, {src_layer}) -> ({src}, {src_layer})",
                                line_number=line_num,
                            )
                        )

                    # Check weight if present
                    if len(parts) >= 5:
                        try:
                            w = float(parts[4])
                            if w < 0:
                                self.issues.append(
                                    LintIssue(
                                        LintIssue.SEVERITY_WARNING,
                                        f"Negative weight: {w}",
                                        line_number=line_num,
                                    )
                                )
                        except ValueError:
                            self.issues.append(
                                LintIssue(
                                    LintIssue.SEVERITY_ERROR,
                                    f"Invalid weight value: '{parts[4]}' (not a number)",
                                    line_number=line_num,
                                )
                            )

                    # Check for duplicates
                    edge_key = (src, src_layer, dst, dst_layer)
                    if edge_key in seen_edges:
                        self.issues.append(
                            LintIssue(
                                LintIssue.SEVERITY_WARNING,
                                f"Duplicate edge: ({src}, {src_layer}) -> ({dst}, {dst_layer})",
                                line_number=line_num,
                            )
                        )
                    seen_edges.add(edge_key)

        except Exception as e:
            self.issues.append(
                LintIssue(
                    LintIssue.SEVERITY_ERROR,
                    f"Failed to parse multiedgelist file: {str(e)}",
                )
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
