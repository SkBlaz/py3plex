"""Robustness contracts for DSL v2.

This module provides certification-grade robustness contracts that ensure
query conclusions are stable under structural perturbations. Contracts are
designed to be easy to use (sensible defaults) while allowing explicit control.

Key Features:
-------------
- **1-line usage**: `Q.nodes().compute("pagerank").top_k(20).contract(Robustness()).execute(net)`
- **Sensible defaults**: Auto-infer perturbation, predicates, grid, samples, and seed
- **Typed failure modes**: Explicit failure classification with evidence
- **Repair mechanisms**: Stable cores, tiers, and stable nodes for different conclusion types
- **Deterministic**: Default seed=0 ensures reproducibility
- **Certification-grade provenance**: Full replay capability

Example:
--------
    >>> from py3plex.dsl import Q
    >>> from py3plex.contracts import Robustness
    >>> 
    >>> # Minimal usage with all defaults
    >>> result = (Q.nodes()
    ...           .compute("pagerank")
    ...           .top_k(20, "pagerank")
    ...           .contract(Robustness())
    ...           .execute(net))
    >>> 
    >>> # Check if contract passed
    >>> if result.contract_ok:
    ...     print("Top-20 PageRank is stable!")
    ... else:
    ...     print(f"Contract failed: {result.failure_mode}")
    ...     print("Stable core:", result.stable_core)

Public API:
-----------
- Robustness: Main contract class with sensible defaults
- ContractResult: Result container with evidence and repair
- FailureMode: Enum of typed failure modes
- Predicates: JaccardAtK, KendallTau, PartitionVI, PartitionARI
"""

from .failure_modes import FailureMode
from .predicates import (
    Predicate,
    JaccardAtK,
    KendallTau,
    PartitionVI,
    PartitionARI,
)
from .contract import Robustness
from .result import ContractResult

__all__ = [
    "FailureMode",
    "Predicate",
    "JaccardAtK",
    "KendallTau",
    "PartitionVI",
    "PartitionARI",
    "Robustness",
    "ContractResult",
]
