"""Error types for DSL v2.

This module provides structured error types with helpful diagnostic information.
Errors include suggestions like "did you mean?" when applicable.
"""

from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from py3plex.diagnostics import Diagnostic


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
    """Base exception for all DSL errors.
    
    Attributes:
        query: Query string that caused the error
        line: Line number in query (if applicable)
        column: Column number in query (if applicable)
        diagnostic: Optional Diagnostic object with structured error info
    """
    
    def __init__(self, message: str, query: Optional[str] = None,
                 line: Optional[int] = None, column: Optional[int] = None,
                 diagnostic: Optional["Diagnostic"] = None):
        super().__init__(message)
        self.query = query
        self.line = line
        self.column = column
        self.diagnostic = diagnostic
    
    def to_diagnostic(self) -> Optional["Diagnostic"]:
        """Get the diagnostic object for this error.
        
        Returns:
            Diagnostic object if available, None otherwise
        """
        return self.diagnostic
        
    def format_message(self) -> str:
        """Format the error message with context."""
        # If we have a diagnostic, use its formatting
        if self.diagnostic:
            return self.diagnostic.format(use_color=True)
        
        msg = str(self)
        
        if self.query and self.line is not None and self.column is not None:
            lines = self.query.split('\n')
            if 0 <= self.line - 1 < len(lines):
                context_line = lines[self.line - 1]
                pointer = ' ' * (self.column - 1) + '^'
                msg = f"{msg}\n\nAt line {self.line}, column {self.column}:\n{context_line}\n{pointer}"
        
        return msg


class DslSyntaxError(DslError):
    """Exception raised for DSL syntax errors.
    
    Enhanced with pedagogical guidance:
    - What the user likely intended
    - Why the syntax is invalid
    - Corrected query examples
    - Common pitfall notes
    """
    
    def __init__(self, message: str, intent: Optional[str] = None,
                 why_failed: Optional[str] = None,
                 examples: Optional[List[str]] = None,
                 pitfall: Optional[str] = None,
                 **kwargs):
        """Initialize with pedagogical context.
        
        Args:
            message: Base error message
            intent: What the user likely intended to do
            why_failed: Explanation of why the syntax is invalid
            examples: List of corrected query examples (1-2 recommended)
            pitfall: Common pitfall note to help avoid this error
            **kwargs: Additional DslError parameters
        """
        full_message = message
        
        if intent:
            full_message += f"\n\n[INTENT] You probably wanted to: {intent}"
        
        if why_failed:
            full_message += f"\n\n[ERROR] Why this failed: {why_failed}"
        
        if examples:
            full_message += "\n\n[CORRECT] Corrected examples:"
            for i, example in enumerate(examples, 1):
                full_message += f"\n  {i}. {example}"
        
        if pitfall:
            full_message += f"\n\n[WARNING]  Common pitfall: {pitfall}"
        
        super().__init__(full_message, **kwargs)


class DslExecutionError(DslError):
    """Exception raised for DSL execution errors.
    
    Enhanced with pedagogical guidance for runtime issues.
    """
    
    def __init__(self, message: str, intent: Optional[str] = None,
                 why_failed: Optional[str] = None,
                 examples: Optional[List[str]] = None,
                 pitfall: Optional[str] = None,
                 **kwargs):
        """Initialize with pedagogical context.
        
        Args:
            message: Base error message
            intent: What the user likely intended
            why_failed: Explanation in DSL or multilayer terms
            examples: List of corrected query examples
            pitfall: Common pitfall note
            **kwargs: Additional DslError parameters
        """
        full_message = message
        
        if intent:
            full_message += f"\n\n[INTENT] You probably wanted to: {intent}"
        
        if why_failed:
            full_message += f"\n\n[ERROR] Why this failed: {why_failed}"
        
        if examples:
            full_message += "\n\n[CORRECT] Corrected examples:"
            for i, example in enumerate(examples, 1):
                full_message += f"\n  {i}. {example}"
        
        if pitfall:
            full_message += f"\n\n[WARNING]  Common pitfall: {pitfall}"
        
        super().__init__(full_message, **kwargs)


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
        
        # Create diagnostic object
        from py3plex.diagnostics import builders as diag_builders
        diagnostic = diag_builders.unknown_field_error(
            field=attribute,
            known_fields=self.known_attributes,
            target_type="node",
            builder_method="where",
            query_fragment=f"{attribute}__gt=3"
        )
        
        super().__init__(message, query, line, column, diagnostic=diagnostic)


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
        
        # Create diagnostic object
        from py3plex.diagnostics import builders as diag_builders
        diagnostic = diag_builders.unknown_measure_error(
            measure=measure,
            known_measures=self.known_measures,
            builder_method="compute"
        )
        
        super().__init__(message, query, line, column, diagnostic=diagnostic)


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
        
        # Create diagnostic object
        from py3plex.diagnostics import builders as diag_builders
        diagnostic = diag_builders.unknown_layer_error(
            layer=layer,
            known_layers=self.known_layers,
            builder_method="from_layers"
        )
        
        super().__init__(message, query, line, column, diagnostic=diagnostic)


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


