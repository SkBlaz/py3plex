"""
Tests for py3plex.algorithms.hedwig.stats.significance module.

This module tests Fisher's exact test for rule significance.
"""

import pytest
pytest.importorskip("rdflib")
from unittest.mock import MagicMock
import scipy.stats as st
import numpy as np


class TestFisherSignificance:
    """Test Fisher's exact test functions."""

    def test_import_module(self):
        """Test that the module can be imported."""
        from py3plex.algorithms.hedwig.stats import significance
        assert hasattr(significance, 'fisher')
        assert hasattr(significance, 'apply_fisher')
        assert hasattr(significance, 'is_redundant')

    def test_fisher_basic(self):
        """Test basic fisher function."""
        from py3plex.algorithms.hedwig.stats.significance import fisher
        
        # Create mock rule
        rule = MagicMock()
        rule.kb = MagicMock()
        rule.kb.examples = list(range(100))  # 100 examples
        rule.coverage = 50
        rule.target = 'target_class'
        rule.kb.distribution = {'target_class': 30}
        rule.distribution = {'target_class': 25}
        
        # Call fisher
        result = fisher(rule)
        
        # Result should be a p-value (float between 0 and 1)
        assert isinstance(result, float)
        assert 0 <= result <= 1

    def test_apply_fisher_updates_pval(self):
        """Test that apply_fisher sets pval attribute on rules."""
        from py3plex.algorithms.hedwig.stats.significance import apply_fisher
        
        # Create mock rule
        rule = MagicMock()
        rule.kb = MagicMock()
        rule.kb.examples = list(range(100))
        rule.coverage = 50
        rule.target = 'target_class'
        rule.kb.distribution = {'target_class': 30}
        rule.distribution = {'target_class': 25}
        
        # Call apply_fisher with a ruleset
        ruleset = [rule]
        apply_fisher(ruleset)
        
        # Check that pval was set
        assert hasattr(rule, 'pval')
        assert isinstance(rule.pval, float)
        assert 0 <= rule.pval <= 1

    def test_apply_fisher_with_multiple_rules(self):
        """Test apply_fisher with multiple rules."""
        from py3plex.algorithms.hedwig.stats.significance import apply_fisher
        
        # Create multiple mock rules
        rules = []
        for i in range(3):
            rule = MagicMock()
            rule.kb = MagicMock()
            rule.kb.examples = list(range(100))
            rule.coverage = 50 - i * 10
            rule.target = 'target_class'
            rule.kb.distribution = {'target_class': 30}
            rule.distribution = {'target_class': 25 - i * 5}
            rules.append(rule)
        
        # Call apply_fisher
        apply_fisher(rules)
        
        # Check that all rules have pval set
        for rule in rules:
            assert hasattr(rule, 'pval')
            assert isinstance(rule.pval, float)
            assert 0 <= rule.pval <= 1

    def test_is_redundant_basic(self):
        """Test is_redundant function."""
        from py3plex.algorithms.hedwig.stats.significance import is_redundant
        
        # Create two mock rules
        rule1 = MagicMock()
        rule1.kb = MagicMock()
        rule1.kb.examples = list(range(100))
        rule1.coverage = 50
        rule1.target = 'target_class'
        rule1.kb.distribution = {'target_class': 30}
        rule1.distribution = {'target_class': 25}
        
        rule2 = MagicMock()
        rule2.kb = MagicMock()
        rule2.kb.examples = list(range(100))
        rule2.coverage = 40
        rule2.target = 'target_class'
        rule2.kb.distribution = {'target_class': 30}
        rule2.distribution = {'target_class': 20}
        
        # Call is_redundant
        result = is_redundant(rule1, rule2)
        
        # Result should be a boolean
        assert isinstance(result, (bool, np.bool_))

    def test_fisher_with_zero_coverage(self):
        """Test fisher with zero coverage."""
        from py3plex.algorithms.hedwig.stats.significance import fisher
        
        rule = MagicMock()
        rule.kb = MagicMock()
        rule.kb.examples = list(range(100))
        rule.coverage = 0  # Zero coverage
        rule.target = 'target_class'
        rule.kb.distribution = {'target_class': 30}
        rule.distribution = {'target_class': 0}
        
        # Should not raise an error
        result = fisher(rule)
        assert isinstance(result, float)
        assert 0 <= result <= 1

    def test_fisher_with_perfect_match(self):
        """Test fisher when all covered examples are positive."""
        from py3plex.algorithms.hedwig.stats.significance import fisher
        
        rule = MagicMock()
        rule.kb = MagicMock()
        rule.kb.examples = list(range(100))
        rule.coverage = 30
        rule.target = 'target_class'
        rule.kb.distribution = {'target_class': 30}
        rule.distribution = {'target_class': 30}  # Perfect match
        
        result = fisher(rule)
        assert isinstance(result, float)
        assert 0 <= result <= 1
        # Perfect match should have very low p-value (highly significant)
        assert result < 0.5

    def test_apply_fisher_with_empty_ruleset(self):
        """Test apply_fisher with empty ruleset."""
        from py3plex.algorithms.hedwig.stats.significance import apply_fisher
        
        # Should not raise an error
        apply_fisher([])

    def test_fisher_different_targets(self):
        """Test fisher with different target classes."""
        from py3plex.algorithms.hedwig.stats.significance import fisher
        
        for target in ['class_a', 'class_b', 'class_c']:
            rule = MagicMock()
            rule.kb = MagicMock()
            rule.kb.examples = list(range(100))
            rule.coverage = 50
            rule.target = target
            rule.kb.distribution = {target: 30}
            rule.distribution = {target: 25}
            
            result = fisher(rule)
            assert isinstance(result, float)
            assert 0 <= result <= 1
