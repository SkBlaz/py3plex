"""Dplyr-style chainable graph operations API for py3plex.

This module provides a fluent, method-chaining interface for working with
nodes and edges in py3plex multilayer networks, inspired by R's dplyr verbs.

Key Features:
    - NodeFrame and EdgeFrame: Chainable views over collections
    - Verbs: filter, select, mutate, arrange, head, group_by, summarise
    - Export: to_pandas, to_subgraph

Example Usage:
    >>> import numpy as np
    >>> from py3plex.core import multinet
    >>> from py3plex.graph_ops import nodes, edges
    >>>
    >>> # Create a multilayer network
    >>> net = multinet.multi_layer_network(directed=False)
    >>> net.add_edges([
    ...     {'source': 'A', 'target': 'B', 'source_type': 'ppi', 'target_type': 'ppi'},
    ...     {'source': 'B', 'target': 'C', 'source_type': 'ppi', 'target_type': 'ppi'},
    ...     {'source': 'A', 'target': 'C', 'source_type': 'ppi', 'target_type': 'ppi'},
    ... ])
    >>>
    >>> # Chainable operations on nodes
    >>> df = (
    ...     nodes(net, layers=["ppi"])
    ...     .filter(lambda n: n["degree"] > 1)
    ...     .mutate(normalized_degree=lambda n: n["degree"] / 3)
    ...     .to_pandas()
    ... )

dplyr Mapping:
    - dplyr::filter  -> NodeFrame.filter / EdgeFrame.filter
    - dplyr::select  -> NodeFrame.select / EdgeFrame.select
    - dplyr::mutate  -> NodeFrame.mutate / EdgeFrame.mutate
    - dplyr::arrange -> NodeFrame.arrange / EdgeFrame.arrange
    - dplyr::group_by -> NodeFrame.group_by
    - dplyr::summarise -> GroupedNodeFrame.summarise
    - dplyr::head    -> NodeFrame.head / EdgeFrame.head

Note:
    There is no direct equivalent of joins or relational joins yet;
    the design is open for joins later (e.g., joining on node ID, layer).
"""

from __future__ import annotations

import ast
import copy
from dataclasses import dataclass, field
from typing import (
    Any,
    Callable,
    Iterable,
)

# We try to import pandas; if unavailable, we define a stub for type hints
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    pd = None  # type: ignore
    PANDAS_AVAILABLE = False


# ═══════════════════════════════════════════════════════════════════════════════
# Adapter functions for py3plex
# ═══════════════════════════════════════════════════════════════════════════════


def _get_node_dicts(
    multinet: Any, layers: list[str] | None = None
) -> list[dict[str, Any]]:
    """Extract node dictionaries from a py3plex multinet.

    This adapter creates node dicts with at least 'id', 'layer', and 'degree'
    from the underlying py3plex graph.

    Args:
        multinet: py3plex multi_layer_network object
        layers: Optional list of layers to filter by

    Returns:
        List of node dictionaries
    """
    if multinet.core_network is None:
        return []

    node_dicts: list[dict[str, Any]] = []
    degree_map = dict(multinet.core_network.degree())

    for node in multinet.get_nodes(data=True):
        # node is typically (node_tuple, data_dict) where node_tuple = (node_id, layer)
        if isinstance(node, tuple) and len(node) >= 2:
            node_tuple = node[0]
            node_data = node[1] if len(node) > 1 and isinstance(node[1], dict) else {}
        else:
            node_tuple = node
            node_data = {}

        # Extract node_id and layer from node_tuple
        if isinstance(node_tuple, tuple) and len(node_tuple) >= 2:
            node_id, layer = node_tuple[0], node_tuple[1]
        else:
            node_id = node_tuple
            layer = "default"

        # Filter by layers if specified
        if layers is not None and layer not in layers:
            continue

        node_dict: dict[str, Any] = {
            "id": node_id,
            "layer": layer,
            "degree": degree_map.get(node_tuple, 0),
            "_node_tuple": node_tuple,  # Keep original tuple for reference
        }

        # Add any additional node attributes
        if isinstance(node_data, dict):
            for key, value in node_data.items():
                if key not in node_dict:
                    node_dict[key] = value

        node_dicts.append(node_dict)

    return node_dicts


def _get_edge_dicts(
    multinet: Any, layers: list[str] | None = None
) -> list[dict[str, Any]]:
    """Extract edge dictionaries from a py3plex multinet.

    This adapter creates edge dicts with 'source', 'target', 'source_layer',
    'target_layer', and edge attributes from the underlying py3plex graph.

    Args:
        multinet: py3plex multi_layer_network object
        layers: Optional list of layers to filter by (source or target layer)

    Returns:
        List of edge dictionaries
    """
    if multinet.core_network is None:
        return []

    edge_dicts: list[dict[str, Any]] = []

    for edge in multinet.get_edges(data=True):
        # edge is typically ((source_id, source_layer), (target_id, target_layer), edge_data)
        if len(edge) >= 2:
            source_tuple = edge[0]
            target_tuple = edge[1]
            edge_data = edge[2] if len(edge) > 2 and isinstance(edge[2], dict) else {}
        else:
            continue

        # Extract source info
        if isinstance(source_tuple, tuple) and len(source_tuple) >= 2:
            source_id, source_layer = source_tuple[0], source_tuple[1]
        else:
            source_id = source_tuple
            source_layer = "default"

        # Extract target info
        if isinstance(target_tuple, tuple) and len(target_tuple) >= 2:
            target_id, target_layer = target_tuple[0], target_tuple[1]
        else:
            target_id = target_tuple
            target_layer = "default"

        # Filter by layers if specified
        if layers is not None:
            if source_layer not in layers and target_layer not in layers:
                continue

        edge_dict: dict[str, Any] = {
            "source": source_id,
            "target": target_id,
            "source_layer": source_layer,
            "target_layer": target_layer,
            "_source_tuple": source_tuple,
            "_target_tuple": target_tuple,
        }

        # Add any additional edge attributes
        if isinstance(edge_data, dict):
            for key, value in edge_data.items():
                if key not in edge_dict:
                    edge_dict[key] = value

        edge_dicts.append(edge_dict)

    return edge_dicts


