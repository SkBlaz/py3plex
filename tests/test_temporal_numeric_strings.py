"""Numeric timestamps must have identical semantics as numbers and strings."""

import pytest

from py3plex.core.temporal_multinet import TemporalMultiLayerNetwork
from py3plex.temporal_utils import _parse_time, extract_edge_time


@pytest.mark.parametrize(
    "value",
    [
        "72420101.0625",
        "20260101",
        "20260101.5",
        "20090213.0",
        " 20260101.5 ",
        "+20260101.5",
        "2.02601015e7",
        "-20260101.5",
    ],
)
def test_numeric_strings_are_not_parsed_as_calendar_dates(value):
    expected = float(value)
    assert _parse_time(value) == expected
    point = extract_edge_time({"t": value})
    assert (point.start, point.end) == (expected, expected)
    interval = extract_edge_time({"t_start": value, "t_end": str(expected + 1)})
    assert (interval.start, interval.end) == (expected, expected + 1)


def test_string_timestamp_is_selected_by_numeric_window():
    value = "72420101.0625"
    tnet = TemporalMultiLayerNetwork()
    tnet.add_edge("A", "L", "B", "L", t=value)
    assert tnet.time_range() == (float(value), float(value))
    assert len(list(tnet.edges_between(float(value) - 1, float(value) + 1))) == 1
