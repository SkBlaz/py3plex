"""Benchmark executor for DSL v2.

This module implements the execution engine for benchmark queries, supporting:
- Grid search with deterministic ordering
- Budget enforcement per unit (repeat/dataset/algorithm)
- Deterministic seeding via SeedSequence
- UQ integration
- Metrics computation
- Run-level and summary-level results
"""

import hashlib
import itertools
import json
import time
import warnings
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from py3plex.benchmarks.budget import Budget
from py3plex.benchmarks.metrics import compute_metric
from py3plex.benchmarks.runners import (
    CommunityAlgorithmRunner,
    CommunityRunResult,
    compute_config_id,
    create_runner_from_spec,
)
from py3plex.dsl.ast import BenchmarkNode, LayerExpr
from py3plex.dsl.result import QueryResult
from py3plex.exceptions import AlgorithmError, BenchmarkError


def execute_benchmark(ast: BenchmarkNode, **params) -> QueryResult:
    """Execute a benchmark query.

    Args:
        ast: BenchmarkNode AST
        **params: Query parameters (e.g., network bindings)

    Returns:
        QueryResult with run-level items and meta["benchmark"]

    Raises:
        BenchmarkError: If benchmark execution fails
    """
    # Validate AST
    if not ast.datasets:
        raise BenchmarkError("Benchmark requires at least one dataset")
    if not ast.algorithm_specs:
        raise BenchmarkError("Benchmark requires at least one algorithm")
    if not ast.metrics:
        warnings.warn("No metrics specified for benchmark")

    # Normalize datasets to list
    datasets = _normalize_datasets(ast.datasets, params)

    # Extract layer expressions
    layer_exprs = _normalize_layer_exprs(ast.layer_expr)

    # Initialize result structures
    runs = []
    traces = {}
    protocol = ast.protocol

    # Compute AST hash for provenance
    ast_hash = _compute_ast_hash(ast)

    # Setup base seed sequence
    base_seed = protocol.seed if protocol.seed is not None else 42
    seed_seq = np.random.SeedSequence(base_seed)

    # Iterate over datasets × layer_expr × repeats
    total_units = len(datasets) * len(layer_exprs) * protocol.repeat
    unit_seeds = seed_seq.spawn(total_units)
    unit_idx = 0

    for dataset_spec in datasets:
        dataset_id, network = _resolve_dataset(dataset_spec, params)

        for layer_expr in layer_exprs:
            layer_names = _resolve_layers(network, layer_expr)
            layer_str = _layer_expr_to_str(layer_expr)

            for repeat_id in range(protocol.repeat):
                # Get seed for this unit (spawn returns SeedSequence objects)
                unit_seed_seq = unit_seeds[unit_idx]
                unit_idx += 1

                # Create budget for this unit
                budget = _create_budget(protocol)

                # Spawn seeds for algorithms within this unit
                algo_seeds = unit_seed_seq.spawn(len(ast.algorithm_specs))

                # Run each algorithm
                for algo_idx, algo_spec in enumerate(ast.algorithm_specs):
                    algo_seed_seq = algo_seeds[algo_idx]

                    # Generate integer seed for algorithm
                    algo_seed = int(algo_seed_seq.generate_state(1)[0])

                    # Spawn UQ seed if needed
                    uq_seed = None
                    if protocol.uq_config:
                        uq_seed_seq = algo_seed_seq.spawn(1)[0]
                        uq_seed = int(uq_seed_seq.generate_state(1)[0])

                    # Run algorithm (grid or single config)
                    algo_runs = _run_algorithm_spec(
                        algo_spec=algo_spec,
                        network=network,
                        layers=layer_names,
                        budget=budget,
                        metrics=ast.metrics,
                        uq_spec=_make_uq_spec(protocol.uq_config, uq_seed),
                        algo_seed=algo_seed,  # Already an int
                        dataset_id=dataset_id,
                        layer_expr=layer_str,
                        repeat_id=repeat_id,
                        ast_hash=ast_hash,
                    )

                    runs.extend(algo_runs)

                    # Collect traces
                    for run in algo_runs:
                        if run.get("trace"):
                            trace_key = (dataset_id, layer_str, repeat_id)
                            if trace_key not in traces:
                                traces[trace_key] = {}
                            traces[trace_key][run["algorithm"]] = run["trace"]

                    # Check if budget exhausted
                    if budget and budget.exhausted():
                        warnings.warn(
                            f"Budget exhausted for {dataset_id}/{layer_str}/repeat_{repeat_id}"
                        )
                        break

    # Create DataFrame from runs
    runs_df = pd.DataFrame(runs)

    # Generate summary
    summary_df = _generate_summary(runs_df)

    # Build meta
    meta = {
        "benchmark": {
            "protocol": _protocol_to_dict(protocol),
            "summary": summary_df,
            "traces": traces if ast.return_trace else {},
            "total_runs": len(runs),
            "ast_hash": ast_hash,
        }
    }

    # Convert runs to QueryResult format
    items = list(range(len(runs)))
    attributes = {}
    
    if runs:
        # Collect all possible keys from all runs
        all_keys = set()
        for run in runs:
            all_keys.update(run.keys())
        
        # Extract columns from run dicts, filling missing values with None
        for key in sorted(all_keys):  # Sort for deterministic ordering
            attributes[key] = [run.get(key) for run in runs]
    
    return QueryResult(target="communities", items=items, attributes=attributes, meta=meta)