# ═══════════════════════════════════════════════════════════════════════════════
# Safe expression evaluator for filter_expr
# ═══════════════════════════════════════════════════════════════════════════════


def _safe_eval_expr(expr: str, context: dict[str, Any]) -> bool:
    """Safely evaluate a filter expression string.

    Uses Python's ast module to parse and evaluate expressions with
    controlled locals, preventing code injection.

    Args:
        expr: Expression string like "degree > 10 and layer == 'ppi'"
        context: Dictionary of available variable names and values

    Returns:
        Boolean result of the expression

    Raises:
        ValueError: If expression contains disallowed constructs
    """
    # Parse the expression
    try:
        tree = ast.parse(expr, mode='eval')
    except SyntaxError as e:
        raise ValueError(f"Invalid expression syntax: {e}")

    # Validate the AST - only allow safe operations
    allowed_nodes = (
        ast.Expression,
        ast.BoolOp,
        ast.And,
        ast.Or,
        ast.Compare,
        ast.Eq,
        ast.NotEq,
        ast.Lt,
        ast.LtE,
        ast.Gt,
        ast.GtE,
        ast.In,
        ast.NotIn,
        ast.Is,
        ast.IsNot,
        ast.UnaryOp,
        ast.Not,
        ast.Name,
        ast.Load,
        ast.Constant,
        ast.BinOp,
        ast.Add,
        ast.Sub,
        ast.Mult,
        ast.Div,
        ast.Mod,
        ast.FloorDiv,
        ast.Pow,
    )

    for node in ast.walk(tree):
        if not isinstance(node, allowed_nodes):
            raise ValueError(
                f"Expression contains disallowed construct: {type(node).__name__}"
            )

    # Evaluate with controlled context
    try:
        return eval(compile(tree, '<string>', 'eval'), {"__builtins__": {}}, context)
    except Exception as e:
        raise ValueError(f"Error evaluating expression: {e}")


# ═══════════════════════════════════════════════════════════════════════════════
# GroupedNodeFrame for group_by + summarise operations
# ═══════════════════════════════════════════════════════════════════════════════


@dataclass
class GroupedNodeFrame:
    """A grouped view of nodes for aggregation operations.

    This class stores a reference to the parent NodeFrame and the grouping
    keys, enabling summarise operations across groups.

    Attributes:
        parent: The parent NodeFrame from which this was created
        group_fields: Tuple of field names to group by

    Example:
        >>> grouped = node_frame.group_by("layer")
        >>> result = grouped.summarise(
        ...     avg_degree=("degree", np.mean),
        ...     n=("id", len),
        ... )
    """

    parent: NodeFrame
    group_fields: tuple[str, ...]

    def summarise(
        self, **aggregations: tuple[str, Callable[[list[Any]], Any]]
    ) -> NodeFrame:
        """Compute aggregations for each group.

        Args:
            **aggregations: Named aggregations as tuples of (field_name, agg_function).
                Example: avg_degree=("degree", np.mean), n=("id", len)

        Returns:
            A new NodeFrame whose "nodes" are group summaries (one dict per group),
            with keys for each grouping field and each summary name.

        Example:
            >>> grouped = frame.group_by("layer")
            >>> result = grouped.summarise(
            ...     avg_degree=("degree", np.mean),
            ...     n=("id", len),
            ... )
            >>> df = result.to_pandas()
        """
        # Group the data
        groups: dict[tuple[Any, ...], list[dict[str, Any]]] = {}
        for item in self.parent._data:
            key = tuple(item.get(f) for f in self.group_fields)
            if key not in groups:
                groups[key] = []
            groups[key].append(item)

        # Compute aggregations for each group
        summaries: list[dict[str, Any]] = []
        for group_key, items in groups.items():
            summary: dict[str, Any] = {}

            # Add group key values
            for i, field_name in enumerate(self.group_fields):
                summary[field_name] = group_key[i]

            # Compute each aggregation
            for agg_name, (agg_field, agg_func) in aggregations.items():
                values = [item.get(agg_field) for item in items if agg_field in item]
                if values:
                    try:
                        summary[agg_name] = agg_func(values)
                    except Exception:
                        summary[agg_name] = None
                else:
                    summary[agg_name] = None

            summaries.append(summary)

        # Return a new NodeFrame with the summaries
        return NodeFrame(
            multinet=self.parent._multinet,
            data=summaries,
        )

    # Alias for British spelling
    summarize = summarise


