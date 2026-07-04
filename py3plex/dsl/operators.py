"""Physical operator stubs for the DSL compiler pipeline.

Each :class:`PhysicalOp` sub-class represents one step of a physical plan.
The ``execute(ctx, rows)`` interface gives a clear extension point for future
per-operator optimisation without touching the monolithic executor.

Current state: all operators delegate to the existing executor, so they are
tested as *wrappers* rather than independent implementations.  The goal is to
make the plan visible and modular, not to rewrite the executor from scratch.

Usage::

    from py3plex.dsl.operators import ScanNodes, LayerFilter, ComputeMetric
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

__all__ = [
    "PhysicalOp",
    "ExecutionContext",
    "ScanNodes",
    "ScanEdges",
    "LayerFilter",
    "PredicateFilter",
    "ComputeMetric",
    "OrderBy",
    "Limit",
]


# ---------------------------------------------------------------------------
# Execution context
# ---------------------------------------------------------------------------


class ExecutionContext:
    """Lightweight container for state shared across operators in one plan.

    Attributes:
        network: The multilayer network being queried.
        params: Bound query parameters.
        planner_config: Active planner configuration dict.
        attributes: Mutable dict used to accumulate computed metric values
            across operators (analogous to a row-set).
    """

    def __init__(
        self,
        network: Any,
        params: Optional[Dict[str, Any]] = None,
        planner_config: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.network = network
        self.params: Dict[str, Any] = params or {}
        self.planner_config: Dict[str, Any] = planner_config or {}
        self.attributes: Dict[str, Any] = {}

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"ExecutionContext(network={type(self.network).__name__!r}, "
            f"params={self.params!r}, planner_config={self.planner_config!r})"
        )


# ---------------------------------------------------------------------------
# Base operator
# ---------------------------------------------------------------------------


class PhysicalOp(ABC):
    """Abstract base for physical operators.

    Sub-classes implement :meth:`execute` which takes an
    :class:`ExecutionContext` and an input *rows* sequence (list of node/edge
    identifiers or similar items) and returns a (possibly transformed) output
    sequence.
    """

    #: Human-readable operator name used in explain output.
    op_name: str = "PhysicalOp"

    @abstractmethod
    def execute(self, ctx: ExecutionContext, rows: List[Any]) -> List[Any]:
        """Execute this operator step and return the resulting rows.

        Args:
            ctx: Shared execution context.
            rows: Input row sequence from the previous operator.

        Returns:
            Output row sequence.
        """
        raise NotImplementedError

    def __repr__(self) -> str:  # pragma: no cover
        return f"{self.__class__.__name__}()"


# ---------------------------------------------------------------------------
# Concrete operators (stubs — delegate to existing executor)
# ---------------------------------------------------------------------------


class ScanNodes(PhysicalOp):
    """Materialises all node replicas from the network."""

    op_name = "ScanNodes"

    def execute(self, ctx: ExecutionContext, rows: List[Any]) -> List[Any]:
        """Return all ``(node, layer)`` tuples from *ctx.network*.

        If *rows* is non-empty it is returned unchanged (allows chaining after
        an upstream scan).
        """
        if rows:
            return rows
        net = ctx.network
        return list(net.get_nodes())


class ScanEdges(PhysicalOp):
    """Materialises all edges from the network."""

    op_name = "ScanEdges"

    def execute(self, ctx: ExecutionContext, rows: List[Any]) -> List[Any]:
        """Return all edge tuples from *ctx.network*."""
        if rows:
            return rows
        net = ctx.network
        return list(net.get_edges())


class LayerFilter(PhysicalOp):
    """Filters rows to only those whose layer is in *allowed_layers*."""

    op_name = "LayerFilter"

    def __init__(self, allowed_layers: Optional[List[str]] = None) -> None:
        self.allowed_layers = set(allowed_layers) if allowed_layers is not None else None

    def execute(self, ctx: ExecutionContext, rows: List[Any]) -> List[Any]:
        if self.allowed_layers is None:
            return rows
        out = []
        for row in rows:
            # node replica: (node_id, layer)
            if isinstance(row, (tuple, list)) and len(row) >= 2:
                layer = row[1]
                if layer in self.allowed_layers:
                    out.append(row)
            else:
                out.append(row)
        return out

    def __repr__(self) -> str:  # pragma: no cover
        return f"LayerFilter(layers={self.allowed_layers!r})"


class PredicateFilter(PhysicalOp):
    """Filters rows using a Python callable predicate."""

    op_name = "PredicateFilter"

    def __init__(self, predicate: Any = None, description: str = "") -> None:
        self._predicate = predicate
        self.description = description

    def execute(self, ctx: ExecutionContext, rows: List[Any]) -> List[Any]:
        if self._predicate is None:
            return rows
        return [row for row in rows if self._predicate(row, ctx)]

    def __repr__(self) -> str:  # pragma: no cover
        return f"PredicateFilter({self.description!r})"


class ComputeMetric(PhysicalOp):
    """Wrapper operator — actual computation is handled by the executor.

    This stub records *which* metrics were requested so they are visible in
    plan/explain output.
    """

    op_name = "ComputeMetric"

    def __init__(self, measures: Optional[List[str]] = None) -> None:
        self.measures: List[str] = list(measures) if measures else []

    def execute(self, ctx: ExecutionContext, rows: List[Any]) -> List[Any]:
        # Computation is delegated to the full executor; rows are passed through.
        return rows

    def __repr__(self) -> str:  # pragma: no cover
        return f"ComputeMetric(measures={self.measures!r})"


class OrderBy(PhysicalOp):
    """Sorts *rows* by a named attribute stored in ``ctx.attributes``."""

    op_name = "OrderBy"

    def __init__(self, key: str = "", descending: bool = False) -> None:
        self.key = key
        self.descending = descending

    def execute(self, ctx: ExecutionContext, rows: List[Any]) -> List[Any]:
        attr_map = ctx.attributes.get(self.key, {})
        if not attr_map:
            return rows
        try:
            return sorted(
                rows,
                key=lambda r: attr_map.get(r, 0),
                reverse=self.descending,
            )
        except Exception:  # pragma: no cover
            return rows

    def __repr__(self) -> str:  # pragma: no cover
        direction = "desc" if self.descending else "asc"
        return f"OrderBy(key={self.key!r}, {direction})"


class Limit(PhysicalOp):
    """Truncates rows to at most *n* items."""

    op_name = "Limit"

    def __init__(self, n: int = 0) -> None:
        self.n = n

    def execute(self, ctx: ExecutionContext, rows: List[Any]) -> List[Any]:
        if self.n <= 0:
            return rows
        return rows[: self.n]

    def __repr__(self) -> str:  # pragma: no cover
        return f"Limit(n={self.n!r})"
