"""DSL201: Unsatisfiable predicate detection."""

from typing import List
from ...ast import Query, SelectStmt, ConditionExpr, ConditionAtom
from ..diagnostic import Diagnostic
from ..lint_context import LintContext


class UnsatisfiablePredicateRule:
    """Check for obviously unsatisfiable predicates.
    
    Detects simple contradictions like:
    - x > 5 AND x < 1
    - timestamp BETWEEN 2021-01-01 AND 2020-01-01
    """
    
    code = "DSL201"
    description = "Unsatisfiable predicate"
    default_severity = "warning"
    
    def apply(self, query: Query, context: LintContext) -> List[Diagnostic]:
        """Apply the rule."""
        diagnostics = []
        
        # Check SELECT statement
        if query.select:
            diagnostics.extend(self._check_select(query.select, context))
        
        return diagnostics
    
    def _check_select(self, select: SelectStmt, context: LintContext) -> List[Diagnostic]:
        """Check for unsatisfiable predicates in SELECT."""
        diagnostics = []
        
        if not select.where:
            return diagnostics
        
        # Look for simple contradictions in AND conditions
        diagnostics.extend(self._check_contradictions(select.where, context))
        
        return diagnostics
    
    def _check_contradictions(self, conditions: ConditionExpr, context: LintContext) -> List[Diagnostic]:
        """Check for contradictory conditions."""
        diagnostics = []
        
        # Collect comparisons grouped by attribute
        comparisons_by_attr = {}
        
        for i, atom in enumerate(conditions.atoms):
            if atom.comparison:
                comp = atom.comparison
                attr = comp.left
                
                if attr not in comparisons_by_attr:
                    comparisons_by_attr[attr] = []
                
                # Track operator position
                is_and = i == 0 or (i > 0 and conditions.ops[i-1] == "AND")
                comparisons_by_attr[attr].append((comp, is_and))
        
        # Check each attribute for contradictions
        for attr, comps in comparisons_by_attr.items():
            # Only check AND-connected comparisons
            and_comps = [c for c, is_and in comps if is_and]
            
            if len(and_comps) >= 2:
                # Check for x > a AND x < b where b <= a
                for i, comp1 in enumerate(and_comps):
                    for comp2 in and_comps[i+1:]:
                        if self._is_contradiction(comp1, comp2):
                            span = (0, len(context.query))
                            message = (
                                f"Contradictory conditions on '{attr}': "
                                f"{comp1.left} {comp1.op} {comp1.right} AND "
                                f"{comp2.left} {comp2.op} {comp2.right}"
                            )
                            
                            diagnostics.append(Diagnostic(
                                code=self.code,
                                severity=self.default_severity,
                                message=message,
                                span=span
                            ))
        
        return diagnostics
    
    def _is_contradiction(self, comp1, comp2) -> bool:
        """Check if two comparisons are contradictory."""
        # Try to convert to numbers
        try:
            # Convert to float, handling both numeric and string values
            val1 = float(comp1.right) if isinstance(comp1.right, (int, float, str)) else None
            val2 = float(comp2.right) if isinstance(comp2.right, (int, float, str)) else None
            
            if val1 is None or val2 is None:
                return False
            
            # Check for contradictions
            # x > a AND x < b where a >= b
            if comp1.op in (">", ">=") and comp2.op in ("<", "<="):
                if val1 >= val2:
                    return True
            
            # x < a AND x > b where a <= b
            if comp1.op in ("<", "<=") and comp2.op in (">", ">="):
                if val1 <= val2:
                    return True
            
            # x = a AND x = b where a != b
            if comp1.op == "=" and comp2.op == "=" and val1 != val2:
                return True
        
        except (ValueError, TypeError):
            pass
        
        return False
