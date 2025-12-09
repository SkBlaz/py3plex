"""Error types for DSL v2.

This module provides structured error types with helpful diagnostic information.
Errors include suggestions like "did you mean?" when applicable.
"""

from typing import List, Optional


def _levenshtein_distance(s1: str, s2: str) -> int:
    """Calculate Levenshtein distance between two strings."""
    if len(s1) < len(s2):
        return _levenshtein_distance(s2, s1)
    
    if len(s2) == 0:
        return len(s1)
    
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    
    return previous_row[-1]


def _suggest_similar(name: str, known_names: List[str], max_distance: int = 3) -> Optional[str]:
    """Suggest a similar name from known names.
    
    Args:
        name: The unknown name
        known_names: List of valid names
        max_distance: Maximum Levenshtein distance for suggestions
        
    Returns:
        The most similar known name, or None if none are close enough
    """
    if not known_names:
        return None
    
    best_match = None
    best_distance = max_distance + 1
    
    for known in known_names:
        distance = _levenshtein_distance(name.lower(), known.lower())
        if distance < best_distance:
            best_distance = distance
            best_match = known
    
    return best_match if best_distance <= max_distance else None


class DslError(Exception):
    """Base exception for all DSL errors."""
    
    def __init__(self, message: str, query: Optional[str] = None,
                 line: Optional[int] = None, column: Optional[int] = None):
        super().__init__(message)
        self.query = query
        self.line = line
        self.column = column
        
    def format_message(self) -> str:
        """Format the error message with context."""
        msg = str(self)
        
        if self.query and self.line is not None and self.column is not None:
            lines = self.query.split('\n')
            if 0 <= self.line - 1 < len(lines):
                context_line = lines[self.line - 1]
                pointer = ' ' * (self.column - 1) + '^'
                msg = f"{msg}\n\nAt line {self.line}, column {self.column}:\n{context_line}\n{pointer}"
        
        return msg


class DslSyntaxError(DslError):
    """Exception raised for DSL syntax errors."""
    pass


class DslExecutionError(DslError):
    """Exception raised for DSL execution errors."""
    pass


class UnknownAttributeError(DslError):
    """Exception raised when an unknown attribute is referenced.
    
    Attributes:
        attribute: The unknown attribute name
        known_attributes: List of valid attribute names
        suggestion: Suggested alternative, if any
    """
    
    def __init__(self, attribute: str, known_attributes: Optional[List[str]] = None,
                 query: Optional[str] = None, line: Optional[int] = None,
                 column: Optional[int] = None):
        self.attribute = attribute
        self.known_attributes = known_attributes or []
        self.suggestion = _suggest_similar(attribute, self.known_attributes)
        
        message = f"Unknown attribute '{attribute}'."
        if self.suggestion:
            message += f" Did you mean '{self.suggestion}'?"
        if self.known_attributes:
            message += f"\nKnown attributes: {', '.join(sorted(self.known_attributes)[:10])}"
        
        super().__init__(message, query, line, column)


class UnknownMeasureError(DslError):
    """Exception raised when an unknown measure is referenced.
    
    Attributes:
        measure: The unknown measure name
        known_measures: List of valid measure names
        suggestion: Suggested alternative, if any
    """
    
    def __init__(self, measure: str, known_measures: Optional[List[str]] = None,
                 query: Optional[str] = None, line: Optional[int] = None,
                 column: Optional[int] = None):
        self.measure = measure
        self.known_measures = known_measures or []
        self.suggestion = _suggest_similar(measure, self.known_measures)
        
        message = f"Unknown measure '{measure}'."
        if self.suggestion:
            message += f" Did you mean '{self.suggestion}'?"
        if self.known_measures:
            message += f"\nKnown measures: {', '.join(sorted(self.known_measures))}"
        
        super().__init__(message, query, line, column)


class UnknownLayerError(DslError):
    """Exception raised when an unknown layer is referenced.
    
    Attributes:
        layer: The unknown layer name
        known_layers: List of valid layer names
        suggestion: Suggested alternative, if any
    """
    
    def __init__(self, layer: str, known_layers: Optional[List[str]] = None,
                 query: Optional[str] = None, line: Optional[int] = None,
                 column: Optional[int] = None):
        self.layer = layer
        self.known_layers = known_layers or []
        self.suggestion = _suggest_similar(layer, self.known_layers)
        
        message = f"Unknown layer '{layer}'."
        if self.suggestion:
            message += f" Did you mean '{self.suggestion}'?"
        if self.known_layers:
            message += f"\nKnown layers: {', '.join(sorted(self.known_layers))}"
        
        super().__init__(message, query, line, column)


class ParameterMissingError(DslError):
    """Exception raised when a required parameter is not provided.
    
    Attributes:
        parameter: The missing parameter name
        provided_params: List of provided parameter names
    """
    
    def __init__(self, parameter: str, provided_params: Optional[List[str]] = None,
                 query: Optional[str] = None, line: Optional[int] = None,
                 column: Optional[int] = None):
        self.parameter = parameter
        self.provided_params = provided_params or []
        
        message = f"Missing required parameter ':{parameter}'."
        if self.provided_params:
            message += f"\nProvided parameters: {', '.join(sorted(self.provided_params))}"
        
        super().__init__(message, query, line, column)


class TypeMismatchError(DslError):
    """Exception raised when there's a type mismatch.
    
    Attributes:
        attribute: The attribute with the type mismatch
        expected_type: Expected type
        actual_type: Actual type received
    """
    
    def __init__(self, attribute: str, expected_type: str, actual_type: str,
                 query: Optional[str] = None, line: Optional[int] = None,
                 column: Optional[int] = None):
        self.attribute = attribute
        self.expected_type = expected_type
        self.actual_type = actual_type
        
        message = f"Type mismatch for attribute '{attribute}': expected {expected_type}, got {actual_type}."
        
        super().__init__(message, query, line, column)


class GroupingError(DslError):
    """Exception raised when a grouping operation is used incorrectly.
    
    This error is raised when operations that require active grouping
    (like coverage) are called without proper grouping context.
    """
    
    def __init__(self, message: str, query: Optional[str] = None,
                 line: Optional[int] = None, column: Optional[int] = None):
        super().__init__(message, query, line, column)


class DslMissingMetricError(DslError):
    """Exception raised when a required metric is missing and cannot be autocomputed.
    
    This error occurs when:
    - A query references a metric that hasn't been computed
    - Autocompute is disabled or the metric is not autocomputable
    - The metric is required for an operation (e.g., top_k, where clause)
    
    Attributes:
        metric: The missing metric name
        required_by: The operation that requires the metric
        autocompute_enabled: Whether autocompute was enabled
    """
    
    def __init__(self, metric: str, required_by: Optional[str] = None,
                 autocompute_enabled: bool = True,
                 query: Optional[str] = None, line: Optional[int] = None,
                 column: Optional[int] = None):
        self.metric = metric
        self.required_by = required_by
        self.autocompute_enabled = autocompute_enabled
        
        message = f"Missing required metric '{metric}'."
        
        if required_by:
            message += f" Required by: {required_by}."
        
        if not autocompute_enabled:
            message += f"\nAutocompute is disabled. Call .compute('{metric}') before using it."
        else:
            message += f"\nThis metric cannot be automatically computed. Call .compute('{metric}') explicitly."
        
        super().__init__(message, query, line, column)
