"""PERF301: Full scan warning."""

from typing import List
from ...ast import Query, SelectStmt, Target
from ..diagnostic import Diagnostic
from ..lint_context import LintContext


class FullScanWarningRule:
    """Warn about queries that will scan all nodes/edges.
    
    Triggers when a query has no WHERE filter and operates on large layers.
    """
    
    code = "PERF301"
    description = "Full scan detected"
    default_severity = "warning"
    
    # Threshold for "large" network
    LARGE_THRESHOLD = 1000
    
    def apply(self, query: Query, context: LintContext) -> List[Diagnostic]:
        """Apply the rule."""
        diagnostics = []
        
        if not context.schema:
            # Can't check without schema
            return diagnostics
        
        # Check SELECT statement
        if query.select:
            diagnostics.extend(self._check_select(query.select, context))
        
        return diagnostics
    
    def _check_select(self, select: SelectStmt, context: LintContext) -> List[Diagnostic]:
        """Check for full scans in SELECT."""
        diagnostics = []
        
        # Only warn if there's no WHERE clause
        if select.where:
            return diagnostics
        
        # Check if we're querying a large layer
        if select.target == Target.NODES:
            count = context.schema.get_node_count()
            entity_type = "nodes"
        else:
            count = context.schema.get_edge_count()
            entity_type = "edges"
        
        if count > self.LARGE_THRESHOLD:
            span = (0, 10)  # Approximate position of SELECT keyword
            message = (
                f"Full scan warning: This query will scan all {count} {entity_type}. "
                f"Consider adding a WHERE filter to improve performance."
            )
            
            diagnostics.append(Diagnostic(
                code=self.code,
                severity=self.default_severity,
                message=message,
                span=span
            ))
        
        return diagnostics
