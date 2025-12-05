"""DSL serializer for simulation AST.

This module provides functions to serialize simulation AST back to DSL strings.
"""

from typing import Any

from .ast import SimulationStmt, InitialSpec


def sim_ast_to_dsl(stmt: SimulationStmt) -> str:
    """Serialize a SimulationStmt to DSL string.

    Args:
        stmt: SimulationStmt AST node

    Returns:
        SIMULATE DSL string
    """
    parts = [f"SIMULATE {stmt.process_name}"]

    # ON clause
    if stmt.layer_expr is not None:
        layer_str = _layer_expr_to_dsl(stmt.layer_expr)
        if layer_str:
            parts.append(f"ON {layer_str}")

    # COUPLING clause
    if stmt.coupling:
        coupling_str = ", ".join(
            f"{k}={_value_to_dsl(v)}" for k, v in stmt.coupling.items()
        )
        parts.append(f"COUPLING {coupling_str}")

    # WITH clause
    if stmt.params:
        params_str = ", ".join(
            f"{k}={_value_to_dsl(v)}" for k, v in stmt.params.items()
        )
        parts.append(f"WITH {params_str}")

    # INITIAL clause
    if stmt.initial:
        initial_parts = []
        for key, spec in stmt.initial.items():
            initial_parts.append(f"{key} = {_initial_spec_to_dsl(spec)}")
        parts.append(f"INITIAL {', '.join(initial_parts)}")

    # FOR clause
    parts.append(f"FOR {stmt.steps} STEPS")

    # MEASURE clause
    if stmt.measures:
        parts.append(f"MEASURE {', '.join(stmt.measures)}")

    # REPLICATES clause
    if stmt.replicates > 1:
        parts.append(f"REPLICATES {stmt.replicates}")

    # SEED clause
    if stmt.seed is not None:
        parts.append(f"SEED {stmt.seed}")

    # TO clause
    if stmt.export_target:
        parts.append(f"TO {stmt.export_target}")

    return "\n".join(parts)


def _layer_expr_to_dsl(layer_expr: Any) -> str:
    """Convert layer expression to DSL string.

    Args:
        layer_expr: LayerExpr AST node

    Returns:
        Layer expression DSL string
    """
    if layer_expr is None:
        return ""

    if not hasattr(layer_expr, 'terms') or not layer_expr.terms:
        return ""

    parts = [f'LAYER("{layer_expr.terms[0].name}")']

    for i, op in enumerate(layer_expr.ops):
        if i + 1 < len(layer_expr.terms):
            next_term = layer_expr.terms[i + 1].name
            parts.append(f' {op} LAYER("{next_term}")')

    return "".join(parts)


def _value_to_dsl(value: Any) -> str:
    """Convert a value to DSL representation.

    Args:
        value: Value to convert

    Returns:
        DSL string representation
    """
    if isinstance(value, str):
        return f'"{value}"'
    elif isinstance(value, bool):
        return "true" if value else "false"
    elif isinstance(value, dict):
        # Layer-specific parameters
        dict_parts = ", ".join(
            f'"{k}": {_value_to_dsl(v)}' for k, v in value.items()
        )
        return "{" + dict_parts + "}"
    else:
        return str(value)


def _initial_spec_to_dsl(spec: InitialSpec) -> str:
    """Convert InitialSpec to DSL string.

    Args:
        spec: InitialSpec AST node

    Returns:
        Initial spec DSL string
    """
    if spec.constant is not None:
        return _value_to_dsl(spec.constant)

    if spec.query is not None:
        # Serialize SELECT query
        from py3plex.dsl.serializer import ast_to_dsl
        from py3plex.dsl.ast import Query

        query = Query(explain=False, select=spec.query)
        return ast_to_dsl(query)

    return "null"
