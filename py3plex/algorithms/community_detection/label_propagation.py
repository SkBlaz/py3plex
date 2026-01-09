"""Label Propagation algorithms for multilayer networks.

This module implements hard-label propagation algorithms for community detection
in multilayer networks:

1. Supra-Graph Label Propagation: Operates on a conceptual supra-graph with
   interlayer identity links
2. Multiplex Consensus Label Propagation: Alternates between layer-local LPA
   and node-wise consensus

Both algorithms use:
- Hard categorical labels (integer labels internally)
- Asynchronous updates
- Uniform random tie-breaking with seeded RNG
- Convergence based on no label changes in a full sweep

References
----------
.. [1] Label Propagation and Complex Networks (various sources)
.. [2] Multilayer network community detection literature
"""

from __future__ import annotations

from typing import Any, Dict, Literal, Optional, Tuple
import logging

import numpy as np

from py3plex.exceptions import AlgorithmError, CommunityDetectionError


logger = logging.getLogger(__name__)


def multilayer_label_propagation_supra(
    network: Any,
    omega: float = 1.0,
    max_iter: int = 100,
    random_state: Optional[int] = None,
    projection: Literal["none", "majority"] = "none",
) -> Dict[str, Any]:
    """Supra-Graph Label Propagation with hard labels.
    
    Operates on a conceptual supra-graph where each node has a replica per layer
    connected by interlayer identity edges with weight omega. Uses asynchronous
    updates with random tie-breaking.
    
    Parameters
    ----------
    network : multi_layer_network
        The multilayer network to partition
    omega : float, default=1.0
        Interlayer identity edge weight (must be >= 0)
    max_iter : int, default=100
        Maximum number of iterations (sweeps over all replicas)
    random_state : int, optional
        Random seed for deterministic tie-breaking. If None, uses 0.
    projection : {"none", "majority"}, default="none"
        Whether to project replica communities to node-level:
        - "none": Return only replica-level labels
        - "majority": Return both replica labels and node-level majority projection
        
    Returns
    -------
    dict
        Dictionary with keys:
        - "partition_supra": Dict mapping (node_id, layer) -> community_id
        - "labels_supra": Same as partition_supra (alias)
        - "algorithm": "label_propagation_supra"
        - "converged": bool, whether algorithm converged
        - "iterations": int, number of iterations performed
        If projection="majority":
        - "partition_nodes": Dict mapping node_id -> community_id
        - "labels_nodes": Same as partition_nodes (alias)
        
    Raises
    ------
    AlgorithmError
        If omega < 0 or max_iter < 1
    CommunityDetectionError
        If network has no nodes or edges
        
    Examples
    --------
    >>> from py3plex.core import multinet
    >>> net = multinet.multi_layer_network(directed=False)
    >>> net.add_edges([
    ...     {"source": "A", "target": "B", "source_type": "L1", "target_type": "L1"},
    ...     {"source": "B", "target": "C", "source_type": "L1", "target_type": "L1"},
    ...     {"source": "A", "target": "C", "source_type": "L2", "target_type": "L2"},
    ... ])
    >>> result = multilayer_label_propagation_supra(net, omega=0.5, random_state=42)
    >>> partition = result["partition_supra"]
    >>> print(f"Communities: {len(set(partition.values()))}")
    
    Notes
    -----
    Complexity: O(max_iter * (|E| + omega * L * |V|)) where E is edges, L layers, V nodes
    """
    # Validate parameters
    if omega < 0:
        raise AlgorithmError(
            f"omega must be >= 0, got {omega}",
            suggestions=["Use omega=0 for independent layer communities",
                        "Use omega > 0 to couple layers"]
        )
    if max_iter < 1:
        raise AlgorithmError(
            f"max_iter must be >= 1, got {max_iter}",
            suggestions=["Use max_iter >= 10 for reasonable convergence"]
        )
    
    # Set up RNG
    seed = random_state if random_state is not None else 0
    rng = np.random.Generator(np.random.PCG64(seed))
    
    # Get network structure - nodes returns (node_id, layer) tuples
    node_layer_tuples = list(network.get_nodes())
    if not node_layer_tuples:
        raise CommunityDetectionError(
            "Network has no nodes",
            suggestions=["Add nodes to the network before running community detection"]
        )
    
    # Extract unique nodes and layers
    nodes = sorted(set(node_id for node_id, layer in node_layer_tuples))
    layers = sorted(set(layer for node_id, layer in node_layer_tuples))
    
    if not layers:
        raise CommunityDetectionError(
            "Network has no layers",
            suggestions=["Add edges to create layers"]
        )
    
    # Build replica list: use the actual (node_id, layer) tuples from network
    replicas = node_layer_tuples
    replica_to_idx = {replica: i for i, replica in enumerate(replicas)}
    n_replicas = len(replicas)
    
    # Initialize labels: unique label per replica
    labels = np.arange(n_replicas, dtype=np.int32)
    
    # Build intralayer adjacency lists
    # For each replica, store list of neighbor replica indices
    intralayer_neighbors = [[] for _ in range(n_replicas)]
    
    for edge_data in network.get_edges(data=True):
        source, target = edge_data[0], edge_data[1]
        if len(edge_data) >= 3 and isinstance(edge_data[2], dict):
            data = edge_data[2]
            source_layer = data.get("source_type", layers[0])
            target_layer = data.get("target_type", layers[0])
        else:
            # Assume same layer
            source_layer = target_layer = layers[0]
        
        # Add intralayer edge (if same layer)
        if source_layer == target_layer:
            source_replica = (source, source_layer)
            target_replica = (target, target_layer)
            
            if source_replica in replica_to_idx and target_replica in replica_to_idx:
                src_idx = replica_to_idx[source_replica]
                tgt_idx = replica_to_idx[target_replica]
                
                if tgt_idx not in intralayer_neighbors[src_idx]:
                    intralayer_neighbors[src_idx].append(tgt_idx)
                if src_idx not in intralayer_neighbors[tgt_idx]:
                    intralayer_neighbors[tgt_idx].append(src_idx)
    
    # Build interlayer connections (replicas of same node across layers)
    # Map node -> list of replica indices
    node_to_replicas = {}
    for i, (node, layer) in enumerate(replicas):
        if node not in node_to_replicas:
            node_to_replicas[node] = []
        node_to_replicas[node].append(i)
    
    # Asynchronous label propagation
    converged = False
    iteration = 0
    
    for iteration in range(max_iter):
        changed = False
        
        # Shuffle replica order for asynchronous updates
        update_order = rng.permutation(n_replicas)
        
        for idx in update_order:
            node, layer = replicas[idx]
            
            # Compute label scores
            label_scores = {}
            
            # Intralayer neighbors
            for neighbor_idx in intralayer_neighbors[idx]:
                neighbor_label = labels[neighbor_idx]
                label_scores[neighbor_label] = label_scores.get(neighbor_label, 0) + 1
            
            # Interlayer identity links (same node, different layers)
            if omega > 0:
                for replica_idx in node_to_replicas[node]:
                    if replica_idx != idx:
                        replica_label = labels[replica_idx]
                        label_scores[replica_label] = label_scores.get(replica_label, 0) + omega
            
            # Find label(s) with maximum score
            if label_scores:
                max_score = max(label_scores.values())
                max_labels = [lbl for lbl, score in label_scores.items() if score == max_score]
                
                # Random tie-breaking
                if len(max_labels) > 1:
                    new_label = rng.choice(max_labels)
                else:
                    new_label = max_labels[0]
                
                # Update label
                if labels[idx] != new_label:
                    labels[idx] = new_label
                    changed = True
            # If no neighbors and omega=0, node keeps its label (isolated node)
        
        # Check convergence
        if not changed:
            converged = True
            break
    
    # Build output partition
    partition_supra = {}
    for i, replica in enumerate(replicas):
        partition_supra[replica] = int(labels[i])
    
    result = {
        "partition_supra": partition_supra,
        "labels_supra": partition_supra,  # Alias
        "algorithm": "label_propagation_supra",
        "converged": converged,
        "iterations": iteration + 1,
        "omega": omega,
    }
    
    # Optional node-level projection
    if projection == "majority":
        partition_nodes = {}
        for node in nodes:
            # Collect labels across layers for this node
            node_labels = []
            for layer in layers:
                replica = (node, layer)
                if replica in partition_supra:
                    node_labels.append(partition_supra[replica])
            
            if node_labels:
                # Majority vote with random tie-breaking
                label_counts = {}
                for lbl in node_labels:
                    label_counts[lbl] = label_counts.get(lbl, 0) + 1
                
                max_count = max(label_counts.values())
                max_labels = [lbl for lbl, cnt in label_counts.items() if cnt == max_count]
                
                if len(max_labels) > 1:
                    partition_nodes[node] = int(rng.choice(max_labels))
                else:
                    partition_nodes[node] = int(max_labels[0])
        
        result["partition_nodes"] = partition_nodes
        result["labels_nodes"] = partition_nodes  # Alias
    
    return result


