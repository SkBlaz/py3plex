"""Type system for Graph Programs in py3plex DSL v2.

This module implements a lightweight static type system for DSL intermediate
representation (IR) that enables type checking, type inference, and UQ-aware
type unification for graph program analysis.

The type system is designed to be:
- Simple: No Hindley-Milner complexity, just practical type checking
- Serializable: All types can be cached and reused
- UQ-aware: Native support for Distribution[T] types
- Actionable: Error messages guide users to fixes

Example:
    >>> from py3plex.dsl import Q, L
    >>> from py3plex.dsl.program.types import type_check, infer_type
    >>> 
    >>> # Build AST
    >>> query_ast = Q.nodes().from_layers(L["social"]).compute("degree").to_ast()
    >>> 
    >>> # Type check
    >>> type_check(query_ast)  # Returns True or raises TypeError
    >>> 
    >>> # Infer types
    >>> result_type = infer_type(query_ast)
    >>> print(result_type)  # TableType(columns={'node': ScalarType, 'layer': ScalarType, ...})
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Union, Tuple
from enum import Enum
import json

from ..ast import (
    Query,
    SelectStmt,
    Target,
    ExportTarget,
    ComputeItem,
    ConditionExpr,
    ConditionAtom,
    Comparison,
    FunctionCall,
    SpecialPredicate,
    LayerExpr,
    OrderItem,
    UQConfig,
    JoinNode,
)


# ============================================================================
# Base Type System
# ============================================================================


@dataclass(frozen=True)
class Type:
    """Base class for all types in the DSL type system.
    
    All types are immutable and support equality checking and serialization.
    """
    
    def __str__(self) -> str:
        """String representation of the type."""
        return self.__class__.__name__
    
    def __repr__(self) -> str:
        """Detailed representation of the type."""
        return self.__str__()
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize type to dictionary for caching."""
        return {"type": self.__class__.__name__}
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Type:
        """Deserialize type from dictionary."""
        type_name = data["type"]
        # Map type names to classes
        type_map = {
            "GraphType": GraphType,
            "NodeSetType": NodeSetType,
            "EdgeSetType": EdgeSetType,
            "PartitionType": PartitionType,
            "TableType": TableType,
            "ScalarType": ScalarType,
            "TimeSeriesType": TimeSeriesType,
            "BoolType": BoolType,
            "StringType": StringType,
            "NumericType": NumericType,
        }
        
        if type_name == "DistributionType":
            inner = cls.from_dict(data["inner"])
            return DistributionType(inner)
        
        type_cls = type_map.get(type_name)
        if type_cls is None:
            raise ValueError(f"Unknown type: {type_name}")
        
        # Handle types with metadata
        if type_name == "TableType":
            columns_data = data.get("columns", {})
            columns = {col_name: cls.from_dict(col_type_data) 
                      for col_name, col_type_data in columns_data.items()}
            return TableType(columns=columns)
        elif type_name == "NodeSetType":
            layers = data.get("layers")
            return NodeSetType(
                layers=frozenset(layers) if layers else None,
                has_metrics=data.get("has_metrics", False)
            )
        elif type_name == "EdgeSetType":
            layers = data.get("layers")
            return EdgeSetType(
                layers=frozenset(layers) if layers else None,
                has_metrics=data.get("has_metrics", False)
            )
        elif type_name == "PartitionType":
            return PartitionType(partition_name=data.get("partition_name"))
        elif type_name == "TimeSeriesType":
            element_type_data = data.get("element_type")
            element_type = cls.from_dict(element_type_data) if element_type_data else ScalarType()
            return TimeSeriesType(element_type=element_type)
        
        return type_cls()


@dataclass(frozen=True)
class GraphType(Type):
    """Type representing the full multilayer network.
    
    This is the top-level type representing the entire graph structure.
    
    Example:
        >>> GraphType()
    """
    
    def __str__(self) -> str:
        return "Graph"


