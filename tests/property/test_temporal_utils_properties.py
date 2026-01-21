#!/usr/bin/env python3
"""
Property-based tests for temporal_utils module.

Tests EdgeTimeInterval and temporal utility functions.
"""

import pytest
from hypothesis import given, settings, assume, strategies as st
from hypothesis import HealthCheck

# Import temporal_utils module
try:
    from py3plex.temporal_utils import (
        EdgeTimeInterval,
        extract_edge_time,
    )
    TEMPORAL_UTILS_AVAILABLE = True
except ImportError:
    TEMPORAL_UTILS_AVAILABLE = False
    pytest.skip("temporal_utils module not available", allow_module_level=True)


# ============================================================================
# Property Tests: EdgeTimeInterval
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    start=st.floats(min_value=0, max_value=1e9, allow_nan=False, allow_infinity=False),
    end=st.floats(min_value=0, max_value=1e9, allow_nan=False, allow_infinity=False)
)
def test_edge_time_interval_creation(start, end):
    """Test that EdgeTimeInterval can be created with valid timestamps."""
    interval = EdgeTimeInterval(start=start, end=end)
    
    assert interval.start == start, \
        "Start time should match input"
    assert interval.end == end, \
        "End time should match input"


@pytest.mark.property
def test_edge_time_interval_atemporal():
    """Test that atemporal intervals (None, None) can be created."""
    interval = EdgeTimeInterval(start=None, end=None)
    
    assert interval.start is None, \
        "Atemporal interval should have None start"
    assert interval.end is None, \
        "Atemporal interval should have None end"


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    start=st.floats(min_value=0, max_value=1e9, allow_nan=False, allow_infinity=False),
    end=st.floats(min_value=0, max_value=1e9, allow_nan=False, allow_infinity=False)
)
def test_edge_time_interval_overlaps_itself(start, end):
    """Test that an interval overlaps with itself."""
    # Ensure start <= end
    if start > end:
        start, end = end, start
    
    interval = EdgeTimeInterval(start=start, end=end)
    
    assert interval.overlaps(start, end), \
        "Interval should overlap with itself"


@pytest.mark.property
def test_atemporal_interval_overlaps_all():
    """Test that atemporal intervals overlap with any query range."""
    interval = EdgeTimeInterval(start=None, end=None)
    
    # Should overlap with any range
    assert interval.overlaps(0, 100), \
        "Atemporal interval should overlap with any range"
    assert interval.overlaps(None, None), \
        "Atemporal interval should overlap with unbounded range"
    assert interval.overlaps(None, 100), \
        "Atemporal interval should overlap with half-bounded range"


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(timestamp=st.floats(min_value=0, max_value=1e9, allow_nan=False, allow_infinity=False))
def test_point_interval_overlaps_containing_range(timestamp):
    """Test that a point interval overlaps with ranges containing it."""
    interval = EdgeTimeInterval(start=timestamp, end=timestamp)
    
    # Should overlap with range containing the point
    assert interval.overlaps(timestamp - 10, timestamp + 10), \
        "Point interval should overlap with containing range"
    assert interval.overlaps(timestamp, timestamp), \
        "Point interval should overlap with exact match"


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    start1=st.floats(min_value=0, max_value=1e8, allow_nan=False, allow_infinity=False),
    start2=st.floats(min_value=0, max_value=1e8, allow_nan=False, allow_infinity=False)
)
def test_disjoint_intervals_dont_overlap(start1, start2):
    """Test that clearly disjoint intervals don't overlap."""
    # Create two intervals with gap
    assume(abs(start2 - start1) > 1000)  # Ensure significant gap
    
    interval1 = EdgeTimeInterval(start=start1, end=start1 + 100)
    
    if start2 > start1:
        # start2 is after interval1
        assert not interval1.overlaps(start2 + 200, start2 + 300), \
            "Interval should not overlap with later disjoint range"
    else:
        # start2 is before interval1
        assert not interval1.overlaps(start2, start2 + 100), \
            "Interval should not overlap with earlier disjoint range"


# ============================================================================
# Property Tests: extract_edge_time
# ============================================================================