# ═══════════════════════════════════════════════════════════════════════════════
# NodeFrame: Chainable view over a collection of nodes
# ═══════════════════════════════════════════════════════════════════════════════


@dataclass
class NodeFrame:
    """A chainable view over a collection of nodes.

    This class wraps a reference to the underlying py3plex graph object
    and a current selection of nodes (as a list of dicts). All verbs
    return a new NodeFrame, enabling method chaining.

    Attributes:
        multinet: Reference to the underlying py3plex multi_layer_network
        data: Current selection of nodes as a list of dicts

    Example:
        >>> df = (
        ...     nodes(multinet, layers=["ppi"])
        ...     .filter(lambda n: n["degree"] > 10)
        ...     .mutate(k=lambda n: n["degree"] / (n["weight"] + 1))
        ...     .to_pandas()
        ... )
    """

    multinet: Any
    data: list[dict[str, Any]] = field(default_factory=list)

    # Create private property aliases for internal use
    @property
    def _multinet(self) -> Any:
        return self.multinet

    @property
    def _data(self) -> list[dict[str, Any]]:
        return self.data

    def filter(self, predicate: Callable[[dict[str, Any]], bool]) -> NodeFrame:
        """Filter nodes using a predicate function.

        Corresponds to dplyr::filter.

        Args:
            predicate: A callable that takes a node dict and returns True to keep it

        Returns:
            A new NodeFrame with only the nodes where predicate(...) is True

        Example:
            >>> frame.filter(lambda n: n["degree"] > 10)
        """
        new_data = [item for item in self._data if predicate(item)]
        return NodeFrame(multinet=self._multinet, data=new_data)

    def filter_expr(self, expr: str) -> NodeFrame:
        """Filter nodes using an expression string.

        Uses a safe mini-expression evaluator for simple conditions.

        Args:
            expr: Expression string like "degree > 10 and layer == 'ppi'"

        Returns:
            A new NodeFrame with only the nodes matching the expression

        Example:
            >>> frame.filter_expr("degree > 10 and layer == 'red'")
        """
        new_data = []
        for item in self._data:
            try:
                if _safe_eval_expr(expr, item):
                    new_data.append(item)
            except (ValueError, KeyError):
                # Skip items that can't be evaluated
                pass
        return NodeFrame(multinet=self._multinet, data=new_data)

    def select(self, *fields: str) -> NodeFrame:
        """Keep only the specified attributes in node dicts.

        Corresponds to dplyr::select.

        Args:
            *fields: Names of attributes to keep

        Returns:
            A new NodeFrame with only the specified fields in each dict.
            If no fields are passed, behaves as a no-op.

        Example:
            >>> frame.select("id", "layer", "degree")
        """
        if not fields:
            return NodeFrame(multinet=self._multinet, data=copy.deepcopy(self._data))

        new_data = []
        for item in self._data:
            new_item = {k: item[k] for k in fields if k in item}
            new_data.append(new_item)
        return NodeFrame(multinet=self._multinet, data=new_data)

    def mutate(
        self, **new_fields: Callable[[dict[str, Any]], Any]
    ) -> NodeFrame:
        """Compute new attributes from existing dict values.

        Corresponds to dplyr::mutate.

        Args:
            **new_fields: Named callables to compute new field values.
                Each callable takes a node dict and returns the new value.

        Returns:
            A new NodeFrame with the new/overwritten fields

        Example:
            >>> frame.mutate(
            ...     k=lambda n: n["degree"] / (n["weight"] + 1),
            ...     log_degree=lambda n: math.log1p(n["degree"]),
            ... )
        """
        new_data = []
        for item in self._data:
            new_item = copy.copy(item)
            for field_name, compute_fn in new_fields.items():
                try:
                    new_item[field_name] = compute_fn(new_item)
                except Exception:
                    new_item[field_name] = None
            new_data.append(new_item)
        return NodeFrame(multinet=self._multinet, data=new_data)

    def arrange(
        self,
        key: str | Callable[[dict[str, Any]], Any],
        reverse: bool = False,
    ) -> NodeFrame:
        """Sort nodes by an attribute or key function.

        Corresponds to dplyr::arrange.

        Args:
            key: If a string, sort by that attribute. If callable, use as key function.
            reverse: If True, sort in descending order

        Returns:
            A new NodeFrame with sorted nodes

        Example:
            >>> frame.arrange("degree", reverse=True)
            >>> frame.arrange(lambda n: -n["degree"])
        """
        if isinstance(key, str):
            def key_fn(item):
                return item.get(key, 0)
        else:
            key_fn = key

        new_data = sorted(self._data, key=key_fn, reverse=reverse)
        return NodeFrame(multinet=self._multinet, data=new_data)

    def head(self, n: int = 5) -> NodeFrame:
        """Keep only the first n nodes in the current selection.

        Corresponds to dplyr::head.

        Args:
            n: Number of nodes to keep (default: 5)

        Returns:
            A new NodeFrame with at most n nodes

        Example:
            >>> frame.head(10)
        """
        new_data = self._data[:n]
        return NodeFrame(multinet=self._multinet, data=new_data)

    def tail(self, n: int = 5) -> NodeFrame:
        """Keep only the last n nodes in the current selection.

        Corresponds to dplyr::tail.

        Args:
            n: Number of nodes to keep from the end (default: 5)

        Returns:
            A new NodeFrame with at most n nodes from the end

        Example:
            >>> frame.tail(10)
        """
        new_data = self._data[-n:] if n > 0 else []
        return NodeFrame(multinet=self._multinet, data=new_data)

    def sample(self, n: int = 5, seed: int | None = None) -> NodeFrame:
        """Randomly sample n nodes from the current selection.

        Args:
            n: Number of nodes to sample (default: 5)
            seed: Optional random seed for reproducibility

        Returns:
            A new NodeFrame with n randomly sampled nodes

        Example:
            >>> frame.sample(10, seed=42)
        """
        import random
        rng = random.Random(seed)
        if n >= len(self._data):
            new_data = list(self._data)
        else:
            new_data = rng.sample(self._data, n)
        return NodeFrame(multinet=self._multinet, data=new_data)

    def distinct(self, *fields: str) -> NodeFrame:
        """Keep only distinct/unique rows based on specified fields.

        If no fields are specified, uses all non-internal fields for uniqueness.

        Args:
            *fields: Field names to check for uniqueness

        Returns:
            A new NodeFrame with duplicates removed

        Example:
            >>> frame.distinct("id")
            >>> frame.distinct("layer", "degree")
        """
        if not fields:
            # Use all non-internal fields
            fields = tuple(
                k for k in (self._data[0].keys() if self._data else [])
                if not k.startswith("_")
            )

        seen: set[tuple[Any, ...]] = set()
        new_data = []
        for item in self._data:
            key = tuple(item.get(f) for f in fields)
            if key not in seen:
                seen.add(key)
                new_data.append(item)
        return NodeFrame(multinet=self._multinet, data=new_data)

    def count(self) -> int:
        """Return the count of nodes in the current selection.

        This is a terminal operation that returns an integer, not a NodeFrame.

        Returns:
            Number of nodes in the selection

        Example:
            >>> n = frame.filter(lambda n: n["degree"] > 5).count()
        """
        return len(self._data)

    def rename(self, **renames: str) -> NodeFrame:
        """Rename fields in the node dicts.

        Args:
            **renames: Mapping of old_name=new_name

        Returns:
            A new NodeFrame with renamed fields

        Example:
            >>> frame.rename(degree="node_degree", id="node_id")
        """
        new_data = []
        for item in self._data:
            new_item = {}
            for key, value in item.items():
                new_key = renames.get(key, key)
                new_item[new_key] = value
            new_data.append(new_item)
        return NodeFrame(multinet=self._multinet, data=new_data)

    def drop(self, *fields: str) -> NodeFrame:
        """Drop specified fields from node dicts.

        Inverse of select - keeps all fields except those specified.

        Args:
            *fields: Field names to drop

        Returns:
            A new NodeFrame without the specified fields

        Example:
            >>> frame.drop("_node_tuple", "_internal_id")
        """
        fields_set = set(fields)
        new_data = []
        for item in self._data:
            new_item = {k: v for k, v in item.items() if k not in fields_set}
            new_data.append(new_item)
        return NodeFrame(multinet=self._multinet, data=new_data)

    def where(self, predicate: Callable[[dict[str, Any]], bool]) -> NodeFrame:
        """Filter nodes using a predicate function (alias for filter).

        SQL-style alias for filter method.

        Args:
            predicate: A callable that takes a node dict and returns True to keep it

        Returns:
            A new NodeFrame with only the nodes where predicate(...) is True

        Example:
            >>> frame.where(lambda n: n["degree"] > 10)
        """
        return self.filter(predicate)

    def order_by(
        self,
        key: str | Callable[[dict[str, Any]], Any],
        descending: bool = False,
    ) -> NodeFrame:
        """Sort nodes by an attribute or key function (alias for arrange).

        SQL-style alias for arrange method with descending parameter.

        Args:
            key: If a string, sort by that attribute. If callable, use as key function.
            descending: If True, sort in descending order (default: False)

        Returns:
            A new NodeFrame with sorted nodes

        Example:
            >>> frame.order_by("degree", descending=True)
        """
        return self.arrange(key, reverse=descending)

    def take(self, n: int = 5) -> NodeFrame:
        """Keep only the first n nodes (alias for head).

        SQL-style alias for head method.

        Args:
            n: Number of nodes to keep (default: 5)

        Returns:
            A new NodeFrame with at most n nodes

        Example:
            >>> frame.take(10)
        """
        return self.head(n)

    def slice(self, start: int, end: int | None = None) -> NodeFrame:
        """Slice the data from start to end index.

        Args:
            start: Starting index (0-based)
            end: Ending index (exclusive). If None, slices to end.

        Returns:
            A new NodeFrame with the sliced data

        Example:
            >>> frame.slice(5, 15)  # rows 5-14
            >>> frame.slice(10)     # rows 10 to end
        """
        new_data = self._data[start:end]
        return NodeFrame(multinet=self._multinet, data=new_data)

    def first(self) -> dict[str, Any] | None:
        """Return the first node dict or None if empty.

        Terminal operation that returns a single item.

        Returns:
            The first node dict or None

        Example:
            >>> node = frame.filter(lambda n: n["layer"] == "ppi").first()
        """
        return self._data[0] if self._data else None

    def last(self) -> dict[str, Any] | None:
        """Return the last node dict or None if empty.

        Terminal operation that returns a single item.

        Returns:
            The last node dict or None

        Example:
            >>> node = frame.arrange("degree", reverse=True).last()
        """
        return self._data[-1] if self._data else None

    def collect(self) -> list[dict[str, Any]]:
        """Return all node dicts as a list.

        Terminal operation that returns the underlying data.

        Returns:
            List of node dictionaries

        Example:
            >>> nodes = frame.filter(lambda n: n["degree"] > 5).collect()
        """
        return list(self._data)

    def pluck(self, field: str) -> list[Any]:
        """Extract values for a single field as a list.

        Args:
            field: Field name to extract

        Returns:
            List of values for the specified field

        Example:
            >>> degrees = frame.pluck("degree")
            >>> ids = frame.filter(lambda n: n["layer"] == "ppi").pluck("id")
        """
        return [item.get(field) for item in self._data]

    def group_by(self, *fields: str) -> GroupedNodeFrame:
        """Group nodes by one or more fields.

        Corresponds to dplyr::group_by.

        Args:
            *fields: Field names to group by

        Returns:
            A GroupedNodeFrame for summarise operations

        Example:
            >>> frame.group_by("layer").summarise(avg_degree=("degree", np.mean))
        """
        return GroupedNodeFrame(parent=self, group_fields=tuple(fields))

    def to_pandas(self) -> Any:
        """Convert the current selection to a pandas DataFrame.

        Returns:
            pandas.DataFrame with the current node data

        Raises:
            ImportError: If pandas is not available

        Example:
            >>> df = frame.to_pandas()
        """
        if not PANDAS_AVAILABLE:
            raise ImportError(
                "pandas is required for to_pandas(). "
                "Install it with: pip install pandas"
            )

        # Remove internal fields before converting to DataFrame
        clean_data = []
        for item in self._data:
            clean_item = {
                k: v for k, v in item.items()
                if not k.startswith("_")
            }
            clean_data.append(clean_item)

        return pd.DataFrame(clean_data)

    def to_subgraph(self) -> Any:
        """Build a py3plex subgraph containing only the selected nodes.

        Returns a new multi_layer_network with the selected nodes and all edges
        between them. Uses py3plex's subnetwork method if available, otherwise
        constructs the subgraph by copying nodes and edges.

        Returns:
            A new py3plex multi_layer_network containing only selected nodes

        Example:
            >>> subgraph = frame.filter(lambda n: n["degree"] > 5).to_subgraph()
        """
        from py3plex.core.multinet import multi_layer_network

        if self._multinet is None:
            return multi_layer_network(directed=False)

        # Get the node tuples to keep
        node_tuples = [item.get("_node_tuple") for item in self._data if "_node_tuple" in item]

        if not node_tuples:
            return multi_layer_network(
                directed=self._multinet.directed,
                network_type=self._multinet.network_type,
            )

        # Use py3plex's subnetwork method if available
        if hasattr(self._multinet, 'subnetwork'):
            return self._multinet.subnetwork(node_tuples, subset_by='node_layer_names')

        # Fallback: Build a new network with selected nodes
        new_net = multi_layer_network(
            directed=self._multinet.directed,
            network_type=self._multinet.network_type,
        )

        # Add selected nodes
        for item in self._data:
            node_id = item.get("id")
            layer = item.get("layer", "default")
            new_net.add_nodes([{"source": node_id, "type": layer}])

        # Add edges between selected nodes
        node_tuple_set = set(node_tuples)
        for edge in self._multinet.get_edges(data=True):
            if len(edge) >= 2:
                source_tuple = edge[0]
                target_tuple = edge[1]
                if source_tuple in node_tuple_set and target_tuple in node_tuple_set:
                    edge_data = edge[2] if len(edge) > 2 else {}
                    if isinstance(source_tuple, tuple) and isinstance(target_tuple, tuple):
                        new_net.add_edges([{
                            "source": source_tuple[0],
                            "target": target_tuple[0],
                            "source_type": source_tuple[1] if len(source_tuple) > 1 else "default",
                            "target_type": target_tuple[1] if len(target_tuple) > 1 else "default",
                            **{k: v for k, v in edge_data.items() if k not in ["source", "target", "source_type", "target_type"]},
                        }])

        return new_net

    def __len__(self) -> int:
        """Return the number of nodes in the current selection."""
        return len(self._data)

    def __iter__(self) -> Iterable[dict[str, Any]]:
        """Iterate over node dicts in the current selection."""
        return iter(self._data)

    def __repr__(self) -> str:
        """Return a string representation of the NodeFrame."""
        return f"NodeFrame(n={len(self._data)})"


