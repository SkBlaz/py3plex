"""
Performance profiling utilities for py3plex.

This module provides decorators and utilities for tracking function execution time,
memory usage, and performance metrics. These tools enable performance regression
detection and optimization efforts.

Example:
    >>> from py3plex.profiling import profile_performance
    >>>
    >>> @profile_performance
    >>> def slow_function():
    ...     # ... computation
    ...     pass
    >>>
    >>> slow_function()  # Logs execution time automatically
"""

import functools
import time
import tracemalloc
from typing import Any, Callable, Dict, Optional

from py3plex.logging_config import get_logger

logger = get_logger(__name__)


class PerformanceMonitor:
    """
    Global performance monitoring registry.

    Tracks execution times and call counts for profiled functions.
    Can be used to generate performance reports and detect regressions.

    Attributes:
        enabled: Whether profiling is enabled globally
        stats: Dictionary mapping function names to performance statistics
    """

    def __init__(self):
        self.enabled = True
        self.stats: Dict[str, Dict[str, Any]] = {}

    def record(
        self, func_name: str, elapsed: float, memory_delta: Optional[float] = None
    ):
        """
        Record performance metrics for a function call.

        Args:
            func_name: Name of the function
            elapsed: Execution time in seconds
            memory_delta: Memory usage change in MB (optional)
        """
        if not self.enabled:
            return

        if func_name not in self.stats:
            self.stats[func_name] = {
                "call_count": 0,
                "total_time": 0.0,
                "min_time": float("inf"),
                "max_time": 0.0,
                "total_memory": 0.0,
            }

        stats = self.stats[func_name]
        stats["call_count"] += 1
        stats["total_time"] += elapsed
        stats["min_time"] = min(stats["min_time"], elapsed)
        stats["max_time"] = max(stats["max_time"], elapsed)

        if memory_delta is not None:
            stats["total_memory"] += memory_delta

    def get_report(self) -> str:
        """
        Generate a performance report.

        Returns:
            String containing formatted performance statistics
        """
        if not self.stats:
            return "No performance data collected."

        lines = ["Performance Report", "=" * 80]
        lines.append(
            f"{'Function':<40} {'Calls':>8} {'Total(s)':>10} {'Avg(ms)':>10} {'Min(ms)':>10} {'Max(ms)':>10}"
        )
        lines.append("-" * 80)

        for func_name, stats in sorted(self.stats.items()):
            avg_time = (
                stats["total_time"] / stats["call_count"]
            ) * 1000  # Convert to ms
            min_time = stats["min_time"] * 1000
            max_time = stats["max_time"] * 1000

            lines.append(
                f"{func_name:<40} {stats['call_count']:>8} "
                f"{stats['total_time']:>10.3f} {avg_time:>10.3f} "
                f"{min_time:>10.3f} {max_time:>10.3f}"
            )

        return "\n".join(lines)

    def clear(self):
        """Clear all collected statistics."""
        self.stats.clear()


# Global performance monitor instance
_monitor = PerformanceMonitor()


def get_monitor() -> PerformanceMonitor:
    """
    Get the global performance monitor instance.

    Returns:
        PerformanceMonitor: Global performance monitoring instance

    Example:
        >>> from py3plex.profiling import get_monitor
        >>> monitor = get_monitor()
        >>> print(monitor.get_report())
    """
    return _monitor


