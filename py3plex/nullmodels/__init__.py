"""Null model generation for multilayer networks.

This module provides functionality for generating randomized versions of
multilayer networks for statistical testing and hypothesis evaluation.

Example Usage:
    >>> from py3plex.nullmodels import generate_null_model, configuration_model
    >>> 
    >>> result = generate_null_model(network, model="configuration", samples=100)
    >>> for sample in result.samples:
    ...     # Analyze randomized network
    ...     pass
"""

from .models import (
    configuration_model,
    erdos_renyi_model,
    layer_shuffle_model,
    edge_swap_model,
    ModelRegistry,
    model_registry,
)
from .result import NullModelResult
from .executor import generate_null_model, execute_nullmodel_stmt

__all__ = [
    "generate_null_model",
    "execute_nullmodel_stmt",
    "configuration_model",
    "erdos_renyi_model",
    "layer_shuffle_model",
    "edge_swap_model",
    "NullModelResult",
    "ModelRegistry",
    "model_registry",
]
