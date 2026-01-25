"""Query executor for DSL v2.

This module provides the execution engine that runs AST queries against
multilayer networks. It supports temporal queries via the TemporalMultinetView wrapper.
"""

import ast
import copy
import logging
import random
import time
from typing import Any, Dict, List, Mapping, Optional, Set, Tuple, Union, Callable

try:
    from typing import TYPE_CHECKING
except ImportError:
    TYPE_CHECKING = False

import networkx as nx
import numpy as np

from .ast import (
    Query,
    SelectStmt,
    Target,
    ExportTarget,
    LayerExpr,
    ConditionExpr,
    ConditionAtom,
    Comparison,
    SpecialPredicate,
    ComputeItem,
    OrderItem,
    ParamRef,
    PlanStep,
    ExecutionPlan,
    TemporalContext,
    WindowSpec,
    DynamicsStmt,
    TrajectoriesStmt,
)
from .result import QueryResult
from .registry import measure_registry
from .operator_registry import get_operator
from .context import DSLExecutionContext
from .provenance import ProvenanceBuilder
from .errors import (
    DslExecutionError,
    ParameterMissingError,
    UnknownLayerError,
    UnknownMeasureError,
    UnknownAttributeError,
    GroupingError,
)

# Import requirements system for algorithm compatibility checking
from py3plex.requirements import check_compat, AlgorithmCompatibilityError

# Import UQ resolution and validation
from .uq_resolution import (
    resolve_uq_config,
    validate_uq_result_schema,
    wrap_deterministic_as_uq,
    UQResolutionError,
    UQSchemaValidationError,
)

# Import uncertainty support
from py3plex.uncertainty import (
    StatSeries,
    estimate_uncertainty,
    ResamplingStrategy,
)

# Import compositional UQ support
from .compositional_uq import (
    should_apply_compositional_uq,
    ResampleSpec,
    aggregate_with_uncertainty,
    compute_rank_stability,
    compute_coverage_stability,
    create_resampled_network,
)


# Resampling method mapping for uncertainty estimation
_RESAMPLING_METHOD_MAP = {
    "bootstrap": ResamplingStrategy.BOOTSTRAP,
    "perturbation": ResamplingStrategy.PERTURBATION,
    "seed": ResamplingStrategy.SEED,
    "jackknife": ResamplingStrategy.JACKKNIFE,
}


# ============================================================================
# UQ Propagation: Deterministic Seed Spawning and Replicate Execution
# ============================================================================

def _spawn_replicate_seed(master_seed: int, replicate_index: int) -> int:
    """Spawn a deterministic seed for a specific replicate.
    
    Uses a simple hash-based approach (SplitMix64-inspired) to generate
    deterministic, independent seeds for each replicate.
    
    Args:
        master_seed: The master seed
        replicate_index: Index of the replicate (0-based)
        
    Returns:
        Deterministic seed for this replicate
    """
    # Simple deterministic seed generation
    # Combine master seed and replicate index using hash
    import hashlib
    combined = f"{master_seed}_{replicate_index}".encode('utf-8')
    hash_bytes = hashlib.sha256(combined).digest()
    # Extract first 8 bytes as seed
    seed = int.from_bytes(hash_bytes[:8], byteorder='big')
    # Keep it within int32 range for numpy compatibility
    return seed % (2**31)


from dataclasses import dataclass as _dataclass_for_replicate

@_dataclass_for_replicate
class ReplicateContext:
    """Context for a single replicate execution.
    
    Attributes:
        replicate_id: Index of this replicate (0-based)
        replicate_seed: Seed for this replicate
        network: Network view for this replicate (may be perturbed/resampled)
        method: UQ method being used
    """
    replicate_id: int
    replicate_seed: int
    network: Any
    method: str


def _make_replicate_plan(
    network: Any,
    resolved_uq: 'ResolvedUQConfig',
) -> List[ReplicateContext]:
    """Create a deterministic plan of replicate contexts.
    
    Args:
        network: Base network
        resolved_uq: Resolved UQ configuration
        
    Returns:
        List of ReplicateContext objects, one per replicate
    """
    master_seed = resolved_uq.seed if resolved_uq.seed is not None else 0
    plan = []
    
    for i in range(resolved_uq.n_samples):
        rep_seed = _spawn_replicate_seed(master_seed, i)
        
        # Create network view for this replicate based on method
        if resolved_uq.method in ("bootstrap", "perturbation", "stratified_perturbation"):
            # These methods need a perturbed/resampled network
            # We'll create it during execution using the rep_seed
            rep_network = network  # Will be resampled/perturbed in executor
        else:
            # For 'seed' method, use the same network with different seed
            rep_network = network
        
        ctx = ReplicateContext(
            replicate_id=i,
            replicate_seed=rep_seed,
            network=rep_network,
            method=resolved_uq.method,
        )
        plan.append(ctx)
    
    return plan


def _create_replicate_network(
    base_network: Any,
    ctx: ReplicateContext,
    resolved_uq: 'ResolvedUQConfig',
) -> Any:
    """Create a network view for a replicate based on the UQ method.
    
    Args:
        base_network: The original network
        ctx: Replicate context
        resolved_uq: Resolved UQ config
        
    Returns:
        Network view (may be perturbed/resampled or same as base)
    """
    method = resolved_uq.method
    
    if method == "seed":
        # Seed method: use same network, different random seed for algorithms
        return base_network
    
    # For perturbation/bootstrap/stratified, create perturbed network
    from .compositional_uq import create_resampled_network, ResampleSpec
    
    # Build ResampleSpec from resolved_uq
    spec = ResampleSpec(
        method=method,
        n_samples=resolved_uq.n_samples,  # Total number of samples for seed spawning
        seed=resolved_uq.seed,  # Master seed
        kwargs=resolved_uq.kwargs
    )
    
    try:
        perturbed_net = create_resampled_network(base_network, spec, resample_idx=ctx.replicate_id)
        return perturbed_net
    except Exception as e:
        # If perturbation fails, log warning and use base network
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Failed to create replicate network for replicate {ctx.replicate_id}: {e}. Using base network.")
        return base_network


def _check_algorithm_compatibility(
    network: Any,
    measure_fn: Callable,
    compute_item: Optional['ComputeItem'] = None,
    seed: Optional[int] = None,
) -> List[Any]:
    """Check algorithm compatibility and return diagnostics.
    
    This function checks if a measure function has requirements attached and
    validates them against the network capabilities.
    
    Args:
        network: Network to check against
        measure_fn: Measure function (may have .requirements attribute)
        compute_item: Optional ComputeItem with UQ info
        seed: Optional random seed
    
    Returns:
        List of diagnostics (may be empty if compatible or no requirements)
    """
    # Check if function has requirements
    if not hasattr(measure_fn, 'requirements'):
        return []
    
    # Get network capabilities
    if not hasattr(network, 'capabilities'):
        return []
    
    net_caps = network.capabilities()
    requirements = measure_fn.requirements
    
    # Determine if UQ is requested
    uq_requested = False
    uq_method = None
    if compute_item:
        uq_requested = compute_item.uncertainty
        uq_method = compute_item.method
    
    # Get measure name
    algo_name = getattr(measure_fn, '__name__', 'unknown')
    
    # Check compatibility
    diagnostics = check_compat(
        net_caps,
        requirements,
        algorithm_name=algo_name,
        seed=seed,
        uq_requested=uq_requested,
        uq_method=uq_method,
    )
    
    return diagnostics


def _attach_diagnostics_to_result(
    result: 'QueryResult',
    diagnostics: List[Any],
) -> None:
    """Attach diagnostics to query result metadata.
    
    Args:
        result: QueryResult to modify
        diagnostics: List of Diagnostic objects
    """
    if not diagnostics:
        return
    
    # Convert diagnostics to dict format
    diag_dicts = [d.to_dict() for d in diagnostics]
    
    # Add to meta
    if 'diagnostics' not in result.meta:
        result.meta['diagnostics'] = []
    
    result.meta['diagnostics'].extend(diag_dicts)


def _format_uq_info(compute_item: ComputeItem, for_edges: bool = False) -> str:
    """Format UQ information for progress logging.
    
    Args:
        compute_item: ComputeItem with uncertainty configuration
        for_edges: If True, format message for edge queries (UQ not yet supported)
        
    Returns:
        Formatted string like " with UQ (perturbation, n=50)" or empty string
    """
    if not compute_item.uncertainty:
        return ""
    
    if for_edges:
        return " with UQ (not yet supported for edges)"
    
    method = compute_item.method or "perturbation"
    n_samples = compute_item.n_samples or 50
    return f" with UQ ({method}, n={n_samples})"


def _wrap_deterministic_uncertainty(values: Any, items: List[Any]) -> Dict[Any, Any]:
    """Wrap deterministic results with uncertainty scaffolding (std=0, certainty=1.0)."""

    def _wrap_single(val: Any) -> Dict[str, Any]:
        if isinstance(val, dict) and "mean" in val:
            return val
        try:
            mean_val = float(val)
        except Exception:
            mean_val = val
        return {
            "mean": mean_val,
            "std": 0.0,
            "quantiles": {},
            "certainty": 1.0,
        }

    if isinstance(values, StatSeries):
        return values.to_dict()

    if isinstance(values, dict):
        return {k: _wrap_single(v) for k, v in values.items()}

    # Scalar: apply to all items
    return {item: _wrap_single(values) for item in items}


# Centrality aliases mapping for smart defaults
# Maps common attribute names to their canonical centrality metric names
CENTRALITY_ALIASES = {
    "degree": "degree",
    "degree_centrality": "degree",
    "betweenness": "betweenness",
    "betweenness_centrality": "betweenness",
    "closeness": "closeness",
    "closeness_centrality": "closeness",
    "eigenvector": "eigenvector",
    "eigenvector_centrality": "eigenvector",
    "pagerank": "pagerank",
}


def _log_query_summary(select: SelectStmt, logger: logging.Logger) -> None:
    """Log a summary of the query pipeline to be executed.
    
    Args:
        select: SELECT statement
        logger: Logger instance
    """
    steps = []
    
    # Target
    steps.append(f"Target: {select.target.value}")
    
    # Layers
    if select.layer_set is not None:
        steps.append(f"Layers: {len(select.layer_set.layers) if hasattr(select.layer_set, 'layers') else 'specified'}")
    elif select.layer_expr:
        steps.append("Layers: filtered")
    
    # Filters
    if select.where:
        steps.append("Filters: WHERE conditions")
    
    # Compute
    if select.compute:
        compute_names = [c.name for c in select.compute]
        uq_enabled = any(c.uncertainty for c in select.compute)
        uq_marker = " (with UQ)" if uq_enabled else ""
        steps.append(f"Compute: {len(select.compute)} measure(s){uq_marker} [{', '.join(compute_names[:3])}{'...' if len(compute_names) > 3 else ''}]")
    
    # Query-level UQ
    if hasattr(select, "uq_config") and select.uq_config and select.uq_config.method:
        method = select.uq_config.method
        n_samples = select.uq_config.n_samples or 50
        steps.append(f"UQ: {method} (n={n_samples})")
    
    # Grouping
    if select.group_by:
        grouping_desc = ", ".join(select.group_by)
        steps.append(f"Grouping: by {grouping_desc}")
        if select.limit_per_group:
            steps.append(f"  Top-k: {select.limit_per_group} per group")
    
    # Coverage
    if select.coverage_mode:
        coverage_desc = select.coverage_mode
        if select.coverage_k:
            coverage_desc += f" (k={select.coverage_k})"
        elif select.coverage_p:
            coverage_desc += f" (p={select.coverage_p})"
        steps.append(f"Coverage: {coverage_desc}")
    
    # Post-processing
    post_ops = []
    if select.mutate_specs:
        post_ops.append(f"mutate({len(select.mutate_specs)})")
    if select.aggregate_specs:
        post_ops.append(f"aggregate({len(select.aggregate_specs)})")
    if select.summarize_aggs:
        post_ops.append(f"summarize({len(select.summarize_aggs)})")
    if select.rank_specs:
        post_ops.append(f"rank({len(select.rank_specs)})")
    if post_ops:
        steps.append(f"Post-processing: {', '.join(post_ops)}")
    
    # Ordering
    if select.order_by:
        order_keys = [o.key for o in select.order_by]
        steps.append(f"Order: {', '.join(order_keys[:2])}{'...' if len(order_keys) > 2 else ''}")
    
    # Limit
    if select.limit:
        steps.append(f"Limit: {select.limit}")
    
    # Explain
    if select.explain_spec:
        steps.append("Explain: enrich with explanations")
    
    logger.info("Query pipeline:")
    for step in steps:
        logger.info(f"  • {step}")


def execute_ast(
    network: Any,
    query: Query,
    params: Optional[Dict[str, Any]] = None,
    progress: bool = True,
    explain_plan: bool = False,
    planner_config: Optional[Dict[str, Any]] = None,
) -> Union[QueryResult, ExecutionPlan]:
    """Execute an AST query on a multilayer network.

    Args:
        network: Multilayer network object
        query: Query AST
        params: Parameter bindings
        progress: If True, log progress messages during query execution (default: True)
        explain_plan: If True, populate result.meta["plan"] with execution plan
        planner_config: Optional planner configuration dict

    Returns:
        QueryResult or ExecutionPlan (if explain=True)
    """
    params = params or {}
    logger = logging.getLogger(__name__)
    
    # Create plan if planner is enabled
    planned_query = None
    if planner_config or explain_plan:
        from .planner import plan_query
        from .errors import DslError
        
        try:
            planned_query = plan_query(query, network, params, planner_config)
        except DslError:
            # Re-raise DSL-specific errors (these are actionable user errors)
            raise
        except Exception as e:
            # If planning fails due to unexpected error, log warning and continue
            logger.warning(f"Query planning failed: {e}. Continuing without planner.")
            planned_query = None

    # Check for provenance configuration in query
    provenance_config = getattr(query.select, "provenance_config", None)
    use_new_provenance = (
        provenance_config and provenance_config.get("mode") == "replayable"
    )

    if use_new_provenance:
        # Use new provenance schema
        from py3plex.provenance.schema import (
            create_provenance_record,
            ProvenanceMode,
            CaptureMethod,
            should_capture_inline,
        )
        from py3plex.provenance.capture import capture_network
        from py3plex.dsl.serializer import serialize_query
        from py3plex.dsl.provenance import (
            network_fingerprint,
            ast_fingerprint,
            ast_summary,
        )

        # Get provenance parameters
        capture_method_str = provenance_config.get("capture", "auto")
        max_bytes = provenance_config.get("max_bytes")
        base_seed = provenance_config.get("seed")

        # Map capture method string to enum
        capture_method_map = {
            "auto": CaptureMethod.AUTO,
            "fingerprint": CaptureMethod.FINGERPRINT_ONLY,
            "snapshot": CaptureMethod.SNAPSHOT_GRAPH,
            "delta": CaptureMethod.DELTA_FROM_DATASET,
        }
        capture_method = capture_method_map.get(capture_method_str, CaptureMethod.AUTO)

        # Capture network fingerprint
        net_fingerprint = network_fingerprint(network)

        # Decide whether to capture inline
        snapshot_data = None
        if capture_method == CaptureMethod.AUTO:
            # Auto-decide based on size
            if should_capture_inline(
                net_fingerprint["node_count"], net_fingerprint["edge_count"]
            ):
                capture_method = CaptureMethod.SNAPSHOT_GRAPH
            else:
                capture_method = CaptureMethod.FINGERPRINT_ONLY

        # Capture network snapshot if needed
        if capture_method == CaptureMethod.SNAPSHOT_GRAPH:
            network_capture = capture_network(network, include_attributes=True)
            snapshot_data = network_capture.to_dict()

        # Serialize AST for replay
        ast_serialized = serialize_query(query)

        # Create provenance record
        prov_record = create_provenance_record(
            mode=ProvenanceMode.REPLAYABLE,
            engine="dsl_v2_executor",
            target=(
                query.select.target.value
                if hasattr(query.select.target, "value")
                else str(query.select.target)
            ),
            ast_hash=ast_fingerprint(query),
            ast_summary=ast_summary(query),
            network_fingerprint=net_fingerprint,
            ast_serialized=ast_serialized,
            params=params,
            capture_method=capture_method,
            snapshot_data=snapshot_data,
            base_seed=base_seed,
            randomness_used=False,  # Will be updated if UQ is used
        )

        # Track timing
        start_time = time.monotonic()
    else:
        # Use legacy provenance builder
        provenance_builder = ProvenanceBuilder("dsl_v2_executor")
        provenance_builder.start_timer()
        provenance_builder.set_network(network)
        provenance_builder.set_query_ast(query)
        provenance_builder.set_params(params)

    if progress:
        logger.info("Starting DSL query execution")

    # Step 1: Parameter binding
    stage_start = time.monotonic()
    if progress:
        logger.info("Step 1: Binding parameters")
    bound_query = _bind_parameters(query, params)
    
    if progress:
        # Show query pipeline summary after binding
        _log_query_summary(bound_query.select, logger)

    if use_new_provenance:
        bind_time = (time.monotonic() - stage_start) * 1000
        prov_record.performance["bind_parameters"] = bind_time
    else:
        provenance_builder.record_stage(
            "bind_parameters", (time.monotonic() - stage_start) * 1000
        )

    # Step 2: Check for EXPLAIN mode
    if bound_query.explain:
        if progress:
            logger.info("Step 2: Building execution plan (EXPLAIN mode)")
        # EXPLAIN mode doesn't execute, so return plan without provenance
        return _build_execution_plan(network, bound_query)

    # Step 3: Check for windowed query
    if bound_query.select.window_spec is not None:
        # Execute windowed query
        if progress:
            logger.info("Step 2: Executing windowed query")
        result = _execute_windowed_query(
            network, bound_query, params, progress=progress
        )
        # Add provenance to windowed result
        if use_new_provenance:
            prov_record.performance["total_ms"] = (time.monotonic() - start_time) * 1000
            result.meta["provenance"] = prov_record.to_dict()
        else:
            result.meta["provenance"] = provenance_builder.build()
        return result

    # Step 4: Wrap network in temporal view if needed
    stage_start = time.monotonic()
    if progress:
        logger.info("Step 2: Applying temporal context (if needed)")
    actual_network = _apply_temporal_context(
        network, bound_query.select.temporal_context
    )

    if use_new_provenance:
        prov_record.performance["temporal_context"] = (
            time.monotonic() - stage_start
        ) * 1000
    else:
        provenance_builder.record_stage(
            "temporal_context", (time.monotonic() - stage_start) * 1000
        )

    # Step 5: Execute SELECT statement (pass params for dynamic resolution)
    if progress:
        logger.info("Step 3: Executing SELECT statement")

    if use_new_provenance:
        # Pass provenance record instead of builder
        result = _execute_select(
            actual_network,
            bound_query.select,
            params,
            progress=progress,
            provenance_record=prov_record,
        )

        # Finalize provenance
        prov_record.performance["total_ms"] = (time.monotonic() - start_time) * 1000
        result.meta["provenance"] = prov_record.to_dict()
    else:
        result = _execute_select(
            actual_network,
            bound_query.select,
            params,
            progress=progress,
            provenance_builder=provenance_builder,
        )

        # Finalize and attach provenance
        prov_dict = provenance_builder.build()
        
        # Add plan metadata if planner was used
        if planned_query:
            prov_dict["query"]["plan_hash"] = planned_query.plan_hash
            prov_dict["backend"]["cache"] = {}  # Will be populated during execution
            prov_dict["performance"]["plan_ms"] = planned_query.plan_meta.get("plan_time_ms", 0)
            
            # Add plan to result metadata if explain_plan is True
            if explain_plan:
                result.meta["plan"] = planned_query.to_dict()
        
        # Merge UQ provenance if it was set
        if hasattr(provenance_builder, '_uq_provenance'):
            prov_dict["uq"] = provenance_builder._uq_provenance
        
        result.meta["provenance"] = prov_dict
    # Step 6: Handle sensitivity analysis if requested
    if bound_query.select.sensitivity_spec is not None:
        if progress:
            logger.info("Step 4: Running sensitivity analysis")

        # Import sensitivity module
        from py3plex.sensitivity import run_sensitivity_analysis

        sensitivity_spec = bound_query.select.sensitivity_spec

        # Create query executor closure
        def query_executor(net):
            """Execute query on a network."""
            # Clone the query but remove sensitivity spec to avoid recursion
            query_copy = copy.deepcopy(bound_query)
            query_copy.select.sensitivity_spec = None
            return _execute_select(
                net,
                query_copy.select,
                params,
                progress=False,  # Suppress progress logs for perturbed runs
                provenance_builder=None,  # No provenance for intermediate runs
            )

        # Run sensitivity analysis
        sensitivity_result = run_sensitivity_analysis(
            network=actual_network,
            query_executor=query_executor,
            query_ast=bound_query,
            perturb=sensitivity_spec.perturb,
            grid=sensitivity_spec.grid,
            n_samples=sensitivity_spec.n_samples,
            seed=sensitivity_spec.seed,
            metrics=sensitivity_spec.metrics,
            scope=sensitivity_spec.scope,
            **sensitivity_spec.kwargs,
        )

        # Attach sensitivity results to query result
        result.sensitivity_result = sensitivity_result
        result.meta["sensitivity"] = sensitivity_result.to_dict()

        # Update provenance to include sensitivity info
        if "provenance" in result.meta:
            result.meta["provenance"]["sensitivity"] = sensitivity_spec.to_dict()

    # Step 7: Handle contract evaluation if specified
    if bound_query.select.contract_spec is not None:
        if progress:
            logger.info("Step 5: Evaluating robustness contract")
        
        # Import contract evaluation engine
        from py3plex.contracts.engine import evaluate_contract
        from py3plex.dsl.builder import QueryBuilder
        
        # Infer conclusion type from query structure
        conclusion_type = _infer_conclusion_type(bound_query.select)
        top_k = bound_query.select.limit
        
        # Infer metric from computed measures
        metric = None
        if bound_query.select.compute:
            metric = bound_query.select.compute[0].name
        
        # Create a QueryBuilder from the SelectStmt for re-execution
        # We need to pass the original query builder that can be re-executed
        # For now, we'll create a minimal wrapper
        class QueryBuilderWrapper:
            def __init__(self, select_stmt):
                self._select = select_stmt
            
            def execute(self, network):
                return _execute_select(network, self._select, params, progress=False)
        
        query_builder_wrapper = QueryBuilderWrapper(bound_query.select)
        
        # Evaluate contract
        contract_result = evaluate_contract(
            baseline_result=result,
            contract=bound_query.select.contract_spec.contract,
            network=actual_network,
            query_builder=query_builder_wrapper,
            conclusion_type=conclusion_type,
            top_k=top_k,
            metric=metric,
        )
        
        # Check if contract failed in hard mode
        if bound_query.select.contract_spec.contract.mode == "hard" and not contract_result.contract_ok:
            # Raise exception in hard mode
            from py3plex.contracts.failure_modes import FailureMode
            
            class ContractViolation(Exception):
                """Contract violation exception (hard mode)."""
                def __init__(self, contract_result):
                    self.contract_result = contract_result
                    super().__init__(f"Contract violated: {contract_result.failure_mode.value if contract_result.failure_mode else 'unknown'}")
            
            raise ContractViolation(contract_result)
        
        # Return ContractResult in soft mode (or if passed)
        return contract_result

    return result


def _infer_conclusion_type(select: SelectStmt) -> str:
    """Infer conclusion type from SELECT statement.
    
    Returns:
        "top_k", "ranking", "community", or "general"
    """
    if select.target == Target.COMMUNITIES:
        return "community"
    
    if select.limit is not None and select.order_by:
        return "top_k"
    
    if select.order_by:
        return "ranking"
    
    return "general"


def _apply_temporal_context(network: Any, temporal_context: Optional[TemporalContext]) -> Any:
    """Apply temporal filtering to network if temporal context exists.

    Args:
        network: Base multilayer network
        temporal_context: Optional temporal context from query

    Returns:
        TemporalMultinetView if temporal context exists, otherwise original network
    """
    if temporal_context is None:
        return network

    # Import here to avoid circular dependencies
    from py3plex.temporal_view import TemporalMultinetView

    # Create temporal view
    view = TemporalMultinetView(network)

    # Apply temporal slice based on context kind
    if temporal_context.kind == "at":
        # Point-in-time snapshot
        if temporal_context.t0 is not None:
            return view.snapshot_at(temporal_context.t0)
        else:
            raise DslExecutionError("AT clause requires a timestamp")

    elif temporal_context.kind == "during":
        # Time range
        return view.with_slice(temporal_context.t0, temporal_context.t1)

    else:
        raise DslExecutionError(
            f"Unknown temporal context kind: {temporal_context.kind}"
        )

    return view


