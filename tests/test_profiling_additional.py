"""Additional tests for py3plex.profiling edge behavior."""

import time

import pytest

from py3plex.profiling import benchmark, get_monitor


def test_monitor_report_no_data_message():
    """Monitor should report no data when empty."""
    monitor = get_monitor()
    monitor.clear()
    assert monitor.get_report() == "No performance data collected."


def test_benchmark_even_iterations_median():
    """Median should average middle two values for even-length timing arrays."""
    timeline = iter([0.0, 1.0, 3.0, 6.0, 10.0, 15.0, 21.0, 28.0])

    def fake_perf_counter():
        return next(timeline)

    original_perf_counter = time.perf_counter
    time.perf_counter = fake_perf_counter
    try:
        stats = benchmark(lambda: None, iterations=4, warmup=0)
    finally:
        time.perf_counter = original_perf_counter

    # Durations are [1, 3, 5, 7]
    assert stats["min"] == pytest.approx(1.0)
    assert stats["max"] == pytest.approx(7.0)
    assert stats["mean"] == pytest.approx(4.0)
    assert stats["median"] == pytest.approx(4.0)
    assert stats["total"] == pytest.approx(16.0)