@dataclass(frozen=True)
class NodeSetType(Type):
    """Type representing a set of nodes (with optional layer context).
    
    Attributes:
        layers: Optional set of layer names if layer context is known
        has_metrics: Whether nodes have computed metrics attached
    
    Example:
        >>> NodeSetType()
        >>> NodeSetType(layers=frozenset({"social", "work"}))
        >>> NodeSetType(layers=frozenset({"social"}), has_metrics=True)
    """
    
    layers: Optional[frozenset] = None
    has_metrics: bool = False
    
    def __str__(self) -> str:
        if self.layers:
            layer_str = ", ".join(sorted(self.layers))
            return f"NodeSet[{layer_str}]"
        return "NodeSet"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "NodeSetType",
            "layers": list(self.layers) if self.layers else None,
            "has_metrics": self.has_metrics,
        }


@dataclass(frozen=True)
class EdgeSetType(Type):
    """Type representing a set of edges (with optional layer context).
    
    Attributes:
        layers: Optional set of layer names if layer context is known
        has_metrics: Whether edges have computed metrics attached
    
    Example:
        >>> EdgeSetType()
        >>> EdgeSetType(layers=frozenset({"social", "work"}))
        >>> EdgeSetType(has_metrics=True)
    """
    
    layers: Optional[frozenset] = None
    has_metrics: bool = False
    
    def __str__(self) -> str:
        if self.layers:
            layer_str = ", ".join(sorted(self.layers))
            return f"EdgeSet[{layer_str}]"
        return "EdgeSet"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "EdgeSetType",
            "layers": list(self.layers) if self.layers else None,
            "has_metrics": self.has_metrics,
        }


@dataclass(frozen=True)
class PartitionType(Type):
    """Type representing a community partition.
    
    A partition assigns nodes to communities (clusters).
    
    Attributes:
        partition_name: Optional name of the partition
    
    Example:
        >>> PartitionType()
        >>> PartitionType(partition_name="louvain")
    """
    
    partition_name: Optional[str] = None
    
    def __str__(self) -> str:
        if self.partition_name:
            return f"Partition[{self.partition_name}]"
        return "Partition"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "PartitionType",
            "partition_name": self.partition_name,
        }


@dataclass(frozen=True)
class TableType(Type):
    """Type representing tabular data (like pandas DataFrame).
    
    Attributes:
        columns: Dictionary mapping column names to their types
    
    Example:
        >>> TableType(columns={"node": StringType(), "degree": NumericType()})
        >>> TableType()  # Unknown schema
    """
    
    columns: Dict[str, Type] = field(default_factory=dict)
    
    def __str__(self) -> str:
        if self.columns:
            col_str = ", ".join(f"{k}: {v}" for k, v in sorted(self.columns.items()))
            return f"Table[{col_str}]"
        return "Table"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "TableType",
            "columns": {k: v.to_dict() for k, v in self.columns.items()},
        }
    
    def has_column(self, name: str) -> bool:
        """Check if table has a column."""
        return name in self.columns
    
    def get_column_type(self, name: str) -> Optional[Type]:
        """Get type of a column."""
        return self.columns.get(name)


@dataclass(frozen=True)
class DistributionType(Type):
    """Type representing uncertainty-wrapped values (UQ-aware).
    
    This is a parametric type: Distribution[T] represents uncertain values of type T.
    
    Attributes:
        inner: The inner type that is wrapped with uncertainty
    
    Example:
        >>> DistributionType(NumericType())
        >>> DistributionType(TableType(columns={"degree": NumericType()}))
    """
    
    inner: Type
    
    def __str__(self) -> str:
        return f"Distribution[{self.inner}]"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "DistributionType",
            "inner": self.inner.to_dict(),
        }


@dataclass(frozen=True)
class ScalarType(Type):
    """Type representing a single value (numeric or string).
    
    This is a general scalar type. Use NumericType or StringType for more specific types.
    
    Example:
        >>> ScalarType()
    """
    
    def __str__(self) -> str:
        return "Scalar"


