"""PERF302: Cross-layer join warning."""

from typing import List
from ...ast import Query, SelectStmt, Target
from ..diagnostic import Diagnostic
from ..lint_context import LintContext


class CrossLayerJoinWarningRule:
    """Warn about expensive cross-layer joins.
    
    Triggers when querying edges across multiple large layers without
    selective predicates.
    """
    
    code = "PERF302"
    description = "Cross-layer join detected"
    default_severity = "hint"
    
    LARGE_THRESHOLD = 500
    
    def apply(self, query: Query, context: LintContext) -> List[Diagnostic]:
        """Apply the rule."""
        diagnostics = []
        
        if not context.schema:
            return diagnostics
        
        # Check SELECT statement
        if query.select:
            diagnostics.extend(self._check_select(query.select, context))
        
        return diagnostics
    
    def _check_select(self, select: SelectStmt, context: LintContext) -> List[Diagnostic]:
        """Check for cross-layer joins."""
        diagnostics = []
        
        # Only relevant for edge queries
        if select.target != Target.EDGES:
            return diagnostics
        
        # Check if querying multiple layers
        if not select.layer_expr or len(select.layer_expr.terms) < 2:
            return diagnostics
        
        # Check if any layer is large
        has_large_layer = False
        for term in select.layer_expr.terms:
            count = context.schema.get_edge_count(term.name)
            if count > self.LARGE_THRESHOLD:
                has_large_layer = True
                break
        
        if has_large_layer and not select.where:
            span = (0, 20)
            layer_names = [t.name for t in select.layer_expr.terms]
            message = (
                f"Cross-layer join warning: Querying edges across layers "
                f"{', '.join(layer_names)} may be expensive. "
                f"Consider adding WHERE filters or pre-materializing results."
            )
            
            diagnostics.append(Diagnostic(
                code=self.code,
                severity=self.default_severity,
                message=message,
                span=span
            ))
        
        return diagnostics