# ═══════════════════════════════════════════════════════════════════════════════
# GroupedEdgeFrame for edge group_by + summarise operations
# ═══════════════════════════════════════════════════════════════════════════════


@dataclass
class GroupedEdgeFrame:
    """A grouped view of edges for aggregation operations.

    Similar to GroupedNodeFrame but for edges.

    Attributes:
        parent: The parent EdgeFrame from which this was created
        group_fields: Tuple of field names to group by
    """

    parent: EdgeFrame
    group_fields: tuple[str, ...]

    def summarise(
        self, **aggregations: tuple[str, Callable[[list[Any]], Any]]
    ) -> EdgeFrame:
        """Compute aggregations for each group.

        Args:
            **aggregations: Named aggregations as tuples of (field_name, agg_function)

        Returns:
            A new EdgeFrame whose "edges" are group summaries
        """
        # Group the data
        groups: dict[tuple[Any, ...], list[dict[str, Any]]] = {}
        for item in self.parent._data:
            key = tuple(item.get(f) for f in self.group_fields)
            if key not in groups:
                groups[key] = []
            groups[key].append(item)

        # Compute aggregations for each group
        summaries: list[dict[str, Any]] = []
        for group_key, items in groups.items():
            summary: dict[str, Any] = {}

            # Add group key values
            for i, field_name in enumerate(self.group_fields):
                summary[field_name] = group_key[i]

            # Compute each aggregation
            for agg_name, (agg_field, agg_func) in aggregations.items():
                values = [item.get(agg_field) for item in items if agg_field in item]
                if values:
                    try:
                        summary[agg_name] = agg_func(values)
                    except Exception:
                        summary[agg_name] = None
                else:
                    summary[agg_name] = None

            summaries.append(summary)

        return EdgeFrame(
            multinet=self.parent._multinet,
            data=summaries,
        )

    summarize = summarise


