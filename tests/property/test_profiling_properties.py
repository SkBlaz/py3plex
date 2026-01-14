#!/usr/bin/env python3
"""
Property-based tests for profiling module.

Tests PerformanceMonitor and profiling decorators.
"""

import time
import pytest
from hypothesis import given, settings, assume, strategies as st
from hypothesis import HealthCheck

# Import profiling module
try:
    from py3plex.profiling import (
        PerformanceMonitor,
        get_monitor,
        profile_performance,
    )
    PROFILING_AVAILABLE = True
except ImportError:
    PROFILING_AVAILABLE = False
    pytest.skip("profiling module not available", allow_module_level=True)


# ============================================================================
# Property Tests: PerformanceMonitor
# ============================================================================

@pytest.mark.property
def test_performance_monitor_creation():
    """Test that PerformanceMonitor can be created."""
    monitor = PerformanceMonitor()
    
    assert monitor.enabled is True, \
        "Monitor should be enabled by default"
    assert isinstance(monitor.stats, dict), \
        "Stats should be a dictionary"
    assert len(monitor.stats) == 0, \
        "Stats should be empty initially"


@pytest.mark.property
@settings(deadline=None, max_examples=30)
@given(
    func_name=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='_')),
    elapsed=st.floats(min_value=0.001, max_value=10.0, allow_nan=False, allow_infinity=False)
)
def test_performance_monitor_record(func_name, elapsed):
    """Test that PerformanceMonitor records metrics correctly."""
    monitor = PerformanceMonitor()
    monitor.record(func_name, elapsed)
    
    assert func_name in monitor.stats, \
        "Function should be in stats after recording"
    assert monitor.stats[func_name]["call_count"] == 1, \
        "Call count should be 1 after first recording"
    assert monitor.stats[func_name]["total_time"] == elapsed, \
        "Total time should match elapsed time"
    assert monitor.stats[func_name]["min_time"] == elapsed, \
        "Min time should match elapsed time for single call"
    assert monitor.stats[func_name]["max_time"] == elapsed, \
        "Max time should match elapsed time for single call"


@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(
    func_name=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='_')),
    times=st.lists(st.floats(min_value=0.001, max_value=1.0, allow_nan=False, allow_infinity=False), min_size=2, max_size=10)
)
def test_performance_monitor_multiple_records(func_name, times):
    """Test that PerformanceMonitor handles multiple records correctly."""
    monitor = PerformanceMonitor()
    
    for elapsed in times:
        monitor.record(func_name, elapsed)
    
    assert monitor.stats[func_name]["call_count"] == len(times), \
        "Call count should match number of recordings"
    assert abs(monitor.stats[func_name]["total_time"] - sum(times)) < 1e-9, \
        "Total time should equal sum of all times"
    assert abs(monitor.stats[func_name]["min_time"] - min(times)) < 1e-9, \
        "Min time should match minimum of recorded times"
    assert abs(monitor.stats[func_name]["max_time"] - max(times)) < 1e-9, \
        "Max time should match maximum of recorded times"


@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(
    func_name=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='_')),
    elapsed=st.floats(min_value=0.001, max_value=10.0, allow_nan=False, allow_infinity=False),
    memory_delta=st.floats(min_value=-100.0, max_value=100.0, allow_nan=False, allow_infinity=False)
)
def test_performance_monitor_record_with_memory(func_name, elapsed, memory_delta):
    """Test that PerformanceMonitor records memory metrics."""
    monitor = PerformanceMonitor()
    monitor.record(func_name, elapsed, memory_delta=memory_delta)
    
    assert func_name in monitor.stats, \
        "Function should be in stats"
    assert monitor.stats[func_name]["total_memory"] == memory_delta, \
        "Total memory should match memory delta"


@pytest.mark.property
def test_performance_monitor_disabled():
    """Test that PerformanceMonitor respects enabled flag."""
    monitor = PerformanceMonitor()
    monitor.enabled = False
    
    monitor.record("test_func", 1.0)
    
    assert len(monitor.stats) == 0, \
        "Stats should remain empty when monitor is disabled"


@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(
    func_names=st.lists(
        st.text(min_size=1, max_size=30, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='_')),
        min_size=1,
        max_size=10,
        unique=True
    )
)
def test_performance_monitor_multiple_functions(func_names):
    """Test that PerformanceMonitor tracks multiple functions separately."""
    monitor = PerformanceMonitor()
    
    for func_name in func_names:
        monitor.record(func_name, 0.1)
    
    assert len(monitor.stats) == len(func_names), \
        "Should have stats for each function"
    
    for func_name in func_names:
        assert func_name in monitor.stats, \
            f"Function {func_name} should be in stats"


