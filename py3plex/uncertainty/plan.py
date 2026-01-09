"""UQ execution plan specification.

This module defines the UQPlan dataclass - the canonical specification for
uncertainty quantification execution. UQPlan is strategy-agnostic and
reducer-driven.

Examples
--------
>>> from py3plex.uncertainty.plan import UQPlan
>>> from py3plex.uncertainty.noise_models import EdgeDrop
>>> from py3plex.uncertainty.reducers.base import Reducer
>>> 
>>> # Define a plan
>>> plan = UQPlan(
...     base_callable=my_algorithm,
...     strategy="perturbation",
...     noise_model=EdgeDrop(p=0.1),
...     n_samples=100,
...     seed=42,
...     reducers=[...],
...     storage_mode="sketch",
...     backend="python"
... )
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, List, Literal, Optional

from py3plex.uncertainty.noise_models import NoiseModel
from py3plex.uncertainty.reducers.base import Reducer


@dataclass
class UQPlan:
    """Canonical specification for UQ execution.
    
    UQPlan encapsulates all information needed to execute uncertainty
    quantification for any algorithm. It is:
    - Strategy-agnostic (seed, perturbation, bootstrap, jackknife)
    - Reducer-driven (reducers compute statistics online)
    - Reproducible (seed controls all randomness)
    - Memory-efficient (storage_mode controls what to keep)
    
    Attributes
    ----------
    base_callable : Callable[[Network, RNG], SampleOutput]
        Function that executes exactly one algorithm run.
        Must be deterministic given RNG.
        Signature: (network, rng) -> SampleOutput
    strategy : Literal["seed", "perturbation", "bootstrap", "jackknife"]
        Resampling strategy:
        - "seed": Multiple runs with different RNG seeds
        - "perturbation": Apply noise_model before each run
        - "bootstrap": Bootstrap resampling (not yet implemented)
        - "jackknife": Leave-one-out (not yet implemented)
    noise_model : NoiseModel | None
        Noise model for perturbation strategy (required if strategy="perturbation")
        Must be None for seed/bootstrap/jackknife strategies.
    n_samples : int
        Number of samples to generate
    seed : int
        Master random seed for reproducibility
    reducers : list[Reducer]
        List of reducer instances to accumulate statistics.
        Reducers must be provided at construction time.
    storage_mode : Literal["none", "sketch", "samples"]
        Controls what samples are stored:
        - "none": No samples stored (only reducer outputs)
        - "sketch": Store summary statistics (default)
        - "samples": Store all sample outputs (memory-intensive)
    backend : Literal["python", "jax"]
        Execution backend (only "python" currently supported)
        
    Examples
    --------
    >>> from py3plex.uncertainty.plan import UQPlan
    >>> from py3plex.uncertainty.noise_models import NoNoise
    >>> from py3plex.uncertainty.partition_reducers import NodeEntropyReducer
    >>> 
    >>> def my_algorithm(net, rng):
    ...     # Run community detection
    ...     return PartitionOutput(labels={...})
    >>> 
    >>> plan = UQPlan(
    ...     base_callable=my_algorithm,
    ...     strategy="seed",
    ...     noise_model=NoNoise(),
    ...     n_samples=50,
    ...     seed=42,
    ...     reducers=[NodeEntropyReducer(n_nodes=10)],
    ...     storage_mode="sketch",
    ...     backend="python"
    ... )
    """
    
    base_callable: Callable[[Any, Any], Any]
    strategy: Literal["seed", "perturbation", "bootstrap", "jackknife"]
    noise_model: Optional[NoiseModel]
    n_samples: int
    seed: int
    reducers: List[Reducer]
    storage_mode: Literal["none", "sketch", "samples"] = "sketch"
    backend: Literal["python", "jax"] = "python"
    
    def __post_init__(self):
        """Validate plan configuration."""
        # Validate strategy
        valid_strategies = {"seed", "perturbation", "bootstrap", "jackknife"}
        if self.strategy not in valid_strategies:
            raise ValueError(
                f"Invalid strategy '{self.strategy}'. "
                f"Must be one of {valid_strategies}"
            )
        
        # Validate noise_model requirements
        if self.strategy == "perturbation" and self.noise_model is None:
            raise ValueError(
                "noise_model is required when strategy='perturbation'"
            )
        
        if self.strategy != "perturbation" and self.noise_model is not None:
            # Allow NoNoise for any strategy
            from py3plex.uncertainty.noise_models import NoNoise
            if not isinstance(self.noise_model, NoNoise):
                raise ValueError(
                    f"noise_model should be None for strategy='{self.strategy}' "
                    f"(or use NoNoise() explicitly)"
                )
        
        # Validate n_samples
        if self.n_samples < 1:
            raise ValueError(f"n_samples must be >= 1, got {self.n_samples}")
        
        # Validate reducers
        if not isinstance(self.reducers, list):
            raise ValueError("reducers must be a list of Reducer instances")
        
        # Validate storage_mode
        valid_modes = {"none", "sketch", "samples"}
        if self.storage_mode not in valid_modes:
            raise ValueError(
                f"Invalid storage_mode '{self.storage_mode}'. "
                f"Must be one of {valid_modes}"
            )
        
        # Validate backend
        valid_backends = {"python", "jax"}
        if self.backend not in valid_backends:
            raise ValueError(
                f"Invalid backend '{self.backend}'. "
                f"Must be one of {valid_backends}"
            )
        
        if self.backend == "jax":
            raise NotImplementedError("JAX backend not yet implemented")


@dataclass
class UQResult:
    """Result container for UQ execution.
    
    Attributes
    ----------
    n_samples : int
        Number of samples executed
    reducer_outputs : dict
        Dictionary mapping reducer class name to finalized output
    samples : list, optional
        Raw sample outputs (only if storage_mode="samples")
    provenance : dict
        Execution metadata (seed, strategy, noise_model, etc.)
    """
    
    n_samples: int
    reducer_outputs: dict = field(default_factory=dict)
    samples: Optional[List[Any]] = None
    provenance: dict = field(default_factory=dict)
