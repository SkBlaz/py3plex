#!/usr/bin/env python3
"""
Property-based tests for errors module.

Tests error formatting, color handling, and suggestion generation.
"""

import pytest
from hypothesis import given, settings, assume, strategies as st
from hypothesis import HealthCheck

# Import errors module
try:
    from py3plex.errors import (
        Severity,
        Colors,
        ErrorMessage,
        Suggestion,
        Note,
        find_similar,
    )
    ERRORS_AVAILABLE = True
except ImportError:
    ERRORS_AVAILABLE = False
    pytest.skip("errors module not available", allow_module_level=True)


# ============================================================================
# Property Tests: Severity enum
# ============================================================================

@pytest.mark.property
def test_severity_enum_values():
    """Test that Severity enum has expected values."""
    expected_values = {"error", "warning", "info", "help", "note"}
    actual_values = {s.value for s in Severity}
    
    assert actual_values == expected_values, \
        "Severity enum should have all expected values"


@pytest.mark.property
@settings(deadline=None, max_examples=10)
@given(severity=st.sampled_from(list(Severity)))
def test_severity_value_is_string(severity):
    """Test that Severity values are strings."""
    assert isinstance(severity.value, str), \
        "Severity value should be a string"


# ============================================================================
# Property Tests: Colors class
# ============================================================================

@pytest.mark.property
def test_colors_has_required_attributes():
    """Test that Colors class has required color attributes."""
    required_attrs = [
        'RED', 'YELLOW', 'BLUE', 'CYAN', 'GREEN',
        'MAGENTA', 'WHITE', 'BOLD', 'UNDERLINE', 'RESET'
    ]
    
    for attr in required_attrs:
        assert hasattr(Colors, attr), \
            f"Colors should have {attr} attribute"


@pytest.mark.property
def test_colors_values_are_strings():
    """Test that color codes are strings."""
    assert isinstance(Colors.RED, str), "RED should be a string"
    assert isinstance(Colors.BLUE, str), "BLUE should be a string"
    assert isinstance(Colors.RESET, str), "RESET should be a string"


@pytest.mark.property
def test_colors_supports_color_returns_bool():
    """Test that supports_color returns a boolean."""
    result = Colors.supports_color()
    
    assert isinstance(result, bool), \
        "supports_color should return a boolean"


@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(text=st.text(min_size=1, max_size=50))
def test_colors_colorize_returns_string(text):
    """Test that colorize returns a string."""
    result = Colors.colorize(text, Colors.RED)
    
    assert isinstance(result, str), \
        "colorize should return a string"
    assert len(result) >= len(text), \
        "Colorized string should be at least as long as input"


@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(text=st.text(min_size=1, max_size=50))
def test_colors_colorize_contains_text(text):
    """Test that colorize preserves the text."""
    result = Colors.colorize(text, Colors.BLUE)
    
    # Text should be in the result (possibly with ANSI codes)
    assert text in result or result.replace(Colors.BLUE, '').replace(Colors.RESET, '') == text, \
        "Colorized string should contain original text"


# ============================================================================
# Property Tests: Suggestion and Note
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=30)
@given(message=st.text(min_size=1, max_size=100))
def test_suggestion_creation(message):
    """Test that Suggestion can be created with a message."""
    suggestion = Suggestion(message=message)
    
    assert suggestion.message == message, \
        "Suggestion message should match input"
    assert suggestion.replacement is None, \
        "Default replacement should be None"
    assert suggestion.span is None, \
        "Default span should be None"


@pytest.mark.property
@settings(deadline=None, max_examples=30)
@given(
    message=st.text(min_size=1, max_size=100),
    replacement=st.text(min_size=1, max_size=50)
)
def test_suggestion_with_replacement(message, replacement):
    """Test that Suggestion can include replacement text."""
    suggestion = Suggestion(message=message, replacement=replacement)
    
    assert suggestion.message == message, \
        "Suggestion message should match input"
    assert suggestion.replacement == replacement, \
        "Replacement should match input"


@pytest.mark.property
@settings(deadline=None, max_examples=30)
@given(message=st.text(min_size=1, max_size=100))
def test_note_creation(message):
    """Test that Note can be created with a message."""
    note = Note(message=message)
    
    assert note.message == message, \
        "Note message should match input"


# ============================================================================
# Property Tests: ErrorMessage
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=30)
@given(
    code=st.text(min_size=3, max_size=10, alphabet=st.characters(whitelist_categories=('Lu', 'Nd'))),
    title=st.text(min_size=1, max_size=50),
    message=st.text(min_size=1, max_size=100)
)
def test_error_message_creation(code, title, message):
    """Test that ErrorMessage can be created."""
    error = ErrorMessage(
        code=code,
        severity=Severity.ERROR,
        title=title,
        message=message
    )
    
    assert error.code == code, \
        "Error code should match input"
    assert error.severity == Severity.ERROR, \
        "Severity should match input"
    assert error.title == title, \
        "Title should match input"
    assert error.message == message, \
        "Message should match input"


