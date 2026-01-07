"""Typed failure modes for robustness contracts.

Each failure mode has a clear semantic meaning and can be tested for
in property-based tests.
"""

from enum import Enum


class FailureMode(Enum):
    """Typed failure modes for contract violations.
    
    Each failure mode represents a specific reason why a contract might fail,
    with clear semantics that enable automated testing and debugging.
    """
    
    INSUFFICIENT_BASELINE = "insufficient_baseline"
    """Baseline query returned empty or insufficient results.
    
    Occurs when:
    - Baseline query returns 0 nodes/edges
    - Baseline has fewer items than required for the predicate (e.g., top_k=20 but only 10 nodes)
    - Baseline community detection fails or returns trivial partition
    
    Contract cannot be evaluated without sufficient baseline data.
    """
    
    NONDETERMINISM_LEAK = "nondeterminism_leak"
    """Determinism requirement violated.
    
    Occurs when:
    - seed is None but allow_nondeterminism=False (default)
    - Perturbation or metric computation is inherently nondeterministic without seed
    
    Contracts require determinism for certification-grade reproducibility.
    """
    
    PERTURBATION_INVALID = "perturbation_invalid"
    """Perturbation specification is invalid or unsupported.
    
    Occurs when:
    - Unknown perturbation type specified
    - Perturbation parameters are out of valid range (e.g., p < 0 or p > 1)
    - Network structure incompatible with perturbation (e.g., weighted perturbation on unweighted graph)
    
    Check perturbation spec and network compatibility.
    """
    
    METRIC_UNDEFINED = "metric_undefined"
    """Metric or comparison is undefined for the given data.
    
    Occurs when:
    - Ranking has too many ties to compute meaningful Kendall's tau
    - Network becomes disconnected/degenerate after perturbation
    - Division by zero or NaN in metric computation
    - Clustering coefficient undefined for graph with no triangles
    
    Some metrics are undefined for certain network structures.
    """
    
    CONTRACT_VIOLATION = "contract_violation"
    """Contract predicate violated (normal failure case).
    
    Occurs when:
    - Predicate threshold not met across perturbation grid
    - Jaccard similarity too low for top-k stability
    - Kendall's tau too low for ranking stability
    - Variation of information too high for partition stability
    
    This is the standard failure mode - the conclusion is not robust.
    """
    
    REPAIR_IMPOSSIBLE = "repair_impossible"
    """Repair attempted but no stable subset found.
    
    Occurs when:
    - Stable core is empty (no items pass frequency threshold)
    - Ranking tiers cannot be constructed
    - Community has no stable nodes
    - Repaired output still violates predicate
    
    The conclusion is so unstable that repair cannot recover a usable result.
    """
    
    RESOURCE_LIMIT = "resource_limit"
    """Resource budget exceeded during evaluation.
    
    Occurs when:
    - Execution time exceeds budget.max_seconds
    - Memory usage exceeds budget.max_memory_mb (if tracked)
    - Too many iterations in repair algorithm
    
    Partial evidence may be available in result.
    """
    
    EXECUTION_ERROR = "execution_error"
    """Unexpected error during contract evaluation.
    
    Occurs when:
    - NetworkX algorithm crashes
    - Numerical instability in computation
    - Unexpected network structure
    - Bug in contract evaluation code
    
    This is a catch-all for unexpected errors. Check details and traceback.
    """
