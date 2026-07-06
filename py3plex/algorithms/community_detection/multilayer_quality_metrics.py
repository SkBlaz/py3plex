"""Multilayer-specific community quality metrics.

This module implements quality metrics designed specifically for evaluating
community detection in multilayer networks. These metrics are intended to
serve as guardrails against degenerate partitions.

Metrics:
- replica_consistency: Measures whether replicas of the same node across
  layers are assigned to the same community (multilayer coherence)
- layer_entropy: Measures the balance of community sizes within each layer,
  averaged across layers (degeneracy guardrail)
- mdl_score: Minimum Description Length based on SBM two-part description
  length (lower is better)
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


def _mdl_single_layer(
    layer_partition: Dict[Any, Any],
    layer_edges: List[tuple],
    directed: bool = False,
) -> float:
    """Compute SBM two-part description length for a single flat graph layer.

    Args:
        layer_partition: Dict mapping node -> community_id for this layer only.
            Community ids need only be hashable (e.g. singleton sentinel
            objects for unassigned nodes are supported).
        layer_edges: List of (u, v) edge pairs within this layer.
        directed: Whether the underlying graph is directed. Controls the
            maximum-edge normalization for block pairs. Defaults to False
            (undirected), preserving backward-compatible behavior for callers
            that do not pass the flag.

    Returns:
        Description length in bits for this layer.
    """
    communities: Dict[Any, List[Any]] = defaultdict(list)
    for node, comm in layer_partition.items():
        communities[comm].append(node)

    k = len(communities)
    n = len(layer_partition)

    if k == 0 or n == 0:
        return 0.0

    # Count edges between/within each block pair. Community ids are only
    # required to be hashable (not orderable) -- singleton sentinel ids used
    # for unassigned nodes are plain objects, so pairs are keyed with a
    # frozenset rather than a min/max tuple.
    # Self-loops are skipped: they do not fit the n_r*(n_r-1) pair model
    edge_counts: Dict[frozenset, int] = defaultdict(int)
    for u, v in layer_edges:
        if u == v:
            continue
        r = layer_partition.get(u)
        s = layer_partition.get(v)
        if r is None or s is None:
            continue
        edge_counts[frozenset((r, s))] += 1

    # Part 1: model cost - n * log2(k) bits to encode node assignments
    model_cost = n * np.log2(k) if k > 1 else 0.0

    # Part 2: data cost - binary entropy per block pair. Block pairs with no
    # observed edges contribute exactly 0 (H(p=0) == 0), so it suffices to
    # iterate over the pairs that actually have edges rather than every pair
    # of communities. This keeps the cost O(|E|) instead of O(k^2), which
    # matters once unassigned nodes are represented as singleton communities
    # (k can then be as large as n).
    data_cost = 0.0
    for pair, e_rs in edge_counts.items():
        if len(pair) == 1:
            (r,) = pair
            s = r
        else:
            r, s = tuple(pair)
        n_r = len(communities[r])
        n_s = len(communities[s])

        # Maximum possible edges between blocks r and s.
        # Directed graphs allow both (u->v) and (v->u): the off-diagonal
        # capacity doubles and the on-diagonal uses n_r*(n_r-1).
        if r == s:
            m_rs = n_r * (n_r - 1) if directed else n_r * (n_r - 1) / 2
        else:
            m_rs = 2 * n_r * n_s if directed else n_r * n_s
        if m_rs == 0:
            continue

        # Clamp to [0, 1]. Parallel/directional edges can push p above 1,
        # which makes log2(1 - p) return nan and silently corrupt the score.
        p = min(e_rs / m_rs, 1.0)

        # Binary entropy H(p); 0 when p == 0 or p == 1
        if 0.0 < p < 1.0:
            data_cost += m_rs * (-p * np.log2(p) - (1.0 - p) * np.log2(1.0 - p))

    return model_cost + data_cost


def mdl_score(
    partition: Dict[Any, int],
    network: Any,
) -> float:
    """Compute MDL (Minimum Description Length) score for a multilayer partition.

    Computes the SBM two-part description length independently per layer and
    sums the results. Operating per layer avoids the flattening problem where
    pooling all layers into core_network inflates block sizes with
    cross-layer node-layer pairs that share no edges, corrupting the edge
    density estimates that drive the data cost.

    Per-layer computation:
      - Part 1 (model cost): n_ℓ * log2(k_ℓ) bits to encode the community
        assignment of each node in layer ℓ, where n_ℓ is the number of
        node-layer pairs in that layer and k_ℓ is the number of distinct
        communities present in that layer.
      - Part 2 (data cost): for every block pair (r, s) within layer ℓ,
        the binary entropy of the observed intra-layer edge density times the
        maximum possible intra-layer edges between those blocks.

    Total MDL = Σ_ℓ (model_cost_ℓ + data_cost_ℓ)

    Lower score is better.

    Partial partitions: every node present in the network is accounted for,
    not just the ones covered by `partition`. A node the partition omits is
    scored as its own singleton community, so both n_ℓ (model cost) and its
    incident edges (data cost) still count. Without this, an algorithm could
    lower its MDL score simply by leaving hard nodes and their edges out of
    the partition.

    Args:
        partition: Dict mapping (node_id, layer) -> community_id.
        network: Multilayer network with a core_network NetworkX graph.

    Returns:
        Total description length in bits (float).  Returns 0.0 for empty
        inputs.

    Examples:
        >>> # Perfect 2-community split on a clique pair
        >>> partition = {('A', 'L'): 0, ('B', 'L'): 0, ('C', 'L'): 1, ('D', 'L'): 1}
        >>> score = mdl_score(partition, net)
        >>> assert score >= 0.0
    """
    G = getattr(network, "core_network", None)
    node_set = set(G.nodes()) if G is not None else set()
    all_nodes = node_set | set(partition.keys())
    if not all_nodes:
        return 0.0

    directed = G.is_directed() if G is not None else False

    # Collect layers and per-layer node assignments. Every node in the
    # network is included -- not just the ones covered by `partition` -- so
    # that an algorithm returning a partial partition cannot shrink n_ℓ or
    # skip edges just by omitting nodes. Nodes missing from `partition` get a
    # unique sentinel object as their "community", i.e. each is treated as
    # its own singleton community.
    layer_partitions: Dict[Any, Dict[Any, Any]] = defaultdict(dict)
    n_unassigned = 0
    for node in all_nodes:
        layer = node[1] if isinstance(node, tuple) and len(node) >= 2 else None
        if node in partition:
            layer_partitions[layer][node] = partition[node]
        else:
            layer_partitions[layer][node] = object()
            n_unassigned += 1

    if n_unassigned:
        warnings.warn(
            f"Partition covers {len(partition)} of {len(all_nodes)} nodes; "
            f"{n_unassigned} unassigned node(s) are scored as singleton "
            "communities so they cannot be omitted to lower the MDL score.",
            stacklevel=2
        )

    # Pre-index edges by layer: only keep intra-layer edges
    layer_edges: Dict[Any, List[tuple]] = defaultdict(list)
    for u, v in (G.edges() if G is not None else []):
        u_layer = u[1] if isinstance(u, tuple) and len(u) >= 2 else None
        v_layer = v[1] if isinstance(v, tuple) and len(v) >= 2 else None
        if u_layer == v_layer:
            layer_edges[u_layer].append((u, v))

    # Sum description length across layers
    total = 0.0
    for layer, lpartition in layer_partitions.items():
        total += _mdl_single_layer(lpartition, layer_edges[layer], directed=directed)

    return total