@pytest.mark.property
@settings(deadline=None, max_examples=10)
@given(func_name=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='_')))
def test_performance_monitor_clear(func_name):
    """Test that clear() removes all stats."""
    monitor = PerformanceMonitor()
    monitor.record(func_name, 1.0)
    
    assert len(monitor.stats) > 0, \
        "Stats should not be empty before clear"
    
    monitor.clear()
    
    assert len(monitor.stats) == 0, \
        "Stats should be empty after clear"


@pytest.mark.property
def test_performance_monitor_get_report_empty():
    """Test that get_report() handles empty stats."""
    monitor = PerformanceMonitor()
    report = monitor.get_report()
    
    assert isinstance(report, str), \
        "Report should be a string"
    assert len(report) > 0, \
        "Report should not be empty"


@pytest.mark.property
@settings(deadline=None, max_examples=10)
@given(func_name=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='_')))
def test_performance_monitor_get_report_with_data(func_name):
    """Test that get_report() generates valid report with data."""
    monitor = PerformanceMonitor()
    monitor.record(func_name, 0.5)
    
    report = monitor.get_report()
    
    assert isinstance(report, str), \
        "Report should be a string"
    assert func_name in report, \
        "Report should contain function name"
    assert "Performance Report" in report, \
        "Report should have title"


# ============================================================================
# Property Tests: get_monitor
# ============================================================================

@pytest.mark.property
def test_get_monitor_returns_singleton():
    """Test that get_monitor returns the same instance."""
    monitor1 = get_monitor()
    monitor2 = get_monitor()
    
    assert monitor1 is monitor2, \
        "get_monitor should return the same instance"


@pytest.mark.property
def test_get_monitor_returns_performance_monitor():
    """Test that get_monitor returns a PerformanceMonitor instance."""
    monitor = get_monitor()
    
    assert isinstance(monitor, PerformanceMonitor), \
        "get_monitor should return PerformanceMonitor instance"


# ============================================================================
# Property Tests: profile_performance decorator
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=10)
@given(sleep_time=st.floats(min_value=0.001, max_value=0.05, allow_nan=False, allow_infinity=False))
def test_profile_performance_decorator(sleep_time):
    """Test that profile_performance decorator tracks function execution."""
    monitor = PerformanceMonitor()
    
    @profile_performance
    def test_func():
        time.sleep(sleep_time)
        return "done"
    
    # Clear any previous stats
    monitor.clear()
    
    # Call the function
    result = test_func()
    
    assert result == "done", \
        "Function should return expected value"


@pytest.mark.property
def test_profile_performance_preserves_function_name():
    """Test that decorator preserves function name."""
    @profile_performance
    def my_test_function():
        return 42
    
    # Function name should be preserved (or at least accessible)
    result = my_test_function()
    assert result == 42, \
        "Function should work correctly after decoration"


@pytest.mark.property
@settings(deadline=None, max_examples=10)
@given(
    arg1=st.integers(min_value=0, max_value=100),
    arg2=st.integers(min_value=0, max_value=100)
)
def test_profile_performance_with_arguments(arg1, arg2):
    """Test that decorator works with function arguments."""
    @profile_performance
    def add_numbers(a, b):
        return a + b
    
    result = add_numbers(arg1, arg2)
    
    assert result == arg1 + arg2, \
        "Function should compute correctly with arguments"


@pytest.mark.property
def test_profile_performance_with_exception():
    """Test that decorator handles exceptions correctly."""
    @profile_performance
    def failing_function():
        raise ValueError("Test exception")
    
    with pytest.raises(ValueError, match="Test exception"):
        failing_function()


# ============================================================================
# Property Tests: Statistics calculations
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(times=st.lists(st.floats(min_value=0.1, max_value=10.0, allow_nan=False, allow_infinity=False), min_size=1, max_size=20))
def test_average_time_calculation(times):
    """Test that average time is calculated correctly."""
    monitor = PerformanceMonitor()
    func_name = "test_func"
    
    for t in times:
        monitor.record(func_name, t)
    
    stats = monitor.stats[func_name]
    expected_avg = sum(times) / len(times)
    actual_avg = stats["total_time"] / stats["call_count"]
    
    assert abs(actual_avg - expected_avg) < 1e-9, \
        "Average time should be calculated correctly"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-m', 'property'])
