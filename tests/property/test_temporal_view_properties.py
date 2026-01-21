#!/usr/bin/env python3
"""
Property-based tests for temporal_view module.

Tests TemporalSlice and TemporalMultinetView.
"""

import pytest
from hypothesis import given, settings, assume, strategies as st
from hypothesis import HealthCheck

# Import temporal_view module
try:
    from py3plex.temporal_view import (
        TemporalSlice,
        TemporalMultinetView,
    )
    TEMPORAL_VIEW_AVAILABLE = True
except ImportError:
    TEMPORAL_VIEW_AVAILABLE = False
    pytest.skip("temporal_view module not available", allow_module_level=True)


# ============================================================================
# Property Tests: TemporalSlice
# ============================================================================

@pytest.mark.property
def test_temporal_slice_default_creation():
    """Test that TemporalSlice can be created with defaults."""
    slice_obj = TemporalSlice()
    
    assert slice_obj.t0 is None, \
        "Default t0 should be None"
    assert slice_obj.t1 is None, \
        "Default t1 should be None"


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    t0=st.floats(min_value=0, max_value=1e9, allow_nan=False, allow_infinity=False),
    t1=st.floats(min_value=0, max_value=1e9, allow_nan=False, allow_infinity=False)
)
def test_temporal_slice_creation_with_times(t0, t1):
    """Test that TemporalSlice can be created with specific times."""
    slice_obj = TemporalSlice(t0=t0, t1=t1)
    
    assert slice_obj.t0 == t0, \
        "t0 should match input"
    assert slice_obj.t1 == t1, \
        "t1 should match input"


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(t0=st.floats(min_value=0, max_value=1e9, allow_nan=False, allow_infinity=False))
def test_temporal_slice_with_only_start(t0):
    """Test that TemporalSlice can be created with only start time."""
    slice_obj = TemporalSlice(t0=t0)
    
    assert slice_obj.t0 == t0, \
        "t0 should match input"
    assert slice_obj.t1 is None, \
        "t1 should be None"


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(t1=st.floats(min_value=0, max_value=1e9, allow_nan=False, allow_infinity=False))
def test_temporal_slice_with_only_end(t1):
    """Test that TemporalSlice can be created with only end time."""
    slice_obj = TemporalSlice(t1=t1)
    
    assert slice_obj.t0 is None, \
        "t0 should be None"
    assert slice_obj.t1 == t1, \
        "t1 should match input"


# ============================================================================
# Property Tests: TemporalMultinetView creation
# ============================================================================

class MockMultinetwork:
    """Mock multilayer network for testing."""
    
    def __init__(self):
        self.edges = []
    
    def add_edge(self, source, target, **attrs):
        self.edges.append({
            'source': source,
            'target': target,
            **attrs
        })


@pytest.mark.property
def test_temporal_multinet_view_creation():
    """Test that TemporalMultinetView can be created."""
    mock_net = MockMultinetwork()
    view = TemporalMultinetView(mock_net)
    
    assert view._base is mock_net, \
        "View should reference base network"
    assert view._time_attr == "t", \
        "Default time attribute should be 't'"
    assert view._t_start_attr == "t_start", \
        "Default start attribute should be 't_start'"
    assert view._t_end_attr == "t_end", \
        "Default end attribute should be 't_end'"


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    time_attr=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll'), whitelist_characters='_')),
    t_start_attr=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll'), whitelist_characters='_')),
    t_end_attr=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll'), whitelist_characters='_'))
)
def test_temporal_multinet_view_custom_attrs(time_attr, t_start_attr, t_end_attr):
    """Test that TemporalMultinetView can use custom attribute names."""
    mock_net = MockMultinetwork()
    view = TemporalMultinetView(
        mock_net,
        time_attr=time_attr,
        t_start_attr=t_start_attr,
        t_end_attr=t_end_attr
    )
    
    assert view._time_attr == time_attr, \
        "Custom time attribute should be set"
    assert view._t_start_attr == t_start_attr, \
        "Custom start attribute should be set"
    assert view._t_end_attr == t_end_attr, \
        "Custom end attribute should be set"


@pytest.mark.property
def test_temporal_multinet_view_initial_slice():
    """Test that TemporalMultinetView starts with unbounded slice."""
    mock_net = MockMultinetwork()
    view = TemporalMultinetView(mock_net)
    
    assert view._slice.t0 is None, \
        "Initial slice should have no start bound"
    assert view._slice.t1 is None, \
        "Initial slice should have no end bound"


