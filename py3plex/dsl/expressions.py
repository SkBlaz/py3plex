"""Expression builder for DSL WHERE clauses.

This module provides a rich expression builder (F) for constructing complex
boolean conditions with operators and parentheses. This complements the
kwargs-based filtering while supporting more complex logic.

Example:
    >>> from py3plex.dsl import Q, L, F
    >>> 
    >>> # Simple expression
    >>> q = Q.nodes().where((F.degree > 5) & (F.betweenness_centrality > 0.1))
    >>> 
    >>> # Complex boolean logic
    >>> expr = (F.degree > 10) | ((F.layer == "social") & (F.clustering < 0.5))
    >>> q = Q.nodes().where(expr)
    >>> 
    >>> # Negation
    >>> q = Q.nodes().where(~F.is_infected)
    >>> 
    >>> # Mix with kwargs
    >>> q = Q.nodes().where(F.degree > 5, layer="social")
"""

from typing import Any, Union
from .ast import ConditionExpr, ConditionAtom, Comparison, ParamRef


class FieldExpression:
    """Represents a field reference that can be compared to values.
    
    This class implements operator overloading to create comparison expressions
    that are then converted to AST ConditionExpr objects.
    
    Attributes:
        _field: The field name being referenced
    """
    
    def __init__(self, field: str):
        """Initialize a field expression.
        
        Args:
            field: The field/attribute name (e.g., "degree", "layer")
        """
        self._field = field
    
    def __gt__(self, value: Union[int, float, str, ParamRef]) -> "BooleanExpression":
        """Greater than comparison: F.degree > 5"""
        return BooleanExpression._from_comparison(self._field, ">", value)
    
    def __ge__(self, value: Union[int, float, str, ParamRef]) -> "BooleanExpression":
        """Greater than or equal: F.degree >= 5"""
        return BooleanExpression._from_comparison(self._field, ">=", value)
    
    def __lt__(self, value: Union[int, float, str, ParamRef]) -> "BooleanExpression":
        """Less than comparison: F.degree < 5"""
        return BooleanExpression._from_comparison(self._field, "<", value)
    
    def __le__(self, value: Union[int, float, str, ParamRef]) -> "BooleanExpression":
        """Less than or equal: F.degree <= 5"""
        return BooleanExpression._from_comparison(self._field, "<=", value)
    
    def __eq__(self, value: Union[int, float, str, ParamRef]) -> "BooleanExpression":  # type: ignore
        """Equality comparison: F.layer == "social" """
        return BooleanExpression._from_comparison(self._field, "=", value)
    
    def __ne__(self, value: Union[int, float, str, ParamRef]) -> "BooleanExpression":  # type: ignore
        """Not equal comparison: F.layer != "bots" """
        return BooleanExpression._from_comparison(self._field, "!=", value)
    
    def __repr__(self) -> str:
        return f"F.{self._field}"