def profile_performance(
    func: Optional[Callable] = None,
    *,
    log_args: bool = False,
    track_memory: bool = False,
) -> Callable:
    """
    Decorator to track function execution time and optionally memory usage.

    This decorator measures the wall-clock time taken by a function and logs it.
    It can also track memory usage changes if requested. Performance metrics
    are stored in the global performance monitor for later analysis.

    Args:
        func: Function to decorate (when used without arguments)
        log_args: If True, log function arguments (default: False)
        track_memory: If True, track memory usage (default: False)

    Returns:
        Decorated function that logs execution time

    Examples:
        Basic usage:
        >>> @profile_performance
        ... def my_function(x, y):
        ...     return x + y

        With options:
        >>> @profile_performance(log_args=True, track_memory=True)
        ... def expensive_function(data):
        ...     # ... expensive computation
        ...     return result

        Manual wrapping:
        >>> def my_function():
        ...     pass
        >>> profiled_func = profile_performance(my_function)

    Note:
        Memory tracking requires the tracemalloc module and adds overhead.
        Use it only when investigating memory issues.
    """

    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            func_name = f"{fn.__module__}.{fn.__qualname__}"

            # Start memory tracking if requested
            memory_before = None
            if track_memory:
                if not tracemalloc.is_tracing():
                    tracemalloc.start()
                memory_before = tracemalloc.get_traced_memory()[0]

            # Log function call with arguments if requested
            if log_args:
                args_str = ", ".join(
                    [repr(a) for a in args[:3]]
                )  # Limit to first 3 args
                if len(args) > 3:
                    args_str += ", ..."
                logger.debug(f"Calling {func_name}({args_str})")

            # Execute function and measure time
            start = time.perf_counter()
            try:
                result = fn(*args, **kwargs)
                elapsed = time.perf_counter() - start

                # Calculate memory delta if tracking
                memory_delta = None
                if track_memory and memory_before is not None:
                    memory_after = tracemalloc.get_traced_memory()[0]
                    memory_delta = (memory_after - memory_before) / (
                        1024 * 1024
                    )  # Convert to MB

                # Record metrics
                _monitor.record(func_name, elapsed, memory_delta)

                # Log execution time
                if elapsed < 0.001:
                    logger.debug(f"{func_name} took {elapsed*1000:.3f}ms")
                elif elapsed < 1.0:
                    logger.debug(f"{func_name} took {elapsed*1000:.1f}ms")
                else:
                    logger.info(f"{func_name} took {elapsed:.2f}s")

                # Log memory usage if tracked
                if memory_delta is not None:
                    if abs(memory_delta) > 1.0:
                        logger.info(f"{func_name} memory delta: {memory_delta:+.2f}MB")
                    else:
                        logger.debug(
                            f"{func_name} memory delta: {memory_delta*1024:+.2f}KB"
                        )

                return result

            except Exception as e:
                elapsed = time.perf_counter() - start
                logger.error(f"{func_name} failed after {elapsed:.2f}s: {e}")
                raise

        return wrapper

    # Handle both @profile_performance and @profile_performance(...) syntax
    if func is None:
        return decorator
    else:
        return decorator(func)


def timed_section(name: str, log_level: str = "info"):
    """
    Context manager for timing code blocks.

    Useful for timing specific sections of code without wrapping entire functions.

    Args:
        name: Name of the code section being timed
        log_level: Logging level ('debug', 'info', 'warning', 'error')

    Example:
        >>> from py3plex.profiling import timed_section
        >>>
        >>> with timed_section("data loading"):
        ...     data = load_large_dataset()
        >>>
        >>> with timed_section("computation", log_level="debug"):
        ...     result = complex_calculation()

    Yields:
        None
    """

    class TimedSection:
        def __init__(self, section_name: str, level: str):
            self.name = section_name
            self.level = level
            self.start: Optional[float] = None

        def __enter__(self):
            self.start = time.perf_counter()
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            if self.start is None:
                return False
            elapsed = time.perf_counter() - self.start

            log_func = getattr(logger, self.level, logger.info)
            if elapsed < 1.0:
                log_func(f"[{self.name}] completed in {elapsed*1000:.1f}ms")
            else:
                log_func(f"[{self.name}] completed in {elapsed:.2f}s")

            return False  # Don't suppress exceptions

    return TimedSection(name, log_level)


def benchmark(
    func: Callable,
    iterations: int = 100,
    warmup: int = 10,
    args: tuple = (),
    kwargs: dict = None,
) -> Dict[str, float]:
    """
    Benchmark a function with multiple iterations.

    Runs the function multiple times and collects statistics about execution time.
    Includes a warmup phase to allow JIT compilation and caching.

    Args:
        func: Function to benchmark
        iterations: Number of iterations to run (default: 100)
        warmup: Number of warmup iterations (default: 10)
        args: Positional arguments for the function
        kwargs: Keyword arguments for the function

    Returns:
        Dictionary containing benchmark statistics:
            - mean: Average execution time (seconds)
            - median: Median execution time (seconds)
            - min: Minimum execution time (seconds)
            - max: Maximum execution time (seconds)
            - std: Standard deviation (seconds)
            - total: Total time for all iterations (seconds)

    Example:
        >>> from py3plex.profiling import benchmark
        >>>
        >>> def my_function(n):
        ...     return sum(range(n))
        >>>
        >>> stats = benchmark(my_function, iterations=1000, args=(1000,))
        >>> print(f"Average time: {stats['mean']*1000:.3f}ms")
    """
    if kwargs is None:
        kwargs = {}

    # Warmup phase
    for _ in range(warmup):
        func(*args, **kwargs)

    # Benchmark phase
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        times.append(elapsed)

    # Calculate statistics
    times_sorted = sorted(times)
    n = len(times)

    return {
        "mean": sum(times) / n,
        "median": (
            times_sorted[n // 2]
            if n % 2 == 1
            else (times_sorted[n // 2 - 1] + times_sorted[n // 2]) / 2
        ),
        "min": min(times),
        "max": max(times),
        "std": (sum((t - sum(times) / n) ** 2 for t in times) / n) ** 0.5,
        "total": sum(times),
    }
