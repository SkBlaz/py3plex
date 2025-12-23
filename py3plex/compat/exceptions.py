"""
Exceptions for the compatibility layer.
"""

from typing import Any, Optional


class CompatibilityError(Exception):
    """
    Raised when a conversion cannot preserve all data in the target format.
    
    This exception is raised in strict mode when the target format cannot
    represent some aspect of the source graph (e.g., multigraph edges in
    a simple graph format, or complex attributes in a matrix format).
    
    Attributes:
        message: Human-readable error message
        reason: Specific reason for incompatibility
        suggestions: List of suggested remediation actions
    """
    
    def __init__(
        self,
        message: str,
        reason: Optional[str] = None,
        suggestions: Optional[list[str]] = None,
    ):
        super().__init__(message)
        self.reason = reason
        self.suggestions = suggestions or []
    
    def __str__(self) -> str:
        parts = [super().__str__()]
        if self.reason:
            parts.append(f"\nReason: {self.reason}")
        if self.suggestions:
            parts.append("\nSuggestions:")
            for suggestion in self.suggestions:
                parts.append(f"  - {suggestion}")
        return "".join(parts)


class SchemaError(Exception):
    """
    Raised when schema validation or inference fails.
    
    This exception is raised when:
    - Schema validation detects type mismatches or invalid data
    - Schema inference encounters ambiguous or unsupported types
    - Required schema constraints are violated
    
    Attributes:
        message: Human-readable error message
        field: The field or attribute that caused the error
        expected: Expected type or value
        actual: Actual type or value found
    """
    
    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        expected: Optional[Any] = None,
        actual: Optional[Any] = None,
    ):
        super().__init__(message)
        self.field = field
        self.expected = expected
        self.actual = actual
    
    def __str__(self) -> str:
        parts = [super().__str__()]
        if self.field:
            parts.append(f"\nField: {self.field}")
        if self.expected is not None:
            parts.append(f"\nExpected: {self.expected}")
        if self.actual is not None:
            parts.append(f"\nActual: {self.actual}")
        return "".join(parts)


class ConversionNotSupportedError(Exception):
    """
    Raised when a requested conversion is not supported.
    
    This exception is raised when:
    - The target format is not recognized or implemented
    - Required optional dependencies are not installed
    - The conversion is fundamentally incompatible (e.g., temporal to static)
    """
    
    pass