@dataclass(frozen=True)
class NumericType(Type):
    """Type representing numeric values (int or float).
    
    Example:
        >>> NumericType()
    """
    
    def __str__(self) -> str:
        return "Numeric"


@dataclass(frozen=True)
class StringType(Type):
    """Type representing string values.
    
    Example:
        >>> StringType()
    """
    
    def __str__(self) -> str:
        return "String"


@dataclass(frozen=True)
class BoolType(Type):
    """Type representing boolean values.
    
    Example:
        >>> BoolType()
    """
    
    def __str__(self) -> str:
        return "Bool"


@dataclass(frozen=True)
class TimeSeriesType(Type):
    """Type representing a temporal sequence of values.
    
    Used for window queries and temporal analysis.
    
    Attributes:
        element_type: Type of elements in the time series
    
    Example:
        >>> TimeSeriesType(element_type=TableType())
        >>> TimeSeriesType(element_type=NumericType())
    """
    
    element_type: Type = field(default_factory=lambda: ScalarType())
    
    def __str__(self) -> str:
        return f"TimeSeries[{self.element_type}]"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "TimeSeriesType",
            "element_type": self.element_type.to_dict(),
        }


# ============================================================================
# Operator Type Signatures
# ============================================================================


class OperatorSignature:
    """Type signature for DSL operators.
    
    Maps operator names to (input_types, output_type) pairs.
    """
    
    def __init__(
        self,
        name: str,
        input_types: List[Type],
        output_type: Type,
        description: str = "",
    ):
        self.name = name
        self.input_types = input_types
        self.output_type = output_type
        self.description = description
    
    def check_inputs(self, actual_types: List[Type]) -> Tuple[bool, Optional[str]]:
        """Check if actual input types match signature.
        
        Returns:
            (is_valid, error_message)
        """
        if len(actual_types) != len(self.input_types):
            return False, f"Expected {len(self.input_types)} inputs, got {len(actual_types)}"
        
        for i, (expected, actual) in enumerate(zip(self.input_types, actual_types)):
            # Check type compatibility
            if not self._types_compatible(expected, actual):
                return False, f"Input {i}: expected {expected}, got {actual}"
        
        return True, None
    
    def _types_compatible(self, expected: Type, actual: Type) -> bool:
        """Check if actual type is compatible with expected type."""
        # Exact match
        if expected == actual:
            return True
        
        # Handle Distribution types
        if isinstance(expected, DistributionType) and isinstance(actual, DistributionType):
            return self._types_compatible(expected.inner, actual.inner)
        
        # Numeric types are compatible with Scalar
        if isinstance(expected, ScalarType) and isinstance(actual, (NumericType, StringType)):
            return True
        
        # NodeSetType with/without layers
        if isinstance(expected, NodeSetType) and isinstance(actual, NodeSetType):
            # If expected has no layer constraint, accept any
            if expected.layers is None:
                return True
            # If actual has no layers specified, we can't verify
            if actual.layers is None:
                return True
            # Check layer compatibility
            return expected.layers.issubset(actual.layers) or actual.layers.issubset(expected.layers)
        
        # EdgeSetType with/without layers
        if isinstance(expected, EdgeSetType) and isinstance(actual, EdgeSetType):
            if expected.layers is None:
                return True
            if actual.layers is None:
                return True
            return expected.layers.issubset(actual.layers) or actual.layers.issubset(expected.layers)
        
        return False


