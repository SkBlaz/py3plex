"""Main claim learning orchestrator.

This module orchestrates the claim learning process:
1. Compute required metrics using DSL
2. Generate candidate antecedents and consequents
3. Score all candidate claims
4. Filter and rank by support/coverage
5. Return claims with provenance
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import hashlib
import json

from py3plex.exceptions import AlgorithmError
from .types import Claim
from .generator import (
    generate_antecedent_candidates,
    generate_consequent_candidates,
    extract_metrics_from_result,
    build_node_data_records,
)
from .scorer import (
    score_claim,
    filter_by_thresholds,
    rank_claims,
    build_claims_from_scored,
    compute_claim_statistics,
)


class ClaimLearningError(AlgorithmError):
    """Exception raised when claim learning fails.
    
    Error code: PX301
    """
    
    default_code = "PX301"


def learn_claims(
    network: Any,
    metrics: List[str],
    layers: Optional[List[str]] = None,
    min_support: float = 0.9,
    min_coverage: float = 0.05,
    max_antecedents: int = 1,
    max_claims: int = 20,
    seed: int = 42,
    cheap_metrics: Optional[List[str]] = None,
    target_metrics: Optional[List[str]] = None,
) -> List[Claim]:
    """Learn claims from network data.
    
    This is the main entry point for claim learning. It orchestrates:
    1. Metric computation via DSL
    2. Candidate generation
    3. Scoring and filtering
    4. Ranking and limiting
    5. Provenance attachment
    
    Args:
        network: py3plex multi_layer_network object
        metrics: List of all metrics to compute and use
        layers: Optional layer restriction (None = all layers)
        min_support: Minimum support threshold (default: 0.9)
        min_coverage: Minimum coverage threshold (default: 0.05)
        max_antecedents: Maximum antecedent terms (MVP: only 1 supported)
        max_claims: Maximum claims to return
        seed: Random seed for determinism
        cheap_metrics: Metrics to use for antecedents (default: derive from metrics)
        target_metrics: Metrics to use for consequents (default: derive from metrics)
        
    Returns:
        List of Claim objects, sorted by rank
        
    Raises:
        ClaimLearningError: If learning fails
    """
    # Validate inputs
    if max_antecedents != 1:
        raise ClaimLearningError(
            f"max_antecedents must be 1 in MVP (got {max_antecedents})",
            suggestions=["Set max_antecedents=1"],
        )
    
    if not metrics:
        raise ClaimLearningError(
            "No metrics specified for claim learning",
            suggestions=["Provide at least one metric name"],
        )
    
    # Determine cheap vs target metrics
    if cheap_metrics is None:
        # Default: cheap metrics are structural properties
        cheap_metrics = [m for m in metrics if m in ["degree", "strength", "layer_count"]]
        if not cheap_metrics:
            cheap_metrics = [metrics[0]]  # Use first metric if none are cheap
    
    if target_metrics is None:
        # Default: target metrics are centrality measures
        target_metrics = [m for m in metrics if m not in cheap_metrics]
        if not target_metrics:
            raise ClaimLearningError(
                "No target metrics for consequents",
                suggestions=["Specify at least one non-cheap metric for consequents"],
            )
    
    # Stage 1: Compute metrics using DSL
    from py3plex.dsl import Q
    
    query = Q.nodes()
    
    if layers is not None:
        # Add layer filtering
        from py3plex.dsl import L
        layer_expr = None
        for layer in layers:
            if layer_expr is None:
                layer_expr = L[layer]
            else:
                layer_expr = layer_expr + L[layer]
        query = query.from_layers(layer_expr)
    
    # Compute all required metrics
    for metric in metrics:
        query = query.compute(metric)
    
    # Also compute layer_count if not already in metrics
    if "layer_count" not in metrics:
        try:
            # Layer count is number of layers a node appears in
            # This is not a standard DSL metric, so we'll compute it manually later
            pass
        except Exception:
            pass
    
    result = query.execute(network)
    
    # Stage 2: Extract metrics data
    metrics_data, node_ids = extract_metrics_from_result(result)
    
    # Manually add layer_count if needed
    if "layer_count" not in metrics_data and node_ids:
        layer_counts = []
        node_layer_map = {}
        for node, layer in node_ids:
            if node not in node_layer_map:
                node_layer_map[node] = set()
            node_layer_map[node].add(layer)
        
        for node, layer in node_ids:
            layer_counts.append(len(node_layer_map[node]))
        
        metrics_data["layer_count"] = layer_counts
    
    node_data_records = build_node_data_records(metrics_data, node_ids)
    
    if not node_data_records:
        raise ClaimLearningError(
            "No nodes found after metric computation",
            suggestions=["Check network has nodes in specified layers"],
        )
    
    # Stage 3: Generate candidates
    antecedent_candidates = generate_antecedent_candidates(
        metrics_data=metrics_data,
        cheap_metrics=cheap_metrics,
        seed=seed,
    )
    
    consequent_candidates = generate_consequent_candidates(
        metrics_data=metrics_data,
        target_metrics=target_metrics,
        seed=seed,
    )
    
    if not antecedent_candidates:
        raise ClaimLearningError(
            "No antecedent candidates generated",
            suggestions=["Check that cheap_metrics have valid values"],
        )
    
    if not consequent_candidates:
        raise ClaimLearningError(
            "No consequent candidates generated",
            suggestions=["Check that target_metrics have valid values"],
        )
    
    # Stage 4: Score all candidate claims
    scored_claims = []
    for antecedent in antecedent_candidates:
        for consequent in consequent_candidates:
            score = score_claim(
                antecedent=antecedent,
                consequent=consequent,
                node_data_records=node_data_records,
                metrics_data=metrics_data,
            )
            
            if score is not None:
                scored_claims.append((antecedent, consequent, score))
    
    # Stage 5: Filter by thresholds
    filtered_claims = filter_by_thresholds(
        scores=scored_claims,
        min_support=min_support,
        min_coverage=min_coverage,
    )
    
    # Stage 6: Rank and limit
    ranked_claims = rank_claims(
        scored_claims=filtered_claims,
        max_claims=max_claims,
    )
    
    # Stage 7: Build Claim objects with provenance
    timestamp_utc = datetime.now(timezone.utc).isoformat()
    
    # Compute network fingerprint
    network_fingerprint = compute_network_fingerprint(network)
    
    # Build metadata template
    meta_template = {
        "provenance": {
            "engine": "claim_learner",
            "py3plex_version": get_py3plex_version(),
            "timestamp_utc": timestamp_utc,
            "network_fingerprint": network_fingerprint,
            "metrics_used": sorted(metrics),
            "cheap_metrics": sorted(cheap_metrics),
            "target_metrics": sorted(target_metrics),
            "parameters": {
                "min_support": min_support,
                "min_coverage": min_coverage,
                "max_antecedents": max_antecedents,
                "max_claims": max_claims,
            },
            "randomness": {
                "seed": seed,
            },
        },
        "layers": layers,
        "params": {},  # Will be filled when claim is used with counterexample engine
    }
    
    claims = build_claims_from_scored(
        scored_claims=ranked_claims,
        meta_template=meta_template,
    )
    
    return claims


def compute_network_fingerprint(network: Any) -> Dict[str, int]:
    """Compute a fingerprint of the network structure.
    
    Args:
        network: py3plex multi_layer_network object
        
    Returns:
        Dictionary with node/edge/layer counts
    """
    try:
        nodes = list(network.get_nodes())
        edges = list(network.get_edges())
        layers = list(network.get_layers())
        
        return {
            "n_nodes": len(nodes),
            "n_edges": len(edges),
            "n_layers": len(layers),
        }
    except Exception:
        return {
            "n_nodes": 0,
            "n_edges": 0,
            "n_layers": 0,
        }


def get_py3plex_version() -> str:
    """Get py3plex version string.
    
    Returns:
        Version string (e.g., "1.1.0")
    """
    try:
        from py3plex import __version__
        return __version__
    except ImportError:
        return "unknown"
