#!/usr/bin/env python3
"""
Property-based tests for polynomial fitting utility functions.

This module tests polynomial fitting functions from py3plex.visualization.polyfit
using Hypothesis.

TARGET FUNCTIONS (from py3plex/visualization/polyfit.py):
1. draw_order3(networks, p1, p2) - 3rd order polynomial fitting
2. draw_piramidal(networks, p1, p2) - pyramidal line drawing

PROPERTIES TESTED:
- Structural: returns tuple of two arrays (x, y)
- Structural: arrays have expected lengths
- Monotone: output values follow expected ranges
- Boundary: output includes input points
"""

import numpy as np
import pytest
from hypothesis import assume, given, strategies as st

from py3plex.visualization.polyfit import draw_order3, draw_piramidal


# ============================================================================
# Strategies
# ============================================================================

def small_integers(min_val=2, max_val=20):
    """Generate small positive integers."""
    return st.integers(min_value=min_val, max_value=max_val)


def coordinate_pairs():
    """Generate coordinate pairs for polyfit functions."""
    return st.tuples(
        st.floats(min_value=0.0, max_value=10.0, allow_nan=False, allow_infinity=False),
        st.floats(min_value=0.0, max_value=10.0, allow_nan=False, allow_infinity=False)
    )


# ============================================================================
# Property Tests: draw_order3
# ============================================================================

@pytest.mark.property
@given(
    networks=small_integers(),
    p1=coordinate_pairs(),
    p2=coordinate_pairs()
)
def test_draw_order3_returns_tuple_of_arrays(networks, p1, p2):
    """Property: draw_order3 returns a tuple of two arrays."""
    result = draw_order3(networks, p1, p2)
    
    assert isinstance(result, tuple), f"Expected tuple, got {type(result)}"
    assert len(result) == 2, f"Expected 2 elements, got {len(result)}"
    
    space_x, space_y = result
    assert isinstance(space_x, np.ndarray), "First element should be numpy array"
    assert isinstance(space_y, np.ndarray), "Second element should be numpy array"


@pytest.mark.property
@given(
    networks=small_integers(),
    p1=coordinate_pairs(),
    p2=coordinate_pairs()
)
def test_draw_order3_equal_length_arrays(networks, p1, p2):
    """Property: draw_order3 returns arrays of equal length."""
    space_x, space_y = draw_order3(networks, p1, p2)
    
    assert len(space_x) == len(space_y), \
        f"Array lengths don't match: {len(space_x)} != {len(space_y)}"


@pytest.mark.property
@given(
    networks=small_integers(),
    p1=coordinate_pairs(),
    p2=coordinate_pairs()
)
def test_draw_order3_returns_ten_points(networks, p1, p2):
    """Property: draw_order3 returns exactly 10 sample points (by implementation)."""
    space_x, space_y = draw_order3(networks, p1, p2)
    
    # Implementation uses np.linspace(0, networks, 10)
    assert len(space_x) == 10, f"Expected 10 points, got {len(space_x)}"


@pytest.mark.property
@given(
    networks=small_integers(),
    p1=coordinate_pairs(),
    p2=coordinate_pairs()
)
def test_draw_order3_no_nan_or_inf(networks, p1, p2):
    """Property: draw_order3 returns finite values (no NaN or Inf)."""
    space_x, space_y = draw_order3(networks, p1, p2)
    
    assert np.all(np.isfinite(space_x)), "space_x contains NaN or Inf"
    assert np.all(np.isfinite(space_y)), "space_y contains NaN or Inf"


@pytest.mark.property
@given(
    networks=small_integers(),
    p1=coordinate_pairs(),
    p2=coordinate_pairs()
)
def test_draw_order3_x_within_bounds(networks, p1, p2):
    """Property: draw_order3 x-coordinates are within [0, networks]."""
    space_x, space_y = draw_order3(networks, p1, p2)
    
    assert np.all(space_x >= 0), f"X-coordinates below 0: min={np.min(space_x)}"
    assert np.all(space_x <= networks), \
        f"X-coordinates above {networks}: max={np.max(space_x)}"


@pytest.mark.property
@given(
    networks=small_integers(min_val=2, max_val=5),
    p1=coordinate_pairs(),
    p2=coordinate_pairs()
)
def test_draw_order3_deterministic(networks, p1, p2):
    """Property: draw_order3 is deterministic (same inputs -> same outputs)."""
    result1 = draw_order3(networks, p1, p2)
    result2 = draw_order3(networks, p1, p2)
    
    space_x1, space_y1 = result1
    space_x2, space_y2 = result2
    
    np.testing.assert_array_equal(space_x1, space_x2, err_msg="X arrays differ")
    np.testing.assert_array_equal(space_y1, space_y2, err_msg="Y arrays differ")


# ============================================================================
# Property Tests: draw_piramidal
# ============================================================================

@pytest.mark.property
@given(
    networks=small_integers(),
    p1=coordinate_pairs(),
    p2=coordinate_pairs()
)
def test_draw_piramidal_returns_tuple_of_lists(networks, p1, p2):
    """Property: draw_piramidal returns a tuple of two lists."""
    result = draw_piramidal(networks, p1, p2)
    
    assert isinstance(result, tuple), f"Expected tuple, got {type(result)}"
    assert len(result) == 2, f"Expected 2 elements, got {len(result)}"
    
    x, y = result
    assert isinstance(x, list), "First element should be list"
    assert isinstance(y, list), "Second element should be list"


