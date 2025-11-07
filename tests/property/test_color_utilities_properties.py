#!/usr/bin/env python3
"""
Property-based tests for py3plex color utility functions.

This module tests pure color conversion and gradient functions from
py3plex.visualization.colors using Hypothesis.

TARGET FUNCTIONS (from py3plex/visualization/colors.py):
1. hex_to_RGB(hex: str) -> List[int]
2. RGB_to_hex(RGB: List[int]) -> str  
3. linear_gradient(start_hex: str, finish_hex: str, n: int) -> Dict

PROPERTIES TESTED:
- Round-trip: RGB -> hex -> RGB preserves values
- Round-trip: hex -> RGB -> hex preserves values (with normalization)
- Structural: hex_to_RGB returns 3-element list with values in [0, 255]
- Structural: RGB_to_hex returns 7-character string starting with '#'
- Monotone: linear_gradient interpolates smoothly between colors
- Structural: gradient has exactly n colors
- Boundary: gradient starts with start_hex and ends with finish_hex (or close to it)
"""

import pytest
from hypothesis import assume, given, strategies as st

from py3plex.visualization.colors import RGB_to_hex, hex_to_RGB, linear_gradient


# ============================================================================
# Strategies for color data
# ============================================================================

def valid_hex_colors():
    """Generate valid 6-digit hex color strings."""
    return st.builds(
        lambda r, g, b: f"#{r:02X}{g:02X}{b:02X}",
        st.integers(min_value=0, max_value=255),
        st.integers(min_value=0, max_value=255),
        st.integers(min_value=0, max_value=255)
    )


def valid_rgb_triples():
    """Generate valid RGB triples [R, G, B] with values in [0, 255]."""
    return st.lists(
        st.integers(min_value=0, max_value=255),
        min_size=3,
        max_size=3
    )


# ============================================================================
# Property Tests: hex_to_RGB
# ============================================================================

@pytest.mark.property
@given(hex_color=valid_hex_colors())
def test_hex_to_RGB_returns_three_values(hex_color):
    """Property: hex_to_RGB always returns exactly 3 RGB values."""
    result = hex_to_RGB(hex_color)
    assert len(result) == 3, f"Expected 3 RGB values, got {len(result)}"


@pytest.mark.property
@given(hex_color=valid_hex_colors())
def test_hex_to_RGB_values_in_valid_range(hex_color):
    """Property: hex_to_RGB returns values in [0, 255]."""
    result = hex_to_RGB(hex_color)
    for val in result:
        assert 0 <= val <= 255, f"RGB value {val} out of range [0, 255]"


@pytest.mark.property
@given(hex_color=valid_hex_colors())
def test_hex_to_RGB_returns_integers(hex_color):
    """Property: hex_to_RGB returns integer values."""
    result = hex_to_RGB(hex_color)
    for val in result:
        assert isinstance(val, int), f"Expected int, got {type(val)}"


# ============================================================================
# Property Tests: RGB_to_hex
# ============================================================================

@pytest.mark.property
@given(rgb=valid_rgb_triples())
def test_RGB_to_hex_returns_hash_prefixed_string(rgb):
    """Property: RGB_to_hex returns string starting with '#'."""
    result = RGB_to_hex(rgb)
    assert result.startswith('#'), f"Expected hex string to start with '#', got {result}"


@pytest.mark.property
@given(rgb=valid_rgb_triples())
def test_RGB_to_hex_returns_seven_chars(rgb):
    """Property: RGB_to_hex returns 7-character string (#RRGGBB)."""
    result = RGB_to_hex(rgb)
    assert len(result) == 7, f"Expected 7 characters, got {len(result)}"


@pytest.mark.property
@given(rgb=valid_rgb_triples())
def test_RGB_to_hex_returns_valid_hex_digits(rgb):
    """Property: RGB_to_hex returns valid hexadecimal string."""
    result = RGB_to_hex(rgb)
    hex_part = result[1:]  # Skip the '#'
    try:
        int(hex_part, 16)  # Should parse as hexadecimal
    except ValueError:
        pytest.fail(f"Invalid hex string: {result}")


# ============================================================================
# Property Tests: Round-trip conversions
# ============================================================================

@pytest.mark.property
@given(rgb=valid_rgb_triples())
def test_roundtrip_RGB_to_hex_to_RGB(rgb):
    """Property: RGB -> hex -> RGB is identity (round-trip preserves values)."""
    hex_color = RGB_to_hex(rgb)
    recovered_rgb = hex_to_RGB(hex_color)
    assert recovered_rgb == rgb, f"Round-trip failed: {rgb} -> {hex_color} -> {recovered_rgb}"


@pytest.mark.property
@given(hex_color=valid_hex_colors())
def test_roundtrip_hex_to_RGB_to_hex(hex_color):
    """Property: hex -> RGB -> hex is identity (with uppercase normalization)."""
    rgb = hex_to_RGB(hex_color)
    recovered_hex = RGB_to_hex(rgb)
    # Normalize to uppercase for comparison
    assert recovered_hex.upper() == hex_color.upper(), \
        f"Round-trip failed: {hex_color} -> {rgb} -> {recovered_hex}"


# ============================================================================
# Property Tests: linear_gradient
# ============================================================================

@pytest.mark.property
@given(
    start_hex=valid_hex_colors(),
    finish_hex=valid_hex_colors(),
    n=st.integers(min_value=2, max_value=20)
)
def test_linear_gradient_returns_n_colors(start_hex, finish_hex, n):
    """Property: linear_gradient returns exactly n colors."""
    result = linear_gradient(start_hex, finish_hex, n)
    
    # Check all keys exist
    assert 'hex' in result
    assert 'r' in result
    assert 'g' in result
    assert 'b' in result
    
    # Check all have n elements
    assert len(result['hex']) == n, f"Expected {n} hex colors, got {len(result['hex'])}"
    assert len(result['r']) == n, f"Expected {n} R values, got {len(result['r'])}"
    assert len(result['g']) == n, f"Expected {n} G values, got {len(result['g'])}"
    assert len(result['b']) == n, f"Expected {n} B values, got {len(result['b'])}"


