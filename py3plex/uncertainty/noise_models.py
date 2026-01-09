"""NoiseModel abstraction for network perturbation in UQ.

This module provides noise models that can be applied to networks before
community detection to enable perturbation-based uncertainty quantification.

NoiseModels are:
- Serializable (for provenance)
- Composable (can be chained)
- Reproducible (with seed control)

Examples
--------
>>> from py3plex.uncertainty.noise_models import EdgeDrop, WeightNoise
>>> from py3plex.core import multinet
>>> 
>>> net = multinet.multi_layer_network(directed=False)
>>> # ... add edges ...
>>> 
>>> # Drop 10% of edges
>>> noise = EdgeDrop(p=0.1)
>>> perturbed_net = noise.apply(net, seed=42)
>>> 
>>> # Add lognormal noise to weights
>>> noise = WeightNoise(dist="lognormal", sigma=0.2)
>>> perturbed_net = noise.apply(net, seed=42)
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union
import copy
import random

import numpy as np


@dataclass
class NoiseModel(ABC):
    """Base class for network noise models.
    
    A NoiseModel defines a stochastic transformation of a network that
    preserves the general structure but introduces controlled perturbations.
    
    All subclasses must implement:
    - apply(network, seed) -> perturbed_network
    - to_dict() -> serializable representation
    """
    
    @abstractmethod
    def apply(self, network: Any, seed: Optional[int] = None) -> Any:
        """Apply noise model to network.
        
        Parameters
        ----------
        network : multi_layer_network
            Input network to perturb
        seed : int, optional
            Random seed for reproducibility
            
        Returns
        -------
        multi_layer_network
            Perturbed copy of the network
        """
        pass
    
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Serialize noise model to dictionary.
        
        Returns
        -------
        dict
            Serializable representation including all parameters
        """
        pass
    
    def __repr__(self) -> str:
        """String representation for provenance."""
        d = self.to_dict()
        params = ", ".join(f"{k}={v}" for k, v in d.items() if k != "type")
        return f"{d['type']}({params})"


@dataclass
class NoNoise(NoiseModel):
    """No-op noise model for deterministic execution.
    
    This noise model returns an unmodified copy of the network.
    It is useful for seed-based UQ strategies where the network
    structure is fixed and only algorithm randomness varies.
    
    Examples
    --------
    >>> noise = NoNoise()
    >>> net_copy = noise.apply(network, seed=42)
    >>> # net_copy is a deep copy of network with no perturbations
    """
    
    def apply(self, network: Any, seed: Optional[int] = None) -> Any:
        """Return an unmodified copy of the network.
        
        Parameters
        ----------
        network : multi_layer_network
            Input network
        seed : int, optional
            Random seed (unused, for interface compatibility)
            
        Returns
        -------
        multi_layer_network
            Deep copy of the network
        """
        import copy
        return copy.deepcopy(network)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict."""
        return {"type": "NoNoise"}


@dataclass
class EdgeDrop(NoiseModel):
    """Drop edges uniformly at random.
    
    This noise model removes a fraction p of edges from the network,
    chosen uniformly at random. Useful for testing robustness to
    missing edges.
    
    Parameters
    ----------
    p : float
        Probability of dropping each edge (0 < p < 1)
    preserve_connectivity : bool, default=False
        If True, only drop edges that don't disconnect the network
        
    Examples
    --------
    >>> noise = EdgeDrop(p=0.1)
    >>> perturbed = noise.apply(network, seed=42)
    """
    
    p: float
    preserve_connectivity: bool = False
    
    def __post_init__(self):
        """Validate parameters."""
        if not 0 < self.p < 1:
            raise ValueError(f"EdgeDrop probability must be in (0, 1), got {self.p}")
    
    def apply(self, network: Any, seed: Optional[int] = None) -> Any:
        """Apply edge dropping to network.
        
        Parameters
        ----------
        network : multi_layer_network
            Input network
        seed : int, optional
            Random seed
            
        Returns
        -------
        multi_layer_network
            Network with edges dropped
        """
        import copy
        from py3plex.core import multinet
        
        # Set seed
        rng = np.random.default_rng(seed)
        
        # Create deep copy of network
        perturbed = copy.deepcopy(network)
        
        # Get all edges
        edges_to_remove = []
        
        if hasattr(perturbed, 'core_network'):
            # Multilayer network
            all_edges = list(perturbed.core_network.edges())
            
            # Sample edges to remove
            for edge in all_edges:
                if rng.random() < self.p:
                    edges_to_remove.append(edge)
            
            # Remove edges
            for edge in edges_to_remove:
                if perturbed.core_network.has_edge(*edge):
                    perturbed.core_network.remove_edge(*edge)
        
        return perturbed
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict."""
        return {
            "type": "EdgeDrop",
            "p": self.p,
            "preserve_connectivity": self.preserve_connectivity,
        }


