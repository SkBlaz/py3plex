"""DSL002: Unknown attribute detection."""

from typing import List, Set
from ...ast import Query, SelectStmt, ConditionExpr, ConditionAtom
from ..diagnostic import Diagnostic, SuggestedFix
from ..lint_context import LintContext
from ..schema import EntityRef


class UnknownAttributeRule:
    """Check for references to unknown attributes.
    
    This rule triggers when an attribute is referenced in WHERE conditions
    but is not found in the schema.
    """
    
    code = "DSL002"
    description = "Unknown attribute reference"
    default_severity = "error"
    
    # Known built-in attributes
    BUILTIN_ATTRIBUTES = {"degree", "layer"}
    
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
        """Check attributes in SELECT statement."""
        diagnostics = []
        
        # Check WHERE conditions
        if select.where:
            diagnostics.extend(self._check_conditions(select.where, context))
        
        return diagnostics
    
    def _check_conditions(self, conditions: ConditionExpr, context: LintContext) -> List[Diagnostic]:
        """Check attributes in conditions."""
        diagnostics = []
        
        for atom in conditions.atoms:
            diagnostics.extend(self._check_atom(atom, context))
        
        return diagnostics
    
    def _check_atom(self, atom: ConditionAtom, context: LintContext) -> List[Diagnostic]:
        """Check attributes in a condition atom."""
        diagnostics = []
        
        if atom.comparison:
            attr_name = atom.comparison.left
            
            # Skip built-in attributes
            if attr_name in self.BUILTIN_ATTRIBUTES:
                return diagnostics
            
            # Check if attribute exists in schema
            entity_ref = EntityRef(entity_type="node", attribute=attr_name)
            attr_type = context.schema.get_attribute_type(entity_ref, attr_name)
            
            if attr_type is None:
                # Attribute not found
                span = self._find_attribute_span(attr_name, context.query)
                
                # Try to find similar attributes
                known_attrs = self._get_known_attributes(context)
                suggestion = self._find_closest_attribute(attr_name, known_attrs)
                
                message = f"Unknown attribute '{attr_name}'"
                if known_attrs:
                    message += f". Known attributes: {', '.join(sorted(known_attrs))}"
                
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
    
    def _get_known_attributes(self, context: LintContext) -> Set[str]:
        """Get set of known attributes from schema and built-ins."""
        attrs = set(self.BUILTIN_ATTRIBUTES)
        
        # Could extend to sample attributes from schema
        # For now, just return built-ins
        
        return attrs
    
    def _find_attribute_span(self, attr_name: str, query: str) -> tuple:
        """Find the span of an attribute name in the query."""
        # Try to find in WHERE clause context
        idx = query.find(attr_name)
        if idx != -1:
            return (idx, idx + len(attr_name))
        
        # Default to start
        return (0, len(attr_name))
    
    def _find_closest_attribute(self, attr_name: str, known_attrs: Set[str]) -> str:
        """Find the closest matching attribute name."""
        if not known_attrs:
            return None
        
        min_distance = float('inf')
        closest = None
        
        for known in known_attrs:
            distance = self._levenshtein_distance(attr_name.lower(), known.lower())
            if distance < min_distance:
                min_distance = distance
                closest = known
        
        # Only suggest if distance is reasonable
        if min_distance <= len(attr_name) // 2:
            return closest
        
        return None
    
    def _levenshtein_distance(self, s1: str, s2: str) -> int:
        """Calculate Levenshtein distance."""
        if len(s1) < len(s2):
            return self._levenshtein_distance(s2, s1)
        
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
