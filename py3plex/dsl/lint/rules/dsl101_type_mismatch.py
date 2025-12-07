"""DSL101: Type mismatch detection."""

from typing import List
from ...ast import Query, SelectStmt, ConditionExpr, ConditionAtom, Comparison
from ..diagnostic import Diagnostic
from ..lint_context import LintContext
from ..types import AttrType


class TypeMismatchRule:
    """Check for type mismatches in comparisons.
    
    This rule triggers when operators are applied to incompatible types,
    such as comparing a numeric attribute to a string literal.
    """
    
    code = "DSL101"
    description = "Type mismatch in comparison"
    default_severity = "error"
    
    def apply(self, query: Query, context: LintContext) -> List[Diagnostic]:
        """Apply the rule."""
        diagnostics = []
        
        # Check SELECT statement
        if query.select:
            diagnostics.extend(self._check_select(query.select, context))
        
        return diagnostics
    
    def _check_select(self, select: SelectStmt, context: LintContext) -> List[Diagnostic]:
        """Check types in SELECT statement."""
        diagnostics = []
        
        # Check WHERE conditions
        if select.where:
            diagnostics.extend(self._check_conditions(select.where, context))
        
        return diagnostics
    
    def _check_conditions(self, conditions: ConditionExpr, context: LintContext) -> List[Diagnostic]:
        """Check types in conditions."""
        diagnostics = []
        
        for atom in conditions.atoms:
            diagnostics.extend(self._check_atom(atom, context))
        
        return diagnostics
    
    def _check_atom(self, atom: ConditionAtom, context: LintContext) -> List[Diagnostic]:
        """Check types in a condition atom."""
        diagnostics = []
        
        if atom.comparison:
            diagnostics.extend(self._check_comparison(atom.comparison, context))
        
        return diagnostics
    
    def _check_comparison(self, comparison: Comparison, context: LintContext) -> List[Diagnostic]:
        """Check types in a comparison."""
        diagnostics = []
        
        # Get left side type (attribute)
        left_type = context.type_env.get_attribute_type(comparison.left)
        
        # Get right side type (literal or param)
        right_type = self._infer_literal_type(comparison.right)
        
        # Check operator compatibility
        if not left_type.supports_operator(comparison.op):
            span = self._find_comparison_span(comparison, context.query)
            message = f"Operator '{comparison.op}' not supported for type {left_type.value}"
            
            diagnostics.append(Diagnostic(
                code=self.code,
                severity=self.default_severity,
                message=message,
                span=span
            ))
        
        # Check type compatibility
        if not left_type.is_comparable(right_type):
            span = self._find_comparison_span(comparison, context.query)
            message = (
                f"Type mismatch: comparing {left_type.value} (left) "
                f"with {right_type.value} (right) using operator '{comparison.op}'"
            )
            
            # Add helpful hint
            if left_type == AttrType.NUMERIC and right_type == AttrType.CATEGORICAL:
                message += ". Did you forget quotes around a string value?"
            elif left_type == AttrType.CATEGORICAL and right_type == AttrType.NUMERIC:
                message += ". Did you use quotes around a numeric value?"
            
            diagnostics.append(Diagnostic(
                code=self.code,
                severity=self.default_severity,
                message=message,
                span=span
            ))
        
        return diagnostics
    
    def _infer_literal_type(self, value) -> AttrType:
        """Infer type from a literal value."""
        if isinstance(value, bool):
            return AttrType.BOOLEAN
        if isinstance(value, (int, float)):
            return AttrType.NUMERIC
        if isinstance(value, str):
            # Try to parse as number
            try:
                float(value)
                return AttrType.NUMERIC
            except ValueError:
                return AttrType.CATEGORICAL
        
        return AttrType.UNKNOWN
    
    def _find_comparison_span(self, comparison: Comparison, query: str) -> tuple:
        """Find the span of a comparison in the query."""
        # Try to find the attribute
        idx = query.find(comparison.left)
        if idx != -1:
            # Approximate span covering the comparison
            end = idx + len(comparison.left) + len(comparison.op) + 10
            return (idx, min(end, len(query)))
        
        # Default
        return (0, 10)