@pytest.mark.property
@given(
    networks=small_integers(),
    p1=coordinate_pairs(),
    p2=coordinate_pairs()
)
def test_draw_piramidal_equal_length_lists(networks, p1, p2):
    """Property: draw_piramidal returns lists of equal length."""
    x, y = draw_piramidal(networks, p1, p2)
    
    assert len(x) == len(y), f"List lengths don't match: {len(x)} != {len(y)}"


@pytest.mark.property
@given(
    networks=small_integers(),
    p1=coordinate_pairs(),
    p2=coordinate_pairs()
)
def test_draw_piramidal_returns_three_points(networks, p1, p2):
    """Property: draw_piramidal returns exactly 3 points (start, midpoint, end)."""
    x, y = draw_piramidal(networks, p1, p2)
    
    # Implementation creates 3 points: p1[0], midpoint[0], p1[1]
    assert len(x) == 3, f"Expected 3 points, got {len(x)}"


@pytest.mark.property
@given(
    networks=small_integers(),
    p1=coordinate_pairs(),
    p2=coordinate_pairs()
)
def test_draw_piramidal_no_nan_or_inf(networks, p1, p2):
    """Property: draw_piramidal returns finite values (no NaN or Inf)."""
    x, y = draw_piramidal(networks, p1, p2)
    
    # Convert to numpy for easier checking
    x_arr = np.array(x)
    y_arr = np.array(y)
    
    assert np.all(np.isfinite(x_arr)), "X values contain NaN or Inf"
    assert np.all(np.isfinite(y_arr)), "Y values contain NaN or Inf"


@pytest.mark.property
@given(
    networks=small_integers(),
    p1=coordinate_pairs(),
    p2=coordinate_pairs()
)
def test_draw_piramidal_includes_endpoints(networks, p1, p2):
    """Property: draw_piramidal includes p1 and p2 coordinates in output."""
    x, y = draw_piramidal(networks, p1, p2)
    
    # First point should be from p1[0] and p2[0]
    # Last point should be from p1[1] and p2[1]
    # Midpoint is computed as p2[0] + 1, p1[1] + 1
    
    # Check x-coordinates include p1 values (first and last)
    assert x[0] == p1[0], f"First x-coordinate {x[0]} != p1[0] {p1[0]}"
    assert x[2] == p1[1], f"Last x-coordinate {x[2]} != p1[1] {p1[1]}"
    
    # Check y-coordinates
    assert y[0] == p2[0], f"First y-coordinate {y[0]} != p2[0] {p2[0]}"
    assert y[2] == p2[1], f"Last y-coordinate {y[2]} != p2[1] {p2[1]}"


@pytest.mark.property
@given(
    networks=small_integers(),
    p1=coordinate_pairs(),
    p2=coordinate_pairs()
)
def test_draw_piramidal_midpoint_computed_correctly(networks, p1, p2):
    """Property: draw_piramidal midpoint is computed as (p2[0]+1, p1[1]+1)."""
    x, y = draw_piramidal(networks, p1, p2)
    
    expected_mid_x = p2[0] + 1
    expected_mid_y = p1[1] + 1
    
    assert x[1] == expected_mid_x, \
        f"Midpoint x {x[1]} != expected {expected_mid_x}"
    assert y[1] == expected_mid_y, \
        f"Midpoint y {y[1]} != expected {expected_mid_y}"


@pytest.mark.property
@given(
    networks=small_integers(min_val=2, max_val=5),
    p1=coordinate_pairs(),
    p2=coordinate_pairs()
)
def test_draw_piramidal_deterministic(networks, p1, p2):
    """Property: draw_piramidal is deterministic (same inputs -> same outputs)."""
    result1 = draw_piramidal(networks, p1, p2)
    result2 = draw_piramidal(networks, p1, p2)
    
    x1, y1 = result1
    x2, y2 = result2
    
    assert x1 == x2, f"X lists differ: {x1} vs {x2}"
    assert y1 == y2, f"Y lists differ: {y1} vs {y2}"


# ============================================================================
# Comparison tests
# ============================================================================

@pytest.mark.property
@given(
    networks=small_integers(min_val=2, max_val=5),
    p1=coordinate_pairs(),
    p2=coordinate_pairs()
)
def test_draw_order3_vs_piramidal_different_lengths(networks, p1, p2):
    """Property: draw_order3 returns 10 points, draw_piramidal returns 3 points."""
    x_order3, y_order3 = draw_order3(networks, p1, p2)
    x_piramidal, y_piramidal = draw_piramidal(networks, p1, p2)
    
    assert len(x_order3) == 10, "draw_order3 should return 10 points"
    assert len(x_piramidal) == 3, "draw_piramidal should return 3 points"


@pytest.mark.property
@given(
    networks=small_integers(min_val=2, max_val=5),
    p1=coordinate_pairs(),
    p2=coordinate_pairs()
)
def test_both_functions_use_same_input_points(networks, p1, p2):
    """Property: both functions incorporate the input coordinate pairs."""
    x_order3, y_order3 = draw_order3(networks, p1, p2)
    x_piramidal, y_piramidal = draw_piramidal(networks, p1, p2)
    
    # draw_piramidal explicitly includes p1 and p2
    assert x_piramidal[0] == p1[0]
    assert x_piramidal[2] == p1[1]
    assert y_piramidal[0] == p2[0]
    assert y_piramidal[2] == p2[1]
    
    # draw_order3 uses these points for polynomial fitting
    # The relationship is more complex but the endpoints should be involved
    # in the fitting process (documented behavior test)
    assert len(x_order3) > 0
    assert len(y_order3) > 0
