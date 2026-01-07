"""Learning Claims from Data.

This module provides inductive reasoning capabilities for discovering plausible,
interpretable implication-style claims from multilayer network data.

Example:
    >>> from py3plex.dsl import Q
    >>> from py3plex.core import multinet
    >>>
    >>> # Build network
    >>> net = multinet.multi_layer_network()
    >>> # ... add nodes and edges ...
    >>>
    >>> # Learn claims
    >>> claims = (
    ...     Q.learn_claims()
    ...      .from_metrics(["degree", "pagerank"])
    ...      .min_support(0.9)
    ...      .min_coverage(0.05)
    ...      .seed(42)
    ...      .execute(net)
    ... )
    >>>
    >>> # Examine claims
    >>> for claim in claims:
    ...     print(claim.claim_string)
    ...     # Falsify with counterexample engine
    ...     cex = claim.counterexample(net)
"""

from .types import (
    Claim,
    Antecedent,
    Consequent,
    ClaimScore,
)

__all__ = [
    "Claim",
    "Antecedent",
    "Consequent",
    "ClaimScore",
]
