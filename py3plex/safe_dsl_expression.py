"""Safe interpreter for the CLI's documented Python-style DSL builder syntax."""
import ast
import operator


_ALLOWED_METHODS = {
    "nodes", "edges", "communities", "from_layers", "where", "compute",
    "order_by", "limit", "top_k", "group_by", "per_layer", "coverage",
    "end_grouping", "uq", "select", "drop", "rename", "distinct",
    "summarize", "mutate", "rank_by", "zscore", "having", "during",
    "window", "approx", "seed", "provenance", "hint", "to_ast",
    "int", "float", "str", "ref",
}
_ALLOWED_BINOPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.BitOr: operator.or_, ast.BitAnd: operator.and_}
_ALLOWED_UNARY = {ast.USub: operator.neg, ast.UAdd: operator.pos}


def evaluate_dsl_expression(source):
    """Evaluate a builder expression using explicit AST nodes and allowlists."""
    from py3plex.dsl import Q, L, Param

    try:
        tree = ast.parse(source, mode="eval")
    except SyntaxError as exc:
        raise ValueError(f"Invalid DSL expression: {exc.msg}") from exc

    def visit(node):
        if isinstance(node, ast.Constant):
            if isinstance(node.value, (str, int, float, bool, type(None))):
                return node.value
            raise ValueError("Unsupported literal in DSL expression")
        if isinstance(node, ast.Name):
            if node.id in {"Q", "L", "Param"}:
                return {"Q": Q, "L": L, "Param": Param}[node.id]
            raise ValueError(f"Name {node.id!r} is not allowed in DSL expressions")
        if isinstance(node, ast.Attribute):
            if node.attr.startswith("_"):
                raise ValueError("Private attributes are not allowed in DSL expressions")
            if isinstance(node.value, ast.Name) and node.value.id in {"Q", "L", "Param"}:
                owner = visit(node.value)
                is_layer = owner is L
            elif isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Attribute):
                if node.value.func.attr not in _ALLOWED_METHODS:
                    raise ValueError("Method chain contains an unsupported operation")
                owner = visit(node.value)
                is_layer = False
            else:
                raise ValueError("Attribute access is allowed only on DSL namespaces or builder results")
            if node.attr not in _ALLOWED_METHODS and not is_layer:
                raise ValueError(f"Attribute {node.attr!r} is not allowed in DSL expressions")
            try:
                return getattr(owner, node.attr)
            except AttributeError as exc:
                raise ValueError(f"Unsupported DSL attribute {node.attr!r}") from exc
        if isinstance(node, ast.Call):
            if node.keywords and any(keyword.arg is None for keyword in node.keywords):
                raise ValueError("Keyword argument unpacking is not allowed")
            function = visit(node.func)
            if isinstance(node.func, ast.Attribute) and node.func.attr not in _ALLOWED_METHODS:
                raise ValueError(f"Method {node.func.attr!r} is not allowed in DSL expressions")
            return function(*[visit(arg) for arg in node.args], **{kw.arg: visit(kw.value) for kw in node.keywords})
        if isinstance(node, ast.Subscript):
            if not isinstance(node.value, ast.Name) or node.value.id != "L":
                raise ValueError("Subscripts are allowed only on L")
            key = visit(node.slice)
            if not isinstance(key, str):
                raise ValueError("Layer names must be strings")
            return L[key]
        if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_BINOPS:
            return _ALLOWED_BINOPS[type(node.op)](visit(node.left), visit(node.right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_UNARY:
            return _ALLOWED_UNARY[type(node.op)](visit(node.operand))
        if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
            values = [visit(item) for item in node.elts]
            return values if isinstance(node, ast.List) else tuple(values) if isinstance(node, ast.Tuple) else set(values)
        if isinstance(node, ast.Dict):
            return {visit(k): visit(v) for k, v in zip(node.keys, node.values)}
        raise ValueError(f"Syntax {type(node).__name__} is not allowed in DSL expressions")

    result = visit(tree.body)
    if not callable(getattr(result, "to_ast", None)):
        raise ValueError("DSL expression must produce a query builder")
    return result
