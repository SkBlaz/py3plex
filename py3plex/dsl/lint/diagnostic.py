"""Diagnostic and suggestion models for DSL linting.

This module defines the core data structures for representing linting findings,
including diagnostics (errors, warnings, hints) and suggested fixes.
"""

from dataclasses import dataclass
from typing import Literal, Optional, Tuple


@dataclass
class SuggestedFix:
    """A suggested fix for a diagnostic.
    
    Attributes:
        replacement: The replacement text
        span: Tuple of (start_index, end_index) in the query string
    """
    replacement: str
    span: Tuple[int, int]


@dataclass
class Diagnostic:
    """A linting diagnostic (error, warning, info, or hint).
    
    Attributes:
        code: Diagnostic code (e.g., "DSL001", "PERF301")
        severity: Severity level
        message: Human-readable message
        span: Tuple of (start_index, end_index) in the query string
        suggested_fix: Optional suggested fix
    """
    code: str
    severity: Literal["error", "warning", "info", "hint"]
    message: str
    span: Tuple[int, int]
    suggested_fix: Optional[SuggestedFix] = None
    
    def __str__(self) -> str:
        """Format diagnostic for display."""
        severity_upper = self.severity.upper()
        start, end = self.span
        result = f"[{severity_upper}] {self.code}: {self.message} (at position {start}-{end})"
        if self.suggested_fix:
            result += f"\n  Suggestion: Replace with '{self.suggested_fix.replacement}'"
        return result
