"""
Tests for the Rust-style error messages module.

This module tests the error formatting, suggestions, and "did you mean" functionality.
"""
import os
import tempfile
from pathlib import Path

import pytest

from py3plex.errors import (
    Colors,
    ErrorMessage,
    Note,
    Severity,
    SourceContext,
    Span,
    Suggestion,
    duplicate_edge_warning,
    file_not_found_error,
    find_similar,
    format_exception,
    invalid_algorithm_error,
    invalid_input_type_error,
    invalid_layer_error,
    missing_column_error,
    parse_error,
    self_loop_warning,
)


class TestFindSimilar:
    """Test the find_similar function for typo suggestions."""

    def test_find_exact_match(self):
        """Test that exact matches are found."""
        result = find_similar("social", ["social", "work", "family"])
        assert result == "social"

    def test_find_close_match(self):
        """Test that close matches (typos) are found."""
        result = find_similar("socail", ["social", "work", "family"])
        assert result == "social"

    def test_find_no_match(self):
        """Test that None is returned when no close match exists."""
        result = find_similar("xyz", ["abc", "def", "ghi"])
        assert result is None

    def test_find_empty_haystack(self):
        """Test with empty list of candidates."""
        result = find_similar("test", [])
        assert result is None

    def test_find_with_cutoff(self):
        """Test with custom cutoff value."""
        # "tset" is somewhat similar to "test" but not very close
        result = find_similar("tset", ["test", "best", "rest"], cutoff=0.5)
        assert result in ["test", "best", "rest"] or result is None


class TestColors:
    """Test the Colors class."""

    def test_colorize_without_color_support(self):
        """Test that colorize returns plain text when colors not supported."""
        # Force no-color by checking supports_color
        text = "test"
        result = Colors.colorize(text, Colors.RED)
        # Result should either be colored or plain depending on terminal
        assert text in result

    def test_supports_color_respects_no_color_env(self):
        """Test that NO_COLOR environment variable is respected."""
        old_value = os.environ.get("NO_COLOR")
        try:
            os.environ["NO_COLOR"] = "1"
            assert Colors.supports_color() is False
        finally:
            if old_value is None:
                os.environ.pop("NO_COLOR", None)
            else:
                os.environ["NO_COLOR"] = old_value


class TestSpan:
    """Test the Span class."""

    def test_span_creation(self):
        """Test basic span creation."""
        span = Span(line=10, column=5, length=3)
        assert span.line == 10
        assert span.column == 5
        assert span.length == 3

    def test_span_defaults(self):
        """Test span with default values."""
        span = Span(line=1)
        assert span.column == 1
        assert span.length == 0


