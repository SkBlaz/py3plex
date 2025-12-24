"""
Extended tests for py3plex.dsl.errors module.

This module adds test coverage for DSL error types and helper functions.
"""

import pytest

from py3plex.dsl.errors import (
    DslError,
    DslSyntaxError,
    DslExecutionError,
    UnknownLayerError,
    UnknownAttributeError,
    UnknownMeasureError,
    _levenshtein_distance,
    _suggest_similar,
)


class TestLevenshteinDistance:
    """Test the Levenshtein distance calculation."""

    def test_identical_strings(self):
        """Test distance between identical strings is 0."""
        assert _levenshtein_distance("hello", "hello") == 0
        assert _levenshtein_distance("", "") == 0

    def test_single_character_difference(self):
        """Test distance for single character substitution."""
        assert _levenshtein_distance("hello", "hallo") == 1

    def test_insertion(self):
        """Test distance for character insertion."""
        assert _levenshtein_distance("hello", "helllo") == 1

    def test_deletion(self):
        """Test distance for character deletion."""
        assert _levenshtein_distance("hello", "hllo") == 1

    def test_multiple_changes(self):
        """Test distance for multiple changes."""
        distance = _levenshtein_distance("kitten", "sitting")
        assert distance == 3  # k->s, e->i, insert g

    def test_completely_different_strings(self):
        """Test distance for completely different strings."""
        distance = _levenshtein_distance("abc", "xyz")
        assert distance == 3

    def test_empty_string(self):
        """Test distance with empty string."""
        assert _levenshtein_distance("hello", "") == 5
        assert _levenshtein_distance("", "world") == 5

    def test_different_lengths(self):
        """Test distance with different length strings."""
        assert _levenshtein_distance("short", "longer string") > 5


class TestSuggestSimilar:
    """Test the _suggest_similar function."""

    def test_exact_match(self):
        """Test suggestion with exact match."""
        result = _suggest_similar("social", ["social", "work", "family"])
        assert result == "social"

    def test_close_typo(self):
        """Test suggestion with a typo."""
        result = _suggest_similar("socail", ["social", "work", "family"])
        assert result == "social"

    def test_no_close_match(self):
        """Test that None is returned when no match is close."""
        result = _suggest_similar("xyz", ["abc", "def", "ghi"])
        assert result is None

    def test_empty_known_names(self):
        """Test with empty list of known names."""
        result = _suggest_similar("test", [])
        assert result is None

    def test_max_distance_parameter(self):
        """Test that max_distance parameter is respected."""
        # "test" and "best" have distance 1
        result = _suggest_similar("test", ["best"], max_distance=1)
        assert result == "best"
        
        # But not if max_distance is 0
        result = _suggest_similar("test", ["best"], max_distance=0)
        assert result is None

    def test_case_insensitive(self):
        """Test that suggestions are case-insensitive."""
        result = _suggest_similar("SOCIAL", ["social", "work"])
        assert result == "social"

    def test_selects_best_match(self):
        """Test that the closest match is selected."""
        result = _suggest_similar("tset", ["test", "seat", "pest"])
        # "test" is closest with distance 2 (transposition)
        assert result == "test"


class TestDslError:
    """Test the base DslError exception."""

    def test_dsl_error_creation(self):
        """Test creating a DslError."""
        error = DslError("Test error message")
        assert isinstance(error, Exception)
        assert "Test error message" in str(error)

    def test_dsl_error_with_query(self):
        """Test DslError with query context."""
        error = DslError("Test error", query="SELECT nodes WHERE layer='test'")
        assert "Test error" in str(error)

    def test_dsl_error_with_column(self):
        """Test DslError with column information."""
        error = DslError("Test error", column=10, line=1)
        assert "Test error" in str(error)


