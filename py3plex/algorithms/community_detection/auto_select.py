"""Automatic community detection algorithm selection.

This module provides the auto_select_community function for automatic
selection of the best community detection algorithm based on multi-metric
evaluation and a "most wins" decision engine.
"""

import logging
from typing import Any, List, Optional

from py3plex.selection.capabilities import scan_capabilities
from py3plex.selection.community_registry import build_registry_from_capabilities
from py3plex.selection.metric_registry import get_metric_registry
from py3plex.selection.evaluate import evaluate_contestant
from py3plex.selection.wins import compute_pairwise_wins, select_winner
from py3plex.selection.result import AutoCommunityResult, ContestantResult

logger = logging.getLogger(__name__)


def auto_select_community(
    network: Any,
    *,
    mode: str = "pareto",
    fast: bool = True,
    max_candidates: int = 10,
    uq: bool = False,
    uq_n_samples: int = 10,
    uq_method: str = "seed",
    seed: int = 0,
    time_budget_s: Optional[float] = None,
    custom_metrics: Optional[List] = None,
    custom_candidates: Optional[List] = None,
    null_model: bool = False,
    null_samples: int = 10,
) -> AutoCommunityResult:
    """Automatically select the best community detection algorithm.
    
    This function provides two selection modes:
    - "pareto" (default): Pareto-optimal multi-objective selection with UQ and null calibration
    - "wins": Legacy "most wins" pairwise comparison (backward compatible)
    
    Pareto Mode Pipeline:
    1. Detects available algorithms
    2. Runs candidates with optional UQ
    3. Computes multi-objective metrics
    4. Applies null-model calibration (if enabled)
    5. Selects via Pareto dominance
    6. Builds consensus if multiple non-dominated
    
    Wins Mode Pipeline (Legacy):
    1. Detects available algorithms
    2. Runs candidates
    3. Scores on bucketed metrics
    4. Picks winner by pairwise wins count
    
    Args:
        network: Multilayer network object
        mode: Selection mode - "pareto" (default) or "wins" (default: "pareto")
        fast: Use fast mode with smaller grids/samples (default: True)
        max_candidates: Maximum number of algorithm candidates (default: 10)
        uq: Enable uncertainty quantification (default: False, auto-enabled in Pareto mode)
        uq_n_samples: Number of UQ samples (default: 10)
        uq_method: UQ method - "seed", "perturbation", or "bootstrap" (default: "seed")
        seed: Master random seed for reproducibility (default: 0)
        time_budget_s: Optional time budget in seconds
        custom_metrics: Optional list of custom MetricSpec objects
        custom_candidates: Optional list of custom CandidateSpec objects
        null_model: Enable null-model calibration (Pareto mode only) (default: False)
        null_samples: Number of null model samples (default: 10)
    
    Returns:
        AutoCommunityResult with:
            - chosen: Winning contestant (wins mode only)
            - partition: Winning/consensus partition
            - algorithm: Algorithm info
            - leaderboard: Rankings DataFrame (wins mode)
            - evaluation_matrix: Metrics DataFrame (Pareto mode)
            - pareto_front: Non-dominated algorithms (Pareto mode)
            - report: Summary statistics
            - provenance: Detection and selection metadata
    
    Examples:
        >>> from py3plex.core import multinet
        >>> from py3plex.algorithms.community_detection import auto_select_community
        >>> 
        >>> # Create network
        >>> net = multinet.multi_layer_network(directed=False)
        >>> # ... add nodes and edges ...
        >>> 
        >>> # Pareto mode (default, multi-objective)
        >>> result = auto_select_community(net, mode="pareto", fast=True, seed=42)
        >>> print(result.explain())
        >>> print(f"Pareto front: {result.pareto_front}")
        >>> 
        >>> # Legacy wins mode (backward compatible)
        >>> result = auto_select_community(net, mode="wins", fast=True, seed=42)
        >>> print(result.explain())
        >>> print(result.leaderboard)
        >>> 
        >>> # Pareto with UQ and null models
        >>> result = auto_select_community(
        ...     net, mode="pareto", uq=True, null_model=True, seed=42
        ... )
    """
    logger.info(f"Starting AutoCommunity selection (mode={mode})")

    # Validate mode
    if mode not in ("pareto", "wins"):
        raise ValueError(
            f"Invalid mode '{mode}'. Must be 'pareto' or 'wins'."
        )

    # Route to appropriate implementation
    if mode == "pareto":
        return _auto_select_pareto(
            network=network,
            fast=fast,
            max_candidates=max_candidates,
            uq=uq,
            uq_n_samples=uq_n_samples,
            uq_method=uq_method,
            seed=seed,
            time_budget_s=time_budget_s,
            custom_metrics=custom_metrics,
            custom_candidates=custom_candidates,
            null_model=null_model,
            null_samples=null_samples,
        )
    else:
        return _auto_select_wins(
            network=network,
            fast=fast,
            max_candidates=max_candidates,
            uq=uq,
            uq_n_samples=uq_n_samples,
            uq_method=uq_method,
            seed=seed,
            time_budget_s=time_budget_s,
            custom_metrics=custom_metrics,
            custom_candidates=custom_candidates,
        )


