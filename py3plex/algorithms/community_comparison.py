"""
Multilayer community comparison methods.

Functions to compare community assignments across layers:
- Adjusted Rand Index (ARI)
- Normalized Mutual Information (NMI)
- Adjusted Mutual Information (AMI)
- Hierarchical community maps

These methods help analyze how community structure varies across layers.

Authors: py3plex contributors
Date: 2025
"""

from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from collections import defaultdict

try:
    from sklearn.metrics import (
        adjusted_rand_score,
        adjusted_mutual_info_score,
        normalized_mutual_info_score,
    )
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


def compare_communities_ari(
    communities1: Dict[Any, int],
    communities2: Dict[Any, int]
) -> float:
    """Compare two community assignments using Adjusted Rand Index.
    
    ARI measures similarity between two clusterings, adjusted for chance.
    Range: [-1, 1], where 1 = perfect agreement, 0 = random, -1 = perfect disagreement.
    
    Args:
        communities1: Dictionary mapping nodes to community IDs (first clustering)
        communities2: Dictionary mapping nodes to community IDs (second clustering)
        
    Returns:
        Adjusted Rand Index score
        
    Raises:
        ImportError: If scikit-learn is not available
        
    Example:
        >>> comm1 = {'A': 0, 'B': 0, 'C': 1}
        >>> comm2 = {'A': 0, 'B': 0, 'C': 0}
        >>> compare_communities_ari(comm1, comm2)
        0.0
        
    References:
        - Hubert, L., & Arabie, P. (1985). "Comparing partitions."
          Journal of Classification, 2(1), 193-218.
    """
    if not SKLEARN_AVAILABLE:
        raise ImportError(
            "scikit-learn is required for ARI computation. "
            "Install with: pip install scikit-learn"
        )
    
    # Ensure we're comparing the same nodes
    common_nodes = set(communities1.keys()) & set(communities2.keys())
    if not common_nodes:
        raise ValueError("No common nodes between community assignments")
    
    # Create aligned label arrays
    labels1 = [communities1[node] for node in sorted(common_nodes)]
    labels2 = [communities2[node] for node in sorted(common_nodes)]
    
    return adjusted_rand_score(labels1, labels2)


def compare_communities_nmi(
    communities1: Dict[Any, int],
    communities2: Dict[Any, int],
    average_method: str = "arithmetic"
) -> float:
    """Compare two community assignments using Normalized Mutual Information.
    
    NMI measures the mutual information between two clusterings,
    normalized to [0, 1] where 1 = perfect agreement, 0 = independent.
    
    Args:
        communities1: Dictionary mapping nodes to community IDs (first clustering)
        communities2: Dictionary mapping nodes to community IDs (second clustering)
        average_method: Averaging method ('arithmetic', 'geometric', 'min', 'max')
        
    Returns:
        Normalized Mutual Information score
        
    Raises:
        ImportError: If scikit-learn is not available
        
    Example:
        >>> comm1 = {'A': 0, 'B': 0, 'C': 1}
        >>> comm2 = {'A': 1, 'B': 1, 'C': 0}
        >>> compare_communities_nmi(comm1, comm2)
        1.0
        
    References:
        - Strehl, A., & Ghosh, J. (2002). "Cluster ensembles."
          Journal of Machine Learning Research, 3, 583-617.
    """
    if not SKLEARN_AVAILABLE:
        raise ImportError(
            "scikit-learn is required for NMI computation. "
            "Install with: pip install scikit-learn"
        )
    
    # Ensure we're comparing the same nodes
    common_nodes = set(communities1.keys()) & set(communities2.keys())
    if not common_nodes:
        raise ValueError("No common nodes between community assignments")
    
    # Create aligned label arrays
    labels1 = [communities1[node] for node in sorted(common_nodes)]
    labels2 = [communities2[node] for node in sorted(common_nodes)]
    
    return normalized_mutual_info_score(labels1, labels2, average_method=average_method)


def compare_communities_ami(
    communities1: Dict[Any, int],
    communities2: Dict[Any, int],
    average_method: str = "arithmetic"
) -> float:
    """Compare two community assignments using Adjusted Mutual Information.
    
    AMI is mutual information adjusted for chance, normalized to [-1, 1]
    where 1 = perfect agreement, 0 = random, negative values = worse than random.
    
    Args:
        communities1: Dictionary mapping nodes to community IDs (first clustering)
        communities2: Dictionary mapping nodes to community IDs (second clustering)
        average_method: Averaging method ('arithmetic', 'geometric', 'min', 'max')
        
    Returns:
        Adjusted Mutual Information score
        
    Raises:
        ImportError: If scikit-learn is not available
        
    Example:
        >>> comm1 = {'A': 0, 'B': 0, 'C': 1, 'D': 1}
        >>> comm2 = {'A': 0, 'B': 0, 'C': 1, 'D': 1}
        >>> compare_communities_ami(comm1, comm2)
        1.0
        
    References:
        - Vinh, N. X., et al. (2010). "Information theoretic measures for
          clusterings comparison." ICML, 2837-2854.
    """
    if not SKLEARN_AVAILABLE:
        raise ImportError(
            "scikit-learn is required for AMI computation. "
            "Install with: pip install scikit-learn"
        )
    
    # Ensure we're comparing the same nodes
    common_nodes = set(communities1.keys()) & set(communities2.keys())
    if not common_nodes:
        raise ValueError("No common nodes between community assignments")
    
    # Create aligned label arrays
    labels1 = [communities1[node] for node in sorted(common_nodes)]
    labels2 = [communities2[node] for node in sorted(common_nodes)]
    
    return adjusted_mutual_info_score(labels1, labels2, average_method=average_method)


