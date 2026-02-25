"""Out-of-core query execution backend for DSL v2 queries.

Supports the following MVP query patterns without loading the full graph:

1. Edge selection: from_layers + where on scalar attrs + limit/order_by
2. Node selection with degree threshold (degree__gt/lt/gte/lte)
3. per_layer() aggregations for edge counts and degree
4. coverage(mode="at_least", k=N) for edges across layer pairs
"""

from __future__ import annotations

import sqlite3
import tempfile
import os
import time
from typing import Any, Dict, Iterator, List, Optional, Tuple

from .errors import OutOfCoreIOError, SchemaError, UnsupportedOutOfCoreOperation
from .network import OutOfCoreNetwork
from .operators import (
    add_field,
    external_groupby,
    external_sort,
    filter_rows,
    limit as op_limit,
    project,
    top_n,
)
from .readers import build_predicates, make_edge_reader
from .schema import canonical_undirected_edge_key


# ---------------------------------------------------------------------------
# Query result wrapper
# ---------------------------------------------------------------------------

class QueryResultOutOfCore:
    """Lazy result wrapper for out-of-core queries.

    Avoids loading large result sets into memory unless explicitly requested.

    Args:
        items: List of items (nodes as (id, layer) or edges as
               (src, dst, src_layer, dst_layer)).
        attributes: Dict mapping attribute name → list of values (parallel to items).
        target: ``"nodes"`` or ``"edges"``.
        meta: Execution metadata dict.
        max_rows: Safety cap applied at construction if items were pre-loaded.
    """

    DEFAULT_MAX_ROWS: int = 10_000

    def __init__(
        self,
        items: List[Any],
        attributes: Dict[str, List[Any]],
        target: str,
        meta: Optional[Dict[str, Any]] = None,
        max_rows: Optional[int] = DEFAULT_MAX_ROWS,
    ) -> None:
        self.items = items
        self.attributes = attributes
        self.target = target
        self.meta = meta or {}
        self._max_rows = max_rows

    @property
    def count(self) -> int:
        """Number of items in the result."""
        return len(self.items)

    def head(self, n: int = 10) -> "QueryResultOutOfCore":
        """Return a new result with at most *n* items."""
        return QueryResultOutOfCore(
            items=self.items[:n],
            attributes={k: v[:n] for k, v in self.attributes.items()},
            target=self.target,
            meta=dict(self.meta),
            max_rows=None,
        )

    def to_pandas(self, limit: Optional[int] = DEFAULT_MAX_ROWS):
        """Convert to a pandas DataFrame.

        Args:
            limit: Maximum rows to return.  Pass ``None`` to disable the cap.

        Returns:
            pandas DataFrame.
        """
        try:
            import pandas as pd
        except ImportError as exc:
            raise ImportError("pandas is required for to_pandas()") from exc

        items = self.items
        attrs = self.attributes
        if limit is not None:
            items = items[:limit]
            attrs = {k: v[:limit] for k, v in attrs.items()}

        if self.target == "nodes":
            rows = [{"id": i[0], "layer": i[1]} for i in items]
        else:
            rows = [
                {
                    "source": i[0],
                    "target": i[1],
                    "source_layer": i[2],
                    "target_layer": i[3],
                }
                for i in items
            ]

        df = pd.DataFrame(rows)
        for col, vals in attrs.items():
            df[col] = vals[:len(df)]
        return df

    def to_arrow(self, limit: Optional[int] = DEFAULT_MAX_ROWS):
        """Convert to an Arrow table (requires pyarrow).

        Args:
            limit: Maximum rows.

        Returns:
            pyarrow.Table.
        """
        try:
            import pyarrow as pa
        except ImportError as exc:
            raise ImportError("pyarrow is required for to_arrow()") from exc

        df = self.to_pandas(limit=limit)
        return pa.Table.from_pandas(df)

    def __repr__(self) -> str:
        return (
            f"QueryResultOutOfCore("
            f"target={self.target!r}, count={self.count}, "
            f"attributes={list(self.attributes)})"
        )


# ---------------------------------------------------------------------------
# Helper: build layer filter predicates
# ---------------------------------------------------------------------------

