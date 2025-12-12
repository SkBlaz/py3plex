"""Canonical schema for uncertainty-aware edge and node attributes.

This module defines standard attribute names for representing uncertain
network data. Using these constants ensures consistency across the library.

The schema supports both deterministic and uncertain representations:

Deterministic mode:
    - Use 'weight' for edge weights (legacy, backward compatible)
    - No uncertainty attributes present

Uncertain mode:
    - Use 'weight_mean', 'weight_var' for parametric uncertainty
    - Or 'weight_dist' for full distribution (UncertainValue)
    - Use 'p_exist' for edge/node existence probability
"""

# =============================================================================
# Edge Attributes
# =============================================================================

# Core weight attributes
WEIGHT = "weight"
"""Standard edge weight attribute (legacy, deterministic)."""

WEIGHT_MEAN = "weight_mean"
"""Mean of edge weight distribution."""

WEIGHT_VAR = "weight_var"
"""Variance of edge weight distribution."""

WEIGHT_STD = "weight_std"
"""Standard deviation of edge weight distribution."""

WEIGHT_DIST = "weight_dist"
"""Full weight distribution as UncertainValue object."""

# Existence probability
P_EXIST = "p_exist"
"""Probability that this edge exists (0.0 to 1.0).

Used for uncertain networks where edges may or may not be present.
A value of 1.0 means the edge definitely exists (deterministic).
Values < 1.0 represent uncertainty in edge existence.
"""

# Legacy alias for backward compatibility
CERTAINTY = "certainty"
"""Legacy alias for p_exist. Deprecated, use p_exist instead.

For backward compatibility only. New code should use P_EXIST.
"""

# =============================================================================
# Node Attributes
# =============================================================================

# Node existence probability
NODE_P_EXIST = "p_exist"
"""Probability that this node exists (0.0 to 1.0).

Used for uncertain networks where nodes may or may not be present.
Most networks have deterministic nodes (p_exist=1.0), but some
applications need uncertain node existence.
"""

# =============================================================================
# Computed Statistics Attributes
# =============================================================================

# Centrality metrics with uncertainty
CENTRALITY_MEAN = "centrality_mean"
"""Mean centrality value."""

CENTRALITY_STD = "centrality_std"
"""Standard deviation of centrality."""

CENTRALITY_DIST = "centrality_dist"
"""Full centrality distribution as UncertainValue or StatSeries."""

# Community detection with uncertainty
COMMUNITY_LABEL = "community"
"""Community label (deterministic)."""

COMMUNITY_STABILITY = "community_stability"
"""Stability of community assignment (0.0 to 1.0).

Fraction of runs in which this node was assigned to its modal community.
"""

# =============================================================================
# Metadata Attributes
# =============================================================================

UNCERTAINTY_SOURCE = "uncertainty_source"
"""String describing the source of uncertainty.

Examples: "bootstrap", "perturbation", "empirical", "model"
"""

N_SAMPLES = "n_samples"
"""Number of samples/runs used to estimate uncertainty."""

CONFIDENCE_LEVEL = "confidence_level"
"""Confidence level for intervals (e.g., 0.95 for 95% CI)."""

# =============================================================================
# Schema Utilities
# =============================================================================

# Attribute groups for validation and documentation
EDGE_UNCERTAINTY_ATTRS = frozenset({
    WEIGHT_MEAN,
    WEIGHT_VAR,
    WEIGHT_STD,
    WEIGHT_DIST,
    P_EXIST,
    CERTAINTY,  # legacy
})
"""Frozenset of all edge attributes related to uncertainty."""

NODE_UNCERTAINTY_ATTRS = frozenset({
    NODE_P_EXIST,
})
"""Frozenset of all node attributes related to uncertainty."""

STAT_UNCERTAINTY_ATTRS = frozenset({
    CENTRALITY_MEAN,
    CENTRALITY_STD,
    CENTRALITY_DIST,
    COMMUNITY_STABILITY,
})
"""Frozenset of all computed statistic attributes related to uncertainty."""

METADATA_ATTRS = frozenset({
    UNCERTAINTY_SOURCE,
    N_SAMPLES,
    CONFIDENCE_LEVEL,
})
"""Frozenset of metadata attributes for uncertainty tracking."""

ALL_UNCERTAINTY_ATTRS = (
    EDGE_UNCERTAINTY_ATTRS
    | NODE_UNCERTAINTY_ATTRS
    | STAT_UNCERTAINTY_ATTRS
    | METADATA_ATTRS
)
"""Set of all uncertainty-related attributes."""