# ==============================================================================
# Helper Functions
# ==============================================================================


def _normalize_datasets(datasets: Any, params: Dict[str, Any]) -> List[Any]:
    """Normalize datasets to list."""
    if isinstance(datasets, list):
        return datasets
    return [datasets]


def _normalize_layer_exprs(layer_expr: Optional[LayerExpr]) -> List[Optional[LayerExpr]]:
    """Normalize layer expressions to list."""
    if layer_expr is None:
        return [None]
    return [layer_expr]


def _resolve_dataset(dataset_spec: Any, params: Dict[str, Any]) -> Tuple[str, Any]:
    """Resolve dataset spec to (id, network).

    Args:
        dataset_spec: Dataset specification (str, dict, or network)
        params: Query parameters

    Returns:
        Tuple of (dataset_id, network)
    """
    if isinstance(dataset_spec, str):
        # Dataset name - resolve from params or datasets module
        if dataset_spec in params:
            return dataset_spec, params[dataset_spec]
        else:
            # Try to load from py3plex.datasets
            try:
                from py3plex.datasets import load_dataset

                network = load_dataset(dataset_spec)
                return dataset_spec, network
            except Exception as e:
                raise BenchmarkError(f"Failed to load dataset '{dataset_spec}': {e}")

    elif isinstance(dataset_spec, dict):
        # Dict with name/network keys
        dataset_id = dataset_spec.get("name", "unnamed")
        network = dataset_spec.get("network")
        if network is None:
            raise BenchmarkError(f"Dataset dict missing 'network' key: {dataset_spec}")
        return dataset_id, network

    else:
        # Assume it's a network object
        return "network", dataset_spec


def _resolve_layers(network: Any, layer_expr: Optional[LayerExpr]) -> List[str]:
    """Resolve layer expression to layer names."""
    if layer_expr is None:
        # Use all layers
        if hasattr(network, "get_layers"):
            return list(network.get_layers())
        return []

    # Extract layer names from expression
    return layer_expr.get_layer_names()


def _layer_expr_to_str(layer_expr: Optional[LayerExpr]) -> str:
    """Convert layer expression to string."""
    if layer_expr is None:
        return "all"

    names = layer_expr.get_layer_names()
    if len(names) == 1:
        return names[0]
    return "+".join(names)