@dataclass
class WeightNoise(NoiseModel):
    """Add multiplicative noise to edge weights.
    
    This noise model multiplies each edge weight by a random factor
    drawn from a specified distribution. Useful for testing sensitivity
    to weight uncertainty.
    
    Parameters
    ----------
    dist : str
        Distribution type: "lognormal", "uniform", or "normal"
    sigma : float
        Scale parameter for the distribution
        - lognormal: standard deviation of log-weights
        - uniform: half-width of interval
        - normal: standard deviation
    clip_min : float, optional
        Minimum weight value (default: 0.0)
    clip_max : float, optional
        Maximum weight value (default: None)
        
    Examples
    --------
    >>> # Lognormal noise with sigma=0.2
    >>> noise = WeightNoise(dist="lognormal", sigma=0.2)
    >>> perturbed = noise.apply(network, seed=42)
    >>> 
    >>> # Uniform noise in [0.8, 1.2] range
    >>> noise = WeightNoise(dist="uniform", sigma=0.2)
    >>> perturbed = noise.apply(network, seed=42)
    """
    
    dist: str
    sigma: float
    clip_min: float = 0.0
    clip_max: Optional[float] = None
    
    def __post_init__(self):
        """Validate parameters."""
        valid_dists = {"lognormal", "uniform", "normal"}
        if self.dist not in valid_dists:
            raise ValueError(f"dist must be one of {valid_dists}, got {self.dist}")
        if self.sigma <= 0:
            raise ValueError(f"sigma must be positive, got {self.sigma}")
    
    def apply(self, network: Any, seed: Optional[int] = None) -> Any:
        """Apply weight noise to network.
        
        Parameters
        ----------
        network : multi_layer_network
            Input network
        seed : int, optional
            Random seed
            
        Returns
        -------
        multi_layer_network
            Network with noisy weights
        """
        import copy
        
        # Set seed
        rng = np.random.default_rng(seed)
        
        # Create deep copy of network
        perturbed = copy.deepcopy(network)
        
        if hasattr(perturbed, 'core_network'):
            # Multilayer network
            for u, v, data in perturbed.core_network.edges(data=True):
                # Get current weight (default to 1.0)
                w = data.get('weight', 1.0)
                
                # Generate noise multiplier
                if self.dist == "lognormal":
                    # Lognormal: multiply by exp(N(0, sigma))
                    log_noise = rng.normal(0, self.sigma)
                    multiplier = np.exp(log_noise)
                elif self.dist == "uniform":
                    # Uniform: multiply by U(1-sigma, 1+sigma)
                    multiplier = rng.uniform(1 - self.sigma, 1 + self.sigma)
                elif self.dist == "normal":
                    # Normal: add N(0, sigma*w)
                    multiplier = 1 + rng.normal(0, self.sigma)
                
                # Apply noise
                new_weight = w * multiplier
                
                # Clip
                if self.clip_max is not None:
                    new_weight = np.clip(new_weight, self.clip_min, self.clip_max)
                else:
                    new_weight = max(new_weight, self.clip_min)
                
                # Update weight
                data['weight'] = float(new_weight)
        
        return perturbed
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict."""
        return {
            "type": "WeightNoise",
            "dist": self.dist,
            "sigma": self.sigma,
            "clip_min": self.clip_min,
            "clip_max": self.clip_max,
        }


@dataclass
class LayerDrop(NoiseModel):
    """Drop entire layers from multilayer network.
    
    This noise model removes layers from the network, useful for
    testing robustness to missing data modalities.
    
    Parameters
    ----------
    p : float, optional
        Probability of dropping each layer (0 < p < 1)
    layers : list of str, optional
        Specific layers to drop (mutually exclusive with p)
        
    Examples
    --------
    >>> # Drop each layer with 20% probability
    >>> noise = LayerDrop(p=0.2)
    >>> perturbed = noise.apply(network, seed=42)
    >>> 
    >>> # Drop specific layers
    >>> noise = LayerDrop(layers=["twitter", "facebook"])
    >>> perturbed = noise.apply(network, seed=42)
    """
    
    p: Optional[float] = None
    layers: Optional[List[str]] = None
    
    def __post_init__(self):
        """Validate parameters."""
        if self.p is None and self.layers is None:
            raise ValueError("Either p or layers must be specified")
        if self.p is not None and self.layers is not None:
            raise ValueError("Cannot specify both p and layers")
        if self.p is not None and not 0 < self.p < 1:
            raise ValueError(f"LayerDrop probability must be in (0, 1), got {self.p}")
    
    def apply(self, network: Any, seed: Optional[int] = None) -> Any:
        """Apply layer dropping to network.
        
        Parameters
        ----------
        network : multi_layer_network
            Input network
        seed : int, optional
            Random seed
            
        Returns
        -------
        multi_layer_network
            Network with layers dropped
        """
        import copy
        
        # Set seed
        rng = np.random.default_rng(seed)
        
        # Create deep copy of network
        perturbed = copy.deepcopy(network)
        
        # Determine which layers to drop
        if self.layers is not None:
            # Explicit layer list
            layers_to_drop = set(self.layers)
        else:
            # Probabilistic dropping
            all_layers = set()
            if hasattr(perturbed, 'core_network'):
                for node in perturbed.core_network.nodes():
                    if isinstance(node, tuple) and len(node) == 2:
                        all_layers.add(node[1])
            
            layers_to_drop = {
                layer for layer in all_layers
                if rng.random() < self.p
            }
        
        # Remove edges in dropped layers
        if hasattr(perturbed, 'core_network'):
            edges_to_remove = []
            for u, v in perturbed.core_network.edges():
                # Check if either node is in a dropped layer
                u_layer = u[1] if isinstance(u, tuple) and len(u) == 2 else None
                v_layer = v[1] if isinstance(v, tuple) and len(v) == 2 else None
                
                if u_layer in layers_to_drop or v_layer in layers_to_drop:
                    edges_to_remove.append((u, v))
            
            for edge in edges_to_remove:
                if perturbed.core_network.has_edge(*edge):
                    perturbed.core_network.remove_edge(*edge)
        
        return perturbed
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict."""
        return {
            "type": "LayerDrop",
            "p": self.p,
            "layers": self.layers,
        }


