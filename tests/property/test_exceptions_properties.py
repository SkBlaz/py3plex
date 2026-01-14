#!/usr/bin/env python3
"""
Property-based tests for exceptions module.

Tests custom exception classes and their formatting.
"""

import pytest
from hypothesis import given, settings, assume, strategies as st
from hypothesis import HealthCheck

# Import exceptions module
try:
    from py3plex.exceptions import (
        Py3plexException,
        NetworkConstructionError,
        InvalidLayerError,
        InvalidNodeError,
        InvalidEdgeError,
    )
    EXCEPTIONS_AVAILABLE = True
except ImportError:
    EXCEPTIONS_AVAILABLE = False
    pytest.skip("exceptions module not available", allow_module_level=True)


# ============================================================================
# Property Tests: Py3plexException base class
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=30)
@given(message=st.text(min_size=1, max_size=100))
def test_py3plex_exception_creation(message):
    """Test that Py3plexException can be created with any message."""
    exc = Py3plexException(message)
    
    assert str(exc) == message or message in str(exc), \
        "Exception message should be preserved"
    assert exc.code == "PX001", \
        "Default error code should be PX001"


@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(
    message=st.text(min_size=1, max_size=100),
    code=st.text(min_size=3, max_size=10, alphabet=st.characters(whitelist_categories=('Lu', 'Nd')))
)
def test_py3plex_exception_custom_code(message, code):
    """Test that Py3plexException accepts custom error codes."""
    exc = Py3plexException(message, code=code)
    
    assert exc.code == code, \
        "Custom error code should be preserved"


@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(
    message=st.text(min_size=1, max_size=100),
    suggestions=st.lists(st.text(min_size=1, max_size=50), min_size=1, max_size=5)
)
def test_py3plex_exception_suggestions(message, suggestions):
    """Test that Py3plexException preserves suggestions."""
    exc = Py3plexException(message, suggestions=suggestions)
    
    assert exc.suggestions == suggestions, \
        "Suggestions should be preserved"
    assert len(exc.suggestions) > 0, \
        "Suggestions list should not be empty"


@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(
    message=st.text(min_size=1, max_size=100),
    notes=st.lists(st.text(min_size=1, max_size=50), min_size=1, max_size=5)
)
def test_py3plex_exception_notes(message, notes):
    """Test that Py3plexException preserves notes."""
    exc = Py3plexException(message, notes=notes)
    
    assert exc.notes == notes, \
        "Notes should be preserved"
    assert len(exc.notes) > 0, \
        "Notes list should not be empty"


@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(
    message=st.text(min_size=1, max_size=100),
    did_you_mean=st.text(min_size=1, max_size=50)
)
def test_py3plex_exception_did_you_mean(message, did_you_mean):
    """Test that Py3plexException preserves did_you_mean suggestion."""
    exc = Py3plexException(message, did_you_mean=did_you_mean)
    
    assert exc.did_you_mean == did_you_mean, \
        "did_you_mean suggestion should be preserved"


@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(
    message=st.text(min_size=1, max_size=100),
    context=st.dictionaries(
        st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll'))),
        st.one_of(st.integers(), st.text(max_size=50), st.floats(allow_nan=False, allow_infinity=False)),
        min_size=1,
        max_size=5
    )
)
def test_py3plex_exception_context(message, context):
    """Test that Py3plexException preserves context dictionary."""
    exc = Py3plexException(message, context=context)
    
    assert exc.context == context, \
        "Context dictionary should be preserved"


@pytest.mark.property
@settings(deadline=None, max_examples=10)
@given(message=st.text(min_size=1, max_size=100))
def test_py3plex_exception_is_exception(message):
    """Test that Py3plexException is a proper exception."""
    exc = Py3plexException(message)
    
    assert isinstance(exc, Exception), \
        "Py3plexException should be an Exception"
    
    # Should be raisable and catchable
    try:
        raise exc
    except Py3plexException as e:
        assert str(e) == str(exc), \
            "Exception should be catchable"
    except Exception:
        pytest.fail("Should be catchable as Py3plexException")


