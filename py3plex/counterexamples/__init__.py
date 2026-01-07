"""Network Counterexample Generation for py3plex.

This module provides counterexample generation capabilities for multilayer networks,
allowing users to find and minimize violations of network invariants and claims.

Example:
    >>> from py3plex.dsl import Q
    >>> from py3plex.core import multinet
    >>>
    >>> # Build network
    >>> net = multinet.multi_layer_network()
    >>> # ... add nodes and edges ...
    >>>
    >>> # Find counterexample
    >>> cex = (Q.counterexample()
    ...          .claim("degree__ge(k) -> pagerank__rank_gt(r)")
    ...          .params(k=10, r=50)
    ...          .seed(42)
    ...          .execute(net))
    >>>
    >>> if cex:
    ...     print(cex.explain())
    ...     witness = cex.subgraph
"""

from .types import (
    Claim,
    Violation,
    Counterexample,
    Budget,
    MinimizationReport,
)

from .engine import (
    find_violation,
    build_witness,
    minimize_witness,
    find_counterexample,
)

__all__ = [
    "Claim",
    "Violation",
    "Counterexample",
    "Budget",
    "MinimizationReport",
    "find_violation",
    "build_witness",
    "minimize_witness",
    "find_counterexample",
]
