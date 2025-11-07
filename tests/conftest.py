"""
Pytest configuration and shared fixtures for py3plex tests.

This module provides common fixtures and configuration that can be used
across all test modules.
"""
import os
import tempfile
import shutil
from pathlib import Path

import pytest

# Configure Hypothesis profiles
try:
    from hypothesis import settings, Verbosity
    
    # Register a "ci" profile for faster CI runs
    settings.register_profile(
        "ci",
        max_examples=10,
        deadline=2000,  # 2 seconds per test
        verbosity=Verbosity.normal,
    )
    
    # Register a "nightly" profile for thorough testing
    settings.register_profile(
        "nightly",
        max_examples=int(os.environ.get("HYPOTHESIS_MAX_EXAMPLES", "600")),
        deadline=None,
        verbosity=Verbosity.verbose,
    )
    
    # Activate profile based on environment
    profile = os.environ.get("HYPOTHESIS_PROFILE", "ci" if os.environ.get("CI") else "default")
    settings.load_profile(profile)
    
except ImportError:
    # Hypothesis not available - tests will be skipped
    pass


@pytest.fixture
def temp_dir():
    """
    Create a temporary directory for test files.
    
    The directory is automatically cleaned up after the test completes.
    
    Yields:
        str: Path to temporary directory
    
    Example:
        >>> def test_file_creation(temp_dir):
        ...     test_file = os.path.join(temp_dir, "test.txt")
        ...     with open(test_file, "w") as f:
        ...         f.write("test")
        ...     assert os.path.exists(test_file)
    """
    temp_path = tempfile.mkdtemp()
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def temp_file():
    """
    Create a temporary file for testing.
    
    The file is automatically cleaned up after the test completes.
    
    Yields:
        str: Path to temporary file
    
    Example:
        >>> def test_file_operations(temp_file):
        ...     with open(temp_file, "w") as f:
        ...         f.write("test content")
        ...     assert os.path.exists(temp_file)
    """
    fd, temp_path = tempfile.mkstemp()
    os.close(fd)
    yield temp_path
    try:
        os.unlink(temp_path)
    except OSError:
        pass


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "property: property-based tests using Hypothesis"
    )
    config.addinivalue_line(
        "markers", "unit: fast unit tests"
    )
    config.addinivalue_line(
        "markers", "metamorphic: metamorphic tests that verify invariants under transformations"
    )