def _auto_select_pareto(
    network: Any,
    fast: bool,
    max_candidates: int,
    uq: bool,
    uq_n_samples: int,
    uq_method: str,
    seed: int,
    time_budget_s: Optional[float],
    custom_metrics: Optional[List],
    custom_candidates: Optional[List],
    null_model: bool,
    null_samples: int,
) -> AutoCommunityResult:
    """Pareto-optimal selection via AutoCommunity executor.
    
    This delegates to the full AutoCommunity pipeline with Pareto selection,
    uncertainty quantification, and null-model calibration.
    
    Returns unified AutoCommunityResult compatible with wins mode.
    """
    logger.info("Using Pareto-based selection (multi-objective mode)")

    # Import AutoCommunity executor
    from py3plex.algorithms.community_detection.autocommunity_executor import (
        execute_autocommunity
    )

    # Phase 0: Detection
    logger.info("Scanning capabilities...")
    capabilities = scan_capabilities()
    metric_registry = get_metric_registry()

    # Build candidate algorithms list
    is_multilayer = _is_multilayer_network(network)

    if custom_candidates:
        # Extract algorithm names from custom candidates
        candidate_algorithms = [c.algo_name for c in custom_candidates]
    else:
        # Use detected algorithms
        if not capabilities.algorithms_found:
            raise RuntimeError(
                "No community detection algorithms found. "
                "Please ensure py3plex.algorithms.community_detection is properly installed."
            )

        # Select top algorithms based on capabilities
        candidate_algorithms = []

        # Map detected names to executor names
        algorithm_mapping = {
            'multilayer_leiden': 'leiden',
            'leiden_multilayer': 'leiden',
            'multilayer_louvain': 'louvain',
            'louvain_multilayer': 'louvain',
            'label_propagation': 'label_propagation',
        }

        # Try preferred algorithms first
        for detected_name in ['multilayer_leiden', 'multilayer_louvain', 'label_propagation']:
            if detected_name in capabilities.algorithms_found:
                mapped_name = algorithm_mapping.get(detected_name, detected_name)
                if mapped_name not in candidate_algorithms:
                    candidate_algorithms.append(mapped_name)
            if len(candidate_algorithms) >= max_candidates:
                break

        # Fallback to any available multilayer algorithm
        if not candidate_algorithms:
            for detected_name, algo_info in capabilities.algorithms_found.items():
                if algo_info.supports_multilayer:
                    mapped_name = algorithm_mapping.get(detected_name, detected_name)
                    if mapped_name not in candidate_algorithms:
                        candidate_algorithms.append(mapped_name)
                    if len(candidate_algorithms) >= max_candidates:
                        break

        if not candidate_algorithms:
            raise RuntimeError(
                "No suitable multilayer algorithms found. "
                "Please ensure py3plex.algorithms.community_detection is properly installed."
            )

    logger.info(f"Selected {len(candidate_algorithms)} candidate algorithms: {candidate_algorithms}")

    # Build metric names list
    if custom_metrics:
        metric_names = [m.name for m in custom_metrics]
    else:
        # Default metrics for Pareto mode
        metric_names = ["modularity", "coverage"]
        if uq:
            metric_names.append("stability")
        custom_metrics = []  # Use empty list instead of custom_metric_funcs

    logger.info(f"Using {len(metric_names)} metrics: {metric_names}")

    # Configure UQ
    uq_config = None
    if uq or not fast:  # Enable UQ in Pareto mode unless fast=True
        uq_config = {
            'method': uq_method,
            'n_samples': uq_n_samples if uq else max(5, uq_n_samples // 2),  # Reduced for fast mode
            'seed': seed,
        }
        logger.info(f"UQ enabled: {uq_config}")

    # Configure null models
    null_config = None
    if null_model:
        null_config = {
            'type': 'configuration',
            'samples': null_samples if not fast else max(5, null_samples // 2),
            'seed': seed,
        }
        logger.info(f"Null model enabled: {null_config}")

    metric_specs = []
    if custom_metrics:
        metric_specs = custom_metrics
    else:
        default_specs = metric_registry.get_default_metrics(uq_enabled=uq)
        metric_specs = [m for m in default_specs if m.name in metric_names]

    metric_directions = {
        m.name: m.direction
        for m in metric_specs
        if getattr(m, "direction", None) in {"min", "max"}
    }

    # Execute Pareto pipeline
    logger.info("Executing Pareto pipeline...")
    pareto_result = execute_autocommunity(
        network=network,
        candidate_algorithms=candidate_algorithms,
        metric_names=metric_names,
        uq_config=uq_config,
        null_config=null_config,
        use_pareto=True,
        seed=seed,
        custom_metrics=custom_metrics,
        custom_candidates=[],
        metric_directions=metric_directions,
    )

    # Convert ParetoResult to unified AutoCommunityResult format
    # Note: The Pareto result structure is already close to what we need

    # Build a ContestantResult for the winner (for API compatibility)
    # Extract actual metrics and runtime from pareto_result if available
    from py3plex.selection.result import ContestantResult

    winner_metrics = {}
    winner_runtime = 0.0

    # Try to extract metrics from evaluation_matrix
    if not pareto_result.evaluation_matrix.empty:
        winner_rows = pareto_result.evaluation_matrix[
            pareto_result.evaluation_matrix['algorithm_id'] == pareto_result.selected
        ]
        if not winner_rows.empty:
            winner_row = winner_rows.iloc[0]
            # Extract all metric columns
            for col in pareto_result.evaluation_matrix.columns:
                if col != 'algorithm_id':
                    winner_metrics[col] = winner_row[col]

    # Try to extract runtime from diagnostics
    if pareto_result.selected in pareto_result.diagnostics:
        winner_runtime = pareto_result.diagnostics[pareto_result.selected].get('runtime_ms', 0.0)

    winner_contestant = ContestantResult(
        contestant_id=pareto_result.selected,
        algo_name=pareto_result.selected.split(':')[0] if ':' in pareto_result.selected else pareto_result.selected,
        params={},  # Parameters not tracked in detail for consensus
        partition=pareto_result.consensus_partition,
        metrics=winner_metrics,  # Actual metrics from evaluation
        runtime_ms=winner_runtime,  # Actual runtime from diagnostics
        seed_used=seed,
    )

    # Build unified result (extend AutoCommunityResult from selection.result)
    # Add Pareto-specific fields as attributes
    unified_result = AutoCommunityResult(
        chosen=winner_contestant,
        partition=pareto_result.consensus_partition,
        algorithm={
            "name": pareto_result.selected,
            "params": {},
            "contestant_id": pareto_result.selected,
        },
        leaderboard=pareto_result.evaluation_matrix,  # Use evaluation matrix as leaderboard
        report={
            "n_contestants": len(pareto_result.algorithms_tested),
            "n_metrics": len(metric_names),
            "mode": "pareto",
            "pareto_front_size": len(pareto_result.pareto_front),
            "metrics_by_bucket": {
                bucket: [m.name for m in metric_specs if m.bucket == bucket]
                for bucket in metric_registry.BUCKET_CAPS.keys()
            },
        },
        provenance={
            **pareto_result.provenance,
            "mode": "pareto",
            "algorithms_detected": list(capabilities.algorithms_found.keys()),
            "selection_config": {
                "fast_mode": fast,
                "max_candidates": max_candidates,
                "uq_enabled": uq_config is not None,
                "uq_n_samples": uq_n_samples if uq_config else None,
                "uq_method": uq_method if uq_config else None,
                "null_model_enabled": null_model,
                "seed": seed,
            },
        },
    )

    # Attach Pareto-specific fields
    unified_result.pareto_front = pareto_result.pareto_front
    unified_result.evaluation_matrix = pareto_result.evaluation_matrix
    unified_result.community_stats = pareto_result.community_stats
    unified_result.null_model_results = pareto_result.null_model_results
    unified_result.graph_regime = pareto_result.graph_regime
    unified_result.diagnostics = pareto_result.diagnostics

    logger.info("Pareto selection complete")
    return unified_result


def _auto_select_wins(
    network: Any,
    fast: bool,
    max_candidates: int,
    uq: bool,
    uq_n_samples: int,
    uq_method: str,
    seed: int,
    time_budget_s: Optional[float],
    custom_metrics: Optional[List],
    custom_candidates: Optional[List],
) -> AutoCommunityResult:
    """Legacy wins-based selection (original implementation).
    
    This is the original "most wins" implementation preserved for
    backward compatibility.
    """
    logger.info("Using wins-based selection (legacy mode)")

    # Phase 0: Detection
    logger.info("Scanning capabilities...")
    capabilities = scan_capabilities()

    logger.info(
        f"Found {len(capabilities.algorithms_found)} algorithms, "
        f"{len(capabilities.metrics_found)} metrics, "
        f"UQ={'available' if capabilities.uq_available else 'unavailable'}"
    )

    # Check if we have any algorithms
    if not capabilities.algorithms_found:
        raise RuntimeError(
            "No community detection algorithms found. "
            "Please ensure py3plex.algorithms.community_detection is properly installed."
        )

    # Phase 1: Build candidate set
    is_multilayer = _is_multilayer_network(network)

    if custom_candidates:
        candidates = custom_candidates
        logger.info(f"Using {len(candidates)} custom candidates")
    else:
        registry, candidates = build_registry_from_capabilities(
            capabilities=capabilities,
            is_multilayer=is_multilayer,
            fast_mode=fast,
            max_candidates=max_candidates,
        )
        logger.info(f"Built {len(candidates)} candidates")

    # Phase 2: Get metrics
    metric_registry = get_metric_registry()

    if custom_metrics:
        metrics = custom_metrics
        logger.info(f"Using {len(metrics)} custom metrics")
    else:
        metrics = metric_registry.get_default_metrics(uq_enabled=uq)
        logger.info(f"Using {len(metrics)} default metrics")

    # Phase 3: Evaluate contestants
    logger.info("Evaluating contestants...")
    contestants: List[ContestantResult] = []

    uq_config = {
        "method": uq_method,
        "n_samples": uq_n_samples,
        "seed": seed,
    } if uq else None

    for i, candidate in enumerate(candidates, 1):
        logger.info(f"Evaluating {i}/{len(candidates)}: {candidate.contestant_id}")

        try:
            contestant_result = evaluate_contestant(
                network=network,
                candidate=candidate,
                metrics=metrics,
                master_seed=seed,
                uq=uq,
                uq_config=uq_config,
                time_budget_s=time_budget_s,
            )

            # Skip failed contestants
            if contestant_result.errors:
                logger.warning(f"Skipping {candidate.contestant_id}: {contestant_result.errors}")
                continue

            contestants.append(contestant_result)

        except Exception as e:
            logger.error(f"Failed to evaluate {candidate.contestant_id}: {e}")
            continue

    if not contestants:
        raise RuntimeError("All contestants failed to evaluate")

    logger.info(f"Successfully evaluated {len(contestants)} contestants")

    # Phase 4: Compute wins
    logger.info("Computing pairwise wins...")
    total_wins, wins_by_bucket, leaderboard = compute_pairwise_wins(
        contestants=contestants,
        metrics=metrics,
        bucket_caps=metric_registry.BUCKET_CAPS,
    )

    # Phase 5: Select winner
    logger.info("Selecting winner...")
    winner = select_winner(
        contestants=contestants,
        total_wins=total_wins,
        wins_by_bucket=wins_by_bucket,
    )

    # Phase 6: Build result
    provenance = {
        "algorithms_detected": list(capabilities.algorithms_found.keys()),
        "metrics_detected": list(capabilities.metrics_found.keys()),
        "uq_available": capabilities.uq_available,
        "dsl_operator_detected": capabilities.dsl_operator_available,
        "selection_config": {
            "fast_mode": fast,
            "max_candidates": max_candidates,
            "uq_enabled": uq,
            "uq_n_samples": uq_n_samples if uq else None,
            "uq_method": uq_method if uq else None,
            "seed": seed,
            "n_candidates_evaluated": len(contestants),
            "n_metrics_used": len(metrics),
        },
        "wins_by_bucket": wins_by_bucket[winner.contestant_id],
    }

    report = {
        "n_contestants": len(contestants),
        "n_metrics": len(metrics),
        "metrics_by_bucket": {
            bucket: [m.name for m in metrics if m.bucket == bucket]
            for bucket in metric_registry.BUCKET_CAPS.keys()
        },
    }

    result = AutoCommunityResult(
        chosen=winner,
        partition=winner.partition,
        algorithm={
            "name": winner.algo_name,
            "params": winner.params,
            "contestant_id": winner.contestant_id,
        },
        leaderboard=leaderboard,
        report=report,
        provenance=provenance,
    )

    logger.info("AutoCommunity selection complete")
    return result


def _is_multilayer_network(network: Any) -> bool:
    """Check if network is multilayer.
    
    Args:
        network: Network object
    
    Returns:
        True if multilayer, False otherwise
    """
    # Check for multi_layer_network signature
    if hasattr(network, "get_layers"):
        layers = network.get_layers()
        return len(layers) > 1

    # Default to multilayer assumption
    return True
