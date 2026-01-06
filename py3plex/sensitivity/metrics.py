"""Stability metrics for sensitivity analysis.

These metrics compare conclusions (rankings, sets, partitions) across
perturbations. They are NOT uncertainty metrics (which measure value dispersion).

Stability metrics answer: "How much does the CONCLUSION change?"
UQ metrics answer: "What is the uncertainty in the MEASUREMENT?"
"""

from typing import Any, Dict, List, Optional, Set, Tuple
import numpy as np


def jaccard_at_k(
    baseline_ranking: List[Any],
    perturbed_ranking: List[Any],
    k: int,
) -> float:
    """Compute Jaccard similarity of top-k sets.

    Measures how much the top-k set changes under perturbation.
    This is a SET stability metric, not a ranking stability metric.

    Args:
        baseline_ranking: Original ranking (list of node IDs, best first)
        perturbed_ranking: Perturbed ranking (list of node IDs, best first)
        k: Size of top-k set to compare

    Returns:
        Jaccard similarity in [0, 1], where:
        - 1.0 = identical top-k sets
        - 0.0 = completely different top-k sets

    Examples:
        >>> baseline = ['a', 'b', 'c', 'd', 'e']
        >>> perturbed = ['a', 'c', 'b', 'f', 'e']
        >>> jaccard_at_k(baseline, perturbed, k=3)
        0.75  # {a,b,c} vs {a,c,b} -> |{a,b,c}|/|{a,b,c}| = 1.0 for sets
              # Actually: |{a,b,c} ∩ {a,c,b}| / |{a,b,c} ∪ {a,c,b}| = 3/3 = 1.0
    """
    if k <= 0:
        raise ValueError(f"k must be positive, got {k}")

    # Extract top-k sets
    top_k_baseline = set(baseline_ranking[:k])
    top_k_perturbed = set(perturbed_ranking[:k])

    # Compute Jaccard similarity
    intersection = top_k_baseline & top_k_perturbed
    union = top_k_baseline | top_k_perturbed

    if len(union) == 0:
        return 1.0  # Both empty = identical

    return len(intersection) / len(union)


def kendall_tau(
    baseline_ranking: List[Any],
    perturbed_ranking: List[Any],
) -> float:
    """Compute Kendall's tau correlation between rankings.

    Measures pairwise agreement in rankings. This is a RANKING stability metric
    that considers order, not just set membership.

    Args:
        baseline_ranking: Original ranking (list of node IDs, best first)
        perturbed_ranking: Perturbed ranking (list of node IDs, best first)

    Returns:
        Kendall's tau in [-1, 1], where:
        - 1.0 = perfect agreement (same ranking)
        - 0.0 = no correlation
        - -1.0 = perfect disagreement (reversed ranking)

    Examples:
        >>> baseline = ['a', 'b', 'c', 'd']
        >>> perturbed = ['a', 'b', 'c', 'd']
        >>> kendall_tau(baseline, perturbed)
        1.0

        >>> perturbed2 = ['d', 'c', 'b', 'a']
        >>> kendall_tau(baseline, perturbed2)
        -1.0
    """
    # Build rank dictionaries
    baseline_ranks = {item: rank for rank, item in enumerate(baseline_ranking)}
    perturbed_ranks = {item: rank for rank, item in enumerate(perturbed_ranking)}

    # Find common items
    common_items = set(baseline_ranks.keys()) & set(perturbed_ranks.keys())

    if len(common_items) < 2:
        # Need at least 2 items to compute correlation
        return 1.0 if len(common_items) == 1 else 0.0

    # Compute concordant and discordant pairs
    concordant = 0
    discordant = 0

    common_list = list(common_items)
    for i in range(len(common_list)):
        for j in range(i + 1, len(common_list)):
            item_i, item_j = common_list[i], common_list[j]

            # Check if order agrees in both rankings
            baseline_order = baseline_ranks[item_i] < baseline_ranks[item_j]
            perturbed_order = perturbed_ranks[item_i] < perturbed_ranks[item_j]

            if baseline_order == perturbed_order:
                concordant += 1
            else:
                discordant += 1

    # Compute tau
    total_pairs = concordant + discordant
    if total_pairs == 0:
        return 1.0

    tau = (concordant - discordant) / total_pairs
    return tau