# ═══════════════════════════════════════════════════════════════════════════════
# EdgeFrame: Chainable view over a collection of edges
# ═══════════════════════════════════════════════════════════════════════════════


@dataclass
class EdgeFrame:
    """A chainable view over a collection of edges.

    This class wraps a reference to the underlying py3plex graph object
    and a current selection of edges (as a list of dicts). All verbs
    return a new EdgeFrame, enabling method chaining.

    Attributes:
        multinet: Reference to the underlying py3plex multi_layer_network
        data: Current selection of edges as a list of dicts

    Example:
        >>> df_edges = (
        ...     edges(multinet, layers=["ppi", "coexpr"])
        ...     .filter(lambda e: e.get("weight", 0) > 0.8)
        ...     .head(100)
        ...     .to_pandas()
        ... )
    """

    multinet: Any
    data: list[dict[str, Any]] = field(default_factory=list)

    # Create private property aliases for internal use
    @property
    def _multinet(self) -> Any:
        return self.multinet

    @property
    def _data(self) -> list[dict[str, Any]]:
        return self.data

    def filter(self, predicate: Callable[[dict[str, Any]], bool]) -> EdgeFrame:
        """Filter edges using a predicate function.

        Corresponds to dplyr::filter.

        Args:
            predicate: A callable that takes an edge dict and returns True to keep it

        Returns:
            A new EdgeFrame with only the edges where predicate(...) is True

        Example:
            >>> frame.filter(lambda e: e.get("weight", 0) > 0.5)
        """
        new_data = [item for item in self._data if predicate(item)]
        return EdgeFrame(multinet=self._multinet, data=new_data)

    def filter_expr(self, expr: str) -> EdgeFrame:
        """Filter edges using an expression string.

        Args:
            expr: Expression string like "weight > 0.5 and source_layer == 'ppi'"

        Returns:
            A new EdgeFrame with only the edges matching the expression

        Example:
            >>> frame.filter_expr("weight > 0.5")
        """
        new_data = []
        for item in self._data:
            try:
                if _safe_eval_expr(expr, item):
                    new_data.append(item)
            except (ValueError, KeyError):
                pass
        return EdgeFrame(multinet=self._multinet, data=new_data)

    def select(self, *fields: str) -> EdgeFrame:
        """Keep only the specified attributes in edge dicts.

        Corresponds to dplyr::select.

        Args:
            *fields: Names of attributes to keep

        Returns:
            A new EdgeFrame with only the specified fields in each dict.
            If no fields are passed, behaves as a no-op.

        Example:
            >>> frame.select("source", "target", "weight")
        """
        if not fields:
            return EdgeFrame(multinet=self._multinet, data=copy.deepcopy(self._data))

        new_data = []
        for item in self._data:
            new_item = {k: item[k] for k in fields if k in item}
            new_data.append(new_item)
        return EdgeFrame(multinet=self._multinet, data=new_data)

    def mutate(
        self, **new_fields: Callable[[dict[str, Any]], Any]
    ) -> EdgeFrame:
        """Compute new attributes from existing dict values.

        Corresponds to dplyr::mutate.

        Args:
            **new_fields: Named callables to compute new field values

        Returns:
            A new EdgeFrame with the new/overwritten fields

        Example:
            >>> frame.mutate(normalized_weight=lambda e: e.get("weight", 1) / max_weight)
        """
        new_data = []
        for item in self._data:
            new_item = copy.copy(item)
            for field_name, compute_fn in new_fields.items():
                try:
                    new_item[field_name] = compute_fn(new_item)
                except Exception:
                    new_item[field_name] = None
            new_data.append(new_item)
        return EdgeFrame(multinet=self._multinet, data=new_data)

    def arrange(
        self,
        key: str | Callable[[dict[str, Any]], Any],
        reverse: bool = False,
    ) -> EdgeFrame:
        """Sort edges by an attribute or key function.

        Corresponds to dplyr::arrange.

        Args:
            key: If a string, sort by that attribute. If callable, use as key function.
            reverse: If True, sort in descending order

        Returns:
            A new EdgeFrame with sorted edges

        Example:
            >>> frame.arrange("weight", reverse=True)
        """
        if isinstance(key, str):
            def key_fn(item):
                return item.get(key, 0)
        else:
            key_fn = key

        new_data = sorted(self._data, key=key_fn, reverse=reverse)
        return EdgeFrame(multinet=self._multinet, data=new_data)

    def head(self, n: int = 5) -> EdgeFrame:
        """Keep only the first n edges in the current selection.

        Corresponds to dplyr::head.

        Args:
            n: Number of edges to keep (default: 5)

        Returns:
            A new EdgeFrame with at most n edges

        Example:
            >>> frame.head(100)
        """
        new_data = self._data[:n]
        return EdgeFrame(multinet=self._multinet, data=new_data)

    def tail(self, n: int = 5) -> EdgeFrame:
        """Keep only the last n edges in the current selection.

        Corresponds to dplyr::tail.

        Args:
            n: Number of edges to keep from the end (default: 5)

        Returns:
            A new EdgeFrame with at most n edges from the end

        Example:
            >>> frame.tail(10)
        """
        new_data = self._data[-n:] if n > 0 else []
        return EdgeFrame(multinet=self._multinet, data=new_data)

    def sample(self, n: int = 5, seed: int | None = None) -> EdgeFrame:
        """Randomly sample n edges from the current selection.

        Args:
            n: Number of edges to sample (default: 5)
            seed: Optional random seed for reproducibility

        Returns:
            A new EdgeFrame with n randomly sampled edges

        Example:
            >>> frame.sample(10, seed=42)
        """
        import random
        rng = random.Random(seed)
        if n >= len(self._data):
            new_data = list(self._data)
        else:
            new_data = rng.sample(self._data, n)
        return EdgeFrame(multinet=self._multinet, data=new_data)

    def distinct(self, *fields: str) -> EdgeFrame:
        """Keep only distinct/unique rows based on specified fields.

        If no fields are specified, uses all non-internal fields for uniqueness.

        Args:
            *fields: Field names to check for uniqueness

        Returns:
            A new EdgeFrame with duplicates removed

        Example:
            >>> frame.distinct("source", "target")
        """
        if not fields:
            fields = tuple(
                k for k in (self._data[0].keys() if self._data else [])
                if not k.startswith("_")
            )

        seen: set[tuple[Any, ...]] = set()
        new_data = []
        for item in self._data:
            key = tuple(item.get(f) for f in fields)
            if key not in seen:
                seen.add(key)
                new_data.append(item)
        return EdgeFrame(multinet=self._multinet, data=new_data)

    def count(self) -> int:
        """Return the count of edges in the current selection.

        Terminal operation that returns an integer, not an EdgeFrame.

        Returns:
            Number of edges in the selection

        Example:
            >>> n = frame.filter(lambda e: e.get("weight", 0) > 0.5).count()
        """
        return len(self._data)

    def rename(self, **renames: str) -> EdgeFrame:
        """Rename fields in the edge dicts.

        Args:
            **renames: Mapping of old_name=new_name

        Returns:
            A new EdgeFrame with renamed fields

        Example:
            >>> frame.rename(weight="edge_weight", source="from_node")
        """
        new_data = []
        for item in self._data:
            new_item = {}
            for key, value in item.items():
                new_key = renames.get(key, key)
                new_item[new_key] = value
            new_data.append(new_item)
        return EdgeFrame(multinet=self._multinet, data=new_data)

    def drop(self, *fields: str) -> EdgeFrame:
        """Drop specified fields from edge dicts.

        Inverse of select - keeps all fields except those specified.

        Args:
            *fields: Field names to drop

        Returns:
            A new EdgeFrame without the specified fields

        Example:
            >>> frame.drop("_source_tuple", "_target_tuple")
        """
        fields_set = set(fields)
        new_data = []
        for item in self._data:
            new_item = {k: v for k, v in item.items() if k not in fields_set}
            new_data.append(new_item)
        return EdgeFrame(multinet=self._multinet, data=new_data)

    def where(self, predicate: Callable[[dict[str, Any]], bool]) -> EdgeFrame:
        """Filter edges using a predicate function (alias for filter).

        SQL-style alias for filter method.

        Args:
            predicate: A callable that takes an edge dict and returns True to keep it

        Returns:
            A new EdgeFrame with only the edges where predicate(...) is True

        Example:
            >>> frame.where(lambda e: e.get("weight", 0) > 0.5)
        """
        return self.filter(predicate)

    def order_by(
        self,
        key: str | Callable[[dict[str, Any]], Any],
        descending: bool = False,
    ) -> EdgeFrame:
        """Sort edges by an attribute or key function (alias for arrange).

        SQL-style alias for arrange method.

        Args:
            key: If a string, sort by that attribute. If callable, use as key function.
            descending: If True, sort in descending order (default: False)

        Returns:
            A new EdgeFrame with sorted edges

        Example:
            >>> frame.order_by("weight", descending=True)
        """
        return self.arrange(key, reverse=descending)

    def take(self, n: int = 5) -> EdgeFrame:
        """Keep only the first n edges (alias for head).

        SQL-style alias for head method.

        Args:
            n: Number of edges to keep (default: 5)

        Returns:
            A new EdgeFrame with at most n edges

        Example:
            >>> frame.take(10)
        """
        return self.head(n)

    def slice(self, start: int, end: int | None = None) -> EdgeFrame:
        """Slice the data from start to end index.

        Args:
            start: Starting index (0-based)
            end: Ending index (exclusive). If None, slices to end.

        Returns:
            A new EdgeFrame with the sliced data

        Example:
            >>> frame.slice(5, 15)  # rows 5-14
        """
        new_data = self._data[start:end]
        return EdgeFrame(multinet=self._multinet, data=new_data)

    def first(self) -> dict[str, Any] | None:
        """Return the first edge dict or None if empty.

        Terminal operation that returns a single item.

        Returns:
            The first edge dict or None

        Example:
            >>> edge = frame.filter(lambda e: e["source_layer"] == "ppi").first()
        """
        return self._data[0] if self._data else None

    def last(self) -> dict[str, Any] | None:
        """Return the last edge dict or None if empty.

        Terminal operation that returns a single item.

        Returns:
            The last edge dict or None

        Example:
            >>> edge = frame.arrange("weight", reverse=True).last()
        """
        return self._data[-1] if self._data else None

    def collect(self) -> list[dict[str, Any]]:
        """Return all edge dicts as a list.

        Terminal operation that returns the underlying data.

        Returns:
            List of edge dictionaries

        Example:
            >>> edges_list = frame.filter(lambda e: e.get("weight", 0) > 0.5).collect()
        """
        return list(self._data)

    def pluck(self, field: str) -> list[Any]:
        """Extract values for a single field as a list.

        Args:
            field: Field name to extract

        Returns:
            List of values for the specified field

        Example:
            >>> weights = frame.pluck("weight")
        """
        return [item.get(field) for item in self._data]

    def group_by(self, *fields: str) -> GroupedEdgeFrame:
        """Group edges by one or more fields.

        Corresponds to dplyr::group_by.

        Args:
            *fields: Field names to group by

        Returns:
            A GroupedEdgeFrame for summarise operations

        Example:
            >>> frame.group_by("source_layer").summarise(n=("source", len))
        """
        return GroupedEdgeFrame(parent=self, group_fields=tuple(fields))

    def to_pandas(self) -> Any:
        """Convert the current selection to a pandas DataFrame.

        Returns:
            pandas.DataFrame with the current edge data

        Raises:
            ImportError: If pandas is not available

        Example:
            >>> df = frame.to_pandas()
        """
        if not PANDAS_AVAILABLE:
            raise ImportError(
                "pandas is required for to_pandas(). "
                "Install it with: pip install pandas"
            )

        # Remove internal fields before converting to DataFrame
        clean_data = []
        for item in self._data:
            clean_item = {
                k: v for k, v in item.items()
                if not k.startswith("_")
            }
            clean_data.append(clean_item)

        return pd.DataFrame(clean_data)

    def __len__(self) -> int:
        """Return the number of edges in the current selection."""
        return len(self._data)

    def __iter__(self) -> Iterable[dict[str, Any]]:
        """Iterate over edge dicts in the current selection."""
        return iter(self._data)

    def __repr__(self) -> str:
        """Return a string representation of the EdgeFrame."""
        return f"EdgeFrame(n={len(self._data)})"


