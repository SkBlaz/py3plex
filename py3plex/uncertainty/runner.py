"""UQ execution runner - the single source of truth for UQ execution.

This module implements run_uq(), the canonical function for executing
uncertainty quantification plans. It is:
- Strategy-agnostic (handles seed, perturbation, bootstrap, jackknife)
- Reducer-driven (no algorithm controls execution)
- Memory-efficient (samples only stored if requested)
- Reproducible (seed controls all randomness)

Examples
--------
>>> from py3plex.uncertainty.plan import UQPlan
>>> from py3plex.uncertainty.runner import run_uq
>>> from py3plex.uncertainty.noise_models import NoNoise
>>> from py3plex.uncertainty.partition_reducers import NodeEntropyReducer
>>> 
>>> # Define plan
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
>>> 
>>> # Execute
>>> result = run_uq(plan, network)
>>> result.reducer_outputs  # Dict mapping reducer name -> output
>>> result.provenance  # Execution metadata
"""

from __future__ import annotations

import copy
from typing import Any, List, Optional

import numpy as np

from py3plex.uncertainty.plan import UQPlan, UQResult
from py3plex.uncertainty.noise_models import NoNoise


def run_uq(plan: UQPlan, network: Any) -> UQResult:
    """Execute uncertainty quantification according to plan.
    
    This is the canonical UQ execution function. It implements the
    following strict execution semantics:
    
    1. Initialize RNG sequence from plan.seed
    2. For i in range(n_samples):
        a. Derive per-sample RNG
        b. Apply NoiseModel (or NoNoise)
        c. Call base_callable(net_i, rng_i)
        d. Pass output to ALL reducers
    3. After loop, call finalize() on reducers
    4. Assemble UQResult
    5. Attach centralized provenance
    
    ABSOLUTE RULES:
    - No reducer may control execution
    - No algorithm may loop internally for UQ
    - No sample outputs stored unless storage_mode == "samples"
    
    Parameters
    ----------
    plan : UQPlan
        UQ execution plan specifying all parameters
    network : multi_layer_network
        Input network to analyze
        
    Returns
    -------
    UQResult
        Result container with reducer outputs and provenance
        
    Examples
    --------
    >>> from py3plex.uncertainty.plan import UQPlan
    >>> from py3plex.uncertainty.runner import run_uq
    >>> from py3plex.uncertainty.noise_models import EdgeDrop
    >>> from py3plex.uncertainty.partition_reducers import (
    ...     NodeEntropyReducer, ConsensusReducer
    ... )
    >>> 
    >>> plan = UQPlan(
    ...     base_callable=lambda net, rng: my_community_detection(net, seed=int(rng.integers(0, 2**31))),
    ...     strategy="perturbation",
    ...     noise_model=EdgeDrop(p=0.1),
    ...     n_samples=100,
    ...     seed=42,
    ...     reducers=[
    ...         NodeEntropyReducer(n_nodes=network.number_of_nodes()),
    ...         ConsensusReducer(n_nodes=network.number_of_nodes())
    ...     ],
    ...     storage_mode="sketch"
    ... )
    >>> 
    >>> result = run_uq(plan, network)
    >>> print(result.reducer_outputs.keys())
    """
    # Step 1: Initialize master RNG from seed
    master_rng = np.random.default_rng(plan.seed)
    
    # Initialize storage for samples if requested
    samples: Optional[List[Any]] = None
    if plan.storage_mode == "samples":
        samples = []
    
    # Step 2: Execute n_samples iterations
    for i in range(plan.n_samples):
        # Step 2a: Derive per-sample RNG
        # Use master RNG to generate a seed for this sample
        sample_seed = int(master_rng.integers(0, 2**31))
        sample_rng = np.random.default_rng(sample_seed)
        
        # Step 2b: Apply noise model
        if plan.noise_model is not None:
            # Use a seed derived from the sample RNG for noise model
            noise_seed = int(sample_rng.integers(0, 2**31))
            net_i = plan.noise_model.apply(network, seed=noise_seed)
        else:
            # No noise model - use original network directly (no copy needed)
            net_i = network
        
        # Step 2c: Call base_callable with perturbed network and RNG
        sample_output = plan.base_callable(net_i, sample_rng)
        
        # Step 2d: Pass output to all reducers
        for reducer in plan.reducers:
            reducer.update(sample_output)
        
        # Store sample if requested
        if samples is not None:
            samples.append(sample_output)
    
    # Step 3: Finalize all reducers
    reducer_outputs = {}
    for reducer in plan.reducers:
        reducer_name = reducer.__class__.__name__
        reducer_outputs[reducer_name] = reducer.finalize()
    
    # Step 4: Assemble UQResult
    result = UQResult(
        n_samples=plan.n_samples,
        reducer_outputs=reducer_outputs,
        samples=samples,
    )
    
    # Step 5: Attach centralized provenance
    result.provenance = {
        "randomness": {
            "seed": plan.seed,
            "n_samples": plan.n_samples,
            "strategy": plan.strategy,
            "noise_model": plan.noise_model.to_dict() if plan.noise_model else None,
        },
        "execution": {
            "storage_mode": plan.storage_mode,
            "backend": plan.backend,
            "reducers": [r.__class__.__name__ for r in plan.reducers],
        },
    }
    
    return result
