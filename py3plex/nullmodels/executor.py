"""Executor for null model generation operations.

This module provides the main execution function for generating null models.
"""

from typing import Any, Dict, List, Optional

from .models import model_registry
from .result import NullModelResult
from py3plex._parallel import parallel_map, spawn_seeds
from py3plex import config


def _generate_single_sample(args):
    """Generate a single null model sample.
    
    This is a module-level function so it can be pickled for multiprocessing.
    
    Parameters
    ----------
    args : tuple
        Tuple of (network, model_fn, sample_seed, params)
    
    Returns
    -------
    Any
        Generated null model sample
    """
    network, model_fn, sample_seed, params = args
    return model_fn(network, seed=sample_seed, **params)


def generate_null_model(
    network: Any,
    model: str = "configuration",
    num_samples: int = 1,
    seed: Optional[int] = None,
    layers: Optional[List[str]] = None,
    n_jobs: Optional[int] = None,
    **params,
) -> NullModelResult:
    """Generate null model samples from a multilayer network.
    
    Args:
        network: Multilayer network to randomize
        model: Null model type (default: "configuration")
        num_samples: Number of samples to generate
        seed: Optional random seed
        layers: Optional list of layers to consider
        n_jobs: Number of parallel jobs (default: from config.DEFAULT_N_JOBS).
                If 1, runs serially. If >1, runs in parallel.
        **params: Additional model parameters
        
    Returns:
        NullModelResult with generated samples
        
    Raises:
        ValueError: If model is not registered
    """
    # Get the model function
    model_fn = model_registry.get(model)
    
    # Determine number of jobs
    if n_jobs is None:
        n_jobs = getattr(config, 'DEFAULT_N_JOBS', 1)
    
    # Generate child seeds for deterministic parallel execution
    child_seeds = spawn_seeds(seed, num_samples)
    
    # Prepare arguments for each sample
    # Note: we pass the network directly, which works for small networks
    # For very large networks, consider passing lightweight edge list instead
    sample_args = [
        (network, model_fn, child_seed, params)
        for child_seed in child_seeds
    ]
    
    # Generate samples in parallel or serial
    samples = parallel_map(
        _generate_single_sample,
        sample_args,
        n_jobs=n_jobs,
        backend=getattr(config, 'DEFAULT_PARALLEL_BACKEND', 'multiprocessing'),
    )
    
    # Build metadata
    meta = {
        "model": model,
        "layers": layers,
        "params": params,
    }
    
    return NullModelResult(
        model_type=model,
        samples=samples,
        seed=seed,
        meta=meta,
    )


def execute_nullmodel_stmt(
    network: Any,
    stmt: "NullModelStmt",
) -> NullModelResult:
    """Execute a NULLMODEL statement from the DSL.
    
    Args:
        network: Multilayer network to randomize
        stmt: NullModelStmt AST node
        
    Returns:
        NullModelResult with generated samples
    """
    # Get layers from layer expression
    layers = None
    if stmt.layer_expr:
        layers = stmt.layer_expr.get_layer_names()
    
    return generate_null_model(
        network=network,
        model=stmt.model_type,
        num_samples=stmt.num_samples,
        seed=stmt.seed,
        layers=layers,
        **stmt.params,
    )