def _execute_windowed_query(
    network: Any,
    query: Query,
    params: Optional[Dict[str, Any]] = None,
    progress: bool = True,
) -> QueryResult:
    """Execute a windowed query over a temporal network.

    Args:
        network: Network (should be TemporalMultiLayerNetwork or convertible)
        query: Query with window_spec
        params: Parameter bindings
        progress: If True, log progress messages during query execution (default: True)

    Returns:
        QueryResult with windowed results

    Raises:
        DslExecutionError: If network doesn't support windowing or window spec is invalid
    """
    logger = logging.getLogger(__name__)
    from py3plex.temporal_utils_extended import parse_duration_string

    window_spec = query.select.window_spec

    # Check if network supports windowing
    if not hasattr(network, "window_iter"):
        # Try to convert to TemporalMultiLayerNetwork
        try:
            from py3plex.core.temporal_multinet import TemporalMultiLayerNetwork

            if isinstance(network, TemporalMultiLayerNetwork):
                # Already temporal
                pass
            else:
                raise DslExecutionError(
                    "Windowed queries require a TemporalMultiLayerNetwork. "
                    "Use TemporalMultiLayerNetwork.from_multilayer_network() to convert."
                )
        except ImportError:
            raise DslExecutionError(
                "TemporalMultiLayerNetwork not available. "
                "Windowed queries require py3plex.core.temporal_multinet module."
            )

    # Parse window size and step (convert duration strings to numeric)
    try:
        window_size = parse_duration_string(window_spec.window_size)
        step = parse_duration_string(window_spec.step) if window_spec.step else None
    except ValueError as e:
        raise DslExecutionError(f"Invalid window specification: {e}")

    # Collect results from each window
    window_results = []

    if progress:
        logger.info(
            f"Processing windowed query (window_size={window_size}, step={step})"
        )

    # Iterate over windows
    window_idx = 0
    for t_start, t_end, window_net in network.window_iter(
        window_size=window_size,
        step=step,
        start=window_spec.start,
        end=window_spec.end,
        return_type="snapshot",
    ):
        if progress:
            logger.info(f"Processing window {window_idx + 1}: [{t_start}, {t_end}]")

        # Execute query on this window
        # Create a copy of the select statement without the window spec
        window_select = copy.deepcopy(query.select)
        window_select.window_spec = None

        # Apply temporal context if specified
        actual_window_net = _apply_temporal_context(
            window_net, window_select.temporal_context
        )

        # Execute on this window (suppress sub-query progress to avoid clutter)
        window_result = _execute_select(
            actual_window_net, window_select, params, progress=False
        )

        # Add window metadata
        window_result.meta["window_start"] = t_start
        window_result.meta["window_end"] = t_end

        window_results.append(window_result)
        window_idx += 1

    if progress:
        logger.info(f"Processed {window_idx} windows")

    # Aggregate results based on aggregation mode
    aggregation = window_spec.aggregation

    if aggregation == "list":
        # Return list of results (default)
        # Wrap in a container QueryResult
        return QueryResult(
            target=query.select.target.value,
            items=window_results,
            attributes={},
            meta={
                "dsl_version": "2.0",
                "windowed": True,
                "window_count": len(window_results),
                "aggregation": "list",
            },
        )

    elif aggregation == "concat":
        # Concatenate all window results into a single result
        try:
            import pandas as pd

            # Convert each window result to DataFrame
            dfs = []
            for window_result in window_results:
                df = window_result.to_pandas()
                # Add window columns
                df["window_start"] = window_result.meta.get("window_start")
                df["window_end"] = window_result.meta.get("window_end")
                dfs.append(df)

            # Concatenate all DataFrames
            if dfs:
                combined_df = pd.concat(dfs, ignore_index=True)

                # Convert back to QueryResult format
                # Extract items (nodes or edges)
                id_col = "id" if "id" in combined_df.columns else combined_df.columns[0]
                items = combined_df[id_col].tolist()

                # Extract attributes (including window columns)
                attributes = {}
                for col in combined_df.columns:
                    if col != id_col:
                        attributes[col] = dict(
                            zip(combined_df[id_col], combined_df[col])
                        )

                return QueryResult(
                    target=query.select.target.value,
                    items=items,
                    attributes=attributes,
                    meta={
                        "dsl_version": "2.0",
                        "windowed": True,
                        "window_count": len(window_results),
                        "aggregation": "concat",
                    },
                )
            else:
                return QueryResult(
                    target=query.select.target.value,
                    items=[],
                    attributes={},
                    meta={
                        "dsl_version": "2.0",
                        "windowed": True,
                        "window_count": 0,
                        "aggregation": "concat",
                    },
                )
        except ImportError:
            raise DslExecutionError(
                "Concatenation aggregation requires pandas. "
                "Install pandas or use aggregation='list'."
            )

    else:
        raise DslExecutionError(
            f"Unknown aggregation mode: '{aggregation}'. "
            f"Supported modes: 'list', 'concat'"
        )


def _bind_parameters(query: Query, params: Dict[str, Any]) -> Query:
    """Bind parameters in the query AST.

    Traverses the AST and replaces ParamRef nodes with actual values.
    """
    # Create a deep copy of the query to avoid mutating the original
    bound_query = copy.deepcopy(query)

    # Bind limit parameter if it's a ParamRef
    if bound_query.select and bound_query.select.limit is not None:
        bound_query.select.limit = _resolve_param(bound_query.select.limit, params)

    # Note: WHERE conditions are resolved dynamically during evaluation
    # This allows for more flexible parameter handling
    return bound_query


def _resolve_param(value: Any, params: Dict[str, Any]) -> Any:
    """Resolve a value, replacing ParamRef with actual value if needed."""
    if isinstance(value, ParamRef):
        if value.name not in params:
            raise ParameterMissingError(value.name, list(params.keys()))
        return params[value.name]
    return value


def _build_execution_plan(network: Any, query: Query) -> ExecutionPlan:
    """Build an execution plan for EXPLAIN queries."""
    steps: List[PlanStep] = []
    warnings: List[str] = []

    select = query.select

    # Get node/edge counts for complexity estimation
    node_count = 0
    edge_count = 0
    if hasattr(network, "core_network") and network.core_network:
        node_count = network.core_network.number_of_nodes()
        edge_count = network.core_network.number_of_edges()

    # Step 1: Target selection
    if select.target == Target.NODES:
        steps.append(
            PlanStep(f"Select all nodes from network", f"O(|V|) = O({node_count})")
        )
    else:
        steps.append(
            PlanStep(f"Select all edges from network", f"O(|E|) = O({edge_count})")
        )

    # Step 2: Layer filtering
    if select.layer_set is not None:
        # New style: LayerSet
        layer_desc = f"<LayerSet: {select.layer_set._repr_expr(select.layer_set.expr)}>"
        steps.append(
            PlanStep(
                f"Filter by layers: {layer_desc}",
                "O(|V|)" if select.target == Target.NODES else "O(|E|)",
            )
        )
    elif select.layer_expr:
        # Old style: LayerExprBuilder
        layer_names = [t.name for t in select.layer_expr.terms]
        steps.append(
            PlanStep(
                f"Filter by layers: {', '.join(layer_names)}",
                "O(|V|)" if select.target == Target.NODES else "O(|E|)",
            )
        )

    # Step 3: Condition filtering
    if select.where:
        steps.append(
            PlanStep(
                f"Apply WHERE conditions ({len(select.where.atoms)} conditions)",
                "O(|V|)" if select.target == Target.NODES else "O(|E|)",
            )
        )

    # Step 4: Compute measures
    for compute in select.compute:
        complexity = _get_measure_complexity(compute.name, node_count, edge_count)
        steps.append(
            PlanStep(
                f"Compute {compute.name}"
                + (f" AS {compute.alias}" if compute.alias else ""),
                complexity,
            )
        )

        # Add warnings for expensive operations
        if compute.name in ("betweenness_centrality", "betweenness"):
            if node_count > 10000:
                warnings.append(
                    f"Graph has ~{node_count} nodes; betweenness_centrality might be slow. "
                    "Consider sampling or approximate methods."
                )

    # Step 5: Grouping and coverage
    if select.group_by:
        steps.append(
            PlanStep(f"Group results by: {', '.join(select.group_by)}", "O(n)")
        )

    if select.limit_per_group is not None:
        steps.append(
            PlanStep(f"Apply top-{select.limit_per_group} per group", "O(n log n)")
        )

    if select.coverage_mode:
        mode_desc = select.coverage_mode
        if select.coverage_k is not None:
            mode_desc = f"{select.coverage_mode} (k={select.coverage_k})"
        steps.append(
            PlanStep(
                f"Apply coverage filter across groups (mode='{mode_desc}')", "O(n)"
            )
        )

    # Step 6: Ordering (when not using grouping)
    if select.order_by and not select.group_by:
        keys = [f"{o.key} {'DESC' if o.desc else 'ASC'}" for o in select.order_by]
        steps.append(PlanStep(f"Order by: {', '.join(keys)}", "O(n log n)"))

    # Step 7: Limit
    if select.limit:
        steps.append(PlanStep(f"Limit to {select.limit} results", "O(1)"))

    return ExecutionPlan(steps=steps, warnings=warnings)


def _get_measure_complexity(measure: str, n: int, m: int) -> str:
    """Get complexity estimate for a measure."""
    complexities = {
        "degree": f"O(|V|) = O({n})",
        "degree_centrality": f"O(|V|) = O({n})",
        "betweenness_centrality": f"O(|V||E|) = O({n * m})",
        "betweenness": f"O(|V||E|) = O({n * m})",
        "closeness_centrality": f"O(|V|²) = O({n * n})",
        "closeness": f"O(|V|²) = O({n * n})",
        "eigenvector_centrality": f"O(|V| + |E|) iterations = O({n + m})",
        "eigenvector": f"O(|V| + |E|) iterations = O({n + m})",
        "pagerank": f"O(|V| + |E|) iterations = O({n + m})",
        "clustering": f"O(|V| * d²) where d=avg degree",
        "communities": f"O(|V| log |V|)",
        "community": f"O(|V| log |V|)",
    }
    return complexities.get(measure, "Unknown")


def _ensure_attribute(
    attr_name: str,
    attributes: Dict[str, Dict],
    items: List[Any],
    network: Any,
    G: nx.Graph,
    select: SelectStmt,
    auto_compute: bool = True,
) -> None:
    """Ensure that an attribute exists in the attributes dict.

    This implements smart defaults by auto-computing centrality metrics
    when they are referenced but not yet computed.

    Supports selector syntax like:
        - metric__mean
        - metric__std
        - metric__ci95__low

    Args:
        attr_name: The attribute name to ensure exists (may include selector)
        attributes: The attributes dictionary (modified in place)
        items: List of items (nodes or edges)
        network: Multilayer network
        G: Core network graph
        select: SELECT statement
        auto_compute: If True, auto-compute recognized centralities

    Raises:
        UnknownAttributeError: If attribute is not found and cannot be auto-computed
    """
    # Handle selector syntax (e.g., "degree__mean", "degree__ci95__low")
    # Strip selector to get base metric name
    if "__" in attr_name:
        base_metric = attr_name.split("__", 1)[0]
    else:
        base_metric = attr_name

    # Check if base attribute already exists
    if base_metric in attributes:
        return

    # For edges, check if this is an edge data attribute (like "weight")
    # Don't try to auto-compute centralities for edge attributes
    if select.target == Target.EDGES:
        # Check if attribute exists in edge data
        for item in items:
            if isinstance(item, tuple) and len(item) >= 3 and isinstance(item[2], dict):
                if base_metric in item[2]:
                    # This is a valid edge attribute, don't auto-compute
                    return

    # Check if this is a known centrality that can be auto-computed
    if auto_compute and base_metric in CENTRALITY_ALIASES:
        # Get the canonical metric name
        metric_name = CENTRALITY_ALIASES[base_metric]

        # Auto-compute the centrality
        if select.target == Target.NODES:
            try:
                # Create subgraph for computation
                subgraph = G.subgraph([item for item in items if item in G]).copy()

                # Get measure function
                measure_fn = measure_registry.get(metric_name)
                
                # Check algorithm compatibility
                diagnostics = _check_algorithm_compatibility(
                    network,
                    measure_fn,
                    compute_item=None if select.uq_config is None else ComputeItem(
                        name=metric_name,
                        uncertainty=True,
                        method=select.uq_config.method,
                    ),
                    seed=select.uq_config.seed if select.uq_config else None,
                )
                
                # Handle compatibility errors
                errors = [d for d in diagnostics if d.severity.value == 'error']
                if errors:
                    raise AlgorithmCompatibilityError(diagnostics, algo_name=metric_name)

                # Check if query has UQ config - if so, compute with uncertainty
                if select.uq_config is not None:
                    # Create a ComputeItem from the query-level UQ config
                    compute_item = ComputeItem(
                        name=metric_name,
                        uncertainty=True,
                        method=select.uq_config.method,
                        n_samples=select.uq_config.n_samples,
                        ci=select.uq_config.ci,
                        random_state=select.uq_config.seed,
                        # Extract kwargs for bootstrap and null model params
                        bootstrap_unit=select.uq_config.kwargs.get("bootstrap_unit"),
                        bootstrap_mode=select.uq_config.kwargs.get("bootstrap_mode"),
                        n_null=select.uq_config.kwargs.get("n_null"),
                        null_model=select.uq_config.kwargs.get("null_model"),
                    )
                    values = _compute_measure_with_uncertainty(
                        network, compute_item, measure_fn, subgraph, items, select
                    )
                else:
                    # Compute deterministically
                    values = measure_fn(subgraph, items)

                # Store with the base metric name (without selector)
                attributes[base_metric] = values

                # Also mark that this was implicitly computed
                # (for potential use in explain() in the future)
                return
            except Exception as e:
                # If auto-compute fails, fall through to error
                logging.getLogger(__name__).debug(
                    f"Failed to auto-compute '{base_metric}': {e}"
                )

    # Attribute not found and cannot be auto-computed
    # Build list of available attributes
    available = list(attributes.keys())

    # Add known centrality metrics that could be auto-computed
    available.extend(CENTRALITY_ALIASES.keys())

    # Also check for node attributes in the graph
    if select.target == Target.NODES and len(items) > 0:
        # Get node attributes from first item if it exists in graph
        first_item = items[0]
        if first_item in G:
            node_attrs = list(G.nodes[first_item].keys())
            available.extend(node_attrs)

    # Remove duplicates and sort
    available = sorted(set(available))

    # Raise error with helpful suggestions
    raise UnknownAttributeError(attr_name, available)


def _compute_communities_with_uncertainty(
    network: Any,
    compute_item: ComputeItem,
    items: List[Any],
) -> Dict[Any, Any]:
    """Compute community assignments with uncertainty quantification.
    
    This function generates an ensemble of community partitions using
    different resampling strategies, then returns probabilistic community
    memberships along with uncertainty metrics.
    
    Args:
        network: Multilayer network
        compute_item: ComputeItem with uncertainty configuration
        items: List of nodes to compute communities for
        
    Returns:
        Dictionary with special structure for probabilistic communities:
        - For each node: Dict with 'mean' (hard label), 'probs' (membership distribution),
          'entropy', 'confidence', etc.
    """
    from py3plex.uncertainty import (
        generate_community_ensemble,
        ProbabilisticCommunityResult
    )
    
    # Get UQ parameters
    method = compute_item.method or "seed"
    n_samples = compute_item.n_samples or 50
    random_state = compute_item.random_state
    
    # Map method names to ensemble generation methods
    method_map = {
        'seed': 'seed',
        'bootstrap': 'bootstrap',
        'perturbation': 'perturbation',
    }
    ensemble_method = method_map.get(method.lower(), 'seed')
    
    # Get method-specific parameters
    perturbation_rate = 0.1  # Default
    bootstrap_unit = compute_item.bootstrap_unit or 'edges'
    
    # Generate community ensemble
    try:
        dist = generate_community_ensemble(
            network=network,
            algorithm='louvain',  # Default to Louvain
            method=ensemble_method,
            n_samples=n_samples,
            seed=random_state,
            perturbation_rate=perturbation_rate,
            bootstrap_unit=bootstrap_unit,
            verbose=False,
        )
        
        # Wrap in ProbabilisticCommunityResult
        result = ProbabilisticCommunityResult(dist)
        
        # Get probabilistic information
        labels = result.labels
        probs = result.probs if not result.is_deterministic else None
        entropy = result.entropy if not result.is_deterministic else None
        confidence = result.confidence if not result.is_deterministic else None
        margin = result.margin if not result.is_deterministic else None
        
        # Build return dictionary with uncertainty structure
        # Each node gets a dict with mean (hard label), probs, entropy, confidence
        output = {}
        for node in items:
            if node in labels:
                node_dict = {
                    'mean': labels[node],  # Hard label (backward compatible)
                    'label': labels[node],  # Alias
                }
                
                if not result.is_deterministic:
                    # Add probabilistic information
                    node_dict['probs'] = probs.get(node, {})
                    node_dict['entropy'] = entropy.get(node, 0.0)
                    node_dict['confidence'] = confidence.get(node, 1.0)
                    node_dict['margin'] = margin.get(node, 1.0)
                    node_dict['std'] = 0.0  # Communities are categorical, no std
                    
                    # Add quantiles for consistency with numeric measures
                    # (though for communities, these are not meaningful)
                    node_dict['quantiles'] = {}
                    node_dict['certainty'] = confidence.get(node, 1.0)
                else:
                    # Deterministic case: perfect certainty
                    node_dict['std'] = 0.0
                    node_dict['entropy'] = 0.0
                    node_dict['confidence'] = 1.0
                    node_dict['margin'] = 1.0
                    node_dict['certainty'] = 1.0
                    node_dict['quantiles'] = {}
                
                output[node] = node_dict
            else:
                # Node not in partition (isolated?)
                output[node] = {
                    'mean': -1,
                    'label': -1,
                    'std': 0.0,
                    'entropy': 0.0,
                    'confidence': 1.0,
                    'margin': 1.0,
                    'certainty': 1.0,
                    'quantiles': {},
                }
        
        # Store the full result object in metadata for later access
        # This is a hack but allows us to pass the rich result through
        if hasattr(network, '_probabilistic_community_result'):
            # Store multiple results if needed
            if not isinstance(network._probabilistic_community_result, dict):
                network._probabilistic_community_result = {}
            network._probabilistic_community_result['latest'] = result
        else:
            network._probabilistic_community_result = result
        
        return output
    
    except Exception as e:
        # Fallback to deterministic if ensemble generation fails
        logging.getLogger(__name__).warning(
            f"Failed to generate community ensemble: {e}. "
            f"Falling back to deterministic community detection."
        )
        
        # Use standard Louvain on the network
        from py3plex.dsl.registry import measure_registry
        measure_fn = measure_registry.get('communities')
        
        G = network.core_network
        subgraph = G.subgraph([item for item in items if item in G]).copy()
        partition = measure_fn(subgraph, items)
        
        # Wrap in deterministic uncertainty format
        output = {}
        for node in items:
            label = partition.get(node, -1)
            output[node] = {
                'mean': label,
                'label': label,
                'std': 0.0,
                'entropy': 0.0,
                'confidence': 1.0,
                'margin': 1.0,
                'certainty': 1.0,
                'quantiles': {},
            }
        
        return output


def _get_measure_function(compute_item: ComputeItem, target: str = "nodes") -> Tuple[Callable, Optional[Dict], bool]:
    """Get the appropriate measure function (exact or approximate).
    
    This is the centralized dispatcher that selects between exact and approximate
    implementations based on the ComputeItem's approximation spec.
    
    Args:
        compute_item: ComputeItem with measure name and optional approximation spec
        target: Target type ("nodes" or "edges")
        
    Returns:
        Tuple of (measure_function, approx_metadata or None, is_fast_path)
        - measure_function: The function to call for computing the measure
        - approx_metadata: Dict with approximation metadata if approx is used, else None
        - is_fast_path: True if approximation is used (fast path)
        
    Raises:
        DslExecutionError: If approximation is requested but not available
    """
    approx_spec = compute_item.approx
    
    # If no approximation requested, return exact measure
    if approx_spec is None or not approx_spec.enabled:
        measure_fn = measure_registry.get(compute_item.name, target=target)
        return measure_fn, None, False
    
    # Approximation requested - check if available
    method = approx_spec.method
    if not measure_registry.has_approx(compute_item.name, method):
        raise DslExecutionError(
            f"Approximate method '{method}' not available for measure '{compute_item.name}'. "
            f"Available approximation methods: {_list_approx_methods(compute_item.name)}"
        )
    
    approx_fn = measure_registry.get_approx(compute_item.name, method)
    
    # Build approx metadata for provenance
    approx_metadata = {
        "measure": compute_item.name,
        "algorithm": f"{method}_{compute_item.name}",
        "method": method,
        "parameters": dict(approx_spec.params),
        "diagnostics_enabled": approx_spec.diagnostics,
    }
    
    return approx_fn, approx_metadata, True


def _list_approx_methods(measure_name: str) -> str:
    """Helper to list available approximation methods for a measure."""
    if hasattr(measure_registry, '_approx_methods') and measure_name in measure_registry._approx_methods:
        methods = list(measure_registry._approx_methods[measure_name].keys())
        return ", ".join(methods) if methods else "none"
    return "none"


def _compute_measure_with_uncertainty(
    network: Any,
    compute_item: ComputeItem,
    measure_fn: Any,
    subgraph: nx.Graph,
    items: List[Any],
    select: Optional[SelectStmt] = None,
) -> Dict[Any, Any]:
    """Compute a measure with optional uncertainty estimation.
    
    This function implements the canonical UQ resolution and validation pipeline:
    1. Resolve UQ config from all priority levels
    2. Compute metric with resolved config
    3. Validate result schema before returning
    4. Store resolved config in result metadata

    Args:
        network: Multilayer network
        compute_item: ComputeItem with uncertainty configuration
        measure_fn: Measure function to call
        subgraph: Subgraph to compute on
        items: List of items (nodes or edges)
        select: Optional SelectStmt for query-level UQ config

    Returns:
        Dictionary mapping items to values or UQ result dictionaries
        
    Raises:
        UQResolutionError: If UQ configuration is invalid
        UQSchemaValidationError: If result doesn't conform to canonical schema
    """
    # Step 1: Resolve UQ configuration using priority order
    query_uq_config = select.uq_config if select else None
    resolved_config = resolve_uq_config(
        compute_item=compute_item,
        query_uq_config=query_uq_config,
        metric_name=compute_item.name,
    )
    
    # If UQ is not enabled, return deterministic results
    if resolved_config is None:
        result = measure_fn(subgraph, items)
        # Handle tuple return from approximate methods (values, diagnostics)
        if isinstance(result, tuple) and len(result) == 2:
            values, diagnostics = result
            # Store diagnostics if requested (TODO: attach to metadata)
            # For now, just return the values
            return values
        else:
            return result
    
    # Log resolved configuration for debugging
    logger = logging.getLogger(__name__)
    logger.debug(
        f"UQ resolution for '{compute_item.name}': "
        f"method={resolved_config.method}, "
        f"n_samples={resolved_config.n_samples}, "
        f"seed={resolved_config.seed}, "
        f"provenance={resolved_config.provenance}"
    )
    
    # Import the uncertainty engines
    from py3plex.uncertainty import bootstrap_metric, null_model_metric
    
    # Create metric function that works with uncertainty engines
    def metric_fn_wrapper(net):
        """Wrapper that computes the measure on the network."""
        # Get the subgraph for the current network state
        if hasattr(net, "core_network"):
            g = net.core_network
        else:
            g = net
        
        # Only compute on nodes that exist in the graph
        valid_items = [item for item in items if item in g]
        if not valid_items:
            return {}
        
        sub = g.subgraph(valid_items).copy()
        result = measure_fn(sub, valid_items)
        # Handle tuple return from approximate methods
        if isinstance(result, tuple) and len(result) == 2:
            return result[0]  # Return only values for UQ, ignore diagnostics
        return result
    
    # Step 2: Choose the appropriate uncertainty estimation method
    method = resolved_config.method.lower()
    
    if method == "bootstrap":
        # Use bootstrap engine
        bootstrap_unit = resolved_config.kwargs.get("bootstrap_unit", "edges")
        bootstrap_mode = resolved_config.kwargs.get("bootstrap_mode", "resample")
        
        result = bootstrap_metric(
            graph=network,
            metric_fn=metric_fn_wrapper,
            n_boot=resolved_config.n_samples,
            unit=bootstrap_unit,
            mode=bootstrap_mode,
            ci=resolved_config.ci,
            random_state=resolved_config.seed,
        )
        
        # Step 3: Convert bootstrap result to canonical UQ schema
        uncertainty_dict = {}
        for i, item in enumerate(result["index"]):
            item_result = {
                "value": float(result["mean"][i]),
                "mean": float(result["mean"][i]),
                "std": float(result["std"][i]),
                "ci_low": float(result["ci_low"][i]),
                "ci_high": float(result["ci_high"][i]),
                "quantiles": {
                    (1 - resolved_config.ci) / 2: float(result["ci_low"][i]),
                    1 - (1 - resolved_config.ci) / 2: float(result["ci_high"][i]),
                },
                "n_samples": resolved_config.n_samples,  # Use resolved config, not result
                "method": "bootstrap",
                "seed": resolved_config.seed,
                "bootstrap_unit": bootstrap_unit,
                "bootstrap_mode": bootstrap_mode,
            }
            
            # Step 4: Validate against canonical schema
            try:
                validate_uq_result_schema(item_result, compute_item.name)
            except UQSchemaValidationError as e:
                logger.error(f"UQ schema validation failed for {compute_item.name}: {e}")
                raise
            
            uncertainty_dict[item] = item_result
        
        return uncertainty_dict
    
    elif method == "null_model":
        # Use null model engine
        n_null = resolved_config.kwargs.get("n_null", 200)
        null_model = resolved_config.kwargs.get("null_model")
        
        if not null_model:
            raise UQResolutionError(
                f"null_model method requires 'null_model' parameter for metric '{compute_item.name}'"
            )
        
        result = null_model_metric(
            graph=network,
            metric_fn=metric_fn_wrapper,
            n_null=n_null,
            model=null_model,
            random_state=resolved_config.seed,
        )
        
        # Convert null model result to canonical UQ schema
        uncertainty_dict = {}
        for i, item in enumerate(result["index"]):
            item_result = {
                "value": float(result["observed"][i]),
                "mean": float(result["observed"][i]),
                "std": float(result["std_null"][i]),
                "ci_low": None,  # Null model doesn't provide CI directly
                "ci_high": None,
                "quantiles": {},
                "n_samples": resolved_config.n_samples,  # Use resolved config
                "method": "null_model",
                "seed": resolved_config.seed,
                "null_model": result["model"],
                # Null model specific fields
                "mean_null": float(result["mean_null"][i]),
                "zscore": float(result["zscore"][i]),
                "pvalue": float(result["pvalue"][i]),
            }
            
            # Validate against canonical schema (allow no CI for null model)
            try:
                validate_uq_result_schema(item_result, compute_item.name, allow_degenerate=True)
            except UQSchemaValidationError as e:
                logger.error(f"UQ schema validation failed for {compute_item.name}: {e}")
                raise
            
            uncertainty_dict[item] = item_result
        
        return uncertainty_dict
    
    elif method in ["perturbation", "seed", "stratified_perturbation"]:
        # Use existing estimate_uncertainty (legacy) or stratified version
        resampling = _RESAMPLING_METHOD_MAP.get(
            method, ResamplingStrategy.PERTURBATION
        )
        
        # Estimate uncertainty
        result = estimate_uncertainty(
            network=network,
            metric_fn=metric_fn_wrapper,
            n_runs=resolved_config.n_samples,
            resampling=resampling,
            random_seed=resolved_config.seed,
        )
        
        # If result is a StatSeries, convert to dict format
        if isinstance(result, StatSeries):
            result_dict = result.to_dict()
            
            # Ensure all items conform to canonical schema
            for item, item_result in result_dict.items():
                if isinstance(item_result, dict):
                    # Add missing required fields
                    if "method" not in item_result:
                        item_result["method"] = method
                    if "seed" not in item_result and resolved_config.seed is not None:
                        item_result["seed"] = resolved_config.seed
                    if "n_samples" not in item_result:
                        item_result["n_samples"] = resolved_config.n_samples
                    
                    # Ensure ci_low/ci_high are present
                    if "ci_low" not in item_result or "ci_high" not in item_result:
                        quantiles = item_result.get("quantiles", {})
                        if quantiles:
                            sorted_qs = sorted(quantiles.keys())
                            if len(sorted_qs) >= 2:
                                item_result["ci_low"] = quantiles[sorted_qs[0]]
                                item_result["ci_high"] = quantiles[sorted_qs[-1]]
                    
                    # Validate
                    try:
                        validate_uq_result_schema(item_result, compute_item.name, allow_degenerate=True)
                    except UQSchemaValidationError as e:
                        logger.warning(f"UQ schema validation warning for {compute_item.name}: {e}")
                        # Don't fail on legacy results, just warn
            
            return result_dict
        else:
            # Wrap non-StatSeries result
            return result
    
    else:
        # Unknown method - should have been caught by validation, but handle gracefully
        logger.error(
            f"Unknown uncertainty method '{method}' for metric '{compute_item.name}'. "
            f"This should have been caught during resolution."
        )
        raise UQResolutionError(
            f"Unknown uncertainty method '{method}' for metric '{compute_item.name}'"
        )


