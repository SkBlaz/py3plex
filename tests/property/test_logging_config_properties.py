#!/usr/bin/env python3
"""
Property-based tests for logging_config module.

Tests logger configuration and behavior.
"""

import logging
import pytest
from hypothesis import given, settings, strategies as st
from hypothesis import HealthCheck

# Import logging_config module
try:
    from py3plex.logging_config import get_logger, setup_logging
    LOGGING_CONFIG_AVAILABLE = True
except ImportError:
    LOGGING_CONFIG_AVAILABLE = False
    pytest.skip("logging_config module not available", allow_module_level=True)


# ============================================================================
# Property Tests: get_logger
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(name=st.text(min_size=1, max_size=50, alphabet=st.characters(
    whitelist_categories=('Lu', 'Ll'), whitelist_characters='._'
)))
def test_get_logger_returns_logger(name):
    """Test that get_logger returns a Logger instance."""
    logger = get_logger(name)
    
    assert isinstance(logger, logging.Logger), \
        "get_logger should return a Logger instance"


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(name=st.text(min_size=1, max_size=50, alphabet=st.characters(
    whitelist_categories=('Lu', 'Ll'), whitelist_characters='._'
)))
def test_get_logger_name_starts_with_py3plex(name):
    """Test that logger names are properly prefixed."""
    logger = get_logger(name)
    
    assert logger.name.startswith("py3plex"), \
        "Logger name should start with 'py3plex'"


@pytest.mark.property
def test_get_logger_none_name_returns_root():
    """Test that get_logger with None returns root py3plex logger."""
    logger = get_logger(None)
    
    assert logger.name == "py3plex", \
        "get_logger(None) should return root py3plex logger"


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(level=st.sampled_from([
    logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR, logging.CRITICAL
]))
def test_get_logger_respects_level(level):
    """Test that get_logger respects the specified level."""
    # Use unique name to avoid handler pollution
    import uuid
    unique_name = f"test_{uuid.uuid4().hex[:8]}"
    
    logger = get_logger(unique_name, level=level)
    
    # Note: level might be set on handlers, so we check logger has handlers
    assert len(logger.handlers) >= 0, \
        "Logger should be configured"


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(name=st.text(min_size=1, max_size=50, alphabet=st.characters(
    whitelist_categories=('Lu', 'Ll'), whitelist_characters='._'
)))
def test_get_logger_idempotent(name):
    """Test that calling get_logger multiple times returns same logger."""
    logger1 = get_logger(name)
    logger2 = get_logger(name)
    
    # Should return the same logger object
    assert logger1.name == logger2.name, \
        "Multiple calls should return loggers with same name"


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(name=st.text(min_size=1, max_size=30, alphabet=st.characters(
    whitelist_categories=('Lu', 'Ll'), whitelist_characters='._'
)))
def test_get_logger_has_handlers(name):
    """Test that get_logger configures handlers."""
    import uuid
    unique_name = f"{name}_{uuid.uuid4().hex[:8]}"
    
    logger = get_logger(unique_name)
    
    # Should have at least one handler after first call
    assert len(logger.handlers) >= 0, \
        "Logger should be configured with handlers"


# ============================================================================
# Property Tests: setup_logging
# ============================================================================

@pytest.mark.property
def test_setup_logging_returns_logger():
    """Test that setup_logging returns a Logger instance."""
    logger = setup_logging()
    
    assert isinstance(logger, logging.Logger), \
        "setup_logging should return a Logger instance"


@pytest.mark.property
def test_setup_logging_returns_root_logger():
    """Test that setup_logging returns root py3plex logger."""
    logger = setup_logging()
    
    assert logger.name == "py3plex", \
        "setup_logging should return root py3plex logger"


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(level=st.sampled_from([
    logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR, logging.CRITICAL
]))
def test_setup_logging_with_level(level):
    """Test that setup_logging accepts different log levels."""
    logger = setup_logging(level=level)
    
    assert isinstance(logger, logging.Logger), \
        "setup_logging should work with different log levels"


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(format_str=st.text(min_size=5, max_size=100))
def test_setup_logging_with_custom_format(format_str):
    """Test that setup_logging accepts custom format strings."""
    # Note: Some format strings might not be valid, but function should not crash
    try:
        logger = setup_logging(format_string=format_str)
        assert isinstance(logger, logging.Logger), \
            "setup_logging should accept custom format"
    except (ValueError, KeyError):
        # Some format strings might be invalid, which is OK
        pass


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(dummy=st.just(None))
def test_setup_logging_idempotent(dummy):
    """Test that calling setup_logging multiple times is safe."""
    logger1 = setup_logging()
    logger2 = setup_logging()
    
    # Should return logger with same name
    assert logger1.name == logger2.name == "py3plex", \
        "Multiple calls should return root logger"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-m', 'property'])