# Define operator signatures for common DSL operations
OPERATOR_SIGNATURES: Dict[str, OperatorSignature] = {
    # Query constructors
    "nodes": OperatorSignature(
        name="nodes",
        input_types=[GraphType()],
        output_type=NodeSetType(),
        description="Select all nodes from the graph",
    ),
    "edges": OperatorSignature(
        name="edges",
        input_types=[GraphType()],
        output_type=EdgeSetType(),
        description="Select all edges from the graph",
    ),
    "communities": OperatorSignature(
        name="communities",
        input_types=[GraphType()],
        output_type=PartitionType(),
        description="Select communities from the graph",
    ),
    
    # Filtering operations
    "where": OperatorSignature(
        name="where",
        input_types=[NodeSetType()],  # Can also be EdgeSetType
        output_type=NodeSetType(),
        description="Filter nodes/edges by conditions",
    ),
    "from_layers": OperatorSignature(
        name="from_layers",
        input_types=[NodeSetType()],
        output_type=NodeSetType(),
        description="Filter to specific layers",
    ),
    
    # Computation operations
    "compute": OperatorSignature(
        name="compute",
        input_types=[NodeSetType()],
        output_type=NodeSetType(has_metrics=True),
        description="Compute metrics on nodes/edges",
    ),
    
    # Ordering and limiting
    "order_by": OperatorSignature(
        name="order_by",
        input_types=[NodeSetType(has_metrics=True)],
        output_type=NodeSetType(has_metrics=True),
        description="Order results by metric",
    ),
    "limit": OperatorSignature(
        name="limit",
        input_types=[NodeSetType()],
        output_type=NodeSetType(),
        description="Limit number of results",
    ),
    "top_k": OperatorSignature(
        name="top_k",
        input_types=[NodeSetType(has_metrics=True)],
        output_type=NodeSetType(has_metrics=True),
        description="Select top k results",
    ),
    
    # Grouping operations
    "per_layer": OperatorSignature(
        name="per_layer",
        input_types=[NodeSetType()],
        output_type=NodeSetType(),  # Grouped
        description="Group results by layer",
    ),
    "per_layer_pair": OperatorSignature(
        name="per_layer_pair",
        input_types=[EdgeSetType()],
        output_type=EdgeSetType(),
        description="Group edges by layer pair",
    ),
    
    # Export operations
    "to_pandas": OperatorSignature(
        name="to_pandas",
        input_types=[NodeSetType()],
        output_type=TableType(),
        description="Convert to pandas DataFrame",
    ),
    "to_networkx": OperatorSignature(
        name="to_networkx",
        input_types=[NodeSetType()],  # Can be NodeSetType or EdgeSetType
        output_type=GraphType(),
        description="Convert to NetworkX graph",
    ),
    
    # UQ operations
    "uq": OperatorSignature(
        name="uq",
        input_types=[NodeSetType()],
        output_type=DistributionType(NodeSetType()),
        description="Apply uncertainty quantification",
    ),
    
    # Join operations
    "join": OperatorSignature(
        name="join",
        input_types=[TableType(), TableType()],
        output_type=TableType(),
        description="Join two tables",
    ),
}


# ============================================================================
# Type Inference
# ============================================================================


def infer_type(ast_node: Union[Query, SelectStmt]) -> Type:
    """Infer the output type of an AST node.
    
    Args:
        ast_node: AST node to analyze
    
    Returns:
        Inferred output type
    
    Example:
        >>> from py3plex.dsl import Q
        >>> ast = Q.nodes().compute("degree").to_ast()
        >>> infer_type(ast)
        NodeSetType(has_metrics=True)
    """
    if isinstance(ast_node, Query):
        return infer_type(ast_node.select)
    
    if isinstance(ast_node, SelectStmt):
        return _infer_select_type(ast_node)
    
    if isinstance(ast_node, JoinNode):
        left_type = infer_type(ast_node.left)
        right_type = infer_type(ast_node.right)
        
        if isinstance(left_type, TableType) and isinstance(right_type, TableType):
            # Merge columns based on join type
            result_columns = left_type.columns.copy()
            for col, col_type in right_type.columns.items():
                if col not in ast_node.on:
                    result_columns[col] = col_type
            return TableType(columns=result_columns)
        
        return TableType()
    
    raise TypeError(f"Cannot infer type for {type(ast_node)}")


