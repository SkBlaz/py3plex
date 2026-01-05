"""Counterfactual reasoning and robustness analysis for multilayer networks.

This module provides tools for testing the sensitivity of analytical conclusions
to explicit structural interventions in the network. This is distinct from
uncertainty quantification (UQ):

- **UQ** quantifies uncertainty of an estimate (e.g., "what is the error bar?")
- **Counterfactuals** quantify sensitivity to interventions (e.g., "would my 
  conclusion hold if I removed 10% of edges?")

Key Concepts:
-------------
- **Intervention**: A controlled structural change to the network (e.g., remove
  edges, rewire, perturb weights)
- **Baseline**: The original query result on the unmodified network
- **Counterfactual**: Query results after applying interventions
- **Robustness**: How stable conclusions are to interventions

Public API:
-----------
The public API consists of three QueryBuilder methods:

1. robustness_check() - Primary interface for quick robustness testing
2. try_strengths() - Compare light/medium/heavy intervention strengths
3. counterfactualize() - Advanced interface with custom intervention specs

Usage Example:
--------------
    >>> from py3plex.dsl import Q
    >>> from py3plex.core import multinet
    >>> 
    >>> # Create network
    >>> net = multinet.multi_layer_network()
    >>> # ... add nodes and edges ...
    >>> 
    >>> # Quick robustness check
    >>> report = (Q.nodes()
    ...           .compute("pagerank")
    ...           .robustness_check(net))
    >>> report.show()
    >>> 
    >>> # Check if top-k ranking is stable
    >>> stable_nodes = report.stable_top_k(k=10, threshold=0.8)
    >>> fragile_nodes = report.fragile(n=5)

Module Structure:
-----------------
- spec: Immutable intervention specifications
- engine: Deterministic execution engine
- comparator: Statistical comparison utilities
- result: Result containers (CounterfactualResult, RobustnessReport)
- presets: User-friendly preset configurations
"""

from .spec import (
    InterventionSpec,
    RemoveEdgesSpec,
    RewireDegreePreservingSpec,
    ShuffleWeightsSpec,
    KnockoutSpec,
)

from .result import (
    CounterfactualResult,
    RobustnessReport,
)

from .engine import (
    CounterfactualEngine,
)

from .presets import (
    get_preset,
    list_presets,
    PRESET_QUICK,
    PRESET_DEGREE_SAFE,
    PRESET_LAYER_SAFE,
    PRESET_WEIGHT_ONLY,
    PRESET_TARGETED,
)

__all__ = [
    # Intervention specs
    "InterventionSpec",
    "RemoveEdgesSpec",
    "RewireDegreePreservingSpec",
    "ShuffleWeightsSpec",
    "KnockoutSpec",
    # Results
    "CounterfactualResult",
    "RobustnessReport",
    # Engine
    "CounterfactualEngine",
    # Presets
    "get_preset",
    "list_presets",
    "PRESET_QUICK",
    "PRESET_DEGREE_SAFE",
    "PRESET_LAYER_SAFE",
    "PRESET_WEIGHT_ONLY",
    "PRESET_TARGETED",
]