class BooleanExpression:
    """Represents a boolean expression that can be combined with & (AND), | (OR), and ~ (NOT).
    
    This class wraps ConditionExpr AST nodes and provides operator overloading
    for building complex boolean logic.
    
    Attributes:
        _condition: The underlying ConditionExpr AST node
        _negated: Whether this expression is negated
    """
    
    def __init__(self, condition: ConditionExpr, negated: bool = False):
        """Initialize a boolean expression.
        
        Args:
            condition: The underlying ConditionExpr
            negated: Whether this expression is negated
        """
        self._condition = condition
        self._negated = negated
    
    @classmethod
    def _from_comparison(cls, field: str, op: str, value: Union[int, float, str, ParamRef]) -> "BooleanExpression":
        """Create a BooleanExpression from a single comparison.
        
        Args:
            field: Field name
            op: Comparison operator
            value: Value to compare against
            
        Returns:
            BooleanExpression wrapping the comparison
        """
        # Wrap value if needed
        if isinstance(value, (int, float, str, ParamRef)):
            wrapped_value = value
        else:
            wrapped_value = str(value)
        
        comparison = Comparison(left=field, op=op, right=wrapped_value)
        atom = ConditionAtom(comparison=comparison)
        condition = ConditionExpr(atoms=[atom], ops=[])
        return cls(condition, negated=False)
    
    def __and__(self, other: "BooleanExpression") -> "BooleanExpression":
        """AND operator: (F.degree > 5) & (F.layer == "social")"""
        if not isinstance(other, BooleanExpression):
            raise TypeError(f"Cannot combine BooleanExpression with {type(other)}")
        
        # Handle negation by applying De Morgan's laws if needed
        # For simplicity, we'll just combine the expressions
        # Negation is handled during AST conversion
        
        # Combine atoms and ops
        new_atoms = self._condition.atoms + other._condition.atoms
        new_ops = self._condition.ops + ["AND"] + other._condition.ops
        
        # Simplify ops list (remove empty trailing ops)
        while new_ops and new_ops[-1] == "":
            new_ops.pop()
        
        new_condition = ConditionExpr(atoms=new_atoms, ops=new_ops)
        return BooleanExpression(new_condition, negated=False)
    
    def __or__(self, other: "BooleanExpression") -> "BooleanExpression":
        """OR operator: (F.degree > 5) | (F.layer == "social")"""
        if not isinstance(other, BooleanExpression):
            raise TypeError(f"Cannot combine BooleanExpression with {type(other)}")
        
        # Combine atoms and ops
        new_atoms = self._condition.atoms + other._condition.atoms
        new_ops = self._condition.ops + ["OR"] + other._condition.ops
        
        # Simplify ops list
        while new_ops and new_ops[-1] == "":
            new_ops.pop()
        
        new_condition = ConditionExpr(atoms=new_atoms, ops=new_ops)
        return BooleanExpression(new_condition, negated=False)
    
    def __invert__(self) -> "BooleanExpression":
        """NOT operator: ~F.is_infected"""
        # Create a new expression with negation flipped
        return BooleanExpression(self._condition, negated=not self._negated)
    
    def to_condition_expr(self) -> ConditionExpr:
        """Convert to AST ConditionExpr.
        
        Returns:
            ConditionExpr that can be used in SelectStmt
        """
        if self._negated:
            # To implement negation, we would need to wrap the entire expression
            # in a NOT operation. For now, we'll handle simple cases.
            # TODO: Full negation support with parentheses
            # For MVP, we'll just mark it somehow or raise an error
            # Actually, let's handle single-atom negation
            if len(self._condition.atoms) == 1 and not self._condition.ops:
                atom = self._condition.atoms[0]
                if atom.comparison:
                    # Invert the operator
                    comp = atom.comparison
                    inverted_op = {
                        ">": "<=",
                        ">=": "<",
                        "<": ">=",
                        "<=": ">",
                        "=": "!=",
                        "!=": "=",
                    }.get(comp.op, comp.op)
                    new_comp = Comparison(left=comp.left, op=inverted_op, right=comp.right)
                    new_atom = ConditionAtom(comparison=new_comp)
                    return ConditionExpr(atoms=[new_atom], ops=[])
            # For complex expressions, we can't easily negate without adding NOT to AST
            raise NotImplementedError(
                "Negation of complex expressions is not yet supported. "
                "Try rewriting using inverted operators or applying De Morgan's laws. "
                "For example:\n"
                "  Instead of: ~((F.degree > 5) & (F.layer == 'social'))\n"
                "  Use: (F.degree <= 5) | (F.layer != 'social')\n"
                "  Or: ~(F.degree > 5) | ~(F.layer == 'social')"
            )
        
        return self._condition
    
    def __repr__(self) -> str:
        neg_str = "~" if self._negated else ""
        if len(self._condition.atoms) == 1:
            atom = self._condition.atoms[0]
            if atom.comparison:
                comp = atom.comparison
                return f"{neg_str}({comp.left} {comp.op} {comp.right})"
        return f"{neg_str}(BooleanExpression with {len(self._condition.atoms)} atoms)"


class FieldProxy:
    """Proxy for creating field expressions via F.field_name syntax.
    
    This allows for intuitive syntax like:
        F.degree > 5
        F.layer == "social"
        F.is_infected
    """
    
    def __getattr__(self, name: str) -> FieldExpression:
        """Create a field expression for the given attribute name.
        
        Args:
            name: The field/attribute name
            
        Returns:
            FieldExpression that can be used in comparisons
        """
        return FieldExpression(name)
    
    def __repr__(self) -> str:
        return "F"


# Global field proxy - this is the main export
F = FieldProxy()


__all__ = ["F", "FieldExpression", "BooleanExpression", "FieldProxy"]
