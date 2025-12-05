"""Tests for the file linter module."""

import tempfile
from pathlib import Path

import pytest

from py3plex.linter import GraphFileLinter, LintIssue


class TestLintIssue:
    """Test LintIssue class."""

    def test_lint_issue_str_without_line_number(self):
        """Test string representation without line number."""
        issue = LintIssue(LintIssue.SEVERITY_ERROR, "Test error")
        result = str(issue)
        # Should contain error severity in Rust-style format
        assert "error" in result.lower()
        assert "Test error" in result

    def test_lint_issue_str_with_line_number(self):
        """Test string representation with line number."""
        issue = LintIssue(LintIssue.SEVERITY_WARNING, "Test warning", line_number=42)
        result = str(issue)
        # Should contain warning severity in Rust-style format
        assert "warning" in result.lower()
        assert "Test warning" in result

    def test_lint_issue_str_with_suggestion(self):
        """Test string representation with suggestion."""
        issue = LintIssue(
            LintIssue.SEVERITY_ERROR,
            "Test error",
            suggestion="Try this fix",
        )
        result = str(issue)
        # Suggestions now appear as "help:" in Rust-style format
        assert "help:" in result.lower() or "suggestion" in result.lower()
        assert "Try this fix" in result


class TestGraphFileLinter:
    """Test GraphFileLinter class."""

    def test_lint_nonexistent_file(self):
        """Test linting a file that doesn't exist."""
        linter = GraphFileLinter("/nonexistent/file.csv")
        issues = linter.lint()

        assert len(issues) == 1
        assert issues[0].severity == LintIssue.SEVERITY_ERROR
        assert "not found" in issues[0].message.lower()

    def test_lint_valid_edgelist(self):
        """Test linting a valid edgelist file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".edgelist", delete=False) as f:
            f.write("A B\n")
            f.write("B C\n")
            f.write("C D\n")
            temp_file = f.name

        try:
            linter = GraphFileLinter(temp_file)
            issues = linter.lint()
            assert len(issues) == 0
        finally:
            Path(temp_file).unlink()

    def test_lint_edgelist_with_self_loop(self):
        """Test linting edgelist with self-loop."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".edgelist", delete=False) as f:
            f.write("A B\n")
            f.write("B B\n")  # Self-loop
            f.write("C D\n")
            temp_file = f.name

        try:
            linter = GraphFileLinter(temp_file)
            issues = linter.lint()

            warnings = [i for i in issues if i.severity == LintIssue.SEVERITY_WARNING]
            assert len(warnings) == 1
            assert "self-loop" in warnings[0].message.lower()
            assert warnings[0].line_number == 2
        finally:
            Path(temp_file).unlink()

    def test_lint_edgelist_with_duplicate(self):
        """Test linting edgelist with duplicate edge."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".edgelist", delete=False) as f:
            f.write("A B\n")
            f.write("B C\n")
            f.write("A B\n")  # Duplicate
            temp_file = f.name

        try:
            linter = GraphFileLinter(temp_file)
            issues = linter.lint()

            warnings = [i for i in issues if i.severity == LintIssue.SEVERITY_WARNING]
            assert len(warnings) == 1
            assert "duplicate" in warnings[0].message.lower()
            assert warnings[0].line_number == 3
        finally:
            Path(temp_file).unlink()

    def test_lint_edgelist_with_invalid_weight(self):
        """Test linting edgelist with invalid weight."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".edgelist", delete=False) as f:
            f.write("A B 1.0\n")
            f.write("B C invalid\n")  # Invalid weight
            f.write("C D 2.0\n")
            temp_file = f.name

        try:
            linter = GraphFileLinter(temp_file)
            issues = linter.lint()

            errors = [i for i in issues if i.severity == LintIssue.SEVERITY_ERROR]
            assert len(errors) == 1
            assert "invalid weight" in errors[0].message.lower()
            assert errors[0].line_number == 2
        finally:
            Path(temp_file).unlink()

    def test_lint_edgelist_with_negative_weight(self):
        """Test linting edgelist with negative weight."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".edgelist", delete=False) as f:
            f.write("A B 1.0\n")
            f.write("B C -2.0\n")  # Negative weight
            f.write("C D 3.0\n")
            temp_file = f.name

        try:
            linter = GraphFileLinter(temp_file)
            issues = linter.lint()

            warnings = [i for i in issues if i.severity == LintIssue.SEVERITY_WARNING]
            assert len(warnings) == 1
            assert "negative weight" in warnings[0].message.lower()
            assert warnings[0].line_number == 2
        finally:
            Path(temp_file).unlink()

    def test_lint_csv_missing_columns(self):
        """Test linting CSV with missing required columns."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("col1,col2\n")
            f.write("A,B\n")
            temp_file = f.name

        try:
            linter = GraphFileLinter(temp_file)
            issues = linter.lint()

            errors = [i for i in issues if i.severity == LintIssue.SEVERITY_ERROR]
            # Should have errors for missing src and dst columns
            assert len(errors) >= 2
            assert any("source" in e.message.lower() for e in errors)
            assert any("destination" in e.message.lower() for e in errors)
        finally:
            Path(temp_file).unlink()

    def test_lint_csv_with_valid_columns(self):
        """Test linting CSV with valid columns."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("src,dst\n")
            f.write("A,B\n")
            f.write("B,C\n")
            temp_file = f.name

        try:
            linter = GraphFileLinter(temp_file)
            issues = linter.lint()

            # Should only have INFO about no layer columns
            errors = [i for i in issues if i.severity == LintIssue.SEVERITY_ERROR]
            assert len(errors) == 0
        finally:
            Path(temp_file).unlink()

    def test_lint_csv_with_empty_values(self):
        """Test linting CSV with empty node values."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("src,dst\n")
            f.write("A,B\n")
            f.write("C,\n")  # Empty destination
            f.write(",D\n")  # Empty source
            temp_file = f.name

        try:
            linter = GraphFileLinter(temp_file)
            issues = linter.lint()

            errors = [i for i in issues if i.severity == LintIssue.SEVERITY_ERROR]
            # Should have 2 errors for empty nodes
            empty_errors = [e for e in errors if "empty" in e.message.lower()]
            assert len(empty_errors) == 2
        finally:
            Path(temp_file).unlink()

    def test_lint_multiedgelist_valid(self):
        """Test linting valid multiedgelist file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("A layer1 B layer1 1.0\n")
            f.write("B layer1 C layer1 1.0\n")
            f.write("A layer2 C layer2 1.0\n")
            temp_file = f.name

        try:
            linter = GraphFileLinter(temp_file)
            issues = linter.lint()
            assert len(issues) == 0
        finally:
            Path(temp_file).unlink()

    def test_lint_multiedgelist_with_self_loop(self):
        """Test linting multiedgelist with self-loop in same layer."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("A layer1 B layer1 1.0\n")
            f.write("B layer1 B layer1 1.0\n")  # Self-loop
            temp_file = f.name

        try:
            linter = GraphFileLinter(temp_file)
            issues = linter.lint()

            warnings = [i for i in issues if i.severity == LintIssue.SEVERITY_WARNING]
            assert len(warnings) == 1
            assert "self-loop" in warnings[0].message.lower()
        finally:
            Path(temp_file).unlink()

    def test_lint_multiedgelist_missing_columns(self):
        """Test linting multiedgelist with missing columns."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            # Write a line that's clearly multiedgelist format (4 or 5 columns)
            f.write("A layer1 B layer1 1.0\n")  # Valid line first
            f.write("A layer1 B\n")  # Only 3 columns, need 4 or 5
            temp_file = f.name

        try:
            linter = GraphFileLinter(temp_file)
            issues = linter.lint()

            errors = [i for i in issues if i.severity == LintIssue.SEVERITY_ERROR]
            assert len(errors) >= 1
            # Should complain about invalid format for line 2
            format_errors = [e for e in errors if "4 columns" in e.message or "invalid" in e.message.lower()]
            assert len(format_errors) >= 1
        finally:
            Path(temp_file).unlink()

    def test_has_errors(self):
        """Test has_errors method."""
        linter = GraphFileLinter("/nonexistent/file.csv")
        linter.issues = [
            LintIssue(LintIssue.SEVERITY_ERROR, "Error 1"),
            LintIssue(LintIssue.SEVERITY_WARNING, "Warning 1"),
        ]
        assert linter.has_errors() is True

        linter.issues = [
            LintIssue(LintIssue.SEVERITY_WARNING, "Warning 1"),
            LintIssue(LintIssue.SEVERITY_INFO, "Info 1"),
        ]
        assert linter.has_errors() is False

    def test_has_warnings(self):
        """Test has_warnings method."""
        linter = GraphFileLinter("/nonexistent/file.csv")
        linter.issues = [
            LintIssue(LintIssue.SEVERITY_WARNING, "Warning 1"),
            LintIssue(LintIssue.SEVERITY_INFO, "Info 1"),
        ]
        assert linter.has_warnings() is True

        linter.issues = [
            LintIssue(LintIssue.SEVERITY_ERROR, "Error 1"),
            LintIssue(LintIssue.SEVERITY_INFO, "Info 1"),
        ]
        assert linter.has_warnings() is False

    def test_format_detection_csv(self):
        """Test format detection for CSV files."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("src,dst,weight\n")
            f.write("A,B,1.0\n")
            temp_file = f.name

        try:
            linter = GraphFileLinter(temp_file)
            detected_format = linter._detect_format()
            assert detected_format == "csv"
        finally:
            Path(temp_file).unlink()

    def test_format_detection_edgelist(self):
        """Test format detection for edgelist files."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("A B\n")
            f.write("B C\n")
            temp_file = f.name

        try:
            linter = GraphFileLinter(temp_file)
            detected_format = linter._detect_format()
            assert detected_format == "edgelist"
        finally:
            Path(temp_file).unlink()

    def test_format_detection_multiedgelist(self):
        """Test format detection for multiedgelist files."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("A layer1 B layer1\n")
            f.write("B layer1 C layer1\n")
            temp_file = f.name

        try:
            linter = GraphFileLinter(temp_file)
            detected_format = linter._detect_format()
            assert detected_format == "multiedgelist"
        finally:
            Path(temp_file).unlink()

    def test_lint_csv_multilayer_missing_dst_layer(self):
        """Test CSV with source layer but missing destination layer."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("src,dst,src_layer\n")
            f.write("A,B,layer1\n")
            temp_file = f.name

        try:
            linter = GraphFileLinter(temp_file)
            issues = linter.lint()

            warnings = [i for i in issues if i.severity == LintIssue.SEVERITY_WARNING]
            # Should warn about missing destination layer
            assert any("destination layer" in w.message.lower() for w in warnings)
        finally:
            Path(temp_file).unlink()

    def test_empty_file(self):
        """Test linting an empty file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            # Write nothing
            temp_file = f.name

        try:
            linter = GraphFileLinter(temp_file)
            issues = linter.lint()
            # Empty file should not crash, might have no issues or a warning
            assert isinstance(issues, list)
        finally:
            Path(temp_file).unlink()

    def test_comments_in_edgelist(self):
        """Test that comments are properly skipped in edgelist."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".edgelist", delete=False) as f:
            f.write("#Comment\n")
            f.write("A B\n")
            f.write("#AnotherComment\n")
            f.write("B C\n")
            temp_file = f.name

        try:
            linter = GraphFileLinter(temp_file)
            issues = linter.lint()
            # Comments should be skipped, no issues expected
            assert len(issues) == 0
        finally:
            Path(temp_file).unlink()