def _create_budget(protocol) -> Optional[Budget]:
    """Create budget from protocol."""
    if protocol.budget_limit_ms is None and protocol.budget_limit_evals is None:
        return None

    return Budget(
        limit_ms=protocol.budget_limit_ms,
        limit_evals=protocol.budget_limit_evals,
    )


def _make_uq_spec(uq_config: Optional[Any], uq_seed: Optional[int]) -> Optional[Dict[str, Any]]:
    """Create UQ specification from config."""
    if uq_config is None:
        return None

    return {
        "method": getattr(uq_config, "method", "seed"),
        "n_samples": getattr(uq_config, "n_samples", 10),
        "seed": uq_seed if uq_seed is not None else 42,
    }


def _run_algorithm_spec(
    algo_spec: Any,
    network: Any,
    layers: List[str],
    budget: Optional[Budget],
    metrics: List[str],
    uq_spec: Optional[Dict[str, Any]],
    algo_seed: int,
    dataset_id: str,
    layer_expr: str,
    repeat_id: int,
    ast_hash: str,
) -> List[Dict[str, Any]]:
    """Run algorithm spec (single config or grid).

    Returns:
        List of run result dicts
    """
    # Convert BenchmarkAlgorithmSpec to format expected by create_runner_from_spec
    if hasattr(algo_spec, 'algorithm'):
        # It's a BenchmarkAlgorithmSpec object
        if algo_spec.params:
            runner, params = create_runner_from_spec((algo_spec.algorithm, algo_spec.params))
        else:
            runner, params = create_runner_from_spec(algo_spec.algorithm)
    else:
        # It's already in string or tuple format
        runner, params = create_runner_from_spec(algo_spec)

    # Check if grid search
    if "grid" in params:
        return _run_grid_search(
            runner=runner,
            grid_params=params["grid"],
            network=network,
            layers=layers,
            budget=budget,
            metrics=metrics,
            uq_spec=uq_spec,
            algo_seed=algo_seed,
            dataset_id=dataset_id,
            layer_expr=layer_expr,
            repeat_id=repeat_id,
            ast_hash=ast_hash,
        )
    else:
        # Single config
        return _run_single_config(
            runner=runner,
            params=params,
            network=network,
            layers=layers,
            budget=budget,
            metrics=metrics,
            uq_spec=uq_spec,
            algo_seed=algo_seed,
            dataset_id=dataset_id,
            layer_expr=layer_expr,
            repeat_id=repeat_id,
            ast_hash=ast_hash,
        )


def _run_grid_search(
    runner: CommunityAlgorithmRunner,
    grid_params: Dict[str, List[Any]],
    network: Any,
    layers: List[str],
    budget: Optional[Budget],
    metrics: List[str],
    uq_spec: Optional[Dict[str, Any]],
    algo_seed: int,
    dataset_id: str,
    layer_expr: str,
    repeat_id: int,
    ast_hash: str,
) -> List[Dict[str, Any]]:
    """Run grid search over parameter configurations."""
    # Expand grid
    configs = _expand_grid(grid_params)

    # Spawn seeds for each config (algo_seed is already an int)
    seed_seq = np.random.SeedSequence(algo_seed)
    config_seeds = seed_seq.spawn(len(configs))

    results = []

    for config_idx, config in enumerate(configs):
        config_seed_seq = config_seeds[config_idx]
        config_seed = int(config_seed_seq.generate_state(1)[0])

        # Check budget before running
        if budget and budget.exhausted():
            # Mark skipped configs
            config_id = compute_config_id(config)
            results.append(
                {
                    "dataset_id": dataset_id,
                    "layer_expr": layer_expr,
                    "repeat_id": repeat_id,
                    "algorithm": runner.name,
                    "config_id": config_id,
                    "params_json": json.dumps(config, sort_keys=True),
                    "timed_out": True,
                    "budget_limit_ms": budget.limit_ms,
                    "budget_used_ms": budget.used_ms,
                    "eval_count": budget.eval_count,
                    "prov_ast_hash": ast_hash,
                    "prov_seed": config_seed,
                    "prov_engine": "benchmark",
                }
            )
            continue

        # Run config
        config_result = _run_single_config(
            runner=runner,
            params=config,
            network=network,
            layers=layers,
            budget=budget,
            metrics=metrics,
            uq_spec=uq_spec,
            algo_seed=config_seed,
            dataset_id=dataset_id,
            layer_expr=layer_expr,
            repeat_id=repeat_id,
            ast_hash=ast_hash,
        )

        results.extend(config_result)

    return results


