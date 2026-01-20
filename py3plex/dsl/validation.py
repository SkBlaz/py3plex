"""AST-level validation for DSL v2.

This module provides compile-time validation for DSL queries, catching
invalid/ambiguous/unsafe queries before execution with precise diagnostics.

Validation supports:
- Field existence and type checking
- Target-specific rules (nodes vs edges)
- Grouping and aggregation correctness
- UQ parameter validation
- Layer expression validation
- Ordering and limiting validation

Stable error codes (DSLVAL_*) enable programmatic error handling.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional, Set, Tuple
import difflib

from .ast import (
    Query,
    SelectStmt,
    Target,
    ConditionExpr,
    ConditionAtom,
    Comparison,
    ComputeItem,
    OrderItem,
    AggregationItem,
    GroupingMode,
    UQConfig,
    LayerExpr,
)
from .errors import _suggest_similar
from py3plex.exceptions import Py3plexException


# Error code constants
DSLVAL_FIELD_UNKNOWN = "DSLVAL_FIELD_UNKNOWN"
DSLVAL_FIELD_TARGET_MISMATCH = "DSLVAL_FIELD_TARGET_MISMATCH"
DSLVAL_RESERVED_FIELD_UNSUPPORTED = "DSLVAL_RESERVED_FIELD_UNSUPPORTED"
DSLVAL_GROUPING_INVALID = "DSLVAL_GROUPING_INVALID"
DSLVAL_AGGREGATION_MISSING_FIELD = "DSLVAL_AGGREGATION_MISSING_FIELD"
DSLVAL_AGGREGATION_INVALID_PARAMS = "DSLVAL_AGGREGATION_INVALID_PARAMS"
DSLVAL_UQ_INVALID_PARAMS = "DSLVAL_UQ_INVALID_PARAMS"
DSLVAL_ORDER_FIELD_MISSING = "DSLVAL_ORDER_FIELD_MISSING"
DSLVAL_LAYER_UNKNOWN = "DSLVAL_LAYER_UNKNOWN"
DSLVAL_LAYER_EMPTY = "DSLVAL_LAYER_EMPTY"


@dataclass
class ValidationIssue:
    """A single validation issue (error or warning).
    
    Attributes:
        code: Stable machine-readable error code (e.g., DSLVAL_FIELD_UNKNOWN)
        severity: "error" or "warning"
        message: Human-readable description
        path: AST path like "where.conditions[0]" or list of path segments
        hint: Optional suggestion for how to fix
        span: Optional (start, end) offset for string DSL
        context: Additional payload (e.g., invalid field name, allowed fields)
    """
    code: str
    severity: Literal["error", "warning"]
    message: str
    path: str | List[str] = ""
    hint: Optional[str] = None
    span: Optional[Tuple[int, int]] = None
    context: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        # Normalize path to string
        if isinstance(self.path, list):
            self.path = ".".join(str(p) for p in self.path)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {
            "code": self.code,
            "severity": self.severity,
            "message": self.message,
            "path": self.path,
        }
        if self.hint:
            result["hint"] = self.hint
        if self.span:
            result["span"] = self.span
        if self.context:
            result["context"] = self.context
        return result


@dataclass
class ValidationResult:
    """Result of AST validation.
    
    Attributes:
        ok: True if no errors (warnings are OK)
        errors: List of error issues
        warnings: List of warning issues
    """
    ok: bool = True
    errors: List[ValidationIssue] = field(default_factory=list)
    warnings: List[ValidationIssue] = field(default_factory=list)
    
    def add_error(self, issue: ValidationIssue):
        """Add an error issue."""
        if issue.severity != "error":
            raise ValueError("Issue must have severity='error'")
        self.errors.append(issue)
        self.ok = False
    
    def add_warning(self, issue: ValidationIssue):
        """Add a warning issue."""
        if issue.severity != "warning":
            raise ValueError("Issue must have severity='warning'")
        self.warnings.append(issue)
    
    def raise_if_errors(self, exc_class=None):
        """Raise exception if there are errors.
        
        Args:
            exc_class: Exception class to raise (default: DSLValidationError)
        """
        if self.errors:
            if exc_class is None:
                exc_class = DSLValidationError
            raise exc_class(issues=self.errors + self.warnings)
    
    @property
    def all_issues(self) -> List[ValidationIssue]:
        """Get all issues (errors + warnings)."""
        return self.errors + self.warnings
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "ok": self.ok,
            "errors": [e.to_dict() for e in self.errors],
            "warnings": [w.to_dict() for w in self.warnings],
        }


class DSLValidationError(Py3plexException):
    """Exception raised when DSL validation fails.
    
    Contains structured validation issues that can be programmatically inspected.
    
    Attributes:
        issues: List of ValidationIssue objects
    """
    
    default_code = "DSLVAL001"
    
    def __init__(self, issues: List[ValidationIssue], **kwargs):
        self.issues = issues
        
        # Format message
        error_count = sum(1 for i in issues if i.severity == "error")
        warning_count = sum(1 for i in issues if i.severity == "warning")
        
        msg_parts = []
        if error_count:
            msg_parts.append(f"{error_count} error(s)")
        if warning_count:
            msg_parts.append(f"{warning_count} warning(s)")
        
        message = f"Validation failed: {', '.join(msg_parts)}"
        
        super().__init__(message, **kwargs)
    
    def __str__(self) -> str:
        """Format error message with all issues."""
        lines = [str(super())]
        
        # Format errors first
        errors = [i for i in self.issues if i.severity == "error"]
        if errors:
            lines.append("\nErrors:")
            for i, issue in enumerate(errors, 1):
                lines.append(f"  {i}. [{issue.code}] {issue.message}")
                if issue.path:
                    lines.append(f"     at: {issue.path}")
                if issue.hint:
                    lines.append(f"     hint: {issue.hint}")
        
        # Then warnings
        warnings = [i for i in self.issues if i.severity == "warning"]
        if warnings:
            lines.append("\nWarnings:")
            for i, issue in enumerate(warnings, 1):
                lines.append(f"  {i}. [{issue.code}] {issue.message}")
                if issue.path:
                    lines.append(f"     at: {issue.path}")
                if issue.hint:
                    lines.append(f"     hint: {issue.hint}")
        
        return "\n".join(lines)


@dataclass
class NetworkSchema:
    """Schema information about a network.
    
    Attributes:
        node_attributes: Set of available node attribute names
        edge_attributes: Set of available edge attribute names
        reserved_node_fields: Set of reserved node fields (degree, layer, etc.)
        reserved_edge_fields: Set of reserved edge fields (src_degree, weight, etc.)
        layers: List of layer names
        node_types: Optional set of node type values
    """
    node_attributes: Set[str] = field(default_factory=set)
    edge_attributes: Set[str] = field(default_factory=set)
    reserved_node_fields: Set[str] = field(default_factory=lambda: {
        "degree", "layer", "id", "type"
    })
    reserved_edge_fields: Set[str] = field(default_factory=lambda: {
        "src_degree", "dst_degree", "source_layer", "target_layer",
        "weight", "source", "target"
    })
    layers: List[str] = field(default_factory=list)
    node_types: Optional[Set[str]] = None
    
    def get_all_node_fields(self) -> Set[str]:
        """Get all valid node fields (attributes + reserved)."""
        return self.node_attributes | self.reserved_node_fields
    
    def get_all_edge_fields(self) -> Set[str]:
        """Get all valid edge fields (attributes + reserved)."""
        return self.edge_attributes | self.reserved_edge_fields


@dataclass
class EngineCapabilities:
    """Engine capabilities for validation.
    
    Attributes:
        supported_measures: Set of supported measure names
        supported_aggregations: Set of supported aggregation functions
        supports_edges: Whether edge queries are supported
        supports_uq: Whether UQ is supported
        supports_pattern: Whether pattern matching is supported
        uq_methods: Set of supported UQ methods
    """
    supported_measures: Set[str] = field(default_factory=set)
    supported_aggregations: Set[str] = field(default_factory=lambda: {
        "count", "mean", "sum", "min", "max", "std", "median", "quantile"
    })
    supports_edges: bool = True
    supports_uq: bool = True
    supports_pattern: bool = False
    uq_methods: Set[str] = field(default_factory=lambda: {
        "bootstrap", "perturbation", "seed", "stratified_perturbation"
    })


def infer_schema(network: Any, sample_size: int = 100) -> NetworkSchema:
    """Infer network schema from a network instance.
    
    Performs minimal introspection to avoid O(N) scans.
    
    Args:
        network: Network instance
        sample_size: Max number of nodes/edges to sample
        
    Returns:
        NetworkSchema with inferred information
    """
    schema = NetworkSchema()
    
    # Get layers
    if hasattr(network, 'get_layers'):
        schema.layers = list(network.get_layers())
    
    # Sample nodes to infer attributes
    if hasattr(network, 'get_nodes'):
        nodes = list(network.get_nodes())
        if nodes:
            sample = nodes[:min(sample_size, len(nodes))]
            
            # Try to get node attributes from first few nodes
            if hasattr(network, 'core_network'):
                G = network.core_network
                for node in sample:
                    if G.has_node(node):
                        attrs = G.nodes[node]
                        schema.node_attributes.update(attrs.keys())
                        break  # Just need one to know the schema
    
    # Sample edges to infer attributes
    if hasattr(network, 'get_edges'):
        edges = list(network.get_edges())
        if edges:
            sample = edges[:min(sample_size, len(edges))]
            
            # Try to get edge attributes
            if hasattr(network, 'core_network'):
                G = network.core_network
                for edge in sample:
                    if len(edge) >= 2:
                        src, dst = edge[0], edge[1]
                        if G.has_edge(src, dst):
                            attrs = G.edges[src, dst]
                            schema.edge_attributes.update(attrs.keys())
                            break
    
    return schema


def get_default_capabilities() -> EngineCapabilities:
    """Get default engine capabilities.
    
    Returns:
        EngineCapabilities with defaults from measure registry
    """
    from .registry import measure_registry
    
    # Get supported measures from registry
    supported_measures = set(measure_registry.keys())
    
    return EngineCapabilities(supported_measures=supported_measures)


def validate_ast(
    query: Query,
    schema: Optional[NetworkSchema] = None,
    capabilities: Optional[EngineCapabilities] = None,
    network: Any = None
) -> ValidationResult:
    """Validate a query AST.
    
    Performs compile-time validation to catch errors before execution.
    
    Args:
        query: Query AST to validate
        schema: Optional network schema (inferred from network if not provided)
        capabilities: Optional engine capabilities (uses defaults if not provided)
        network: Optional network instance (used to infer schema)
        
    Returns:
        ValidationResult with errors and warnings
    """
    result = ValidationResult()
    
    # Infer schema if needed
    if schema is None and network is not None:
        schema = infer_schema(network)
    
    # Use default capabilities if not provided
    if capabilities is None:
        capabilities = get_default_capabilities()
    
    # Validate based on query type
    if isinstance(query.stmt, SelectStmt):
        _validate_select_stmt(query.stmt, result, schema, capabilities)
    
    return result


def _validate_select_stmt(
    stmt: SelectStmt,
    result: ValidationResult,
    schema: Optional[NetworkSchema],
    capabilities: EngineCapabilities
):
    """Validate a SELECT statement.
    
    Args:
        stmt: SELECT statement to validate
        result: ValidationResult to append issues to
        schema: Network schema (may be None)
        capabilities: Engine capabilities
    """
    # Determine what fields are available based on target
    if schema:
        if stmt.target == Target.NODES:
            available_fields = schema.get_all_node_fields()
        elif stmt.target == Target.EDGES:
            available_fields = schema.get_all_edge_fields()
        else:
            available_fields = set()
    else:
        available_fields = None
    
    # Track computed fields
    computed_fields = set()
    
    # Validate WHERE clause
    if stmt.where:
        _validate_where_clause(
            stmt.where, stmt.target, result, available_fields, schema
        )
    
    # Validate COMPUTE items
    if stmt.compute:
        for item in stmt.compute:
            _validate_compute_item(
                item, stmt.target, result, capabilities, computed_fields
            )
            computed_fields.add(item.alias or item.measure)
    
    # Update available fields with computed ones
    if available_fields is not None:
        available_fields = available_fields | computed_fields
    
    # Validate grouping
    if stmt.grouping:
        _validate_grouping(stmt.grouping, stmt.target, result)
    
    # Validate aggregations
    if stmt.aggregations:
        for agg in stmt.aggregations:
            _validate_aggregation(
                agg, result, available_fields, capabilities
            )
    
    # Validate ORDER BY
    if stmt.order_by:
        for order_item in stmt.order_by:
            _validate_order_by(order_item, result, available_fields)
    
    # Validate layer expression
    if stmt.layer_expr and schema:
        _validate_layer_expr(stmt.layer_expr, result, schema)
    
    # Validate UQ config
    if stmt.uq_config:
        _validate_uq_config(stmt.uq_config, result, capabilities)


def _validate_where_clause(
    where: ConditionExpr,
    target: Target,
    result: ValidationResult,
    available_fields: Optional[Set[str]],
    schema: Optional[NetworkSchema]
):
    """Validate WHERE clause conditions."""
    for atom in where.atoms:
        if atom.comparison:
            _validate_field_access(
                atom.comparison.left,
                target,
                result,
                available_fields,
                schema,
                path="where"
            )


def _validate_field_access(
    field_name: str,
    target: Target,
    result: ValidationResult,
    available_fields: Optional[Set[str]],
    schema: Optional[NetworkSchema],
    path: str = ""
):
    """Validate field access based on target and schema.
    
    Args:
        field_name: Name of field being accessed
        target: Query target (NODES or EDGES)
        result: ValidationResult to append issues to
        available_fields: Set of available fields (may be None)
        schema: Network schema (may be None)
        path: AST path for error reporting
    """
    if available_fields is None:
        # Can't validate without schema
        return
    
    if field_name not in available_fields:
        # Check if it's a target-specific mismatch
        if schema:
            if target == Target.NODES:
                # Check if it's an edge field
                if field_name in schema.reserved_edge_fields:
                    hint = None
                    if field_name == "weight":
                        hint = "weight is an edge attribute; use it in edge queries"
                    elif field_name == "src_degree":
                        hint = "use 'degree' for node queries (src_degree is for edges)"
                    
                    result.add_error(ValidationIssue(
                        code=DSLVAL_FIELD_TARGET_MISMATCH,
                        severity="error",
                        message=f"Field '{field_name}' is not valid for node queries",
                        path=path,
                        hint=hint,
                        context={"field": field_name, "target": "nodes"}
                    ))
                    return
            elif target == Target.EDGES:
                # Check if it's a node field
                if field_name == "degree":
                    result.add_error(ValidationIssue(
                        code=DSLVAL_FIELD_TARGET_MISMATCH,
                        severity="error",
                        message=f"Field 'degree' is not valid for edge queries",
                        path=path,
                        hint="use 'src_degree' or 'dst_degree' for edge queries",
                        context={"field": field_name, "target": "edges"}
                    ))
                    return
        
        # Unknown field
        suggestion = _suggest_similar(field_name, list(available_fields))
        hint = f"Did you mean '{suggestion}'?" if suggestion else None
        if not hint and len(available_fields) < 20:
            hint = f"Available fields: {', '.join(sorted(available_fields))}"
        
        result.add_error(ValidationIssue(
            code=DSLVAL_FIELD_UNKNOWN,
            severity="error",
            message=f"Unknown field '{field_name}'",
            path=path,
            hint=hint,
            context={"field": field_name, "available": list(available_fields)}
        ))


def _validate_compute_item(
    item: ComputeItem,
    target: Target,
    result: ValidationResult,
    capabilities: EngineCapabilities,
    computed_fields: Set[str]
):
    """Validate a COMPUTE item."""
    # Check if measure is supported
    if item.measure not in capabilities.supported_measures:
        suggestion = _suggest_similar(
            item.measure, list(capabilities.supported_measures)
        )
        hint = f"Did you mean '{suggestion}'?" if suggestion else None
        
        result.add_error(ValidationIssue(
            code=DSLVAL_FIELD_UNKNOWN,
            severity="error",
            message=f"Unknown measure '{item.measure}'",
            path="compute",
            hint=hint,
            context={"measure": item.measure}
        ))
    
    # Validate UQ parameters if present
    if item.uncertainty and item.uq_params:
        _validate_uq_params(item.uq_params, result, capabilities, path="compute")


def _validate_grouping(
    grouping: GroupingMode,
    target: Target,
    result: ValidationResult
):
    """Validate grouping mode."""
    # per_layer_pair only valid for edges
    if grouping == GroupingMode.PER_LAYER_PAIR and target != Target.EDGES:
        result.add_error(ValidationIssue(
            code=DSLVAL_GROUPING_INVALID,
            severity="error",
            message="per_layer_pair() is only valid for edge queries",
            path="grouping",
            hint="use per_layer() for node queries",
            context={"grouping": str(grouping), "target": str(target)}
        ))


def _validate_aggregation(
    agg: AggregationItem,
    result: ValidationResult,
    available_fields: Optional[Set[str]],
    capabilities: EngineCapabilities
):
    """Validate an aggregation."""
    # Check if aggregation function is supported
    if agg.function not in capabilities.supported_aggregations:
        result.add_error(ValidationIssue(
            code=DSLVAL_AGGREGATION_INVALID_PARAMS,
            severity="error",
            message=f"Unsupported aggregation function '{agg.function}'",
            path="aggregate",
            hint=f"Supported: {', '.join(sorted(capabilities.supported_aggregations))}",
            context={"function": agg.function}
        ))
    
    # Check if field exists (if available_fields is known)
    if agg.column and available_fields is not None:
        if agg.column not in available_fields:
            result.add_error(ValidationIssue(
                code=DSLVAL_AGGREGATION_MISSING_FIELD,
                severity="error",
                message=f"Aggregation references unknown field '{agg.column}'",
                path="aggregate",
                hint=f"Add .compute('{agg.column}') before aggregation",
                context={"column": agg.column}
            ))
    
    # Validate aggregation-specific parameters
    if agg.function == "quantile":
        if "p" not in agg.params:
            result.add_error(ValidationIssue(
                code=DSLVAL_AGGREGATION_INVALID_PARAMS,
                severity="error",
                message="quantile() requires parameter 'p'",
                path="aggregate",
                hint="Example: quantile(field, p=0.5)",
                context={"function": "quantile"}
            ))
        elif not (0 <= agg.params.get("p", -1) <= 1):
            result.add_error(ValidationIssue(
                code=DSLVAL_AGGREGATION_INVALID_PARAMS,
                severity="error",
                message=f"quantile() parameter 'p' must be in [0, 1], got {agg.params['p']}",
                path="aggregate",
                hint="Use p between 0.0 and 1.0 (e.g., p=0.5 for median)",
                context={"p": agg.params["p"]}
            ))


def _validate_order_by(
    order_item: OrderItem,
    result: ValidationResult,
    available_fields: Optional[Set[str]]
):
    """Validate ORDER BY item."""
    if available_fields is not None:
        if order_item.key not in available_fields:
            suggestion = _suggest_similar(order_item.key, list(available_fields))
            hint = f"Did you mean '{suggestion}'?" if suggestion else None
            if not hint:
                hint = "Ensure field is computed or available before ordering"
            
            result.add_error(ValidationIssue(
                code=DSLVAL_ORDER_FIELD_MISSING,
                severity="error",
                message=f"ORDER BY references unknown field '{order_item.key}'",
                path="order_by",
                hint=hint,
                context={"field": order_item.key}
            ))


def _validate_layer_expr(
    layer_expr: LayerExpr,
    result: ValidationResult,
    schema: NetworkSchema
):
    """Validate layer expression."""
    if not schema.layers:
        # Can't validate without layer information
        return
    
    available_layers = set(schema.layers)
    referenced_layers = set(layer_expr.get_layer_names())
    
    # Check for unknown layers
    for layer in referenced_layers:
        if layer != "*" and layer not in available_layers:
            suggestion = _suggest_similar(layer, schema.layers)
            hint = f"Did you mean '{suggestion}'?" if suggestion else None
            if not hint and len(schema.layers) < 20:
                hint = f"Available layers: {', '.join(sorted(schema.layers))}"
            
            result.add_error(ValidationIssue(
                code=DSLVAL_LAYER_UNKNOWN,
                severity="error",
                message=f"Unknown layer '{layer}'",
                path="from_layers",
                hint=hint,
                context={"layer": layer, "available": schema.layers}
            ))
    
    # Warn if expression might resolve to empty set
    if not referenced_layers:
        result.add_warning(ValidationIssue(
            code=DSLVAL_LAYER_EMPTY,
            severity="warning",
            message="Layer expression may resolve to empty set",
            path="from_layers",
            hint="Ensure layer expression includes at least one layer",
            context={}
        ))


def _validate_uq_config(
    uq_config: UQConfig,
    result: ValidationResult,
    capabilities: EngineCapabilities
):
    """Validate UQ configuration."""
    _validate_uq_params(uq_config.__dict__, result, capabilities, path="uq")


def _validate_uq_params(
    params: Dict[str, Any],
    result: ValidationResult,
    capabilities: EngineCapabilities,
    path: str = "uq"
):
    """Validate UQ parameters."""
    # Check n_samples
    if "n_samples" in params:
        n_samples = params["n_samples"]
        if n_samples is not None and n_samples <= 0:
            result.add_error(ValidationIssue(
                code=DSLVAL_UQ_INVALID_PARAMS,
                severity="error",
                message=f"n_samples must be positive, got {n_samples}",
                path=path,
                hint="Use n_samples >= 10 for meaningful uncertainty estimates",
                context={"n_samples": n_samples}
            ))
    
    # Check ci
    if "ci" in params:
        ci = params["ci"]
        if ci is not None and not (0 < ci < 1):
            result.add_error(ValidationIssue(
                code=DSLVAL_UQ_INVALID_PARAMS,
                severity="error",
                message=f"ci must be in (0, 1), got {ci}",
                path=path,
                hint="Common values: 0.95, 0.99",
                context={"ci": ci}
            ))
    
    # Check method
    if "method" in params:
        method = params["method"]
        if method and method not in capabilities.uq_methods:
            result.add_error(ValidationIssue(
                code=DSLVAL_UQ_INVALID_PARAMS,
                severity="error",
                message=f"Unknown UQ method '{method}'",
                path=path,
                hint=f"Supported methods: {', '.join(sorted(capabilities.uq_methods))}",
                context={"method": method}
            ))


def format_validation_report(result: ValidationResult) -> str:
    """Format a validation result as a human-readable report.
    
    Args:
        result: ValidationResult to format
        
    Returns:
        Formatted string report
    """
    lines = []
    
    if result.ok and not result.warnings:
        lines.append("✓ Validation passed")
        return "\n".join(lines)
    
    # Summary
    error_count = len(result.errors)
    warning_count = len(result.warnings)
    
    if error_count:
        lines.append(f"✗ Validation failed: {error_count} error(s)")
    else:
        lines.append(f"✓ Validation passed with {warning_count} warning(s)")
    
    lines.append("")
    
    # Errors
    if result.errors:
        lines.append("Errors:")
        for i, issue in enumerate(result.errors, 1):
            lines.append(f"  {i}. [{issue.code}] {issue.message}")
            if issue.path:
                lines.append(f"     at: {issue.path}")
            if issue.hint:
                lines.append(f"     hint: {issue.hint}")
            lines.append("")
    
    # Warnings
    if result.warnings:
        lines.append("Warnings:")
        for i, issue in enumerate(result.warnings, 1):
            lines.append(f"  {i}. [{issue.code}] {issue.message}")
            if issue.path:
                lines.append(f"     at: {issue.path}")
            if issue.hint:
                lines.append(f"     hint: {issue.hint}")
            lines.append("")
    
    return "\n".join(lines).rstrip()
