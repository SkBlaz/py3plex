"""Tests for errors.py (Rust-style error messages) to improve coverage."""

import os
import sys
from dataclasses import is_dataclass

import pytest

from py3plex.errors import (
    ERROR_CODES,
    Colors,
    ErrorMessage,
    Note,
    Severity,
    Span,
    SourceContext,
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
    """Tests for find_similar()."""

    def test_exact_match(self):
        result = find_similar("edgelist", ["edgelist", "graphml", "json"])
        assert result == "edgelist"

    def test_close_match(self):
        result = find_similar("egelist", ["edgelist", "graphml", "json"])
        assert result == "edgelist"

    def test_no_match(self):
        result = find_similar("zzzzz", ["edgelist", "graphml", "json"])
        assert result is None

    def test_empty_haystack(self):
        result = find_similar("anything", [])
        assert result is None

    def test_cutoff_respected(self):
        # With high cutoff, even close matches are rejected
        result = find_similar("edgelist", ["edgelst"], cutoff=0.99)
        assert result is None

    def test_returns_single_best(self):
        result = find_similar("social", ["social", "social_layer", "work"])
        assert result == "social"


class TestSeverity:
    """Tests for the Severity enum."""

    def test_values_exist(self):
        assert Severity.ERROR.value == "error"
        assert Severity.WARNING.value == "warning"
        assert Severity.INFO.value == "info"
        assert Severity.HELP.value == "help"
        assert Severity.NOTE.value == "note"

    def test_five_levels(self):
        assert len(list(Severity)) == 5


class TestColors:
    """Tests for the Colors class."""

    def test_supports_color_returns_bool(self):
        result = Colors.supports_color()
        assert isinstance(result, bool)

    def test_no_color_env_disables_color(self, monkeypatch):
        monkeypatch.setenv("NO_COLOR", "1")
        assert Colors.supports_color() is False

    def test_colorize_without_tty_is_passthrough(self, monkeypatch):
        # In CI there's no TTY, so colorize should return the original text
        monkeypatch.setenv("NO_COLOR", "1")
        result = Colors.colorize("hello", Colors.RED)
        assert result == "hello"

    def test_ansi_codes_are_strings(self):
        assert isinstance(Colors.RED, str)
        assert isinstance(Colors.RESET, str)
        assert isinstance(Colors.BOLD, str)


class TestDataclasses:
    """Tests for Span, SourceContext, Suggestion, Note, ErrorMessage dataclasses."""

    def test_span_creation(self):
        s = Span(line=5, column=3, length=10)
        assert s.line == 5
        assert s.column == 3
        assert s.length == 10
        assert s.end_line is None

    def test_source_context_empty(self):
        ctx = SourceContext()
        assert ctx.file_path is None
        assert ctx.lines == []

    def test_source_context_from_nonexistent_file(self):
        ctx = SourceContext.from_file("/nonexistent/file.py", line_number=3)
        assert ctx.file_path == "/nonexistent/file.py"
        assert ctx.lines == []  # fallback on OSError

    def test_suggestion_creation(self):
        s = Suggestion(message="Try this fix", replacement="correct_code")
        assert s.message == "Try this fix"
        assert s.replacement == "correct_code"

    def test_note_creation(self):
        n = Note(message="This is a note")
        assert n.message == "This is a note"

    def test_error_message_is_dataclass(self):
        assert is_dataclass(ErrorMessage)

    def test_error_message_format_no_color(self):
        err = ErrorMessage(
            code="PX101",
            severity=Severity.ERROR,
            title="file not found",
            message="could not find file `test.csv`",
        )
        text = err.format(use_color=False)
        assert "PX101" in text
        assert "file not found" in text
        assert "error" in text

    def test_error_message_format_with_suggestions(self):
        err = ErrorMessage(
            code="PX001",
            severity=Severity.WARNING,
            title="bad arg",
            message="something is wrong",
            suggestions=[Suggestion(message="try this instead")],
        )
        text = err.format(use_color=False)
        assert "try this instead" in text

    def test_error_message_format_with_notes(self):
        err = ErrorMessage(
            code="PX001",
            severity=Severity.INFO,
            title="info",
            message="here is info",
            notes=[Note(message="additional context here")],
        )
        text = err.format(use_color=False)
        assert "additional context here" in text

    def test_error_message_format_did_you_mean(self):
        err = ErrorMessage(
            code="PX201",
            severity=Severity.ERROR,
            title="unknown layer",
            message="layer 'socail' not found",
            did_you_mean="social",
        )
        text = err.format(use_color=False)
        assert "social" in text

    def test_error_message_format_with_context(self):
        err = ErrorMessage(
            code="PX001",
            severity=Severity.ERROR,
            title="test",
            message="test error",
            context=SourceContext(
                file_path="test.py",
                lines=["line one", "line two", "line three"],
                span=Span(line=2, column=1, length=4),
            ),
        )
        text = err.format(use_color=False)
        assert "test.py" in text


class TestErrorFactoryFunctions:
    """Tests for factory functions that create ErrorMessage instances."""

    def test_file_not_found_error_basic(self):
        err = file_not_found_error("/path/to/missing.csv")
        assert isinstance(err, ErrorMessage)
        assert err.code == "PX101"
        assert err.severity == Severity.ERROR
        assert "missing.csv" in err.message

    def test_file_not_found_error_with_similar(self):
        err = file_not_found_error(
            "/data/netwrk.csv",
            similar_files=["/data/network.csv"],
        )
        assert err.did_you_mean == "/data/network.csv"

    def test_file_not_found_error_no_similar_match(self):
        err = file_not_found_error(
            "/data/xyzabc.csv",
            similar_files=["/data/network.csv"],
        )
        assert err.did_you_mean is None

    def test_invalid_input_type_error(self):
        err = invalid_input_type_error("edgelst", ["edgelist", "graphml", "json"])
        assert isinstance(err, ErrorMessage)
        assert err.severity == Severity.ERROR
        # Should suggest 'edgelist' as did you mean
        assert err.did_you_mean == "edgelist"

    def test_invalid_input_type_error_many_types(self):
        valid = [f"type{i}" for i in range(10)]
        err = invalid_input_type_error("xtype", valid)
        assert isinstance(err, ErrorMessage)
        # Should not crash with many types
        text = err.format(use_color=False)
        assert "valid input types" in text

    def test_missing_column_error(self):
        err = missing_column_error(
            "/fake/path.csv",
            missing_columns=["source_node"],
            found_columns=["source", "target", "layer"],
        )
        assert isinstance(err, ErrorMessage)
        assert "source_node" in err.message or "source" in err.format(use_color=False)

    def test_invalid_layer_error(self):
        err = invalid_layer_error("socail", available_layers=["social", "work", "family"])
        assert isinstance(err, ErrorMessage)
        assert err.code == "PX201"
        assert err.did_you_mean == "social"

    def test_invalid_layer_error_with_file_context(self):
        err = invalid_layer_error(
            "missing_layer",
            available_layers=["social", "work"],
            file_path="/some/file.csv",
            line_number=3,
        )
        assert isinstance(err, ErrorMessage)
        assert err.code == "PX201"

    def test_parse_error(self):
        err = parse_error("test.csv", line_number=5, message="unexpected token")
        assert isinstance(err, ErrorMessage)
        assert err.code == "PX105"

    def test_invalid_algorithm_error(self):
        err = invalid_algorithm_error("louvainx", valid_algorithms=["louvain", "leiden"])
        assert isinstance(err, ErrorMessage)
        assert err.severity == Severity.ERROR
        assert err.did_you_mean == "louvain"

    def test_self_loop_warning(self):
        err = self_loop_warning("node_A", "layer1")
        assert isinstance(err, ErrorMessage)
        assert err.severity == Severity.WARNING
        assert err.code == "PX206"

    def test_duplicate_edge_warning(self):
        err = duplicate_edge_warning("A", "B", "social")
        assert isinstance(err, ErrorMessage)
        assert err.severity == Severity.WARNING

    def test_format_exception_generic(self):
        exc = ValueError("something went wrong")
        text = format_exception(exc)
        assert isinstance(text, str)
        assert "something went wrong" in text

    def test_format_exception_with_code(self):
        exc = RuntimeError("runtime problem")
        text = format_exception(exc, code="PX001")
        assert "PX001" in text

    def test_format_exception_with_suggestions(self):
        exc = ValueError("bad value")
        text = format_exception(exc, suggestions=["try a different value"])
        assert "try a different value" in text

    def test_format_exception_with_notes(self):
        exc = OSError("file issue")
        text = format_exception(exc, notes=["check file permissions"])
        assert "check file permissions" in text


class TestErrorCodeRegistry:
    """Tests for the ERROR_CODES registry."""

    def test_registry_non_empty(self):
        assert len(ERROR_CODES) > 0

    def test_all_codes_have_two_elements(self):
        for code, value in ERROR_CODES.items():
            assert isinstance(value, tuple) and len(value) == 2

    def test_known_codes_present(self):
        assert "PX001" in ERROR_CODES
        assert "PX101" in ERROR_CODES
        assert "PX201" in ERROR_CODES
        assert "PX301" in ERROR_CODES

    def test_codes_start_with_px(self):
        for code in ERROR_CODES:
            assert code.startswith("PX"), f"Bad code: {code}"
