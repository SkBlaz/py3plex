"""Query planner for DSL v2.

This module implements an internal planning layer that sits between AST compilation
and execution. The planner:
1. Reorders safe query stages to reduce cost (filter early, compute late)
2. Computes pushdown: compute only measures needed for downstream steps
3. Caches expensive computations keyed by stable identifiers
4. Provides explain_plan() output with costs and stage order
5. Ensures determinism: same network + AST + params + seed → same plan and results
"""

import hashlib
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union, TYPE_CHECKING

if TYPE_CHECKING:
    from .ast import Query, SelectStmt
    from py3plex.core.multinet import multi_layer_network


# ==============================================================================
# Stage Types
# ==============================================================================


class StageType(Enum):
    """Types of execution stages in the planner."""
    GET_ITEMS = "get_items"
    FILTER_LAYERS = "filter_layers"
    FILTER_WHERE = "filter_where"
    GROUP = "group"
    COVERAGE = "coverage"
    COMPUTE = "compute"
    AGGREGATE = "aggregate"
    ORDER_BY = "order_by"
    LIMIT = "limit"
    EXPLAIN = "explain"
    EXPORT = "export"


@dataclass
class Stage:
    """Base class for execution stages.
    
    Attributes:
        stage_type: Type of stage
        requires_fields: Fields that must exist before this stage
        provides_fields: Fields provided by this stage
        cost_estimate: Relative cost estimate (1-100 scale)
        name: Human-readable stage name
        params: Stage-specific parameters
    """
    stage_type: StageType
    requires_fields: Set[str] = field(default_factory=set)
    provides_fields: Set[str] = field(default_factory=set)
    cost_estimate: int = 1
    name: str = ""
    params: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.name:
            self.name = self.stage_type.value


@dataclass
class GetItemsStage(Stage):
    """Stage for retrieving items (nodes or edges) from network."""
    def __init__(self, target: str):
        super().__init__(
            stage_type=StageType.GET_ITEMS,
            name=f"get_{target}",
            provides_fields={"id", "layer", "type"},
            cost_estimate=5,
            params={"target": target}
        )


@dataclass
class FilterLayersStage(Stage):
    """Stage for filtering by layer."""
    def __init__(self, layer_expr: Any):
        super().__init__(
            stage_type=StageType.FILTER_LAYERS,
            name="filter_layers",
            requires_fields={"layer"},
            cost_estimate=2,
            params={"layer_expr": layer_expr}
        )


@dataclass
class FilterWhereStage(Stage):
    """Stage for filtering by WHERE conditions."""
    def __init__(self, conditions: Any, references: Set[str]):
        super().__init__(
            stage_type=StageType.FILTER_WHERE,
            name="filter_where",
            requires_fields=references,
            cost_estimate=3,
            params={"conditions": conditions, "references": references}
        )


@dataclass
class GroupStage(Stage):
    """Stage for grouping items."""
    def __init__(self, group_by: List[str]):
        super().__init__(
            stage_type=StageType.GROUP,
            name="group_by",
            requires_fields=set(group_by),
            provides_fields={"__group_id__"},
            cost_estimate=4,
            params={"group_by": group_by}
        )


@dataclass
class CoverageStage(Stage):
    """Stage for coverage filtering."""
    def __init__(self, coverage_spec: Dict[str, Any]):
        super().__init__(
            stage_type=StageType.COVERAGE,
            name="coverage_filter",
            requires_fields={"__group_id__"},
            cost_estimate=5,
            params=coverage_spec
        )


@dataclass
class ComputeStage(Stage):
    """Stage for computing measures."""
    # Base cost for compute stage - actual cost varies by measure
    BASE_COST = 50
    
    def __init__(self, measures: List[str]):
        super().__init__(
            stage_type=StageType.COMPUTE,
            name="compute",
            provides_fields=set(measures),
            cost_estimate=self.BASE_COST,  # Could be refined based on measures
            params={"measures": measures}
        )