# ============================================================================
# Property Tests: TemporalMultinetView.with_slice
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    t0=st.floats(min_value=0, max_value=1e9, allow_nan=False, allow_infinity=False),
    t1=st.floats(min_value=0, max_value=1e9, allow_nan=False, allow_infinity=False)
)
def test_temporal_multinet_view_with_slice(t0, t1):
    """Test that with_slice returns a new view with the specified slice."""
    # Ensure t0 <= t1
    if t0 > t1:
        t0, t1 = t1, t0
    
    mock_net = MockMultinetwork()
    view = TemporalMultinetView(mock_net)
    new_view = view.with_slice(t0, t1)
    
    assert isinstance(new_view, TemporalMultinetView), \
        "with_slice should return a TemporalMultinetView"
    assert new_view._slice.t0 == t0, \
        "New view should have correct start time"
    assert new_view._slice.t1 == t1, \
        "New view should have correct end time"


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    t0=st.floats(min_value=0, max_value=1e9, allow_nan=False, allow_infinity=False),
    t1=st.floats(min_value=0, max_value=1e9, allow_nan=False, allow_infinity=False)
)
def test_temporal_multinet_view_with_slice_does_not_modify_original(t0, t1):
    """Test that with_slice doesn't modify the original view."""
    # Ensure t0 <= t1
    if t0 > t1:
        t0, t1 = t1, t0
    
    mock_net = MockMultinetwork()
    view = TemporalMultinetView(mock_net)
    original_t0 = view._slice.t0
    original_t1 = view._slice.t1
    
    new_view = view.with_slice(t0, t1)
    
    assert view._slice.t0 == original_t0, \
        "Original view t0 should not change"
    assert view._slice.t1 == original_t1, \
        "Original view t1 should not change"


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(t0=st.floats(min_value=0, max_value=1e9, allow_nan=False, allow_infinity=False))
def test_temporal_multinet_view_with_slice_none_end(t0):
    """Test that with_slice accepts None for end time."""
    mock_net = MockMultinetwork()
    view = TemporalMultinetView(mock_net)
    new_view = view.with_slice(t0, None)
    
    assert new_view._slice.t0 == t0, \
        "Start time should be set"
    assert new_view._slice.t1 is None, \
        "End time should be None"


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(t1=st.floats(min_value=0, max_value=1e9, allow_nan=False, allow_infinity=False))
def test_temporal_multinet_view_with_slice_none_start(t1):
    """Test that with_slice accepts None for start time."""
    mock_net = MockMultinetwork()
    view = TemporalMultinetView(mock_net)
    new_view = view.with_slice(None, t1)
    
    assert new_view._slice.t0 is None, \
        "Start time should be None"
    assert new_view._slice.t1 == t1, \
        "End time should be set"


# ============================================================================
# Property Tests: TemporalMultinetView.snapshot_at
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(timestamp=st.floats(min_value=0, max_value=1e9, allow_nan=False, allow_infinity=False))
def test_temporal_multinet_view_snapshot_at(timestamp):
    """Test that snapshot_at returns a view with appropriate slice."""
    mock_net = MockMultinetwork()
    view = TemporalMultinetView(mock_net)
    snapshot = view.snapshot_at(timestamp)
    
    assert isinstance(snapshot, TemporalMultinetView), \
        "snapshot_at should return a TemporalMultinetView"
    assert snapshot._slice.t0 == timestamp, \
        "Snapshot should have start bound at timestamp"
    assert snapshot._slice.t1 == timestamp, \
        "Snapshot should have end bound at timestamp (instantaneous)"


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(timestamp=st.floats(min_value=0, max_value=1e9, allow_nan=False, allow_infinity=False))
def test_temporal_multinet_view_snapshot_at_does_not_modify_original(timestamp):
    """Test that snapshot_at doesn't modify the original view."""
    mock_net = MockMultinetwork()
    view = TemporalMultinetView(mock_net)
    original_t0 = view._slice.t0
    original_t1 = view._slice.t1
    
    snapshot = view.snapshot_at(timestamp)
    
    assert view._slice.t0 == original_t0, \
        "Original view t0 should not change"
    assert view._slice.t1 == original_t1, \
        "Original view t1 should not change"


# ============================================================================
# Property Tests: View immutability
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    t0_1=st.floats(min_value=0, max_value=1e8, allow_nan=False, allow_infinity=False),
    t1_1=st.floats(min_value=0, max_value=1e8, allow_nan=False, allow_infinity=False),
    t0_2=st.floats(min_value=0, max_value=1e8, allow_nan=False, allow_infinity=False),
    t1_2=st.floats(min_value=0, max_value=1e8, allow_nan=False, allow_infinity=False)
)
def test_temporal_multinet_view_multiple_slices_independent(t0_1, t1_1, t0_2, t1_2):
    """Test that multiple slices are independent."""
    # Ensure valid ranges
    if t0_1 > t1_1:
        t0_1, t1_1 = t1_1, t0_1
    if t0_2 > t1_2:
        t0_2, t1_2 = t1_2, t0_2
    
    mock_net = MockMultinetwork()
    view = TemporalMultinetView(mock_net)
    
    slice1 = view.with_slice(t0_1, t1_1)
    slice2 = view.with_slice(t0_2, t1_2)
    
    assert slice1._slice.t0 == t0_1, \
        "First slice should have its own t0"
    assert slice1._slice.t1 == t1_1, \
        "First slice should have its own t1"
    assert slice2._slice.t0 == t0_2, \
        "Second slice should have its own t0"
    assert slice2._slice.t1 == t1_2, \
        "Second slice should have its own t1"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-m', 'property'])