# ============================================================================
# UQ Propagation Mode: Execute Entire Query Per Replicate
# ============================================================================

def _execute_with_uq_propagation(
    network: Any,
    select: SelectStmt,
    params: Optional[Dict[str, Any]] = None,
    progress: bool = True,
    provenance_builder: Optional[ProvenanceBuilder] = None,
    provenance_record: Optional[Any] = None,
) -> QueryResult:
    """Execute a query in propagate mode: run entire query per replicate and reduce.
    
    This implements end-to-end uncertainty propagation where the entire query
    (filtering, ordering, limiting) is executed independently for each replicate,
    then results are combined.
    
    Args:
        network: Multilayer network
        select: SELECT statement AST
        params: Parameter bindings
        progress: Whether to log progress
        provenance_builder: Optional provenance builder
        provenance_record: Optional provenance record
        
    Returns:
        QueryResult with p_present, p_selected, and UQ-aware metrics
    """
    logger = logging.getLogger(__name__)
    
    # Resolve UQ configuration
    from .uq_resolution import ResolvedUQConfig
    
    # Quick-resolve from query UQ config
    uq_config = select.uq_config
    if not uq_config or not uq_config.method or uq_config.mode != "propagate":
        # Should not reach here, but fallback to regular execution
        return _execute_select(
            network, select, params, progress,
            provenance_builder=provenance_builder,
            provenance_record=provenance_record
        )
    
    # Build resolved UQ config (simplified - actual resolution happens per metric)
    resolved_uq = ResolvedUQConfig(
        method=uq_config.method or "perturbation",
        n_samples=uq_config.n_samples or 50,
        ci=uq_config.ci or 0.95,
        seed=uq_config.seed,
        mode="propagate",
        keep_samples=uq_config.keep_samples if uq_config.keep_samples is not None else True,
        reduce=uq_config.reduce or "empirical",
        kwargs=uq_config.kwargs or {},
        context="query",
        enabled=True,
    )
    
    if progress:
        logger.info(f"UQ Propagation: Executing {resolved_uq.n_samples} replicates with method={resolved_uq.method}")
    
    # 1. Create replicate plan
    plan = _make_replicate_plan(network, resolved_uq)
    
    # 2. Execute each replicate
    replicate_results = []
    
    for ctx in plan:
        # Create replicate network
        rep_network = _create_replicate_network(network, ctx, resolved_uq)
        
        # Create a copy of select with UQ disabled inside replicate
        import copy as copy_module
        select_copy = copy_module.deepcopy(select)
        
        # Disable UQ for scalar execution (prevent nested UQ loops)
        if hasattr(select_copy, 'uq_config') and select_copy.uq_config:
            select_copy.uq_config = None
        
        # Disable UQ in compute items too
        if select_copy.compute:
            for compute_item in select_copy.compute:
                compute_item.uncertainty = False
                compute_item.method = None
                compute_item.n_samples = None
        
        # Execute scalar query on this replicate
        try:
            rep_result = _execute_select(
                rep_network,
                select_copy,
                params,
                progress=False,  # Suppress per-replicate logs
                provenance_builder=None,  # Don't track per-replicate provenance
                provenance_record=None,
            )
            # Attach replicate metadata
            rep_result.meta['replicate_id'] = ctx.replicate_id
            rep_result.meta['replicate_seed'] = ctx.replicate_seed
            replicate_results.append(rep_result)
        except Exception as e:
            logger.warning(f"Replicate {ctx.replicate_id} failed: {e}. Skipping.")
            continue
    
    if not replicate_results:
        # All replicates failed
        raise DslExecutionError("All replicates failed in propagate mode")
    
    if progress:
        logger.info(f"Completed {len(replicate_results)} replicates. Reducing results...")
    
    # 3. Reduce replicate results
    result = _reduce_replicate_results(
        replicate_results, resolved_uq, select, progress=progress
    )
    
    # 4. Attach provenance
    uq_provenance = {
        "enabled": True,
        "method": resolved_uq.method,
        "n_samples": len(replicate_results),
        "ci": resolved_uq.ci,
        "seed": resolved_uq.seed,
        "mode": "propagate",
        "keep_samples": resolved_uq.keep_samples,
        "reduce": resolved_uq.reduce,
        "plan": {
            "total_replicates": resolved_uq.n_samples,
            "successful_replicates": len(replicate_results),
            "method": resolved_uq.method,
        }
    }
    
    # Set UQ provenance in the provenance builder/record
    if provenance_record is not None:
        provenance_record.metadata["uq"] = uq_provenance
        # Don't build yet - let executor do it
    elif provenance_builder is not None:
        # Store UQ info separately so it can be merged at the top level
        # We'll manually add it after build() is called
        provenance_builder._uq_provenance = uq_provenance
        # Don't build yet - let executor do it
    else:
        # Create minimal provenance with UQ info
        result.meta["provenance"] = {
            "engine": "dsl_v2_executor",
            "uq": uq_provenance
        }
    
    return result


def _reduce_replicate_results(
    replicate_results: List[QueryResult],
    resolved_uq: 'ResolvedUQConfig',
    select: SelectStmt,
    progress: bool = True,
) -> QueryResult:
    """Reduce multiple replicate QueryResults into a single UQ-aware result.
    
    This computes:
    - p_present: fraction of replicates where item appears
    - p_selected: fraction of replicates where item is in final selection (after limit/top_k)
    - rank_uq: uncertainty over rankings
    - UQ-wrapped metrics using UQValue
    
    Args:
        replicate_results: List of QueryResult from each replicate
        resolved_uq: Resolved UQ configuration
        select: Original SELECT statement (to detect truncation)
        progress: Whether to log progress
        
    Returns:
        Combined QueryResult with UQ
    """
    logger = logging.getLogger(__name__)
    
    if not replicate_results:
        raise DslExecutionError("Cannot reduce zero replicate results")
    
    # Detect if query has truncation/selection (limit, top_k)
    has_selection = False
    selection_key = None
    selection_k = None
    
    if select.limit is not None:
        has_selection = True
        selection_k = select.limit
        # Find ordering key if present
        if select.order_by:
            selection_key = select.order_by[0].key
    elif hasattr(select, 'top_k_spec') and select.top_k_spec:
        has_selection = True
        selection_k = select.top_k_spec.k
        selection_key = select.top_k_spec.key
    
    # Get union of all items across replicates
    all_items = set()
    for rep_result in replicate_results:
        all_items.update(rep_result.items)
    
    # Sort for deterministic ordering
    all_items = sorted(list(all_items))
    
    # Determine target and metrics
    target = replicate_results[0].target
    all_metrics = set()
    for rep_result in replicate_results:
        all_metrics.update(rep_result.attributes.keys())
    all_metrics = sorted(list(all_metrics))
    
    # Initialize output structures
    attributes = {}
    
    # Import UQValue for aggregation
    from .uq_algebra import UQValue, convert_to_uqvalue
    
    # For each item, aggregate across replicates
    for item in all_items:
        # Count presence
        present_count = sum(1 for rep in replicate_results if item in rep.items)
        selected_count = 0
        rank_samples = []
        
        # Collect metric samples
        metric_samples = {metric: [] for metric in all_metrics}
        
        for rep_result in replicate_results:
            if item in rep_result.items:
                # Collect metric values
                for metric in all_metrics:
                    if metric in rep_result.attributes:
                        # Get value for this item
                        if isinstance(rep_result.attributes[metric], dict):
                            # Dict-style attributes
                            if item in rep_result.attributes[metric]:
                                val = rep_result.attributes[metric][item]
                                # Extract scalar value (mean if UQ dict)
                                if isinstance(val, dict) and 'mean' in val:
                                    metric_samples[metric].append(val['mean'])
                                else:
                                    metric_samples[metric].append(val)
                        elif isinstance(rep_result.attributes[metric], list):
                            # List-style attributes
                            try:
                                idx = rep_result.items.index(item)
                                val = rep_result.attributes[metric][idx]
                                if isinstance(val, dict) and 'mean' in val:
                                    metric_samples[metric].append(val['mean'])
                                else:
                                    metric_samples[metric].append(val)
                            except (ValueError, IndexError):
                                pass
                
                # Check if selected (if selection is present)
                if has_selection:
                    # Item is selected if it appears in result (after limit/top_k)
                    selected_count += 1
                    
                    # Try to get rank
                    if selection_key and selection_key in rep_result.attributes:
                        try:
                            idx = rep_result.items.index(item)
                            rank_samples.append(idx)
                        except ValueError:
                            pass
    
    # Build final attributes
    p_present_col = []
    p_selected_col = [] if has_selection else None
    rank_uq_col = [] if has_selection else None
    
    metric_cols = {metric: [] for metric in all_metrics}
    
    for item in all_items:
        # Compute p_present
        present_count = sum(1 for rep in replicate_results if item in rep.items)
        p_present = present_count / len(replicate_results)
        p_present_col.append(p_present)
        
        # Compute p_selected
        if has_selection:
            selected_count = sum(
                1 for rep in replicate_results
                if item in rep.items  # Simplified: in result = selected
            )
            p_selected = selected_count / len(replicate_results)
            p_selected_col.append(p_selected)
        
        # Build UQ for each metric
        for metric in all_metrics:
            samples = []
            for rep_result in replicate_results:
                if item in rep_result.items and metric in rep_result.attributes:
                    if isinstance(rep_result.attributes[metric], dict):
                        if item in rep_result.attributes[metric]:
                            val = rep_result.attributes[metric][item]
                            if isinstance(val, dict) and 'mean' in val:
                                samples.append(val['mean'])
                            else:
                                samples.append(val)
                    elif isinstance(rep_result.attributes[metric], list):
                        try:
                            idx = rep_result.items.index(item)
                            val = rep_result.attributes[metric][idx]
                            if isinstance(val, dict) and 'mean' in val:
                                samples.append(val['mean'])
                            else:
                                samples.append(val)
                        except (ValueError, IndexError):
                            pass
            
            # Convert samples to UQValue
            if samples:
                import numpy as np
                samples_arr = np.array(samples)
                mean_val = np.mean(samples_arr)
                std_val = np.std(samples_arr, ddof=1) if len(samples_arr) > 1 else 0.0
                
                # Compute quantiles
                ci_level = resolved_uq.ci
                quantiles_dict = {}
                if len(samples_arr) > 1:
                    quantiles_dict[0.025] = np.percentile(samples_arr, 2.5)
                    quantiles_dict[0.05] = np.percentile(samples_arr, 5.0)
                    quantiles_dict[0.5] = np.percentile(samples_arr, 50.0)
                    quantiles_dict[0.95] = np.percentile(samples_arr, 95.0)
                    quantiles_dict[0.975] = np.percentile(samples_arr, 97.5)
                
                # Create provenance
                from .uq_algebra import ProvenanceInfo, DistributionType
                prov = ProvenanceInfo(
                    method=resolved_uq.method,
                    n_samples=len(samples),
                    seed=resolved_uq.seed,
                )
                
                # Decide distribution type
                if resolved_uq.reduce == "gaussian":
                    dist_type = DistributionType.GAUSSIAN
                    keep_samples = False
                else:  # empirical
                    dist_type = DistributionType.EMPIRICAL
                    keep_samples = resolved_uq.keep_samples if resolved_uq.keep_samples is not None else True
                
                uq_value = UQValue(
                    distribution_type=dist_type,
                    mean=mean_val,
                    std=std_val,
                    quantiles=quantiles_dict,
                    samples=samples_arr if keep_samples else None,
                    provenance=prov,
                    effective_count=float(len(samples)),
                )
                metric_cols[metric].append(uq_value.to_dict())
            else:
                # No samples - use None or NaN
                metric_cols[metric].append(None)
        
        # Rank UQ (if applicable)
        if has_selection and rank_uq_col is not None:
            rank_samples_for_item = []
            for i, rep_result in enumerate(replicate_results):
                if item in rep_result.items:
                    try:
                        idx = rep_result.items.index(item)
                        rank_samples_for_item.append(idx)
                    except ValueError:
                        pass
            
            if rank_samples_for_item:
                import numpy as np
                samples_arr = np.array(rank_samples_for_item, dtype=float)
                mean_val = np.mean(samples_arr)
                std_val = np.std(samples_arr, ddof=1) if len(samples_arr) > 1 else 0.0
                
                # Compute quantiles
                quantiles_dict = {}
                if len(samples_arr) > 1:
                    quantiles_dict[0.025] = np.percentile(samples_arr, 2.5)
                    quantiles_dict[0.05] = np.percentile(samples_arr, 5.0)
                    quantiles_dict[0.5] = np.percentile(samples_arr, 50.0)
                    quantiles_dict[0.95] = np.percentile(samples_arr, 95.0)
                    quantiles_dict[0.975] = np.percentile(samples_arr, 97.5)
                
                # Create provenance
                from .uq_algebra import ProvenanceInfo, DistributionType
                prov = ProvenanceInfo(
                    method=resolved_uq.method,
                    n_samples=len(rank_samples_for_item),
                    seed=resolved_uq.seed,
                )
                
                rank_uq_value = UQValue(
                    distribution_type=DistributionType.EMPIRICAL,
                    mean=mean_val,
                    std=std_val,
                    quantiles=quantiles_dict,
                    samples=None,  # Don't store rank samples by default
                    provenance=prov,
                    effective_count=float(len(rank_samples_for_item)),
                )
                rank_uq_col.append(rank_uq_value.to_dict())
            else:
                rank_uq_col.append(None)
    
    # Assemble final QueryResult
    final_attributes = {}
    final_attributes['p_present'] = p_present_col
    
    if has_selection and p_selected_col:
        final_attributes['p_selected'] = p_selected_col
    
    if has_selection and rank_uq_col:
        final_attributes['rank_uq'] = rank_uq_col
    
    for metric, values in metric_cols.items():
        final_attributes[metric] = values
    
    # Create result
    result = QueryResult(
        target=target,
        items=all_items,
        attributes=final_attributes,
        meta={
            "dsl_version": "2.0",
            "uq_propagation": {
                "n_samples": len(replicate_results),
                "mode": "propagate",
                "selection": {
                    "has_topk": has_selection and hasattr(select, 'top_k_spec') and select.top_k_spec is not None,
                    "has_limit": select.limit is not None,
                    "key": selection_key if has_selection else None,
                    "k": selection_k if has_selection else None,
                },
                "p_present_column": "p_present",
                "p_selected_column": "p_selected" if has_selection else None,
                "rank_uq_column": "rank_uq" if has_selection else None,
            }
        }
    )
    
    return result


def _execute_select(
    network: Any,
    select: SelectStmt,
    params: Optional[Dict[str, Any]] = None,
    progress: bool = True,
    provenance_builder: Optional[ProvenanceBuilder] = None,
    provenance_record: Optional[Any] = None,
) -> QueryResult:
    """Execute a SELECT statement.

    Args:
        network: Multilayer network
        select: SELECT statement AST
        params: Parameter bindings for dynamic resolution
        progress: If True, log progress messages during query execution (default: True)
        provenance_builder: Optional legacy provenance builder for tracking execution
        provenance_record: Optional new provenance record for replayable mode
    """
    params = params or {}
    logger = logging.getLogger(__name__)

    # Helper function to record timing in either provenance system
    def _record_timing(stage_name: str, duration_ms: float):
        if provenance_record is not None:
            provenance_record.performance[stage_name] = duration_ms
        elif provenance_builder is not None:
            provenance_builder.record_stage(stage_name, duration_ms)

    # Create provenance builder if neither is provided (for standalone calls)
    if provenance_builder is None and provenance_record is None:
        provenance_builder = ProvenanceBuilder("dsl_v2_executor")
        provenance_builder.start_timer()
        provenance_builder.set_network(network)

    # Get core network
    if not hasattr(network, "core_network") or network.core_network is None:
        result = QueryResult(
            target=select.target.value,
            items=[],
            attributes={},
            meta={"dsl_version": "2.0", "warning": "Network has no core_network"},
        )
        if provenance_record is not None:
            result.meta["provenance"] = provenance_record.to_dict()
        elif provenance_builder is not None:
            result.meta["provenance"] = provenance_builder.build()
        return result

    G = network.core_network

    # Check if this is a propagate mode UQ query
    if hasattr(select, "uq_config") and select.uq_config:
        if select.uq_config.method and select.uq_config.mode == "propagate":
            if progress:
                logger.info("Detected propagate mode UQ query - routing to propagate executor")
            return _execute_with_uq_propagation(
                network, select, params, progress=progress,
                provenance_builder=provenance_builder,
                provenance_record=provenance_record
            )

    # Handle auto community detection for both COMMUNITIES and NODES targets
    if hasattr(select, "auto_community_config") and select.auto_community_config and select.auto_community_config.enabled:
        return _execute_auto_community(
            network, select, params, progress=progress,
            provenance_builder=provenance_builder,
            provenance_record=provenance_record
        )

    # Handle community queries specially
    if select.target == Target.COMMUNITIES:
        return _execute_community_select(network, select, params, progress=progress)

    # Check if this is a bridge query from communities
    if hasattr(select, "_from_communities") and select._from_communities is not None:
        return _execute_community_bridge(network, select, params, progress=progress)
    
    # Check if community detection with UQ is requested
    if hasattr(select, "community_config") and select.community_config:
        # Check if UQ is also requested
        if hasattr(select, "uq_config") and select.uq_config and select.uq_config.method:
            return _execute_nodes_with_community_uq(
                network, select, params, progress=progress,
                provenance_builder=provenance_builder,
                provenance_record=provenance_record
            )
        else:
            # Community detection without UQ (deterministic)
            return _execute_nodes_with_community(
                network, select, params, progress=progress,
                provenance_builder=provenance_builder,
                provenance_record=provenance_record
            )
    
    # Check if compositional UQ should be applied (aggregate/summarize/order_by/coverage with UQ)
    if should_apply_compositional_uq(select):
        if progress:
            logger.info("Detected compositional UQ query - routing to compositional UQ executor")
        return _execute_select_with_compositional_uq(
            network, select, params, progress=progress,
            provenance_builder=provenance_builder,
            provenance_record=provenance_record
        )
    
    # Check if selection query with UQ is requested
    if hasattr(select, "uq_config") and select.uq_config and select.uq_config.method:
        from .selection_uq import is_selection_query, execute_selection_with_uq
        
        if is_selection_query(select):
            if progress:
                logger.info("Detected selection query with UQ - routing to SelectionUQ")
            result = execute_selection_with_uq(
                network, select, params, progress=progress
            )
            # Add provenance
            if provenance_record is not None:
                provenance_record.metadata["randomness"] = {
                    "method": select.uq_config.method,
                    "noise_model": str(select.uq_config.kwargs.get("noise_model")) if select.uq_config.kwargs else None,
                    "n_samples": select.uq_config.n_samples,
                    "seed": select.uq_config.seed,
                }
                provenance_record.metadata["uq"] = {
                    "type": "selection",
                    "storage_mode": select.uq_config.kwargs.get("store", "sketch") if select.uq_config.kwargs else "sketch",
                    "ci_method": "wilson",
                }
                result.meta["provenance"] = provenance_record.to_dict()
            elif provenance_builder is not None:
                result.meta["provenance"] = provenance_builder.build()
            return result

    # Step 1: Get initial items
    stage_start = time.monotonic()
    if progress:
        logger.info(f"Step 3.1: Getting initial {select.target.value}")
    if select.target == Target.NODES:
        items = list(network.get_nodes())
    else:
        # Get edges with data to access attributes like weight
        items = list(network.get_edges(data=True))
    if progress:
        logger.info(f"Found {len(items)} initial {select.target.value}")
    _record_timing("get_items", (time.monotonic() - stage_start) * 1000)

    # Step 2: Apply layer filter
    stage_start = time.monotonic()
    if select.layer_set is not None:
        # New style: LayerSet with algebra
        if progress:
            logger.info("Step 3.2: Applying layer filter")
        active_layers = select.layer_set.resolve(network, strict=False, warn_empty=True)
        items = _filter_by_layers(items, active_layers, select.target)
        if progress:
            logger.info(
                f"Filtered to {len(items)} {select.target.value} in {len(active_layers)} layers"
            )
    elif select.layer_expr:
        # Old style: LayerExprBuilder compatibility
        if progress:
            logger.info("Step 3.2: Applying layer filter")
        active_layers = _evaluate_layer_expr(select.layer_expr, network)
        items = _filter_by_layers(items, active_layers, select.target)
        if progress:
            logger.info(
                f"Filtered to {len(items)} {select.target.value} in {len(active_layers)} layers"
            )
    _record_timing("filter_layers", (time.monotonic() - stage_start) * 1000)

    # Step 3: Apply WHERE conditions
    stage_start = time.monotonic()
    if select.where:
        if progress:
            logger.info("Step 3.3: Applying WHERE conditions")
        items = _filter_by_conditions(items, select.where, network, G, params)
        if progress:
            logger.info(f"Filtered to {len(items)} {select.target.value}")
    _record_timing("filter_where", (time.monotonic() - stage_start) * 1000)

    # Step 3.5: Apply post-filters (e.g., has_community with lambdas)
    if select.post_filters:
        if progress:
            logger.info("Step 3.3.5: Applying post-filters")
        items = _apply_post_filters(items, select.post_filters, network, G)
        if progress:
            logger.info(f"Filtered to {len(items)} {select.target.value}")

    # Optimization: Early LIMIT when ORDER BY uses existing attributes
    # This reduces the number of items before expensive compute operations
    early_limit_applied = False
    if (
        select.limit is not None
        and select.order_by
        and not select.group_by  # Only works for non-grouped queries
        and select.compute
    ):  # Only beneficial when we have compute operations

        # Check if all ORDER BY keys are available without computing
        # (i.e., they're not in the COMPUTE list)
        compute_names = {c.result_name for c in select.compute}
        order_keys_to_check = []
        for o in select.order_by:
            # Extract base key, handling "-degree" prefix and "__mean" suffix
            key = o.key.lstrip("-").split("__")[0]
            order_keys_to_check.append(key)

        # If ordering attributes are not being computed, check if they're available
        can_apply_early_limit = True
        if not set(order_keys_to_check).intersection(compute_names):
            # Check if attributes exist (e.g., "degree" from graph structure)
            for key in order_keys_to_check:
                # Check if this is a graph attribute that exists
                attr_available = False

                if select.target == Target.NODES and len(items) > 0:
                    # Check if it's a node attribute
                    first_item = items[0]
                    if first_item in G:
                        # Check node data
                        if key in G.nodes[first_item]:
                            attr_available = True
                        # Check if it's a special attribute like "layer" or "degree"
                        elif key == "layer" or key == "degree":
                            attr_available = True
                elif select.target == Target.EDGES and len(items) > 0:
                    # Check if it's an edge attribute
                    if (
                        isinstance(items[0], tuple)
                        and len(items[0]) >= 3
                        and isinstance(items[0][2], dict)
                    ):
                        if key in items[0][2]:
                            attr_available = True
                    # Check special edge attributes
                    elif key in ["source_layer", "target_layer", "layer", "weight"]:
                        attr_available = True

                if not attr_available:
                    can_apply_early_limit = False
                    break

            # If all ordering attributes are available, apply early limit
            if can_apply_early_limit:
                items = _apply_ordering(items, select.order_by, {})
                items = items[: select.limit]
                early_limit_applied = True

    # Step 4: Compute measures
    stage_start = time.monotonic()
    attributes: Dict[str, Dict] = {}
    
    # Track approximation usage for provenance (initialize before compute block)
    approx_used = []
    fast_path_enabled = False
    
    if select.compute:
        if progress:
            logger.info(f"Step 3.4: Computing {len(select.compute)} measure(s)")
        if select.target == Target.NODES:
            # Node measures - existing implementation
            # Create subgraph for computation
            subgraph = G.subgraph([item for item in items if item in G]).copy()

            # Build execution context for operators
            active_layers = None
            if select.layer_set is not None:
                # New style: LayerSet
                active_layers = list(
                    select.layer_set.resolve(network, strict=False, warn_empty=False)
                )
            elif select.layer_expr:
                # Old style: LayerExprBuilder
                active_layers = list(_evaluate_layer_expr(select.layer_expr, network))

            context = DSLExecutionContext(
                graph=network,
                current_layers=active_layers,
                current_nodes=items,
                params={},
            )
            
            for i, compute_item in enumerate(select.compute):
                if progress:
                    uq_info = _format_uq_info(compute_item)
                    logger.info(
                        f"  Computing {compute_item.name} ({i+1}/{len(select.compute)}){uq_info}"
                    )
                try:
                    # First, try to resolve from operator registry
                    operator = get_operator(compute_item.name)
                    if operator is not None:
                        # Call custom operator with context
                        result = operator.func(context)
                        result_name = compute_item.result_name

                        # Convert result to dict if it's not already
                        if isinstance(result, dict):
                            attributes[result_name] = (
                                _wrap_deterministic_uncertainty(result, items)
                                if compute_item.uncertainty
                                else result
                            )
                        else:
                            # If result is a scalar, assign it to all nodes
                            base = {node: result for node in items}
                            attributes[result_name] = (
                                _wrap_deterministic_uncertainty(base, items)
                                if compute_item.uncertainty
                                else base
                            )
                    else:
                        # Fall back to measure registry (built-in measures)
                        # Use dispatcher to get exact or approximate implementation
                        measure_fn, approx_metadata, is_fast_path = _get_measure_function(compute_item, target="nodes")
                        result_name = compute_item.result_name

                        # Track approximation usage
                        if approx_metadata is not None:
                            approx_used.append(approx_metadata)
                        if is_fast_path:
                            fast_path_enabled = True


                        
                        # Special handling for community detection with UQ
                        if compute_item.name in ['communities', 'community'] and compute_item.uncertainty:
                            values = _compute_communities_with_uncertainty(
                                network=network,
                                compute_item=compute_item,
                                items=items,
                            )
                        else:
                            # Standard uncertainty handling
                            values = _compute_measure_with_uncertainty(
                                network=network,
                                compute_item=compute_item,
                                measure_fn=measure_fn,
                                subgraph=subgraph,
                                items=items,
                                select=select,
                            )

                        attributes[result_name] = values
                except (UQResolutionError, UQSchemaValidationError):
                    # UQ errors should propagate (fail-fast)
                    raise
                except UnknownMeasureError:
                    # Re-raise unknown measure errors (they have helpful suggestions)
                    raise
                except Exception as e:
                    # Log specific error and continue with other measures
                    logging.getLogger(__name__).warning(
                        f"Error computing measure '{compute_item.name}': {e}"
                    )
                    attributes[compute_item.result_name] = {}
        else:
            # Edge measures - new implementation
            for i, compute_item in enumerate(select.compute):
                if progress:
                    uq_info = _format_uq_info(compute_item, for_edges=True)
                    logger.info(
                        f"  Computing {compute_item.name} ({i+1}/{len(select.compute)}){uq_info}"
                    )
                try:
                    # Check if this is an edge-specific measure
                    measure_fn = measure_registry.get(compute_item.name, target="edges")
                    result_name = compute_item.result_name

                    # Compute the measure on edges (always deterministic for now)
                    values = measure_fn(G, items)
                    if compute_item.uncertainty:
                        logging.getLogger(__name__).warning(
                            f"Uncertainty not yet supported for edge measure '{compute_item.name}'. "
                            "Returning deterministic values with std=0."
                        )
                        values = _wrap_deterministic_uncertainty(values, items)
                    attributes[result_name] = values
                except UnknownMeasureError:
                    # Re-raise with context that this is an edge query
                    raise
                except DslExecutionError:
                    # Re-raise DSL execution errors (e.g., wrong target)
                    raise
                except Exception as e:
                    # Log specific error and continue with other measures
                    logging.getLogger(__name__).warning(
                        f"Error computing edge measure '{compute_item.name}': {e}"
                    )
                    attributes[compute_item.result_name] = {}

    # Step 4.5: Apply grouping, per-group operations, and coverage filtering
    grouping_metadata = None
    if select.group_by or select.limit_per_group is not None or select.coverage_mode:
        if progress:
            logger.info("Step 3.4.5: Applying grouping and coverage filtering")
        items, grouping_metadata = _apply_grouping_and_coverage(
            items=items,
            select=select,
            network=network,
            G=G,
            attributes=attributes,
            progress=progress,
        )
        if progress and grouping_metadata is not None:
            num_groups = len(grouping_metadata.get("groups", []))
            logger.info(f"Grouped into {num_groups} group(s)")
        # Skip global ORDER BY when grouping is used (ordering is per-group)
    else:
        # Step 5: Apply global ORDER BY (only when not grouping and not already ordered)
        if select.order_by and not early_limit_applied:
            if progress:
                logger.info("Step 3.5: Applying ORDER BY")
            # Smart defaults: Ensure attributes exist before ordering
            for order_item in select.order_by:
                # Skip validation for attributes that will be created by summarize
                if select.summarize_aggs and order_item.key in select.summarize_aggs:
                    continue

                # Skip validation for attributes that will be created by rename
                if select.rename_map and order_item.key in select.rename_map:
                    continue

                _ensure_attribute(
                    attr_name=order_item.key,
                    attributes=attributes,
                    items=items,
                    network=network,
                    G=G,
                    select=select,
                    auto_compute=True,
                )
            items = _apply_ordering(items, select.order_by, attributes)

    # Step 5.5: Apply post-processing operations (aggregate, summarize, mutate, rank, zscore, distinct, select, drop, rename)
    if (
        select.aggregate_specs
        or select.summarize_aggs
        or select.mutate_specs
        or select.rank_specs
        or select.zscore_attrs
        or select.distinct_cols is not None
        or select.select_cols
        or select.drop_cols
        or select.rename_map
    ):
        if progress:
            logger.info("Step 3.5.5: Applying post-processing operations")
        items, attributes = _apply_post_processing(
            items=items,
            attributes=attributes,
            select=select,
            network=network,
            G=G,
            progress=progress,
        )
    _record_timing("group_aggregate", (time.monotonic() - stage_start) * 1000)

    # Step 6: Apply global LIMIT (if not already applied early)
    if select.limit is not None and not early_limit_applied:
        if progress:
            logger.info(f"Step 3.6: Applying LIMIT {select.limit}")
        items = items[: select.limit]
    _record_timing("limit", (time.monotonic() - stage_start) * 1000)

    # Step 6.5: Apply explanations if specified
    if select.explain_spec is not None:
        if progress:
            logger.info("Step 3.6.5: Attaching explanations to results")
        items, attributes = _apply_explanations(
            network=network,
            items=items,
            attributes=attributes,
            explain_spec=select.explain_spec,
            target=select.target,
        )

    # Create result
    stage_start = time.monotonic()
    if progress:
        logger.info(
            f"Step 3.7: Creating QueryResult with {len(items)} {select.target.value}"
        )
    meta_dict = {"dsl_version": "2.0"}
    if grouping_metadata is not None:
        meta_dict["grouping"] = grouping_metadata

    # Don't add provenance yet - will be added by caller

    # Add approximation metadata if any approx was used
    if approx_used:
        meta_dict["approximation"] = {
            "enabled": True,
            "measures": approx_used,
            "fast_path": fast_path_enabled,
        }


    # Set fast_path in provenance if approximation was used
    if fast_path_enabled and provenance_builder is not None:
        provenance_builder.backend_info["fast_path"] = True

    result = QueryResult(
        target=select.target.value, items=items, attributes=attributes, meta=meta_dict
    )
    _record_timing("materialize", (time.monotonic() - stage_start) * 1000)

    # Step 7: Apply file export if specified
    if select.file_export:
        if progress:
            logger.info(f"Step 3.8: Exporting to file: {select.file_export}")
        from .export import export_result

        export_result(result, select.file_export)

    # Step 8: Apply export if specified (for result format conversion)
    if select.export:
        if progress:
            logger.info(f"Step 3.9: Converting to {select.export.value}")
        if select.export == ExportTarget.PANDAS:
            return result.to_pandas()
        elif select.export == ExportTarget.NETWORKX:
            return result.to_networkx(network)
        elif select.export == ExportTarget.ARROW:
            return result.to_arrow()

    if progress:
        logger.info("Query execution completed")

    return result