@pytest.mark.property
def test_extract_edge_time_atemporal():
    """Test extracting time from atemporal edge."""
    attrs = {'weight': 1.0, 'label': 'test'}
    interval = extract_edge_time(attrs)
    
    assert interval.start is None, \
        "Atemporal edge should have None start"
    assert interval.end is None, \
        "Atemporal edge should have None end"


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(timestamp=st.floats(min_value=0, max_value=1e9, allow_nan=False, allow_infinity=False))
def test_extract_edge_time_point(timestamp):
    """Test extracting time from point-in-time edge."""
    attrs = {'t': timestamp}
    interval = extract_edge_time(attrs)
    
    assert interval.start == timestamp, \
        "Point edge start should match 't' attribute"
    assert interval.end == timestamp, \
        "Point edge end should match 't' attribute (same as start)"


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    start=st.floats(min_value=0, max_value=1e9, allow_nan=False, allow_infinity=False),
    end=st.floats(min_value=0, max_value=1e9, allow_nan=False, allow_infinity=False)
)
def test_extract_edge_time_interval(start, end):
    """Test extracting time from interval edge."""
    # Ensure start <= end
    if start > end:
        start, end = end, start
    
    attrs = {'t_start': start, 't_end': end}
    interval = extract_edge_time(attrs)
    
    assert interval.start == start, \
        "Interval edge start should match 't_start' attribute"
    assert interval.end == end, \
        "Interval edge end should match 't_end' attribute"


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(start=st.floats(min_value=0, max_value=1e9, allow_nan=False, allow_infinity=False))
def test_extract_edge_time_unbounded_end(start):
    """Test extracting time from interval with only start."""
    attrs = {'t_start': start}
    interval = extract_edge_time(attrs)
    
    assert interval.start == start, \
        "Interval with only start should use that start"
    assert interval.end == float('inf'), \
        "Interval with only start should have infinite end"


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(end=st.floats(min_value=0, max_value=1e9, allow_nan=False, allow_infinity=False))
def test_extract_edge_time_unbounded_start(end):
    """Test extracting time from interval with only end."""
    attrs = {'t_end': end}
    interval = extract_edge_time(attrs)
    
    assert interval.start == float('-inf'), \
        "Interval with only end should have negative infinite start"
    assert interval.end == end, \
        "Interval with only end should use that end"


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    t=st.floats(min_value=0, max_value=1e9, allow_nan=False, allow_infinity=False),
    t_start=st.floats(min_value=0, max_value=1e9, allow_nan=False, allow_infinity=False),
    t_end=st.floats(min_value=0, max_value=1e9, allow_nan=False, allow_infinity=False)
)
def test_extract_edge_time_interval_takes_precedence(t, t_start, t_end):
    """Test that interval form (t_start/t_end) takes precedence over point form (t)."""
    # Ensure start <= end
    if t_start > t_end:
        t_start, t_end = t_end, t_start
    
    attrs = {'t': t, 't_start': t_start, 't_end': t_end}
    interval = extract_edge_time(attrs)
    
    # Should use interval form
    assert interval.start == t_start, \
        "When both present, should use t_start"
    assert interval.end == t_end, \
        "When both present, should use t_end"


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(timestamp=st.integers(min_value=0, max_value=int(1e9)))
def test_extract_edge_time_accepts_int(timestamp):
    """Test that extract_edge_time accepts integer timestamps."""
    attrs = {'t': timestamp}
    interval = extract_edge_time(attrs)
    
    assert interval.start == float(timestamp), \
        "Integer timestamp should be converted to float"
    assert interval.end == float(timestamp), \
        "Integer timestamp should be converted to float"


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(timestamp=st.floats(min_value=0, max_value=1e9, allow_nan=False, allow_infinity=False))
def test_extract_edge_time_string_timestamp(timestamp):
    """Test that extract_edge_time accepts string timestamps."""
    attrs = {'t': str(timestamp)}
    interval = extract_edge_time(attrs)
    
    assert abs(interval.start - timestamp) < 1e-6, \
        "String timestamp should be parsed to float"
    assert abs(interval.end - timestamp) < 1e-6, \
        "String timestamp should be parsed to float"


# ============================================================================
# Property Tests: Combined behavior
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    t1=st.floats(min_value=0, max_value=1e8, allow_nan=False, allow_infinity=False),
    t2=st.floats(min_value=0, max_value=1e8, allow_nan=False, allow_infinity=False),
    query_t=st.floats(min_value=0, max_value=1e8, allow_nan=False, allow_infinity=False)
)
def test_point_edge_overlap_consistency(t1, t2, query_t):
    """Test that point edges overlap correctly with query ranges."""
    # Create point edge
    attrs = {'t': t1}
    interval = extract_edge_time(attrs)
    
    # Check overlap with query range [t2, query_t]
    if t2 > query_t:
        t2, query_t = query_t, t2
    
    expected_overlap = (t2 <= t1 <= query_t)
    actual_overlap = interval.overlaps(t2, query_t)
    
    assert actual_overlap == expected_overlap, \
        "Point edge overlap should match expected behavior"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-m', 'property'])
