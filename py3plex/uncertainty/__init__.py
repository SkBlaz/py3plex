"""First-class uncertainty support for py3plex.

This module provides types and utilities for representing statistics with
uncertainty information. The core idea is that every statistic is an object
that can carry a distribution:

- Deterministic mode: object has mean with std=None (certainty 1.0)
- Uncertainty mode: object has mean, std, quantiles populated

This makes uncertainty "first-class" - it's baked into how numbers exist in
the library, not bolted on later.

Examples
--------
>>> from py3plex.uncertainty import StatSeries
>>> # Deterministic result
>>> result = StatSeries(
...     index=['a', 'b', 'c'],
...     mean=np.array([1.0, 2.0, 3.0])
... )
>>> result.is_deterministic
True
>>> result.certainty
1.0

>>> # Uncertain result
>>> result_unc = StatSeries(
...     index=['a', 'b', 'c'],
...     mean=np.array([1.0, 2.0, 3.0]),
...     std=np.array([0.1, 0.2, 0.15]),
...     quantiles={
...         0.025: np.array([0.8, 1.6, 2.7]),
...         0.975: np.array([1.2, 2.4, 3.3])
...     }
... )
>>> result_unc.is_deterministic
False
>>> np.array(result_unc)  # Backward compat - gives mean
array([1., 2., 3.])
"""

from .types import (
    StatSeries,
    StatMatrix,
    CommunityStats,
    ResamplingStrategy,
    UncertaintyMode,
    UncertaintyConfig,
)
from .context import (
    get_uncertainty_config,
    set_uncertainty_config,
    uncertainty_enabled,
)
from .estimation import (
    estimate_uncertainty,
)
from .bootstrap import (
    bootstrap_metric,
)
from .null_models import (
    null_model_metric,
)

__all__ = [
    # Core stat types
    "StatSeries",
    "StatMatrix",
    "CommunityStats",
    # Enums
    "ResamplingStrategy",
    "UncertaintyMode",
    "UncertaintyConfig",
    # Context management
    "get_uncertainty_config",
    "set_uncertainty_config",
    "uncertainty_enabled",
    # Estimation
    "estimate_uncertainty",
    # Bootstrap
    "bootstrap_metric",
    # Null models
    "null_model_metric",
]