# ============================================================================
# Property Tests: NetworkConstructionError
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(message=st.text(min_size=1, max_size=100))
def test_network_construction_error_has_correct_code(message):
    """Test that NetworkConstructionError has the correct error code."""
    exc = NetworkConstructionError(message)
    
    assert exc.code == "PX208", \
        "NetworkConstructionError should have code PX208"
    assert isinstance(exc, Py3plexException), \
        "NetworkConstructionError should inherit from Py3plexException"


# ============================================================================
# Property Tests: InvalidLayerError
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=30)
@given(layer_name=st.text(min_size=1, max_size=30, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))))
def test_invalid_layer_error_creation(layer_name):
    """Test that InvalidLayerError can be created with layer name."""
    exc = InvalidLayerError(layer_name)
    
    assert layer_name in str(exc), \
        "Layer name should appear in error message"
    assert exc.code == "PX201", \
        "InvalidLayerError should have code PX201"


@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(
    layer_name=st.text(min_size=1, max_size=30, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))),
    available_layers=st.lists(
        st.text(min_size=1, max_size=30, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))),
        min_size=1,
        max_size=10
    )
)
def test_invalid_layer_error_with_available_layers(layer_name, available_layers):
    """Test that InvalidLayerError includes available layers in suggestions."""
    # Ensure layer_name is not in available_layers
    available_layers = [l for l in available_layers if l != layer_name]
    assume(len(available_layers) > 0)
    
    exc = InvalidLayerError(layer_name, available_layers=available_layers)
    
    assert layer_name in str(exc), \
        "Layer name should appear in error message"
    assert len(exc.suggestions) > 0, \
        "Should have suggestions when available_layers provided"


# ============================================================================
# Property Tests: InvalidNodeError
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=30)
@given(node_id=st.text(min_size=1, max_size=30))
def test_invalid_node_error_creation(node_id):
    """Test that InvalidNodeError can be created with node ID."""
    exc = InvalidNodeError(node_id)
    
    assert node_id in str(exc), \
        "Node ID should appear in error message"
    assert exc.code == "PX202", \
        "InvalidNodeError should have code PX202"


@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(
    node_id=st.integers(min_value=0, max_value=1000),
    available_nodes=st.lists(st.integers(min_value=0, max_value=1000), min_size=1, max_size=50)
)
def test_invalid_node_error_with_numeric_nodes(node_id, available_nodes):
    """Test that InvalidNodeError works with numeric node IDs."""
    # Ensure node_id is not in available_nodes
    available_nodes = [n for n in available_nodes if n != node_id]
    assume(len(available_nodes) > 0)
    
    exc = InvalidNodeError(node_id, available_nodes=available_nodes)
    
    assert str(node_id) in str(exc), \
        "Node ID should appear in error message"


# ============================================================================
# Property Tests: InvalidEdgeError
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=30)
@given(message=st.text(min_size=1, max_size=100))
def test_invalid_edge_error_has_correct_code(message):
    """Test that InvalidEdgeError has the correct error code."""
    exc = InvalidEdgeError(message)
    
    assert exc.code == "PX203", \
        "InvalidEdgeError should have code PX203"
    assert isinstance(exc, Py3plexException), \
        "InvalidEdgeError should inherit from Py3plexException"


# ============================================================================
# Property Tests: Exception hierarchy
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=10)
@given(message=st.text(min_size=1, max_size=100))
def test_all_exceptions_inherit_from_base(message):
    """Test that all custom exceptions inherit from Py3plexException."""
    exceptions = [
        NetworkConstructionError(message),
        InvalidLayerError("layer"),
        InvalidNodeError("node"),
        InvalidEdgeError(message),
    ]
    
    for exc in exceptions:
        assert isinstance(exc, Py3plexException), \
            f"{type(exc).__name__} should inherit from Py3plexException"
        assert isinstance(exc, Exception), \
            f"{type(exc).__name__} should be an Exception"


@pytest.mark.property
@settings(deadline=None, max_examples=10)
@given(message=st.text(min_size=1, max_size=100))
def test_all_exceptions_have_unique_codes(message):
    """Test that different exception types have unique error codes."""
    codes = {
        NetworkConstructionError(message).code,
        InvalidLayerError("layer").code,
        InvalidNodeError("node").code,
        InvalidEdgeError(message).code,
    }
    
    # All codes should be unique
    assert len(codes) == 4, \
        "Each exception type should have a unique error code"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-m', 'property'])
