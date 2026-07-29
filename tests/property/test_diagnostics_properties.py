#!/usr/bin/env python3
"""
Property-based tests for diagnostics module.

Tests Diagnostic, FixSuggestion, DiagnosticContext, and DiagnosticSeverity
invariants and serialisation properties.
"""

import pytest
from hypothesis import given, settings, strategies as st

# Import diagnostics module
try:
    from py3plex.diagnostics import (
        Diagnostic,
        DiagnosticSeverity,
        DiagnosticContext,
        FixSuggestion,
    )
    DIAGNOSTICS_AVAILABLE = True
except ImportError:
    DIAGNOSTICS_AVAILABLE = False
    pytest.skip("diagnostics module not available", allow_module_level=True)


# ---------------------------------------------------------------------------
# Shared strategies
# ---------------------------------------------------------------------------

_severities = st.sampled_from(list(DiagnosticSeverity))
_short_text = st.text(min_size=1, max_size=60, alphabet=st.characters(
    whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters=" _.-:"
))
_error_code = st.text(
    min_size=3, max_size=15,
    alphabet=st.characters(whitelist_categories=("Lu", "Nd"), whitelist_characters="_"),
)


# ---------------------------------------------------------------------------
# DiagnosticSeverity
# ---------------------------------------------------------------------------


@pytest.mark.property
def test_severity_enum_has_expected_values():
    """DiagnosticSeverity should have error, warning and info values."""
    values = {s.value for s in DiagnosticSeverity}
    assert "error" in values
    assert "warning" in values
    assert "info" in values


@pytest.mark.property
@settings(deadline=None, max_examples=15)
@given(severity=_severities)
def test_severity_value_is_string(severity):
    """Each DiagnosticSeverity value should be a non-empty string."""
    assert isinstance(severity.value, str)
    assert len(severity.value) > 0


# ---------------------------------------------------------------------------
# FixSuggestion
# ---------------------------------------------------------------------------


@pytest.mark.property
@settings(deadline=None, max_examples=30)
@given(description=_short_text)
def test_fix_suggestion_creation(description):
    """FixSuggestion can be created with any non-empty description."""
    fix = FixSuggestion(description=description)
    assert fix.description == description
    assert fix.replacement is None
    assert fix.example is None


@pytest.mark.property
@settings(deadline=None, max_examples=30)
@given(
    description=_short_text,
    replacement=st.one_of(st.none(), _short_text),
    example=st.one_of(st.none(), _short_text),
)
def test_fix_suggestion_to_dict_contains_description(description, replacement, example):
    """FixSuggestion.to_dict() always includes description."""
    fix = FixSuggestion(description=description, replacement=replacement, example=example)
    d = fix.to_dict()
    assert "description" in d
    assert d["description"] == description


@pytest.mark.property
@settings(deadline=None, max_examples=30)
@given(description=_short_text, replacement=_short_text)
def test_fix_suggestion_dict_excludes_none_fields(description, replacement):
    """FixSuggestion.to_dict() omits None fields."""
    fix = FixSuggestion(description=description, replacement=replacement, example=None)
    d = fix.to_dict()
    assert "example" not in d
    assert "replacement" in d


# ---------------------------------------------------------------------------
# DiagnosticContext
# ---------------------------------------------------------------------------


@pytest.mark.property
def test_diagnostic_context_defaults():
    """DiagnosticContext has all-None defaults."""
    ctx = DiagnosticContext()
    assert ctx.ast_node is None
    assert ctx.builder_method is None
    assert ctx.query_fragment is None
    assert ctx.line_number is None


@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(
    method=st.one_of(st.none(), _short_text),
    node=st.one_of(st.none(), _short_text),
)
def test_diagnostic_context_to_dict_omits_none(method, node):
    """DiagnosticContext.to_dict() does not include None fields."""
    ctx = DiagnosticContext(builder_method=method, ast_node=node)
    d = ctx.to_dict()
    for key, val in d.items():
        assert val is not None, f"to_dict should not include None for key '{key}'"


@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(method=_short_text)
def test_diagnostic_context_preserves_method(method):
    """DiagnosticContext.to_dict() preserves builder_method."""
    ctx = DiagnosticContext(builder_method=method)
    d = ctx.to_dict()
    assert d.get("builder_method") == method


# ---------------------------------------------------------------------------
# Diagnostic
# ---------------------------------------------------------------------------


@pytest.mark.property
@settings(deadline=None, max_examples=40)
@given(
    severity=_severities,
    code=_error_code,
    message=_short_text,
)
def test_diagnostic_creation(severity, code, message):
    """Diagnostic can be created with any valid severity, code and message."""
    diag = Diagnostic(severity=severity, code=code, message=message)
    assert diag.severity == severity
    assert diag.code == code
    assert diag.message == message
    assert diag.fixes == []
    assert diag.related == []


@pytest.mark.property
@settings(deadline=None, max_examples=30)
@given(
    severity=_severities,
    code=_error_code,
    message=_short_text,
)
def test_diagnostic_to_dict_required_keys(severity, code, message):
    """Diagnostic.to_dict() always includes severity, code, and message."""
    diag = Diagnostic(severity=severity, code=code, message=message)
    d = diag.to_dict()
    assert "severity" in d
    assert "code" in d
    assert "message" in d
    assert d["severity"] == severity.value
    assert d["code"] == code
    assert d["message"] == message


@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(
    severity=_severities,
    code=_error_code,
    message=_short_text,
)
def test_diagnostic_to_dict_omits_empty_optionals(severity, code, message):
    """Diagnostic.to_dict() should omit absent optional fields."""
    diag = Diagnostic(severity=severity, code=code, message=message)
    d = diag.to_dict()
    # No cause, no context, no fixes, no related supplied
    assert "cause" not in d
    assert "context" not in d
    assert "fixes" not in d
    assert "related" not in d


@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(
    severity=_severities,
    code=_error_code,
    message=_short_text,
    cause=_short_text,
)
def test_diagnostic_to_dict_includes_cause_when_set(severity, code, message, cause):
    """Diagnostic.to_dict() includes cause when provided."""
    diag = Diagnostic(severity=severity, code=code, message=message, cause=cause)
    d = diag.to_dict()
    assert "cause" in d
    assert d["cause"] == cause


@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(
    severity=_severities,
    code=_error_code,
    message=_short_text,
    desc=_short_text,
)
def test_diagnostic_with_fix_in_dict(severity, code, message, desc):
    """Diagnostic.to_dict() includes fixes list when fixes are added."""
    fix = FixSuggestion(description=desc)
    diag = Diagnostic(severity=severity, code=code, message=message, fixes=[fix])
    d = diag.to_dict()
    assert "fixes" in d
    assert len(d["fixes"]) == 1
    assert d["fixes"][0]["description"] == desc


@pytest.mark.property
@settings(deadline=None, max_examples=15)
@given(
    severity=_severities,
    code=_error_code,
    message=_short_text,
)
def test_diagnostic_severity_value_in_dict_is_string(severity, code, message):
    """Diagnostic.to_dict() severity is a plain string (not enum)."""
    diag = Diagnostic(severity=severity, code=code, message=message)
    d = diag.to_dict()
    assert isinstance(d["severity"], str)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "property"])