def _infer_select_type(stmt: SelectStmt) -> Type:
    """Infer type for a SELECT statement."""
    # Start with base type from target
    if stmt.target == Target.NODES:
        base_type = NodeSetType()
    elif stmt.target == Target.EDGES:
        base_type = EdgeSetType()
    elif stmt.target == Target.COMMUNITIES:
        base_type = PartitionType()
    else:
        raise TypeError(f"Unknown target: {stmt.target}")
    
    # Apply layer filtering if present
    if stmt.layer_expr or stmt.layer_set:
        layers = _extract_layer_names(stmt.layer_expr) if stmt.layer_expr else None
        if isinstance(base_type, NodeSetType):
            base_type = NodeSetType(layers=frozenset(layers) if layers else None)
        elif isinstance(base_type, EdgeSetType):
            base_type = EdgeSetType(layers=frozenset(layers) if layers else None)
    
    # Apply compute operations
    if stmt.compute:
        if isinstance(base_type, NodeSetType):
            base_type = NodeSetType(layers=base_type.layers, has_metrics=True)
        elif isinstance(base_type, EdgeSetType):
            base_type = EdgeSetType(layers=base_type.layers, has_metrics=True)
    
    # Apply UQ wrapper if present
    if stmt.uq_config and stmt.uq_config.method:
        base_type = DistributionType(base_type)
    
    # Apply export transformation if present
    if stmt.export == ExportTarget.PANDAS:
        return _to_table_type(base_type, stmt)
    elif stmt.export == ExportTarget.NETWORKX:
        return GraphType()
    
    # Window spec produces time series
    if stmt.window_spec:
        return TimeSeriesType(element_type=base_type)
    
    return base_type


def _to_table_type(source_type: Type, stmt: SelectStmt) -> TableType:
    """Convert a source type to TableType based on SELECT statement."""
    columns = {}
    
    # Add base columns based on source type
    is_nodeset = (isinstance(source_type, NodeSetType) or 
                  (isinstance(source_type, DistributionType) and isinstance(source_type.inner, NodeSetType)))
    is_edgeset = (isinstance(source_type, EdgeSetType) or 
                  (isinstance(source_type, DistributionType) and isinstance(source_type.inner, EdgeSetType)))
    
    if is_nodeset:
        columns["node"] = StringType()
        columns["layer"] = StringType()
    elif is_edgeset:
        columns["source"] = StringType()
        columns["target"] = StringType()
        columns["source_layer"] = StringType()
        columns["target_layer"] = StringType()
    elif isinstance(source_type, PartitionType):
        columns["node"] = StringType()
        columns["layer"] = StringType()
        columns["community"] = NumericType()
    
    # Add computed metrics
    for compute_item in stmt.compute:
        metric_name = compute_item.result_name
        # A metric is wrapped in DistributionType only if both conditions are true
        if _should_wrap_in_distribution(compute_item, stmt):
            columns[metric_name] = DistributionType(NumericType())
        else:
            columns[metric_name] = NumericType()
    
    return TableType(columns=columns)


def _should_wrap_in_distribution(compute_item: ComputeItem, stmt: SelectStmt) -> bool:
    """Check if a metric should be wrapped in DistributionType.
    
    A metric is wrapped if BOTH:
    1. The compute item has uncertainty=True
    2. There is a query-level UQ config with a method specified
    
    Args:
        compute_item: The compute item to check
        stmt: The SELECT statement containing UQ config
    
    Returns:
        True if the metric should be wrapped in DistributionType
    """
    has_uncertainty = compute_item.uncertainty
    has_uq_config = stmt.uq_config is not None and stmt.uq_config.method is not None
    return has_uncertainty and has_uq_config


def _extract_layer_names(layer_expr: Optional[LayerExpr]) -> Optional[List[str]]:
    """Extract layer names from a layer expression."""
    if layer_expr is None:
        return None
    return layer_expr.get_layer_names()


