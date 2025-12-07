"""DSL001: Unknown layer detection."""

from typing import List
from ...ast import Query, SelectStmt
from ..diagnostic import Diagnostic, SuggestedFix
from ..lint_context import LintContext


class UnknownLayerRule:
    """Check for references to unknown layers.
    
    This rule triggers when a layer is referenced in the query but is not
    found in the schema provider's list of available layers.
    """
    
    code = "DSL001"
    description = "Unknown layer reference"
    default_severity = "error"
    
    def apply(self, query: Query, context: LintContext) -> List[Diagnostic]:
        """Apply the rule."""
        diagnostics = []
        
        if not context.schema:
            # Can't check without schema
            return diagnostics
        
        available_layers = set(context.schema.list_layers())
        
        # Check SELECT statement
        if query.select:
            diagnostics.extend(self._check_select(query.select, available_layers, context))
        
        return diagnostics
    
    def _check_select(self, select: SelectStmt, available_layers: set, context: LintContext) -> List[Diagnostic]:
        """Check layers in SELECT statement."""
        diagnostics = []
        
        if not select.layer_expr:
            return diagnostics
        
        # Check each layer term
        for term in select.layer_expr.terms:
            if term.name not in available_layers:
                # Find position in query (approximate)
                span = self._find_layer_span(term.name, context.query)
                
                # Find closest match for suggestion
                suggestion = self._find_closest_layer(term.name, available_layers)
                
                message = f"Unknown layer '{term.name}'"
                if available_layers:
                    message += f". Available layers: {', '.join(sorted(available_layers))}"
                
                suggested_fix = None
                if suggestion:
                    suggested_fix = SuggestedFix(
                        replacement=suggestion,
                        span=span
                    )
                    message += f". Did you mean '{suggestion}'?"
                
                diagnostics.append(Diagnostic(
                    code=self.code,
                    severity=self.default_severity,
                    message=message,
                    span=span,
                    suggested_fix=suggested_fix
                ))
        
        return diagnostics
    
    def _find_layer_span(self, layer_name: str, query: str) -> tuple:
        """Find the span of a layer name in the query.
        
        Returns approximate position if exact match not found.
        """
        # Try to find exact match
        idx = query.find(f'"{layer_name}"')
        if idx != -1:
            return (idx + 1, idx + 1 + len(layer_name))
        
        idx = query.find(f"'{layer_name}'")
        if idx != -1:
            return (idx + 1, idx + 1 + len(layer_name))
        
        idx = query.find(layer_name)
        if idx != -1:
            return (idx, idx + len(layer_name))
        
        # Default to start of query
        return (0, len(layer_name))
    
    def _find_closest_layer(self, layer_name: str, available_layers: set) -> str:
        """Find the closest matching layer name using edit distance."""
        if not available_layers:
            return None
        
        min_distance = float('inf')
        closest = None
        
        for available in available_layers:
            distance = self._levenshtein_distance(layer_name.lower(), available.lower())
            if distance < min_distance:
                min_distance = distance
                closest = available
        
        # Only suggest if distance is reasonable (< 50% of name length)
        if min_distance <= len(layer_name) // 2:
            return closest
        
        return None
    
    def _levenshtein_distance(self, s1: str, s2: str) -> int:
        """Calculate Levenshtein distance between two strings."""
        if len(s1) < len(s2):
            return self._levenshtein_distance(s2, s1)
        
        if len(s2) == 0:
            return len(s1)
        
        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                # Cost of insertions, deletions, or substitutions
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]
