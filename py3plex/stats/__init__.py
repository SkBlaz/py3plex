"""First-class uncertainty statistics system.

This module provides a complete uncertainty-first statistics system where
every statistic is represented as (value + uncertainty + provenance).

Core components:
- StatValue: Container for value + uncertainty + provenance
- Uncertainty models: Delta, Gaussian, Bootstrap, Empirical, Interval
- Provenance: Recording of computation metadata
- Registry: Enforced registration of statistics with uncertainty models

Examples
--------
>>> from py3plex.stats import StatValue, Delta, Gaussian, Provenance
>>> 
>>> # Deterministic value
>>> sv = StatValue(
...     value=0.42,
...     uncertainty=Delta(0.0),
...     provenance=Provenance("degree", "delta", {})
... )
>>> float(sv)
0.42
>>> sv.std()
0.0
>>> 
>>> # Value with uncertainty
>>> sv2 = StatValue(
...     value=0.5,
...     uncertainty=Gaussian(0.0, 0.05),
...     provenance=Provenance("betweenness", "analytic", {})
... )
>>> sv2.ci(0.95)
(0.402, 0.598)
>>> 
>>> # Arithmetic with uncertainty propagation
>>> sv3 = sv + sv2
>>> sv3.std()  # Propagated uncertainty
"""

from .statvalue import StatValue
from .uncertainty import (
    Uncertainty,
    Delta,
    Gaussian,
    Bootstrap,
    Empirical,
    Interval,
)
from .provenance import Provenance
from .registry import (
    StatisticSpec,
    StatisticsRegistry,
    register_statistic,
    get_statistic,
    list_statistics,
    compute_statistic,
)

__all__ = [
    # Core types
    "StatValue",
    # Uncertainty models
    "Uncertainty",
    "Delta",
    "Gaussian",
    "Bootstrap",
    "Empirical",
    "Interval",
    # Provenance
    "Provenance",
    # Registry
    "StatisticSpec",
    "StatisticsRegistry",
    "register_statistic",
    "get_statistic",
    "list_statistics",
    "compute_statistic",
]
