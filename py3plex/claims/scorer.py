"""Scoring and ranking logic for claims.

This module computes support and coverage statistics for candidate claims
and implements deterministic ranking logic.
"""

from typing import Any, Dict, List, Optional
import numpy as np

from .types import Antecedent, Consequent, Claim, ClaimScore


def score_claim(
    antecedent: Antecedent,
    consequent: Consequent,
    node_data_records: List[Dict[str, Any]],
    metrics_data: Dict[str, List[float]],
) -> Optional[ClaimScore]:
    """Compute support and coverage for a candidate claim.
    
    Support = P(consequent | antecedent) = |{v: A(v) AND B(v)}| / |{v: A(v)}|
    Coverage = P(antecedent) = |{v: A(v)}| / N
    
    Args:
        antecedent: Antecedent predicate
        consequent: Consequent predicate
        node_data_records: List of node data dictionaries
        metrics_data: Dictionary of metric name -> all values (for rank/top_p evaluation)
        
    Returns:
        ClaimScore object, or None if antecedent has no satisfying nodes
    """
    n_total = len(node_data_records)
    if n_total == 0:
        return None
    
    n_antecedent = 0
    n_both = 0
    
    for record in node_data_records:
        # Check antecedent
        satisfies_antecedent = antecedent.evaluate(record, metrics_data)
        
        if satisfies_antecedent:
            n_antecedent += 1
            
            # Check consequent
            satisfies_consequent = consequent.evaluate(record, metrics_data)
            if satisfies_consequent:
                n_both += 1
    
    if n_antecedent == 0:
        return None
    
    support = n_both / n_antecedent
    coverage = n_antecedent / n_total
    
    return ClaimScore(
        support=support,
        coverage=coverage,
        n_antecedent=n_antecedent,
        n_both=n_both,
        n_total=n_total,
    )


def filter_by_thresholds(
    scores: List[tuple],
    min_support: float,
    min_coverage: float,
) -> List[tuple]:
    """Filter claims by support and coverage thresholds.
    
    Args:
        scores: List of (antecedent, consequent, score) tuples
        min_support: Minimum support threshold
        min_coverage: Minimum coverage threshold
        
    Returns:
        Filtered list of tuples
    """
    filtered = []
    for antecedent, consequent, score in scores:
        if score.support >= min_support and score.coverage >= min_coverage:
            filtered.append((antecedent, consequent, score))
    return filtered


def rank_claims(
    scored_claims: List[tuple],
    max_claims: Optional[int] = None,
) -> List[tuple]:
    """Rank claims by support, coverage, and simplicity.
    
    Primary sort:
    1. Support (descending)
    2. Coverage (descending)
    3. Antecedent simplicity (prefer threshold over top_p)
    4. Claim string lexicographic (for stable tie-breaking)
    
    Args:
        scored_claims: List of (antecedent, consequent, score) tuples
        max_claims: Maximum number of claims to return (None = all)
        
    Returns:
        Sorted and limited list of tuples
    """
    def sort_key(item):
        antecedent, consequent, score = item
        
        # Simplicity score: threshold predicates are simpler than top_p
        simplicity = 0
        if antecedent.predicate_type == "threshold":
            simplicity = 2
        elif antecedent.predicate_type == "layer_count":
            simplicity = 1
        else:  # top_p
            simplicity = 0
        
        # Build claim string for tie-breaking
        claim_str = f"{antecedent.to_dsl_string()} -> {consequent.to_dsl_string()}"
        
        # Return sort key: (support desc, coverage desc, simplicity desc, claim_str asc)
        return (
            -score.support,  # Negative for descending
            -score.coverage,
            -simplicity,
            claim_str,  # Lexicographic ascending
        )
    
    sorted_claims = sorted(scored_claims, key=sort_key)
    
    if max_claims is not None:
        sorted_claims = sorted_claims[:max_claims]
    
    return sorted_claims


def build_claims_from_scored(
    scored_claims: List[tuple],
    meta_template: Dict[str, Any],
) -> List[Claim]:
    """Build Claim objects from scored tuples.
    
    Args:
        scored_claims: List of (antecedent, consequent, score) tuples
        meta_template: Template metadata dictionary to include in each claim
        
    Returns:
        List of Claim objects
    """
    claims = []
    
    for antecedent, consequent, score in scored_claims:
        # Build claim string
        claim_string = f"{antecedent.to_dsl_string()} -> {consequent.to_dsl_string()}"
        
        # Copy metadata
        meta = dict(meta_template)
        meta["antecedent_dsl"] = antecedent.to_dsl_string()
        meta["consequent_dsl"] = consequent.to_dsl_string()
        
        claim = Claim(
            antecedent=antecedent,
            consequent=consequent,
            score=score,
            claim_string=claim_string,
            meta=meta,
        )
        
        claims.append(claim)
    
    return claims


def compute_claim_statistics(claims: List[Claim]) -> Dict[str, Any]:
    """Compute summary statistics for a list of claims.
    
    Args:
        claims: List of Claim objects
        
    Returns:
        Dictionary with summary statistics
    """
    if not claims:
        return {
            "n_claims": 0,
            "mean_support": 0.0,
            "mean_coverage": 0.0,
            "median_support": 0.0,
            "median_coverage": 0.0,
        }
    
    supports = [c.support for c in claims]
    coverages = [c.coverage for c in claims]
    
    return {
        "n_claims": len(claims),
        "mean_support": float(np.mean(supports)),
        "mean_coverage": float(np.mean(coverages)),
        "median_support": float(np.median(supports)),
        "median_coverage": float(np.median(coverages)),
        "min_support": float(np.min(supports)),
        "max_support": float(np.max(supports)),
        "min_coverage": float(np.min(coverages)),
        "max_coverage": float(np.max(coverages)),
    }