def _layer_predicates(layer_names: Optional[List[str]]) -> List:
    """Return predicates that filter edges to *layer_names*.

    For edge queries we check source_layer and target_layer both.
    An edge passes if source_layer AND target_layer are both in layer_names
    (intra-layer) OR if at least one of them is in layer_names (any-touch).

    For the MVP we use "any-touch": the edge appears in the result if at
    least one endpoint layer is in the requested layers, matching the
    in-memory executor semantics for ``from_layers``.

    Args:
        layer_names: List of layer names, or None for all layers.

    Returns:
        List of predicate callables (empty list = pass all).
    """
    if not layer_names:
        return []
    layer_set = set(layer_names)

    def _pred(row: dict) -> bool:
        sl = row.get("source_layer", "")
        tl = row.get("target_layer", "")
        return sl in layer_set or tl in layer_set

    return [_pred]


# ---------------------------------------------------------------------------
# Main out-of-core executor
# ---------------------------------------------------------------------------

class OutOfCoreBackend:
    """Execute DSL v2 query plans against an OutOfCoreNetwork.

    This class is the single execution entry point for the out-of-core
    backend.  The DSL executor calls ``execute()`` with a parsed query plan.

    In-memory integration: The DSL executor checks
    ``isinstance(network, OutOfCoreNetwork)`` and delegates here.

    Args:
        network: The OutOfCoreNetwork descriptor.
    """

    def __init__(self, network: OutOfCoreNetwork) -> None:
        self.network = network

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def execute(self, plan: Dict[str, Any]) -> QueryResultOutOfCore:
        """Execute a query plan and return a QueryResultOutOfCore.

        The *plan* dict mirrors the minimal subset of the DSL v2 AST that
        the out-of-core backend supports:

        ``target``: ``"nodes"`` or ``"edges"``
        ``layer_names``: Optional list of layer names (from_layers filter).
        ``conditions``: List of ``{field, op, value}`` dicts (where clause).
        ``compute``: List of measure names to compute.
        ``order_by``: Optional ``{key: field, asc: bool}``.
        ``limit_n``: Optional int.
        ``groupby``: Optional ``{key_fields, aggregations}`` (per_layer).
        ``coverage``: Optional ``{mode, k}`` for cross-layer coverage.
        ``directed``: Whether to treat the graph as directed.

        Args:
            plan: Query plan dict.

        Returns:
            QueryResultOutOfCore with results.
        """
        t_start = time.perf_counter()
        target = plan.get("target", "edges")
        compute = plan.get("compute", [])

        # Validate compute measures
        self._validate_compute(compute)

        if target == "edges":
            result = self._execute_edges(plan)
        elif target == "nodes":
            result = self._execute_nodes(plan)
        else:
            raise UnsupportedOutOfCoreOperation(f"target={target!r}")

        elapsed = time.perf_counter() - t_start
        backend_info = {
            "graph_backend": "out_of_core",
            "fast_path": True,
            "edges_format": self.network.edges_format,
        }
        performance_info = {"total_ms": round(elapsed * 1000, 3)}
        network_fingerprint = dict(self.network.fingerprint)

        # Flat top-level keys (backward compat)
        result.meta["performance"] = performance_info
        result.meta["engine"] = "dsl_v2_executor_out_of_core"
        result.meta["backend"] = backend_info
        result.meta["network_fingerprint"] = network_fingerprint

        # Nested provenance dict (matches DSL v2 provenance schema expected by tests)
        result.meta["provenance"] = {
            "engine": "dsl_v2_executor_out_of_core",
            "backend": backend_info,
            "performance": performance_info,
            "network_fingerprint": network_fingerprint,
        }
        return result

    # ------------------------------------------------------------------
    # Edge selection
    # ------------------------------------------------------------------

    def _execute_edges(self, plan: Dict[str, Any]) -> QueryResultOutOfCore:
        layer_names = plan.get("layer_names")
        conditions = plan.get("conditions", [])
        order_spec = plan.get("order_by")
        limit_n = plan.get("limit_n")
        coverage_spec = plan.get("coverage")
        groupby_spec = plan.get("groupby")

        reader = make_edge_reader(
            self.network.edges_path,
            self.network.edges_format,
        )

        # Build predicates: layer filter + attribute conditions
        preds = _layer_predicates(layer_names) + build_predicates(conditions)

        if coverage_spec:
            return self._execute_edges_coverage(reader, preds, coverage_spec, plan)

        if groupby_spec:
            return self._execute_edges_groupby(reader, preds, groupby_spec, plan)

        rows = reader.scan(predicates=preds)

        # Sorting + limit
        if order_spec and limit_n:
            key = order_spec.get("key", "source")
            asc = order_spec.get("asc", True)
            result_rows = top_n(rows, n=limit_n, key_fields=[key], asc=asc)
        elif order_spec:
            key = order_spec.get("key", "source")
            asc = order_spec.get("asc", True)
            result_rows = list(
                external_sort(rows, key_fields=[key], asc=asc, workdir=self.network.workdir)
            )
        elif limit_n:
            result_rows = list(op_limit(rows, limit_n))
        else:
            result_rows = list(rows)

        return self._rows_to_edge_result(result_rows, plan)

    def _execute_edges_coverage(
        self,
        reader,
        preds: List,
        coverage_spec: Dict[str, Any],
        plan: Dict[str, Any],
    ) -> QueryResultOutOfCore:
        """Apply coverage filter: keep edges present in >= k layer pairs."""
        k = coverage_spec.get("k", 1)
        directed = plan.get("directed", self.network.directed)

        # Step 1: emit (base_edge_key, source_layer, target_layer) per row
        def _key_rows(reader, preds):
            for row in reader.scan(predicates=preds):
                s = str(row.get("source", ""))
                t = str(row.get("target", ""))
                sl = str(row.get("source_layer", ""))
                tl = str(row.get("target_layer", ""))
                if directed:
                    base = (s, t)
                else:
                    base = canonical_undirected_edge_key(s, t)
                yield {
                    "_base_src": base[0],
                    "_base_dst": base[1],
                    "_sl": sl,
                    "_tl": tl,
                    "_orig_row": row,
                }

        # Step 2: count distinct layer pairs per base edge using sqlite3
        conn = sqlite3.connect(":memory:")
        cur = conn.cursor()
        cur.execute(
            "CREATE TABLE _edge_lp ("
            "  base_src TEXT, base_dst TEXT, sl TEXT, tl TEXT, "
            "  PRIMARY KEY(base_src, base_dst, sl, tl))"
        )
        # Also count rows for later result reconstruction
        cur.execute(
            "CREATE TABLE _edge_rows ("
            "  base_src TEXT, base_dst TEXT, sl TEXT, tl TEXT, row_json TEXT)"
        )
        import json
        for krow in _key_rows(reader, preds):
            bs, bd = krow["_base_src"], krow["_base_dst"]
            sl, tl = krow["_sl"], krow["_tl"]
            try:
                cur.execute("INSERT OR IGNORE INTO _edge_lp VALUES (?,?,?,?)", (bs, bd, sl, tl))
            except sqlite3.IntegrityError:
                pass
            cur.execute(
                "INSERT INTO _edge_rows VALUES (?,?,?,?,?)",
                (bs, bd, sl, tl, json.dumps(krow["_orig_row"], ensure_ascii=False)),
            )

        # Step 3: find base edges with >= k distinct layer pairs
        cur.execute(
            "SELECT base_src, base_dst FROM _edge_lp "
            "GROUP BY base_src, base_dst HAVING COUNT(*) >= ?",
            (k,),
        )
        qualifying = set((r[0], r[1]) for r in cur.fetchall())
        conn.close()

        # Step 4: re-scan original reader (or use stored rows) and filter
        reader2 = make_edge_reader(self.network.edges_path, self.network.edges_format)
        result_rows = []
        for row in reader2.scan(predicates=preds):
            s = str(row.get("source", ""))
            t = str(row.get("target", ""))
            if not directed:
                base = canonical_undirected_edge_key(s, t)
            else:
                base = (s, t)
            if base in qualifying:
                result_rows.append(row)

        limit_n = plan.get("limit_n")
        if limit_n:
            result_rows = result_rows[:limit_n]

        return self._rows_to_edge_result(result_rows, plan)

    def _execute_edges_groupby(
        self,
        reader,
        preds: List,
        groupby_spec: Dict[str, Any],
        plan: Dict[str, Any],
    ) -> QueryResultOutOfCore:
        """Execute per-layer edge aggregations."""
        key_fields = groupby_spec.get("key_fields", ["source_layer", "target_layer"])
        aggs_spec = groupby_spec.get("aggregations", {"edge_count": "count"})

        agg_fns: Dict[str, Any] = {}
        for out_col, agg_type in aggs_spec.items():
            if agg_type == "count":
                agg_fns[out_col] = lambda buf: len(buf)
            elif agg_type == "sum_weight":
                agg_fns[out_col] = lambda buf: sum(
                    float(r.get("weight") or 0) for r in buf
                )
            elif agg_type == "mean_weight":
                def _mean(buf):
                    vals = [float(r.get("weight") or 0) for r in buf]
                    return sum(vals) / len(vals) if vals else 0.0
                agg_fns[out_col] = _mean
            else:
                agg_fns[out_col] = lambda buf: len(buf)

        grouped = list(
            external_groupby(
                reader.scan(predicates=preds),
                key_fields=key_fields,
                aggregations=agg_fns,
                workdir=self.network.workdir,
            )
        )

        # Build QueryResultOutOfCore from aggregation rows
        items = []
        attrs: Dict[str, List] = {col: [] for col in agg_fns}
        for grow in grouped:
            key_tuple = tuple(grow.get(f, "") for f in key_fields)
            if len(key_fields) == 2:
                items.append((key_tuple[0], key_tuple[1]))
            else:
                items.append(key_tuple)
            for col in agg_fns:
                attrs[col].append(grow.get(col))

        return QueryResultOutOfCore(
            items=items,
            attributes=attrs,
            target="edges",
            meta={"grouping": {"mode": "per_layer_pair", "key_fields": key_fields}},
        )

    # ------------------------------------------------------------------
    # Node selection (with out-of-core degree computation)
    # ------------------------------------------------------------------

    def _execute_nodes(self, plan: Dict[str, Any]) -> QueryResultOutOfCore:
        layer_names = plan.get("layer_names")
        conditions = plan.get("conditions", [])
        order_spec = plan.get("order_by")
        limit_n = plan.get("limit_n")
        groupby_spec = plan.get("groupby")
        compute = plan.get("compute", [])

        degree_conditions = [c for c in conditions if c["field"] == "degree"]
        other_conditions = [c for c in conditions if c["field"] != "degree"]

        needs_degree = bool(degree_conditions) or "degree" in compute

        if needs_degree:
            return self._execute_nodes_with_degree(
                layer_names, degree_conditions, other_conditions, groupby_spec, order_spec, limit_n, plan
            )

        # Without degree: scan node table if available; else derive from edges.
        if self.network.nodes_path:
            return self._scan_node_table(layer_names, other_conditions, order_spec, limit_n, plan)

        # No explicit degree conditions but caller wants node list – derive
        # all nodes from edges and always include computed degree.
        return self._execute_nodes_with_degree(
            layer_names, [], other_conditions, groupby_spec, order_spec, limit_n, plan
        )

    def _execute_nodes_with_degree(
        self,
        layer_names: Optional[List[str]],
        degree_conditions: List[Dict],
        other_conditions: List[Dict],
        groupby_spec: Optional[Dict],
        order_spec: Optional[Dict],
        limit_n: Optional[int],
        plan: Dict[str, Any],
    ) -> QueryResultOutOfCore:
        """Compute node degrees out-of-core via SQLite then filter/sort."""
        directed = plan.get("directed", self.network.directed)

        reader = make_edge_reader(
            self.network.edges_path,
            self.network.edges_format,
        )
        layer_preds = _layer_predicates(layer_names)
        other_preds = build_predicates(other_conditions)
        all_preds = layer_preds + other_preds

        # Use SQLite as bounded external KV store for degree accumulation
        db_path = tempfile.mktemp(suffix=".db", dir=self.network.workdir)
        try:
            conn = sqlite3.connect(db_path)
            cur = conn.cursor()
            cur.execute(
                "CREATE TABLE degrees "
                "(node TEXT, layer TEXT, degree INTEGER, PRIMARY KEY(node, layer))"
            )
            conn.commit()

            for row in reader.scan(predicates=all_preds):
                src = str(row.get("source", ""))
                tgt = str(row.get("target", ""))
                sl = str(row.get("source_layer", ""))
                tl = str(row.get("target_layer", ""))

                # Undirected: increment both endpoints; directed: same (total degree)
                for node, layer in [(src, sl), (tgt, tl)]:
                    cur.execute(
                        "INSERT INTO degrees(node, layer, degree) VALUES(?,?,1) "
                        "ON CONFLICT(node, layer) DO UPDATE SET degree=degree+1",
                        (node, layer),
                    )

            conn.commit()

            # Build SQL WHERE clause for degree conditions
            sql_parts = ["1=1"]
            sql_params = []
            for dc in degree_conditions:
                op_map = {
                    "gt": ">", "gte": ">=", "ge": ">=",
                    "lt": "<", "lte": "<=", "le": "<=",
                    "eq": "=", "ne": "!=",
                }
                sql_op = op_map.get(dc["op"], "=")
                sql_parts.append(f"degree {sql_op} ?")
                sql_params.append(int(dc["value"]))

            where_clause = " AND ".join(sql_parts)
            order_clause = "ORDER BY node, layer"
            if order_spec:
                key = order_spec.get("key", "node")
                direction = "ASC" if order_spec.get("asc", True) else "DESC"
                order_clause = f"ORDER BY {key} {direction}"

            limit_clause = ""
            if limit_n:
                limit_clause = f"LIMIT {int(limit_n)}"

            cur.execute(
                f"SELECT node, layer, degree FROM degrees "
                f"WHERE {where_clause} {order_clause} {limit_clause}",
                sql_params,
            )
            db_rows = cur.fetchall()
            conn.close()

        finally:
            try:
                os.unlink(db_path)
            except Exception:
                pass

        items = [(r[0], r[1]) for r in db_rows]
        degree_vals = [r[2] for r in db_rows]

        if groupby_spec:
            # per_layer aggregation
            key_fields = groupby_spec.get("key_fields", ["layer"])
            layer_counts: Dict[str, int] = {}
            for (node, layer), _deg in zip(items, degree_vals):
                layer_counts[layer] = layer_counts.get(layer, 0) + 1
            grp_items = [(layer,) for layer in sorted(layer_counts)]
            grp_attrs = {"node_count": [layer_counts[l[0]] for l in grp_items]}
            return QueryResultOutOfCore(
                items=grp_items,
                attributes=grp_attrs,
                target="nodes",
                meta={"grouping": {"mode": "per_layer", "key_fields": key_fields}},
            )

        return QueryResultOutOfCore(
            items=items,
            attributes={"degree": degree_vals},
            target="nodes",
        )

    def _scan_node_table(
        self,
        layer_names: Optional[List[str]],
        conditions: List[Dict],
        order_spec: Optional[Dict],
        limit_n: Optional[int],
        plan: Dict[str, Any],
    ) -> QueryResultOutOfCore:
        """Scan the node table when it exists."""
        reader = make_edge_reader(
            self.network.nodes_path,
            self.network.nodes_format or "csv",
        )
        preds: List = []
        if layer_names:
            layer_set = set(layer_names)
            preds.append(lambda r: r.get("layer", "") in layer_set)
        preds += build_predicates(conditions)

        rows = reader.scan(predicates=preds)
        if order_spec:
            key = order_spec.get("key", "id")
            asc = order_spec.get("asc", True)
            if limit_n:
                rows_list = top_n(rows, n=limit_n, key_fields=[key], asc=asc)
            else:
                rows_list = list(external_sort(rows, key_fields=[key], asc=asc, workdir=self.network.workdir))
        elif limit_n:
            rows_list = list(op_limit(rows, limit_n))
        else:
            rows_list = list(rows)

        items = [(r.get("id", ""), r.get("layer", "")) for r in rows_list]
        return QueryResultOutOfCore(items=items, attributes={}, target="nodes")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _rows_to_edge_result(
        rows: List[dict],
        plan: Dict[str, Any],
    ) -> QueryResultOutOfCore:
        """Convert a list of edge row dicts to a QueryResultOutOfCore."""
        items = []
        weight_vals = []
        has_weight = any("weight" in r for r in rows)
        extra_keys: List[str] = []
        if rows:
            extra_keys = [
                k for k in rows[0]
                if k not in ("source", "target", "source_layer", "target_layer", "weight")
            ]

        for row in rows:
            items.append((
                row.get("source", ""),
                row.get("target", ""),
                row.get("source_layer", ""),
                row.get("target_layer", ""),
            ))
            if has_weight:
                weight_vals.append(row.get("weight"))

        attrs: Dict[str, List] = {}
        if has_weight:
            attrs["weight"] = weight_vals
        for k in extra_keys:
            attrs[k] = [r.get(k) for r in rows]

        return QueryResultOutOfCore(
            items=items,
            attributes=attrs,
            target="edges",
        )

    @staticmethod
    def _validate_compute(compute: List[str]) -> None:
        """Raise UnsupportedOutOfCoreOperation for unsupported measures."""
        unsupported = {
            "betweenness_centrality",
            "closeness_centrality",
            "eigenvector_centrality",
            "pagerank",
            "clustering",
            "triangles",
        }
        requested = set(compute) & unsupported
        if requested:
            raise UnsupportedOutOfCoreOperation(
                f"compute measures: {sorted(requested)}",
                suggestion=(
                    "Load the network into memory with multi_layer_network() "
                    "for exact centrality computations."
                ),
            )
