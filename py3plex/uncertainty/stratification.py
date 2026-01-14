"""Stratification support for variance-reduced uncertainty quantification.

This module implements stratified resampling strategies that preserve key
network structural properties during perturbation, reducing estimator variance.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import networkx as nx

from py3plex.core import multinet


@dataclass
class StratificationSpec:
    """Configuration for stratified resampling.
    
    Attributes
    ----------
    strata : List[str]
        List of stratification dimensions to apply.
        Supported: "degree", "layer", "layer_pair", "weight"
    bins : Dict[str, int]
        Number of bins for each continuous dimension.
        E.g., {"degree": 5, "weight": 3}
    seed : Optional[int]
        Random seed for reproducibility.
    """
    strata: List[str] = field(default_factory=list)
    bins: Dict[str, int] = field(default_factory=dict)
    seed: Optional[int] = None
    
    def __post_init__(self):
        """Validate stratification specification."""
        valid_strata = {"degree", "layer", "layer_pair", "weight"}
        for s in self.strata:
            if s not in valid_strata:
                raise ValueError(
                    f"Unknown stratification dimension: {s}. "
                    f"Valid: {valid_strata}"
                )
        
        # Set default bins
        for s in self.strata:
            if s in ("degree", "weight") and s not in self.bins:
                self.bins[s] = 5  # Conservative default
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "strata": self.strata,
            "bins": self.bins,
            "seed": self.seed,
        }


def auto_select_strata(target: str) -> List[str]:
    """Automatically select stratification dimensions based on query target.
    
    Parameters
    ----------
    target : str
        Query target type ("nodes" or "edges")
    
    Returns
    -------
    List[str]
        Recommended stratification dimensions
    """
    if target == "nodes":
        return ["degree"]
    elif target == "edges":
        return ["layer_pair"]
    else:
        return []


def stratify_nodes_by_degree(
    network: multinet.multi_layer_network,
    n_bins: int = 5,
) -> Dict[int, List[Any]]:
    """Stratify nodes by degree quantiles.
    
    Parameters
    ----------
    network : multi_layer_network
        The network to stratify.
    n_bins : int
        Number of degree bins (quantiles).
    
    Returns
    -------
    Dict[int, List[Any]]
        Mapping from bin index to list of nodes.
    """
    # Handle empty network or network without core_network
    if network.core_network is None or network.core_network.number_of_nodes() == 0:
        return {0: []}
    
    # Get degrees
    degrees = dict(network.core_network.degree())
    if not degrees:
        return {0: []}
    
    nodes = list(degrees.keys())
    degree_vals = np.array([degrees[n] for n in nodes])
    
    # Create bins using quantiles
    if len(set(degree_vals)) < n_bins:
        # Few unique values - use value-based bins
        unique_vals = sorted(set(degree_vals))
        bins_edges = unique_vals + [unique_vals[-1] + 1]
        bin_indices = np.digitize(degree_vals, bins_edges[:-1], right=False)
    else:
        # Use quantile-based bins
        quantiles = np.linspace(0, 100, n_bins + 1)
        bin_edges = np.percentile(degree_vals, quantiles)
        bin_edges[-1] += 1  # Include max value
        bin_indices = np.digitize(degree_vals, bin_edges[:-1], right=False)
    
    # Group nodes by bin
    strata: Dict[int, List[Any]] = {}
    for node, bin_idx in zip(nodes, bin_indices):
        if bin_idx not in strata:
            strata[bin_idx] = []
        strata[bin_idx].append(node)
    
    return strata


def stratify_nodes_by_layer(
    network: multinet.multi_layer_network,
) -> Dict[str, List[Any]]:
    """Stratify nodes by layer membership.
    
    Parameters
    ----------
    network : multi_layer_network
        The network to stratify.
    
    Returns
    -------
    Dict[str, List[Any]]
        Mapping from layer name to list of nodes.
    """
    from collections import defaultdict
    
    strata: Dict[str, List[Any]] = defaultdict(list)
    node_layers: Dict[Any, set] = defaultdict(set)
    
    # First pass: collect all layers for each node
    for edge in network.core_network.edges(data=True):
        src, dst, data = edge
        
        # Check source_type and target_type
        if 'source_type' in data:
            node_layers[src].add(data['source_type'])
        if 'target_type' in data:
            node_layers[dst].add(data['target_type'])
        # Also check 'type' field for backward compatibility
        if 'type' in data:
            node_layers[src].add(data['type'])
            node_layers[dst].add(data['type'])
    
    # Second pass: add each node to its layer strata (once per layer)
    for node, layers in node_layers.items():
        for layer in layers:
            strata[layer].append(node)
    
    return dict(strata)


def stratify_edges_by_layer_pair(
    network: multinet.multi_layer_network,
) -> Dict[Tuple[str, str], List[Tuple[Any, Any]]]:
    """Stratify edges by source-target layer pair.
    
    Parameters
    ----------
    network : multi_layer_network
        The network to stratify.
    
    Returns
    -------
    Dict[Tuple[str, str], List[Tuple[Any, Any]]]
        Mapping from (src_layer, dst_layer) to list of (src, dst) edges.
    """
    strata: Dict[Tuple[str, str], List[Tuple[Any, Any]]] = {}
    
    for src, dst, data in network.core_network.edges(data=True):
        src_layer = data.get('source_type', 'default')
        dst_layer = data.get('target_type', 'default')
        
        layer_pair = (src_layer, dst_layer)
        if layer_pair not in strata:
            strata[layer_pair] = []
        strata[layer_pair].append((src, dst))
    
    return strata


def stratify_edges_by_weight(
    network: multinet.multi_layer_network,
    n_bins: int = 3,
) -> Dict[int, List[Tuple[Any, Any]]]:
    """Stratify edges by weight quantiles.
    
    Parameters
    ----------
    network : multi_layer_network
        The network to stratify.
    n_bins : int
        Number of weight bins (quantiles).
    
    Returns
    -------
    Dict[int, List[Tuple[Any, Any]]]
        Mapping from bin index to list of (src, dst) edges.
    """
    # Collect edges and weights
    edges = []
    weights = []
    
    for src, dst, data in network.core_network.edges(data=True):
        edges.append((src, dst))
        weights.append(data.get('weight', 1.0))
    
    if not edges:
        return {0: []}
    
    weights_arr = np.array(weights)
    
    # Create bins using quantiles
    if len(set(weights)) < n_bins:
        # Few unique values - use value-based bins
        unique_vals = sorted(set(weights))
        bins_edges = unique_vals + [unique_vals[-1] + 1]
        bin_indices = np.digitize(weights_arr, bins_edges[:-1], right=False)
    else:
        # Use quantile-based bins
        quantiles = np.linspace(0, 100, n_bins + 1)
        bin_edges = np.percentile(weights_arr, quantiles)
        bin_edges[-1] += 1  # Include max value
        bin_indices = np.digitize(weights_arr, bin_edges[:-1], right=False)
    
    # Group edges by bin
    strata: Dict[int, List[Tuple[Any, Any]]] = {}
    for edge, bin_idx in zip(edges, bin_indices):
        if bin_idx not in strata:
            strata[bin_idx] = []
        strata[bin_idx].append(edge)
    
    return strata


def compute_composite_strata(
    network: multinet.multi_layer_network,
    spec: StratificationSpec,
    target: str = "nodes",
) -> Dict[Tuple, List[Any]]:
    """Compute composite stratification by crossing multiple dimensions.
    
    Parameters
    ----------
    network : multi_layer_network
        The network to stratify.
    spec : StratificationSpec
        Stratification specification.
    target : str
        Target type ("nodes" or "edges")
    
    Returns
    -------
    Dict[Tuple, List[Any]]
        Mapping from composite stratum key to list of items.
    """
    if not spec.strata:
        # No stratification - return all items in one stratum
        if target == "nodes":
            items = list(network.get_nodes())
        else:
            items = [(s, d) for s, d, _ in network.core_network.edges(data=True)]
        return {(): items}
    
    # Compute individual stratifications
    individual_strata = {}
    
    if target == "nodes":
        if "degree" in spec.strata:
            individual_strata["degree"] = stratify_nodes_by_degree(
                network, spec.bins.get("degree", 5)
            )
        if "layer" in spec.strata:
            individual_strata["layer"] = stratify_nodes_by_layer(network)
    
    elif target == "edges":
        if "layer_pair" in spec.strata:
            individual_strata["layer_pair"] = stratify_edges_by_layer_pair(network)
        if "weight" in spec.strata:
            individual_strata["weight"] = stratify_edges_by_weight(
                network, spec.bins.get("weight", 3)
            )
    
    if not individual_strata:
        # No valid stratifications - return all items
        if target == "nodes":
            items = list(network.get_nodes())
        else:
            items = [(s, d) for s, d, _ in network.core_network.edges(data=True)]
        return {(): items}
    
    # Build composite strata by crossing dimensions
    # Start with first dimension
    first_dim = list(individual_strata.keys())[0]
    composite: Dict[Tuple, List[Any]] = {}
    
    for key, items in individual_strata[first_dim].items():
        composite[(key,)] = items.copy()
    
    # Cross with remaining dimensions
    for dim in list(individual_strata.keys())[1:]:
        new_composite: Dict[Tuple, List[Any]] = {}
        
        for comp_key, comp_items in composite.items():
            for dim_key, dim_items in individual_strata[dim].items():
                # Find intersection
                intersection = [item for item in comp_items if item in dim_items]
                if intersection:
                    new_key = comp_key + (dim_key,)
                    new_composite[new_key] = intersection
        
        composite = new_composite
    
    return composite


def compute_variance_reduction_ratio(
    baseline_std: np.ndarray,
    stratified_std: np.ndarray,
) -> float:
    """Compute variance reduction ratio.
    
    Parameters
    ----------
    baseline_std : np.ndarray
        Standard deviations from baseline (unstratified) estimation.
    stratified_std : np.ndarray
        Standard deviations from stratified estimation.
    
    Returns
    -------
    float
        Variance reduction ratio: (baseline_var - stratified_var) / baseline_var
        Values > 0 indicate variance reduction, < 0 indicate increase.
    """
    baseline_var = np.mean(baseline_std ** 2)
    stratified_var = np.mean(stratified_std ** 2)
    
    if baseline_var == 0:
        return 0.0
    
    return (baseline_var - stratified_var) / baseline_var