def _execute_auto_community(
    network: Any,
    select: SelectStmt,
    params: Optional[Dict[str, Any]] = None,
    progress: bool = True,
    provenance_builder: Optional[ProvenanceBuilder] = None,
    provenance_record: Optional[Any] = None,
) -> QueryResult:
    """Execute auto community detection and return assignment table or annotated nodes.
    
    Implements single-run + caching semantics as specified in the issue requirements.
    
    Args:
        network: Multilayer network
        select: SELECT statement with auto_community_config
        params: Parameter bindings
        progress: If True, log progress messages
        provenance_builder: Optional provenance builder
        provenance_record: Optional provenance record
    
    Returns:
        QueryResult with assignment table (COMMUNITIES) or annotated nodes (NODES)
    """
    import hashlib
    import pandas as pd
    from py3plex.algorithms.community_detection import auto_select_community
    
    logger = logging.getLogger(__name__)
    params = params or {}
    
    # Get auto community config
    config = select.auto_community_config
    
    # Create execution context with caching
    ctx = DSLExecutionContext(
        graph=network,
        current_layers=None,
        current_nodes=None,
        params=params,
    )
    
    # Generate cache key based on network id + params
    network_id = id(network)  # Use object identity
    config_dict = {
        "seed": config.seed,
        "fast": config.fast,
        **config.params,
    }
    config_str = str(sorted(config_dict.items()))
    cache_key = hashlib.md5(f"{network_id}_{config_str}".encode()).hexdigest()
    
    if progress:
        logger.info(f"AutoCommunity: cache key = {cache_key}")
    
    # Check cache
    if cache_key in ctx.cache["autocommunity"]:
        if progress:
            logger.info("AutoCommunity: Using cached result")
        assignments_df, meta = ctx.cache["autocommunity"][cache_key]
    else:
        if progress:
            logger.info("AutoCommunity: Running auto_select_community")
        
        # Increment debug counter for testing
        if "autocommunity_runs" not in ctx.debug_counters:
            ctx.debug_counters["autocommunity_runs"] = 0
        ctx.debug_counters["autocommunity_runs"] += 1
        
        # Check if UQ is enabled
        uq_config = getattr(select, "uq_config", None)
        uq_enabled = uq_config is not None
        
        if uq_enabled:
            uq_method = uq_config.uq_method or "seed"
            uq_n_samples = uq_config.n_samples or 10
        else:
            uq_method = "seed"
            uq_n_samples = 10
        
        # Run auto_select_community with new mode parameter
        try:
            # Detect mode from config and other custom params
            mode = config.params.get('mode', 'pareto')  # Default to Pareto mode
            null_model = config.params.get('null_model', False)
            null_samples = config.params.get('null_samples', 10)
            
            # Extract any other custom parameters (for extensibility)
            other_params = {
                k: v for k, v in config.params.items()
                if k not in ('mode', 'null_model', 'null_samples')
            }
            
            result = auto_select_community(
                network=network,
                mode=mode,  # New: Pareto or wins mode
                fast=config.fast,
                uq=uq_enabled,
                uq_n_samples=uq_n_samples,
                uq_method=uq_method,
                seed=config.seed or 0,
                null_model=null_model,  # New: null model calibration
                null_samples=null_samples,  # New: null samples count
                **other_params,  # Pass through any other custom parameters
            )
        except Exception as e:
            logger.error(f"AutoCommunity failed: {e}")
            raise
        
        # Build assignment table from result
        partition = result.partition
        
        # Determine if multilayer
        is_multilayer = False
        sample_keys = list(partition.keys())[:5]
        for key in sample_keys:
            if isinstance(key, tuple) and len(key) == 2:
                is_multilayer = True
                break
        
        # Build assignment records
        records = []
        for node_layer, community_id in partition.items():
            if is_multilayer and isinstance(node_layer, tuple):
                node, layer = node_layer
            else:
                node = node_layer
                layer = None
            
            # For now, use deterministic fallback for UQ metrics if not available
            # TODO: Extract from result if UQ was enabled
            confidence = 1.0
            entropy = 0.0
            margin = 1.0
            
            records.append({
                "node": node,
                "layer": layer,
                "community": community_id,
                "confidence": confidence,
                "entropy": entropy,
                "margin": margin,
            })
        
        # Convert to DataFrame for easy manipulation
        assignments_df = pd.DataFrame(records)
        
        # Compute community sizes
        community_sizes = assignments_df.groupby("community").size().to_dict()
        assignments_df["community_size"] = assignments_df["community"].map(community_sizes)
        
        # Build metadata
        meta = {
            "algorithm": result.algorithm,
            "provenance": result.provenance,
            "leaderboard": result.leaderboard,
        }
        
        # Cache the result
        ctx.cache["autocommunity"][cache_key] = (assignments_df, meta)
        
        if progress:
            logger.info(f"AutoCommunity: Detected {len(community_sizes)} communities")
    
    # Now handle based on query kind
    if config.kind == "communities":
        # Return assignment table as QueryResult
        if progress:
            logger.info("AutoCommunity: Returning assignment table")
        
        # Apply WHERE filters if present
        if select.where:
            filtered_df = assignments_df.copy()
            filters = {}
            _extract_auto_community_filters(select.where, filters)
            
            for filter_key, filter_value in filters.items():
                if "__" in filter_key:
                    attr, op = filter_key.rsplit("__", 1)
                else:
                    attr = filter_key
                    op = "eq"
                
                if op == "gt":
                    filtered_df = filtered_df[filtered_df[attr] > filter_value]
                elif op == "gte":
                    filtered_df = filtered_df[filtered_df[attr] >= filter_value]
                elif op == "lt":
                    filtered_df = filtered_df[filtered_df[attr] < filter_value]
                elif op == "lte":
                    filtered_df = filtered_df[filtered_df[attr] <= filter_value]
                elif op == "eq":
                    filtered_df = filtered_df[filtered_df[attr] == filter_value]
                elif op == "ne":
                    filtered_df = filtered_df[filtered_df[attr] != filter_value]
            
            assignments_df = filtered_df
        
        # Convert to QueryResult format
        items = list(range(len(assignments_df)))
        attributes = {
            col: {i: val for i, val in enumerate(assignments_df[col].values)}
            for col in assignments_df.columns
        }
        
        result_meta = {
            "dsl_version": "2.1",
            "kind": "auto_community_assignments",
            "num_assignments": len(items),
            **meta,
        }
        
        return QueryResult(
            target="communities",
            items=items,
            attributes=attributes,
            meta=result_meta,
        )
    
    elif config.kind == "nodes_join":
        # Join annotations to nodes view
        if progress:
            logger.info("AutoCommunity: Joining annotations to nodes")
        
        # First, execute the base nodes query
        # Create a modified select without auto_community_config
        base_select = SelectStmt(
            target=select.target,
            layer_expr=select.layer_expr,
            layer_set=select.layer_set,
            where=None,  # Apply WHERE after join
            compute=select.compute,
            order_by=select.order_by,
            limit=select.limit,
            autocompute=select.autocompute,
            uq_config=select.uq_config,
        )
        
        # Execute base query
        # Get nodes directly
        items = list(network.get_nodes())
        base_result = _execute_select_with_items(
            network, base_select, items, params=params, progress=False
        )
        
        # Join community annotations
        for i, item in enumerate(base_result.items):
            node = item
            layer = base_result.attributes.get("layer", {}).get(i)
            
            # Find matching assignment
            if is_multilayer and layer is not None:
                mask = (assignments_df["node"] == node) & (assignments_df["layer"] == layer)
            else:
                mask = assignments_df["node"] == node
            
            matching = assignments_df[mask]
            if len(matching) > 0:
                row = matching.iloc[0]
                # Add community attributes
                for col in ["community", "confidence", "entropy", "margin", "community_size"]:
                    if col not in base_result.attributes:
                        base_result.attributes[col] = {}
                    base_result.attributes[col][i] = row[col]
        
        # Now apply WHERE filters (including community filters)
        if select.where:
            filtered_items = []
            for i in base_result.items:
                if _check_where_condition(base_result, i, select.where, params):
                    filtered_items.append(i)
            
            base_result.items = filtered_items
        
        # Update metadata
        base_result.meta["auto_community"] = meta
        
        return base_result
    
    else:
        raise ValueError(f"Unknown auto_community kind: {config.kind}")


def _extract_auto_community_filters(where: ConditionExpr, filters: Dict[str, Any]) -> None:
    """Extract filters from WHERE conditions for auto community fields.
    
    Args:
        where: ConditionExpr AST node
        filters: Dict to populate with filters
    """
    for atom in where.atoms:
        if atom.comparison:
            comp = atom.comparison
            attr = comp.left
            op = comp.op
            value = comp.right
            
            # Map operator to filter suffix
            op_map = {
                ">": "gt",
                ">=": "gte",
                "<": "lt",
                "<=": "lte",
                "=": "eq",
                "!=": "ne",
            }
            
            suffix = op_map.get(op, "eq")
            filter_key = f"{attr}__{suffix}" if suffix != "eq" else attr
            filters[filter_key] = value


def _check_where_condition(
    result: QueryResult,
    item_idx: int,
    where: ConditionExpr,
    params: Dict[str, Any]
) -> bool:
    """Check if an item satisfies WHERE conditions.
    
    Args:
        result: QueryResult with attributes
        item_idx: Index of item to check
        where: WHERE condition expression
        params: Parameter bindings
    
    Returns:
        True if item satisfies conditions, False otherwise
    """
    for atom in where.atoms:
        if atom.comparison:
            comp = atom.comparison
            attr = comp.left
            op = comp.op
            value = comp.right
            
            # Get actual value
            if attr in result.attributes:
                actual = result.attributes[attr].get(item_idx)
            else:
                # Attribute not present, skip this condition
                continue
            
            # Check condition
            if op == ">":
                if not (actual > value):
                    return False
            elif op == ">=":
                if not (actual >= value):
                    return False
            elif op == "<":
                if not (actual < value):
                    return False
            elif op == "<=":
                if not (actual <= value):
                    return False
            elif op == "=":
                if not (actual == value):
                    return False
            elif op == "!=":
                if not (actual != value):
                    return False
    
    return True


def _execute_community_select(
    network: Any,
    select: SelectStmt,
    params: Optional[Dict[str, Any]] = None,
    progress: bool = False,
) -> QueryResult:
    """Execute a SELECT statement for communities.

    Args:
        network: Multilayer network
        select: SELECT statement AST
        params: Parameter bindings for dynamic resolution
        progress: If True, log progress messages during query execution

    Returns:
        QueryResult with community records
    """
    from .communities import build_community_records, compute_community_metric

    params = params or {}
    logger = logging.getLogger(__name__)

    if progress:
        logger.info("Executing community query")

    # Step 1: Get partition name (from select or default)
    partition_name = getattr(select, "partition_name", "default")

    if progress:
        logger.info(f"Step 1: Loading partition '{partition_name}'")

    # Step 2: Get partition from network
    partition = network.get_partition_by_name(partition_name)

    if partition is None:
        raise DslExecutionError(
            f"No partition named '{partition_name}' found in network. "
            f"Available partitions: {network.list_partitions()}. "
            f"Use network.assign_partition(partition, name='...') to assign a partition."
        )

    if progress:
        logger.info(f"Loaded partition with {len(set(partition.values()))} communities")

    # Step 3: Build community records
    records = build_community_records(network, partition, name=partition_name)

    if progress:
        logger.info(f"Built {len(records)} community records")

    # Step 4: Apply WHERE conditions (filter communities)
    if select.where:
        if progress:
            logger.info("Step 2: Applying WHERE conditions")

        # Build filters dict from conditions
        filters = {}
        _extract_community_filters(select.where, filters)

        # Apply filters
        from .communities import filter_communities

        records = filter_communities(records, **filters)

        if progress:
            logger.info(f"Filtered to {len(records)} communities")

    # Step 5: Compute additional metrics
    attributes: Dict[str, Dict] = {}
    if select.compute:
        if progress:
            logger.info(f"Step 3: Computing {len(select.compute)} measure(s)")

        for compute_item in select.compute:
            metric_name = compute_item.name
            result_name = compute_item.alias or metric_name

            # Compute metric for each community
            metric_values = {}
            for record in records:
                value = compute_community_metric(record, metric_name, network)
                metric_values[record.community_id] = value

            attributes[result_name] = metric_values

        if progress:
            logger.info(f"Computed {len(attributes)} metrics")

    # Step 6: Convert records to items (community_id)
    items = [record.community_id for record in records]

    # Step 7: Build attributes dict with community properties
    # Add built-in attributes
    attributes["size"] = {r.community_id: r.size for r in records}
    attributes["intra_edges"] = {r.community_id: r.intra_edges for r in records}
    attributes["inter_edges"] = {r.community_id: r.inter_edges for r in records}
    attributes["density_intra"] = {r.community_id: r.density_intra for r in records}
    attributes["cut_size"] = {r.community_id: r.cut_size for r in records}
    attributes["layer_scope"] = {r.community_id: r.layer_scope for r in records}

    # Step 8: Apply ordering
    if select.order_by:
        if progress:
            logger.info("Step 4: Applying ORDER BY")
        items = _apply_ordering(items, select.order_by, attributes)

    # Step 9: Apply limit
    if select.limit is not None:
        if progress:
            logger.info(f"Step 5: Applying LIMIT {select.limit}")
        items = items[: select.limit]

    # Step 10: Apply grouping if requested
    grouping_meta = None
    if select.group_by:
        if progress:
            logger.info(f"Step 6: Applying grouping by {select.group_by}")

        # Build grouping metadata
        groups: Dict[Any, List[Any]] = {}
        for comm_id in items:
            # Get group key based on group_by fields
            if "layer" in select.group_by:
                # Group by layer_scope
                record = next(r for r in records if r.community_id == comm_id)
                key = record.layer_scope
            else:
                # Group by algorithm or other metadata
                key = tuple(
                    attributes.get(field, {}).get(comm_id) for field in select.group_by
                )

            if key not in groups:
                groups[key] = []
            groups[key].append(comm_id)

        grouping_meta = {
            "grouping": "community",
            "groups": groups,
            "group_by": select.group_by,
        }

    # Build metadata
    meta_dict = {
        "dsl_version": "2.1",
        "partition_name": partition_name,
        "num_communities": len(items),
        "total_communities": len(records),
    }

    if grouping_meta:
        meta_dict.update(grouping_meta)

    # Store community records in metadata for bridge methods
    meta_dict["_community_records"] = {r.community_id: r for r in records}

    if progress:
        logger.info("Community query execution completed")

    return QueryResult(
        target=select.target.value, items=items, attributes=attributes, meta=meta_dict
    )


def _extract_community_filters(where: ConditionExpr, filters: Dict[str, Any]) -> None:
    """Extract community filters from WHERE conditions.

    Args:
        where: ConditionExpr AST node
        filters: Dict to populate with filters
    """
    for atom in where.atoms:
        if atom.comparison:
            comp = atom.comparison
            attr = comp.left
            op = comp.op
            value = comp.right

            # Map operator to filter suffix
            op_map = {
                ">": "gt",
                ">=": "gte",
                "<": "lt",
                "<=": "lte",
                "=": "eq",
                "!=": "ne",
            }

            suffix = op_map.get(op, "eq")
            filter_key = f"{attr}__{suffix}" if suffix != "eq" else attr
            filters[filter_key] = value


