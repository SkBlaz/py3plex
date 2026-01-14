"""Multilayer-specific community quality metrics.

This module implements quality metrics designed specifically for evaluating
community detection in multilayer networks. These metrics are intended to
serve as guardrails against degenerate partitions.

Metrics:
- replica_consistency: Measures whether replicas of the same node across
  layers are assigned to the same community (multilayer coherence)
- layer_entropy: Measures the balance of community sizes within each layer,
  averaged across layers (degeneracy guardrail)
"""

from __future__ import annotations

import math
import warnings
from collections import defaultdict
from typing import Any, Dict, Iterable, List, Optional, Tuple

import numpy as np


def iter_layered_assignments(
    partition: Dict[Any, int],
    network: Any
) -> Iterable[Tuple[Any, Any, int]]:
    """Iterate over layered node assignments from partition.
    
    This adapter converts various partition formats into a normalized stream
    of (node_id, layer, community_id) tuples for metric computation.
    
    Args:
        partition: Partition dict mapping nodes to community IDs.
            Expected format: {(node_id, layer): community_id} or
            {node_id: community_id} for single-layer networks.
        network: Multilayer network object
    
    Yields:
        Tuple of (node_id, layer, community_id)
    
    Examples:
        >>> partition = {('A', 'social'): 0, ('A', 'work'): 0, ('B', 'social'): 1}
        >>> for node_id, layer, comm_id in iter_layered_assignments(partition, net):
        ...     print(f"Node {node_id} in layer {layer} → community {comm_id}")
    """
    for node, comm_id in partition.items():
        if isinstance(node, tuple) and len(node) >= 2:
            # Format: (node_id, layer)
            node_id, layer = node[0], node[1]
            yield (node_id, layer, comm_id)
        else:
            # Single-layer or node without explicit layer
            # Try to extract layer info from network
            yield (node, None, comm_id)


def replica_consistency(
    partition: Dict[Any, int],
    network: Any,
    *,
    mode: str = "node_match",
    layers: Optional[List[str]] = None
) -> float:
    """Compute replica consistency: coherence of node assignments across layers.
    
    Measures whether replicas of the same node in different layers are assigned
    to the same community. This is a multilayer-specific quality metric that
    detects inconsistent partitions where a node's identity is split across
    layers.
    
    Formula:
        For each node v with replicas in L_v layers (|L_v| ≥ 2):
        
        RC(v) = (2 / (|L_v| * (|L_v| - 1))) * Σ_{i<j} 1[c(v,ℓ_i) = c(v,ℓ_j)]
        
        RC = (1 / |{v: |L_v| ≥ 2}|) * Σ_v RC(v)
    
    Efficient implementation uses count-based formula:
        For each node v, count label frequencies across layers: n_1, n_2, ...
        Agreement pairs = Σ_k n_k*(n_k-1)/2
        Total pairs = |L_v|*(|L_v|-1)/2
        RC(v) = agreement_pairs / total_pairs
    
    Args:
        partition: Partition dict mapping (node_id, layer) to community_id
        network: Multilayer network
        mode: Consistency mode (default: "node_match")
            - "node_match": Compare community labels directly (label-permutation invariant)
        layers: Optional list of layers to consider (default: all layers)
    
    Returns:
        Replica consistency in [0, 1]:
            - 1.0: All replicas of each node have same community
            - 0.0: No agreement (random assignment)
            - NaN: No nodes with replicas in ≥2 layers
    
    Raises:
        ValueError: If mode is invalid
    
    Examples:
        >>> # Perfect consistency
        >>> partition = {('A', 'social'): 0, ('A', 'work'): 0}
        >>> rc = replica_consistency(partition, net)
        >>> assert rc == 1.0
        
        >>> # No consistency
        >>> partition = {('A', 'social'): 0, ('A', 'work'): 1}
        >>> rc = replica_consistency(partition, net)
        >>> assert rc == 0.0
    
    Notes:
        - Metric is label-permutation invariant (only compares within-node labels)
        - Nodes appearing in single layer only are skipped
        - If no eligible nodes found, returns 0.0 with warning
        - Complexity: O(Σ_v |L_v|^2) but efficient with count-based implementation
    """
    if mode not in ("node_match",):
        raise ValueError(f"Invalid mode '{mode}'. Supported: 'node_match'")
    
    # Group assignments by (node_id, layer) → community_id
    node_layers: Dict[Any, Dict[Any, int]] = defaultdict(dict)
    
    for node_id, layer, comm_id in iter_layered_assignments(partition, network):
        if layer is None:
            # Skip nodes without layer information
            continue
        
        if layers is not None and layer not in layers:
            # Skip layers not in filter
            continue
        
        node_layers[node_id][layer] = comm_id
    
    # Compute RC for each node with replicas in ≥2 layers
    node_rcs = []
    
    for node_id, layer_comms in node_layers.items():
        n_layers = len(layer_comms)
        
        if n_layers < 2:
            # Skip nodes in single layer
            continue
        
        # Count label frequencies using efficient formula
        # For labels [0, 0, 1, 0]: counts = {0: 3, 1: 1}
        # Agreement pairs = 3*(3-1)/2 + 1*(1-1)/2 = 3
        # Total pairs = 4*(4-1)/2 = 6
        # RC = 3/6 = 0.5
        
        label_counts = defaultdict(int)
        for comm_id in layer_comms.values():
            label_counts[comm_id] += 1
        
        # Compute agreement pairs
        agreement_pairs = sum(
            count * (count - 1) / 2
            for count in label_counts.values()
        )
        
        # Compute total pairs
        total_pairs = n_layers * (n_layers - 1) / 2
        
        # Node RC
        if total_pairs > 0:
            node_rc = agreement_pairs / total_pairs
            node_rcs.append(node_rc)
    
    # Aggregate
    if not node_rcs:
        warnings.warn(
            "No nodes with replicas in ≥2 layers found. "
            "Returning RC=0.0",
            stacklevel=2
        )
        return 0.0
    
    return float(np.mean(node_rcs))


