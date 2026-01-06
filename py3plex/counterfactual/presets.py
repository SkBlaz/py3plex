"""User-friendly preset configurations for counterfactual analysis.

This module provides dummy-proof preset configurations that users can
apply without needing to understand intervention details.
"""

from typing import Dict, Optional
from .spec import (
    InterventionSpec,
    RemoveEdgesSpec,
    RewireDegreePreservingSpec,
    ShuffleWeightsSpec,
)


# Preset names
PRESET_QUICK = "quick"
PRESET_DEGREE_SAFE = "degree_safe"
PRESET_LAYER_SAFE = "layer_safe"
PRESET_WEIGHT_ONLY = "weight_only"
PRESET_TARGETED = "targeted"


def get_preset(name: str, 
              strength: str = "medium",
              targets: Optional[any] = None) -> InterventionSpec:
    """Get a preset intervention specification.
    
    Args:
        name: Preset name (quick, degree_safe, layer_safe, weight_only, targeted)
        strength: Intervention strength (light, medium, heavy)
        targets: Optional target specification for targeted presets
        
    Returns:
        InterventionSpec instance
        
    Raises:
        ValueError: If preset name or strength is invalid
    """
    if name not in _PRESET_REGISTRY:
        available = ", ".join(_PRESET_REGISTRY.keys())
        raise ValueError(f"Unknown preset '{name}'. Available: {available}")
    
    if strength not in ("light", "medium", "heavy"):
        raise ValueError(f"Strength must be 'light', 'medium', or 'heavy', got '{strength}'")
    
    return _PRESET_REGISTRY[name](strength, targets)


def list_presets() -> Dict[str, str]:
    """List available presets with descriptions.
    
    Returns:
        Dictionary mapping preset names to descriptions
    """
    return {
        PRESET_QUICK: "Quick edge removal (fast, minimal perturbation)",
        PRESET_DEGREE_SAFE: "Degree-preserving rewiring + mild edge removal (DEFAULT)",
        PRESET_LAYER_SAFE: "Preserve per-layer edge counts",
        PRESET_WEIGHT_ONLY: "Shuffle edge weights only (structure preserved)",
        PRESET_TARGETED: "Perturb around selected nodes/layers",
    }


def _quick_preset(strength: str, targets: Optional[any] = None) -> InterventionSpec:
    """Quick preset - minimal edge removal.
    
    Fast and conservative, good for initial exploration.
    """
    proportions = {
        "light": 0.02,    # 2% of edges
        "medium": 0.05,   # 5% of edges
        "heavy": 0.10,    # 10% of edges
    }
    
    return RemoveEdgesSpec(
        proportion=proportions[strength],
        on=targets,
        mode="random"
    )


def _degree_safe_preset(strength: str, targets: Optional[any] = None) -> InterventionSpec:
    """Degree-safe preset - degree-preserving rewiring.
    
    This is the DEFAULT preset. It preserves node degrees while
    testing sensitivity to edge rewiring. Good for most analyses.
    """
    # For degree-preserving, we use number of swaps
    # Rough heuristic: light = 10% of edges, medium = 25%, heavy = 50%
    # The actual number will depend on network size
    
    # Note: We'll need to know the network size to compute n_swaps
    # For now, we return a factory that will be resolved later
    # This is a simplification - in practice, the engine should handle this
    
    swaps_multiplier = {
        "light": 0.10,
        "medium": 0.25,
        "heavy": 0.50,
    }
    
    # For now, use a heuristic default based on typical network sizes
    # The engine should adjust this based on actual network size
    n_swaps_default = {
        "light": 50,
        "medium": 200,
        "heavy": 500,
    }
    
    return RewireDegreePreservingSpec(
        n_swaps=n_swaps_default[strength],
        on=targets
    )


def _layer_safe_preset(strength: str, targets: Optional[any] = None) -> InterventionSpec:
    """Layer-safe preset - preserve per-layer edge counts.
    
    Shuffles edges within each layer separately, preserving
    layer-specific statistics.
    """
    # For layer-safe, we'll do weight shuffling per layer
    # This is a simplification - could also do layer-specific rewiring
    
    return ShuffleWeightsSpec(
        on=targets,
        preserve_layer=True
    )


def _weight_only_preset(strength: str, targets: Optional[any] = None) -> InterventionSpec:
    """Weight-only preset - shuffle weights without changing structure.
    
    Tests sensitivity to edge weights while keeping topology fixed.
    """
    return ShuffleWeightsSpec(
        on=targets,
        preserve_layer=True  # Shuffle within layers
    )


def _targeted_preset(strength: str, targets: Optional[any] = None) -> InterventionSpec:
    """Targeted preset - perturb around selected nodes/layers.
    
    Removes edges with highest weights (or random if targets specified).
    Requires targets to be specified.
    """
    if targets is None:
        # Default to removing high-weight edges
        mode = "targeted"
    else:
        # If targets specified, remove random edges from targets
        mode = "random"
    
    proportions = {
        "light": 0.05,
        "medium": 0.15,
        "heavy": 0.30,
    }
    
    return RemoveEdgesSpec(
        proportion=proportions[strength],
        on=targets,
        mode=mode
    )


# Registry mapping preset names to factory functions
_PRESET_REGISTRY = {
    PRESET_QUICK: _quick_preset,
    PRESET_DEGREE_SAFE: _degree_safe_preset,
    PRESET_LAYER_SAFE: _layer_safe_preset,
    PRESET_WEIGHT_ONLY: _weight_only_preset,
    PRESET_TARGETED: _targeted_preset,
}


def get_default_preset(strength: str = "medium") -> InterventionSpec:
    """Get the default preset (degree_safe).
    
    Args:
        strength: Intervention strength (light, medium, heavy)
        
    Returns:
        Default InterventionSpec
    """
    return get_preset(PRESET_DEGREE_SAFE, strength=strength)
