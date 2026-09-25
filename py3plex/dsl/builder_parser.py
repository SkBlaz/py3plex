"""Parser for the CLI's restricted Q/L/Param builder syntax."""

import ast
import operator
from typing import Any

from .builder import L, Param, Q, QueryBuilder, LayerExprBuilder
from .layers import LayerSet


_BUILDER_METHODS = frozenset({
    "from_layers", "where", "compute", "order_by", "limit", "top_k",
    "per_layer", "per_layer_pair", "end_grouping", "coverage", "uq",
    "community", "select", "drop", "rename", "summarize", "distinct",
    "rank_by", "zscore", "aggregate", "mutate", "at", "during",
})
_LAYER_OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.BitAnd: operator.and_}


def parse_builder_query(source: str) -> QueryBuilder:
    """Build a query from a limited expression tree, without Python evaluation."""
    try:
        root = ast.parse(source, mode="eval").body
    except SyntaxError as exc:
        raise ValueError(f"Invalid DSL syntax: {exc}") from exc

    def literal(node: ast.AST) -> Any:
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.List):
            return [literal(item) for item in node.elts]
        if isinstance(node, ast.Tuple):
            return tuple(literal(item) for item in node.elts)
        if isinstance(node, ast.Dict):
            return {literal(key): literal(value) for key, value in zip(node.keys, node.values)}
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            value = literal(node.operand)
            if type(value) not in (int, float):
                raise ValueError("Unary operators require numeric literals")
            return value if isinstance(node.op, ast.UAdd) else -value
        if isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name) and node.value.id == "L":
            layer = literal(node.slice)
            if not isinstance(layer, str):
                raise ValueError("Layer names must be strings")
            return L[layer]
        if isinstance(node, ast.BinOp) and type(node.op) in _LAYER_OPS:
            left, right = literal(node.left), literal(node.right)
            if not isinstance(left, (LayerExprBuilder, LayerSet)) or not isinstance(right, type(left)):
                raise ValueError("Layer operators require matching layer expressions")
            return _LAYER_OPS[type(node.op)](left, right)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            func = node.func
            if not isinstance(func.value, ast.Name) or func.value.id != "Param" or func.attr not in {"int", "float", "str", "ref"}:
                raise ValueError("Only Param.int/float/str/ref calls are allowed in arguments")
            if len(node.args) != 1 or node.keywords:
                raise ValueError("Param calls require one name")
            name = literal(node.args[0])
            if not isinstance(name, str):
                raise ValueError("Parameter names must be strings")
            return getattr(Param, func.attr)(name)
        raise ValueError(f"Unsupported DSL argument: {type(node).__name__}")

    def build(node: ast.AST) -> QueryBuilder:
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            raise ValueError("DSL query must be a Q factory call followed by builder methods")
        attr = node.func.attr
        if any(keyword.arg is None for keyword in node.keywords):
            raise ValueError("Keyword unpacking is not allowed in DSL queries")
        args = [literal(item) for item in node.args]
        kwargs = {item.arg: literal(item.value) for item in node.keywords}
        if isinstance(node.func.value, ast.Name) and node.func.value.id == "Q":
            if attr not in {"nodes", "edges", "communities"}:
                raise ValueError(f"Unsupported Q factory: {attr}")
            return getattr(Q, attr)(*args, **kwargs)
        builder = build(node.func.value)
        if attr not in _BUILDER_METHODS:
            raise ValueError(f"Unsupported DSL builder method: {attr}")
        result = getattr(builder, attr)(*args, **kwargs)
        if not isinstance(result, QueryBuilder):
            raise ValueError(f"Builder method {attr} did not return a query")
        return result

    return build(root)
