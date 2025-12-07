"""DSL202: Redundant predicate detection."""

from typing import List
from ...ast import Query, SelectStmt, ConditionExpr
from ..diagnostic import Diagnostic
from ..lint_context import LintContext


class RedundantPredicateRule:
    """Check for redundant predicates.
    
    Detects redundant conditions like:
    - x > 5 AND x > 3 (the x > 3 is redundant)
    """
    
    code = "DSL202"
    description = "Redundant predicate"
    default_severity = "info"
    
    def apply(self, query: Query, context: LintContext) -> List[Diagnostic]:
        """Apply the rule."""
        diagnostics = []
        
        # Check SELECT statement
        if query.select:
            diagnostics.extend(self._check_select(query.select, context))
        
        return diagnostics
    
    def _check_select(self, select: SelectStmt, context: LintContext) -> List[Diagnostic]:
        """Check for redundant predicates in SELECT."""
        diagnostics = []
        
        if not select.where:
            return diagnostics
        
        diagnostics.extend(self._check_redundancy(select.where, context))
        
        return diagnostics
    
    def _check_redundancy(self, conditions: ConditionExpr, context: LintContext) -> List[Diagnostic]:
        """Check for redundant conditions."""
        diagnostics = []
        
        # Collect comparisons grouped by attribute
        comparisons_by_attr = {}
        
        for i, atom in enumerate(conditions.atoms):
            if atom.comparison:
                comp = atom.comparison
                attr = comp.left
                
                if attr not in comparisons_by_attr:
                    comparisons_by_attr[attr] = []
                
                is_and = i == 0 or (i > 0 and conditions.ops[i-1] == "AND")
                comparisons_by_attr[attr].append((comp, is_and, i))
        
        # Check each attribute for redundancy
        for attr, comps in comparisons_by_attr.items():
            and_comps = [(c, idx) for c, is_and, idx in comps if is_and]
            
            if len(and_comps) >= 2:
                # Check for redundant comparisons
                for i, (comp1, idx1) in enumerate(and_comps):
                    for comp2, idx2 in and_comps[i+1:]:
                        if self._is_redundant(comp1, comp2):
                            span = (0, len(context.query))
                            message = (
                                f"Redundant condition on '{attr}': "
                                f"{comp2.left} {comp2.op} {comp2.right} is implied by "
                                f"{comp1.left} {comp1.op} {comp1.right}"
                            )
                            
                            diagnostics.append(Diagnostic(
                                code=self.code,
                                severity=self.default_severity,
                                message=message,
                                span=span
                            ))
        
        return diagnostics
    
    def _is_redundant(self, comp1, comp2) -> bool:
        """Check if comp2 is made redundant by comp1."""
        try:
            # Convert to float, handling both numeric and string values
            val1 = float(comp1.right) if isinstance(comp1.right, (int, float, str)) else None
            val2 = float(comp2.right) if isinstance(comp2.right, (int, float, str)) else None
            
            if val1 is None or val2 is None:
                return False
            
            # x > 5 makes x > 3 redundant
            if comp1.op == ">" and comp2.op == ">" and val1 > val2:
                return True
            
            # x >= 5 makes x >= 3 redundant
            if comp1.op == ">=" and comp2.op == ">=" and val1 > val2:
                return True
            
            # x < 3 makes x < 5 redundant
            if comp1.op == "<" and comp2.op == "<" and val1 < val2:
                return True
            
            # x <= 3 makes x <= 5 redundant
            if comp1.op == "<=" and comp2.op == "<=" and val1 < val2:
                return True
        
        except (ValueError, TypeError):
            pass
        
        return False