def _expand_grid(grid_params: Dict[str, List[Any]]) -> List[Dict[str, Any]]:
    """Expand grid parameters to list of configs.

    Uses deterministic ordering (sorted keys + itertools.product).
    """
    if not grid_params:
        return [{}]

    # Sort keys for deterministic ordering
    sorted_keys = sorted(grid_params.keys())
    sorted_values = [grid_params[k] for k in sorted_keys]

    # Cartesian product
    configs = []
    for combo in itertools.product(*sorted_values):
        config = {k: v for k, v in zip(sorted_keys, combo)}
        configs.append(config)

    return configs


def _run_single_config(
    runner: CommunityAlgorithmRunner,
    params: Dict[str, Any],
    network: Any,
    layers: List[str],
    budget: Optional[Budget],
    metrics: List[str],
    uq_spec: Optional[Dict[str, Any]],
    algo_seed: int,
    dataset_id: str,
    layer_expr: str,
    repeat_id: int,
    ast_hash: str,
) -> List[Dict[str, Any]]:
    """Run single algorithm configuration."""
    # Compute config ID
    config_id = compute_config_id(params)

    # Run algorithm
    try:
        start_time = time.time()
        result = runner.run(
            network=network,
            layers=layers,
            seed=algo_seed,
            budget=budget,
            uq_spec=uq_spec,
            **params,
        )
        runtime_ms = (time.time() - start_time) * 1000

        # Charge budget
        if budget:
            budget.charge(ms=runtime_ms, evals=1)

    except AlgorithmError as e:
        warnings.warn(f"Algorithm {runner.name} failed: {e}")
        error_row = {
            "dataset_id": dataset_id,
            "layer_expr": layer_expr,
            "repeat_id": repeat_id,
            "algorithm": runner.name,
            "config_id": config_id,
            "params_json": json.dumps(params, sort_keys=True),
            "runtime_ms": 0.0,
            "error": str(e),
            "timed_out": False,
            "budget_limit_ms": budget.limit_ms if budget else None,
            "budget_used_ms": budget.used_ms if budget else 0.0,
            "eval_count": budget.eval_count if budget else 0,
            "prov_ast_hash": ast_hash,
            "prov_seed": algo_seed,
            "prov_engine": "benchmark",
        }
        # Add NaN for all metrics
        for metric in metrics:
            error_row[metric] = float("nan")
        return [error_row]

    # Compute metrics
    metric_values = _compute_metrics(
        network=network,
        partition=result.partition,
        layers=layers,
        metrics=metrics,
        uq_partitions=result.uq_partitions,
    )

    # Build result row
    row = {
        "dataset_id": dataset_id,
        "layer_expr": layer_expr,
        "repeat_id": repeat_id,
        "algorithm": runner.name,
        "config_id": config_id,
        "params_json": json.dumps(params, sort_keys=True),
        "runtime_ms": result.runtime_ms,
        "timed_out": False,
        "budget_limit_ms": budget.limit_ms if budget else None,
        "budget_used_ms": budget.used_ms if budget else 0.0,
        "eval_count": budget.eval_count if budget else 1,
        "prov_ast_hash": ast_hash,
        "prov_seed": algo_seed,
        "prov_engine": "benchmark",
    }

    # Add metrics
    row.update(metric_values)

    # Add trace if available
    if result.trace:
        row["trace"] = result.trace

    return [row]