def compare_multilayer_communities(
    layer_communities: Dict[str, Dict[Any, int]],
    metrics: Optional[List[str]] = None
) -> Dict[Tuple[str, str], Dict[str, float]]:
    """Compare community structures across multiple layers.
    
    Computes pairwise comparison metrics between all pairs of layers.
    
    Args:
        layer_communities: Dictionary mapping layer names to community assignments
        metrics: List of metrics to compute ('ari', 'nmi', 'ami'). Default: all.
        
    Returns:
        Dictionary mapping (layer1, layer2) -> {metric: score}
        
    Example:
        >>> communities = {
        ...     'social': {'A': 0, 'B': 0, 'C': 1},
        ...     'email': {'A': 0, 'B': 1, 'C': 1},
        ...     'work': {'A': 0, 'B': 0, 'C': 0}
        ... }
        >>> results = compare_multilayer_communities(communities)
        >>> results[('social', 'email')]['ari']
        0.333...
    """
    if metrics is None:
        metrics = ['ari', 'nmi', 'ami']
    
    results = {}
    layer_names = list(layer_communities.keys())
    
    for i, layer1 in enumerate(layer_names):
        for layer2 in layer_names[i+1:]:
            comm1 = layer_communities[layer1]
            comm2 = layer_communities[layer2]
            
            scores = {}
            
            if 'ari' in metrics:
                try:
                    scores['ari'] = compare_communities_ari(comm1, comm2)
                except Exception:
                    scores['ari'] = np.nan
            
            if 'nmi' in metrics:
                try:
                    scores['nmi'] = compare_communities_nmi(comm1, comm2)
                except Exception:
                    scores['nmi'] = np.nan
            
            if 'ami' in metrics:
                try:
                    scores['ami'] = compare_communities_ami(comm1, comm2)
                except Exception:
                    scores['ami'] = np.nan
            
            results[(layer1, layer2)] = scores
    
    return results


def hierarchical_community_map(
    layer_communities: Dict[str, Dict[Any, int]],
    method: str = "jaccard"
) -> Dict[Tuple[str, int, int], float]:
    """Create hierarchical map of community relationships across layers.
    
    Maps how communities in one layer relate to communities in another layer.
    
    Args:
        layer_communities: Dictionary mapping layer names to community assignments
        method: Similarity method ('jaccard', 'overlap', 'dice')
        
    Returns:
        Dictionary mapping (layer1, comm1, layer2, comm2) -> similarity score
        
    Example:
        >>> communities = {
        ...     'L1': {'A': 0, 'B': 0, 'C': 1},
        ...     'L2': {'A': 0, 'B': 1, 'C': 1}
        ... }
        >>> map_result = hierarchical_community_map(communities)
    """
    results = {}
    layer_names = list(layer_communities.keys())
    
    for i, layer1 in enumerate(layer_names):
        for layer2 in layer_names[i+1:]:
            comm1 = layer_communities[layer1]
            comm2 = layer_communities[layer2]
            
            # Group nodes by community
            comm1_groups = defaultdict(set)
            comm2_groups = defaultdict(set)
            
            for node, comm_id in comm1.items():
                comm1_groups[comm_id].add(node)
            
            for node, comm_id in comm2.items():
                comm2_groups[comm_id].add(node)
            
            # Compute pairwise similarities
            for c1_id, c1_nodes in comm1_groups.items():
                for c2_id, c2_nodes in comm2_groups.items():
                    similarity = _compute_set_similarity(c1_nodes, c2_nodes, method)
                    results[(layer1, c1_id, layer2, c2_id)] = similarity
    
    return results


def _compute_set_similarity(set1: set, set2: set, method: str) -> float:
    """Compute similarity between two sets.
    
    Args:
        set1: First set
        set2: Second set
        method: Similarity method ('jaccard', 'overlap', 'dice')
        
    Returns:
        Similarity score in [0, 1]
    """
    intersection = len(set1 & set2)
    
    if method == "jaccard":
        union = len(set1 | set2)
        return intersection / union if union > 0 else 0.0
    
    elif method == "overlap":
        min_size = min(len(set1), len(set2))
        return intersection / min_size if min_size > 0 else 0.0
    
    elif method == "dice":
        sum_sizes = len(set1) + len(set2)
        return 2 * intersection / sum_sizes if sum_sizes > 0 else 0.0
    
    else:
        raise ValueError(f"Unknown similarity method: {method}")


def community_persistence_score(
    layer_communities: Dict[str, Dict[Any, int]],
    node: Any
) -> float:
    """Measure how consistently a node stays in the same community across layers.
    
    Args:
        layer_communities: Dictionary mapping layer names to community assignments
        node: Node to analyze
        
    Returns:
        Persistence score in [0, 1], where 1 = always in same community
        
    Algorithm:
        Computes pairwise agreement of community membership across all layers.
    """
    # Get community assignments for this node across layers
    node_communities = []
    for layer_name, communities in layer_communities.items():
        if node in communities:
            node_communities.append(communities[node])
    
    if len(node_communities) < 2:
        return 1.0  # Trivially consistent if only in one layer
    
    # Count agreements
    agreements = 0
    comparisons = 0
    
    for i in range(len(node_communities)):
        for j in range(i+1, len(node_communities)):
            comparisons += 1
            if node_communities[i] == node_communities[j]:
                agreements += 1
    
    return agreements / comparisons if comparisons > 0 else 1.0
