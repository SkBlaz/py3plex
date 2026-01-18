"""Unified diagnostic system for py3plex.

This module provides a comprehensive diagnostic framework that transforms
errors, warnings, and info messages into actionable guidance for both
human researchers and LLMs.

The diagnostic system follows these principles:
1. Precise explanation of what went wrong
2. Concrete fix or alternative
3. Pointer to correct API surface
4. Machine-readable diagnostic object usable by LLMs, tests, and notebooks
"""

from .core import (
    Diagnostic,
    FixSuggestion,
    DiagnosticSeverity,
    DiagnosticContext,
    DiagnosticResult,
)
from .codes import ERROR_CODES, ErrorCode
from .utils import fuzzy_match, did_you_mean

__all__ = [
    "Diagnostic",
    "FixSuggestion",
    "DiagnosticSeverity",
    "DiagnosticContext",
    "DiagnosticResult",
    "ERROR_CODES",
    "ErrorCode",
    "fuzzy_match",
    "did_you_mean",
]