def _execute_community_bridge(
    network: Any,
    select: SelectStmt,
    params: Optional[Dict[str, Any]] = None,
    progress: bool = False,
) -> QueryResult:
    """Execute a query that bridges from communities to nodes/edges.

    Args:
        network: Multilayer network
        select: SELECT statement AST (with _from_communities)
        params: Parameter bindings for dynamic resolution
        progress: If True, log progress messages during query execution

    Returns:
        QueryResult with filtered nodes or edges
    """
    logger = logging.getLogger(__name__)

    if progress:
        logger.info("Executing community bridge query")

    # First, execute the community query to get selected communities
    community_select = select._from_communities
    community_result = _execute_community_select(
        network, community_select, params, progress=progress
    )

    # Get community records from metadata
    community_records_dict = community_result.meta.get("_community_records", {})
    selected_comm_ids = set(community_result.items)

    if progress:
        logger.info(
            f"Bridge from {len(selected_comm_ids)} communities to {select.target.value}"
        )

    # Get core network
    G = network.core_network

    if select.target == Target.NODES:
        # .members() bridge: get all nodes in selected communities
        member_nodes = []
        for comm_id in selected_comm_ids:
            if comm_id in community_records_dict:
                record = community_records_dict[comm_id]
                member_nodes.extend(record.members)

        if progress:
            logger.info(f"Found {len(member_nodes)} member nodes")

        # Set items for the rest of execution
        items = member_nodes

    elif select.target == Target.EDGES:
        # .boundary_edges() bridge: get edges crossing community boundaries
        edge_type = getattr(select, "_community_edge_type", "boundary")

        if edge_type == "boundary":
            # Get boundary edges
            boundary_edges = []

            # Get all members across selected communities
            all_members = set()
            for comm_id in selected_comm_ids:
                if comm_id in community_records_dict:
                    record = community_records_dict[comm_id]
                    all_members.update(record.members)

            # Find edges where endpoints are in different communities
            for edge in network.get_edges(data=True):
                src, dst = edge[0], edge[1]

                if src in all_members and dst in all_members:
                    # Check if they're in different communities
                    src_comm = None
                    dst_comm = None

                    for comm_id in selected_comm_ids:
                        record = community_records_dict[comm_id]
                        if src in record.members:
                            src_comm = comm_id
                        if dst in record.members:
                            dst_comm = comm_id

                    if (
                        src_comm is not None
                        and dst_comm is not None
                        and src_comm != dst_comm
                    ):
                        boundary_edges.append(edge)

            if progress:
                logger.info(f"Found {len(boundary_edges)} boundary edges")

            items = boundary_edges
        else:
            # Unknown edge type
            items = []
    else:
        # Should not happen
        items = []

    # Now continue with the normal execution path by temporarily removing the
    # _from_communities marker and executing the rest
    original_from_communities = select._from_communities
    select._from_communities = None

    # Apply layer filters
    if select.layer_set is not None:
        if progress:
            logger.info("Applying layer filter")
        active_layers = select.layer_set.resolve(network, strict=False, warn_empty=True)
        items = _filter_by_layers(items, active_layers, select.target)
    elif select.layer_expr:
        if progress:
            logger.info("Applying layer filter")
        active_layers = _evaluate_layer_expr(select.layer_expr, network)
        items = _filter_by_layers(items, active_layers, select.target)

    # Apply WHERE conditions
    if select.where:
        if progress:
            logger.info("Applying WHERE conditions")
        items = _filter_by_conditions(items, select.where, network, G, params)

    # Build execution context for operators
    if select.compute and select.target == Target.NODES:
        # For nodes, we need to compute measures - use the existing code path
        # by creating a new SelectStmt and executing it

        # Create a modified network that only contains our filtered items
        temp_select = SelectStmt(target=select.target, autocompute=select.autocompute)
        temp_select.compute = select.compute
        temp_select.order_by = select.order_by
        temp_select.limit = select.limit
        temp_select.group_by = select.group_by

        # Store the items for filtering
        temp_select._prefiltered_items = items

        # Execute via the standard path
        result = _execute_select_with_items(
            network, temp_select, items, params, progress=progress
        )

        # Restore marker
        select._from_communities = original_from_communities

        return result

    # Simple case: no compute, just return filtered items
    attributes: Dict[str, Dict] = {}

    # Apply ordering
    if select.order_by:
        if progress:
            logger.info("Applying ORDER BY")
        items = _apply_ordering(items, select.order_by, attributes)

    # Apply limit
    if select.limit is not None:
        if progress:
            logger.info(f"Applying LIMIT {select.limit}")
        items = items[: select.limit]

    # Restore marker
    select._from_communities = original_from_communities

    if progress:
        logger.info("Community bridge query execution completed")

    return QueryResult(
        target=select.target.value,
        items=items,
        attributes=attributes,
        meta={"dsl_version": "2.1", "from_communities": True},
    )


def _execute_select_with_items(
    network: Any,
    select: SelectStmt,
    items: List[Any],
    params: Optional[Dict[str, Any]] = None,
    progress: bool = False,
) -> QueryResult:
    """Execute SELECT with pre-filtered items.

    This is a helper for bridge queries where items are already filtered.
    """
    logger = logging.getLogger(__name__)
    G = network.core_network

    # Compute measures if needed
    attributes: Dict[str, Dict] = {}
    if select.compute:
        if progress:
            logger.info(f"Computing {len(select.compute)} measure(s)")

        if select.target == Target.NODES:
            # Node measures
            subgraph = G.subgraph([item for item in items if item in G]).copy()

            for compute_item in select.compute:
                result_name = compute_item.alias or compute_item.name

                # Look up measure in registry
                measure_fn = measure_registry.get(compute_item.name)
                if measure_fn:
                    try:
                        values = measure_fn(subgraph, items)
                        attributes[result_name] = values
                    except Exception as e:
                        if progress:
                            logger.warning(
                                f"Failed to compute {compute_item.name}: {e}"
                            )
                        # Return None for all items
                        attributes[result_name] = {item: None for item in items}
                else:
                    # Unknown measure
                    if progress:
                        logger.warning(f"Unknown measure: {compute_item.name}")
                    attributes[result_name] = {item: None for item in items}

    # Apply ordering
    if select.order_by:
        items = _apply_ordering(items, select.order_by, attributes)

    # Apply limit
    if select.limit is not None:
        items = items[: select.limit]

    return QueryResult(
        target=select.target.value,
        items=items,
        attributes=attributes,
        meta={"dsl_version": "2.1"},
    )


def _apply_explanations(
    network: Any,
    items: List[Any],
    attributes: Dict[str, Dict],
    explain_spec: "ExplainSpec",
    target: Target,
) -> Tuple[List[Any], Dict[str, Dict]]:
    """Apply explanations to result items.

    Args:
        network: Multilayer network instance
        items: Result items (nodes or edges)
        attributes: Computed attributes
        explain_spec: Explanation specification
        target: Query target (nodes or edges)

    Returns:
        Tuple of (items, enhanced_attributes) with explanation data
    """
    from .explain import explain_rows
    from .ast import ExplainSpec
    
    logger = logging.getLogger(__name__)

    # Only support node explanations in Phase 1
    if target != Target.NODES:
        logger.warning("Explanations are currently only supported for node queries")
        return items, attributes

    if not items:
        return items, attributes

    # Convert items to row format expected by explain engine
    rows = []
    for item in items:
        row = {}
        if isinstance(item, tuple) and len(item) >= 2:
            row["id"] = item[0]
            row["layer"] = item[1]
        else:
            row["id"] = item
            row["layer"] = None
        rows.append(row)

    # Call explanation engine
    try:
        enriched_rows, explanation_schema = explain_rows(
            network=network,
            rows=rows,
            include=explain_spec.include,
            neighbors_top=explain_spec.neighbors_top,
            neighbors_cfg=explain_spec.neighbors_cfg,
            community_cfg=explain_spec.community_cfg,
            layer_footprint_cfg=explain_spec.layer_footprint_cfg,
            attribution_cfg=explain_spec.attribution_cfg,
            cache=explain_spec.cache,
        )
    except Exception as e:
        logger.warning(f"Failed to generate explanations: {e}")
        return items, attributes

    # Extract explanations from enriched rows and add to attributes
    # Store explanations as attributes so they can be exported
    for i, enriched_row in enumerate(enriched_rows):
        explanations = enriched_row.get("_explanations", {})
        item = items[i]

        # Add each explanation field as an attribute
        for key, value in explanations.items():
            if key not in attributes:
                attributes[key] = {}
            attributes[key][item] = value

    return items, attributes


def _expand_layer_term(name: str, network: Any) -> Set[str]:
    """Expand a single layer term, handling wildcards.

    Args:
        name: Layer name or "*" for all layers
        network: Multilayer network object

    Returns:
        Set of layer names
    """
    if name == "*":
        # Expand wildcard to all layers in the network
        if hasattr(network, "layers"):
            return {str(l) for l in network.layers}
        # Fallback: derive layers from nodes
        if hasattr(network, "get_nodes"):
            return {str(layer) for (_, layer) in network.get_nodes()}
        return set()
    return {name}


def _evaluate_layer_expr(layer_expr: LayerExpr, network: Any) -> Set[str]:
    """Evaluate a layer expression to get the set of active layers.

    Supports:
        - Wildcard: L["*"] → all layers in network
        - Union (+): L["a"] + L["b"] → {"a", "b"}
        - Difference (-): L["a"] - L["b"] → {"a"} - {"b"}
        - Intersection (&): L["a"] & L["b"] → {"a"} ∩ {"b"}
        - Combined: L["*"] - L["foo"] → all layers except "foo"
    """
    if not layer_expr.terms:
        return set()

    # Start with first term (expanded if wildcard)
    result = _expand_layer_term(layer_expr.terms[0].name, network)

    # Apply operations
    for i, op in enumerate(layer_expr.ops):
        other = _expand_layer_term(layer_expr.terms[i + 1].name, network)

        if op == "+":
            result |= other
        elif op == "-":
            result -= other
        elif op == "&":
            result &= other

    return result


def _filter_by_layers(
    items: List[Any], active_layers: Set[str], target: Target
) -> List[Any]:
    """Filter items by layer membership.

    Args:
        items: List of items (nodes or edges)
        active_layers: Set of layer names (as strings)
        target: Target type (NODES or EDGES)

    Returns:
        Filtered list of items
    """
    if target == Target.NODES:
        # Nodes are tuples (node_id, layer)
        return [
            item
            for item in items
            if isinstance(item, tuple)
            and len(item) >= 2
            and str(item[1]) in active_layers
        ]
    else:
        # Edges are tuples of node tuples
        filtered = []
        for item in items:
            if isinstance(item, tuple) and len(item) >= 2:
                source, target_node = item[0], item[1]
                if isinstance(source, tuple) and isinstance(target_node, tuple):
                    if len(source) >= 2 and len(target_node) >= 2:
                        if (
                            str(source[1]) in active_layers
                            or str(target_node[1]) in active_layers
                        ):
                            filtered.append(item)
        return filtered


def _filter_by_conditions(
    items: List[Any],
    conditions: ConditionExpr,
    network: Any,
    G: nx.Graph,
    params: Optional[Dict[str, Any]] = None,
) -> List[Any]:
    """Filter items by WHERE conditions."""
    params = params or {}
    result = []

    for item in items:
        if _evaluate_conditions(item, conditions, network, G, params):
            result.append(item)

    return result


def _evaluate_conditions(
    item: Any,
    conditions: ConditionExpr,
    network: Any,
    G: nx.Graph,
    params: Optional[Dict[str, Any]] = None,
) -> bool:
    """Evaluate all conditions for an item."""
    params = params or {}

    if not conditions.atoms:
        return True

    # Standard boolean precedence: AND binds tighter than OR.
    # ConditionExpr is a flat sequence of atoms with ops in-between; interpret it as
    # an OR of AND-chains.
    first = _evaluate_atom(item, conditions.atoms[0], network, G, params)
    current_and_chain = first
    or_terms: List[bool] = []

    for i, op in enumerate(conditions.ops):
        next_result = _evaluate_atom(item, conditions.atoms[i + 1], network, G, params)
        if op == "AND":
            current_and_chain = current_and_chain and next_result
        elif op == "OR":
            or_terms.append(current_and_chain)
            current_and_chain = next_result

    or_terms.append(current_and_chain)
    return any(or_terms)


def _evaluate_atom(
    item: Any,
    atom: ConditionAtom,
    network: Any,
    G: nx.Graph,
    params: Optional[Dict[str, Any]] = None,
) -> bool:
    """Evaluate a single condition atom."""
    params = params or {}

    if atom.comparison:
        return _evaluate_comparison(item, atom.comparison, network, G, params)
    elif atom.special:
        return _evaluate_special(item, atom.special, network, G)
    elif atom.function:
        # Function calls would need more complex handling
        return True
    return True


def _evaluate_comparison(
    item: Any,
    comparison: Comparison,
    network: Any,
    G: nx.Graph,
    params: Optional[Dict[str, Any]] = None,
) -> bool:
    """Evaluate a comparison condition."""
    params = params or {}

    # Get actual value
    actual_value = _get_attribute_value(item, comparison.left, network, G)

    if actual_value is None:
        return False

    # Get expected value (resolve param if needed)
    expected_value = _resolve_param(comparison.right, params)

    # Compare
    op = comparison.op

    if op == "=":
        # Prefer numeric equality when both sides look numeric.
        try:
            return float(actual_value) == float(expected_value)
        except (ValueError, TypeError):
            return str(actual_value) == str(expected_value)
    elif op == "!=":
        try:
            return float(actual_value) != float(expected_value)
        except (ValueError, TypeError):
            return str(actual_value) != str(expected_value)
    elif op == ">":
        try:
            return float(actual_value) > float(expected_value)
        except (ValueError, TypeError):
            return False
    elif op == "<":
        try:
            return float(actual_value) < float(expected_value)
        except (ValueError, TypeError):
            return False
    elif op == ">=":
        try:
            return float(actual_value) >= float(expected_value)
        except (ValueError, TypeError):
            return False
    elif op == "<=":
        try:
            return float(actual_value) <= float(expected_value)
        except (ValueError, TypeError):
            return False

    return False


def _evaluate_special(
    item: Any, special: SpecialPredicate, network: Any, G: nx.Graph
) -> bool:
    """Evaluate a special predicate."""
    if special.kind == "intralayer":
        # For edges: check if source and target are in same layer
        if isinstance(item, tuple) and len(item) >= 2:
            source, target = item[0], item[1]
            if isinstance(source, tuple) and isinstance(target, tuple):
                if len(source) >= 2 and len(target) >= 2:
                    return source[1] == target[1]
        return False

    elif special.kind == "interlayer":
        # For edges: check if source is in src_layer and target is in dst_layer
        # If params is empty, check for any inter-layer edge (src_layer != dst_layer)
        src_layer = special.params.get("src")
        dst_layer = special.params.get("dst")

        if isinstance(item, tuple) and len(item) >= 2:
            source, target = item[0], item[1]
            if isinstance(source, tuple) and isinstance(target, tuple):
                if len(source) >= 2 and len(target) >= 2:
                    if src_layer is None and dst_layer is None:
                        # interlayer=True: any inter-layer edge
                        return source[1] != target[1]
                    else:
                        # interlayer=(src, dst): specific layer pair
                        return source[1] == src_layer and target[1] == dst_layer
        return False

    elif special.kind == "temporal_range":
        # For nodes or edges: check timestamp attribute lies within [t_start, t_end]
        t_start = special.params.get("t_start")
        t_end = special.params.get("t_end")

        t_value = _get_attribute_value(item, "t", network, G)
        if t_value is None:
            return False

        try:
            if t_start is not None and t_value < t_start:
                return False
            if t_end is not None and t_value > t_end:
                return False
            return True
        except TypeError:
            # Non-comparable timestamp
            return False

    return True


def _get_attribute_value(item: Any, attribute: str, network: Any, G: nx.Graph) -> Any:
    """Get an attribute value from a node or edge.

    For nodes (tuples of (node_id, layer)):
        - 'layer': returns the layer name
        - 'degree': returns node degree
        - other: looks up node attributes

    For edges (tuples of ((node_id, layer), (node_id, layer), {data})):
        - 'source_layer': returns source node's layer
        - 'target_layer': returns target node's layer
        - 'layer': returns source layer (for intralayer edges) or None
        - 'weight': returns edge weight (default 1.0)
        - 'src_degree' / 'source_degree': returns source node's degree
        - 'dst_degree' / 'target_degree': returns target node's degree
        - other: looks up edge attributes
    """
    # Check if this is an edge (tuple with 2 node tuples as first elements)
    if isinstance(item, tuple) and len(item) >= 2:
        first_elem = item[0]
        second_elem = item[1]

        # Check if this is an edge: ((node, layer), (node, layer), {data}?)
        if isinstance(first_elem, tuple) and isinstance(second_elem, tuple):
            if len(first_elem) >= 2 and len(second_elem) >= 2:
                # This is an edge
                source_node, source_layer = first_elem[0], first_elem[1]
                target_node, target_layer = second_elem[0], second_elem[1]

                # Handle edge-specific attributes
                if attribute == "source_layer":
                    return str(source_layer)
                elif attribute == "target_layer":
                    return str(target_layer)
                elif attribute == "layer":
                    # For intralayer edges, return the common layer
                    if source_layer == target_layer:
                        return str(source_layer)
                    return None
                elif attribute == "weight":
                    # Get edge data if available
                    if len(item) >= 3 and isinstance(item[2], dict):
                        return item[2].get("weight", 1.0)
                    # Try to get from graph
                    if G.has_edge(first_elem, second_elem):
                        edge_data = G.get_edge_data(first_elem, second_elem)
                        if edge_data:
                            return edge_data.get("weight", 1.0)
                    return 1.0
                elif attribute in ("src_degree", "source_degree"):
                    # Get source node's degree
                    if first_elem in G:
                        return G.degree(first_elem)
                    return 0
                elif attribute in ("dst_degree", "target_degree"):
                    # Get target node's degree
                    if second_elem in G:
                        return G.degree(second_elem)
                    return 0
                else:
                    # Try to get from edge data dict
                    if len(item) >= 3 and isinstance(item[2], dict):
                        if attribute in item[2]:
                            return item[2][attribute]
                    # Try to get from graph
                    if G.has_edge(first_elem, second_elem):
                        edge_data = G.get_edge_data(first_elem, second_elem)
                        if edge_data and attribute in edge_data:
                            return edge_data[attribute]
                return None

        # This is a node (tuple of (node_id, layer))
        node_id, layer = item[0], item[1]

        if attribute == "layer":
            return str(layer)

        if attribute == "degree":
            if item in G:
                return G.degree(item)
            return 0

        # Try to get from node attributes
        if item in G:
            node_data = G.nodes.get(item, {})
            if attribute in node_data:
                return node_data[attribute]

    return None


def _get_edge_key(edge: Any) -> Tuple[Any, Any]:
    """Get a hashable key for an edge.

    Converts edge tuple (u, v, {data}?) to simple (u, v) for use as dict key.
    """
    if isinstance(edge, tuple) and len(edge) >= 2:
        return (edge[0], edge[1])
    return edge


def _get_item_key(item: Any) -> Any:
    """Extract a hashable key from an item (node or edge).

    For edges (tuples with 3+ elements), returns the edge key (source, target).
    For nodes, returns the item itself.

    Args:
        item: Node or edge item

    Returns:
        Hashable key
    """
    if isinstance(item, tuple) and len(item) >= 3:
        # This is an edge with data
        return _get_edge_key(item)
    return item


def _resolve_selector(value: Any, selector: str) -> float:
    """Resolve a selector path on an uncertainty value.

    Supports selectors like:
        - metric__mean - mean value
        - metric__std - standard deviation
        - metric__ci95__low - 95% confidence interval lower bound
        - metric__ci95__high - 95% confidence interval upper bound
        - metric__ci95__width - 95% confidence interval width
        - metric (no selector) - defaults to mean/point estimate

    Args:
        value: The value (may be dict with uncertainty info from uncertainty
              estimation, or a scalar numeric value)
        selector: The selector suffix (e.g., "mean", "std", "ci95__low")

    Returns:
        Resolved numeric value (float)

    Note:
        When uncertainty is computed, values are stored as dicts with keys:
        'mean', 'std', 'quantiles', etc. This function extracts the requested
        component. For deterministic values (no uncertainty), returns the
        scalar value or 0.0 for missing selectors.
    """
    # If no selector or value is scalar, return as-is
    if not selector or not isinstance(value, dict):
        if isinstance(value, dict) and "mean" in value:
            return value["mean"]
        return float(value) if isinstance(value, (int, float)) else 0.0

    # Parse selector components
    parts = selector.split("__")

    if not parts:
        # No selector - default to mean
        if isinstance(value, dict) and "mean" in value:
            return value["mean"]
        return float(value) if isinstance(value, (int, float)) else 0.0

    # Handle simple selectors
    if parts[0] == "mean":
        return value.get("mean", 0.0)
    elif parts[0] == "std":
        return value.get("std", 0.0)

    # Handle CI selectors like ci95__low, ci95__high, ci95__width
    if parts[0].startswith("ci") and len(parts) >= 2:
        # Extract CI level (e.g., "95" from "ci95")
        ci_level_str = parts[0][2:]  # Remove "ci" prefix
        try:
            ci_level = float(ci_level_str) / 100.0  # Convert to fraction
        except ValueError:
            ci_level = 0.95  # Default

        # Get quantiles dict
        quantiles = value.get("quantiles", {})

        if parts[1] == "low":
            # Lower bound of CI
            lower_q = (1 - ci_level) / 2
            return quantiles.get(lower_q, value.get("mean", 0.0))
        elif parts[1] == "high":
            # Upper bound of CI
            upper_q = 1 - (1 - ci_level) / 2
            return quantiles.get(upper_q, value.get("mean", 0.0))
        elif parts[1] == "width":
            # CI width
            lower_q = (1 - ci_level) / 2
            upper_q = 1 - (1 - ci_level) / 2
            low = quantiles.get(lower_q, value.get("mean", 0.0))
            high = quantiles.get(upper_q, value.get("mean", 0.0))
            return high - low

    # Fallback to mean
    if isinstance(value, dict) and "mean" in value:
        return value["mean"]
    return float(value) if isinstance(value, (int, float)) else 0.0


def _top_k_stream(
    items: List[Any],
    key_fn: Callable[[Any], float],
    k: int,
    *,
    desc: bool = True,
    tie_breaker_fn: Optional[Callable[[Any], Any]] = None
) -> List[Any]:
    """Select top-k items using streaming algorithm (O(n log k) instead of O(n log n)).
    
    This function efficiently selects the top k items from a list without fully sorting.
    Uses a min-heap to maintain only the k largest elements, resulting in O(n log k)
    time complexity instead of O(n log n) for full sorting.
    
    Args:
        items: List of items to select from
        key_fn: Function to extract comparison value from item
        k: Number of items to select (top k)
        desc: If True (default), return highest values first (descending order)
              If False, return lowest values first (ascending order)
        tie_breaker_fn: Optional function to produce stable tie-breaking key
                       Should return a comparable value (e.g., node_id, tuple)
    
    Returns:
        List of top k items, ordered by value (descending if desc=True)
        If k <= 0, returns empty list
        If len(items) <= k, returns all items sorted by value
    
    Examples:
        >>> items = [('A', 10), ('B', 20), ('C', 15)]
        >>> key_fn = lambda x: x[1]
        >>> tie_breaker = lambda x: x[0]
        >>> result = _top_k_stream(items, key_fn, 2, desc=True, tie_breaker_fn=tie_breaker)
        >>> result  # [('B', 20), ('C', 15)]
    
    Implementation Notes:
        - Uses heapq with fixed-size min-heap for efficiency
        - Heap elements: (value, tie_breaker, index, item) for proper ordering
        - For descending (desc=True): inverts values to use min-heap as max-heap
        - For ascending (desc=False): uses values directly in min-heap
        - Tie-breaking ensures deterministic results for equal values
        - After selection, returns items sorted from best to worst
    """
    import heapq
    
    # Edge case: k <= 0
    if k <= 0:
        return []
    
    # Edge case: items is empty
    if not items:
        return []
    
    # Edge case: k >= len(items), just sort and return
    if k >= len(items):
        # Build sort key with tie-breaking
        def sort_key(item):
            value = key_fn(item)
            tie_breaker = tie_breaker_fn(item) if tie_breaker_fn else item
            # For descending, negate value; for ascending, use as-is
            # Tie-breaker is always ascending (lower is better for stability)
            if desc:
                return (-value, tie_breaker)
            else:
                return (value, tie_breaker)
        
        return sorted(items, key=sort_key)
    
    # Main algorithm: maintain a min-heap of size k
    # For descending order (get largest k): use min-heap with original values
    #   heap[0] = minimum of k items = worst of the k largest
    # For ascending order (get smallest k): use min-heap with negated values
    #   heap[0] = minimum negated = maximum original = worst of the k smallest
    heap = []
    
    for idx, item in enumerate(items):
        value = key_fn(item)
        tie_breaker = tie_breaker_fn(item) if tie_breaker_fn else idx
        
        # For descending (want largest k), use value directly
        # For ascending (want smallest k), negate value
        if desc:
            heap_value = value  # Keep largest, so use min-heap with actual values
        else:
            heap_value = -value  # Keep smallest, so negate for min-heap
        
        # Heap element: (heap_value, tie_breaker, idx, item)
        heap_element = (heap_value, tie_breaker, idx, item)
        
        if len(heap) < k:
            heapq.heappush(heap, heap_element)
        else:
            # Replace if current item is better than worst in heap
            # For desc=True: heap[0] = min = worst of k largest, replace if new > min
            # For desc=False: heap[0] = min negated = max original = worst of k smallest, replace if new negated < min negated
            # In both cases: replace if heap_element > heap[0]
            if heap_element > heap[0]:
                heapq.heapreplace(heap, heap_element)
    
    # Extract items from heap and sort them properly
    # Heap is in min-heap order, so we need to sort to get proper output order
    selected = [item for _, _, _, item in heap]
    
    # Sort selected items by their actual values (best to worst)
    def final_sort_key(item):
        value = key_fn(item)
        tie_breaker = tie_breaker_fn(item) if tie_breaker_fn else item
        if desc:
            return (-value, tie_breaker)  # Descending: negate for sorting
        else:
            return (value, tie_breaker)  # Ascending: positive for sorting
    
    return sorted(selected, key=final_sort_key)


def _apply_ordering(
    items: List[Any], order_by: List[OrderItem], attributes: Dict[str, Dict]
) -> List[Any]:
    """Apply ORDER BY to items.

    For nodes: Uses computed attributes
    For edges: Uses computed attributes or edge data attributes (e.g., weight)

    Supports uncertainty selectors:
        - metric__mean (or just metric)
        - metric__std
        - metric__ci95__low
        - metric__ci95__high
        - metric__ci95__width
    """
    if not order_by:
        return items

    def sort_key(item):
        values = []
        for order_item in order_by:
            key = order_item.key

            # Parse key for selector syntax (metric__selector)
            if "__" in key:
                # Split on __ to separate metric name from selector
                parts = key.split("__", 1)
                metric_name = parts[0]
                selector = parts[1]
            else:
                metric_name = key
                selector = None

            # Get value from computed attributes first
            if metric_name in attributes:
                # For edges, use hashable key
                item_key = _get_item_key(item)
                value = attributes[metric_name].get(item_key, 0)

                # Resolve selector if present
                if selector:
                    value = _resolve_selector(value, selector)
                else:
                    # Handle uncertainty dict format: extract 'mean' value by default
                    if isinstance(value, dict) and "mean" in value:
                        value = value["mean"]
            else:
                # For edges, try to get from edge data (e.g., weight)
                if (
                    isinstance(item, tuple)
                    and len(item) >= 3
                    and isinstance(item[2], dict)
                ):
                    value = item[2].get(metric_name, 0)
                else:
                    value = 0

            # Negate for descending
            if order_item.desc and isinstance(value, (int, float)):
                value = -value

            values.append(value)

        return tuple(values)

    return sorted(items, key=sort_key)


