"""Additional tests for py3plex.profiling edge behavior."""

import time

import pytest

from py3plex.profiling import benchmark, get_monitor


def test_monitor_report_no_data_message():
    """Monitor should report no data when empty."""
    monitor = get_monitor()
    monitor.clear()
    assert monitor.get_report() == "No performance data collected."


def test_benchmark_even_iterations_median(monkeypatch):
    """Median should average middle two values for even-length timing arrays."""
    # Timeline values are chosen so iteration durations become [1, 3, 5, 7],
    # which validates even-length median averaging: (3 + 5) / 2 == 4.0.
    timeline = iter([0.0, 1.0, 3.0, 6.0, 10.0, 15.0, 21.0, 28.0])

    def fake_perf_counter():
        return next(timeline)

    monkeypatch.setattr(time, "perf_counter", fake_perf_counter)
    stats = benchmark(lambda: None, iterations=4, warmup=0)

    # Durations [1, 3, 5, 7] test median averaging for even-length arrays.
    assert stats["min"] == pytest.approx(1.0)
    assert stats["max"] == pytest.approx(7.0)
    assert stats["mean"] == pytest.approx(4.0)
    assert stats["median"] == pytest.approx(4.0)
    assert stats["total"] == pytest.approx(16.0)


def test_benchmark_odd_iterations_median(monkeypatch):
    """Median should pick the middle value for odd-length timing arrays."""
    timeline = iter([0.0, 2.0, 5.0, 10.0, 14.0, 20.0])

    def fake_perf_counter():
        return next(timeline)

    monkeypatch.setattr(time, "perf_counter", fake_perf_counter)
    stats = benchmark(lambda: None, iterations=3, warmup=0)

    # Durations are [2, 5, 6], median is the middle value 5.
    assert stats["min"] == pytest.approx(2.0)
    assert stats["max"] == pytest.approx(6.0)
    assert stats["mean"] == pytest.approx((2.0 + 5.0 + 6.0) / 3.0)
    assert stats["median"] == pytest.approx(5.0)
    assert stats["total"] == pytest.approx(13.0)