@dataclass
class AggregateStage(Stage):
    """Stage for aggregation."""
    def __init__(self, aggregations: Dict[str, Any], references: Set[str]):
        super().__init__(
            stage_type=StageType.AGGREGATE,
            name="aggregate",
            requires_fields=references,
            provides_fields=set(aggregations.keys()),
            cost_estimate=10,
            params={"aggregations": aggregations}
        )


@dataclass
class OrderByStage(Stage):
    """Stage for ordering results."""
    def __init__(self, keys: List[str]):
        super().__init__(
            stage_type=StageType.ORDER_BY,
            name="order_by",
            requires_fields=set(keys),
            cost_estimate=15,
            params={"keys": keys}
        )


@dataclass
class LimitStage(Stage):
    """Stage for limiting results."""
    def __init__(self, limit: int):
        super().__init__(
            stage_type=StageType.LIMIT,
            name="limit",
            cost_estimate=1,
            params={"limit": limit}
        )


@dataclass
class ExplainStage(Stage):
    """Stage for adding explanations."""
    def __init__(self, explain_spec: Any):
        super().__init__(
            stage_type=StageType.EXPLAIN,
            name="explain",
            cost_estimate=20,
            params={"explain_spec": explain_spec}
        )


# ==============================================================================
# Cache Plan
# ==============================================================================


@dataclass
class CacheEntry:
    """A cache plan entry for a single stage.
    
    Attributes:
        lookup: Whether to try cache lookup
        store: Whether to store in cache
        key: Cache key
    """
    lookup: bool = False
    store: bool = False
    key: Optional[str] = None


@dataclass
class CachePlan:
    """Plan for cache operations.
    
    Attributes:
        enabled: Whether caching is enabled
        entries: Cache plan per stage (by stage index)
        backend_config: Configuration for cache backend
    """
    enabled: bool = False
    entries: Dict[int, CacheEntry] = field(default_factory=dict)
    backend_config: Dict[str, Any] = field(default_factory=dict)


# ==============================================================================
# Planned Query
# ==============================================================================


