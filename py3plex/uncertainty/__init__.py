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
from .partition import (
    CommunityDistribution,
    partition_dict_to_array,
    partition_array_to_dict,
)
from .community_result import (
    ProbabilisticCommunityResult,
)
from .community_ensemble import (
    generate_community_ensemble,
)
from .resampling_graph import (
    perturb_network_edges,
    bootstrap_network_edges,
    resample_network_nodes,
)
from .noise_models import (
    NoiseModel,
    NoNoise,
    EdgeDrop,
    WeightNoise,
    LayerDrop,
    TemporalWindowBootstrap,
    noise_model_from_dict,
)
from .partition_uq import (
    PartitionUQ,
)
from .partition_types import (
    PartitionOutput,
)
from .partition_reducers import (
    PartitionReducer,
    NodeEntropyReducer,
    NodeMarginalReducer,
    CoAssignmentReducer,
    PartitionDistanceReducer,
    ConsensusReducer,
    ConsensusPartitionReducer,
    StabilityReducer,
)
from .partition_metrics import (
    variation_of_information,
    normalized_mutual_information,
    adjusted_rand_index,
    vi,
    nmi,
    ari,
    pairwise_partition_distances,
)
from .selection_types import (
    SelectionOutput,
)
from .selection_uq import (
    SelectionUQ,
)
from .selection_reducers import (
    SelectionReducer,
    InclusionReducer,
    SizeReducer,
    StabilityReducer,
    RankReducer,
    TopKOverlapReducer,
    GroupedReducer,
)
from .selection_execution import (
    execute_selection_uq,
)
from .ci_utils import (
    wilson_score_interval,
    clopper_pearson_interval,
    binomial_proportion_ci,
    rank_ci_from_samples,
)
from .plan import (
    UQPlan,
    UQResult,
)
from .runner import (
    run_uq,
)
from .reducers.base import (
    Reducer,
)
from .stratification import (
    StratificationSpec,
    auto_select_strata,
    compute_composite_strata,
    compute_variance_reduction_ratio,
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
    # Community distributions
    "CommunityDistribution",
    "ProbabilisticCommunityResult",
    "generate_community_ensemble",
    "partition_dict_to_array",
    "partition_array_to_dict",
    # Graph resampling
    "perturb_network_edges",
    "bootstrap_network_edges",
    "resample_network_nodes",
    # Noise models
    "NoiseModel",
    "NoNoise",
    "EdgeDrop",
    "WeightNoise",
    "LayerDrop",
    "TemporalWindowBootstrap",
    "noise_model_from_dict",
    # Partition UQ
    "PartitionUQ",
    "PartitionOutput",
    # Partition reducers
    "PartitionReducer",
    "NodeEntropyReducer",
    "NodeMarginalReducer",
    "CoAssignmentReducer",
    "PartitionDistanceReducer",
    "ConsensusReducer",
    "ConsensusPartitionReducer",
    "StabilityReducer",
    # Partition metrics
    "variation_of_information",
    "normalized_mutual_information",
    "adjusted_rand_index",
    "vi",
    "nmi",
    "ari",
    "pairwise_partition_distances",
    # Selection UQ
    "SelectionOutput",
    "SelectionUQ",
    "SelectionReducer",
    "InclusionReducer",
    "SizeReducer",
    "StabilityReducer",
    "RankReducer",
    "TopKOverlapReducer",
    "GroupedReducer",
    "execute_selection_uq",
    # CI utilities
    "wilson_score_interval",
    "clopper_pearson_interval",
    "binomial_proportion_ci",
    "rank_ci_from_samples",
    # UQ execution spine
    "UQPlan",
    "UQResult",
    "run_uq",
    "Reducer",
    # Stratification
    "StratificationSpec",
    "auto_select_strata",
    "compute_composite_strata",
    "compute_variance_reduction_ratio",
]
