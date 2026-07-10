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

import networkx as nx
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


def _dedupe_node_pairs(edges: List[tuple], directed: bool) -> List[tuple]:
    """Collapse parallel/multi-edges into a single edge per node pair.

    py3plex's default `core_network` container is a `nx.MultiGraph` /
    `nx.MultiDiGraph`, which can hold more than one edge between the same
    node pair. The block-pair capacity `m_rs` computed in
    `_mdl_single_layer` counts *distinct* node pairs, so leaving multi-edges
    un-collapsed lets the raw edge count `e_rs` exceed `m_rs` -- silently
    clamped to a density of 1.0, which scores e.g. a 2-edge and a 200-edge
    block identically. Deduplicating here is a deliberate, explicit collapse
    (one of "reject / collapse / weighted likelihood") that keeps the
    Bernoulli block model well-defined for multigraph inputs, at the cost of
    discarding multiplicity (and, since `_mdl_single_layer` never looks at
    edge weight, weight magnitude too -- see `mdl_score`'s warning).
    """
    seen: set = set()
    deduped = []
    for u, v in edges:
        key = (u, v) if directed else frozenset((u, v))
        if key in seen:
            continue
        seen.add(key)
        deduped.append((u, v))
    return deduped


def _mdl_single_layer(
    layer_partition: Dict[Any, Any],
    layer_edges: List[tuple],
    directed: bool = False,
    include_model_cost: bool = True,
) -> float:
    """Compute SBM two-part description length for a flat edge set.

    Despite the name, this is used for two things in `mdl_score`: the
    per-layer intra-layer term (with `include_model_cost=True`, using a
    single layer's local node -> community assignment), and the global
    inter-layer term (with `include_model_cost=False`, using the full
    across-all-layers node-layer -> community assignment, restricted to
    edges that cross layers). See `mdl_score` for why model cost is only
    charged once, per layer.

    Args:
        layer_partition: Dict mapping node -> community_id.
            Community ids need only be hashable (e.g. singleton sentinel
            objects for unassigned nodes are supported).
        layer_edges: List of (u, v) edge pairs to account for. Both
            endpoints must be keys of `layer_partition`. May contain
            parallel/multi-edges (e.g. from a MultiGraph); these are
            collapsed to a single edge per node pair before scoring, see
            `_dedupe_node_pairs`.
        directed: Whether the underlying graph is directed. Controls the
            maximum-edge normalization for block pairs. Defaults to False
            (undirected), preserving backward-compatible behavior for callers
            that do not pass the flag.
        include_model_cost: Whether to add the n * log2(k) model-cost term.
            Set to False when `layer_partition`/`layer_edges` describe a
            block structure whose assignment cost was already charged
            elsewhere (e.g. the inter-layer term reuses assignments already
            paid for by the per-layer model cost).

    Returns:
        Description length in bits.

    Notes:
        - Complexity: O(n + |E|), not O(k^2). The data cost loop iterates
          only over `edge_counts` (block pairs with at least one observed
          edge), not over all k^2 pairs of communities -- block pairs with
          no edges contribute exactly 0 (H(p=0) == 0), so they're skipped
          rather than enumerated. This matters once heavily-fragmented
          partitions (e.g. many singleton communities from unassigned nodes,
          see `mdl_score`) push k up toward n: a naive double loop over
          communities would be O(k^2) regardless of how sparse the edges
          are, whereas this stays tied to the actual edge count. The
          remaining cost still scales with |E| itself, which is inherent to
          reading every edge once and not specific to fragmentation -- a
          dense graph is the same O(|E|) cost whether it has 2 communities
          or n of them.
    """
    communities: Dict[Any, List[Any]] = defaultdict(list)
    for node, comm in layer_partition.items():
        communities[comm].append(node)

    k = len(communities)
    n = len(layer_partition)

    if k == 0 or n == 0:
        return 0.0

    # Collapse parallel/multi-edges before block-pair counting, so e_rs can
    # never exceed the simple-graph capacity m_rs computed below.
    layer_edges = _dedupe_node_pairs(layer_edges, directed)

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
    model_cost = n * np.log2(k) if (include_model_cost and k > 1) else 0.0

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

        # e_rs <= m_rs is now guaranteed by the parallel-edge collapse above
        # (each node pair contributes at most one edge), so this clamp is a
        # defensive fallback rather than the primary safeguard -- without it,
        # p > 1 would make log2(1 - p) return nan and silently corrupt the
        # score.
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
    sums the results, then adds one more term for inter-layer (cross-layer)
    edges. Operating per layer for the intra-layer term avoids the flattening
    problem where pooling all layers into core_network inflates block sizes
    with cross-layer node-layer pairs that share no edges, corrupting the
    edge density estimates that drive the data cost.

    Per-layer computation (intra-layer edges only):
      - Part 1 (model cost): n_ℓ * log2(k_ℓ) bits to encode the community
        assignment of each node in layer ℓ, where n_ℓ is the number of
        node-layer pairs in that layer and k_ℓ is the number of distinct
        communities present in that layer.
      - Part 2 (data cost): for every block pair (r, s) within layer ℓ,
        the binary entropy of the observed intra-layer edge density times the
        maximum possible intra-layer edges between those blocks.

    Inter-layer computation (edges whose endpoints are in different layers,
    e.g. multiplex coupling edges or general cross-layer edges):
      - No additional model cost is charged -- every node-layer pair's
        community assignment was already paid for by the per-layer model
        cost above.
      - Data cost only: block sizes N_r/N_s are the *global* community
        sizes (summed across all layers), and the block pair (r, s) is
        scored using the observed inter-layer edge density between them,
        the same binary-entropy formula as the intra-layer case. This
        slightly overstates the space of possible inter-layer edges (it
        does not subtract same-layer node pairs from N_r * N_s, since
        inter-layer edges in py3plex are not restricted to same-node
        couplings and can connect arbitrary node-layer pairs), which is a
        conservative approximation rather than an exact block model.

    Total MDL = Σ_ℓ (model_cost_ℓ + data_cost_ℓ) + data_cost_inter_layer

    Lower score is better. Ignoring inter-layer edges entirely would let two
    partitions with identical intra-layer structure but very different (e.g.
    incoherent vs. replica-consistent) cross-layer coupling score identically,
    which is misleading for a *multilayer* MDL metric.

    Partial partitions: every node present in the network is accounted for,
    not just the ones covered by `partition`. A node the partition omits is
    scored as its own singleton community, so both n_ℓ (model cost) and its
    incident edges (data cost) still count. Without this, an algorithm could
    lower its MDL score simply by leaving hard nodes and their edges out of
    the partition.

    Parallel/weighted edges: the block model above is Bernoulli (edge
    present or absent between a node pair), which is only well-defined for
    simple graphs. py3plex's default network container is a
    `nx.MultiGraph`/`nx.MultiDiGraph`, so if the same node pair carries more
    than one edge, it is collapsed to a single edge before scoring (see
    `_dedupe_node_pairs`) rather than left to silently overflow the
    simple-graph capacity and clamp to a density of 1.0. Edge `weight`
    attributes are likewise ignored -- every edge counts as one, regardless
    of magnitude. Both cases emit a `UserWarning` since the description
    length then cannot distinguish a lightly- from a heavily-connected block.

    Args:
        partition: Dict mapping (node_id, layer) -> community_id.
        network: Multilayer network with a core_network NetworkX graph.

    Returns:
        Total description length in bits (float).  Returns 0.0 for empty
        inputs.

    Notes:
        - Complexity: O(N + |E|) total across layers, where N is the number
          of node-layer pairs and E the edges (intra- plus inter-layer) --
          see `_mdl_single_layer`'s Notes for why fragmentation (many
          singleton communities, e.g. from unassigned nodes) doesn't push
          this toward O(k^2). On expected AutoCommunity graph sizes (up to
          ~1e5 nodes / ~1e6 edges, matching the practical_limits declared
          for candidate algorithms like leiden_multilayer), this is expected
          to stay well under a second; see
          `tests/test_mdl_score.py::TestPerformance::test_no_quadratic_blowup_mdl_fragmented`
          (and `..._large_scale` for a slow-marked ~2M-node check) for
          regression guards against a future reintroduction of a
          quadratic-in-communities loop.

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
    raw_edges: List[tuple] = list(G.edges()) if G is not None else []

    # Detect parallel edges (possible on py3plex's default MultiGraph/
    # MultiDiGraph container) and non-unit edge weights. Neither is modeled
    # by the Bernoulli block structure below -- multi-edges are collapsed to
    # a single edge per node pair (see `_dedupe_node_pairs`) and weight
    # magnitude is ignored entirely -- so warn rather than silently scoring
    # a lightly- and heavily-connected block identically.
    if isinstance(G, (nx.MultiGraph, nx.MultiDiGraph)):
        has_parallel_edges = len(_dedupe_node_pairs(raw_edges, directed)) < len(raw_edges)
    else:
        has_parallel_edges = False
    has_weighted_edges = G is not None and any(
        data.get("weight", 1) != 1 for _, _, data in G.edges(data=True)
    )
    if has_parallel_edges or has_weighted_edges:
        warnings.warn(
            "Network has parallel edges and/or non-unit edge weights; "
            "mdl_score models a simple Bernoulli block structure, so "
            "parallel edges are collapsed to one edge per node pair and "
            "weight magnitude is ignored. The resulting description length "
            "cannot distinguish a lightly- from a heavily-connected block.",
            stacklevel=2,
        )

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

    # Split edges into intra-layer (same layer on both ends) and inter-layer
    # (endpoints in different layers, e.g. multiplex coupling edges).
    layer_edges: Dict[Any, List[tuple]] = defaultdict(list)
    inter_layer_edges: List[tuple] = []
    for u, v in raw_edges:
        u_layer = u[1] if isinstance(u, tuple) and len(u) >= 2 else None
        v_layer = v[1] if isinstance(v, tuple) and len(v) >= 2 else None
        if u_layer == v_layer:
            layer_edges[u_layer].append((u, v))
        else:
            inter_layer_edges.append((u, v))

    # Sum description length across layers (intra-layer model + data cost)
    total = 0.0
    global_partition: Dict[Any, Any] = {}
    for layer, lpartition in layer_partitions.items():
        total += _mdl_single_layer(lpartition, layer_edges[layer], directed=directed)
        global_partition.update(lpartition)

    # Add the inter-layer data cost: community assignments were already paid
    # for above, so only the observed cross-layer edge density is charged.
    if inter_layer_edges:
        total += _mdl_single_layer(
            global_partition,
            inter_layer_edges,
            directed=directed,
            include_model_cost=False,
        )

    return total