@pytest.mark.property
@given(
    start_hex=valid_hex_colors(),
    finish_hex=valid_hex_colors(),
    n=st.integers(min_value=2, max_value=20)
)
def test_linear_gradient_starts_with_start_color(start_hex, finish_hex, n):
    """Property: linear_gradient first color matches start_hex."""
    result = linear_gradient(start_hex, finish_hex, n)
    start_rgb = hex_to_RGB(start_hex)
    
    assert result['r'][0] == start_rgb[0], "First R value doesn't match start color"
    assert result['g'][0] == start_rgb[1], "First G value doesn't match start color"
    assert result['b'][0] == start_rgb[2], "First B value doesn't match start color"


@pytest.mark.property
@given(
    start_hex=valid_hex_colors(),
    finish_hex=valid_hex_colors(),
    n=st.integers(min_value=2, max_value=20)
)
def test_linear_gradient_ends_with_finish_color(start_hex, finish_hex, n):
    """Property: linear_gradient last color matches finish_hex (approximately)."""
    result = linear_gradient(start_hex, finish_hex, n)
    finish_rgb = hex_to_RGB(finish_hex)
    
    # Allow small tolerance due to interpolation rounding
    assert abs(result['r'][-1] - finish_rgb[0]) <= 1, "Last R value doesn't match finish color"
    assert abs(result['g'][-1] - finish_rgb[1]) <= 1, "Last G value doesn't match finish color"
    assert abs(result['b'][-1] - finish_rgb[2]) <= 1, "Last B value doesn't match finish color"


@pytest.mark.property
@given(
    start_hex=valid_hex_colors(),
    finish_hex=valid_hex_colors(),
    n=st.integers(min_value=2, max_value=20)
)
def test_linear_gradient_values_in_valid_range(start_hex, finish_hex, n):
    """Property: linear_gradient RGB values are in [0, 255]."""
    result = linear_gradient(start_hex, finish_hex, n)
    
    for r in result['r']:
        assert 0 <= r <= 255, f"R value {r} out of range"
    for g in result['g']:
        assert 0 <= g <= 255, f"G value {g} out of range"
    for b in result['b']:
        assert 0 <= b <= 255, f"B value {b} out of range"


@pytest.mark.property
@given(
    start_hex=valid_hex_colors(),
    finish_hex=valid_hex_colors(),
    n=st.integers(min_value=2, max_value=20)
)
def test_linear_gradient_monotone_property(start_hex, finish_hex, n):
    """Property: linear_gradient interpolates monotonically (when start != finish per channel)."""
    result = linear_gradient(start_hex, finish_hex, n)
    start_rgb = hex_to_RGB(start_hex)
    finish_rgb = hex_to_RGB(finish_hex)
    
    # Check monotonicity for each channel (R, G, B)
    for channel_idx, channel_name in enumerate(['r', 'g', 'b']):
        channel_values = result[channel_name]
        start_val = start_rgb[channel_idx]
        finish_val = finish_rgb[channel_idx]
        
        if start_val < finish_val:
            # Should be non-decreasing
            for i in range(len(channel_values) - 1):
                assert channel_values[i] <= channel_values[i + 1] + 1, \
                    f"Channel {channel_name} not monotone increasing: {channel_values}"
        elif start_val > finish_val:
            # Should be non-increasing
            for i in range(len(channel_values) - 1):
                assert channel_values[i] >= channel_values[i + 1] - 1, \
                    f"Channel {channel_name} not monotone decreasing: {channel_values}"
        # If start_val == finish_val, all values should be approximately equal


@pytest.mark.property
@given(
    start_hex=valid_hex_colors(),
    n=st.integers(min_value=2, max_value=20)
)
def test_linear_gradient_to_white_default(start_hex, n):
    """Property: linear_gradient with default finish_hex uses white (#FFFFFF)."""
    result = linear_gradient(start_hex, n=n)
    
    # Last color should be close to white (255, 255, 255)
    assert result['r'][-1] >= 254, "Gradient to white should end with R ~255"
    assert result['g'][-1] >= 254, "Gradient to white should end with G ~255"
    assert result['b'][-1] >= 254, "Gradient to white should end with B ~255"


@pytest.mark.property
@given(hex_color=valid_hex_colors())
def test_linear_gradient_single_step_returns_start_color(hex_color):
    """Property: linear_gradient with n=1 returns just the start color."""
    result = linear_gradient(hex_color, hex_color, n=1)
    start_rgb = hex_to_RGB(hex_color)
    
    assert len(result['hex']) == 1
    assert result['r'][0] == start_rgb[0]
    assert result['g'][0] == start_rgb[1]
    assert result['b'][0] == start_rgb[2]


# ============================================================================
# Edge cases and error handling
# ============================================================================

@pytest.mark.property
@given(
    hex_color=valid_hex_colors(),
    invalid_n=st.integers(max_value=0)
)
def test_linear_gradient_invalid_n_handling(hex_color, invalid_n):
    """Property: linear_gradient with n <= 0 may fail or return empty (error behavior test)."""
    # This documents current behavior - may raise or return unexpected results
    # Actual behavior depends on implementation
    try:
        result = linear_gradient(hex_color, hex_color, n=invalid_n)
        # If it doesn't raise, check what it returns
        # Current implementation may have issues with n <= 0
    except (ValueError, ZeroDivisionError, IndexError):
        # Expected behavior for invalid input
        pass