class MultilayerSemanticError(DslError):
    """Exception raised for multilayer-specific semantic issues.
    
    This error helps users understand common multilayer network pitfalls:
    - Node replicas vs physical nodes
    - Degree meaning ambiguity (intra-layer, inter-layer, aggregate)
    - Coverage filters removing expected nodes
    - Global vs per-layer operations
    """
    
    def __init__(self, message: str, 
                 semantic_issue: str,
                 multilayer_context: Optional[str] = None,
                 examples: Optional[List[str]] = None,
                 **kwargs):
        """Initialize with multilayer-specific context.
        
        Args:
            message: Base error message
            semantic_issue: The specific multilayer semantic issue
            multilayer_context: Explanation of multilayer network semantics
            examples: Corrected query examples
            **kwargs: Additional DslError parameters
        """
        full_message = message
        
        if semantic_issue:
            full_message += f"\n\n[STATE] Multilayer semantic issue: {semantic_issue}"
        
        if multilayer_context:
            full_message += f"\n\n[CONCEPT] Multilayer concept: {multilayer_context}"
        
        if examples:
            full_message += "\n\n[CORRECT] Recommended approach:"
            for i, example in enumerate(examples, 1):
                full_message += f"\n  {i}. {example}"
        
        super().__init__(full_message, **kwargs)


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


class DSLCompileError(DslError):
    """Exception raised for DSL compile-time errors with rich diagnostics.
    
    This error provides compiler-quality error messages with:
    - Stage identification (where error occurred in DSL pipeline)
    - Field-specific context
    - Actionable suggestions
    - AST summary for debugging
    
    Attributes:
        message: Error message
        stage: DSL stage where error occurred (e.g., 'where', 'compute', 'join')
        field: Field name related to the error, if applicable
        suggestion: Actionable suggestion to fix the error
        ast_summary: Compact AST summary for context
        expected: Expected value/type, if applicable
        actual: Actual value/type received, if applicable
    """
    
    def __init__(
        self,
        message: str,
        stage: Optional[str] = None,
        field: Optional[str] = None,
        suggestion: Optional[str] = None,
        ast_summary: Optional[str] = None,
        expected: Optional[str] = None,
        actual: Optional[str] = None,
        query: Optional[str] = None,
        line: Optional[int] = None,
        column: Optional[int] = None,
    ):
        self.stage = stage
        self.field = field
        self.suggestion = suggestion
        self.ast_summary = ast_summary
        self.expected = expected
        self.actual = actual
        
        # Enhance message with structured diagnostics
        full_message = message
        
        if stage:
            full_message += f"\n  Stage: {stage}"
        
        if field:
            full_message += f"\n  Field: {field}"
        
        if expected and actual:
            full_message += f"\n  Expected: {expected}"
            full_message += f"\n  Actual: {actual}"
        
        if suggestion:
            full_message += f"\n  Suggestion: {suggestion}"
        
        if ast_summary:
            full_message += f"\n  Query: {ast_summary}"
        
        super().__init__(full_message, query, line, column)


