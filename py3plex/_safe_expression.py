"""Evaluate the small expression language used by filters and dynamics rules."""

import ast
import operator
from numbers import Real
from typing import Any, Mapping


_BINARY = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}
_UNARY = {
    ast.Not: operator.not_,
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}
_COMPARE = {
    ast.Eq: operator.eq,
    ast.NotEq: operator.ne,
    ast.Lt: operator.lt,
    ast.LtE: operator.le,
    ast.Gt: operator.gt,
    ast.GtE: operator.ge,
    ast.In: lambda left, right: left in right,
    ast.NotIn: lambda left, right: left not in right,
    ast.Is: operator.is_,
    ast.IsNot: operator.is_not,
}


def evaluate_expression(expr: str, context: Mapping[str, Any], *, arithmetic_only: bool = False) -> Any:
    """Interpret literals, names, arithmetic, and optionally comparisons/booleans.

    Calls, attributes, indexing, comprehensions, and arbitrary Python code are
    outside this language. Unknown names raise ValueError.
    """
    try:
        tree = ast.parse(expr, mode="eval")
    except SyntaxError as exc:
        raise ValueError(f"Invalid expression syntax: {exc}") from exc

    def visit(node: ast.AST) -> Any:
        if isinstance(node, ast.Expression):
            return visit(node.body)
        if isinstance(node, ast.Constant):
            if arithmetic_only and (isinstance(node.value, bool) or not isinstance(node.value, (int, float))):
                raise ValueError("Arithmetic expressions require numeric literals")
            return node.value
        if isinstance(node, ast.Name):
            if node.id not in context:
                raise ValueError(f"Unknown expression name: {node.id}")
            value = context[node.id]
            if arithmetic_only and not isinstance(value, Real):
                raise ValueError(f"Arithmetic expression name {node.id} must be numeric")
            return value
        if isinstance(node, ast.BinOp) and type(node.op) in _BINARY:
            return _BINARY[type(node.op)](visit(node.left), visit(node.right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY:
            if arithmetic_only and isinstance(node.op, ast.Not):
                raise ValueError("Boolean operations are not allowed in arithmetic expressions")
            return _UNARY[type(node.op)](visit(node.operand))
        if not arithmetic_only and isinstance(node, ast.BoolOp):
            if isinstance(node.op, ast.And):
                value = True
                for item in node.values:
                    value = visit(item)
                    if not value:
                        return value
                return value
            if isinstance(node.op, ast.Or):
                value = False
                for item in node.values:
                    value = visit(item)
                    if value:
                        return value
                return value
        if not arithmetic_only and isinstance(node, ast.Compare):
            left = visit(node.left)
            for op, comparator in zip(node.ops, node.comparators):
                operation = _COMPARE.get(type(op))
                if operation is None:
                    raise ValueError(f"Expression contains disallowed construct: {type(op).__name__}")
                right = visit(comparator)
                if not operation(left, right):
                    return False
                left = right
            return True
        raise ValueError(f"Expression contains disallowed construct: {type(node).__name__}")

    try:
        return visit(tree)
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError(f"Error evaluating expression: {exc}") from exc
