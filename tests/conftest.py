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
