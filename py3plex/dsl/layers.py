"""Layer Set Algebra for py3plex DSL.

This module provides a first-class layer set algebra system that makes layer
selection expressive, composable, and safe across the DSL.

Key Features:
    - Set-theoretic operations (union, intersection, difference, complement)
    - Ergonomic one-liner syntax
    - Late evaluation (resolved at execution time)
    - Named layer groups for reusability
    - Full introspection and explainability

Example:
    >>> from py3plex.dsl.layers import LayerSet, L
    >>> 
    >>> # Basic layer selection
    >>> social = LayerSet("social")
    >>> work = LayerSet("work")
    >>> 
    >>> # Set operations
    >>> both = social | work  # Union
    >>> intersection = social & work  # Intersection
    >>> difference = social - work  # Difference
    >>> complement = ~social  # Complement (all except social)
    >>> 
    >>> # String expressions
    >>> layers = LayerSet.parse("* - coupling - transport")
    >>> layers = LayerSet.parse("(ppi | gene) & disease")
    >>> 
    >>> # Named groups
    >>> LayerSet.define_group("bio", LayerSet.parse("ppi | gene | disease"))
    >>> bio = LayerSet("bio")  # Reference named group
    >>> 
    >>> # Resolution
    >>> active_layers = layers.resolve(network)
    >>> print(layers.explain())
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Set, Union
from dataclasses import dataclass

from .errors import UnknownLayerError, DslSyntaxError


# Global registry for named layer groups
_LAYER_GROUPS: Dict[str, "LayerSet"] = {}


@dataclass
class LayerExpr:
    """Internal AST node for layer expressions.
    
    Represents the parsed structure of a layer expression before evaluation.
    """
    kind: str  # "term", "union", "intersection", "difference", "complement"
    value: Optional[str] = None  # For "term" kind
    left: Optional["LayerExpr"] = None  # For binary operations
    right: Optional["LayerExpr"] = None  # For binary operations
    operand: Optional["LayerExpr"] = None  # For unary operations (complement)


class LayerSet:
    """Represents an unevaluated layer expression.
    
    LayerSet objects are immutable and composable. They maintain an internal
    AST representation that is only evaluated when resolve() is called.
    
    Attributes:
        expr: Internal expression AST
        
    Example:
        >>> # Create from layer name
        >>> social = LayerSet("social")
        >>> 
        >>> # Set operations
        >>> both = social | LayerSet("work")
        >>> non_coupling = LayerSet("*") - LayerSet("coupling")
        >>> 
        >>> # Parse from string
        >>> layers = LayerSet.parse("* - coupling - transport")
        >>> 
        >>> # Resolve to actual layer names
        >>> active = layers.resolve(network)
        >>> print(active)  # {'social', 'work', 'hobby'}
    """
    
    def __init__(self, name_or_expr: Union[str, LayerExpr]):
        """Initialize LayerSet from a name or expression.
        
        Args:
            name_or_expr: Layer name (string) or LayerExpr AST node
        """
        if isinstance(name_or_expr, str):
            self.expr = LayerExpr(kind="term", value=name_or_expr)
        elif isinstance(name_or_expr, LayerExpr):
            self.expr = name_or_expr
        else:
            raise TypeError(f"Expected str or LayerExpr, got {type(name_or_expr)}")
    
    def __or__(self, other: "LayerSet") -> "LayerSet":
        """Union: self | other.
        
        Returns:
            New LayerSet representing the union
        """
        return LayerSet(LayerExpr(
            kind="union",
            left=self.expr,
            right=other.expr
        ))
    
    def __and__(self, other: "LayerSet") -> "LayerSet":
        """Intersection: self & other.
        
        Returns:
            New LayerSet representing the intersection
        """
        return LayerSet(LayerExpr(
            kind="intersection",
            left=self.expr,
            right=other.expr
        ))
    
    def __sub__(self, other: "LayerSet") -> "LayerSet":
        """Difference: self - other.
        
        Returns:
            New LayerSet representing the difference
        """
        return LayerSet(LayerExpr(
            kind="difference",
            left=self.expr,
            right=other.expr
        ))
    
    def __invert__(self) -> "LayerSet":
        """Complement: ~self (all layers except self).
        
        Returns:
            New LayerSet representing the complement
        """
        return LayerSet(LayerExpr(
            kind="complement",
            operand=self.expr
        ))
    
    def resolve(self, network: Any, *, strict: bool = False, warn_empty: bool = True) -> Set[str]:
        """Resolve the layer expression to a set of actual layer names.
        
        This is where late evaluation happens. The expression is evaluated
        against the network's actual layers.
        
        Args:
            network: Multilayer network object
            strict: If True, raise error for unknown layers (default: False)
            warn_empty: If True, warn when result is empty (default: True)
            
        Returns:
            Set of layer names (as strings)
            
        Raises:
            UnknownLayerError: If strict=True and a referenced layer doesn't exist
            
        Example:
            >>> layers = LayerSet("social") | LayerSet("work")
            >>> active = layers.resolve(network)
            >>> print(active)  # {'social', 'work'}
        """
        # Get all available layers from network
        available_layers = self._get_available_layers(network)
        
        # Evaluate the expression
        result = self._evaluate_expr(self.expr, available_layers, network, strict)
        
        # Warn if empty (unless disabled)
        if warn_empty and not result:
            import warnings
            warnings.warn(
                f"Layer expression resolved to empty set. "
                f"Available layers: {sorted(available_layers)}",
                UserWarning
            )
        
        # Return as ordered set (preserve deterministic order)
        return set(result)
    
    def explain(self, network: Optional[Any] = None) -> str:
        """Generate human-readable explanation of the layer expression.
        
        Args:
            network: Optional network to resolve against (shows actual layers)
            
        Returns:
            Formatted explanation string
            
        Example:
            >>> layers = LayerSet("*") - LayerSet("coupling")
            >>> print(layers.explain())
            LayerSet:
              difference(
                all_layers("*"),
                layer("coupling")
              )
        """
        lines = ["LayerSet:"]
        lines.append(self._explain_expr(self.expr, indent=2))
        
        if network is not None:
            resolved = self.resolve(network, warn_empty=False)
            lines.append(f"\n→ resolved to: {sorted(resolved)}")
        
        return "\n".join(lines)
    
    @staticmethod
    def parse(expr_str: str) -> "LayerSet":
        """Parse a layer expression from string.
        
        Supports:
            - Layer names: "social", "work"
            - Wildcard: "*"
            - Union: "social | work" or "social + work"
            - Intersection: "social & work"
            - Difference: "social - work"
            - Complement: "~social" (future)
            - Parentheses: "(social | work) & ~coupling"
            - Named groups: "bio" (if defined via define_group)
        
        Args:
            expr_str: Expression string to parse
            
        Returns:
            LayerSet object
            
        Raises:
            DslSyntaxError: If expression is invalid
            
        Example:
            >>> layers = LayerSet.parse("* - coupling - transport")
            >>> layers = LayerSet.parse("(ppi | gene) & disease")
        """
        parser = _LayerExprParser(expr_str)
        ast = parser.parse()
        return LayerSet(ast)
    
    @staticmethod
    def define_group(name: str, layer_set: "LayerSet") -> None:
        """Define a named layer group for reuse.
        
        Args:
            name: Group name
            layer_set: LayerSet to associate with the name
            
        Example:
            >>> bio = LayerSet.parse("ppi | gene | disease")
            >>> LayerSet.define_group("bio", bio)
            >>> 
            >>> # Later, reference the group
            >>> layers = LayerSet("bio") & LayerSet("*")
        """
        _LAYER_GROUPS[name] = layer_set
    
    @staticmethod
    def list_groups() -> Dict[str, "LayerSet"]:
        """List all defined layer groups.
        
        Returns:
            Dictionary mapping group names to LayerSet objects
        """
        return dict(_LAYER_GROUPS)
    
    @staticmethod
    def clear_groups() -> None:
        """Clear all defined layer groups.
        
        Useful for testing or resetting state.
        """
        _LAYER_GROUPS.clear()
    
    def _get_available_layers(self, network: Any) -> Set[str]:
        """Get all available layers from the network.
        
        Args:
            network: Multilayer network object
            
        Returns:
            Set of layer names
        """
        if hasattr(network, "layers"):
            return {str(l) for l in network.layers}
        if hasattr(network, "get_nodes"):
            return {str(layer) for (_, layer) in network.get_nodes()}
        return set()
    
    def _evaluate_expr(self, expr: LayerExpr, available: Set[str],
                      network: Any, strict: bool) -> Set[str]:
        """Recursively evaluate a layer expression.
        
        Args:
            expr: Expression AST node
            available: Available layer names
            network: Network object
            strict: Whether to enforce strict layer validation
            
        Returns:
            Set of layer names
        """
        if expr.kind == "term":
            # Terminal: resolve a single term
            return self._resolve_term(expr.value, available, network, strict)
        
        elif expr.kind == "union":
            # Binary: A | B
            left = self._evaluate_expr(expr.left, available, network, strict)
            right = self._evaluate_expr(expr.right, available, network, strict)
            return left | right
        
        elif expr.kind == "intersection":
            # Binary: A & B
            left = self._evaluate_expr(expr.left, available, network, strict)
            right = self._evaluate_expr(expr.right, available, network, strict)
            return left & right
        
        elif expr.kind == "difference":
            # Binary: A - B
            left = self._evaluate_expr(expr.left, available, network, strict)
            right = self._evaluate_expr(expr.right, available, network, strict)
            return left - right
        
        elif expr.kind == "complement":
            # Unary: ~A
            operand = self._evaluate_expr(expr.operand, available, network, strict)
            return available - operand
        
        else:
            raise DslSyntaxError(f"Unknown expression kind: {expr.kind}")
    
    def _resolve_term(self, name: str, available: Set[str],
                     network: Any, strict: bool) -> Set[str]:
        """Resolve a single term (layer name, wildcard, or group).
        
        Args:
            name: Term name
            available: Available layer names
            network: Network object
            strict: Whether to enforce strict validation
            
        Returns:
            Set of layer names
        """
        # Check for wildcard
        if name == "*":
            return available
        
        # Check for named group
        if name in _LAYER_GROUPS:
            group = _LAYER_GROUPS[name]
            return group.resolve(network, strict=strict, warn_empty=False)
        
        # Regular layer name
        if name not in available:
            if strict:
                raise UnknownLayerError(
                    f"Layer '{name}' not found. Available: {sorted(available)}"
                )
            # In non-strict mode, just skip unknown layers
            return set()
        
        return {name}
    
    def _explain_expr(self, expr: LayerExpr, indent: int = 0) -> str:
        """Recursively generate explanation for an expression.
        
        Args:
            expr: Expression AST node
            indent: Indentation level
            
        Returns:
            Formatted explanation string
        """
        prefix = " " * indent
        
        if expr.kind == "term":
            if expr.value == "*":
                return f'{prefix}all_layers("*")'
            elif expr.value in _LAYER_GROUPS:
                return f'{prefix}group("{expr.value}")'
            else:
                return f'{prefix}layer("{expr.value}")'
        
        elif expr.kind == "union":
            lines = [f"{prefix}union("]
            lines.append(self._explain_expr(expr.left, indent + 2) + ",")
            lines.append(self._explain_expr(expr.right, indent + 2))
            lines.append(f"{prefix})")
            return "\n".join(lines)
        
        elif expr.kind == "intersection":
            lines = [f"{prefix}intersection("]
            lines.append(self._explain_expr(expr.left, indent + 2) + ",")
            lines.append(self._explain_expr(expr.right, indent + 2))
            lines.append(f"{prefix})")
            return "\n".join(lines)
        
        elif expr.kind == "difference":
            lines = [f"{prefix}difference("]
            lines.append(self._explain_expr(expr.left, indent + 2) + ",")
            lines.append(self._explain_expr(expr.right, indent + 2))
            lines.append(f"{prefix})")
            return "\n".join(lines)
        
        elif expr.kind == "complement":
            lines = [f"{prefix}complement("]
            lines.append(self._explain_expr(expr.operand, indent + 2))
            lines.append(f"{prefix})")
            return "\n".join(lines)
        
        return f"{prefix}<unknown>"
    
    def __repr__(self) -> str:
        """String representation."""
        return f"LayerSet({self._repr_expr(self.expr)})"
    
    def _repr_expr(self, expr: LayerExpr) -> str:
        """Generate compact representation of expression."""
        if expr.kind == "term":
            return f'"{expr.value}"'
        elif expr.kind == "union":
            return f"({self._repr_expr(expr.left)} | {self._repr_expr(expr.right)})"
        elif expr.kind == "intersection":
            return f"({self._repr_expr(expr.left)} & {self._repr_expr(expr.right)})"
        elif expr.kind == "difference":
            return f"({self._repr_expr(expr.left)} - {self._repr_expr(expr.right)})"
        elif expr.kind == "complement":
            return f"~{self._repr_expr(expr.operand)}"
        return "<unknown>"


class _LayerExprParser:
    """Recursive descent parser for layer expressions.
    
    Grammar:
        expr     := or_expr
        or_expr  := and_expr ( ('|' | '+') and_expr )*
        and_expr := diff_expr ( '&' diff_expr )*
        diff_expr:= term ( '-' term )*
        term     := '(' expr ')' | '~' term | identifier | '*'
        identifier := [a-zA-Z_][a-zA-Z0-9_]*
    
    Example:
        >>> parser = _LayerExprParser("(social | work) & ~coupling")
        >>> ast = parser.parse()
    """
    
    def __init__(self, text: str):
        """Initialize parser with input text.
        
        Args:
            text: Expression string to parse
        """
        self.text = text.strip()
        self.pos = 0
        self.length = len(self.text)
    
    def parse(self) -> LayerExpr:
        """Parse the expression and return AST.
        
        Returns:
            LayerExpr AST node
            
        Raises:
            DslSyntaxError: If parsing fails
        """
        if not self.text:
            raise DslSyntaxError("Empty layer expression")
        
        ast = self._parse_or_expr()
        
        # Ensure we consumed all input
        self._skip_whitespace()
        if self.pos < self.length:
            raise DslSyntaxError(
                f"Unexpected characters at position {self.pos}: '{self.text[self.pos:]}'"
            )
        
        return ast
    
    def _parse_or_expr(self) -> LayerExpr:
        """Parse union expression: A | B | C."""
        left = self._parse_and_expr()
        
        while self._peek_char() in ("|", "+"):
            self._consume_char()  # Consume | or +
            right = self._parse_and_expr()
            left = LayerExpr(kind="union", left=left, right=right)
        
        return left
    
    def _parse_and_expr(self) -> LayerExpr:
        """Parse intersection expression: A & B & C."""
        left = self._parse_diff_expr()
        
        while self._peek_char() == "&":
            self._consume_char()  # Consume &
            right = self._parse_diff_expr()
            left = LayerExpr(kind="intersection", left=left, right=right)
        
        return left
    
    def _parse_diff_expr(self) -> LayerExpr:
        """Parse difference expression: A - B - C."""
        left = self._parse_term()
        
        while self._peek_char() == "-":
            self._consume_char()  # Consume -
            right = self._parse_term()
            left = LayerExpr(kind="difference", left=left, right=right)
        
        return left
    
    def _parse_term(self) -> LayerExpr:
        """Parse terminal: identifier, *, (expr), or ~term."""
        self._skip_whitespace()
        
        # Check for empty
        if self.pos >= self.length:
            raise DslSyntaxError("Unexpected end of expression")
        
        # Parenthesized expression
        if self._peek_char() == "(":
            self._consume_char()  # Consume (
            expr = self._parse_or_expr()
            self._skip_whitespace()
            if self._peek_char() != ")":
                raise DslSyntaxError(f"Expected ')' at position {self.pos}")
            self._consume_char()  # Consume )
            return expr
        
        # Complement
        if self._peek_char() == "~":
            self._consume_char()  # Consume ~
            operand = self._parse_term()
            return LayerExpr(kind="complement", operand=operand)
        
        # Wildcard
        if self._peek_char() == "*":
            self._consume_char()  # Consume *
            return LayerExpr(kind="term", value="*")
        
        # Identifier
        identifier = self._parse_identifier()
        if not identifier:
            raise DslSyntaxError(
                f"Expected identifier at position {self.pos}, got '{self._peek_char()}'"
            )
        return LayerExpr(kind="term", value=identifier)
    
    def _parse_identifier(self) -> str:
        """Parse an identifier: [a-zA-Z_][a-zA-Z0-9_]*."""
        self._skip_whitespace()
        
        start = self.pos
        
        # First character: letter or underscore
        if self.pos < self.length and (self.text[self.pos].isalpha() or self.text[self.pos] == "_"):
            self.pos += 1
        else:
            return ""
        
        # Subsequent characters: letter, digit, or underscore
        while self.pos < self.length and (self.text[self.pos].isalnum() or self.text[self.pos] == "_"):
            self.pos += 1
        
        return self.text[start:self.pos]
    
    def _peek_char(self) -> Optional[str]:
        """Peek at current character without consuming it."""
        self._skip_whitespace()
        if self.pos < self.length:
            return self.text[self.pos]
        return None
    
    def _consume_char(self) -> None:
        """Consume current character."""
        self._skip_whitespace()
        if self.pos < self.length:
            self.pos += 1
    
    def _skip_whitespace(self) -> None:
        """Skip whitespace characters."""
        while self.pos < self.length and self.text[self.pos].isspace():
            self.pos += 1


# Convenience alias
L = LayerSet


__all__ = [
    "LayerSet",
    "LayerExpr",
    "L",
]