def _coverage_bitmask(
    groups: Dict[Any, List[Any]],
    select: SelectStmt,
    network: Any,
    G: nx.Graph,
    num_groups: int,
) -> Set[Any]:
    """Apply coverage filtering using bitmask for fast membership testing.
    
    This function uses integer bitmasks instead of sets to efficiently track
    which groups each item appears in. This is significantly faster than
    set operations, especially for large numbers of groups.
    
    Args:
        groups: Dictionary mapping group keys to lists of items
        select: SELECT statement with coverage configuration
        network: Multilayer network
        G: Core network graph
        num_groups: Total number of groups
    
    Returns:
        Set of allowed identity values (items passing coverage filter)
    
    Coverage Modes:
        - mode="all": Items in ALL groups (bitwise AND of all bits set)
        - mode="any": Items in ANY group (always returns all items)
        - mode="at_least": Items in at least k groups
        - mode="exact": Items in exactly k groups
        - mode="fraction": Items in at least fraction p of groups
    
    Implementation:
        - Each group gets an index i in [0, num_groups-1]
        - For each item in group i, set bit i in its bitmask
        - Coverage check is then simple bitwise operations:
          - all: mask == all_mask (all bits set)
          - at_least k: popcount(mask) >= k
          - etc.
    
    Time Complexity:
        - Building masks: O(total_items) single pass
        - Filtering: O(unique_items) with fast bitwise ops
        - Compare to set-based: O(total_items * groups) for intersections
    
    Example:
        3 groups, 4 items:
        - Item A in groups 0,1,2: mask = 0b111 = 7
        - Item B in groups 0,1:   mask = 0b011 = 3
        - Item C in group 0:      mask = 0b001 = 1
        
        mode="all" with 3 groups: only A passes (mask == 7)
        mode="at_least", k=2: A and B pass (popcount >= 2)
    """
    mode = select.coverage_mode
    k = select.coverage_k
    p = select.coverage_p
    
    # Early return for "any" mode - no filtering needed
    if mode == "any":
        # Return all unique identities
        all_ids = set()
        for group_items in groups.values():
            for item in group_items:
                identity = _get_coverage_identity(item, select, network, G)
                all_ids.add(identity)
        return all_ids
    
    # Build deterministic group ordering
    # Sort group keys to ensure deterministic bit assignment
    group_keys_sorted = sorted(groups.keys(), key=lambda x: str(x))
    group_to_index = {key: idx for idx, key in enumerate(group_keys_sorted)}
    
    # Build bitmask map: identity -> bitmask
    # Each bit represents presence in a group
    mask_map: Dict[Any, int] = {}
    
    for group_key, group_items in groups.items():
        group_idx = group_to_index[group_key]
        bit = 1 << group_idx  # Bit for this group
        
        for item in group_items:
            identity = _get_coverage_identity(item, select, network, G)
            if identity not in mask_map:
                mask_map[identity] = 0
            mask_map[identity] |= bit
    
    # Calculate all_mask (all bits set for num_groups)
    # For 3 groups: all_mask = 0b111 = 7
    all_mask = (1 << num_groups) - 1
    
    # Apply coverage mode to determine allowed identities
    allowed_ids = set()
    
    for item_id, mask in mask_map.items():
        # Count number of bits set (number of groups item appears in)
        # Use Brian Kernighan's algorithm for fast popcount
        count = 0
        temp_mask = mask
        while temp_mask:
            temp_mask &= temp_mask - 1
            count += 1
        
        # Apply coverage mode
        if mode == "all":
            if mask == all_mask:
                allowed_ids.add(item_id)
        elif mode == "at_least":
            if k is not None and count >= k:
                allowed_ids.add(item_id)
        elif mode == "exact":
            if k is not None and count == k:
                allowed_ids.add(item_id)
        elif mode == "fraction":
            if p is not None and num_groups > 0:
                import math
                # Use ceiling to ensure we require at least p fraction of groups
                threshold = math.ceil(p * num_groups)
                if count >= threshold:
                    allowed_ids.add(item_id)
    
    return allowed_ids


def _apply_grouping_and_coverage(
    items: List[Any],
    select: SelectStmt,
    network: Any,
    G: nx.Graph,
    attributes: Dict[str, Dict],
    progress: bool = False,
) -> Tuple[List[Any], Optional[Dict[str, Any]]]:
    """Apply grouping, per-group operations, and coverage filtering.

    This handles:
    1. Grouping items by specified fields (e.g., "layer")
    2. Per-group ordering (if order_by is specified)
    3. Per-group top-k limiting (if limit_per_group is specified)
    4. Coverage filtering across groups (if coverage_mode is specified)

    Args:
        items: List of items (nodes or edges)
        select: SELECT statement with grouping/coverage configuration
        network: Multilayer network
        G: Core network graph
        attributes: Computed attributes dict
        progress: If True, log progress messages

    Returns:
        Tuple of (filtered items, grouping_metadata)
        grouping_metadata is a dict with grouping info, or None if no grouping

    Raises:
        DslExecutionError: If configuration is invalid
    """
    logger = logging.getLogger(__name__)
    # Validate grouping is set up when needed
    if not select.group_by:
        # Check for coverage specifically to provide better error
        if select.coverage_mode:
            raise GroupingError(
                "coverage(...) requires an active grouping (e.g. per_layer(), group_by('layer')). "
                "No grouping is currently active.\n"
                "Example:\n"
                '    Q.nodes().from_layers(L["*"])\n'
                '        .per_layer().top_k(5, "degree").end_grouping()\n'
                '        .coverage(mode="all")'
            )
        # Generic check for other operations
        if select.limit_per_group is not None:
            raise DslExecutionError(
                "Grouping must be configured (via .group_by() or .per_layer()) "
                "before using .top_k()"
            )

    # Smart defaults: Ensure attributes exist before ordering
    if select.order_by:
        for order_item in select.order_by:
            # Skip validation for attributes that will be created by summarize
            if select.summarize_aggs and order_item.key in select.summarize_aggs:
                continue

            # Skip validation for attributes that will be created by rename
            if select.rename_map and order_item.key in select.rename_map:
                continue

            _ensure_attribute(
                attr_name=order_item.key,
                attributes=attributes,
                items=items,
                network=network,
                G=G,
                select=select,
                auto_compute=True,
            )

    # Build groups
    if progress:
        logger.info(f"  Grouping {len(items)} items by {select.group_by}")
    groups: Dict[Any, List[Any]] = {}
    for item in items:
        group_key = _get_group_key(item, select, network, G)
        if group_key not in groups:
            groups[group_key] = []
        groups[group_key].append(item)
    
    if progress:
        logger.info(f"  Created {len(groups)} groups")

    # Per-group ordering
    if select.order_by:
        if progress:
            logger.info(f"  Applying per-group ORDER BY")
        for key in groups:
            groups[key] = _apply_ordering(groups[key], select.order_by, attributes)

    # Per-group top-k (optimized with streaming algorithm)
    if select.limit_per_group is not None:
        k = select.limit_per_group
        if progress:
            logger.info(f"  Applying per-group top-k (k={k}) with streaming algorithm")
        
        # Build key function and tie-breaker for streaming top-k
        if select.order_by:
            # Use the ordering specification for top-k
            order_item = select.order_by[0]  # Use first order item as primary key
            key_attr = order_item.key
            desc = order_item.desc
            
            # Parse key for selector syntax (metric__selector)
            if "__" in key_attr:
                parts = key_attr.split("__", 1)
                metric_name = parts[0]
                selector = parts[1]
            else:
                metric_name = key_attr
                selector = None
            
            def key_fn(item):
                """Extract comparison value from item."""
                item_key = _get_item_key(item)
                if metric_name in attributes:
                    value = attributes[metric_name].get(item_key, 0)
                    
                    # Resolve selector if present
                    if selector:
                        value = _resolve_selector(value, selector)
                    else:
                        # Handle uncertainty dict format: extract 'mean' value by default
                        if isinstance(value, dict) and "mean" in value:
                            value = value["mean"]
                else:
                    # For edges, try to get from edge data
                    if (
                        isinstance(item, tuple)
                        and len(item) >= 3
                        and isinstance(item[2], dict)
                    ):
                        value = item[2].get(metric_name, 0)
                    else:
                        value = 0
                
                return float(value) if isinstance(value, (int, float)) else 0.0
            
            def tie_breaker_fn(item):
                """Generate deterministic tie-breaker key."""
                # For nodes: use (node_id, layer)
                # For edges: use (src, tgt, src_layer, tgt_layer)
                if isinstance(item, tuple) and len(item) >= 2:
                    if not isinstance(item[0], tuple):
                        # Node: (node_id, layer)
                        return (str(item[0]), str(item[1]))
                    else:
                        # Edge: ((src, src_layer), (tgt, tgt_layer), ...)
                        src = item[0]
                        tgt = item[1]
                        if isinstance(src, tuple) and isinstance(tgt, tuple):
                            return (str(src[0]), str(src[1]), str(tgt[0]), str(tgt[1]))
                return str(item)
            
            # Apply streaming top-k per group
            for group_key in groups:
                groups[group_key] = _top_k_stream(
                    groups[group_key],
                    key_fn,
                    k,
                    desc=desc,
                    tie_breaker_fn=tie_breaker_fn
                )
        else:
            # No ordering specified, just slice
            for group_key in groups:
                groups[group_key] = groups[group_key][:k]

    # Coverage filtering (optimized with bitmask)
    if select.coverage_mode:
        if progress:
            mode_desc = select.coverage_mode
            if select.coverage_k is not None:
                mode_desc += f" k={select.coverage_k}"
            elif select.coverage_p is not None:
                mode_desc += f" p={select.coverage_p}"
            logger.info(f"  Applying coverage filter (mode={mode_desc}) with bitmask")
        
        # Use bitmask-based coverage filtering
        num_groups = len(groups)
        allowed_ids = _coverage_bitmask(groups, select, network, G, num_groups)

        # Filter groups to only include allowed identities
        for group_key in groups:
            filtered_group = []
            for item in groups[group_key]:
                identity = _get_coverage_identity(item, select, network, G)
                if identity in allowed_ids:
                    filtered_group.append(item)
            groups[group_key] = filtered_group
        
        if progress:
            logger.info(f"  Coverage filter kept {len(allowed_ids)} unique items across groups")

    # Flatten groups back to a single list (ordered by group key for determinism)
    new_items = []
    for key in sorted(groups.keys(), key=lambda x: str(x)):
        new_items.extend(groups[key])
    
    if progress:
        logger.info(f"  Flattened to {len(new_items)} items after grouping operations")

    # Build grouping metadata
    grouping_kind = "custom"
    grouping_keys = list(select.group_by)

    # Detect common grouping patterns
    if select.group_by == ["layer"]:
        grouping_kind = "per_layer"
    elif select.group_by == ["src_layer", "dst_layer"]:
        grouping_kind = "per_layer_pair"

    # Build group metadata list
    group_metadata_list = []
    for group_key in sorted(groups.keys(), key=lambda x: str(x)):
        group_items = groups[group_key]

        # Build key dict
        if isinstance(group_key, tuple):
            key_dict = {k: v for k, v in zip(grouping_keys, group_key)}
        else:
            key_dict = {grouping_keys[0]: group_key}

        group_metadata_list.append(
            {
                "key": key_dict,
                "n_items": len(group_items),
            }
        )

    grouping_metadata = {
        "kind": grouping_kind,
        "target": select.target.value,
        "keys": grouping_keys,
        "groups": group_metadata_list,
    }

    return new_items, grouping_metadata


def _get_group_key(item: Any, select: SelectStmt, network: Any, G: nx.Graph) -> Any:
    """Get the grouping key for an item.

    Args:
        item: Node or edge item
        select: SELECT statement with group_by fields
        network: Multilayer network
        G: Core network graph

    Returns:
        Grouping key (single value or tuple)
    """
    keys = []
    for field in select.group_by:
        if field == "layer":
            # Special handling for layer field
            if isinstance(item, tuple) and len(item) >= 2:
                # Node: (node_id, layer)
                if not isinstance(item[0], tuple):
                    keys.append(str(item[1]))
                    continue
                # Edge: ((src_node, src_layer), (tgt_node, tgt_layer), {data}?)
                src = item[0]
                if isinstance(src, tuple) and len(src) >= 2:
                    keys.append(str(src[1]))
                    continue
            # Fallback to attribute lookup
            value = _get_attribute_value(item, "layer", network, G)
            keys.append(str(value) if value is not None else "None")
        elif field == "src_layer":
            # Special handling for src_layer field (edges only)
            if isinstance(item, tuple) and len(item) >= 2:
                # Edge: ((src_node, src_layer), (tgt_node, tgt_layer), {data}?)
                src = item[0]
                if isinstance(src, tuple) and len(src) >= 2:
                    keys.append(str(src[1]))
                    continue
            # Fallback to attribute lookup
            value = _get_attribute_value(item, "src_layer", network, G)
            keys.append(str(value) if value is not None else "None")
        elif field == "dst_layer":
            # Special handling for dst_layer field (edges only)
            if isinstance(item, tuple) and len(item) >= 2:
                # Edge: ((src_node, src_layer), (tgt_node, tgt_layer), {data}?)
                tgt = item[1]
                if isinstance(tgt, tuple) and len(tgt) >= 2:
                    keys.append(str(tgt[1]))
                    continue
            # Fallback to attribute lookup
            value = _get_attribute_value(item, "dst_layer", network, G)
            keys.append(str(value) if value is not None else "None")
        else:
            # Generic attribute lookup
            value = _get_attribute_value(item, field, network, G)
            keys.append(str(value) if value is not None else "None")

    return tuple(keys) if len(keys) > 1 else keys[0]


def _get_coverage_identity(
    item: Any, select: SelectStmt, network: Any, G: nx.Graph
) -> Any:
    """Get the coverage identity for an item.

    For nodes, the identity is typically the node ID (item[0]).
    This allows (node_id, layer1) and (node_id, layer2) to be treated
    as the same entity for coverage counting.

    Args:
        item: Node or edge item
        select: SELECT statement with coverage_id_field
        network: Multilayer network
        G: Core network graph

    Returns:
        Coverage identity (typically node ID for nodes)
    """
    id_field = select.coverage_id_field or "id"

    # Node queries
    if select.target == Target.NODES:
        if id_field == "id":
            # Use logical node ID (first element of tuple)
            if isinstance(item, tuple) and len(item) >= 1:
                return item[0]
            return item
        # Future: other fields via _get_attribute_value
        return _get_attribute_value(item, id_field, network, G)
    else:
        # Edge queries (if ever supported)
        if id_field == "id":
            return _get_edge_key(item)
        return _get_attribute_value(item, id_field, network, G)


def _parse_aggregation_expr(expr: str) -> Tuple[str, Optional[str], Optional[float]]:
    """Parse an aggregation expression like 'mean(degree)', 'n()', or 'quantile(degree, 0.95)'.

    Args:
        expr: Aggregation expression string

    Returns:
        Tuple of (agg_func, attr_name, quantile_p) where:
            - attr_name is None for n()
            - quantile_p is None except for quantile() function

    Raises:
        ValueError: If expression format is invalid
    """
    import re

    # Match pattern: func(attr) or func() or func(attr, param)
    match = re.match(r"([a-z_]+)\(([^)]*)\)$", expr.strip())
    if not match:
        raise ValueError(
            f"Invalid aggregation expression: '{expr}'. Expected format: 'func(attr)', 'func(attr, param)', or 'n()'"
        )

    func = match.group(1)
    args_str = match.group(2).strip() if match.group(2) else None

    if not args_str:
        # func() - e.g., n()
        return func, None, None

    # Split arguments by comma
    args = [arg.strip() for arg in args_str.split(",")]

    if len(args) == 1:
        # func(attr) - e.g., mean(degree)
        return func, args[0], None
    elif len(args) == 2:
        # func(attr, param) - e.g., quantile(degree, 0.95)
        attr_name = args[0]
        try:
            param = float(args[1])
        except ValueError:
            raise ValueError(
                f"Invalid parameter in aggregation expression: '{args[1]}' (expected numeric value)"
            )
        return func, attr_name, param
    else:
        raise ValueError(
            f"Invalid aggregation expression: '{expr}'. Too many arguments (max 2)"
        )


def _apply_aggregation(
    values: List[Any], func: str, quantile_p: Optional[float] = None
) -> Any:
    """Apply an aggregation function to a list of values.

    Args:
        values: List of numeric values (or uncertainty dicts/UQValues)
        func: Aggregation function name (mean, sum, min, max, std, var, median, quantile, count, n)
        quantile_p: Quantile probability for 'quantile' function (e.g., 0.95 for 95th percentile)

    Returns:
        Aggregated result (float for numeric ops, int for count, or UQ dict for UQ-aware aggregation)
        Returns NaN for empty lists on statistical functions

    Raises:
        ValueError: If function is unknown or quantile_p is missing for quantile function
        UQReductionError: If UQ aggregation is requested for unsupported function
    """
    import numpy as np

    if func in ("n", "count"):
        return len(values)

    # Return NaN for empty lists on statistical operations
    if not values:
        return float("nan")

    # Check if any values are UQ dicts - if so, use UQ algebra
    has_uq = any(isinstance(v, dict) and ("mean" in v or "value" in v) for v in values)
    
    if has_uq:
        # Import UQ algebra for uncertainty-aware aggregation
        from .uq_algebra import UQValue, UQAlgebra, convert_to_uqvalue
        from .uq_resolution import UQReductionError
        
        # Convert all values to UQValue
        uq_values = []
        for v in values:
            try:
                uq_values.append(convert_to_uqvalue(v))
            except Exception:
                # If conversion fails, skip (or could raise)
                continue
        
        if not uq_values:
            return float("nan")
        
        # Apply UQ-aware aggregation
        if func == "mean":
            # Use UQ algebra for weighted mean
            result_uqvalue = UQAlgebra.aggregate_mean(uq_values)
            return result_uqvalue.to_dict()
        elif func == "sum":
            # Sum via repeated addition
            result_uqvalue = uq_values[0]
            for uqv in uq_values[1:]:
                # UQValue doesn't have __add__, so we aggregate with equal weights
                # and then scale
                pass  # TODO: implement proper sum if needed
            # For now, fallback to summing means
            return sum(uqv.mean for uqv in uq_values)
        elif func == "count":
            return len(uq_values)
        else:
            # For other functions, UQ aggregation is not yet supported
            raise UQReductionError(
                f"UQ-aware aggregation for '{func}' is not yet implemented. "
                f"Supported: mean, sum, count. "
                f"Consider extracting mean values first or disable UQ for aggregation."
            )
    
    # Non-UQ path: extract numeric values
    numeric_values = []
    for v in values:
        if isinstance(v, dict) and "mean" in v:
            # Extract mean value from uncertainty dict (should not reach here if has_uq=True)
            numeric_values.append(v["mean"])
        else:
            numeric_values.append(v)

    if func == "mean":
        return float(np.mean(numeric_values))
    elif func == "sum":
        return float(np.sum(numeric_values))
    elif func == "min":
        return float(np.min(numeric_values))
    elif func == "max":
        return float(np.max(numeric_values))
    elif func == "std":
        return float(np.std(numeric_values))
    elif func == "var":
        return float(np.var(numeric_values))
    elif func == "median":
        return float(np.median(numeric_values))
    elif func == "quantile":
        if quantile_p is None:
            raise ValueError(
                "quantile() aggregation requires a probability argument (e.g., quantile(attr, 0.95))"
            )
        return float(np.quantile(numeric_values, quantile_p))
    else:
        raise ValueError(f"Unknown aggregation function: '{func}'")


def _apply_post_filters(
    items: List[Any],
    post_filters: List[Dict[str, Any]],
    network: Any,
    G: nx.Graph,
) -> List[Any]:

    """Apply post-filters like has_community(), tail(), sample(), etc.
    

    Args:
        items: List of items to filter
        post_filters: List of filter specifications
        network: Multilayer network
        G: Core network graph

    Returns:
        Filtered list of items
    """
    filtered_items = items

    for filter_spec in post_filters:
        filter_type = filter_spec.get("type")

        if filter_type == "community_predicate":
            predicate = filter_spec["predicate"]

            if callable(predicate):
                # Lambda or function - call with each item
                filtered_items = [item for item in filtered_items if predicate(item)]
            else:
                # Direct value - match against "community" attribute
                filtered_items = [
                    item
                    for item in filtered_items
                    if G.nodes.get(item, {}).get("community") == predicate
                ]

        
        elif filter_type == "expression":
            # String-based expression filtering
            expr = filter_spec["expr"]
            new_items = []
            for item in filtered_items:
                # Build context dict from item attributes
                if isinstance(item, dict):
                    context = item
                else:
                    # Try to extract attributes from graph
                    context = {"id": item}
                    if hasattr(item, "__iter__") and len(item) >= 2:
                        context["layer"] = item[1] if len(item) > 1 else None
                    # Add graph attributes
                    if G and G.has_node(item):
                        context.update(G.nodes[item])
                    # Add degree
                    if G and G.has_node(item):
                        context["degree"] = G.degree(item)
                
                try:
                    # Safe evaluation of expression
                    if _safe_eval_expr(expr, context):
                        new_items.append(item)
                except (ValueError, KeyError, TypeError):
                    # Skip items that fail evaluation
                    pass
            filtered_items = new_items
        
        elif filter_type == "tail":
            # Keep last n items
            n = filter_spec["n"]
            filtered_items = filtered_items[-n:] if n > 0 and len(filtered_items) > n else filtered_items
        
        elif filter_type == "sample":
            # Random sampling
            n = filter_spec["n"]
            seed = filter_spec.get("seed")
            if n >= len(filtered_items):
                # Don't sample if n >= total items
                pass
            else:
                rng = random.Random(seed) if seed is not None else random
                filtered_items = rng.sample(filtered_items, n)
        
        elif filter_type == "slice":
            # Array slicing
            start = filter_spec["start"]
            end = filter_spec.get("end")
            filtered_items = filtered_items[start:end]
        
        elif filter_type == "last":
            # Keep only last item
            filtered_items = filtered_items[-1:] if filtered_items else []
    

    return filtered_items


def _safe_eval_expr(expr: str, context: dict) -> bool:
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


def _apply_aggregate(
    items: List[Any],
    attributes: Dict[str, Dict],
    select: SelectStmt,
    network: Any,
    G: nx.Graph,
) -> Tuple[List[Any], Dict[str, Dict]]:
    """Apply aggregate operation with support for lambdas and direct attributes.

    Similar to summarize but more flexible:
    - Supports lambda functions
    - Supports direct attribute references
    - Supports builtin aggregation functions

    Args:
        items: List of items
        attributes: Computed attributes
        select: SELECT statement
        network: Multilayer network
        G: Core network graph

    Returns:
        Tuple of (aggregated_items, aggregated_attributes)
    """
    # Build groups if grouping is active
    if select.group_by:
        groups: Dict[Any, List[Any]] = {}
        for item in items:
            group_key = _get_group_key(item, select, network, G)
            if group_key not in groups:
                groups[group_key] = []
            groups[group_key].append(item)
    else:
        # No grouping - treat all items as one group
        groups = {"__global__": items}

    # Compute aggregations per group
    agg_items = []
    agg_attrs: Dict[str, Dict] = {}

    for agg_name in select.aggregate_specs.keys():
        agg_attrs[agg_name] = {}

    for group_key, group_items in groups.items():
        # Create an aggregated item representing this group
        if select.group_by:
            agg_item = group_key
        else:
            agg_item = "__global__"

        agg_items.append(agg_item)

        # Compute each aggregation for this group
        for agg_name, agg_spec in select.aggregate_specs.items():
            if callable(agg_spec):
                # Lambda function - call with first item (representative)
                # For more complex aggregations, the lambda should access network state
                if group_items:
                    result = agg_spec(group_items[0])
                else:
                    result = None
            elif isinstance(agg_spec, str):
                # Check if it's a function call like "mean(degree)" or "quantile(degree, 0.95)"
                if "(" in agg_spec and ")" in agg_spec:
                    func, attr, quantile_p = _parse_aggregation_expr(agg_spec)

                    if func in ("n", "count"):
                        # Count of items in group
                        result = len(group_items)
                    else:
                        # Need to extract attribute values from group items
                        if attr in attributes:
                            # Attribute was computed
                            values = []
                            for item in group_items:
                                item_key = _get_item_key(item)
                                if item_key in attributes[attr]:
                                    values.append(attributes[attr][item_key])
                        else:
                            # Try to extract from item data (e.g., edge weight, node attributes)
                            values = []
                            for item in group_items:
                                val = _get_attribute_value(item, attr, network, G)
                                if val is not None:
                                    values.append(val)

                            if not values:
                                raise DslExecutionError(
                                    f"Cannot aggregate on '{attr}' - attribute not found or computed"
                                )

                        # Apply aggregation
                        result = _apply_aggregation(values, func, quantile_p)
                else:
                    # Direct attribute reference - just get the value
                    # For grouped results, get from first item
                    if group_items:
                        first_item = group_items[0]
                        item_key = _get_item_key(first_item)
                        if agg_spec in attributes:
                            result = attributes[agg_spec].get(item_key)
                        else:
                            # Try to get from node/edge attributes
                            result = G.nodes.get(first_item, {}).get(agg_spec)
                    else:
                        result = None
            else:
                # Unknown aggregation type
                result = None

            agg_attrs[agg_name][agg_item] = result

    return agg_items, agg_attrs


