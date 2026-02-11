"""
Tests for py3plex.algorithms.community_detection.sbm_metrics module.

This module tests SBM-specific metric extraction functions.
"""

import pytest
from py3plex.algorithms.community_detection.sbm_metrics import (
    sbm_log_likelihood,
    sbm_mdl,
    sbm_n_blocks,
    SBM_METRICS,
)


class TestSBMLogLikelihood:
    """Test sbm_log_likelihood function."""

    def test_extracts_log_likelihood_from_meta(self):
        """Test that log-likelihood is extracted from metadata."""
        meta = {'log_likelihood': -1234.56}
        result = sbm_log_likelihood(None, None, meta)
        assert result == -1234.56

    def test_returns_none_when_not_present(self):
        """Test returns None when log_likelihood not in metadata."""
        meta = {'other_key': 'value'}
        result = sbm_log_likelihood(None, None, meta)
        assert result is None

    def test_empty_meta_returns_none(self):
        """Test empty metadata returns None."""
        result = sbm_log_likelihood(None, None, {})
        assert result is None

    def test_network_and_partition_not_used(self):
        """Test that network and partition arguments are ignored."""
        meta = {'log_likelihood': 100.5}
        result = sbm_log_likelihood("fake_network", {"node": 1}, meta)
        assert result == 100.5


class TestSBMMDL:
    """Test sbm_mdl function."""

    def test_extracts_mdl_from_meta(self):
        """Test that MDL is extracted from metadata."""
        meta = {'mdl': 2500.12}
        result = sbm_mdl(None, None, meta)
        assert result == 2500.12

    def test_extracts_bic_when_mdl_absent(self):
        """Test that BIC is used as fallback when MDL not present."""
        meta = {'bic': 2600.34}
        result = sbm_mdl(None, None, meta)
        assert result == 2600.34

    def test_mdl_takes_precedence_over_bic(self):
        """Test that MDL is preferred when both are present."""
        meta = {'mdl': 2500.0, 'bic': 2600.0}
        result = sbm_mdl(None, None, meta)
        assert result == 2500.0

    def test_returns_none_when_neither_present(self):
        """Test returns None when neither mdl nor bic in metadata."""
        meta = {'other_key': 'value'}
        result = sbm_mdl(None, None, meta)
        assert result is None

    def test_empty_meta_returns_none(self):
        """Test empty metadata returns None."""
        result = sbm_mdl(None, None, {})
        assert result is None

    def test_bic_zero_returns_zero(self):
        """Test that BIC=0 is properly returned when MDL absent."""
        meta = {'bic': 0}
        result = sbm_mdl(None, None, meta)
        # The implementation uses "or" which treats 0 as falsy
        # So 0 or None returns 0 (not None)
        assert result == 0

    def test_mdl_zero_returns_none_due_to_or_operator(self):
        """Test that MDL=0 returns None due to 'or' operator behavior."""
        meta = {'mdl': 0}
        result = sbm_mdl(None, None, meta)
        # Due to "meta.get('mdl') or meta.get('bic')" logic,
        # mdl=0 is falsy, so it evaluates meta.get('bic') which is None
        # This is a quirk of the implementation
        assert result is None


class TestSBMNBlocks:
    """Test sbm_n_blocks function."""

    def test_extracts_k_selected_from_meta(self):
        """Test that K_selected is extracted from metadata."""
        meta = {'K_selected': 5}
        result = sbm_n_blocks(None, None, meta)
        assert result == 5

    def test_returns_none_when_not_present(self):
        """Test returns None when K_selected not in metadata."""
        meta = {'other_key': 'value'}
        result = sbm_n_blocks(None, None, meta)
        assert result is None

    def test_empty_meta_returns_none(self):
        """Test empty metadata returns None."""
        result = sbm_n_blocks(None, None, {})
        assert result is None

    def test_k_selected_various_values(self):
        """Test K_selected with various valid values."""
        for k in [1, 2, 5, 10, 100]:
            meta = {'K_selected': k}
            result = sbm_n_blocks(None, None, meta)
            assert result == k


class TestSBMMetricsRegistry:
    """Test SBM_METRICS registry structure."""

    def test_registry_has_expected_keys(self):
        """Test that registry contains all expected metrics."""
        expected = ['sbm_log_likelihood', 'sbm_mdl', 'sbm_n_blocks']
        assert set(SBM_METRICS.keys()) == set(expected)

    def test_log_likelihood_entry(self):
        """Test sbm_log_likelihood registry entry."""
        entry = SBM_METRICS['sbm_log_likelihood']
        assert entry['function'] == sbm_log_likelihood
        assert entry['direction'] == 'maximize'
        assert 'description' in entry
        assert 'requires' in entry
        assert 'sbm' in entry['requires']
        assert 'dc_sbm' in entry['requires']

    def test_mdl_entry(self):
        """Test sbm_mdl registry entry."""
        entry = SBM_METRICS['sbm_mdl']
        assert entry['function'] == sbm_mdl
        assert entry['direction'] == 'minimize'
        assert 'description' in entry
        assert 'requires' in entry
        assert 'sbm' in entry['requires']
        assert 'dc_sbm' in entry['requires']

    def test_n_blocks_entry(self):
        """Test sbm_n_blocks registry entry."""
        entry = SBM_METRICS['sbm_n_blocks']
        assert entry['function'] == sbm_n_blocks
        assert entry['direction'] == 'none'
        assert 'description' in entry
        assert 'requires' in entry
        assert 'sbm' in entry['requires']
        assert 'dc_sbm' in entry['requires']

    def test_all_entries_have_required_fields(self):
        """Test that all entries have function, direction, description, requires."""
        for metric_name, entry in SBM_METRICS.items():
            assert 'function' in entry, f"{metric_name} missing 'function'"
            assert 'direction' in entry, f"{metric_name} missing 'direction'"
            assert 'description' in entry, f"{metric_name} missing 'description'"
            assert 'requires' in entry, f"{metric_name} missing 'requires'"
            assert callable(entry['function']), f"{metric_name} 'function' not callable"
            assert isinstance(entry['description'], str), f"{metric_name} 'description' not string"
            assert isinstance(entry['requires'], list), f"{metric_name} 'requires' not list"

    def test_direction_values_valid(self):
        """Test that all direction values are valid."""
        valid_directions = {'maximize', 'minimize', 'none'}
        for metric_name, entry in SBM_METRICS.items():
            assert entry['direction'] in valid_directions, \
                f"{metric_name} has invalid direction: {entry['direction']}"