@dataclass
class PlannedQuery:
    """A fully planned query ready for execution.
    
    Attributes:
        planned_stages: Ordered list of execution stages
        required_measures: Set of measures that must be computed
        cache_plan: Cache operations plan
        plan_meta: Metadata about the plan (costs, rewrites, warnings)
        ast_hash: Hash of original AST
        plan_hash: Hash of planned stages
    """
    planned_stages: List[Stage] = field(default_factory=list)
    required_measures: Set[str] = field(default_factory=set)
    cache_plan: CachePlan = field(default_factory=CachePlan)
    plan_meta: Dict[str, Any] = field(default_factory=dict)
    ast_hash: str = ""
    plan_hash: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for metadata storage."""
        return {
            "ast_hash": self.ast_hash,
            "plan_hash": self.plan_hash,
            "planned_stage_order": [
                {
                    "name": stage.name,
                    "type": stage.stage_type.value,
                    "requires_fields": sorted(stage.requires_fields),
                    "provides_fields": sorted(stage.provides_fields),
                    "estimated_cost": stage.cost_estimate,
                }
                for stage in self.planned_stages
            ],
            "required_measures": sorted(self.required_measures),
            "rewrite_summary": self.plan_meta.get("rewrite_summary", []),
            "warnings": self.plan_meta.get("warnings", []),
            "total_estimated_cost": sum(s.cost_estimate for s in self.planned_stages),
        }


# ==============================================================================
# Compute Policy
# ==============================================================================


class ComputePolicy(Enum):
    """Policy for determining which measures to compute."""
    EXPLICIT = "explicit"  # Compute exactly what user requested + required for semantics
    MINIMAL = "minimal"    # Ignore unused user-requested computes (opt-in)
    ALL = "all"            # Compute everything requested regardless


# ==============================================================================
# Query Planner
# ==============================================================================


class QueryPlanner:
    """Query planner for DSL v2.
    
    The planner analyzes AST queries and produces optimized execution plans.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize planner.
        
        Args:
            config: Optional planner configuration
                - compute_policy: "explicit" (default), "minimal", or "all"
                - enable_cache: Whether to enable caching (default: True)
                - cache_config: Cache backend configuration
        """
        self.config = config or {}
        self.compute_policy = ComputePolicy(
            self.config.get("compute_policy", "explicit")
        )
        self.enable_cache = self.config.get("enable_cache", True)
        self.cache_config = self.config.get("cache_config", {})
    
    def plan(
        self,
        ast: Union['Query', 'SelectStmt'],
        network: Any,
        params: Optional[Dict[str, Any]] = None
    ) -> PlannedQuery:
        """Create an execution plan for a query.
        
        Args:
            ast: Query or SelectStmt AST
            network: Multilayer network
            params: Bound parameter values
            
        Returns:
            PlannedQuery with optimized stage order
        """
        from .ast import Query, SelectStmt
        from .provenance import ast_fingerprint
        
        # Extract SelectStmt
        if isinstance(ast, Query):
            select = ast.select
        elif isinstance(ast, SelectStmt):
            select = ast
        else:
            raise TypeError(f"Expected Query or SelectStmt, got {type(ast)}")
        
        # Start timing
        start_time = time.monotonic()
        
        # Get AST hash
        ast_hash = ast_fingerprint(ast)
        
        # Extract stages from AST
        stages = self._extract_stages(select)
        
        # Analyze dependencies
        available_fields = self._get_intrinsic_fields(select.target.value)
        
        # Determine required measures
        required_measures = self._compute_required_measures(select, stages)
        
        # Reorder stages for optimization
        planned_stages, rewrite_summary = self._reorder_stages(
            stages, available_fields, required_measures
        )
        
        # Create cache plan
        cache_plan = self._create_cache_plan(
            planned_stages, network, ast_hash, params
        )
        
        # Calculate plan hash
        plan_hash = self._compute_plan_hash(planned_stages, required_measures)
        
        # Build metadata
        plan_time_ms = (time.monotonic() - start_time) * 1000
        warnings = []
        
        # Check for network version
        if not hasattr(network, "_version") and not hasattr(network, "version"):
            warnings.append(
                "network_version unavailable; caching uses fingerprint only"
            )
        
        plan_meta = {
            "rewrite_summary": rewrite_summary,
            "warnings": warnings,
            "plan_time_ms": plan_time_ms,
        }
        
        return PlannedQuery(
            planned_stages=planned_stages,
            required_measures=required_measures,
            cache_plan=cache_plan,
            plan_meta=plan_meta,
            ast_hash=ast_hash,
            plan_hash=plan_hash,
        )
    
    def _extract_stages(self, select: 'SelectStmt') -> List[Stage]:
        """Extract execution stages from SELECT statement.
        
        Args:
            select: SELECT statement
            
        Returns:
            List of stages in original AST order
        """
        stages: List[Stage] = []
        
        # 1. GetItems stage (always first)
        target = select.target.value
        stages.append(GetItemsStage(target))
        
        # 2. Layer filtering
        if select.layer_expr is not None or select.layer_set is not None:
            layer_expr = select.layer_expr or select.layer_set
            stages.append(FilterLayersStage(layer_expr))
        
        # 3. WHERE filtering
        if select.where is not None:
            references = self._extract_field_references(select.where)
            stages.append(FilterWhereStage(select.where, references))
        
        # 4. Grouping
        if select.group_by:
            stages.append(GroupStage(select.group_by))
        
        # 5. Coverage filtering
        if select.coverage_mode is not None:
            coverage_spec = {
                "mode": select.coverage_mode,
                "k": select.coverage_k,
                "p": select.coverage_p,
                "group": select.coverage_group,
                "id_field": select.coverage_id_field,
            }
            stages.append(CoverageStage(coverage_spec))
        
        # 6. Compute
        if select.compute:
            measure_names = [c.name for c in select.compute]
            stages.append(ComputeStage(measure_names))
        
        # 7. Aggregation
        if select.aggregate_specs:
            references = self._extract_aggregation_references(select.aggregate_specs)
            stages.append(AggregateStage(select.aggregate_specs, references))
        
        # 8. Ordering
        if select.order_by:
            keys = [o.key for o in select.order_by]
            stages.append(OrderByStage(keys))
        
        # 9. Limit
        if select.limit is not None:
            stages.append(LimitStage(select.limit))
        
        # 10. Explain
        if select.explain_spec is not None:
            stages.append(ExplainStage(select.explain_spec))
        
        return stages
    
    def _extract_field_references(self, where: Any) -> Set[str]:
        """Extract field names referenced in WHERE clause.
        
        Args:
            where: ConditionExpr
            
        Returns:
            Set of field names
        """
        fields = set()
        
        if hasattr(where, 'atoms'):
            for atom in where.atoms:
                if hasattr(atom, 'comparison') and atom.comparison:
                    fields.add(atom.comparison.left)
        
        return fields
    
    def _extract_aggregation_references(self, agg_specs: Dict[str, Any]) -> Set[str]:
        """Extract field names referenced in aggregations.
        
        Args:
            agg_specs: Aggregation specifications
            
        Returns:
            Set of field names
            
        Note:
            This is a simplified implementation. Full implementation would
            parse aggregation expressions to extract field references.
            For now, assumes aggregations may reference any available fields.
        """
        # Conservative approach: return empty set since we can't parse complex expressions yet
        # This means aggregations won't trigger dependency errors, but also won't
        # benefit from compute pushdown optimization
        return set()
    
    def _get_intrinsic_fields(self, target: str) -> Set[str]:
        """Get intrinsic fields available before any computation.
        
        Args:
            target: "nodes" or "edges"
            
        Returns:
            Set of field names
        """
        if target == "nodes":
            return {"id", "layer", "type", "node"}
        elif target == "edges":
            return {"source", "target", "source_layer", "target_layer", "type"}
        else:
            return {"id", "layer", "type"}
    
    def _compute_required_measures(
        self, select: 'SelectStmt', stages: List[Stage]
    ) -> Set[str]:
        """Determine which measures must be computed.
        
        Args:
            select: SELECT statement
            stages: List of stages
            
        Returns:
            Set of required measure names
        """
        required = set()
        
        # Measures referenced in WHERE
        if select.where is not None:
            refs = self._extract_field_references(select.where)
            required.update(refs)
        
        # Measures referenced in ORDER BY
        if select.order_by:
            required.update(o.key for o in select.order_by)
        
        # Measures referenced in aggregations
        if select.aggregate_specs:
            refs = self._extract_aggregation_references(select.aggregate_specs)
            required.update(refs)
        
        # Policy: explicit (default) - include user-requested computes
        if self.compute_policy == ComputePolicy.EXPLICIT:
            if select.compute:
                required.update(c.name for c in select.compute)
        
        # Policy: minimal - only include computes if actually used
        # (already computed above)
        
        # Policy: all - include everything
        if self.compute_policy == ComputePolicy.ALL:
            if select.compute:
                required.update(c.name for c in select.compute)
        
        return required
    
    def _reorder_stages(
        self,
        stages: List[Stage],
        available_fields: Set[str],
        required_measures: Set[str]
    ) -> Tuple[List[Stage], List[str]]:
        """Reorder stages for optimization.
        
        Args:
            stages: Original stage order
            available_fields: Fields available before any computation
            required_measures: Measures that must be computed
            
        Returns:
            Tuple of (reordered stages, rewrite summary)
            
        Raises:
            DslExecutionError: If dependencies cannot be satisfied
        """
        from .errors import DslExecutionError
        
        rewrite_summary = []
        
        # Separate stages by type
        get_items = None
        filter_layers = None
        filter_where = None
        computes = []
        others = []
        
        for stage in stages:
            if stage.stage_type == StageType.GET_ITEMS:
                get_items = stage
            elif stage.stage_type == StageType.FILTER_LAYERS:
                filter_layers = stage
            elif stage.stage_type == StageType.FILTER_WHERE:
                filter_where = stage
            elif stage.stage_type == StageType.COMPUTE:
                computes.append(stage)
            else:
                others.append(stage)
        
        # Build optimized order
        optimized = []
        computed_fields = set(available_fields)
        
        # 1. Always start with GetItems
        if get_items:
            optimized.append(get_items)
            computed_fields.update(get_items.provides_fields)
        
        # 2. Push layer filtering early
        if filter_layers:
            optimized.append(filter_layers)
            rewrite_summary.append("Moved layer filtering early")
        
        # 3. Determine if WHERE filter can be moved before compute
        if filter_where:
            # Check if all referenced fields are available without compute
            refs = filter_where.requires_fields
            computed_refs = refs - computed_fields
            
            if not computed_refs:
                # All fields available - filter early
                optimized.append(filter_where)
                rewrite_summary.append("Moved WHERE filter before compute")
                filter_where = None  # Don't add again later
            elif computes:
                # Some fields need computation - validate they will be provided
                compute_provides = set()
                for compute in computes:
                    compute_provides.update(compute.provides_fields)
                
                missing = computed_refs - compute_provides
                if missing:
                    # Fields are referenced but never computed
                    missing_list = sorted(missing)
                    
                    # Check if missing fields look like known measures
                    # Get known measures from registry if available
                    try:
                        from .registry import measure_registry
                        known_measures = list(measure_registry.keys())
                    except Exception:
                        # Fallback to common measures if registry unavailable
                        known_measures = ["degree", "betweenness_centrality", 
                                         "closeness_centrality", "eigenvector_centrality", 
                                         "pagerank"]
                    
                    likely_measures = [m for m in missing_list if m in known_measures]
                    
                    if likely_measures:
                        raise DslExecutionError(
                            f"Field(s) {likely_measures} referenced in WHERE clause but not computed. "
                            f"Add .compute({', '.join(repr(m) for m in likely_measures)}) before the WHERE clause, "
                            f"or use .compute(...) earlier in the query."
                        )
                    else:
                        raise DslExecutionError(
                            f"Field(s) {missing_list} referenced in WHERE clause but not computed. "
                            f"Add .compute({', '.join(repr(m) for m in missing_list)}) before the WHERE clause, "
                            f"or use .compute(...) earlier in the query."
                        )
            else:
                # No compute stages but WHERE needs computed fields
                missing_list = sorted(computed_refs)
                raise DslExecutionError(
                    f"Field(s) {missing_list} referenced in WHERE clause but not computed. "
                    f"Add .compute({', '.join(repr(m) for m in missing_list)}) before the WHERE clause."
                )
        
        # 4. Add compute stage (delayed as much as possible)
        if computes:
            # Update compute stage to only include required measures
            if self.compute_policy == ComputePolicy.MINIMAL:
                for compute in computes:
                    original_measures = set(compute.params["measures"])
                    needed_measures = original_measures & required_measures
                    if needed_measures != original_measures:
                        compute.params["measures"] = list(needed_measures)
                        compute.provides_fields = needed_measures
                        rewrite_summary.append(
                            f"Reduced compute from {len(original_measures)} to "
                            f"{len(needed_measures)} measures (compute pushdown)"
                        )
            optimized.extend(computes)
            for compute in computes:
                computed_fields.update(compute.provides_fields)
        
        # 5. Add WHERE filter if it needs computed fields
        if filter_where:
            optimized.append(filter_where)
        
        # 6. Validate remaining stages have required fields
        for stage in others:
            missing = stage.requires_fields - computed_fields
            if missing:
                # Try to provide helpful error message
                stage_name = stage.name or stage.stage_type.value
                missing_list = sorted(missing)
                
                # Check if missing fields look like known measures
                try:
                    from .registry import measure_registry
                    known_measures = list(measure_registry.keys())
                except Exception:
                    # Fallback to common measures if registry unavailable
                    known_measures = ["degree", "betweenness_centrality", 
                                     "closeness_centrality", "eigenvector_centrality", 
                                     "pagerank"]
                
                likely_measures = [m for m in missing_list if m in known_measures]
                
                if likely_measures:
                    raise DslExecutionError(
                        f"Field(s) {likely_measures} required by {stage_name} but not computed. "
                        f"Add .compute({', '.join(repr(m) for m in likely_measures)}) before "
                        f"the operation that requires them."
                    )
                else:
                    raise DslExecutionError(
                        f"Field(s) {missing_list} required by {stage_name} are not available. "
                        f"Check that all required fields are computed or available as intrinsic fields."
                    )
        
        # 7. Add remaining stages in dependency order
        optimized.extend(others)
        
        return optimized, rewrite_summary
    
    def _create_cache_plan(
        self,
        stages: List[Stage],
        network: Any,
        ast_hash: str,
        params: Optional[Dict[str, Any]]
    ) -> CachePlan:
        """Create cache plan for stages.
        
        Args:
            stages: Planned stages
            network: Network
            ast_hash: AST hash
            params: Query parameters
            
        Returns:
            CachePlan
        """
        if not self.enable_cache:
            return CachePlan(enabled=False)
        
        from .provenance import network_fingerprint
        
        # Get network fingerprint
        net_fp = network_fingerprint(network)
        fp_str = f"{net_fp['node_count']}_{net_fp['edge_count']}_{net_fp['layer_count']}"
        
        # Build cache plan
        entries = {}
        for i, stage in enumerate(stages):
            if stage.stage_type == StageType.COMPUTE:
                # Cache compute stages
                measures = stage.params.get("measures", [])
                for measure in measures:
                    # Create cache key
                    key_parts = [
                        fp_str,
                        ast_hash,
                        measure,
                        str(params) if params else "",
                    ]
                    cache_key = hashlib.sha256(
                        "|".join(key_parts).encode()
                    ).hexdigest()[:16]
                    
                    entries[i] = CacheEntry(
                        lookup=True,
                        store=True,
                        key=cache_key
                    )
                    break  # One entry per stage
        
        return CachePlan(
            enabled=True,
            entries=entries,
            backend_config=self.cache_config
        )
    
    def _compute_plan_hash(
        self, stages: List[Stage], required_measures: Set[str]
    ) -> str:
        """Compute hash of the planned stages.
        
        Args:
            stages: Planned stages
            required_measures: Required measures
            
        Returns:
            Hash string
        """
        # Create canonical representation
        parts = []
        for stage in stages:
            parts.append(f"{stage.stage_type.value}:{sorted(stage.requires_fields)}")
        parts.append(f"measures:{sorted(required_measures)}")
        
        canonical = "|".join(parts)
        return hashlib.sha256(canonical.encode()).hexdigest()[:16]


# ==============================================================================
# Public API
# ==============================================================================


def plan_query(
    ast: Union['Query', 'SelectStmt'],
    network: Any,
    params: Optional[Dict[str, Any]] = None,
    config: Optional[Dict[str, Any]] = None
) -> PlannedQuery:
    """Plan a query for execution.
    
    This is the main entry point for query planning.
    
    Args:
        ast: Query or SelectStmt AST
        network: Multilayer network
        params: Bound parameter values
        config: Optional planner configuration
        
    Returns:
        PlannedQuery with optimized execution plan
        
    Example:
        >>> from py3plex.dsl import Q
        >>> q = Q.nodes().compute("degree").order_by("degree")
        >>> plan = plan_query(q._ast, network)
        >>> print(plan.plan_meta["rewrite_summary"])
    """
    planner = QueryPlanner(config)
    return planner.plan(ast, network, params)