# ============================================================================
# Type Checking Constants
# ============================================================================


# Base attributes that are always available on nodes and edges
BASE_NODE_ATTRIBUTES = frozenset({"node", "layer", "degree"})
BASE_EDGE_ATTRIBUTES = frozenset({"source", "target", "source_layer", "target_layer"})

# Known numeric metric names (for type inference)
# NOTE: This is a default set. New metrics can be registered via plugins or
# custom operators. Type inference will still work for unregistered metrics
# by defaulting to ScalarType.
NUMERIC_METRIC_NAMES = frozenset({
    "degree", "betweenness_centrality", "closeness_centrality", 
    "pagerank", "clustering", "eigenvector_centrality",
    "katz_centrality", "harmonic_centrality", "load_centrality"
})


# ============================================================================
# Type Checking
# ============================================================================


class TypeCheckError(Exception):
    """Exception raised when type checking fails."""
    
    def __init__(self, message: str, node: Any = None):
        super().__init__(message)
        self.node = node


def type_check(ast_node: Union[Query, SelectStmt]) -> bool:
    """Type check an AST node.
    
    Args:
        ast_node: AST node to check
    
    Returns:
        True if type checking succeeds
    
    Raises:
        TypeCheckError: If type checking fails
    
    Example:
        >>> from py3plex.dsl import Q
        >>> ast = Q.nodes().compute("degree").order_by("degree").to_ast()
        >>> type_check(ast)
        True
    """
    if isinstance(ast_node, Query):
        return type_check(ast_node.select)
    
    if isinstance(ast_node, SelectStmt):
        return _type_check_select(ast_node)
    
    if isinstance(ast_node, JoinNode):
        return _type_check_join(ast_node)
    
    raise TypeCheckError(f"Cannot type check {type(ast_node)}", ast_node)


def _type_check_select(stmt: SelectStmt) -> bool:
    """Type check a SELECT statement."""
    # Infer current type
    current_type = infer_type(stmt)
    
    # Check that order_by references computed metrics
    if stmt.order_by:
        for order_item in stmt.order_by:
            if not _is_metric_computed(order_item.key, stmt):
                if stmt.autocompute:
                    # Autocompute will handle it
                    pass
                else:
                    raise TypeCheckError(
                        f"Metric '{order_item.key}' used in order_by but not computed. "
                        f"Add .compute('{order_item.key}') or enable autocompute.",
                        stmt
                    )
    
    # Check that where conditions reference valid attributes
    if stmt.where:
        _type_check_conditions(stmt.where, stmt)
    
    # Check UQ compatibility
    if stmt.uq_config and stmt.uq_config.method:
        if not stmt.compute:
            raise TypeCheckError(
                "UQ requires computed metrics. Add .compute() before .uq().",
                stmt
            )
    
    # Check that limit_per_group requires grouping
    if stmt.limit_per_group and not stmt.group_by:
        raise TypeCheckError(
            "limit_per_group requires group_by. Add .per_layer() or similar grouping.",
            stmt
        )
    
    # Check export compatibility
    if stmt.export == ExportTarget.NETWORKX:
        if stmt.target == Target.COMMUNITIES:
            raise TypeCheckError(
                "Cannot export communities directly to NetworkX. "
                "Use .to_pandas() instead.",
                stmt
            )
    
    return True


def _type_check_conditions(cond_expr: ConditionExpr, stmt: SelectStmt) -> bool:
    """Type check condition expressions."""
    for atom in cond_expr.atoms:
        if atom.comparison:
            comp = atom.comparison
            # Check that attribute exists or can be computed
            if not _is_attribute_available(comp.left, stmt):
                raise TypeCheckError(
                    f"Attribute '{comp.left}' not available. "
                    f"Add .compute('{comp.left}') or check spelling.",
                    stmt
                )
            
            # Check operator compatibility
            attr_type = _get_attribute_type(comp.left, stmt)
            if not _operator_supports_type(comp.op, attr_type):
                raise TypeCheckError(
                    f"Operator '{comp.op}' not supported for attribute '{comp.left}' "
                    f"of type {attr_type}.",
                    stmt
                )
    
    return True