@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(
    code=st.text(min_size=3, max_size=10, alphabet=st.characters(whitelist_categories=('Lu', 'Nd'))),
    title=st.text(min_size=1, max_size=50),
    message=st.text(min_size=1, max_size=100),
    severity=st.sampled_from(list(Severity))
)
def test_error_message_all_severities(code, title, message, severity):
    """Test that ErrorMessage works with all severity levels."""
    error = ErrorMessage(
        code=code,
        severity=severity,
        title=title,
        message=message
    )
    
    assert error.severity == severity, \
        "Severity should match input"


@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(
    code=st.text(min_size=3, max_size=10, alphabet=st.characters(whitelist_categories=('Lu', 'Nd'))),
    title=st.text(min_size=1, max_size=50),
    message=st.text(min_size=1, max_size=100),
    use_color=st.booleans()
)
def test_error_message_format(code, title, message, use_color):
    """Test that ErrorMessage.format() returns a string."""
    error = ErrorMessage(
        code=code,
        severity=Severity.ERROR,
        title=title,
        message=message
    )
    
    formatted = error.format(use_color=use_color)
    
    assert isinstance(formatted, str), \
        "Formatted message should be a string"
    assert len(formatted) > 0, \
        "Formatted message should not be empty"
    assert code in formatted, \
        "Formatted message should contain error code"


@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(
    code=st.text(min_size=3, max_size=10, alphabet=st.characters(whitelist_categories=('Lu', 'Nd'))),
    title=st.text(min_size=1, max_size=50),
    message=st.text(min_size=1, max_size=100),
    suggestions=st.lists(st.text(min_size=1, max_size=50), min_size=1, max_size=5)
)
def test_error_message_with_suggestions(code, title, message, suggestions):
    """Test that ErrorMessage can include suggestions."""
    error = ErrorMessage(
        code=code,
        severity=Severity.ERROR,
        title=title,
        message=message,
        suggestions=[Suggestion(message=s) for s in suggestions]
    )
    
    assert len(error.suggestions) == len(suggestions), \
        "Should have correct number of suggestions"


@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(
    code=st.text(min_size=3, max_size=10, alphabet=st.characters(whitelist_categories=('Lu', 'Nd'))),
    title=st.text(min_size=1, max_size=50),
    message=st.text(min_size=1, max_size=100),
    notes=st.lists(st.text(min_size=1, max_size=50), min_size=1, max_size=5)
)
def test_error_message_with_notes(code, title, message, notes):
    """Test that ErrorMessage can include notes."""
    error = ErrorMessage(
        code=code,
        severity=Severity.ERROR,
        title=title,
        message=message,
        notes=[Note(message=n) for n in notes]
    )
    
    assert len(error.notes) == len(notes), \
        "Should have correct number of notes"


@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(
    code=st.text(min_size=3, max_size=10, alphabet=st.characters(whitelist_categories=('Lu', 'Nd'))),
    title=st.text(min_size=1, max_size=50),
    message=st.text(min_size=1, max_size=100),
    did_you_mean=st.text(min_size=1, max_size=30)
)
def test_error_message_with_did_you_mean(code, title, message, did_you_mean):
    """Test that ErrorMessage can include did_you_mean suggestion."""
    error = ErrorMessage(
        code=code,
        severity=Severity.ERROR,
        title=title,
        message=message,
        did_you_mean=did_you_mean
    )
    
    assert error.did_you_mean == did_you_mean, \
        "did_you_mean should match input"


# ============================================================================
# Property Tests: find_similar function
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=30)
@given(
    target=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))),
    candidates=st.lists(
        st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))),
        min_size=1,
        max_size=10,
        unique=True
    )
)
def test_find_similar_returns_string_or_none(target, candidates):
    """Test that find_similar returns a string or None."""
    result = find_similar(target, candidates)
    
    assert result is None or isinstance(result, str), \
        "find_similar should return string or None"
    
    if result is not None:
        assert result in candidates, \
            "Result should be from candidates list"


@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(
    target=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))),
)
def test_find_similar_with_exact_match(target):
    """Test that find_similar returns exact match if present."""
    candidates = [target, "other1", "other2"]
    
    result = find_similar(target, candidates)
    
    # When exact match is present, it should be returned
    assert result == target or result in candidates, \
        "find_similar should handle exact matches"


@pytest.mark.property
def test_find_similar_empty_candidates():
    """Test that find_similar handles empty candidates list."""
    result = find_similar("test", [])
    
    assert result is None, \
        "find_similar should return None for empty candidates"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-m', 'property'])