class InvalidJoinKeyError(DSLCompileError):
    """Exception raised when join keys are invalid or missing from schema.
    
    Attributes:
        missing_keys: List of keys not found in the schema
        available_fields: List of available fields in the schema
        side: Which side of the join has the issue ('left' or 'right')
    """
    
    def __init__(
        self,
        missing_keys: List[str],
        available_fields: List[str],
        side: str = "left",
        ast_summary: Optional[str] = None,
    ):
        self.missing_keys = missing_keys
        self.available_fields = available_fields
        self.side = side
        
        message = f"Join key(s) not found in {side} schema: {', '.join(missing_keys)}"
        
        suggestion = f"Available fields in {side}: {', '.join(sorted(available_fields)[:10])}"
        if len(available_fields) > 10:
            suggestion += f" ... and {len(available_fields) - 10} more"
        
        super().__init__(
            message=message,
            stage="join",
            suggestion=suggestion,
            ast_summary=ast_summary,
        )


class ComputedFieldMisuseError(DSLCompileError):
    """Exception raised when filtering on a computed field before it's computed.
    
    Attributes:
        field: The computed field being misused
        stage: Stage where the misuse occurred
    """
    
    def __init__(
        self,
        field: str,
        stage: str = "where",
        ast_summary: Optional[str] = None,
    ):
        message = f"Field '{field}' is computed but not available at this stage"
        suggestion = f"Add .compute('{field}') before .{stage}()"
        
        super().__init__(
            message=message,
            stage=stage,
            field=field,
            suggestion=suggestion,
            ast_summary=ast_summary,
        )


class InvalidGroupAggregateError(DSLCompileError):
    """Exception raised when filtering on raw fields after grouping.
    
    Attributes:
        field: The field being filtered
        available_aggregates: List of available aggregate functions
    """
    
    def __init__(
        self,
        field: str,
        available_aggregates: Optional[List[str]] = None,
        ast_summary: Optional[str] = None,
    ):
        message = f"Filtering on raw field '{field}' after grouping is ambiguous"
        
        if available_aggregates:
            agg_list = ", ".join(available_aggregates[:5])
            suggestion = f"Use an aggregate (e.g., {field}__mean__gt=3) or move filter before grouping"
        else:
            suggestion = "Move filter before grouping or use aggregated form"
        
        super().__init__(
            message=message,
            stage="where",
            field=field,
            suggestion=suggestion,
            ast_summary=ast_summary,
        )


# ==============================================================================
# AST Validation Errors
# ==============================================================================


class ASTValidationError(DslError):
    """Base class for AST validation errors.
    
    Raised when AST structure is invalid, incomplete, or incompatible.
    """
    pass


class ASTSchemaVersionError(ASTValidationError):
    """Exception raised when AST schema version is incompatible.
    
    Attributes:
        found_version: The schema version found in the AST
        expected_version: The expected schema version
    """
    
    def __init__(self, found_version: str, expected_version: str = "2.0"):
        self.found_version = found_version
        self.expected_version = expected_version
        message = (
            f"Incompatible AST schema version: {found_version} "
            f"(expected {expected_version})"
        )
        super().__init__(message)


class ASTInvalidStructureError(ASTValidationError):
    """Exception raised when AST structure is invalid.
    
    Attributes:
        issue: Description of the structural issue
        ast_fragment: Fragment of AST causing the issue
    """
    
    def __init__(self, issue: str, ast_fragment: Optional[str] = None):
        self.issue = issue
        self.ast_fragment = ast_fragment
        message = f"Invalid AST structure: {issue}"
        if ast_fragment:
            message += f"\nAST fragment: {ast_fragment}"
        super().__init__(message)


class ASTMissingFieldError(ASTValidationError):
    """Exception raised when required AST field is missing.
    
    Attributes:
        field: The missing field name
        ast_type: The AST node type missing the field
    """
    
    def __init__(self, field: str, ast_type: str):
        self.field = field
        self.ast_type = ast_type
        message = f"Required field '{field}' missing from {ast_type} AST node"
        super().__init__(message)


class ASTIllegalPlacementError(ASTValidationError):
    """Exception raised when AST element is placed illegally.
    
    Examples:
    - UQ config on incompatible measure
    - Coverage without prior grouping
    - Aggregation without grouping
    
    Attributes:
        element: The illegally placed element
        reason: Why the placement is illegal
        suggestion: How to fix it
    """
    
    def __init__(self, element: str, reason: str, suggestion: Optional[str] = None):
        self.element = element
        self.reason = reason
        self.suggestion = suggestion
        message = f"Illegal placement of {element}: {reason}"
        if suggestion:
            message += f"\nSuggestion: {suggestion}"
        super().__init__(message)

