"""
Tests for py3plex.algebra.fixed_point module.

Tests fixed-point iteration for semiring operations.
"""

import pytest
from py3plex.algebra.fixed_point import fixed_point_iteration, _numeric_converged


class TestFixedPointIteration:
    """Test the fixed_point_iteration function."""

    def test_converges_with_exact_equality(self):
        """Test convergence with exact state equality."""
        # Simple state that converges immediately
        initial_state = {"a": 1, "b": 2}
        
        # Update function that returns same state (fixed point)
        def update_fn(state):
            return state.copy()
        
        final_state, converged, iters = fixed_point_iteration(
            initial_state, update_fn, max_iters=10
        )
        
        assert converged is True
        assert iters == 1  # Converges in first iteration
        assert final_state == initial_state

    def test_converges_after_multiple_iterations(self):
        """Test convergence after multiple iterations."""
        initial_state = {"x": 10.0}
        
        # Update function that halves the value
        def update_fn(state):
            if state["x"] > 1.0:
                return {"x": state["x"] / 2}
            return state
        
        final_state, converged, iters = fixed_point_iteration(
            initial_state, update_fn, max_iters=20
        )
        
        assert converged is True
        assert final_state["x"] <= 1.0

    def test_max_iterations_reached(self):
        """Test when max iterations is reached without convergence."""
        initial_state = {"counter": 0}
        
        # Update function that always increments (never converges)
        def update_fn(state):
            return {"counter": state["counter"] + 1}
        
        final_state, converged, iters = fixed_point_iteration(
            initial_state, update_fn, max_iters=5
        )
        
        assert converged is False
        assert iters == 5
        assert final_state["counter"] == 5

    def test_numeric_convergence_with_tolerance(self):
        """Test numeric convergence check with tolerance."""
        initial_state = {"value": 1.0}
        
        # Update function that makes small changes
        iteration_count = [0]
        def update_fn(state):
            iteration_count[0] += 1
            # Decrease by smaller amounts each time
            delta = 0.01 / iteration_count[0]
            return {"value": state["value"] + delta}
        
        final_state, converged, iters = fixed_point_iteration(
            initial_state, update_fn, max_iters=100, tol=0.001
        )
        
        assert converged is True
        assert iters < 100  # Should converge before max

    def test_custom_convergence_check(self):
        """Test with custom convergence function."""
        initial_state = {"a": 0, "b": 0}
        
        def update_fn(state):
            return {"a": state["a"] + 1, "b": state["b"] + 2}
        
        # Custom convergence: stop when a >= 5
        def convergence_check(old_state, new_state):
            return new_state["a"] >= 5
        
        final_state, converged, iters = fixed_point_iteration(
            initial_state,
            update_fn,
            max_iters=20,
            convergence_check=convergence_check
        )
        
        assert converged is True
        assert final_state["a"] >= 5

    def test_empty_initial_state(self):
        """Test with empty initial state."""
        initial_state = {}
        
        def update_fn(state):
            return state
        
        final_state, converged, iters = fixed_point_iteration(
            initial_state, update_fn, max_iters=5
        )
        
        assert converged is True
        assert iters == 1
        assert final_state == {}

    def test_state_is_copied(self):
        """Test that initial state is not modified."""
        initial_state = {"value": 1}
        original_value = initial_state["value"]
        
        def update_fn(state):
            state["value"] = 999  # Try to modify
            return {"value": 2}
        
        final_state, converged, iters = fixed_point_iteration(
            initial_state, update_fn, max_iters=10
        )
        
        # Original should not be modified
        assert initial_state["value"] == original_value

    def test_convergence_with_multiple_keys(self):
        """Test convergence with multiple state keys."""
        initial_state = {"x": 1.0, "y": 2.0, "z": 3.0}
        
        def update_fn(state):
            # Slowly approach target values
            return {
                "x": 0.8 * state["x"] + 0.2 * 5.0,
                "y": 0.8 * state["y"] + 0.2 * 10.0,
                "z": 0.8 * state["z"] + 0.2 * 15.0,
            }
        
        final_state, converged, iters = fixed_point_iteration(
            initial_state, update_fn, max_iters=100, tol=0.01
        )
        
        assert converged is True
        assert abs(final_state["x"] - 5.0) < 0.5
        assert abs(final_state["y"] - 10.0) < 0.5
        assert abs(final_state["z"] - 15.0) < 0.5


class TestNumericConverged:
    """Test the _numeric_converged helper function."""

    def test_converged_within_tolerance(self):
        """Test detection of convergence within tolerance."""
        state1 = {"a": 1.0, "b": 2.0}
        state2 = {"a": 1.001, "b": 2.001}
        
        assert _numeric_converged(state1, state2, tol=0.01) is True

    def test_not_converged_exceeds_tolerance(self):
        """Test detection when tolerance is exceeded."""
        state1 = {"a": 1.0, "b": 2.0}
        state2 = {"a": 1.1, "b": 2.0}
        
        assert _numeric_converged(state1, state2, tol=0.01) is False

    def test_different_keys_not_converged(self):
        """Test that different keys mean not converged."""
        state1 = {"a": 1.0}
        state2 = {"a": 1.0, "b": 2.0}
        
        assert _numeric_converged(state1, state2, tol=0.01) is False

    def test_exact_equality(self):
        """Test exact equality with zero tolerance."""
        state1 = {"a": 1.0, "b": 2.0}
        state2 = {"a": 1.0, "b": 2.0}
        
        assert _numeric_converged(state1, state2, tol=0.0) is True

    def test_non_numeric_values_use_equality(self):
        """Test that non-numeric values fall back to equality check."""
        state1 = {"a": "value", "b": 123}
        state2 = {"a": "value", "b": 123}
        
        assert _numeric_converged(state1, state2, tol=0.01) is True

    def test_non_numeric_values_not_equal(self):
        """Test that non-numeric inequality is detected."""
        state1 = {"a": "value1", "b": 123}
        state2 = {"a": "value2", "b": 123}
        
        assert _numeric_converged(state1, state2, tol=0.01) is False

    def test_empty_states(self):
        """Test convergence with empty states."""
        state1 = {}
        state2 = {}
        
        assert _numeric_converged(state1, state2, tol=0.01) is True

    def test_mixed_numeric_and_non_numeric(self):
        """Test with mixed types."""
        state1 = {"num": 1.0, "str": "value", "int": 42}
        state2 = {"num": 1.001, "str": "value", "int": 42}
        
        assert _numeric_converged(state1, state2, tol=0.01) is True

    def test_large_tolerance(self):
        """Test with large tolerance."""
        state1 = {"a": 1.0}
        state2 = {"a": 5.0}
        
        assert _numeric_converged(state1, state2, tol=10.0) is True

    def test_negative_values(self):
        """Test with negative values."""
        state1 = {"a": -1.0, "b": -2.0}
        state2 = {"a": -1.005, "b": -2.005}
        
        assert _numeric_converged(state1, state2, tol=0.01) is True