def multiplex_label_propagation_consensus(
    network: Any,
    max_iter: int = 25,
    inner_max_iter: int = 50,
    random_state: Optional[int] = None,
) -> Dict[str, Any]:
    """Multiplex Consensus Label Propagation with hard labels.
    
    Alternates between:
    1. Independent layer-local LPA in each layer
    2. Node-wise consensus (majority vote across layers)
    3. Synchronization (all replicas adopt consensus label)
    
    Never uses interlayer edges. Converges when node consensus labels stabilize.
    
    Parameters
    ----------
    network : multi_layer_network
        The multilayer network to partition
    max_iter : int, default=25
        Maximum number of outer cycles (layer-local LPA → consensus → sync)
    inner_max_iter : int, default=50
        Maximum iterations for layer-local LPA per cycle
    random_state : int, optional
        Random seed for deterministic tie-breaking. If None, uses 0.
        
    Returns
    -------
    dict
        Dictionary with keys:
        - "partition_nodes": Dict mapping node_id -> community_id
        - "labels_nodes": Same as partition_nodes (alias)
        - "labels_by_layer": Dict mapping (node_id, layer) -> community_id
        - "algorithm": "label_propagation_consensus"
        - "converged": bool, whether algorithm converged
        - "iterations": int, number of outer iterations performed
        
    Raises
    ------
    AlgorithmError
        If max_iter < 1 or inner_max_iter < 1
    CommunityDetectionError
        If network has no nodes or edges
        
    Examples
    --------
    >>> from py3plex.core import multinet
    >>> net = multinet.multi_layer_network(directed=False)
    >>> net.add_edges([
    ...     {"source": "A", "target": "B", "source_type": "L1", "target_type": "L1"},
    ...     {"source": "B", "target": "C", "source_type": "L1", "target_type": "L1"},
    ...     {"source": "A", "target": "C", "source_type": "L2", "target_type": "L2"},
    ... ])
    >>> result = multiplex_label_propagation_consensus(net, random_state=42)
    >>> partition = result["partition_nodes"]
    >>> print(f"Communities: {len(set(partition.values()))}")
    
    Notes
    -----
    Complexity: O(max_iter * inner_max_iter * |E|) where E is edges
    """
    # Validate parameters
    if max_iter < 1:
        raise AlgorithmError(
            f"max_iter must be >= 1, got {max_iter}",
            suggestions=["Use max_iter >= 10 for reasonable convergence"]
        )
    if inner_max_iter < 1:
        raise AlgorithmError(
            f"inner_max_iter must be >= 1, got {inner_max_iter}",
            suggestions=["Use inner_max_iter >= 10 for layer convergence"]
        )
    
    # Set up RNG
    seed = random_state if random_state is not None else 0
    rng = np.random.Generator(np.random.PCG64(seed))
    
    # Get network structure - nodes returns (node_id, layer) tuples
    node_layer_tuples = list(network.get_nodes())
    if not node_layer_tuples:
        raise CommunityDetectionError(
            "Network has no nodes",
            suggestions=["Add nodes to the network before running community detection"]
        )
    
    # Extract unique nodes and layers
    nodes = sorted(set(node_id for node_id, layer in node_layer_tuples))
    layers = sorted(set(layer for node_id, layer in node_layer_tuples))
    
    if not layers:
        raise CommunityDetectionError(
            "Network has no layers",
            suggestions=["Add edges to create layers"]
        )
    
    # Build replica list and mappings - use actual node-layer tuples
    replicas = node_layer_tuples
    replica_to_idx = {replica: i for i, replica in enumerate(replicas)}
    n_replicas = len(replicas)
    
    # Initialize labels: unique label per replica
    labels = np.arange(n_replicas, dtype=np.int32)
    
    # Build layer-specific adjacency lists
    layer_replicas = {layer: [] for layer in layers}
    layer_neighbors = {layer: {} for layer in layers}
    
    for i, (node, layer) in enumerate(replicas):
        layer_replicas[layer].append(i)
        layer_neighbors[layer][i] = []
    
    # Build intralayer adjacency
    for edge_data in network.get_edges(data=True):
        source, target = edge_data[0], edge_data[1]
        if len(edge_data) >= 3 and isinstance(edge_data[2], dict):
            data = edge_data[2]
            source_layer = data.get("source_type", layers[0])
            target_layer = data.get("target_type", layers[0])
        else:
            source_layer = target_layer = layers[0]
        
        if source_layer == target_layer:
            source_replica = (source, source_layer)
            target_replica = (target, target_layer)
            
            if source_replica in replica_to_idx and target_replica in replica_to_idx:
                src_idx = replica_to_idx[source_replica]
                tgt_idx = replica_to_idx[target_replica]
                
                if tgt_idx not in layer_neighbors[source_layer][src_idx]:
                    layer_neighbors[source_layer][src_idx].append(tgt_idx)
                if src_idx not in layer_neighbors[target_layer][tgt_idx]:
                    layer_neighbors[target_layer][tgt_idx].append(src_idx)
    
    # Map node -> list of replica indices
    node_to_replicas = {}
    for i, (node, layer) in enumerate(replicas):
        if node not in node_to_replicas:
            node_to_replicas[node] = []
        node_to_replicas[node].append(i)
    
    # Track node consensus labels
    node_consensus = {node: labels[node_to_replicas[node][0]] for node in nodes}
    
    # Outer iteration loop
    converged = False
    iteration = 0
    
    for iteration in range(max_iter):
        # Step 1: Layer-local LPA for each layer
        for layer in layers:
            layer_reps = layer_replicas[layer]
            if not layer_reps:
                continue
            
            # Run LPA in this layer
            for _ in range(inner_max_iter):
                changed = False
                update_order = rng.permutation(len(layer_reps))
                
                for order_idx in update_order:
                    idx = layer_reps[order_idx]
                    
                    # Compute label scores from intralayer neighbors
                    label_scores = {}
                    for neighbor_idx in layer_neighbors[layer][idx]:
                        neighbor_label = labels[neighbor_idx]
                        label_scores[neighbor_label] = label_scores.get(neighbor_label, 0) + 1
                    
                    if label_scores:
                        max_score = max(label_scores.values())
                        max_labels = [lbl for lbl, score in label_scores.items() if score == max_score]
                        
                        # Random tie-breaking
                        if len(max_labels) > 1:
                            new_label = rng.choice(max_labels)
                        else:
                            new_label = max_labels[0]
                        
                        if labels[idx] != new_label:
                            labels[idx] = new_label
                            changed = True
                    # If no neighbors, node keeps its label (isolated node)
                
                # Early stopping if layer converged
                if not changed:
                    break
        
        # Step 2: Node-wise consensus (majority vote)
        new_consensus = {}
        for node in nodes:
            node_labels = [labels[idx] for idx in node_to_replicas[node]]
            
            # Count occurrences
            label_counts = {}
            for lbl in node_labels:
                label_counts[lbl] = label_counts.get(lbl, 0) + 1
            
            max_count = max(label_counts.values())
            max_labels = [lbl for lbl, cnt in label_counts.items() if cnt == max_count]
            
            # Random tie-breaking
            if len(max_labels) > 1:
                new_consensus[node] = int(rng.choice(max_labels))
            else:
                new_consensus[node] = int(max_labels[0])
        
        # Check if consensus changed
        consensus_changed = any(
            new_consensus[node] != node_consensus[node] for node in nodes
        )
        
        # Step 3: Synchronization - assign consensus label to all replicas
        node_consensus = new_consensus
        for node in nodes:
            consensus_label = node_consensus[node]
            for idx in node_to_replicas[node]:
                labels[idx] = consensus_label
        
        if not consensus_changed:
            converged = True
            break
    
    # Build output partitions
    partition_nodes = {node: int(node_consensus[node]) for node in nodes}
    labels_by_layer = {replicas[i]: int(labels[i]) for i in range(n_replicas)}
    
    result = {
        "partition_nodes": partition_nodes,
        "labels_nodes": partition_nodes,  # Alias
        "labels_by_layer": labels_by_layer,
        "algorithm": "label_propagation_consensus",
        "converged": converged,
        "iterations": iteration + 1,
    }
    
    return result