def _compute_metrics(
    network: Any,
    partition: Dict[Any, int],
    layers: List[str],
    metrics: List[str],
    uq_partitions: Optional[List[Dict[Any, int]]] = None,
) -> Dict[str, float]:
    """Compute all metrics for a partition.

    Args:
        network: Multilayer network
        partition: Node -> community mapping
        layers: Layer list
        metrics: Metric names
        uq_partitions: Optional UQ replicates

    Returns:
        Dict of metric_name -> value
    """
    result = {}

    for metric_name in metrics:
        try:
            value = compute_metric(
                name=metric_name,
                network=network,
                partition=partition,
                layers=layers,
                uq_results=uq_partitions,
            )
            result[metric_name] = value
        except Exception as e:
            warnings.warn(f"Failed to compute {metric_name}: {e}")
            result[metric_name] = float("nan")

    return result


def _generate_summary(runs_df: pd.DataFrame) -> pd.DataFrame:
    """Generate summary statistics by aggregating runs.

    Groups by (dataset, layer, algorithm, config) and computes mean/std.

    Args:
        runs_df: DataFrame of run-level results

    Returns:
        Summary DataFrame
    """
    if runs_df.empty:
        return pd.DataFrame()

    # Identify metric columns (exclude known metadata columns)
    metadata_cols = {
        "dataset_id",
        "layer_expr",
        "repeat_id",
        "algorithm",
        "config_id",
        "params_json",
        "runtime_ms",
        "timed_out",
        "budget_limit_ms",
        "budget_used_ms",
        "eval_count",
        "prov_ast_hash",
        "prov_seed",
        "prov_engine",
        "error",
        "trace",
    }

    metric_cols = [col for col in runs_df.columns if col not in metadata_cols]

    # Group by dataset, layer, algorithm, config
    group_cols = ["dataset_id", "layer_expr", "algorithm", "config_id"]
    group_cols = [c for c in group_cols if c in runs_df.columns]

    if not group_cols:
        return pd.DataFrame()

    # Aggregate
    agg_funcs = {}
    for col in metric_cols:
        if pd.api.types.is_numeric_dtype(runs_df[col]):
            agg_funcs[col] = ["mean", "std", "count"]

    # Also aggregate runtime_ms if present
    if "runtime_ms" in runs_df.columns:
        agg_funcs["runtime_ms"] = ["mean", "std"]

    if not agg_funcs:
        # No numeric columns to aggregate
        return runs_df.drop_duplicates(subset=group_cols).reset_index(drop=True)

    summary = runs_df.groupby(group_cols, as_index=False).agg(agg_funcs)

    # Flatten multi-level column names
    summary.columns = [
        "_".join(col).strip("_") if isinstance(col, tuple) else col
        for col in summary.columns
    ]

    return summary


def _protocol_to_dict(protocol) -> Dict[str, Any]:
    """Convert protocol to dict."""
    return {
        "repeat": protocol.repeat,
        "seed": protocol.seed,
        "budget_limit_ms": protocol.budget_limit_ms,
        "budget_limit_evals": protocol.budget_limit_evals,
        "budget_per": protocol.budget_per,
        "n_jobs": protocol.n_jobs,
        "uq_config": str(protocol.uq_config) if protocol.uq_config else None,
    }


def _compute_ast_hash(ast: BenchmarkNode) -> str:
    """Compute hash of AST for provenance."""
    # Create stable representation
    ast_dict = {
        "benchmark_type": ast.benchmark_type,
        "algorithms": [spec.algorithm for spec in ast.algorithm_specs],
        "metrics": sorted(ast.metrics),
        "protocol": {
            "repeat": ast.protocol.repeat,
            "seed": ast.protocol.seed,
        },
    }

    normalized = json.dumps(ast_dict, sort_keys=True)
    return hashlib.sha256(normalized.encode()).hexdigest()[:16]
