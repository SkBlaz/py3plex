"""OutOfCoreNetwork descriptor and constructors."""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from .errors import OutOfCoreIOError, SchemaError
from .schema import SUPPORTED_EDGE_FORMATS


# ---------------------------------------------------------------------------
# DSL-style kwarg condition parser
# ---------------------------------------------------------------------------

_SUFFIX_OPS = {
    "__gt": "gt",
    "__gte": "gte",
    "__ge": "ge",
    "__lt": "lt",
    "__lte": "lte",
    "__le": "le",
    "__eq": "eq",
    "__ne": "ne",
}


def _parse_condition_kwargs(conditions: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Parse DSL-style ``field__op=value`` kwargs into condition dicts.

    For example::

        _parse_condition_kwargs({"weight__gt": 0.5, "source__eq": "Alice"})
        # [{"field": "weight", "op": "gt", "value": 0.5},
        #  {"field": "source", "op": "eq", "value": "Alice"}]

    Plain ``field=value`` (no operator suffix) is treated as equality.

    Args:
        conditions: Mapping of ``field__op`` to value (from **kwargs).

    Returns:
        List of condition spec dicts with keys ``field``, ``op``, ``value``.
    """
    result = []
    for key, value in conditions.items():
        matched = False
        for suffix, op in _SUFFIX_OPS.items():
            if key.endswith(suffix):
                field = key[: -len(suffix)]
                result.append({"field": field, "op": op, "value": value})
                matched = True
                break
        if not matched:
            # No operator suffix – treat as equality
            result.append({"field": key, "op": "eq", "value": value})
    return result


class OutOfCoreNetwork:
    """Descriptor for a multilayer network stored on disk.

    An ``OutOfCoreNetwork`` does not load any data into memory at
    construction time.  It records the location and format of the on-disk
    edge (and optional node) table so that the executor can scan them in
    chunks when a query is executed.

    Args:
        edges_path: Path to the edge table file (or directory for Parquet).
        edges_format: One of ``"csv"``, ``"parquet"``, ``"arrow"``,
                      ``"jsonl"``.
        nodes_path: Optional path to the node table.
        nodes_format: Format of the node table (same options as edges).
        directed: Whether the network is directed (default ``False``).
        partitioning: Optional metadata dict describing how the data is
                      physically partitioned (e.g. by ``source_layer``).
        fingerprint: Optional pre-computed counts dict, e.g.
                     ``{"node_count": 1000, "edge_count": 5000}``.
        workdir: Working directory for spill files during query execution.
                 Defaults to the system temp directory.
    """

    is_out_of_core: bool = True

    def __init__(
        self,
        edges_path: str,
        edges_format: str = "csv",
        nodes_path: Optional[str] = None,
        nodes_format: Optional[str] = None,
        directed: bool = False,
        partitioning: Optional[Dict[str, Any]] = None,
        fingerprint: Optional[Dict[str, Any]] = None,
        workdir: Optional[str] = None,
    ) -> None:
        fmt = edges_format.lower()
        if fmt not in SUPPORTED_EDGE_FORMATS:
            raise OutOfCoreIOError(
                f"Unsupported edge format {edges_format!r}. "
                f"Supported: {SUPPORTED_EDGE_FORMATS}"
            )
        self.edges_path = str(edges_path)
        self.edges_format = fmt
        self.nodes_path = str(nodes_path) if nodes_path else None
        self.nodes_format = nodes_format.lower() if nodes_format else None
        self.directed = directed
        self.partitioning = partitioning or {}
        self.fingerprint: Dict[str, Any] = fingerprint or {}
        self.workdir = workdir
        # Mark fingerprint as estimated when counts are not provided
        if "node_count" not in self.fingerprint and "edge_count" not in self.fingerprint:
            self.fingerprint["estimated"] = True

    # ------------------------------------------------------------------
    # Constructors
    # ------------------------------------------------------------------

    @classmethod
    def from_edges_csv(
        cls,
        path: str,
        directed: bool = False,
        workdir: Optional[str] = None,
    ) -> "OutOfCoreNetwork":
        """Create an OutOfCoreNetwork backed by a CSV edge list.

        The CSV must have a header row with at least the columns:
        ``source``, ``target``, ``source_layer``, ``target_layer``.

        Args:
            path: Path to the CSV file.
            directed: Whether edges are directed.
            workdir: Spill workdir.

        Returns:
            OutOfCoreNetwork instance.
        """
        if not os.path.isfile(path):
            raise OutOfCoreIOError(f"CSV file not found: {path!r}")
        return cls(
            edges_path=path,
            edges_format="csv",
            directed=directed,
            workdir=workdir,
        )

    @classmethod
    def from_edges_parquet(
        cls,
        path: str,
        directed: bool = False,
        workdir: Optional[str] = None,
    ) -> "OutOfCoreNetwork":
        """Create an OutOfCoreNetwork backed by a Parquet edge table.

        Requires ``pyarrow`` to be installed.

        Args:
            path: Path to a Parquet file or directory.
            directed: Whether edges are directed.
            workdir: Spill workdir.

        Returns:
            OutOfCoreNetwork instance.
        """
        if not os.path.exists(path):
            raise OutOfCoreIOError(f"Parquet path not found: {path!r}")
        return cls(
            edges_path=path,
            edges_format="parquet",
            directed=directed,
            workdir=workdir,
        )

    # ------------------------------------------------------------------
    # Info
    # ------------------------------------------------------------------

    def info(self) -> Dict[str, Any]:
        """Return a summary dict of the network descriptor.

        Returns:
            Dict with keys: edges_path, edges_format, directed,
            nodes_path, nodes_format, fingerprint, partitioning.
        """
        return {
            "edges_path": self.edges_path,
            "edges_format": self.edges_format,
            "directed": self.directed,
            "nodes_path": self.nodes_path,
            "nodes_format": self.nodes_format,
            "fingerprint": dict(self.fingerprint),
            "partitioning": dict(self.partitioning),
            "workdir": self.workdir,
        }

    def __repr__(self) -> str:
        return (
            f"OutOfCoreNetwork("
            f"edges={self.edges_path!r}, "
            f"format={self.edges_format!r}, "
            f"directed={self.directed})"
        )

    # ------------------------------------------------------------------
    # Builder-style query methods (DSL-like API)
    # ------------------------------------------------------------------

    def query_edges(
        self,
        layer: Optional[str] = None,
        layers: Optional[List[str]] = None,
        limit: Optional[int] = None,
        order_by: Optional[str] = None,
        order_asc: bool = True,
        per_layer_pair: bool = False,
        coverage_k: Optional[int] = None,
        **conditions: Any,
    ) -> "QueryResultOutOfCore":
        """Query edges using a DSL-style builder interface.

        Supports predicate pushdown, chunked scanning, optional sorting,
        per-layer-pair aggregation, and coverage filtering — all without
        loading the full graph into memory.

        Args:
            layer: Single layer name to filter on (any-touch semantics: edge
                   passes if either endpoint layer matches).
            layers: List of layer names (alternative to ``layer``).
            limit: Maximum number of edges to return.
            order_by: Column name to sort by.  Prefix with ``"-"`` for
                      descending order (e.g. ``"-weight"``).
            order_asc: Sort ascending when ``True`` (default).  Ignored when
                       ``order_by`` starts with ``"-"``.
            per_layer_pair: When ``True``, return edge counts grouped by
                            ``(source_layer, target_layer)`` pairs instead of
                            individual edges.
            coverage_k: When set, keep only edges whose ``(source, target)``
                        base pair appears in at least *k* distinct layer pairs.
            **conditions: Attribute filter conditions using DSL-style
                          ``field__op=value`` syntax.  For example:
                          ``weight__gt=0.5``, ``source__eq="Alice"``,
                          ``weight__lte=1.0``.  A plain ``field=value``
                          (no operator suffix) is treated as equality.

        Returns:
            :class:`~py3plex.out_of_core.executor.QueryResultOutOfCore`

        Example::

            net = OutOfCoreNetwork.from_edges_csv("edges.csv")

            # Filter edges in the social layer with weight > 0.5
            result = net.query_edges(layer="social", weight__gt=0.5, limit=100)
            df = result.to_pandas()

            # Multiple layers, sorted by weight descending
            result = net.query_edges(layers=["social", "work"],
                                     order_by="-weight", limit=50)

            # Per-layer-pair edge counts
            result = net.query_edges(per_layer_pair=True)

            # Cross-layer coverage: edges in >= 2 layer pairs
            result = net.query_edges(coverage_k=2, limit=200)
        """
        from .executor import OutOfCoreBackend

        layer_names: Optional[List[str]] = None
        if layer is not None:
            layer_names = [layer] if isinstance(layer, str) else list(layer)
        elif layers is not None:
            layer_names = list(layers)

        condition_dicts = _parse_condition_kwargs(conditions)

        order_spec: Optional[Dict[str, Any]] = None
        if order_by is not None:
            if order_by.startswith("-"):
                order_spec = {"key": order_by[1:], "asc": False}
            else:
                order_spec = {"key": order_by, "asc": order_asc}

        groupby_spec: Optional[Dict[str, Any]] = None
        if per_layer_pair:
            groupby_spec = {
                "key_fields": ["source_layer", "target_layer"],
                "aggregations": {"edge_count": "count"},
            }

        coverage_spec: Optional[Dict[str, Any]] = None
        if coverage_k is not None:
            coverage_spec = {"mode": "at_least", "k": coverage_k}

        plan: Dict[str, Any] = {
            "target": "edges",
            "layer_names": layer_names,
            "conditions": condition_dicts,
            "order_by": order_spec,
            "limit_n": limit,
            "groupby": groupby_spec,
            "coverage": coverage_spec,
            "directed": self.directed,
        }

        backend = OutOfCoreBackend(self)
        return backend.execute(plan)

    def query_nodes(
        self,
        layer: Optional[str] = None,
        layers: Optional[List[str]] = None,
        limit: Optional[int] = None,
        order_by: Optional[str] = None,
        order_asc: bool = True,
        per_layer: bool = False,
        **conditions: Any,
    ) -> "QueryResultOutOfCore":
        """Query nodes using a DSL-style builder interface.

        Node degree is computed out-of-core by scanning the edge table (no
        full adjacency structure needed).  Degree-based conditions
        (``degree__gt``, ``degree__lte``, etc.) are pushed down to an
        in-process SQLite accumulator.

        Args:
            layer: Single layer name to restrict the search to.
            layers: List of layer names (alternative to ``layer``).
            limit: Maximum number of nodes to return.
            order_by: Column name to sort by (``"node"``, ``"degree"``,
                      ``"layer"``).  Prefix ``"-"`` for descending.
            order_asc: Sort ascending (default ``True``).
            per_layer: When ``True``, return per-layer node counts grouped
                       by layer instead of individual nodes.
            **conditions: Attribute filter conditions.  Degree-based
                          conditions are handled natively out-of-core:
                          ``degree__gt=3``, ``degree__lte=10``.

        Returns:
            :class:`~py3plex.out_of_core.executor.QueryResultOutOfCore`

        Example::

            net = OutOfCoreNetwork.from_edges_csv("edges.csv")

            # Nodes in 'work' layer with degree > 3
            result = net.query_nodes(layer="work", degree__gt=3)
            df = result.to_pandas()

            # Top-10 highest-degree nodes
            result = net.query_nodes(order_by="-degree", limit=10)

            # Per-layer node counts
            result = net.query_nodes(per_layer=True)
        """
        from .executor import OutOfCoreBackend

        layer_names: Optional[List[str]] = None
        if layer is not None:
            layer_names = [layer] if isinstance(layer, str) else list(layer)
        elif layers is not None:
            layer_names = list(layers)

        condition_dicts = _parse_condition_kwargs(conditions)

        order_spec: Optional[Dict[str, Any]] = None
        if order_by is not None:
            if order_by.startswith("-"):
                order_spec = {"key": order_by[1:], "asc": False}
            else:
                order_spec = {"key": order_by, "asc": order_asc}

        groupby_spec: Optional[Dict[str, Any]] = None
        if per_layer:
            groupby_spec = {
                "key_fields": ["layer"],
                "aggregations": {"node_count": "count"},
            }

        plan: Dict[str, Any] = {
            "target": "nodes",
            "layer_names": layer_names,
            "conditions": condition_dicts,
            "order_by": order_spec,
            "limit_n": limit,
            "groupby": groupby_spec,
            "directed": self.directed,
        }

        backend = OutOfCoreBackend(self)
        return backend.execute(plan)


# ---------------------------------------------------------------------------
# Forward declaration: QueryResultOutOfCore type alias for type hints
# ---------------------------------------------------------------------------
# Avoid circular import by using a string annotation; the real class lives in
# executor.py and is only imported inside the query methods above.
try:
    from .executor import QueryResultOutOfCore  # noqa: F401
except ImportError:
    pass
