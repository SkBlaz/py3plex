"""Tests for py3plex.fast_examples module.

Tests the utilities for managing example execution performance in CI/testing environments.
"""

import os
import sys
import pytest
from py3plex.fast_examples import (
    is_fast_mode,
    get_fast_params,
    TimeoutError,
    print_fast_mode_info,
    FAST_UQ_PARAMS,
    FAST_COMMUNITY_PARAMS,
    FAST_LAYOUT_PARAMS,
    FAST_DYNAMICS_PARAMS,
)


class TestFastMode:
    """Test fast mode detection."""

    def test_is_fast_mode_disabled_by_default(self):
        """Test that fast mode is disabled when env var not set."""
        # Ensure clean environment
        if "FAST_EXAMPLES" in os.environ:
            del os.environ["FAST_EXAMPLES"]
        assert is_fast_mode() is False

    def test_is_fast_mode_enabled_with_1(self):
        """Test fast mode enabled with FAST_EXAMPLES=1."""
        os.environ["FAST_EXAMPLES"] = "1"
        try:
            assert is_fast_mode() is True
        finally:
            del os.environ["FAST_EXAMPLES"]

    def test_is_fast_mode_enabled_with_true(self):
        """Test fast mode enabled with FAST_EXAMPLES=true."""
        os.environ["FAST_EXAMPLES"] = "true"
        try:
            assert is_fast_mode() is True
        finally:
            del os.environ["FAST_EXAMPLES"]

    def test_is_fast_mode_enabled_with_yes(self):
        """Test fast mode enabled with FAST_EXAMPLES=yes."""
        os.environ["FAST_EXAMPLES"] = "yes"
        try:
            assert is_fast_mode() is True
        finally:
            del os.environ["FAST_EXAMPLES"]

    def test_is_fast_mode_case_insensitive(self):
        """Test that fast mode detection is case-insensitive."""
        for value in ["TRUE", "True", "YES", "Yes", "ON", "On"]:
            os.environ["FAST_EXAMPLES"] = value
            try:
                assert is_fast_mode() is True, f"Failed for value: {value}"
            finally:
                del os.environ["FAST_EXAMPLES"]

    def test_is_fast_mode_disabled_with_0(self):
        """Test fast mode disabled with FAST_EXAMPLES=0."""
        os.environ["FAST_EXAMPLES"] = "0"
        try:
            assert is_fast_mode() is False
        finally:
            del os.environ["FAST_EXAMPLES"]


class TestGetFastParams:
    """Test parameter selection based on fast mode."""

    def test_returns_defaults_when_fast_mode_off(self):
        """Test that defaults are returned when fast mode is off."""
        if "FAST_EXAMPLES" in os.environ:
            del os.environ["FAST_EXAMPLES"]
        
        defaults = {"n_samples": 100, "max_iter": 1000}
        fast = {"n_samples": 10, "max_iter": 50}
        
        result = get_fast_params(defaults, fast)
        assert result == defaults
        assert result is defaults  # Returns same object

    def test_returns_merged_params_when_fast_mode_on(self):
        """Test that fast overrides are merged when fast mode is on."""
        os.environ["FAST_EXAMPLES"] = "1"
        try:
            defaults = {"n_samples": 100, "max_iter": 1000, "seed": 42}
            fast = {"n_samples": 10, "max_iter": 50}
            
            result = get_fast_params(defaults, fast)
            
            # Fast overrides applied
            assert result["n_samples"] == 10
            assert result["max_iter"] == 50
            # Default preserved
            assert result["seed"] == 42
        finally:
            del os.environ["FAST_EXAMPLES"]

    def test_fast_overrides_do_not_mutate_defaults(self):
        """Test that applying fast overrides doesn't mutate defaults."""
        os.environ["FAST_EXAMPLES"] = "1"
        try:
            defaults = {"n_samples": 100}
            fast = {"n_samples": 10}
            
            result = get_fast_params(defaults, fast)
            
            # Defaults unchanged
            assert defaults["n_samples"] == 100
            # Result has override
            assert result["n_samples"] == 10
        finally:
            del os.environ["FAST_EXAMPLES"]


class TestTimeoutError:
    """Test TimeoutError exception."""

    def test_timeout_error_is_exception(self):
        """Test that TimeoutError is an Exception."""
        assert issubclass(TimeoutError, Exception)

    def test_timeout_error_can_be_raised(self):
        """Test that TimeoutError can be raised and caught."""
        with pytest.raises(TimeoutError, match="Example execution exceeded"):
            raise TimeoutError("Example execution exceeded time limit")


class TestPrintFastModeInfo:
    """Test fast mode info printing."""

    def test_print_info_when_fast_mode_enabled(self, capsys):
        """Test that info is printed when fast mode is enabled."""
        os.environ["FAST_EXAMPLES"] = "1"
        try:
            print_fast_mode_info()
            captured = capsys.readouterr()
            assert "FAST_EXAMPLES mode enabled" in captured.out
            assert "reduced parameters" in captured.out
        finally:
            del os.environ["FAST_EXAMPLES"]

    def test_no_output_when_fast_mode_disabled(self, capsys):
        """Test that no output when fast mode is disabled."""
        if "FAST_EXAMPLES" in os.environ:
            del os.environ["FAST_EXAMPLES"]
        
        print_fast_mode_info()
        captured = capsys.readouterr()
        assert captured.out == ""


class TestPresetParams:
    """Test preset parameter constants."""

    def test_fast_uq_params_defined(self):
        """Test that FAST_UQ_PARAMS is properly defined."""
        assert isinstance(FAST_UQ_PARAMS, dict)
        assert "n_samples" in FAST_UQ_PARAMS
        assert "ci" in FAST_UQ_PARAMS
        assert FAST_UQ_PARAMS["n_samples"] < 50  # Should be reduced

    def test_fast_community_params_defined(self):
        """Test that FAST_COMMUNITY_PARAMS is properly defined."""
        assert isinstance(FAST_COMMUNITY_PARAMS, dict)
        assert "max_iter" in FAST_COMMUNITY_PARAMS
        assert "n_restarts" in FAST_COMMUNITY_PARAMS
        assert FAST_COMMUNITY_PARAMS["max_iter"] < 100  # Should be reduced

    def test_fast_layout_params_defined(self):
        """Test that FAST_LAYOUT_PARAMS is properly defined."""
        assert isinstance(FAST_LAYOUT_PARAMS, dict)
        assert "iterations" in FAST_LAYOUT_PARAMS
        assert FAST_LAYOUT_PARAMS["iterations"] < 200  # Should be reduced

    def test_fast_dynamics_params_defined(self):
        """Test that FAST_DYNAMICS_PARAMS is properly defined."""
        assert isinstance(FAST_DYNAMICS_PARAMS, dict)
        assert "steps" in FAST_DYNAMICS_PARAMS
        assert "replicates" in FAST_DYNAMICS_PARAMS
        assert FAST_DYNAMICS_PARAMS["steps"] < 100  # Should be reduced
        assert FAST_DYNAMICS_PARAMS["replicates"] < 10  # Should be reduced
