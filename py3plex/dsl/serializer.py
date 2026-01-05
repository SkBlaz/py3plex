"""AST to DSL string serializer and deserializer.

This module provides functionality to convert AST Query objects to/from
DSL string representation and JSON format for provenance.
"""

from typing import Any, Dict, Union

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


def serialize_query(query: Query) -> Dict[str, Any]:
    """Serialize a Query AST to JSON-compatible dictionary.
    
    This is used for provenance storage and replay.
    
    Args:
        query: Query AST object
        
    Returns:
        Dictionary representation of the query
    """
    from dataclasses import asdict
    
    # Convert to dict, handling dataclasses recursively
    def _to_dict(obj: Any) -> Any:
        if obj is None:
            return None
        elif isinstance(obj, (str, int, float, bool)):
            return obj
        elif isinstance(obj, (Target, ExportTarget)):
            return obj.value
        elif hasattr(obj, '__dataclass_fields__'):
            # Dataclass
            result = {}
            for field_name in obj.__dataclass_fields__:
                value = getattr(obj, field_name)
                result[field_name] = _to_dict(value)
            result['__class__'] = obj.__class__.__name__
            return result
        elif isinstance(obj, list):
            return [_to_dict(item) for item in obj]
        elif isinstance(obj, dict):
            return {k: _to_dict(v) for k, v in obj.items()}
        else:
            return str(obj)
    
    return _to_dict(query)


def deserialize_query(data: Dict[str, Any]) -> Query:
    """Deserialize a Query AST from JSON-compatible dictionary.
    
    This reconstructs the query for replay.
    
    Args:
        data: Dictionary representation of the query
        
    Returns:
        Query AST object
    """
    def _from_dict(obj: Any, target_class: Any = None) -> Any:
        if obj is None:
            return None
        elif isinstance(obj, (str, int, float, bool)):
            return obj
        elif isinstance(obj, list):
            return [_from_dict(item) for item in obj]
        elif isinstance(obj, dict):
            class_name = obj.get('__class__')
            if class_name:
                # Reconstruct dataclass
                obj_copy = dict(obj)
                del obj_copy['__class__']
                
                # Map class names to classes
                class_map = {
                    'Query': Query,
                    'SelectStmt': SelectStmt,
                    'Target': Target,
                    'ExportTarget': ExportTarget,
                    'LayerExpr': LayerExpr,
                    'ConditionExpr': ConditionExpr,
                    'ConditionAtom': ConditionAtom,
                    'Comparison': Comparison,
                    'FunctionCall': FunctionCall,
                    'SpecialPredicate': SpecialPredicate,
                    'ComputeItem': ComputeItem,
                    'OrderItem': OrderItem,
                    'ParamRef': ParamRef,
                }
                
                cls = class_map.get(class_name)
                if cls:
                    # Handle enums specially - they should be reconstructed from value
                    if class_name == 'Target' and 'value' in obj_copy:
                        return Target(obj_copy['value'])
                    elif class_name == 'ExportTarget' and 'value' in obj_copy:
                        return ExportTarget(obj_copy['value'])
                    
                    # Recursively reconstruct fields
                    kwargs = {}
                    for key, value in obj_copy.items():
                        # Convert enum values back to enums
                        if key == 'target' and isinstance(value, str):
                            # If target is already a string value, convert to Target enum
                            kwargs[key] = Target(value) if value in ['nodes', 'edges', 'communities'] else _from_dict(value)
                        elif key == 'export' and isinstance(value, str):
                            # If export is a string value, convert to ExportTarget enum
                            kwargs[key] = ExportTarget(value) if value in ['pandas', 'networkx', 'arrow', 'dict'] else _from_dict(value)
                        else:
                            kwargs[key] = _from_dict(value)
                    
                    return cls(**kwargs)
            
            # Regular dict
            return {k: _from_dict(v) for k, v in obj.items()}
        else:
            return obj
    
    return _from_dict(data)
