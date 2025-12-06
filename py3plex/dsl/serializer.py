"""AST to DSL string serializer.

This module provides functionality to convert AST Query objects back to
DSL string representation.
"""

from typing import Any, Union

from .ast import (
    Query,
    SelectStmt,
    Target,
    ExportTarget,
    LayerExpr,
    ConditionExpr,
    ConditionAtom,
    Comparison,
    FunctionCall,
    SpecialPredicate,
    ComputeItem,
    OrderItem,
    ParamRef,
)


def ast_to_dsl(query: Query) -> str:
    """Convert a Query AST to DSL string.
    
    Args:
        query: Query AST object
        
    Returns:
        DSL query string
    """
    parts = []
    
    # EXPLAIN prefix
    if query.explain:
        parts.append("EXPLAIN")
    
    # SELECT statement
    parts.append(_serialize_select(query.select))
    
    return " ".join(parts)


def _serialize_select(select: SelectStmt) -> str:
    """Serialize a SELECT statement."""
    parts = []
    
    # SELECT target
    parts.append(f"SELECT {select.target.value}")
    
    # FROM layer_expr
    if select.layer_expr:
        parts.append("FROM " + _serialize_layer_expr(select.layer_expr))
    
    # WHERE conditions
    if select.where and select.where.atoms:
        parts.append("WHERE " + _serialize_conditions(select.where))
    
    # COMPUTE measures
    if select.compute:
        compute_parts = []
        for item in select.compute:
            if item.alias:
                compute_parts.append(f"{item.name} AS {item.alias}")
            else:
                compute_parts.append(item.name)
        parts.append("COMPUTE " + ", ".join(compute_parts))
    
    # ORDER BY
    if select.order_by:
        order_parts = []
        for item in select.order_by:
            if item.desc:
                order_parts.append(f"{item.key} DESC")
            else:
                order_parts.append(f"{item.key} ASC")
        parts.append("ORDER BY " + ", ".join(order_parts))
    
    # LIMIT
    if select.limit is not None:
        parts.append(f"LIMIT {select.limit}")
    
    # EXPORT (file export)
    if select.file_export:
        # Escape single quotes in path
        escaped_path = select.file_export.path.replace("'", "\\'")
        export_str = f"EXPORT TO '{escaped_path}'"
        export_str += f" FORMAT {select.file_export.fmt.upper()}"
        if select.file_export.columns:
            cols = ", ".join(select.file_export.columns)
            export_str += f" COLUMNS ({cols})"
        parts.append(export_str)
    
    # TO export (result format conversion)
    if select.export:
        parts.append(f"TO {select.export.value}")
    
    return " ".join(parts)


def _serialize_layer_expr(layer_expr: LayerExpr) -> str:
    """Serialize a layer expression."""
    if not layer_expr.terms:
        return ""
    
    parts = [f'LAYER("{layer_expr.terms[0].name}")']
    
    for i, op in enumerate(layer_expr.ops):
        next_term = layer_expr.terms[i + 1]
        parts.append(f' {op} LAYER("{next_term.name}")')
    
    return "".join(parts)


def _serialize_conditions(conditions: ConditionExpr) -> str:
    """Serialize condition expression."""
    if not conditions.atoms:
        return ""
    
    parts = [_serialize_atom(conditions.atoms[0])]
    
    for i, op in enumerate(conditions.ops):
        next_atom = conditions.atoms[i + 1]
        parts.append(f" {op} {_serialize_atom(next_atom)}")
    
    return "".join(parts)


def _serialize_atom(atom: ConditionAtom) -> str:
    """Serialize a condition atom."""
    if atom.comparison:
        return _serialize_comparison(atom.comparison)
    elif atom.special:
        return _serialize_special(atom.special)
    elif atom.function:
        return _serialize_function(atom.function)
    return ""


def _serialize_comparison(comparison: Comparison) -> str:
    """Serialize a comparison."""
    value = _serialize_value(comparison.right)
    return f"{comparison.left} {comparison.op} {value}"


def _serialize_value(value: Any) -> str:
    """Serialize a value."""
    if isinstance(value, ParamRef):
        return f":{value.name}"
    elif isinstance(value, str):
        return f'"{value}"'
    else:
        return str(value)


def _serialize_special(special: SpecialPredicate) -> str:
    """Serialize a special predicate."""
    if special.kind == "intralayer":
        return "intralayer"
    elif special.kind == "interlayer":
        src = special.params.get("src", "")
        dst = special.params.get("dst", "")
        return f'interlayer("{src}", "{dst}")'
    elif special.kind == "motif":
        motif_name = special.params.get("name", "")
        return f'motif="{motif_name}"'
    else:
        return special.kind


def _serialize_function(function: FunctionCall) -> str:
    """Serialize a function call."""
    args = ", ".join(_serialize_value(arg) for arg in function.args)
    return f"{function.name}({args})"
