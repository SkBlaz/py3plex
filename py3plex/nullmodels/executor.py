"""Executor for null model generation operations.

This module provides the main execution function for generating null models.
"""

from typing import Any, Dict, List, Optional

from .models import model_registry
from .result import NullModelResult


def generate_null_model(
    network: Any,
    model: str = "configuration",
    num_samples: int = 1,
    seed: Optional[int] = None,
    layers: Optional[List[str]] = None,
    **params,
) -> NullModelResult:
    """Generate null model samples from a multilayer network.
    
    Args:
        network: Multilayer network to randomize
        model: Null model type (default: "configuration")
        num_samples: Number of samples to generate
        seed: Optional random seed
        layers: Optional list of layers to consider
        **params: Additional model parameters
        
    Returns:
        NullModelResult with generated samples
        
    Raises:
        ValueError: If model is not registered
    """
    import random
    
    # Get the model function
    model_fn = model_registry.get(model)
    
    # Set initial seed
    if seed is not None:
        random.seed(seed)
    
    # Generate samples
    samples = []
    for i in range(num_samples):
        # Use different seed for each sample
        sample_seed = seed + i if seed is not None else None
        sample = model_fn(network, seed=sample_seed, **params)
        samples.append(sample)
    
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