def variation_of_information(
    baseline_partition: Dict[Any, int],
    perturbed_partition: Dict[Any, int],
) -> float:
    """Compute variation of information between community partitions.

    Measures distance between community assignments. This is a PARTITION
    stability metric for community detection.

    VI(X,Y) = H(X) + H(Y) - 2*I(X,Y)
    where H is entropy and I is mutual information.

    Args:
        baseline_partition: Original partition {node: community_id}
        perturbed_partition: Perturbed partition {node: community_id}

    Returns:
        Variation of information in [0, ∞), where:
        - 0.0 = identical partitions
        - Higher values = more different partitions
        - Upper bound is 2*log(n) for n nodes

    Examples:
        >>> baseline = {'a': 0, 'b': 0, 'c': 1, 'd': 1}
        >>> perturbed = {'a': 0, 'b': 0, 'c': 1, 'd': 1}
        >>> variation_of_information(baseline, perturbed)
        0.0
    """
    # Find common nodes
    common_nodes = set(baseline_partition.keys()) & set(perturbed_partition.keys())

    if len(common_nodes) == 0:
        return 0.0

    # Build contingency table
    baseline_communities = {}
    perturbed_communities = {}

    for node in common_nodes:
        b_comm = baseline_partition[node]
        p_comm = perturbed_partition[node]

        if b_comm not in baseline_communities:
            baseline_communities[b_comm] = set()
        baseline_communities[b_comm].add(node)

        if p_comm not in perturbed_communities:
            perturbed_communities[p_comm] = set()
        perturbed_communities[p_comm].add(node)

    n = len(common_nodes)

    # Compute entropies
    h_baseline = 0.0
    for comm_nodes in baseline_communities.values():
        p = len(comm_nodes) / n
        if p > 0:
            h_baseline -= p * np.log2(p)

    h_perturbed = 0.0
    for comm_nodes in perturbed_communities.values():
        p = len(comm_nodes) / n
        if p > 0:
            h_perturbed -= p * np.log2(p)

    # Compute mutual information
    mutual_info = 0.0
    for b_comm, b_nodes in baseline_communities.items():
        for p_comm, p_nodes in perturbed_communities.items():
            overlap = b_nodes & p_nodes
            if len(overlap) > 0:
                p_joint = len(overlap) / n
                p_baseline = len(b_nodes) / n
                p_perturbed = len(p_nodes) / n
                mutual_info += p_joint * np.log2(p_joint / (p_baseline * p_perturbed))

    # VI = H(X) + H(Y) - 2*I(X,Y)
    vi = h_baseline + h_perturbed - 2 * mutual_info

    return max(0.0, vi)  # Numerical stability


def community_flip_probability(
    partitions: List[Dict[Any, int]],
    node: Any,
) -> float:
    """Compute probability that a node changes community across perturbations.

    Measures instability of individual node community assignments.

    Args:
        partitions: List of community partitions from different perturbations
        node: Node to analyze

    Returns:
        Flip probability in [0, 1], where:
        - 0.0 = node never changes community
        - 1.0 = node changes community in every perturbation

    Examples:
        >>> partitions = [
        ...     {'a': 0, 'b': 0, 'c': 1},
        ...     {'a': 0, 'b': 1, 'c': 1},
        ...     {'a': 1, 'b': 0, 'c': 1},
        ... ]
        >>> community_flip_probability(partitions, 'a')
        0.67  # 'a' changes community in 2 out of 3 perturbations
    """
    if len(partitions) == 0:
        return 0.0

    # Get baseline assignment (first partition)
    if node not in partitions[0]:
        return 0.0

    baseline_comm = partitions[0][node]

    # Count flips
    flips = 0
    for partition in partitions[1:]:
        if node in partition and partition[node] != baseline_comm:
            flips += 1

    if len(partitions) == 1:
        return 0.0

    return flips / (len(partitions) - 1)


def parse_metric_spec(metric_spec: str) -> Tuple[str, Dict[str, Any]]:
    """Parse a metric specification string.

    Args:
        metric_spec: Metric specification (e.g., 'jaccard_at_k(20)', 'kendall_tau')

    Returns:
        Tuple of (metric_name, kwargs)

    Examples:
        >>> parse_metric_spec('jaccard_at_k(20)')
        ('jaccard_at_k', {'k': 20})

        >>> parse_metric_spec('kendall_tau')
        ('kendall_tau', {})
    """
    if "(" in metric_spec:
        # Parse function call syntax
        name, args_str = metric_spec.split("(", 1)
        args_str = args_str.rstrip(")")

        # Simple parser for numeric arguments
        kwargs = {}
        if args_str:
            try:
                # For now, assume single numeric argument
                if name == "jaccard_at_k":
                    kwargs["k"] = int(args_str)
            except ValueError:
                pass

        return name.strip(), kwargs
    else:
        return metric_spec.strip(), {}
