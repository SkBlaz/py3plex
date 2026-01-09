"""Automatic community detection algorithm selection.

This module provides the auto_select_community function for automatic
selection of the best community detection algorithm based on multi-metric
evaluation and a "most wins" decision engine.
"""

import logging
from typing import Any, Dict, List, Optional

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
    fast: bool = True,
    max_candidates: int = 10,
    uq: bool = False,
    uq_n_samples: int = 10,
    uq_method: str = "seed",
    seed: int = 0,
    time_budget_s: Optional[float] = None,
    custom_metrics: Optional[List] = None,
    custom_candidates: Optional[List] = None,
) -> AutoCommunityResult:
    """Automatically select the best community detection algorithm.
    
    This function:
    1. Detects available community detection algorithms
    2. Runs a candidate set of algorithms with parameter grids
    3. Scores them on multiple metrics (bucketed)
    4. Picks the winner by "MOST WINS" (pairwise wins across metrics)
    5. Optionally uses UQ to gate wins by significance
    6. Returns AutoCommunityResult with partition, leaderboard, and explanation
    
    Args:
        network: Multilayer network object
        fast: Use fast mode with smaller parameter grids (default: True)
        max_candidates: Maximum number of algorithm candidates (default: 10)
        uq: Enable uncertainty quantification (default: False)
        uq_n_samples: Number of UQ samples (default: 10)
        uq_method: UQ method - "seed", "perturbation", or "bootstrap" (default: "seed")
        seed: Master random seed for reproducibility (default: 0)
        time_budget_s: Optional time budget in seconds
        custom_metrics: Optional list of custom MetricSpec objects
        custom_candidates: Optional list of custom CandidateSpec objects
    
    Returns:
        AutoCommunityResult with:
            - chosen: Winning contestant
            - partition: Winning partition
            - algorithm: Algorithm info
            - leaderboard: Rankings DataFrame
            - report: Per-metric summaries
            - provenance: Detection and selection metadata
    
    Examples:
        >>> from py3plex.core import multinet
        >>> from py3plex.algorithms.community_detection import auto_select_community
        >>> 
        >>> # Create network
        >>> net = multinet.multi_layer_network(directed=False)
        >>> # ... add nodes and edges ...
        >>> 
        >>> # Auto-select community detection algorithm
        >>> result = auto_select_community(net, fast=True, seed=42)
        >>> 
        >>> # Access results
        >>> print(result.explain())
        >>> print(result.leaderboard)
        >>> 
        >>> # Assign partition to network
        >>> net.assign_partition(result.partition)
        >>> 
        >>> # With UQ for stability
        >>> result = auto_select_community(net, uq=True, uq_n_samples=50, seed=42)
        >>> print(result.explain())
    """
    logger.info("Starting AutoCommunity selection")
    
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
