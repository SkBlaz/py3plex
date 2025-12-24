"""
Extended tests for py3plex.dsl.errors module.

This module adds test coverage for DSL error types and helper functions.
"""

import pytest

from py3plex.dsl.errors import (
    DslError,
    UnknownLayerError,
    UnknownOperatorError,
    InvalidFilterError,
    InvalidComputeError,
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

    def test_dsl_error_with_position(self):
        """Test DslError with position information."""
        error = DslError("Test error", position=10)
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
        available = ["social", "work", "family"]
        error = UnknownLayerError("socail", available_layers=available)
        error_msg = str(error)
        assert "socail" in error_msg
        # Should suggest "social" as it's similar
        assert "social" in error_msg or "Did you mean" in error_msg.lower()

    def test_unknown_layer_error_no_suggestions(self):
        """Test UnknownLayerError when no similar layers exist."""
        available = ["layer1", "layer2"]
        error = UnknownLayerError("xyz", available_layers=available)
        error_msg = str(error)
        assert "xyz" in error_msg


class TestUnknownOperatorError:
    """Test the UnknownOperatorError exception."""

    def test_unknown_operator_error_basic(self):
        """Test basic UnknownOperatorError."""
        error = UnknownOperatorError("invalid_op")
        assert isinstance(error, DslError)
        assert "invalid_op" in str(error)

    def test_unknown_operator_error_with_suggestions(self):
        """Test UnknownOperatorError with operator suggestions."""
        available = ["degree", "betweenness", "closeness"]
        error = UnknownOperatorError("betweeness", available_operators=available)
        error_msg = str(error)
        assert "betweeness" in error_msg
        # Should suggest "betweenness" 
        assert "betweenness" in error_msg or "Did you mean" in error_msg.lower()


class TestInvalidFilterError:
    """Test the InvalidFilterError exception."""

    def test_invalid_filter_error_basic(self):
        """Test basic InvalidFilterError."""
        error = InvalidFilterError("Invalid filter condition")
        assert isinstance(error, DslError)
        assert "Invalid filter condition" in str(error)

    def test_invalid_filter_error_with_details(self):
        """Test InvalidFilterError with filter details."""
        error = InvalidFilterError(
            "Comparison requires numeric type",
            filter_expression="layer > 5"
        )
        error_msg = str(error)
        assert "numeric type" in error_msg


class TestInvalidComputeError:
    """Test the InvalidComputeError exception."""

    def test_invalid_compute_error_basic(self):
        """Test basic InvalidComputeError."""
        error = InvalidComputeError("Invalid computation")
        assert isinstance(error, DslError)
        assert "Invalid computation" in str(error)

    def test_invalid_compute_error_with_metric(self):
        """Test InvalidComputeError with metric name."""
        error = InvalidComputeError(
            "Metric not applicable to this graph type",
            metric_name="clustering_coefficient"
        )
        error_msg = str(error)
        assert "clustering_coefficient" in error_msg or "Metric" in error_msg


class TestErrorHierarchy:
    """Test the error inheritance hierarchy."""

    def test_all_dsl_errors_inherit_from_base(self):
        """Test that all DSL errors inherit from DslError."""
        errors_to_test = [
            UnknownLayerError("test"),
            UnknownOperatorError("test"),
            InvalidFilterError("test"),
            InvalidComputeError("test"),
        ]
        
        for error in errors_to_test:
            assert isinstance(error, DslError)
            assert isinstance(error, Exception)

    def test_error_messages_are_strings(self):
        """Test that all error messages can be converted to strings."""
        errors_to_test = [
            DslError("msg"),
            UnknownLayerError("layer"),
            UnknownOperatorError("op"),
            InvalidFilterError("filter"),
            InvalidComputeError("compute"),
        ]
        
        for error in errors_to_test:
            msg = str(error)
            assert isinstance(msg, str)
            assert len(msg) > 0