def _apply_mutate(
    items: List[Any],
    attributes: Dict[str, Dict],
    select: SelectStmt,
    network: Any,
    G: nx.Graph,
) -> Dict[str, Dict]:
    """Apply mutate operation - transform or create new columns row-by-row.

    Similar to dplyr::mutate, this operation creates new columns or modifies
    existing ones by applying transformations to each row individually
    (unlike aggregate/summarize which operate on groups).

    Args:
        items: List of items (nodes or edges)
        attributes: Computed attributes dict
        select: SELECT statement with mutate_specs
        network: Multilayer network
        G: Core network graph

    Returns:
        Updated attributes dict with new/modified columns
    """
    if not select.mutate_specs:
        return attributes

    # Create new attribute columns
    for new_col, transformation in select.mutate_specs.items():
        attributes[new_col] = {}

        for item in items:
            item_key = _get_item_key(item)

            # Build a row dict with all current attributes for this item
            row = {}
            for attr_name, attr_dict in attributes.items():
                if item_key in attr_dict:
                    row[attr_name] = attr_dict[item_key]

            # Add node/edge attributes from network if available
            if select.target == Target.NODES:
                if isinstance(item, tuple):
                    node, layer = item
                    node_attrs = G.nodes.get(item, {})
                    row.update(node_attrs)
                    row["id"] = node
                    row["layer"] = layer
                else:
                    node_attrs = G.nodes.get(item, {})
                    row.update(node_attrs)
                    row["id"] = item
            elif select.target == Target.EDGES:
                if isinstance(item, tuple) and len(item) >= 2:
                    edge_attrs = (
                        G.edges.get((item[0], item[1]), {})
                        if G.has_edge(item[0], item[1])
                        else {}
                    )
                    row.update(edge_attrs)

            # Apply transformation
            try:
                if callable(transformation):
                    # Lambda function
                    result = transformation(row)
                elif isinstance(transformation, str):
                    # String expression - could be evaluated, but for safety
                    # we'll just treat it as a reference to another column
                    result = row.get(transformation)
                else:
                    # Constant value
                    result = transformation
            except Exception as e:
                # If transformation fails, set to None
                logging.getLogger(__name__).debug(
                    f"Mutation failed for item {item_key}, column {new_col}: {e}"
                )
                result = None

            attributes[new_col][item_key] = result

    return attributes


def _apply_post_processing(
    items: List[Any],
    attributes: Dict[str, Dict],
    select: SelectStmt,
    network: Any,
    G: nx.Graph,
    progress: bool = False,
) -> Tuple[List[Any], Dict[str, Dict]]:
    """Apply post-processing operations to query results.

    Handles: aggregate, summarize, mutate, rank_by, zscore, distinct, rename, select, drop.

    Operations are applied in this order:
    1. aggregate (create aggregated columns with lambda support)
    2. summarize (create aggregated columns)
    3. mutate (create or transform columns row-by-row)
    4. rank_by (add rank columns)
    5. zscore (add z-score columns)
    6. distinct (deduplicate rows)
    7. rename (rename columns - must be before select/drop)
    8. select (filter columns)
    9. drop (remove columns)

    Args:
        items: List of items (nodes or edges)
        attributes: Computed attributes dict
        select: SELECT statement with post-processing specs
        network: Multilayer network
        G: Core network graph
        progress: If True, log progress messages

    Returns:
        Tuple of (processed_items, processed_attributes)
    """
    logger = logging.getLogger(__name__)
    
    # 0. Apply aggregate (more flexible aggregation with lambda support)
    if select.aggregate_specs:
        if progress:
            logger.info(f"    Applying aggregate on {len(select.aggregate_specs)} column(s)")
        items, attributes = _apply_aggregate(items, attributes, select, network, G)

    # 1. Apply summarize (aggregation over groups)
    if select.summarize_aggs:
        if progress:
            logger.info(f"    Applying summarize with {len(select.summarize_aggs)} aggregation(s)")
        items, attributes = _apply_summarize(items, attributes, select, network, G)

    # 2. Apply mutate (create or transform columns row-by-row)
    if select.mutate_specs:
        if progress:
            logger.info(f"    Applying mutate on {len(select.mutate_specs)} column(s)")
        attributes = _apply_mutate(items, attributes, select, network, G)

    # 3. Apply rank_by (add rank columns)
    if select.rank_specs:
        if progress:
            logger.info(f"    Applying rank_by for {len(select.rank_specs)} column(s)")
        attributes = _apply_rank_by(items, attributes, select, network, G)

    # 4. Apply zscore (add z-score columns)
    if select.zscore_attrs:
        if progress:
            logger.info(f"    Applying zscore for {len(select.zscore_attrs)} column(s)")
        attributes = _apply_zscore(items, attributes, select, network, G)

    # 5. Apply distinct (deduplicate rows)
    if select.distinct_cols is not None:
        if progress:
            logger.info(f"    Applying distinct on {len(select.distinct_cols) if select.distinct_cols else 'all'} column(s)")
        items = _apply_distinct(items, attributes, select)

    # 6. Apply rename (rename columns - must be before select/drop)
    if select.rename_map:
        if progress:
            logger.info(f"    Renaming {len(select.rename_map)} column(s)")
        attributes = _apply_rename(attributes, select.rename_map)

    # 7. Apply select (filter columns)
    if select.select_cols:
        if progress:
            logger.info(f"    Selecting {len(select.select_cols)} column(s)")
        attributes = _apply_select(attributes, select.select_cols)

    # 8. Apply drop (remove columns)
    if select.drop_cols:
        if progress:
            logger.info(f"    Dropping {len(select.drop_cols)} column(s)")
        attributes = _apply_drop(attributes, select.drop_cols)

    return items, attributes


def _apply_summarize(
    items: List[Any],
    attributes: Dict[str, Dict],
    select: SelectStmt,
    network: Any,
    G: nx.Graph,
) -> Tuple[List[Any], Dict[str, Dict]]:
    """Apply summarize operation - aggregate over groups.

    Args:
        items: List of items
        attributes: Computed attributes
        select: SELECT statement
        network: Multilayer network
        G: Core network graph

    Returns:
        Tuple of (summary_items, summary_attributes)
    """
    # Build groups if grouping is active
    if select.group_by:
        groups: Dict[Any, List[Any]] = {}
        for item in items:
            group_key = _get_group_key(item, select, network, G)
            if group_key not in groups:
                groups[group_key] = []
            groups[group_key].append(item)
    else:
        # No grouping - treat all items as one group
        groups = {"__global__": items}

    # Compute aggregations per group
    summary_items = []
    summary_attrs: Dict[str, Dict] = {}

    for agg_name, agg_expr in select.summarize_aggs.items():
        summary_attrs[agg_name] = {}

    for group_key, group_items in groups.items():
        # Create a summary item representing this group
        if select.group_by:
            summary_item = group_key
        else:
            summary_item = "__global__"

        summary_items.append(summary_item)

        # Compute each aggregation for this group
        for agg_name, agg_expr in select.summarize_aggs.items():
            func, attr, quantile_p = _parse_aggregation_expr(agg_expr)

            if func in ("n", "count"):
                # Count of items in group
                value = len(group_items)
            else:
                # Need to extract attribute values from group items
                if attr in attributes:
                    # Attribute was computed
                    values = []
                    for item in group_items:
                        item_key = _get_item_key(item)
                        if item_key in attributes[attr]:
                            values.append(attributes[attr][item_key])
                else:
                    # Try to extract from item data (e.g., edge weight, node attributes)
                    values = []
                    for item in group_items:
                        val = _get_attribute_value(item, attr, network, G)
                        if val is not None:
                            values.append(val)

                    if not values:
                        raise DslExecutionError(
                            f"Cannot aggregate on '{attr}' - attribute not found or computed"
                        )

                # Apply aggregation
                value = _apply_aggregation(values, func, quantile_p)

            summary_attrs[agg_name][summary_item] = value

    return summary_items, summary_attrs


def _apply_rank_by(
    items: List[Any],
    attributes: Dict[str, Dict],
    select: SelectStmt,
    network: Any,
    G: nx.Graph,
) -> Dict[str, Dict]:
    """Apply rank_by operation - add rank columns.

    Args:
        items: List of items
        attributes: Computed attributes
        select: SELECT statement
        network: Multilayer network
        G: Core network graph

    Returns:
        Updated attributes dict with rank columns
    """
    import pandas as pd

    # Build groups if grouping is active
    if select.group_by:
        groups: Dict[Any, List[Any]] = {}
        for item in items:
            group_key = _get_group_key(item, select, network, G)
            if group_key not in groups:
                groups[group_key] = []
            groups[group_key].append(item)
    else:
        # No grouping - treat all items as one group
        groups = {"__global__": items}

    # Apply ranking for each specified attribute
    for attr, method in select.rank_specs:
        if attr not in attributes:
            raise DslExecutionError(f"Cannot rank by '{attr}' - attribute not computed")

        rank_col_name = f"{attr}_rank"
        attributes[rank_col_name] = {}

        # Rank within each group
        for group_items in groups.values():
            # Get values for this group
            values = []
            item_keys = []
            for item in group_items:
                item_key = _get_item_key(item)
                item_keys.append(item_key)
                values.append(attributes[attr].get(item_key, 0))

            # Use pandas for ranking
            series = pd.Series(values, index=item_keys)
            ranks = series.rank(method=method, ascending=False)

            # Store ranks
            for item_key, rank in ranks.items():
                attributes[rank_col_name][item_key] = int(rank)

    return attributes


def _apply_zscore(
    items: List[Any],
    attributes: Dict[str, Dict],
    select: SelectStmt,
    network: Any,
    G: nx.Graph,
) -> Dict[str, Dict]:
    """Apply zscore operation - compute z-scores within groups.

    Args:
        items: List of items
        attributes: Computed attributes
        select: SELECT statement
        network: Multilayer network
        G: Core network graph

    Returns:
        Updated attributes dict with z-score columns
    """
    import numpy as np

    # Build groups if grouping is active
    if select.group_by:
        groups: Dict[Any, List[Any]] = {}
        for item in items:
            group_key = _get_group_key(item, select, network, G)
            if group_key not in groups:
                groups[group_key] = []
            groups[group_key].append(item)
    else:
        # No grouping - treat all items as one group
        groups = {"__global__": items}

    # Compute z-scores for each specified attribute
    for attr in select.zscore_attrs:
        if attr not in attributes:
            raise DslExecutionError(
                f"Cannot compute z-score for '{attr}' - attribute not computed"
            )

        zscore_col_name = f"{attr}_zscore"
        attributes[zscore_col_name] = {}

        # Compute z-score within each group
        for group_items in groups.values():
            # Get values for this group
            values = []
            item_keys = []
            for item in group_items:
                item_key = _get_item_key(item)
                item_keys.append(item_key)
                value = attributes[attr].get(item_key, 0)
                # Extract mean from uncertainty dict if present
                if isinstance(value, dict) and "mean" in value:
                    value = value["mean"]
                values.append(value)

            # Compute z-scores
            values_array = np.array(values)
            mean = np.mean(values_array)
            std = np.std(values_array)

            if std > 0:
                zscores = (values_array - mean) / std
            else:
                # Standard deviation is zero (constant values or single value) - all z-scores are 0
                zscores = np.zeros_like(values_array)

            # Store z-scores
            for item_key, zscore in zip(item_keys, zscores):
                attributes[zscore_col_name][item_key] = float(zscore)

    return attributes


def _apply_distinct(
    items: List[Any],
    attributes: Dict[str, Dict],
    select: SelectStmt,
) -> List[Any]:
    """Apply distinct operation - deduplicate rows.

    Args:
        items: List of items
        attributes: Computed attributes
        select: SELECT statement

    Returns:
        Deduplicated list of items
    """
    if not select.distinct_cols:
        # Deduplicate on all columns (items themselves)
        seen = set()
        unique_items = []
        for item in items:
            # Make hashable
            item_key = _get_item_key(item)
            if item_key not in seen:
                seen.add(item_key)
                unique_items.append(item)
        return unique_items
    else:
        # Deduplicate on specific columns
        seen = set()
        unique_items = []
        for item in items:
            item_key = _get_item_key(item)

            # Build key from specified columns
            key_parts = []
            for col in select.distinct_cols:
                if col in attributes and item_key in attributes[col]:
                    key_parts.append(attributes[col][item_key])
                else:
                    key_parts.append(None)

            key = tuple(key_parts)
            if key not in seen:
                seen.add(key)
                unique_items.append(item)

        return unique_items


def _apply_select(
    attributes: Dict[str, Dict],
    columns: List[str],
) -> Dict[str, Dict]:
    """Apply select operation - keep only specified columns.

    Args:
        attributes: Computed attributes
        columns: Columns to keep

    Returns:
        Filtered attributes dict
    """
    return {col: attributes[col] for col in columns if col in attributes}


def _apply_drop(
    attributes: Dict[str, Dict],
    columns: List[str],
) -> Dict[str, Dict]:
    """Apply drop operation - remove specified columns.

    Args:
        attributes: Computed attributes
        columns: Columns to drop

    Returns:
        Filtered attributes dict
    """
    return {col: vals for col, vals in attributes.items() if col not in columns}


def _apply_rename(
    attributes: Dict[str, Dict],
    rename_map: Dict[str, str],
) -> Dict[str, Dict]:
    """Apply rename operation - rename columns.

    Args:
        attributes: Computed attributes
        rename_map: Mapping from new names to old names

    Returns:
        Renamed attributes dict
    """
    result = {}
    for col, vals in attributes.items():
        # Check if this column should be renamed
        new_name = None
        for new, old in rename_map.items():
            if col == old:
                new_name = new
                break

        # Use new name if found, otherwise keep original
        result[new_name if new_name else col] = vals

    return result


# ==============================================================================
# Dynamics & Trajectories Execution (Part D)
# ==============================================================================


def execute_dynamics_stmt(network: Any, stmt: DynamicsStmt) -> Any:
    """Execute a DYNAMICS statement on a multilayer network.

    This function bridges the DSL dynamics API (Q.dynamics) with the existing
    dynamics module (D.process). It translates the DynamicsStmt AST into
    a SimulationStmt and executes it using the dynamics executor.

    Args:
        network: Multilayer network object
        stmt: DynamicsStmt from AST

    Returns:
        SimulationResult with trajectory data

    Example:
        >>> from py3plex.dsl import Q, L
        >>> sim = (
        ...     Q.dynamics("SIS", beta=0.3, mu=0.1)
        ...      .on_layers(L["contacts"])
        ...      .seed(0.01)
        ...      .run(steps=100, replicates=10, track=["prevalence"])
        ...      .execute(network)
        ... )
    """
    # Import dynamics components
    from py3plex.dynamics import run_simulation, _DynamicsConfig
    from py3plex.dynamics.ast import SimulationStmt, InitialSpec

    # Resolve layers
    resolved_layers = []
    if stmt.layer_expr:
        # Import layer evaluation from dynamics module
        from py3plex.dynamics.executor import _evaluate_layer_expr
        resolved_layers = list(_evaluate_layer_expr(stmt.layer_expr, network))

    # Build initial conditions
    initial_dict = {}
    initial_condition = {}

    # Handle seeding
    if stmt.seed_query is not None:
        # Execute the seed query to get nodes
        seed_result = _execute_select(network, stmt.seed_query, params={})
        initial_dict["infected"] = InitialSpec(query=stmt.seed_query)
        initial_condition["infections_nodes"] = seed_result.items
    elif stmt.seed_fraction is not None:
        # Use fraction-based seeding
        initial_dict["infected"] = InitialSpec(constant=stmt.seed_fraction)
        initial_condition["infections_fraction"] = stmt.seed_fraction
    else:
        # Default: 1% infected
        initial_dict["infected"] = InitialSpec(constant=0.01)
        initial_condition["infections_fraction"] = 0.01

    # Determine measures to track
    measures = stmt.track if stmt.track else ["prevalence"]

    # Create canonical _DynamicsConfig for provenance
    n_jobs = getattr(stmt, 'n_jobs', 1)  # Default to 1 if not set
    uq_config = getattr(stmt, 'uq_config', None)  # Get UQ config if set
    dynamics_config = _DynamicsConfig(
        model_id=stmt.process_name,
        model_params=stmt.params or {},
        layers=resolved_layers,
        layer_expr_original=str(stmt.layer_expr) if stmt.layer_expr else None,
        steps=stmt.steps or 100,
        replicates=stmt.replicates or 1,
        track=measures,
        initial_condition=initial_condition,
        seed=stmt.seed,
        n_jobs=n_jobs,
        uq_config=uq_config,
    )

    # Build SimulationStmt
    sim_stmt = SimulationStmt(
        process_name=stmt.process_name,
        layer_expr=stmt.layer_expr,
        coupling={},  # Could be extended in future
        params=stmt.params,
        initial=initial_dict,
        steps=stmt.steps,
        measures=measures,
        replicates=stmt.replicates,
        seed=stmt.seed,
        export_target=stmt.export_target,
    )

    # Attach dynamics_config to sim_stmt for provenance
    sim_stmt._dynamics_config = dynamics_config

    # Execute simulation using dynamics module
    result = run_simulation(network, sim_stmt)

    # Attach config hash to result metadata for provenance
    if hasattr(result, 'meta') and result.meta is not None:
        if 'provenance' not in result.meta:
            result.meta['provenance'] = {}
        result.meta['provenance']['dynamics_config_hash'] = dynamics_config.config_hash()
        result.meta['provenance']['dynamics_config'] = dynamics_config.to_dict()

    return result


def execute_trajectories_stmt(
    stmt: TrajectoriesStmt, context: Optional[Any] = None
) -> QueryResult:
    """Execute a TRAJECTORIES statement to query simulation results.

    This function queries over trajectory data from simulation results,
    enabling temporal analysis and filtering of dynamical processes.

    Args:
        stmt: TrajectoriesStmt from AST
        context: SimulationResult or dict containing simulation results

    Returns:
        QueryResult with trajectory data

    Example:
        >>> from py3plex.dsl import Q
        >>> # First run a dynamics simulation
        >>> sim_result = Q.dynamics("SIS", beta=0.3, mu=0.1).run(steps=100).execute(network)
        >>> # Then query trajectories
        >>> result = (
        ...     Q.trajectories("sim_result")
        ...      .at(50)
        ...      .measure("peak_time", "final_state")
        ...      .execute(sim_result)
        ... )
    """
    from .result import QueryResult
    import numpy as np

    # Validate context
    if context is None:
        raise DslExecutionError(
            "Trajectory queries require a context with simulation results. "
            "Pass the result of a Q.dynamics() execution as context."
        )

    # Extract SimulationResult from context
    # Context can be either a SimulationResult directly or a dict with process_ref as key
    sim_result = None
    if hasattr(context, "data") and hasattr(context, "measures"):
        # It's a SimulationResult object
        sim_result = context
    elif isinstance(context, dict) and stmt.process_ref in context:
        # It's a dict mapping process names to results
        sim_result = context[stmt.process_ref]
    else:
        raise DslExecutionError(
            f"Cannot find simulation result for process '{stmt.process_ref}' in context. "
            "Pass a SimulationResult object or dict with the process_ref as key."
        )

    # Get the primary measure (typically 'prevalence' or first available)
    primary_measure = sim_result.measures[0] if sim_result.measures else None
    if primary_measure is None or primary_measure not in sim_result.data:
        raise DslExecutionError("No trajectory data found in simulation result")

    trajectory_data = sim_result.data[primary_measure]  # Shape: (replicates, steps)

    # Ensure it's a numpy array
    if not isinstance(trajectory_data, np.ndarray):
        trajectory_data = np.array(trajectory_data)

    # Handle temporal filtering
    time_offset = 0  # Track time offset for filtering
    if stmt.temporal_context is not None:
        tc = stmt.temporal_context
        if tc.kind == "at":
            # Single time point
            t_idx = int(tc.t0)
            time_offset = t_idx
            if trajectory_data.ndim == 2:
                trajectory_data = trajectory_data[:, t_idx : t_idx + 1]  # Keep 2D shape
            else:
                trajectory_data = trajectory_data[t_idx : t_idx + 1]
        elif tc.kind == "during":
            # Time range [t0, t1]
            t0_idx = int(tc.t0) if tc.t0 is not None else 0
            t1_idx = int(tc.t1) + 1 if tc.t1 is not None else trajectory_data.shape[-1]
            time_offset = t0_idx
            if trajectory_data.ndim == 2:
                trajectory_data = trajectory_data[:, t0_idx:t1_idx]
            else:
                trajectory_data = trajectory_data[t0_idx:t1_idx]

    # Build items and attributes for QueryResult
    # Items are simple tuples: (replicate, t) for trajectory points
    # This makes them hashable and compatible with QueryResult.to_pandas()
    items = []
    attributes = {}

    # Store item metadata for WHERE filtering
    item_metadata = []  # List of dicts with replicate, t, value

    if trajectory_data.ndim == 1:
        # Single replicate: (steps,)
        for t_idx in range(len(trajectory_data)):
            items.append((0, t_idx + time_offset))
            item_metadata.append(
                {
                    "replicate": 0,
                    "t": t_idx + time_offset,
                    "value": float(trajectory_data[t_idx]),
                }
            )
    elif trajectory_data.ndim == 2:
        # Multiple replicates: (replicates, steps)
        for rep_idx in range(trajectory_data.shape[0]):
            for t_idx in range(trajectory_data.shape[1]):
                items.append((rep_idx, t_idx + time_offset))
                item_metadata.append(
                    {
                        "replicate": rep_idx,
                        "t": t_idx + time_offset,
                        "value": float(trajectory_data[rep_idx, t_idx]),
                    }
                )

    # Apply WHERE conditions if present
    if stmt.where is not None:
        filtered_items = []
        filtered_metadata = []
        for item, metadata in zip(items, item_metadata):
            if _evaluate_trajectory_condition(metadata, stmt.where):
                filtered_items.append(item)
                filtered_metadata.append(metadata)
        items = filtered_items
        item_metadata = filtered_metadata

    # Compute requested measures
    if stmt.measures:
        for measure_name in stmt.measures:
            measure_values = _compute_trajectory_measure(
                item_metadata, trajectory_data, measure_name, sim_result
            )
            # Use items (tuples) as keys
            attributes[measure_name] = {
                items[i]: measure_values[i] for i in range(len(items))
            }

    # Add basic attributes - use items (tuples) as keys
    attributes["replicate"] = {
        items[i]: metadata["replicate"] for i, metadata in enumerate(item_metadata)
    }
    attributes["t"] = {
        items[i]: metadata["t"] for i, metadata in enumerate(item_metadata)
    }
    attributes["value"] = {
        items[i]: metadata["value"] for i, metadata in enumerate(item_metadata)
    }

    # Apply ordering
    if stmt.order_by:
        items, item_metadata = _apply_trajectory_ordering(
            items, item_metadata, attributes, stmt.order_by
        )

    # Apply limit
    if stmt.limit is not None:
        items = items[: stmt.limit]
        item_metadata = item_metadata[: stmt.limit]
        # Also trim attributes to match
        for attr_name in list(attributes.keys()):
            if isinstance(attributes[attr_name], dict):
                new_attr = {}
                for item in items:
                    if item in attributes[attr_name]:
                        new_attr[item] = attributes[attr_name][item]
                attributes[attr_name] = new_attr

    # Create QueryResult
    result = QueryResult(
        items=items,
        attributes=attributes,
        target="trajectories",
        meta={
            "process_ref": stmt.process_ref,
            "process_name": sim_result.process_name,
            "measures": sim_result.measures,
            "num_items": len(items),
        },
    )

    return result


def _evaluate_trajectory_condition(item: Dict[str, Any], where: ConditionExpr) -> bool:
    """Evaluate WHERE conditions on a trajectory item.

    Args:
        item: Trajectory item dict with replicate, t, value
        where: ConditionExpr to evaluate

    Returns:
        True if condition matches, False otherwise
    """
    # Simple evaluation - check each atom
    results = []
    for atom in where.atoms:
        if atom.is_comparison:
            cmp = atom.comparison
            left_val = item.get(cmp.left)
            right_val = cmp.right

            if left_val is None:
                results.append(False)
                continue

            # Evaluate comparison
            if cmp.op == "=":
                results.append(left_val == right_val)
            elif cmp.op == ">":
                results.append(left_val > right_val)
            elif cmp.op == ">=":
                results.append(left_val >= right_val)
            elif cmp.op == "<":
                results.append(left_val < right_val)
            elif cmp.op == "<=":
                results.append(left_val <= right_val)
            elif cmp.op == "!=":
                results.append(left_val != right_val)
            else:
                results.append(False)
        else:
            # For non-comparison atoms, default to True
            results.append(True)

    # Combine results with operators (default AND)
    if not results:
        return True

    result = results[0]
    for i, op in enumerate(where.ops):
        if i + 1 < len(results):
            if op == "AND":
                result = result and results[i + 1]
            elif op == "OR":
                result = result or results[i + 1]

    return result