def _type_check_join(join_node: JoinNode) -> bool:
    """Type check a join operation."""
    # Check both sides
    type_check(join_node.left)
    type_check(join_node.right)
    
    # Check that join keys exist
    left_type = infer_type(join_node.left)
    right_type = infer_type(join_node.right)
    
    if isinstance(left_type, TableType) and isinstance(right_type, TableType):
        for key in join_node.on:
            if not left_type.has_column(key):
                raise TypeCheckError(
                    f"Join key '{key}' not found in left table.",
                    join_node
                )
            if not right_type.has_column(key):
                raise TypeCheckError(
                    f"Join key '{key}' not found in right table.",
                    join_node
                )
    
    return True


def _is_metric_computed(metric: str, stmt: SelectStmt) -> bool:
    """Check if a metric is computed in the statement."""
    for compute_item in stmt.compute:
        if compute_item.result_name == metric:
            return True
    return False


def _is_attribute_available(attr: str, stmt: SelectStmt) -> bool:
    """Check if an attribute is available (computed or base attribute)."""
    # Base attributes always available
    if attr in BASE_NODE_ATTRIBUTES or attr in BASE_EDGE_ATTRIBUTES:
        return True
    
    # Check computed metrics
    if _is_metric_computed(attr, stmt):
        return True
    
    # If autocompute enabled, assume it's available
    if stmt.autocompute:
        return True
    
    return False


def _get_attribute_type(attr: str, stmt: SelectStmt) -> Type:
    """Get the type of an attribute."""
    # Base attributes
    if attr in BASE_NODE_ATTRIBUTES or attr in BASE_EDGE_ATTRIBUTES:
        if attr in {"node", "layer", "source", "target", "source_layer", "target_layer"}:
            return StringType()
        else:
            return NumericType()
    
    # Numeric metrics
    if attr in NUMERIC_METRIC_NAMES:
        # Check if it has uncertainty
        for compute_item in stmt.compute:
            if compute_item.result_name == attr and compute_item.uncertainty:
                return DistributionType(NumericType())
        return NumericType()
    
    # Check computed metrics
    for compute_item in stmt.compute:
        if compute_item.result_name == attr:
            if compute_item.uncertainty:
                return DistributionType(NumericType())
            return NumericType()
    
    return ScalarType()


def _operator_supports_type(op: str, attr_type: Type) -> bool:
    """Check if an operator is compatible with an attribute type."""
    # Equality works for all types
    if op in {"=", "!="}:
        return True
    
    # Ordering requires numeric types
    if op in {">", "<", ">=", "<="}:
        return isinstance(attr_type, (NumericType, ScalarType)) or (
            isinstance(attr_type, DistributionType) and 
            isinstance(attr_type.inner, NumericType)
        )
    
    return False


# ============================================================================
# Type System Class
# ============================================================================


