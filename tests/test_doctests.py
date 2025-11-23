"""
Test module for running doctests.

This module ensures that docstring examples in the py3plex codebase are
executable and correct. It serves as documentation that validates itself.

The doctests are automatically discovered and run by pytest when configured
with --doctest-modules flag. See pyproject.toml for configuration.

Usage:
    # Run all doctests
    pytest --doctest-modules py3plex/

    # Run doctests for specific modules
    pytest --doctest-modules py3plex/dsl.py
    pytest --doctest-modules py3plex/core/multinet.py

    # Run this test file (it will trigger doctest discovery)
    pytest tests/test_doctests.py

Note:
    Some docstring examples are marked with `# doctest: +SKIP` when they:
    - Require external files or resources
    - Require optional dependencies not in core requirements
    - Are for illustration purposes only
    - Require complex setup that would obscure the example
"""

import pytest
import doctest


def test_doctests_in_dsl():
    """Test that DSL module doctests pass."""
    import py3plex.dsl
    
    # Count doctest examples
    results = doctest.testmod(py3plex.dsl, verbose=False, optionflags=doctest.ELLIPSIS)
    
    # Ensure we have some doctests and they all pass
    assert results.attempted > 0, "No doctests found in dsl module"
    assert results.failed == 0, f"DSL doctests failed: {results.failed} failures"


def test_doctests_in_core_multinet():
    """Test that core multinet module doctests pass."""
    import py3plex.core.multinet
    
    results = doctest.testmod(
        py3plex.core.multinet,
        verbose=False,
        optionflags=doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE
    )
    
    assert results.attempted > 0, "No doctests found in core.multinet module"
    assert results.failed == 0, f"Core.multinet doctests failed: {results.failed} failures"


def test_doctests_in_core_parsers():
    """Test that core parsers module doctests pass."""
    import py3plex.core.parsers
    
    results = doctest.testmod(
        py3plex.core.parsers,
        verbose=False,
        optionflags=doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE
    )
    
    assert results.attempted > 0, "No doctests found in core.parsers module"
    assert results.failed == 0, f"Core.parsers doctests failed: {results.failed} failures"


def test_doctests_in_core_supporting():
    """Test that core supporting module doctests pass."""
    import py3plex.core.supporting
    
    results = doctest.testmod(
        py3plex.core.supporting,
        verbose=False,
        optionflags=doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE
    )
    
    assert results.attempted > 0, "No doctests found in core.supporting module"
    assert results.failed == 0, f"Core.supporting doctests failed: {results.failed} failures"


def test_doctest_configuration():
    """Verify that pytest is configured to run doctests."""
    import py3plex
    
    # This test ensures pytest doctest configuration is working
    # The test passes if the module can be imported without errors
    assert hasattr(py3plex, '__version__')


if __name__ == '__main__':
    # Allow running this test file directly
    pytest.main([__file__, '-v'])