def is_uncertainty_attr(attr_name: str) -> bool:
    """Check if an attribute name is uncertainty-related.

    Parameters
    ----------
    attr_name : str
        The attribute name to check.

    Returns
    -------
    bool
        True if the attribute is uncertainty-related, False otherwise.

    Examples
    --------
    >>> is_uncertainty_attr("weight_mean")
    True
    >>> is_uncertainty_attr("weight")
    False
    >>> is_uncertainty_attr("p_exist")
    True
    """
    return attr_name in ALL_UNCERTAINTY_ATTRS


def is_deterministic_edge(edge_data: dict) -> bool:
    """Check if an edge is deterministic (no uncertainty attributes).

    Parameters
    ----------
    edge_data : dict
        Edge attribute dictionary.

    Returns
    -------
    bool
        True if edge has no uncertainty attributes, False otherwise.

    Examples
    --------
    >>> is_deterministic_edge({"weight": 1.0})
    True
    >>> is_deterministic_edge({"weight_mean": 1.0, "weight_var": 0.1})
    False
    >>> is_deterministic_edge({"p_exist": 0.8})
    False
    """
    return not any(attr in edge_data for attr in EDGE_UNCERTAINTY_ATTRS)


def is_deterministic_node(node_data: dict) -> bool:
    """Check if a node is deterministic (no uncertainty attributes).

    Parameters
    ----------
    node_data : dict
        Node attribute dictionary.

    Returns
    -------
    bool
        True if node has no uncertainty attributes, False otherwise.

    Examples
    --------
    >>> is_deterministic_node({"label": "A"})
    True
    >>> is_deterministic_node({"p_exist": 0.9})
    False
    """
    return not any(attr in node_data for attr in NODE_UNCERTAINTY_ATTRS)


def get_edge_weight(edge_data: dict, default: float = 1.0) -> float:
    """Get edge weight, handling both deterministic and uncertain representations.

    Priority order:
    1. weight (deterministic, legacy)
    2. weight_mean (uncertain)
    3. weight_dist.mean() (full distribution)
    4. default value

    Parameters
    ----------
    edge_data : dict
        Edge attribute dictionary.
    default : float, default=1.0
        Default weight if no weight attribute is found.

    Returns
    -------
    float
        The edge weight (mean if uncertain).

    Examples
    --------
    >>> get_edge_weight({"weight": 2.0})
    2.0
    >>> get_edge_weight({"weight_mean": 3.0})
    3.0
    >>> get_edge_weight({})
    1.0
    """
    # Check deterministic weight first (backward compat)
    if WEIGHT in edge_data:
        return float(edge_data[WEIGHT])

    # Check mean of uncertain weight
    if WEIGHT_MEAN in edge_data:
        return float(edge_data[WEIGHT_MEAN])

    # Check full distribution
    if WEIGHT_DIST in edge_data:
        dist = edge_data[WEIGHT_DIST]
        # Assume it's an UncertainValue with a mean() method
        if hasattr(dist, "mean"):
            return float(dist.mean())

    return default


def get_edge_existence_prob(edge_data: dict, default: float = 1.0) -> float:
    """Get edge existence probability.

    Parameters
    ----------
    edge_data : dict
        Edge attribute dictionary.
    default : float, default=1.0
        Default probability if no p_exist attribute is found.

    Returns
    -------
    float
        Edge existence probability (0.0 to 1.0).

    Examples
    --------
    >>> get_edge_existence_prob({"p_exist": 0.8})
    0.8
    >>> get_edge_existence_prob({"certainty": 0.9})  # legacy
    0.9
    >>> get_edge_existence_prob({})
    1.0
    """
    if P_EXIST in edge_data:
        return float(edge_data[P_EXIST])

    # Check legacy alias
    if CERTAINTY in edge_data:
        return float(edge_data[CERTAINTY])

    return default


def get_node_existence_prob(node_data: dict, default: float = 1.0) -> float:
    """Get node existence probability.

    Parameters
    ----------
    node_data : dict
        Node attribute dictionary.
    default : float, default=1.0
        Default probability if no p_exist attribute is found.

    Returns
    -------
    float
        Node existence probability (0.0 to 1.0).

    Examples
    --------
    >>> get_node_existence_prob({"p_exist": 0.95})
    0.95
    >>> get_node_existence_prob({})
    1.0
    """
    if NODE_P_EXIST in node_data:
        return float(node_data[NODE_P_EXIST])

    return default
