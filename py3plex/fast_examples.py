"""Utilities for managing example execution performance.

This module provides utilities to make examples run faster in CI/testing
environments while maintaining full functionality for development.
"""

import os
import sys
import time
import signal
from functools import wraps


def is_fast_mode():
    """Check if FAST_EXAMPLES environment variable is set.
    
    Returns:
        bool: True if FAST_EXAMPLES is set to '1', 'true', 'yes', or 'on' (case-insensitive)
    """
    fast_env = os.environ.get('FAST_EXAMPLES', '').lower()
    return fast_env in ('1', 'true', 'yes', 'on')


def get_fast_params(defaults, fast_overrides):
    """Get parameters based on fast mode.
    
    Args:
        defaults (dict): Default parameter values
        fast_overrides (dict): Override values when in fast mode
        
    Returns:
        dict: Merged parameters (fast overrides applied if in fast mode)
        
    Example:
        >>> params = get_fast_params(
        ...     defaults={'n_samples': 100, 'max_iter': 1000},
        ...     fast_overrides={'n_samples': 10, 'max_iter': 50}
        ... )
        >>> # Returns fast_overrides if FAST_EXAMPLES=1, else defaults
    """
    if is_fast_mode():
        result = defaults.copy()
        result.update(fast_overrides)
        return result
    return defaults


class TimeoutError(Exception):
    """Raised when example exceeds time limit."""
    pass


def timeout_handler(signum, frame):
    """Signal handler for timeout."""
    raise TimeoutError("Example execution exceeded time limit")


def with_timeout(seconds=30):
    """Decorator to enforce time limit on example execution.
    
    Args:
        seconds (int): Maximum execution time in seconds
        
    Example:
        >>> @with_timeout(30)
        ... def my_example():
        ...     # Example code here
        ...     pass
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Set up signal handler (Unix only)
            if hasattr(signal, 'SIGALRM'):
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(seconds)
                try:
                    result = func(*args, **kwargs)
                    signal.alarm(0)  # Cancel alarm
                    return result
                except TimeoutError:
                    print(f"ERROR: Example timed out after {seconds}s", file=sys.stderr)
                    print("Consider adding FAST_EXAMPLES=1 support", file=sys.stderr)
                    sys.exit(1)
            else:
                # Windows or other platforms - just run without timeout
                return func(*args, **kwargs)
        return wrapper
    return decorator


def print_fast_mode_info():
    """Print information about fast mode if enabled."""
    if is_fast_mode():
        print("=" * 60)
        print("FAST_EXAMPLES mode enabled - using reduced parameters")
        print("Set FAST_EXAMPLES=0 to run with full parameters")
        print("=" * 60)
        print()


# Preset parameter sets for common operations

FAST_UQ_PARAMS = {
    'n_samples': 10,  # Reduced from typical 50-100
    'ci': 0.95,
}

FAST_COMMUNITY_PARAMS = {
    'max_iter': 50,  # Reduced from typical 100-500
    'n_restarts': 2,  # Reduced from typical 5-10
}

FAST_LAYOUT_PARAMS = {
    'iterations': 50,  # Reduced from typical 200-1000
}

FAST_DYNAMICS_PARAMS = {
    'steps': 50,  # Reduced from typical 100-500
    'replicates': 5,  # Reduced from typical 10-50
}
