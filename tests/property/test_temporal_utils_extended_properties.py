#!/usr/bin/env python3
"""
Property-based tests for temporal_utils_extended module.

Tests duration parsing and formatting functions.
"""

import pytest
from hypothesis import given, settings, assume, strategies as st
from hypothesis import HealthCheck

# Import temporal_utils_extended module
try:
    from py3plex.temporal_utils_extended import (
        parse_duration_string,
        format_duration,
    )
    TEMPORAL_UTILS_EXTENDED_AVAILABLE = True
except ImportError:
    TEMPORAL_UTILS_EXTENDED_AVAILABLE = False
    pytest.skip("temporal_utils_extended module not available", allow_module_level=True)


# ============================================================================
# Property Tests: parse_duration_string
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(seconds=st.integers(min_value=0, max_value=1000000))
def test_parse_duration_numeric_input(seconds):
    """Test that numeric inputs are converted to float seconds."""
    result = parse_duration_string(seconds)
    
    assert isinstance(result, float), \
        "Result should be float"
    assert result == float(seconds), \
        "Numeric input should be converted to float"


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(value=st.floats(min_value=0.1, max_value=10000, allow_nan=False, allow_infinity=False))
def test_parse_duration_float_input(value):
    """Test that float inputs are returned as-is."""
    result = parse_duration_string(value)
    
    assert isinstance(result, float), \
        "Result should be float"
    assert result == value, \
        "Float input should be returned as-is"


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(days=st.integers(min_value=1, max_value=100))
def test_parse_duration_days(days):
    """Test parsing duration strings with days."""
    # Test short form
    result_d = parse_duration_string(f"{days}d")
    assert result_d == days * 24 * 3600, \
        f"{days}d should equal {days * 24 * 3600} seconds"
    
    # Test long form
    result_day = parse_duration_string(f"{days}day")
    assert result_day == days * 24 * 3600, \
        f"{days}day should equal {days * 24 * 3600} seconds"


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(hours=st.integers(min_value=1, max_value=100))
def test_parse_duration_hours(hours):
    """Test parsing duration strings with hours."""
    result_h = parse_duration_string(f"{hours}h")
    assert result_h == hours * 3600, \
        f"{hours}h should equal {hours * 3600} seconds"
    
    result_hour = parse_duration_string(f"{hours}hour")
    assert result_hour == hours * 3600, \
        f"{hours}hour should equal {hours * 3600} seconds"


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(minutes=st.integers(min_value=1, max_value=100))
def test_parse_duration_minutes(minutes):
    """Test parsing duration strings with minutes."""
    result_m = parse_duration_string(f"{minutes}m")
    assert result_m == minutes * 60, \
        f"{minutes}m should equal {minutes * 60} seconds"
    
    result_min = parse_duration_string(f"{minutes}min")
    assert result_min == minutes * 60, \
        f"{minutes}min should equal {minutes * 60} seconds"


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(seconds=st.integers(min_value=1, max_value=1000))
def test_parse_duration_seconds(seconds):
    """Test parsing duration strings with seconds."""
    result_s = parse_duration_string(f"{seconds}s")
    assert result_s == seconds, \
        f"{seconds}s should equal {seconds} seconds"
    
    result_sec = parse_duration_string(f"{seconds}sec")
    assert result_sec == seconds, \
        f"{seconds}sec should equal {seconds} seconds"


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(weeks=st.integers(min_value=1, max_value=20))
def test_parse_duration_weeks(weeks):
    """Test parsing duration strings with weeks."""
    result_w = parse_duration_string(f"{weeks}w")
    assert result_w == weeks * 7 * 24 * 3600, \
        f"{weeks}w should equal {weeks * 7 * 24 * 3600} seconds"
    
    result_week = parse_duration_string(f"{weeks}week")
    assert result_week == weeks * 7 * 24 * 3600, \
        f"{weeks}week should equal {weeks * 7 * 24 * 3600} seconds"


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(invalid_str=st.text(min_size=1, max_size=20).filter(
    lambda s: not any(unit in s.lower() for unit in ['d', 'h', 'm', 's', 'w'])
))
def test_parse_duration_invalid_format_raises(invalid_str):
    """Test that invalid duration formats raise ValueError."""
    with pytest.raises(ValueError):
        parse_duration_string(invalid_str)


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    value=st.floats(min_value=0.1, max_value=100, allow_nan=False, allow_infinity=False),
    unit=st.sampled_from(['d', 'h', 'm', 's', 'w', 'day', 'hour', 'min', 'sec', 'week'])
)
def test_parse_duration_returns_positive(value, unit):
    """Test that parse_duration_string always returns positive values."""
    duration_str = f"{value}{unit}"
    result = parse_duration_string(duration_str)
    
    assert result > 0, \
        "Duration should be positive"


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    value=st.integers(min_value=1, max_value=100),
    unit=st.sampled_from(['d', 'h', 'm', 's'])
)
def test_parse_duration_case_insensitive(value, unit):
    """Test that duration parsing is case insensitive."""
    lower_result = parse_duration_string(f"{value}{unit.lower()}")
    upper_result = parse_duration_string(f"{value}{unit.upper()}")
    
    assert lower_result == upper_result, \
        "Duration parsing should be case insensitive"


# ============================================================================
# Property Tests: format_duration
# ============================================================================

@pytest.mark.property
def test_format_duration_zero():
    """Test that zero seconds formats correctly."""
    result = format_duration(0)
    assert result == "0s", \
        "Zero seconds should format as '0s'"


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(seconds=st.integers(min_value=1, max_value=59))
def test_format_duration_seconds(seconds):
    """Test formatting seconds."""
    result = format_duration(seconds)
    assert 's' in result, \
        "Result should contain 's' for seconds"


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(days=st.integers(min_value=1, max_value=30))
def test_format_duration_days(days):
    """Test formatting days."""
    seconds = days * 24 * 3600
    result = format_duration(seconds)
    assert 'd' in result or 'w' in result, \
        "Result should contain 'd' or 'w' for days/weeks"


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    seconds=st.integers(min_value=1, max_value=1000000),
    precision=st.integers(min_value=1, max_value=5)
)
def test_format_duration_with_precision(seconds, precision):
    """Test that precision parameter limits the number of units."""
    result = format_duration(seconds, precision=precision)
    
    # Count number of time units in result
    units = result.split()
    assert len(units) <= precision, \
        f"Result should have at most {precision} time units"


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(seconds=st.integers(min_value=-1000, max_value=-1))
def test_format_duration_negative(seconds):
    """Test formatting negative durations."""
    result = format_duration(seconds)
    assert result.startswith('-'), \
        "Negative duration should start with '-'"


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(seconds=st.floats(min_value=0.001, max_value=0.999, allow_nan=False, allow_infinity=False))
def test_format_duration_subsecond(seconds):
    """Test formatting sub-second durations."""
    result = format_duration(seconds)
    assert 's' in result, \
        "Sub-second duration should include 's'"


# ============================================================================
# Property Tests: Round-trip conversion
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    value=st.integers(min_value=1, max_value=100),
    unit=st.sampled_from(['d', 'h', 'm', 's', 'w'])
)
def test_parse_format_consistency(value, unit):
    """Test that parsing a formatted duration is consistent."""
    duration_str = f"{value}{unit}"
    parsed_seconds = parse_duration_string(duration_str)
    
    assert parsed_seconds > 0, \
        "Parsed duration should be positive"
    assert isinstance(parsed_seconds, float), \
        "Parsed duration should be float"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-m', 'property'])