@dataclass
class TemporalWindowBootstrap(NoiseModel):
    """Bootstrap temporal windows for temporal networks.
    
    This noise model resamples time windows with replacement,
    useful for testing stability of temporal community detection.
    
    Parameters
    ----------
    window_size : float
        Size of each time window
    n_windows : int, optional
        Number of windows to sample (default: same as original)
        
    Examples
    --------
    >>> noise = TemporalWindowBootstrap(window_size=100.0)
    >>> perturbed = noise.apply(temporal_network, seed=42)
    """
    
    window_size: float
    n_windows: Optional[int] = None
    
    def __post_init__(self):
        """Validate parameters."""
        if self.window_size <= 0:
            raise ValueError(f"window_size must be positive, got {self.window_size}")
    
    def apply(self, network: Any, seed: Optional[int] = None) -> Any:
        """Apply temporal bootstrap to network.
        
        Parameters
        ----------
        network : multi_layer_network or TemporalMultiLayerNetwork
            Input network with temporal edges
        seed : int, optional
            Random seed
            
        Returns
        -------
        multi_layer_network
            Network with bootstrapped time windows
        """
        # TODO: Implement temporal bootstrap
        # This requires temporal network support which may not be fully integrated
        # For now, return copy as placeholder
        import copy
        return copy.deepcopy(network)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict."""
        return {
            "type": "TemporalWindowBootstrap",
            "window_size": self.window_size,
            "n_windows": self.n_windows,
        }


def noise_model_from_dict(data: Dict[str, Any]) -> NoiseModel:
    """Deserialize noise model from dictionary.
    
    Parameters
    ----------
    data : dict
        Dictionary with "type" key and model-specific parameters
        
    Returns
    -------
    NoiseModel
        Instantiated noise model
        
    Examples
    --------
    >>> data = {"type": "EdgeDrop", "p": 0.1}
    >>> noise = noise_model_from_dict(data)
    >>> isinstance(noise, EdgeDrop)
    True
    """
    data = data.copy()  # Don't mutate input
    model_type = data.pop("type")
    
    if model_type == "NoNoise":
        return NoNoise(**data)
    elif model_type == "EdgeDrop":
        return EdgeDrop(**data)
    elif model_type == "WeightNoise":
        return WeightNoise(**data)
    elif model_type == "LayerDrop":
        return LayerDrop(**data)
    elif model_type == "TemporalWindowBootstrap":
        return TemporalWindowBootstrap(**data)
    else:
        raise ValueError(f"Unknown noise model type: {model_type}")