def _compute_trajectory_measure(
    item_metadata: List[Dict[str, Any]],
    trajectory_data: np.ndarray,
    measure_name: str,
    sim_result: Any,
) -> Dict[int, Any]:
    """Compute a trajectory measure.

    Args:
        item_metadata: List of item metadata dicts
        trajectory_data: Raw trajectory array (post-filtering)
        measure_name: Name of measure to compute
        sim_result: SimulationResult object

    Returns:
        Dict mapping item index to measure value
    """
    import numpy as np

    # Get the original full trajectory data for computing measures
    primary_measure = sim_result.measures[0]
    full_trajectory_data = sim_result.data[primary_measure]
    if not isinstance(full_trajectory_data, np.ndarray):
        full_trajectory_data = np.array(full_trajectory_data)

    measure_values = {}

    if measure_name == "peak_time":
        # Time of maximum value for each replicate
        if full_trajectory_data.ndim == 2:
            for i, metadata in enumerate(item_metadata):
                rep_idx = metadata["replicate"]
                peak_t = int(np.argmax(full_trajectory_data[rep_idx, :]))
                measure_values[i] = peak_t
        else:
            peak_t = int(np.argmax(full_trajectory_data))
            for i in range(len(item_metadata)):
                measure_values[i] = peak_t

    elif measure_name == "final_state":
        # Final value for each replicate
        if full_trajectory_data.ndim == 2:
            for i, metadata in enumerate(item_metadata):
                rep_idx = metadata["replicate"]
                final_val = float(full_trajectory_data[rep_idx, -1])
                measure_values[i] = final_val
        else:
            final_val = float(full_trajectory_data[-1])
            for i in range(len(item_metadata)):
                measure_values[i] = final_val

    elif measure_name == "peak_value":
        # Maximum value for each replicate
        if full_trajectory_data.ndim == 2:
            for i, metadata in enumerate(item_metadata):
                rep_idx = metadata["replicate"]
                peak_val = float(np.max(full_trajectory_data[rep_idx, :]))
                measure_values[i] = peak_val
        else:
            peak_val = float(np.max(full_trajectory_data))
            for i in range(len(item_metadata)):
                measure_values[i] = peak_val

    elif measure_name == "mean_value":
        # Mean value over time for each replicate
        if full_trajectory_data.ndim == 2:
            for i, metadata in enumerate(item_metadata):
                rep_idx = metadata["replicate"]
                mean_val = float(np.mean(full_trajectory_data[rep_idx, :]))
                measure_values[i] = mean_val
        else:
            mean_val = float(np.mean(full_trajectory_data))
            for i in range(len(item_metadata)):
                measure_values[i] = mean_val

    else:
        # Unknown measure - return zeros
        for i in range(len(item_metadata)):
            measure_values[i] = 0.0

    return measure_values


def _apply_trajectory_ordering(
    items: List[Tuple[int, int]],
    item_metadata: List[Dict[str, Any]],
    attributes: Dict[str, Dict],
    order_specs: List[OrderItem],
) -> Tuple[List[Tuple[int, int]], List[Dict[str, Any]]]:
    """Apply ordering to trajectory items.

    Args:
        items: List of (replicate, t) tuples
        item_metadata: List of metadata dicts
        attributes: Computed attributes dict
        order_specs: List of OrderItem specifications

    Returns:
        Tuple of (sorted items, sorted metadata)
    """
    if not order_specs:
        return items, item_metadata

    # Create list of (item, metadata, sort_keys) tuples
    indexed_items = []
    for i, (item, metadata) in enumerate(zip(items, item_metadata)):
        sort_keys = []
        for order_spec in order_specs:
            key = order_spec.key
            # Try to get value from metadata first, then attributes
            if key in metadata:
                val = metadata[key]
            elif key in attributes and item in attributes[key]:
                val = attributes[key][item]
            else:
                val = 0  # Default
            sort_keys.append(val)
        indexed_items.append((item, metadata, tuple(sort_keys)))

    # Sort by keys
    reverse = order_specs[0].desc if order_specs else False
    indexed_items.sort(key=lambda x: x[2], reverse=reverse)

    # Return sorted items and metadata
    return [x[0] for x in indexed_items], [x[1] for x in indexed_items]


def _execute_nodes_with_community(
    network: Any,
    select: SelectStmt,
    params: Optional[Dict[str, Any]] = None,
    progress: bool = False,
    provenance_builder: Optional[ProvenanceBuilder] = None,
    provenance_record: Optional[Any] = None,
) -> QueryResult:
    """Execute nodes query with deterministic community detection.
    
    This handler runs community detection once and attaches the partition
    to the network, then continues with normal node query execution.
    """
    logger = logging.getLogger(__name__)
    
    # Extract community config
    config = select.community_config
    method = config.get("method", "leiden")
    partition_name = config.get("partition_name", "default")
    
    if progress:
        logger.info(f"Running {method} community detection (deterministic)")
    
    # Get community detection function
    from .community_uq import _get_community_function
    
    community_func = _get_community_function(method)
    
    # Run once deterministically
    random_state = config.get("random_state", 0)
    
    # Build kwargs for community function
    func_kwargs = {
        'seed': random_state,
        'gamma': config.get("gamma", 1.0),
        'omega': config.get("omega", 1.0),
        'n_iterations': config.get("n_iterations", 2),
    }
    
    # Only pass k if it's provided (for spectral clustering methods)
    if config.get("k") is not None:
        func_kwargs['k'] = config.get("k")
    
    # Add any other config items not already handled
    func_kwargs.update({k: v for k, v in config.items() if k not in ['method', 'partition_name', 'random_state', 'gamma', 'omega', 'n_iterations', 'k']})
    
    partition_dict = community_func(network, **func_kwargs)
    
    # Attach partition to network
    network.assign_partition(partition_dict, name=partition_name)
    
    if progress:
        n_communities = len(set(partition_dict.values()))
        logger.info(f"Detected {n_communities} communities, attached as '{partition_name}'")
    
    # Now execute normal node query
    # Clear community_config to avoid recursion
    select.community_config = None
    
    result = _execute_select(
        network, select, params, progress,
        provenance_builder=provenance_builder,
        provenance_record=provenance_record
    )
    
    # Add community metadata
    result.meta["community_detection"] = {
        "method": method,
        "partition_name": partition_name,
        "n_communities": n_communities,
        "parameters": {
            "gamma": config.get("gamma", 1.0),
            "omega": config.get("omega", 1.0),
            "random_state": random_state,
        }
    }
    
    return result


def _execute_nodes_with_community_uq(
    network: Any,
    select: SelectStmt,
    params: Optional[Dict[str, Any]] = None,
    progress: bool = False,
    provenance_builder: Optional[ProvenanceBuilder] = None,
    provenance_record: Optional[Any] = None,
) -> QueryResult:
    """Execute nodes query with community detection + UQ.
    
    This handler runs community detection with UQ, attaches the consensus
    partition to the network, then returns node-level results with UQ columns.
    """
    import time
    logger = logging.getLogger(__name__)
    
    # Extract configs
    comm_config = select.community_config
    uq_config = select.uq_config
    
    method = comm_config.get("method", "leiden")
    partition_name = comm_config.get("partition_name", "default")
    uq_method = uq_config.method or "seed"
    n_samples = uq_config.n_samples or 50
    seed = uq_config.seed or 42
    
    if progress:
        logger.info(
            f"Running {method} community detection with UQ "
            f"(method={uq_method}, n_samples={n_samples})"
        )
    
    # Extract noise model from uq_config.kwargs if present
    noise_model = uq_config.kwargs.get("noise_model") if uq_config.kwargs else None
    
    # Run community detection with UQ
    from .community_uq import execute_community_with_uq
    
    stage_start = time.monotonic()
    
    consensus_partition, partition_uq = execute_community_with_uq(
        network=network,
        method=method,
        uq_method=uq_method,
        n_samples=n_samples,
        seed=seed,
        noise_model=noise_model,
        store=uq_config.kwargs.get("store", "sketch") if uq_config.kwargs else "sketch",
        progress=progress,
        gamma=comm_config.get("gamma", 1.0),
        omega=comm_config.get("omega", 1.0),
        n_iterations=comm_config.get("n_iterations", 2),
    )
    
    uq_duration_ms = (time.monotonic() - stage_start) * 1000
    
    if progress:
        logger.info(
            f"UQ complete in {uq_duration_ms:.0f}ms: "
            f"{partition_uq.n_communities} communities, "
            f"VI={partition_uq.vi_mean:.3f}±{partition_uq.vi_std:.3f}"
        )
    
    # Attach consensus partition to network
    network.assign_partition(consensus_partition, name=partition_name)
    
    # Execute normal node query to get base results
    # Clear configs to avoid recursion
    select.community_config = None
    select.uq_config = None
    
    result = _execute_select(
        network, select, params, progress,
        provenance_builder=provenance_builder,
        provenance_record=provenance_record
    )
    
    # Add community UQ columns to result
    # Map node IDs to UQ data
    node_to_uq = {}
    for i, node_id in enumerate(partition_uq.node_ids):
        node_to_uq[node_id] = {
            "community_id": int(partition_uq.consensus_partition[i]),
            "community_entropy": float(partition_uq.membership_entropy[i]),
            "community_confidence": float(partition_uq.p_max_membership[i]),
        }
    
    # Add UQ columns to attributes
    result.attributes["community_id"] = {
        item: node_to_uq.get(item, {}).get("community_id", -1)
        for item in result.items
    }
    result.attributes["community_entropy"] = {
        item: node_to_uq.get(item, {}).get("community_entropy", 0.0)
        for item in result.items
    }
    result.attributes["community_confidence"] = {
        item: node_to_uq.get(item, {}).get("community_confidence", 1.0)
        for item in result.items
    }
    
    # Add UQ metadata
    boundary_nodes = partition_uq.boundary_nodes(threshold=0.5, metric="confidence")
    
    result.meta["uq"] = {
        "type": "partition",
        "n_samples": n_samples,
        "method": uq_method,
        "noise_model": str(noise_model) if noise_model else None,
        "stability": partition_uq.stability_summary(),
        "boundary_nodes": boundary_nodes[:100],  # Limit to first 100
        "duration_ms": uq_duration_ms,
    }
    
    # Store full PartitionUQ object
    result.meta["partition_uq"] = partition_uq
    
    # Add provenance
    if provenance_record is not None:
        provenance_record.metadata["randomness"] = {
            "method": uq_method,
            "noise_model": str(noise_model) if noise_model else None,
            "n_samples": n_samples,
            "seed": seed,
        }
        provenance_record.metadata["uq"] = {
            "type": "partition",
            "storage_mode": partition_uq.store_mode,
        }
    
    return result


def _execute_select_with_compositional_uq(
    network: Any,
    select: SelectStmt,
    params: Optional[Dict[str, Any]] = None,
    progress: bool = True,
    provenance_builder: Optional[ProvenanceBuilder] = None,
    provenance_record: Optional[Any] = None,
) -> QueryResult:
    """Execute a SELECT with compositional UQ (aggregate/summarize/order_by/coverage).
    
    This function wraps the entire query execution with resampling, executing
    the query multiple times on resampled networks and aggregating results.
    
    Args:
        network: Multilayer network
        select: SELECT statement with UQ config
        params: Parameter bindings
        progress: If True, log progress messages
        provenance_builder: Optional provenance builder
        provenance_record: Optional provenance record
        
    Returns:
        QueryResult with uncertainty information in attributes and metadata
    """
    logger_local = logging.getLogger(__name__)
    
    if progress:
        logger_local.info("=== Compositional UQ Execution ===")
    
    # Extract UQ configuration
    uq_config = select.uq_config
    if not uq_config:
        # Should not happen due to should_apply_compositional_uq check
        logger_local.warning("No UQ config found, falling back to deterministic execution")
        return _execute_select(network, select, params, progress, provenance_builder, provenance_record)
    
    # Create resample specification
    resample_spec = ResampleSpec(
        method=uq_config.method or "perturbation",
        n_samples=uq_config.n_samples or 50,
        seed=uq_config.seed,
        kwargs=uq_config.kwargs or {},
    )
    
    if progress:
        logger_local.info(f"UQ Method: {resample_spec.method}, Samples: {resample_spec.n_samples}, Seed: {resample_spec.seed}")
    
    # Create a modified select without UQ for individual resample execution
    select_no_uq = copy.deepcopy(select)
    select_no_uq.uq_config = None
    
    # Storage for resample results
    resample_results = []
    
    # Execute query on each resample
    for i in range(resample_spec.n_samples):
        if progress and i % max(1, resample_spec.n_samples // 10) == 0:
            logger_local.info(f"Processing resample {i+1}/{resample_spec.n_samples}")
        
        # Create resampled network
        resampled_net = create_resampled_network(network, resample_spec, i)
        
        # Execute query on this resample (without UQ to avoid recursion)
        resample_result = _execute_select(
            resampled_net,
            select_no_uq,
            params,
            progress=False,  # Don't log for each resample
            provenance_builder=None,
            provenance_record=None,
        )
        
        resample_results.append(resample_result)
    
    if progress:
        logger_local.info(f"Completed {len(resample_results)} resamples")
    
    # Now aggregate results across resamples
    final_result = _aggregate_compositional_results(
        resample_results,
        select,
        resample_spec,
        progress=progress,
    )
    
    # Add UQ metadata
    final_result.meta["uq"] = {
        "type": "compositional",
        "method": resample_spec.method,
        "n_samples": resample_spec.n_samples,
        "seed": resample_spec.seed,
        "has_aggregate": bool(select.aggregate_specs or select.summarize_aggs),
        "has_ordering": bool(select.order_by),
        "has_coverage": bool(select.coverage_mode),
    }
    
    # Add provenance
    if provenance_record is not None:
        provenance_record.metadata["randomness"] = {
            "method": resample_spec.method,
            "n_samples": resample_spec.n_samples,
            "seed": resample_spec.seed,
        }
        provenance_record.metadata["uq"] = final_result.meta["uq"]
        final_result.meta["provenance"] = provenance_record.to_dict()
    elif provenance_builder is not None:
        final_result.meta["provenance"] = provenance_builder.build()
    
    return final_result


def _aggregate_compositional_results(
    resample_results: List[QueryResult],
    select: SelectStmt,
    resample_spec: ResampleSpec,
    progress: bool = True,
) -> QueryResult:
    """Aggregate results from multiple resamples into a single QueryResult with uncertainty.
    
    Args:
        resample_results: List of QueryResult objects, one per resample
        select: Original SELECT statement
        resample_spec: Resampling specification
        progress: If True, log progress messages
        
    Returns:
        Aggregated QueryResult with uncertainty information
    """
    logger_local = logging.getLogger(__name__)
    
    if not resample_results:
        return QueryResult(
            target=select.target.value,
            items=[],
            attributes={},
            meta={"warning": "No resample results to aggregate"},
        )
    
    # Get the structure from the first result
    first_result = resample_results[0]
    target = first_result.target
    
    # Collect all unique items across resamples
    all_items = set()
    for result in resample_results:
        all_items.update(result.items)
    
    final_items = sorted(all_items)
    
    if progress:
        logger_local.info(f"Aggregating {len(final_items)} items across {len(resample_results)} resamples")
    
    # Aggregate attributes
    final_attributes = {}
    
    # Get attribute names from first result
    attr_names = list(first_result.attributes.keys())
    
    for attr_name in attr_names:
        if progress:
            logger_local.debug(f"Aggregating attribute: {attr_name}")
        
        final_attributes[attr_name] = {}
        
        # For each item, collect values across resamples
        for item in final_items:
            values = []
            for result in resample_results:
                if item in result.items and item in result.attributes.get(attr_name, {}):
                    val = result.attributes[attr_name][item]
                    
                    # Extract numeric value (handle dict format from UQ)
                    if isinstance(val, dict) and "mean" in val:
                        values.append(val["mean"])
                    elif isinstance(val, (int, float)):
                        values.append(float(val))
                    # Skip non-numeric values for now
            
            if values:
                # Aggregate with uncertainty
                uq_result = aggregate_with_uncertainty(
                    values,
                    func="mean",  # Always use mean for aggregating across resamples
                    ci_level=0.95,
                )
                final_attributes[attr_name][item] = uq_result
            else:
                # Item not present in any resample or non-numeric
                final_attributes[attr_name][item] = None
    
    # Handle ranking uncertainty if query has order_by
    rank_stability = None
    if select.order_by:
        if progress:
            logger_local.info("Computing rank stability")
        rank_stability = _compute_rank_stability_across_resamples(
            resample_results,
            select.order_by,
        )
    
    # Handle coverage uncertainty if query has coverage
    coverage_stability = None
    if select.coverage_mode:
        if progress:
            logger_local.info("Computing coverage stability")
        coverage_stability = _compute_coverage_stability_across_resamples(
            resample_results,
            final_items,
        )
    
    # Build final QueryResult
    final_result = QueryResult(
        target=target,
        items=final_items,
        attributes=final_attributes,
        meta={
            "dsl_version": "2.0",
            "uq_compositional": True,
            "n_resamples": len(resample_results),
        },
    )
    
    # Add stability metadata if computed
    if rank_stability:
        final_result.meta["rank_stability"] = rank_stability
    
    if coverage_stability:
        final_result.meta["coverage_stability"] = coverage_stability
    
    return final_result


def _compute_rank_stability_across_resamples(
    resample_results: List[QueryResult],
    order_by_spec: List[Any],
) -> Dict[str, Any]:
    """Compute ranking stability across resamples.
    
    Args:
        resample_results: List of QueryResult objects
        order_by_spec: ORDER BY specification
        
    Returns:
        Dict with rank stability metrics
    """
    # Extract rankings from each resample
    rank_samples = []
    
    for result in resample_results:
        # Reconstruct ranking based on order_by attribute
        # For simplicity, use first order_by key
        if not order_by_spec:
            continue
        
        first_order = order_by_spec[0]
        key_attr = first_order.key if hasattr(first_order, 'key') else str(first_order)
        desc = first_order.desc if hasattr(first_order, 'desc') else False
        
        # Get values for this attribute
        if key_attr in result.attributes:
            values = []
            for item in result.items:
                val = result.attributes[key_attr].get(item)
                if val is not None:
                    # Extract numeric value
                    if isinstance(val, dict) and "mean" in val:
                        values.append((item, val["mean"]))
                    elif isinstance(val, (int, float)):
                        values.append((item, val))
            
            # Sort to get ranking
            values.sort(key=lambda x: x[1], reverse=desc)
            
            # Create rank dict
            ranks = {item: rank + 1 for rank, (item, _) in enumerate(values)}
            rank_samples.append(ranks)
    
    if not rank_samples:
        return {}
    
    # Get all items
    all_items = set()
    for ranks in rank_samples:
        all_items.update(ranks.keys())
    
    # Compute stability
    return compute_rank_stability(rank_samples, list(all_items))


def _compute_coverage_stability_across_resamples(
    resample_results: List[QueryResult],
    all_items: List[Any],
) -> Dict[str, Any]:
    """Compute coverage stability across resamples.
    
    Args:
        resample_results: List of QueryResult objects
        all_items: List of all items
        
    Returns:
        Dict with coverage stability metrics
    """
    # Extract coverage membership from each resample
    coverage_samples = []
    
    for result in resample_results:
        # An item is covered if it's in the result
        membership = {item: (item in result.items) for item in all_items}
        coverage_samples.append(membership)
    
    return compute_coverage_stability(coverage_samples, all_items)


def execute_join(
    network: Any,
    join_node: "JoinNode",
    post_where: Optional[ConditionExpr] = None,
    post_compute: Optional[List[ComputeItem]] = None,
    post_order_by: Optional[List[OrderItem]] = None,
    post_limit: Optional[int] = None,
    params: Optional[Dict[str, Any]] = None,
    progress: bool = True,
    explain_plan: bool = False,
    planner_config: Optional[Dict[str, Any]] = None,
) -> QueryResult:
    """Execute a join operation between two queries.

    This function executes both sides of the join, performs the relational join,
    and applies any post-join operations (filtering, computation, ordering, limiting).

    Args:
        network: Multilayer network object
        join_node: JoinNode containing join specification
        post_where: Optional WHERE conditions to apply after join
        post_compute: Optional measures to compute after join
        post_order_by: Optional ordering to apply after join
        post_limit: Optional limit to apply after join
        params: Parameter bindings
        progress: Whether to log progress
        explain_plan: If True, populate result.meta["plan"] with execution plan
        planner_config: Optional planner configuration dict
    
    Returns:
        QueryResult with joined data and provenance
    
    Raises:
        InvalidJoinKeyError: If join keys don't exist in both schemas
    """
    from .ast import JoinNode, Query, SelectStmt
    from .errors import InvalidJoinKeyError
    import pandas as pd
    import hashlib
    
    params = params or {}
    
    # Execute left and right queries
    logger = logging.getLogger(__name__)
    if progress:
        logger.info(f"Executing join: {join_node.how} join on {join_node.on}")
    
    # Execute left query
    if progress:
        logger.info("  Executing left query...")
    
    # Check if left is a QueryResult or SelectStmt
    # Import QueryResult here to avoid circular dependency
    from .result import QueryResult as QR
    
    if isinstance(join_node.left, QR):
        # It's a QueryResult
        left_result = join_node.left
    else:
        # It's a SelectStmt - execute it
        left_ast = Query(explain=False, select=join_node.left)
        left_result = execute_ast(network, left_ast, params=params, progress=False)
    
    # Execute right query
    if progress:
        logger.info("  Executing right query...")
    
    # Check if right is a QueryResult or SelectStmt
    if isinstance(join_node.right, QR):
        # It's a QueryResult
        right_result = join_node.right
    else:
        # It's a SelectStmt - execute it
        right_ast = Query(explain=False, select=join_node.right)
        right_result = execute_ast(network, right_ast, params=params, progress=False)
    
    # Convert results to DataFrames for joining
    left_df = left_result.to_pandas()
    right_df = right_result.to_pandas()
    
    # Validate join keys exist in both schemas
    left_cols = set(left_df.columns)
    right_cols = set(right_df.columns)
    
    missing_left = [k for k in join_node.on if k not in left_cols]
    missing_right = [k for k in join_node.on if k not in right_cols]
    
    if missing_left:
        raise InvalidJoinKeyError(
            missing_keys=missing_left,
            available_fields=sorted(left_cols),
            side="left",
            ast_summary=f"Join on {join_node.on}",
        )
    
    if missing_right:
        raise InvalidJoinKeyError(
            missing_keys=missing_right,
            available_fields=sorted(right_cols),
            side="right",
            ast_summary=f"Join on {join_node.on}",
        )
    
    # Perform the join
    if progress:
        logger.info(f"  Joining {len(left_df)} left rows with {len(right_df)} right rows...")
    
    if join_node.how == "semi":
        # Semi-join: left rows that have a match in right (left columns only)
        # Use inner join then drop duplicates from left
        joined_df = left_df.merge(
            right_df[list(join_node.on)].drop_duplicates(),
            on=list(join_node.on),
            how="inner",
            suffixes=join_node.suffixes,
        )
        # Keep only left columns
        joined_df = joined_df[left_df.columns].drop_duplicates()
    
    elif join_node.how == "anti":
        # Anti-join: left rows that have NO match in right (left columns only)
        # Use indicator to find non-matches
        joined_df = left_df.merge(
            right_df[list(join_node.on)],
            on=list(join_node.on),
            how="left",
            indicator=True,
        )
        # Keep only rows where right side is null
        joined_df = joined_df[joined_df["_merge"] == "left_only"]
        joined_df = joined_df.drop(columns=["_merge"])
        # Keep only left columns
        joined_df = joined_df[left_df.columns]
    
    else:
        # Standard join (inner, left, right, outer)
        joined_df = left_df.merge(
            right_df,
            on=list(join_node.on),
            how=join_node.how,
            suffixes=join_node.suffixes,
        )
    
    if progress:
        logger.info(f"  Join produced {len(joined_df)} rows")
    
    # Apply post-join operations
    if post_where:
        # Apply WHERE filter using pandas query
        # Build filter expression from ConditionExpr
        for atom in post_where.atoms:
            if atom.comparison:
                comp = atom.comparison
                field = comp.left
                op = comp.op
                value = comp.right
                
                # Apply filter
                if op == "=":
                    joined_df = joined_df[joined_df[field] == value]
                elif op == ">":
                    joined_df = joined_df[joined_df[field] > value]
                elif op == ">=":
                    joined_df = joined_df[joined_df[field] >= value]
                elif op == "<":
                    joined_df = joined_df[joined_df[field] < value]
                elif op == "<=":
                    joined_df = joined_df[joined_df[field] <= value]
                elif op == "!=":
                    joined_df = joined_df[joined_df[field] != value]
        
        if progress:
            logger.info(f"  Post-join filtering reduced to {len(joined_df)} rows")
    
    if post_compute:
        # Compute additional metrics on joined data
        # Note: This is a simplified implementation
        # Full implementation would require computing metrics on the network
        if progress:
            logger.info(f"  Computing {len(post_compute)} metrics on joined data...")
        
        # For now, skip actual computation - would need network context
        # This would require refactoring to support post-join computation
    
    if post_order_by:
        # Sort results
        sort_keys = []
        sort_ascending = []
        for order_item in post_order_by:
            sort_keys.append(order_item.key)
            sort_ascending.append(not order_item.desc)
        
        joined_df = joined_df.sort_values(by=sort_keys, ascending=sort_ascending)
        
        if progress:
            logger.info(f"  Sorted by {sort_keys}")
    
    if post_limit:
        # Limit results
        joined_df = joined_df.head(post_limit)
        if progress:
            logger.info(f"  Limited to {post_limit} rows")
    
    # Convert DataFrame back to QueryResult
    # Use the first column as the primary identifier (id)
    # If 'id' column exists, use it; otherwise use first column
    if 'id' in joined_df.columns:
        items = joined_df['id'].tolist()
        # Get all columns except 'id' for attributes
        attr_cols = [col for col in joined_df.columns if col != 'id']
    else:
        # Fallback: use first column
        items = joined_df.iloc[:, 0].tolist()
        attr_cols = joined_df.columns[1:].tolist()
    
    attributes = {}
    for col in attr_cols:
        attributes[col] = joined_df[col].tolist()
    
    # Build provenance
    provenance = {
        "join": {
            "type": join_node.how,
            "on": list(join_node.on),
            "left_ast_hash": hashlib.sha256(str(join_node.left).encode()).hexdigest()[:8],
            "right_ast_hash": hashlib.sha256(str(join_node.right).encode()).hexdigest()[:8],
            "row_counts": {
                "left": len(left_df),
                "right": len(right_df),
                "output": len(joined_df),
            },
        }
    }
    
    result = QueryResult(
        target=left_result.target,  # Inherit target from left side
        items=items,
        attributes=attributes,
        meta={"provenance": provenance, "dsl_version": "2.1"},
    )
    
    return result