def layer_entropy(
    partition: Dict[Any, int],
    network: Any,
    *,
    layers: Optional[List[str]] = None,
    clip: Tuple[float, float] = (0.1, 0.9),
    base: str = "e"
) -> float:
    """Compute layer entropy: normalized entropy of community sizes per layer.
    
    Measures the balance of community sizes within each layer, averaged across
    layers. Serves as a guardrail against degenerate partitions (e.g., giant
    clusters or extreme fragmentation).
    
    Formula:
        For each layer ℓ:
            Let p_i^ℓ = |community_i in layer ℓ| / |V_ℓ|
            If |C_ℓ| ≤ 1: H_ℓ = 0.0
            Else: H_ℓ = -Σ_i p_i^ℓ log(p_i^ℓ) / log(|C_ℓ|)
        
        H = mean_ℓ(H_ℓ)
        H_clipped = clip(H, lo, hi)
    
    Args:
        partition: Partition dict mapping (node_id, layer) to community_id
        network: Multilayer network
        layers: Optional list of layers to consider (default: all layers)
        clip: Tuple of (min, max) bounds for final entropy (default: (0.1, 0.9))
            Prevents extreme fragmentation from being rewarded
        base: Logarithm base (default: "e" for natural log)
            Options: "e", "2", "10"
    
    Returns:
        Layer entropy in [clip[0], clip[1]]:
            - 1.0: Perfectly balanced communities in all layers
            - 0.0: Single community per layer (degenerate)
            - Values clipped to [clip[0], clip[1]] by default
    
    Raises:
        ValueError: If base is invalid
    
    Examples:
        >>> # Balanced partition (2 equal communities per layer)
        >>> partition = {
        ...     ('A', 'social'): 0, ('B', 'social'): 1,
        ...     ('A', 'work'): 0, ('B', 'work'): 1
        ... }
        >>> entropy = layer_entropy(partition, net)
        >>> assert 0.9 <= entropy <= 1.0  # High entropy (balanced)
        
        >>> # Giant cluster (one community per layer)
        >>> partition = {
        ...     ('A', 'social'): 0, ('B', 'social'): 0,
        ...     ('A', 'work'): 0, ('B', 'work'): 0
        ... }
        >>> entropy = layer_entropy(partition, net)
        >>> assert entropy == 0.1  # Clipped to minimum
    
    Notes:
        - Entropy is normalized by log(|C_ℓ|) to be in [0, 1]
        - Clipping prevents extreme values from dominating
        - Layers with 0 nodes are skipped with warning
        - Complexity: O(|E|) where E is edges/assignments
    """
    if base not in ("e", "2", "10"):
        raise ValueError(f"Invalid base '{base}'. Supported: 'e', '2', '10'")
    
    # Select log function
    if base == "e":
        log_fn = math.log
    elif base == "2":
        log_fn = math.log2
    else:  # base == "10"
        log_fn = math.log10
    
    # Group assignments by layer → community_id → count
    layer_comms: Dict[Any, Dict[int, int]] = defaultdict(lambda: defaultdict(int))
    
    for node_id, layer, comm_id in iter_layered_assignments(partition, network):
        if layer is None:
            # Skip nodes without layer information
            continue
        
        if layers is not None and layer not in layers:
            # Skip layers not in filter
            continue
        
        layer_comms[layer][comm_id] += 1
    
    # Compute entropy for each layer
    layer_entropies = []
    
    for layer, comm_counts in layer_comms.items():
        n_nodes_in_layer = sum(comm_counts.values())
        n_communities = len(comm_counts)
        
        if n_nodes_in_layer == 0:
            warnings.warn(
                f"Layer '{layer}' has 0 nodes. Skipping.",
                stacklevel=2
            )
            continue
        
        if n_communities <= 1:
            # Single community or empty layer → entropy = 0
            layer_entropies.append(0.0)
            continue
        
        # Compute normalized entropy
        # H = -Σ p_i log(p_i) / log(K)
        probs = np.array(list(comm_counts.values())) / n_nodes_in_layer
        
        # Shannon entropy
        # Add epsilon to avoid log(0)
        epsilon = 1e-10
        entropy = -np.sum(probs * np.log(probs + epsilon))
        
        # Convert to specified base
        if base == "2":
            entropy = entropy / math.log(2)
        elif base == "10":
            entropy = entropy / math.log(10)
        # else: base == "e", no conversion needed
        
        # Normalize by max entropy (log(K))
        max_entropy = log_fn(n_communities)
        normalized_entropy = entropy / max_entropy if max_entropy > 0 else 0.0
        
        layer_entropies.append(normalized_entropy)
    
    # Aggregate across layers
    if not layer_entropies:
        warnings.warn(
            "No valid layers found for entropy computation. "
            "Returning H=0.0",
            stacklevel=2
        )
        return 0.0
    
    mean_entropy = float(np.mean(layer_entropies))
    
    # Apply clipping
    clipped_entropy = np.clip(mean_entropy, clip[0], clip[1])
    
    return float(clipped_entropy)
