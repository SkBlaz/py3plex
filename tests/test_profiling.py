"""
Tests for the performance profiling utilities.
"""

import time
import pytest
from py3plex.profiling import (
    profile_performance,
    timed_section,
    benchmark,
    get_monitor,
)


def test_profile_performance_decorator():
    """Test the profile_performance decorator tracks execution time."""
    
    @profile_performance
    def sample_function(n):
        time.sleep(0.01)  # Sleep for 10ms
        return n * 2
    
    # Clear any previous stats
    monitor = get_monitor()
    monitor.clear()
    
    # Run the function
    result = sample_function(5)
    assert result == 10
    
    # Check that stats were recorded
    stats = monitor.stats
    
    # Function name will be the full qualified name including test scope
    assert len(stats) == 1
    func_name = list(stats.keys())[0]
    assert 'sample_function' in func_name
    assert stats[func_name]['call_count'] == 1
    assert stats[func_name]['total_time'] >= 0.01  # At least 10ms
    assert stats[func_name]['min_time'] >= 0.01
    assert stats[func_name]['max_time'] >= 0.01


def test_profile_performance_multiple_calls():
    """Test that multiple calls are tracked correctly."""
    
    @profile_performance
    def another_function(x):
        time.sleep(0.005)  # Sleep for 5ms
        return x + 1
    
    monitor = get_monitor()
    monitor.clear()
    
    # Run multiple times
    for i in range(3):
        another_function(i)
    
    stats = monitor.stats
    
    # Function name will be the full qualified name including test scope
    assert len(stats) == 1
    func_name = list(stats.keys())[0]
    assert 'another_function' in func_name
    assert stats[func_name]['call_count'] == 3
    assert stats[func_name]['total_time'] >= 0.015  # At least 15ms total


def test_profile_performance_with_exception():
    """Test that profiling works even when function raises exception."""
    
    @profile_performance
    def failing_function():
        time.sleep(0.005)
        raise ValueError("Test error")
    
    monitor = get_monitor()
    monitor.clear()
    
    with pytest.raises(ValueError, match="Test error"):
        failing_function()
    
    # Stats should still be empty since we don't record failed calls in the current impl
    # (This behavior could be changed if we want to track failures)


def test_timed_section():
    """Test the timed_section context manager."""
    
    with timed_section("test section"):
        time.sleep(0.01)
        result = 42
    
    assert result == 42  # Ensure code execution continues


def test_timed_section_with_exception():
    """Test that timed_section doesn't suppress exceptions."""
    
    with pytest.raises(RuntimeError, match="Test error"):
        with timed_section("failing section"):
            raise RuntimeError("Test error")


def test_benchmark_basic():
    """Test basic benchmarking functionality."""
    
    def fast_function(n):
        return sum(range(n))
    
    stats = benchmark(fast_function, iterations=10, warmup=2, args=(100,))
    
    assert 'mean' in stats
    assert 'median' in stats
    assert 'min' in stats
    assert 'max' in stats
    assert 'std' in stats
    assert 'total' in stats
    
    # Sanity checks
    assert stats['mean'] > 0
    assert stats['min'] <= stats['mean'] <= stats['max']
    assert stats['median'] > 0
    assert stats['std'] >= 0
    assert stats['total'] >= stats['mean'] * 10  # Total should be sum of all iterations


def test_benchmark_with_kwargs():
    """Test benchmark with keyword arguments."""
    
    def function_with_kwargs(x, y=10):
        return x * y
    
    stats = benchmark(
        function_with_kwargs,
        iterations=5,
        warmup=1,
        args=(5,),
        kwargs={'y': 20}
    )
    
    assert stats['mean'] > 0


def test_get_monitor():
    """Test getting the global monitor instance."""
    
    monitor1 = get_monitor()
    monitor2 = get_monitor()
    
    # Should be the same instance
    assert monitor1 is monitor2


def test_monitor_report():
    """Test generating a performance report."""
    
    @profile_performance
    def test_func_1():
        time.sleep(0.005)
    
    @profile_performance
    def test_func_2():
        time.sleep(0.003)
    
    monitor = get_monitor()
    monitor.clear()
    
    # Run both functions
    test_func_1()
    test_func_2()
    test_func_2()  # Run twice
    
    # Generate report
    report = monitor.get_report()
    
    assert "Performance Report" in report
    assert "test_func_1" in report
    assert "test_func_2" in report
    assert "Calls" in report
    assert "Total(s)" in report


def test_monitor_clear():
    """Test clearing monitor statistics."""
    
    @profile_performance
    def some_function():
        pass
    
    monitor = get_monitor()
    monitor.clear()
    
    some_function()
    assert len(monitor.stats) == 1
    
    monitor.clear()
    assert len(monitor.stats) == 0


def test_monitor_disabled():
    """Test that monitoring can be disabled."""
    
    monitor = get_monitor()
    monitor.clear()
    monitor.enabled = False
    
    @profile_performance
    def disabled_function():
        time.sleep(0.005)
    
    disabled_function()
    
    # No stats should be recorded
    assert len(monitor.stats) == 0
    
    # Re-enable for other tests
    monitor.enabled = True


def test_profile_performance_decorator_syntax():
    """Test both decorator syntaxes work."""
    
    # Without arguments
    @profile_performance
    def func1():
        return 1
    
    # With arguments
    @profile_performance(log_args=True)
    def func2(x):
        return x
    
    monitor = get_monitor()
    monitor.clear()
    
    func1()
    func2(42)
    
    assert len(monitor.stats) == 2


def test_benchmark_statistics_accuracy():
    """Test that benchmark statistics are reasonable."""
    
    def consistent_function():
        # Do some work with consistent time
        result = 0
        for i in range(100):
            result += i
        return result
    
    stats = benchmark(consistent_function, iterations=50, warmup=5)
    
    # Standard deviation should be relatively small for consistent function
    # (though this can vary based on system load)
    assert stats['std'] < stats['mean']  # Std dev should be less than mean
    assert stats['min'] < stats['max']  # Some variation expected
    assert abs(stats['median'] - stats['mean']) < stats['mean'] * 0.5  # Median close to mean


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
