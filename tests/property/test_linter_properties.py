#!/usr/bin/env python3
"""
Property-based tests for the linter module.

Tests LintIssue construction, severity constants, LINT_ERROR_CODES mapping,
default code logic, and simple formatting invariants.
"""

import pytest
from hypothesis import given, settings, strategies as st

# Import linter module
try:
    from py3plex.linter import LintIssue, LINT_ERROR_CODES
    LINTER_AVAILABLE = True
except ImportError:
    LINTER_AVAILABLE = False
    pytest.skip("linter module not available", allow_module_level=True)


# ---------------------------------------------------------------------------
# Shared strategies
# ---------------------------------------------------------------------------

_short_message = st.text(
    min_size=1, max_size=80,
    alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters=" _.-:/"),
)
_severities = st.sampled_from([
    LintIssue.SEVERITY_ERROR,
    LintIssue.SEVERITY_WARNING,
    LintIssue.SEVERITY_INFO,
])
_pos_line = st.integers(min_value=1, max_value=10000)
_error_code = st.sampled_from(list(LINT_ERROR_CODES.values()))


# ---------------------------------------------------------------------------
# LINT_ERROR_CODES
# ---------------------------------------------------------------------------


@pytest.mark.property
def test_lint_error_codes_is_dict():
    """LINT_ERROR_CODES should be a dict."""
    assert isinstance(LINT_ERROR_CODES, dict)


@pytest.mark.property
def test_lint_error_codes_non_empty():
    """LINT_ERROR_CODES should have at least one entry."""
    assert len(LINT_ERROR_CODES) > 0


@pytest.mark.property
def test_lint_error_codes_values_are_strings():
    """All LINT_ERROR_CODES values should be strings."""
    for key, value in LINT_ERROR_CODES.items():
        assert isinstance(key, str), f"Key {key!r} should be a string"
        assert isinstance(value, str), f"Value {value!r} should be a string"


@pytest.mark.property
def test_lint_error_codes_values_start_with_px():
    """All LINT_ERROR_CODES values should start with 'PX'."""
    for value in LINT_ERROR_CODES.values():
        assert value.startswith("PX"), f"Code {value!r} should start with 'PX'"


@pytest.mark.property
def test_lint_error_codes_values_are_unique():
    """All LINT_ERROR_CODES values should be unique."""
    values = list(LINT_ERROR_CODES.values())
    assert len(values) == len(set(values)), "LINT_ERROR_CODES values should be unique"


@pytest.mark.property
def test_lint_error_codes_known_keys():
    """LINT_ERROR_CODES should contain standard expected keys."""
    for expected_key in ("file_not_found", "parse_error", "missing_column"):
        assert expected_key in LINT_ERROR_CODES, f"Expected key '{expected_key}' in LINT_ERROR_CODES"


# ---------------------------------------------------------------------------
# LintIssue severity constants
# ---------------------------------------------------------------------------


@pytest.mark.property
def test_severity_error_constant():
    """SEVERITY_ERROR constant is 'ERROR'."""
    assert LintIssue.SEVERITY_ERROR == "ERROR"


@pytest.mark.property
def test_severity_warning_constant():
    """SEVERITY_WARNING constant is 'WARNING'."""
    assert LintIssue.SEVERITY_WARNING == "WARNING"


@pytest.mark.property
def test_severity_info_constant():
    """SEVERITY_INFO constant is 'INFO'."""
    assert LintIssue.SEVERITY_INFO == "INFO"


# ---------------------------------------------------------------------------
# LintIssue construction
# ---------------------------------------------------------------------------


@pytest.mark.property
@settings(deadline=None, max_examples=30)
@given(severity=_severities, message=_short_message)
def test_lint_issue_basic_creation(severity, message):
    """LintIssue can be created with severity and message."""
    issue = LintIssue(severity=severity, message=message)
    assert issue.severity == severity
    assert issue.message == message


@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(message=_short_message)
def test_lint_issue_default_line_number_is_none(message):
    """LintIssue line_number defaults to None."""
    issue = LintIssue(severity=LintIssue.SEVERITY_ERROR, message=message)
    assert issue.line_number is None


@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(message=_short_message)
def test_lint_issue_default_suggestion_is_none(message):
    """LintIssue suggestion defaults to None."""
    issue = LintIssue(severity=LintIssue.SEVERITY_ERROR, message=message)
    assert issue.suggestion is None