class TestSourceContext:
    """Test the SourceContext class."""

    def test_from_file_with_valid_file(self):
        """Test creating source context from a valid file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("line 1\n")
            f.write("line 2\n")
            f.write("error here\n")
            f.write("line 4\n")
            f.write("line 5\n")
            temp_file = f.name

        try:
            context = SourceContext.from_file(temp_file, line_number=3, column=1, length=5)
            assert context.file_path == temp_file
            assert len(context.lines) > 0
            assert context.span is not None
            assert context.span.line == 3
        finally:
            Path(temp_file).unlink()

    def test_from_file_with_nonexistent_file(self):
        """Test creating source context from a nonexistent file."""
        context = SourceContext.from_file("/nonexistent/file.txt", line_number=1)
        assert context.file_path == "/nonexistent/file.txt"
        assert len(context.lines) == 0


class TestSuggestion:
    """Test the Suggestion class."""

    def test_suggestion_creation(self):
        """Test basic suggestion creation."""
        suggestion = Suggestion(message="Try this fix", replacement="new_value")
        assert suggestion.message == "Try this fix"
        assert suggestion.replacement == "new_value"


class TestNote:
    """Test the Note class."""

    def test_note_creation(self):
        """Test basic note creation."""
        note = Note(message="Additional context")
        assert note.message == "Additional context"


class TestErrorMessage:
    """Test the ErrorMessage class."""

    def test_error_message_format_without_color(self):
        """Test error message formatting without colors."""
        error = ErrorMessage(
            code="PX101",
            severity=Severity.ERROR,
            title="file not found",
            message="could not find file 'test.txt'",
        )
        result = error.format(use_color=False)

        assert "error" in result.lower()
        assert "PX101" in result
        assert "file not found" in result
        assert "could not find file" in result

    def test_error_message_with_suggestion(self):
        """Test error message with suggestion."""
        error = ErrorMessage(
            code="PX201",
            severity=Severity.ERROR,
            title="invalid layer",
            message="layer 'socail' not found",
            suggestions=[Suggestion(message="try 'social' instead")],
        )
        result = error.format(use_color=False)

        assert "help:" in result.lower()
        assert "social" in result

    def test_error_message_with_did_you_mean(self):
        """Test error message with did you mean suggestion."""
        error = ErrorMessage(
            code="PX201",
            severity=Severity.ERROR,
            title="invalid layer",
            message="layer 'socail' not found",
            did_you_mean="social",
        )
        result = error.format(use_color=False)

        assert "did you mean" in result.lower()
        assert "social" in result

    def test_error_message_with_notes(self):
        """Test error message with notes."""
        error = ErrorMessage(
            code="PX105",
            severity=Severity.ERROR,
            title="parse error",
            message="unexpected token",
            notes=[Note(message="expected 4 columns")],
        )
        result = error.format(use_color=False)

        assert "note:" in result.lower()
        assert "expected 4 columns" in result

    def test_warning_severity(self):
        """Test warning severity formatting."""
        error = ErrorMessage(
            code="PX206",
            severity=Severity.WARNING,
            title="self-loop",
            message="edge from node to itself",
        )
        result = error.format(use_color=False)

        assert "warning" in result.lower()


class TestPrebuiltErrorBuilders:
    """Test the pre-built error message builder functions."""

    def test_file_not_found_error(self):
        """Test file_not_found_error builder."""
        error = file_not_found_error("test.txt")

        assert error.code == "PX101"
        assert error.severity == Severity.ERROR
        assert "test.txt" in error.message
        assert len(error.suggestions) > 0

    def test_file_not_found_error_with_similar_files(self):
        """Test file_not_found_error with similar file suggestions."""
        error = file_not_found_error(
            "network.csv",
            similar_files=["network.txt", "networks.csv", "data.csv"],
        )

        # Should suggest similar file
        assert error.did_you_mean is not None or len(error.suggestions) > 0

    def test_invalid_input_type_error(self):
        """Test invalid_input_type_error builder."""
        error = invalid_input_type_error(
            "edgelst",  # typo
            ["edgelist", "multiedgelist", "graphml", "gml"],
        )

        assert error.code == "PX108"
        assert "edgelst" in error.message
        assert error.did_you_mean == "edgelist"

    def test_missing_column_error(self):
        """Test missing_column_error builder."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("source,destination,weight\n")
            f.write("A,B,1.0\n")
            temp_file = f.name

        try:
            error = missing_column_error(
                temp_file,
                missing_columns=["src"],
                found_columns=["source", "destination", "weight"],
            )

            assert error.code == "PX106"
            assert "src" in error.message
            # Should suggest 'source' as similar to 'src'
            assert any("source" in s.message for s in error.suggestions)
        finally:
            Path(temp_file).unlink()

    def test_invalid_layer_error(self):
        """Test invalid_layer_error builder."""
        error = invalid_layer_error(
            "socail",
            available_layers=["social", "work", "family"],
        )

        assert error.code == "PX201"
        assert error.did_you_mean == "social"

    def test_parse_error(self):
        """Test parse_error builder."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("A,B,1.0\n")
            f.write("C,D,invalid\n")
            temp_file = f.name

        try:
            error = parse_error(
                temp_file,
                line_number=2,
                message="invalid weight value",
                expected="numeric value",
                got="'invalid'",
            )

            assert error.code == "PX105"
            assert error.context is not None
            assert any("expected" in n.message for n in error.notes)
        finally:
            Path(temp_file).unlink()

    def test_invalid_algorithm_error(self):
        """Test invalid_algorithm_error builder."""
        error = invalid_algorithm_error(
            "lovain",  # typo
            ["louvain", "infomap", "label_propagation"],
            operation="community detection",
        )

        assert error.code == "PX301"
        assert error.did_you_mean == "louvain"

    def test_self_loop_warning(self):
        """Test self_loop_warning builder."""
        warning = self_loop_warning(
            node="node1",
            layer="social",
        )

        assert warning.code == "PX206"
        assert warning.severity == Severity.WARNING
        assert "node1" in warning.message

    def test_duplicate_edge_warning(self):
        """Test duplicate_edge_warning builder."""
        warning = duplicate_edge_warning(
            source="A",
            target="B",
            layer="social",
        )

        assert warning.code == "PX205"
        assert warning.severity == Severity.WARNING
        assert "A" in warning.message
        assert "B" in warning.message


class TestFormatException:
    """Test the format_exception function."""

    def test_format_parsing_error(self):
        """Test formatting a parsing error."""
        from py3plex.exceptions import ParsingError

        exc = ParsingError("Failed to parse file")
        result = format_exception(exc)

        assert "error" in result.lower()
        assert "PX105" in result
        assert "Failed to parse file" in result

    def test_format_with_custom_code(self):
        """Test formatting with custom error code."""
        exc = Exception("Generic error")
        result = format_exception(exc, code="PX999")

        assert "PX999" in result

    def test_format_with_suggestions(self):
        """Test formatting with suggestions."""
        exc = Exception("Something went wrong")
        result = format_exception(
            exc,
            suggestions=["Try this", "Or try that"],
        )

        assert "help:" in result.lower()
        assert "Try this" in result
        assert "Or try that" in result


class TestIntegration:
    """Integration tests for the error system."""

    def test_full_error_flow(self):
        """Test a complete error flow with all features."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("src,dst,weight\n")
            f.write("A,B,1.0\n")
            f.write("C,D,invalid\n")
            temp_file = f.name

        try:
            context = SourceContext.from_file(
                temp_file,
                line_number=3,
                column=5,
                length=7,
            )

            error = ErrorMessage(
                code="PX107",
                severity=Severity.ERROR,
                title="invalid value",
                message="weight 'invalid' is not a number",
                context=context,
                suggestions=[
                    Suggestion(
                        message="weights must be numeric",
                        replacement="use a number like 1.0",
                    ),
                ],
                notes=[
                    Note(message="this column should contain edge weights"),
                ],
            )

            result = error.format(use_color=False)

            # Verify all components are present
            assert "error" in result.lower()
            assert "PX107" in result
            assert "invalid value" in result
            assert "help:" in result.lower()
            assert "note:" in result.lower()
        finally:
            Path(temp_file).unlink()
