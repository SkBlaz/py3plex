"""Tests for py3plex.contracts.failure_modes module.

Tests the FailureMode enum for typed failure modes.
"""

import pytest
from py3plex.contracts.failure_modes import FailureMode


class TestFailureModeEnum:
    """Test FailureMode enum."""
    
    def test_failure_mode_values(self):
        """Test that all failure modes have expected values."""
        assert FailureMode.INSUFFICIENT_BASELINE.value == "insufficient_baseline"
        assert FailureMode.NONDETERMINISM_LEAK.value == "nondeterminism_leak"
        assert FailureMode.PERTURBATION_INVALID.value == "perturbation_invalid"
        assert FailureMode.METRIC_UNDEFINED.value == "metric_undefined"
        assert FailureMode.CONTRACT_VIOLATION.value == "contract_violation"
        assert FailureMode.REPAIR_IMPOSSIBLE.value == "repair_impossible"
        assert FailureMode.RESOURCE_LIMIT.value == "resource_limit"
        assert FailureMode.EXECUTION_ERROR.value == "execution_error"
    
    def test_failure_mode_count(self):
        """Test that there are exactly 8 failure modes."""
        modes = list(FailureMode)
        assert len(modes) == 8
    
    def test_failure_modes_are_unique(self):
        """Test that all failure mode values are unique."""
        values = [mode.value for mode in FailureMode]
        assert len(values) == len(set(values))
    
    def test_failure_mode_from_value(self):
        """Test creating FailureMode from string value."""
        mode = FailureMode("contract_violation")
        assert mode == FailureMode.CONTRACT_VIOLATION
    
    def test_failure_mode_equality(self):
        """Test that failure modes are comparable."""
        mode1 = FailureMode.INSUFFICIENT_BASELINE
        mode2 = FailureMode.INSUFFICIENT_BASELINE
        mode3 = FailureMode.NONDETERMINISM_LEAK
        
        assert mode1 == mode2
        assert mode1 != mode3
    
    def test_failure_mode_hashable(self):
        """Test that failure modes are hashable."""
        modes_set = {
            FailureMode.INSUFFICIENT_BASELINE,
            FailureMode.CONTRACT_VIOLATION,
            FailureMode.REPAIR_IMPOSSIBLE
        }
        
        assert len(modes_set) == 3
        assert FailureMode.INSUFFICIENT_BASELINE in modes_set


class TestFailureModeSemantics:
    """Test semantic meaning of each failure mode."""
    
    def test_insufficient_baseline_semantic(self):
        """Test INSUFFICIENT_BASELINE represents empty/insufficient baseline."""
        mode = FailureMode.INSUFFICIENT_BASELINE
        
        # Should be distinguishable from other modes
        assert mode != FailureMode.CONTRACT_VIOLATION
        assert "baseline" in mode.value
    
    def test_nondeterminism_leak_semantic(self):
        """Test NONDETERMINISM_LEAK represents missing seed."""
        mode = FailureMode.NONDETERMINISM_LEAK
        
        assert "nondeterminism" in mode.value
        assert mode != FailureMode.EXECUTION_ERROR
    
    def test_perturbation_invalid_semantic(self):
        """Test PERTURBATION_INVALID represents bad perturbation spec."""
        mode = FailureMode.PERTURBATION_INVALID
        
        assert "perturbation" in mode.value
        assert mode != FailureMode.METRIC_UNDEFINED
    
    def test_metric_undefined_semantic(self):
        """Test METRIC_UNDEFINED represents undefined metric computation."""
        mode = FailureMode.METRIC_UNDEFINED
        
        assert "metric" in mode.value
        assert mode != FailureMode.PERTURBATION_INVALID
    
    def test_contract_violation_semantic(self):
        """Test CONTRACT_VIOLATION is standard failure case."""
        mode = FailureMode.CONTRACT_VIOLATION
        
        assert "contract" in mode.value
        # This is the "normal" failure mode
        assert mode != FailureMode.EXECUTION_ERROR
    
    def test_repair_impossible_semantic(self):
        """Test REPAIR_IMPOSSIBLE represents failed repair attempt."""
        mode = FailureMode.REPAIR_IMPOSSIBLE
        
        assert "repair" in mode.value
        assert mode != FailureMode.CONTRACT_VIOLATION
    
    def test_resource_limit_semantic(self):
        """Test RESOURCE_LIMIT represents budget exceeded."""
        mode = FailureMode.RESOURCE_LIMIT
        
        assert "resource" in mode.value
        assert mode != FailureMode.EXECUTION_ERROR
    
    def test_execution_error_semantic(self):
        """Test EXECUTION_ERROR is catch-all for unexpected errors."""
        mode = FailureMode.EXECUTION_ERROR
        
        assert "execution" in mode.value
        # Should be different from other error modes
        assert mode != FailureMode.METRIC_UNDEFINED
        assert mode != FailureMode.PERTURBATION_INVALID


class TestFailureModeUsage:
    """Test typical usage patterns for failure modes."""
    
    def test_failure_mode_in_dict_key(self):
        """Test using failure modes as dict keys."""
        failure_counts = {
            FailureMode.INSUFFICIENT_BASELINE: 5,
            FailureMode.CONTRACT_VIOLATION: 10,
            FailureMode.REPAIR_IMPOSSIBLE: 2
        }
        
        assert failure_counts[FailureMode.INSUFFICIENT_BASELINE] == 5
        assert failure_counts[FailureMode.CONTRACT_VIOLATION] == 10
    
    def test_failure_mode_in_switch_case(self):
        """Test using failure modes in conditional logic."""
        mode = FailureMode.CONTRACT_VIOLATION
        
        if mode == FailureMode.INSUFFICIENT_BASELINE:
            message = "Need more baseline data"
        elif mode == FailureMode.CONTRACT_VIOLATION:
            message = "Predicate not met"
        elif mode == FailureMode.EXECUTION_ERROR:
            message = "Unexpected error"
        else:
            message = "Other failure"
        
        assert message == "Predicate not met"
    
    def test_failure_mode_categorization(self):
        """Test categorizing failure modes by type."""
        # Data quality issues
        data_issues = {
            FailureMode.INSUFFICIENT_BASELINE,
            FailureMode.METRIC_UNDEFINED
        }
        
        # Configuration issues
        config_issues = {
            FailureMode.NONDETERMINISM_LEAK,
            FailureMode.PERTURBATION_INVALID
        }
        
        # Analysis failures
        analysis_failures = {
            FailureMode.CONTRACT_VIOLATION,
            FailureMode.REPAIR_IMPOSSIBLE
        }
        
        # Infrastructure failures
        infra_failures = {
            FailureMode.RESOURCE_LIMIT,
            FailureMode.EXECUTION_ERROR
        }
        
        # All modes should be categorized
        all_modes = data_issues | config_issues | analysis_failures | infra_failures
        assert len(all_modes) == 8
        assert all_modes == set(FailureMode)
