"""
Tests for py3plex.temporal_utils module.

This module tests temporal utility functions for multilayer networks.
"""

import pytest
import datetime
from py3plex.temporal_utils import (
    EdgeTimeInterval,
    _parse_time,
    extract_edge_time,
)


class TestEdgeTimeInterval:
    """Test the EdgeTimeInterval class."""

    def test_atemporal_interval_overlaps_everything(self):
        """Atemporal intervals (None, None) should overlap with any query."""
        interval = EdgeTimeInterval(None, None)
        assert interval.overlaps(None, None)
        assert interval.overlaps(0.0, 100.0)
        assert interval.overlaps(100.0, 200.0)

    def test_temporal_interval_overlaps_unbounded_query(self):
        """Temporal intervals should overlap with unbounded queries."""
        interval = EdgeTimeInterval(50.0, 150.0)
        assert interval.overlaps(None, None)

    def test_interval_overlaps_with_start_bound(self):
        """Test overlap with query having only start bound."""
        interval = EdgeTimeInterval(50.0, 150.0)
        assert interval.overlaps(100.0, None)
        assert interval.overlaps(0.0, None)
        assert not interval.overlaps(200.0, None)

    def test_interval_overlaps_with_end_bound(self):
        """Test overlap with query having only end bound."""
        interval = EdgeTimeInterval(50.0, 150.0)
        assert interval.overlaps(None, 100.0)
        assert interval.overlaps(None, 200.0)
        assert not interval.overlaps(None, 25.0)

    def test_interval_overlaps_with_both_bounds(self):
        """Test overlap with fully bounded query."""
        interval = EdgeTimeInterval(50.0, 150.0)
        # Complete overlap
        assert interval.overlaps(0.0, 200.0)
        # Partial overlap from left
        assert interval.overlaps(25.0, 75.0)
        # Partial overlap from right
        assert interval.overlaps(125.0, 175.0)
        # Query inside interval
        assert interval.overlaps(75.0, 125.0)
        # No overlap (before)
        assert not interval.overlaps(0.0, 25.0)
        # No overlap (after)
        assert not interval.overlaps(175.0, 200.0)

    def test_point_interval(self):
        """Test interval where start equals end."""
        interval = EdgeTimeInterval(100.0, 100.0)
        assert interval.overlaps(50.0, 150.0)
        assert interval.overlaps(100.0, 100.0)
        assert not interval.overlaps(0.0, 50.0)
        assert not interval.overlaps(150.0, 200.0)


class TestParseTime:
    """Test the _parse_time function."""

    def test_parse_int_timestamp(self):
        """Test parsing integer timestamp."""
        assert _parse_time(1234567890) == 1234567890.0

    def test_parse_float_timestamp(self):
        """Test parsing float timestamp."""
        assert _parse_time(1234567890.5) == 1234567890.5

    def test_parse_iso_string(self):
        """Test parsing ISO format string."""
        # ISO format string
        timestamp = _parse_time("2009-02-13T23:31:30Z")
        expected = datetime.datetime(2009, 2, 13, 23, 31, 30).timestamp()
        assert timestamp == expected

    def test_parse_datetime_object(self):
        """Test parsing datetime object."""
        dt = datetime.datetime(2009, 2, 13, 23, 31, 30)
        assert _parse_time(dt) == dt.timestamp()

    def test_parse_invalid_string_raises_error(self):
        """Test that invalid string raises ValueError."""
        with pytest.raises(ValueError):
            _parse_time("not a valid timestamp")


class TestExtractEdgeTime:
    """Test the extract_edge_time function."""

    def test_extract_from_point_timestamp(self):
        """Test extraction from edge with 't' attribute."""
        edge = {'source': 'A', 'target': 'B', 't': 100.0}
        interval = extract_edge_time(edge)
        assert interval.start == 100.0
        assert interval.end == 100.0

    def test_extract_from_interval_timestamps(self):
        """Test extraction from edge with 't_start' and 't_end' attributes."""
        edge = {'source': 'A', 'target': 'B', 't_start': 50.0, 't_end': 150.0}
        interval = extract_edge_time(edge)
        assert interval.start == 50.0
        assert interval.end == 150.0

    def test_interval_takes_precedence_over_point(self):
        """Test that interval form takes precedence when both exist."""
        edge = {
            'source': 'A',
            'target': 'B',
            't': 100.0,
            't_start': 50.0,
            't_end': 150.0
        }
        interval = extract_edge_time(edge)
        # Interval form should win
        assert interval.start == 50.0
        assert interval.end == 150.0

    def test_atemporal_edge(self):
        """Test extraction from edge with no temporal attributes."""
        edge = {'source': 'A', 'target': 'B'}
        interval = extract_edge_time(edge)
        assert interval.start is None
        assert interval.end is None

    def test_extract_with_string_timestamp(self):
        """Test extraction with ISO string timestamp."""
        edge = {'source': 'A', 'target': 'B', 't': "2009-02-13T23:31:30Z"}
        interval = extract_edge_time(edge)
        expected = datetime.datetime(2009, 2, 13, 23, 31, 30).timestamp()
        assert interval.start == expected
        assert interval.end == expected




class TestExtractEdgeTimeUnbounded:
    """Test extract_edge_time with unbounded intervals."""

    def test_extract_only_start_becomes_unbounded_end(self):
        """Test that only t_start present results in unbounded end (inf)."""
        edge = {'source': 'A', 'target': 'B', 't_start': 50.0}
        interval = extract_edge_time(edge)
        assert interval.start == 50.0
        assert interval.end == float('inf')

    def test_extract_only_end_becomes_unbounded_start(self):
        """Test that only t_end present results in unbounded start (-inf)."""
        edge = {'source': 'A', 'target': 'B', 't_end': 150.0}
        interval = extract_edge_time(edge)
        assert interval.start == float('-inf')
        assert interval.end == 150.0

    def test_extract_handles_invalid_timestamp(self):
        """Test that invalid timestamps are handled gracefully."""
        edge = {'source': 'A', 'target': 'B', 't': 'invalid'}
        interval = extract_edge_time(edge)
        # Should return atemporal interval when parsing fails
        assert interval.start is None
        assert interval.end is None
