"""Query Sensitivity Analysis for py3plex.

This module provides sensitivity analysis capabilities for network queries,
distinct from Uncertainty Quantification (UQ):

- **UQ**: Estimates uncertainty of metric VALUES (mean, std, CI)
- **Sensitivity**: Assesses stability of CONCLUSIONS (rankings, sets, communities)
  under perturbations

Sensitivity analysis answers: "Is this result robust to perturbations?"
UQ answers: "What is the uncertainty in this measurement?"

Key concepts:
- Stability curves: How conclusions change as perturbation strength varies
- Ranking stability: Jaccard@k, Kendall-τ for comparing rankings
- Community stability: Variation of information, flip probability
- Local influence: Per-node/per-layer attribution of instability
- Tipping points: Perturbation thresholds where conclusions collapse

Examples
--------
>>> from py3plex.dsl import Q
>>> # Sensitivity of top-k centrality rankings under edge perturbation
>>> result = (
...     Q.nodes()
...      .compute("betweenness_centrality")
...      .order_by("-betweenness_centrality")
...      .limit(20)
...      .sensitivity(
...          perturb="edge_drop",
...          grid=[0.0, 0.05, 0.1, 0.15, 0.2],
...          n_samples=30,
...          metrics=["jaccard_at_k(20)", "kendall_tau"],
...          seed=42
...      )
...      .execute(network)
... )
>>>
>>> # Access stability curves
>>> curves = result.sensitivity_curves
>>> print(curves["jaccard_at_k(20)"])  # {0.0: 1.0, 0.05: 0.95, ...}
>>>
>>> # Export to pandas with sensitivity columns
>>> df = result.to_pandas(expand_sensitivity=True)
"""

from .types import (
    SensitivityResult,
    PerturbationSpec,
    StabilityCurve,
    LocalInfluence,
)
from .perturbations import (
    edge_drop,
    degree_preserving_rewire,
    apply_perturbation,
)
from .metrics import (
    jaccard_at_k,
    kendall_tau,
    variation_of_information,
    community_flip_probability,
)
from .executor import (
    run_sensitivity_analysis,
)

__all__ = [
    # Core types
    "SensitivityResult",
    "PerturbationSpec",
    "StabilityCurve",
    "LocalInfluence",
    # Perturbations
    "edge_drop",
    "degree_preserving_rewire",
    "apply_perturbation",
    # Stability metrics
    "jaccard_at_k",
    "kendall_tau",
    "variation_of_information",
    "community_flip_probability",
    # Execution
    "run_sensitivity_analysis",
]