class TypeSystem:
    """Type system for DSL queries.
    
    Provides type inference, type checking, and type unification.
    
    Example:
        >>> from py3plex.dsl import Q
        >>> ts = TypeSystem()
        >>> ast = Q.nodes().compute("degree").to_ast()
        >>> result_type = ts.infer(ast)
        >>> ts.check(ast)
        True
    """
    
    def __init__(self):
        """Initialize type system."""
        self.signatures = OPERATOR_SIGNATURES.copy()
    
    def infer(self, ast_node: Union[Query, SelectStmt]) -> Type:
        """Infer type of an AST node."""
        return infer_type(ast_node)
    
    def check(self, ast_node: Union[Query, SelectStmt]) -> bool:
        """Type check an AST node."""
        return type_check(ast_node)
    
    def register_operator(self, signature: OperatorSignature) -> None:
        """Register a new operator signature."""
        self.signatures[signature.name] = signature
    
    def get_operator_signature(self, name: str) -> Optional[OperatorSignature]:
        """Get operator signature by name."""
        return self.signatures.get(name)
    
    def unify(self, t1: Type, t2: Type) -> Optional[Type]:
        """Unify two types (find common type).
        
        Used for merging result types in joins and aggregations.
        
        Args:
            t1: First type
            t2: Second type
        
        Returns:
            Unified type or None if types cannot be unified
        
        Example:
            >>> ts = TypeSystem()
            >>> ts.unify(NumericType(), NumericType())
            NumericType()
            >>> ts.unify(NumericType(), StringType())
            None
        """
        # Exact match
        if t1 == t2:
            return t1
        
        # Distribution unification
        if isinstance(t1, DistributionType) and isinstance(t2, DistributionType):
            inner = self.unify(t1.inner, t2.inner)
            return DistributionType(inner) if inner else None
        
        # Distribution vs non-distribution: prefer distribution
        if isinstance(t1, DistributionType) and not isinstance(t2, DistributionType):
            inner = self.unify(t1.inner, t2)
            return DistributionType(inner) if inner else None
        
        if isinstance(t2, DistributionType) and not isinstance(t1, DistributionType):
            inner = self.unify(t1, t2.inner)
            return DistributionType(inner) if inner else None
        
        # Numeric and Scalar unify to ScalarType (least upper bound)
        # NOTE: In type theory, LUB is the most general type that encompasses both.
        # ScalarType is more general than NumericType, so it's the correct LUB.
        # Example: unify(NumericType, StringType) would fail, but
        #          unify(NumericType, ScalarType) succeeds with ScalarType.
        if isinstance(t1, (NumericType, ScalarType)) and isinstance(t2, (NumericType, ScalarType)):
            return ScalarType()
        
        # NodeSetType unification
        if isinstance(t1, NodeSetType) and isinstance(t2, NodeSetType):
            # Unify layers (intersection if both specified)
            layers = None
            if t1.layers and t2.layers:
                layers = t1.layers & t2.layers
            elif t1.layers:
                layers = t1.layers
            elif t2.layers:
                layers = t2.layers
            
            # Unify has_metrics (both must have metrics)
            has_metrics = t1.has_metrics and t2.has_metrics
            
            return NodeSetType(layers=layers, has_metrics=has_metrics)
        
        # EdgeSetType unification
        if isinstance(t1, EdgeSetType) and isinstance(t2, EdgeSetType):
            layers = None
            if t1.layers and t2.layers:
                layers = t1.layers & t2.layers
            elif t1.layers:
                layers = t1.layers
            elif t2.layers:
                layers = t2.layers
            
            has_metrics = t1.has_metrics and t2.has_metrics
            
            return EdgeSetType(layers=layers, has_metrics=has_metrics)
        
        # TableType unification
        if isinstance(t1, TableType) and isinstance(t2, TableType):
            # Unify columns (intersection)
            common_columns = {}
            for col in set(t1.columns.keys()) & set(t2.columns.keys()):
                col_type = self.unify(t1.columns[col], t2.columns[col])
                if col_type:
                    common_columns[col] = col_type
            return TableType(columns=common_columns)
        
        # Cannot unify
        return None


# ============================================================================
# Public API
# ============================================================================


__all__ = [
    # Base types
    "Type",
    "GraphType",
    "NodeSetType",
    "EdgeSetType",
    "PartitionType",
    "TableType",
    "DistributionType",
    "ScalarType",
    "NumericType",
    "StringType",
    "BoolType",
    "TimeSeriesType",
    
    # Type system
    "TypeSystem",
    "OperatorSignature",
    "OPERATOR_SIGNATURES",
    
    # Functions
    "infer_type",
    "type_check",
    
    # Errors
    "TypeCheckError",
]