@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(message=_short_message, line=_pos_line)
def test_lint_issue_stores_line_number(message, line):
    """LintIssue stores the provided line_number."""
    issue = LintIssue(severity=LintIssue.SEVERITY_WARNING, message=message, line_number=line)
    assert issue.line_number == line


@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(message=_short_message, suggestion=_short_message)
def test_lint_issue_stores_suggestion(message, suggestion):
    """LintIssue stores the provided suggestion."""
    issue = LintIssue(severity=LintIssue.SEVERITY_INFO, message=message, suggestion=suggestion)
    assert issue.suggestion == suggestion


# ---------------------------------------------------------------------------
# LintIssue – default code logic
# ---------------------------------------------------------------------------


@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(message=_short_message)
def test_lint_issue_error_default_code(message):
    """LintIssue ERROR severity uses default code PX105."""
    issue = LintIssue(severity=LintIssue.SEVERITY_ERROR, message=message)
    assert issue.code == "PX105"


@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(message=_short_message)
def test_lint_issue_warning_default_code(message):
    """LintIssue WARNING severity uses default code PX107."""
    issue = LintIssue(severity=LintIssue.SEVERITY_WARNING, message=message)
    assert issue.code == "PX107"


@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(message=_short_message)
def test_lint_issue_info_default_code(message):
    """LintIssue INFO severity uses a fallback code."""
    issue = LintIssue(severity=LintIssue.SEVERITY_INFO, message=message)
    assert isinstance(issue.code, str)
    assert len(issue.code) > 0


@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(message=_short_message, code=_error_code)
def test_lint_issue_custom_code_overrides_default(message, code):
    """LintIssue uses the provided code, not the default."""
    issue = LintIssue(severity=LintIssue.SEVERITY_ERROR, message=message, code=code)
    assert issue.code == code


# ---------------------------------------------------------------------------
# LintIssue – simple_format / __str__
# ---------------------------------------------------------------------------


@pytest.mark.property
@settings(deadline=None, max_examples=30)
@given(severity=_severities, message=_short_message)
def test_lint_issue_str_is_string(severity, message):
    """str(LintIssue) returns a non-empty string."""
    issue = LintIssue(severity=severity, message=message)
    result = str(issue)
    assert isinstance(result, str)
    assert len(result) > 0


@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(message=_short_message, line=_pos_line)
def test_lint_issue_format_contains_message(message, line):
    """_simple_format() includes the message text."""
    issue = LintIssue(severity=LintIssue.SEVERITY_ERROR, message=message, line_number=line)
    formatted = issue._simple_format()
    assert message in formatted


@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(message=_short_message, line=_pos_line)
def test_lint_issue_format_contains_severity(message, line):
    """_simple_format() includes the severity label."""
    for sev in (LintIssue.SEVERITY_ERROR, LintIssue.SEVERITY_WARNING, LintIssue.SEVERITY_INFO):
        issue = LintIssue(severity=sev, message=message, line_number=line)
        formatted = issue._simple_format()
        assert sev in formatted


@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(message=_short_message, line=_pos_line)
def test_lint_issue_format_contains_line_number(message, line):
    """_simple_format() includes the line number when provided."""
    issue = LintIssue(severity=LintIssue.SEVERITY_ERROR, message=message, line_number=line)
    formatted = issue._simple_format()
    assert str(line) in formatted


@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(message=_short_message, suggestion=_short_message)
def test_lint_issue_format_contains_suggestion(message, suggestion):
    """_simple_format() includes the suggestion when provided."""
    issue = LintIssue(
        severity=LintIssue.SEVERITY_WARNING,
        message=message,
        suggestion=suggestion,
    )
    formatted = issue._simple_format()
    assert suggestion in formatted


@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(severity=_severities, message=_short_message)
def test_lint_issue_format_no_color_is_string(severity, message):
    """LintIssue.format(use_color=False) returns a non-empty string."""
    issue = LintIssue(severity=severity, message=message)
    result = issue.format(use_color=False)
    assert isinstance(result, str)
    assert len(result) > 0


# ---------------------------------------------------------------------------
# LintIssue – column defaults
# ---------------------------------------------------------------------------


@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(message=_short_message)
def test_lint_issue_default_column_is_one(message):
    """LintIssue column defaults to 1."""
    issue = LintIssue(severity=LintIssue.SEVERITY_ERROR, message=message)
    assert issue.column == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "property"])