class TestUnknownLayerError:
    """Test the UnknownLayerError exception."""

    def test_unknown_layer_error_basic(self):
        """Test basic UnknownLayerError."""
        error = UnknownLayerError("undefined_layer")
        assert isinstance(error, DslError)
        assert "undefined_layer" in str(error)

    def test_unknown_layer_error_with_suggestions(self):
        """Test UnknownLayerError with layer suggestions."""
        known = ["social", "work", "family"]
        error = UnknownLayerError("socail", known_layers=known)
        error_msg = str(error)
        assert "socail" in error_msg
        # Should suggest "social" as it's similar
        assert "social" in error_msg or "Did you mean" in error_msg.lower()

    def test_unknown_layer_error_no_suggestions(self):
        """Test UnknownLayerError when no similar layers exist."""
        known = ["layer1", "layer2"]
        error = UnknownLayerError("xyz", known_layers=known)
        error_msg = str(error)
        assert "xyz" in error_msg


class TestUnknownMeasureError:
    """Test the UnknownMeasureError exception."""

    def test_unknown_measure_error_basic(self):
        """Test basic UnknownMeasureError."""
        error = UnknownMeasureError("invalid_measure")
        assert isinstance(error, DslError)
        assert "invalid_measure" in str(error)

    def test_unknown_measure_error_with_suggestions(self):
        """Test UnknownMeasureError with measure suggestions."""
        known = ["degree", "betweenness", "closeness"]
        error = UnknownMeasureError("betweeness", known_measures=known)
        error_msg = str(error)
        assert "betweeness" in error_msg
        # Should suggest "betweenness" 
        assert "betweenness" in error_msg or "Did you mean" in error_msg.lower()


class TestUnknownAttributeError:
    """Test the UnknownAttributeError exception."""

    def test_unknown_attribute_error_basic(self):
        """Test basic UnknownAttributeError."""
        error = UnknownAttributeError("invalid_attr")
        assert isinstance(error, DslError)
        assert "invalid_attr" in str(error)

    def test_unknown_attribute_error_with_suggestions(self):
        """Test UnknownAttributeError with attribute suggestions."""
        known = ["degree", "betweenness", "closeness"]
        error = UnknownAttributeError("betweeness", known_attributes=known)
        error_msg = str(error)
        assert "betweeness" in error_msg
        # Should suggest "betweenness"
        assert "betweenness" in error_msg or "Did you mean" in error_msg.lower()


class TestDslSyntaxError:
    """Test the DslSyntaxError exception."""

    def test_dsl_syntax_error_basic(self):
        """Test basic DslSyntaxError."""
        error = DslSyntaxError("Syntax error in query")
        assert isinstance(error, DslError)
        assert "Syntax error" in str(error)

    def test_dsl_syntax_error_with_position(self):
        """Test DslSyntaxError with position information."""
        error = DslSyntaxError(
            "Unexpected token",
            query="SELECT nodes WHERE",
            line=1,
            column=19
        )
        error_msg = str(error)
        assert "Unexpected token" in error_msg


class TestDslExecutionError:
    """Test the DslExecutionError exception."""

    def test_dsl_execution_error_basic(self):
        """Test basic DslExecutionError."""
        error = DslExecutionError("Execution failed")
        assert isinstance(error, DslError)
        assert "Execution failed" in str(error)

    def test_dsl_execution_error_with_details(self):
        """Test DslExecutionError with details."""
        error = DslExecutionError(
            "Network has no nodes",
            query="SELECT nodes WHERE degree > 10"
        )
        error_msg = str(error)
        assert "no nodes" in error_msg


class TestErrorHierarchy:
    """Test the error inheritance hierarchy."""

    def test_all_dsl_errors_inherit_from_base(self):
        """Test that all DSL errors inherit from DslError."""
        errors_to_test = [
            DslSyntaxError("test"),
            DslExecutionError("test"),
            UnknownLayerError("test"),
            UnknownAttributeError("test"),
            UnknownMeasureError("test"),
        ]
        
        for error in errors_to_test:
            assert isinstance(error, DslError)
            assert isinstance(error, Exception)

    def test_error_messages_are_strings(self):
        """Test that all error messages can be converted to strings."""
        errors_to_test = [
            DslError("msg"),
            DslSyntaxError("syntax"),
            DslExecutionError("exec"),
            UnknownLayerError("layer"),
            UnknownAttributeError("attr"),
            UnknownMeasureError("measure"),
        ]
        
        for error in errors_to_test:
            msg = str(error)
            assert isinstance(msg, str)
            assert len(msg) > 0
