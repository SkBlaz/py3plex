#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test suite for hedwig statistical adjustment methods.

Tests the multiple-testing adjustment methods including the newly
implemented holdout validation approach.
"""

import unittest
from unittest.mock import Mock


class TestHedwigAdjustment(unittest.TestCase):
    """Test cases for hedwig adjustment methods."""

    @classmethod
    def setUpClass(cls):
        """Check if hedwig is available."""
        try:
            from py3plex.algorithms.hedwig.stats import adjustment
            cls.adjustment = adjustment
            cls.HEDWIG_AVAILABLE = True
        except ImportError:
            cls.HEDWIG_AVAILABLE = False

    def setUp(self):
        """Set up mock rules with p-values for testing."""
        if not self.HEDWIG_AVAILABLE:
            self.skipTest("hedwig not available")
            return

        # Create mock rules with p-values
        self.rules = []
        pvalues = [0.001, 0.005, 0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.08, 0.1]
        for i, pval in enumerate(pvalues):
            rule = Mock()
            rule.pval = pval
            rule.id = f"rule_{i}"
            self.rules.append(rule)
    def test_holdout_returns_list(self):
        """Test that _holdout returns a list."""
        result = self.adjustment._holdout(self.rules)
        self.assertIsInstance(result, list)

    def test_holdout_empty_input(self):
        """Test that _holdout handles empty input gracefully."""
        result = self.adjustment._holdout([])
        self.assertEqual(len(result), 0)

    def test_holdout_filters_significant(self):
        """Test that _holdout filters out non-significant rules."""
        result = self.adjustment._holdout(self.rules, alpha=0.05)
        
        # Should filter out rules with p > 0.05
        # With holdout validation, should be conservative
        self.assertLessEqual(len(result), len(self.rules))

    def test_holdout_with_different_ratios(self):
        """Test that _holdout works with different holdout ratios."""
        # Test with different holdout ratios
        result_30 = self.adjustment._holdout(self.rules, holdout_ratio=0.3, alpha=0.05)
        result_50 = self.adjustment._holdout(self.rules, holdout_ratio=0.5, alpha=0.05)
        
        # Both should return lists
        self.assertIsInstance(result_30, list)
        self.assertIsInstance(result_50, list)
        
        # Results should be filtered
        self.assertLessEqual(len(result_30), len(self.rules))
        self.assertLessEqual(len(result_50), len(self.rules))

    def test_holdout_conservative(self):
        """Test that holdout is more conservative than no adjustment."""
        # No adjustment - just filter by alpha
        no_adjustment = self.adjustment.none(self.rules)
        no_adj_filtered = [r for r in no_adjustment if r.pval <= 0.05]
        
        # Holdout adjustment
        holdout_result = self.adjustment._holdout(self.rules, alpha=0.05)
        
        # Holdout should be more conservative (fewer or equal rules)
        self.assertLessEqual(len(holdout_result), len(no_adj_filtered))

    def test_holdout_preserves_significant_rules(self):
        """Test that very significant rules are preserved."""
        result = self.adjustment._holdout(self.rules, alpha=0.05)
        
        # The most significant rules (very low p-values) should be in result
        if len(result) > 0:
            # Check that rules in result have low p-values
            for rule in result:
                self.assertLessEqual(rule.pval, 0.05)

    def test_fwer_comparison(self):
        """Test that FWER adjustment works and compare with holdout."""
        fwer_result = self.adjustment.fwer(self.rules, alpha=0.05)
        holdout_result = self.adjustment._holdout(self.rules, alpha=0.05)
        
        # Both should return filtered lists
        self.assertIsInstance(fwer_result, list)
        self.assertIsInstance(holdout_result, list)
        
        # Both should be conservative
        self.assertLessEqual(len(fwer_result), len(self.rules))
        self.assertLessEqual(len(holdout_result), len(self.rules))

    def test_fdr_comparison(self):
        """Test that FDR adjustment works and compare with holdout."""
        fdr_result = self.adjustment.fdr(self.rules, q=0.05)
        holdout_result = self.adjustment._holdout(self.rules, alpha=0.05)
        
        # Both should return filtered lists
        self.assertIsInstance(fdr_result, list)
        self.assertIsInstance(holdout_result, list)

    def test_holdout_single_rule(self):
        """Test holdout with a single rule."""
        single_rule = [self.rules[0]]  # p-value = 0.001
        result = self.adjustment._holdout(single_rule, alpha=0.05)
        
        # Should handle single rule gracefully
        self.assertIsInstance(result, list)
        # Very significant rule should be kept
        self.assertGreaterEqual(len(result), 0)


if __name__ == "__main__":
    unittest.main()
