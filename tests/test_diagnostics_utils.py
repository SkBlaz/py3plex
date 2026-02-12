"""
Tests for py3plex.diagnostics.utils module.

This module tests fuzzy matching, "did you mean?" suggestions,
and Levenshtein distance calculations.
"""

import pytest
from py3plex.diagnostics.utils import (
    fuzzy_match,
    did_you_mean,
    levenshtein_distance,
    suggest_similar_field,
    suggest_builder_method,
)


class TestFuzzyMatch:
    """Test the fuzzy_match function."""

    def test_exact_match(self):
        """Test exact match returns highest score."""
        candidates = ["degree", "betweenness", "closeness"]
        matches = fuzzy_match("degree", candidates)
        
        assert len(matches) >= 1
        assert matches[0][0] == "degree"
        assert matches[0][1] == 1.0  # Perfect match

    def test_close_match(self):
        """Test close match with typo."""
        candidates = ["degree", "betweenness", "closeness"]
        matches = fuzzy_match("degre", candidates)
        
        assert len(matches) >= 1
        assert matches[0][0] == "degree"
        assert matches[0][1] > 0.8  # High similarity

    def test_no_matches(self):
        """Test no matches below cutoff."""
        candidates = ["degree", "betweenness"]
        matches = fuzzy_match("xyz123", candidates, cutoff=0.9)
        
        assert len(matches) == 0

    def test_multiple_matches(self):
        """Test multiple matches sorted by score."""
        candidates = ["pagerank", "eigenvector", "katz"]
        matches = fuzzy_match("rank", candidates, max_suggestions=3)
        
        assert len(matches) >= 1
        # First match should be pagerank (contains "rank")
        assert "rank" in matches[0][0].lower()

    def test_empty_candidates(self):
        """Test empty candidates list."""
        matches = fuzzy_match("degree", [])
        
        assert matches == []

    def test_max_suggestions_limit(self):
        """Test max_suggestions parameter."""
        candidates = ["a", "b", "c", "d", "e"]
        matches = fuzzy_match("a", candidates, max_suggestions=2)
        
        assert len(matches) <= 2

    def test_case_insensitive(self):
        """Test case-insensitive matching."""
        candidates = ["PageRank", "Betweenness", "Closeness"]
        matches = fuzzy_match("pagerank", candidates)
        
        assert len(matches) >= 1
        assert matches[0][0] == "PageRank"


class TestDidYouMean:
    """Test the did_you_mean function."""

    def test_good_suggestion(self):
        """Test suggestion for close match."""
        candidates = ["degree", "betweenness", "closeness"]
        suggestion = did_you_mean("degre", candidates)
        
        assert suggestion == "degree"

    def test_no_suggestion(self):
        """Test no suggestion for poor match."""
        candidates = ["degree", "betweenness"]
        suggestion = did_you_mean("xyz123", candidates, cutoff=0.9)
        
        assert suggestion is None

    def test_empty_candidates(self):
        """Test empty candidates list."""
        suggestion = did_you_mean("degree", [])
        
        assert suggestion is None

    def test_exact_match_suggestion(self):
        """Test exact match returns the same word."""
        candidates = ["degree", "betweenness"]
        suggestion = did_you_mean("degree", candidates)
        
        assert suggestion == "degree"


class TestLevenshteinDistance:
    """Test the levenshtein_distance function."""

    def test_identical_strings(self):
        """Test distance between identical strings."""
        distance = levenshtein_distance("abc", "abc")
        
        assert distance == 0

    def test_single_insertion(self):
        """Test single character insertion."""
        distance = levenshtein_distance("abc", "abcd")
        
        assert distance == 1

    def test_single_deletion(self):
        """Test single character deletion."""
        distance = levenshtein_distance("abcd", "abc")
        
        assert distance == 1

    def test_single_substitution(self):
        """Test single character substitution."""
        distance = levenshtein_distance("abc", "abd")
        
        assert distance == 1

    def test_empty_strings(self):
        """Test empty strings."""
        assert levenshtein_distance("", "") == 0
        assert levenshtein_distance("abc", "") == 3
        assert levenshtein_distance("", "abc") == 3

    def test_completely_different(self):
        """Test completely different strings."""
        distance = levenshtein_distance("abc", "xyz")
        
        assert distance == 3  # All characters different

    def test_case_sensitive(self):
        """Test that distance is case-sensitive."""
        distance = levenshtein_distance("ABC", "abc")
        
        assert distance == 3  # All characters different in case


class TestSuggestSimilarField:
    """Test the suggest_similar_field function."""

    def test_close_field(self):
        """Test suggestion for close field name."""
        known_fields = ["degree", "betweenness_centrality", "pagerank"]
        suggestion = suggest_similar_field("degre", known_fields)
        
        assert suggestion == "degree"

    def test_no_close_field(self):
        """Test no suggestion for distant field."""
        known_fields = ["degree", "betweenness"]
        suggestion = suggest_similar_field("xyz123", known_fields, max_distance=2)
        
        assert suggestion is None

    def test_empty_known_fields(self):
        """Test empty known fields list."""
        suggestion = suggest_similar_field("degree", [])
        
        assert suggestion is None

    def test_max_distance_limit(self):
        """Test max_distance parameter."""
        known_fields = ["degree", "betweenness"]
        # "degreeee" is 3 edits away from "degree"
        suggestion = suggest_similar_field("degreeee", known_fields, max_distance=2)
        
        # Should be None because distance > max_distance
        assert suggestion is None

    def test_case_insensitive_suggestion(self):
        """Test case-insensitive field suggestions."""
        known_fields = ["PageRank", "Betweenness"]
        suggestion = suggest_similar_field("pagerank", known_fields)
        
        assert suggestion == "PageRank"


class TestSuggestBuilderMethod:
    """Test the suggest_builder_method function."""

    def test_close_method(self):
        """Test suggestion for close method name."""
        known_methods = ["per_layer", "top_k", "limit"]
        suggestion = suggest_builder_method("per_laye", known_methods)
        
        assert suggestion == "per_layer"

    def test_underscore_removal(self):
        """Test suggestion with underscores removed."""
        known_methods = ["per_layer", "top_k", "order_by"]
        suggestion = suggest_builder_method("perlayer", known_methods)
        
        assert suggestion == "per_layer"

    def test_no_suggestion(self):
        """Test no suggestion for unknown method."""
        known_methods = ["per_layer", "top_k"]
        suggestion = suggest_builder_method("xyz123", known_methods)
        
        assert suggestion is None

    def test_exact_match(self):
        """Test exact match returns the same method."""
        known_methods = ["per_layer", "top_k", "limit"]
        suggestion = suggest_builder_method("per_layer", known_methods)
        
        assert suggestion == "per_layer"

    def test_common_typo_perlayer(self):
        """Test common typo: perlayer → per_layer."""
        known_methods = ["per_layer", "per_layer_pair", "end_grouping"]
        suggestion = suggest_builder_method("perlayer", known_methods)
        
        assert suggestion == "per_layer"

    def test_common_typo_orderby(self):
        """Test common typo: orderby → order_by."""
        known_methods = ["order_by", "limit", "compute"]
        suggestion = suggest_builder_method("orderby", known_methods)
        
        assert suggestion == "order_by"