# ═══════════════════════════════════════════════════════════════════════════════
# Top-level helper functions
# ═══════════════════════════════════════════════════════════════════════════════


def nodes(multinet: Any, layers: list[str] | None = None) -> NodeFrame:
    """Create a NodeFrame from a py3plex multi_layer_network.

    This is the main entry point for working with nodes in a chainable way.

    Args:
        multinet: py3plex multi_layer_network object
        layers: Optional list of layers to restrict to

    Returns:
        A NodeFrame wrapping the network's nodes

    Example:
        >>> from py3plex.graph_ops import nodes
        >>> df = (
        ...     nodes(multinet, layers=["ppi"])
        ...     .filter(lambda n: n["degree"] > 10)
        ...     .mutate(k=lambda n: n["degree"] / (n["weight"] + 1))
        ...     .to_pandas()
        ... )
    """
    data = _get_node_dicts(multinet, layers)
    return NodeFrame(multinet=multinet, data=data)


def edges(multinet: Any, layers: list[str] | None = None) -> EdgeFrame:
    """Create an EdgeFrame from a py3plex multi_layer_network.

    This is the main entry point for working with edges in a chainable way.

    Args:
        multinet: py3plex multi_layer_network object
        layers: Optional list of layers to restrict to (by source or target layer)

    Returns:
        An EdgeFrame wrapping the network's edges

    Example:
        >>> from py3plex.graph_ops import edges
        >>> df_edges = (
        ...     edges(multinet, layers=["ppi", "coexpr"])
        ...     .filter(lambda e: e.get("weight", 0) > 0.8)
        ...     .head(100)
        ...     .to_pandas()
        ... )
    """
    data = _get_edge_dicts(multinet, layers)
    return EdgeFrame(multinet=multinet, data=data)


# ═══════════════════════════════════════════════════════════════════════════════
# Module exports
# ═══════════════════════════════════════════════════════════════════════════════


__all__ = [
    "nodes",
    "edges",
    "NodeFrame",
    "EdgeFrame",
    "GroupedNodeFrame",
    "GroupedEdgeFrame",
]
