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

from typing import Union
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
        
        return BooleanExpression(self.to_condition_expr().combine(other.to_condition_expr(), "AND"))

    def __or__(self, other: "BooleanExpression") -> "BooleanExpression":
        """OR operator: (F.degree > 5) | (F.layer == "social")"""
        if not isinstance(other, BooleanExpression):
            raise TypeError(f"Cannot combine BooleanExpression with {type(other)}")
        return BooleanExpression(self.to_condition_expr().combine(other.to_condition_expr(), "OR"))

    def __invert__(self) -> "BooleanExpression":
        """NOT operator: ~F.is_infected"""
        # Create a new expression with negation flipped
        return BooleanExpression(self._condition, negated=not self._negated)
    
    def to_condition_expr(self) -> ConditionExpr:
        """Convert to AST ConditionExpr.
        
        Returns:
            ConditionExpr that can be used in SelectStmt
        """
        condition = self._condition
        if not self._negated:
            return condition
        return ConditionExpr(
            atoms=condition.atoms,
            ops=condition.ops,
            postfix=(condition.postfix or condition._flat_postfix()) + ["NOT"],
        )

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
