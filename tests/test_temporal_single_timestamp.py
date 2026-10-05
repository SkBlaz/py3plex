"""Windowing must retain networks whose events share a single timestamp."""

from datetime import datetime, timedelta, timezone

import pytest

from py3plex.algorithms.temporal.centrality import streaming_degree_centrality, streaming_pagerank
from py3plex.core.temporal_multinet import TemporalMultiLayerNetwork


@pytest.mark.parametrize("return_type", ["temporal", "snapshot"])
@pytest.mark.parametrize("window_size", [10.0, timedelta(seconds=10)])
@pytest.mark.parametrize("step", [None, 2.0, 20.0])
@pytest.mark.parametrize("timestamp", [0.0, datetime(2026, 1, 1, tzinfo=timezone.utc)])
@pytest.mark.parametrize("layers", [None, ["social"], []])
def test_inferred_point_range_emits_one_full_window(return_type, window_size, step, timestamp, layers):
    net = TemporalMultiLayerNetwork(directed=True)
    for layer in ["social", "work"]:
        net.add_edge("A", layer, "B", layer, t=timestamp, event=layer)
    t = timestamp.timestamp() if isinstance(timestamp, datetime) else timestamp
    windows = list(net.window_iter(
        window_size=window_size, step=step, layers=layers, return_type=return_type
    ))
    assert len(windows) == 1
    start, end, window = windows[0]
    assert (start, end) == (t, t + 10)
    base = window.base_network if return_type == "temporal" else window
    events = {
        data["event"] for _, _, data in base.get_edges(data=True, multiplex_edges=True)
    } if base.core_network is not None else set()
    assert events == (set(["social", "work"]) if layers is None else set(layers))
    assert net.time_range() == (t, t)
    assert net.number_of_edges() == 2


@pytest.mark.parametrize("return_type", ["temporal", "snapshot"])
def test_inferred_end_at_explicit_start_retains_last_event(return_type):
    net = TemporalMultiLayerNetwork()
    net.add_edge("A", "L", "B", "L", t=100.0)
    windows = list(net.window_iter(window_size=10, start=100, return_type=return_type))
    assert len(windows) == 1
    assert windows[0][:2] == (100, 110)


@pytest.mark.parametrize("return_type", ["temporal", "snapshot"])
@pytest.mark.parametrize("end", [100.0, 99.0])
def test_explicit_empty_ranges_remain_empty(return_type, end):
    net = TemporalMultiLayerNetwork()
    net.add_edge("A", "L", "B", "L", t=100.0)
    assert list(net.window_iter(window_size=10, end=end, return_type=return_type)) == []


@pytest.mark.parametrize("return_type", ["temporal", "snapshot"])
def test_empty_network_still_has_no_windows(return_type):
    assert list(TemporalMultiLayerNetwork().window_iter(window_size=10, return_type=return_type)) == []


@pytest.mark.parametrize("return_type", ["temporal", "snapshot"])
@pytest.mark.parametrize("window_size", [10.0, timedelta(seconds=10)])
def test_multiple_timestamps_keep_existing_boundaries(return_type, window_size):
    net = TemporalMultiLayerNetwork()
    for t in [100, 110, 120]:
        net.add_edge("A", "L", str(t), "L", t=t)
    windows = list(net.window_iter(window_size=window_size, return_type=return_type))
    assert [w[:2] for w in windows] == [(100, 110), (110, 120)]


@pytest.mark.parametrize("algorithm", [streaming_pagerank, streaming_degree_centrality])
def test_streaming_centrality_returns_scores_for_simultaneous_events(algorithm):
    net = TemporalMultiLayerNetwork(directed=True)
    net.add_edge("A", "L", "B", "L", t=100.0)
    net.add_edge("B", "L", "A", "L", t=100.0)
    windows = list(algorithm(net, window_size=10))
    assert len(windows) == 1
    assert windows[0][:2] == (100, 110)
    assert set(windows[0][2]) == {("A", "L"), ("B", "L")}


@pytest.mark.parametrize("return_type", ["temporal", "snapshot"])
@pytest.mark.parametrize("timestamp,kwargs,message", [
    (1e16, {"window_size": 1e-6}, "window_size"),
    (1e16, {"window_size": 100, "step": 1e-6}, "step"),
    (1e308, {"window_size": 1e308}, "finite"),
])
def test_inferred_single_window_rejects_unrepresentable_boundaries(return_type, timestamp, kwargs, message):
    net = TemporalMultiLayerNetwork()
    net.add_edge("A", "L", "B", "L", t=timestamp)
    with pytest.raises(ValueError, match=message):
        list(net.window_iter(return_type=return_type, **kwargs))
