"""Streaming community detection algorithms for temporal networks.

This module provides algorithms for detecting and tracking community
changes over time in temporal multilayer networks.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, Iterator, Optional, Set, Tuple

import networkx as nx


def streaming_community_change(
    temporal_network: Any,  # TemporalMultiLayerNetwork type hint avoided for circular import
    community_detector: Callable[[Any], Dict[Any, Any]],
    window_size: float,
    step: Optional[float] = None,
    layers: Optional[Any] = None,
    change_metric: str = "jaccard",
) -> Iterator[Tuple[float, float, Dict[Any, Any], float]]:
    """Apply community detection over time windows and compute change scores.
    
    This function iterates over sliding windows, applies a community detection
    algorithm to each window, and computes a change score between consecutive
    windows to quantify community dynamics.
    
    Args:
        temporal_network: TemporalMultiLayerNetwork instance
        community_detector: Function that takes a network and returns a dict
                          mapping node IDs to community IDs.
                          Example: lambda net: nx.algorithms.community.louvain_communities(net.core_network)
        window_size: Size of each time window
        step: Step size between windows (defaults to window_size)
        layers: Optional layer filter
        change_metric: Metric for computing change score:
                      - "jaccard": Jaccard similarity of community membership
                      - "nmi": Normalized mutual information (requires sklearn)
                      - "node_moves": Fraction of nodes that changed communities
        
    Yields:
        Tuples of (t_start, t_end, communities, change_score) where:
        - t_start, t_end: Time window boundaries
        - communities: Dict mapping node IDs to community IDs
        - change_score: Change score compared to previous window (0.0 for first window)
        
    Example:
        >>> from py3plex.core.temporal_multinet import TemporalMultiLayerNetwork
        >>> from py3plex.algorithms.temporal import streaming_community_change
        >>> import networkx as nx
        >>> 
        >>> # Create temporal network
        >>> tnet = TemporalMultiLayerNetwork()
        >>> # ... add edges ...
        >>> 
        >>> # Define community detector
        >>> def detect_communities(net):
        ...     graph = net.core_network if hasattr(net, 'core_network') else net
        ...     communities = nx.algorithms.community.label_propagation_communities(graph)
        ...     # Convert to node -> community_id mapping
        ...     result = {}
        ...     for i, comm in enumerate(communities):
        ...         for node in comm:
        ...             result[node] = i
        ...     return result
        >>> 
        >>> # Stream community changes
        >>> for t_start, t_end, comms, change in streaming_community_change(
        ...     tnet, detect_communities, window_size=100
        ... ):
        ...     print(f"Window [{t_start}, {t_end}]: {len(set(comms.values()))} communities, change={change:.3f}")
    """
    prev_communities = None
    
    for t_start, t_end, window_net in temporal_network.window_iter(
        window_size=window_size,
        step=step,
        layers=layers,
        return_type="snapshot",
    ):
        # Apply community detection
        try:
            communities = community_detector(window_net)
        except Exception as e:
            # If detection fails (e.g., empty graph), return empty result
            yield (t_start, t_end, {}, 0.0)
            continue
        
        # Compute change score
        if prev_communities is None:
            # First window - no previous communities to compare
            change_score = 0.0
        else:
            change_score = _compute_community_change(
                prev_communities,
                communities,
                metric=change_metric,
            )
        
        yield (t_start, t_end, communities, change_score)
        
        prev_communities = communities


def _compute_community_change(
    prev: Dict[Any, Any],
    current: Dict[Any, Any],
    metric: str = "jaccard",
) -> float:
    """Compute change score between two community assignments.
    
    Args:
        prev: Previous community assignment (node -> community_id)
        current: Current community assignment (node -> community_id)
        metric: Change metric to use
        
    Returns:
        Change score (higher means more change)
    """
    # Get common nodes
    common_nodes = set(prev.keys()) & set(current.keys())
    
    if not common_nodes:
        # No overlap - maximum change
        return 1.0
    
    if metric == "jaccard":
        # Compute Jaccard similarity of community membership
        # For each pair of nodes, check if they're in the same community
        same_prev = 0
        same_current = 0
        same_both = 0
        
        nodes = list(common_nodes)
        for i in range(len(nodes)):
            for j in range(i + 1, len(nodes)):
                node_i, node_j = nodes[i], nodes[j]
                
                in_same_prev = (prev[node_i] == prev[node_j])
                in_same_current = (current[node_i] == current[node_j])
                
                if in_same_prev:
                    same_prev += 1
                if in_same_current:
                    same_current += 1
                if in_same_prev and in_same_current:
                    same_both += 1
        
        # Jaccard similarity
        if same_prev + same_current - same_both == 0:
            similarity = 1.0  # All nodes in single community in both
        else:
            similarity = same_both / (same_prev + same_current - same_both)
        
        # Return change score (1 - similarity)
        return 1.0 - similarity
    
    elif metric == "node_moves":
        # Fraction of nodes that changed communities
        # Map community IDs to canonical form (largest community gets ID 0, etc.)
        prev_canonical = _canonicalize_communities(prev)
        current_canonical = _canonicalize_communities(current)
        
        # Count nodes that changed
        changed = sum(1 for node in common_nodes 
                     if prev_canonical.get(node) != current_canonical.get(node))
        
        return changed / len(common_nodes)
    
    elif metric == "nmi":
        # Normalized mutual information
        try:
            from sklearn.metrics import normalized_mutual_info_score
            
            # Align node order
            nodes = list(common_nodes)
            prev_labels = [prev[node] for node in nodes]
            current_labels = [current[node] for node in nodes]
            
            nmi = normalized_mutual_info_score(prev_labels, current_labels)
            
            # Return change score (1 - NMI)
            return 1.0 - nmi
        except ImportError:
            # Fallback to node_moves if sklearn not available
            return _compute_community_change(prev, current, metric="node_moves")
    
    else:
        raise ValueError(f"Unknown change metric: {metric}")


def _canonicalize_communities(communities: Dict[Any, Any]) -> Dict[Any, int]:
    """Map community IDs to canonical form (0, 1, 2, ...).
    
    Largest community gets ID 0, second largest gets ID 1, etc.
    
    Args:
        communities: Node -> community_id mapping
        
    Returns:
        Node -> canonical_community_id mapping
    """
    from collections import Counter
    
    # Count community sizes
    comm_sizes = Counter(communities.values())
    
    # Sort communities by size (descending)
    sorted_comms = [comm_id for comm_id, _ in comm_sizes.most_common()]
    
    # Create mapping from original ID to canonical ID
    id_map = {comm_id: i for i, comm_id in enumerate(sorted_comms)}
    
    # Apply mapping
    return {node: id_map[comm_id] for node, comm_id in communities.items()}


def detect_community_events(
    temporal_network: Any,
    community_detector: Callable[[Any], Dict[Any, Any]],
    window_size: float,
    step: Optional[float] = None,
    change_threshold: float = 0.3,
) -> Iterator[Tuple[float, float, str, float]]:
    """Detect significant community events (merge, split, birth, death).
    
    This is a higher-level function that identifies specific types of
    community changes rather than just a change score.
    
    Args:
        temporal_network: TemporalMultiLayerNetwork instance
        community_detector: Community detection function
        window_size: Size of each time window
        step: Step size between windows
        change_threshold: Minimum change score to consider an event
        
    Yields:
        Tuples of (t_start, t_end, event_type, change_score) where
        event_type is one of: "stable", "high_change", "merge", "split"
        
    Example:
        >>> for t_start, t_end, event, change in detect_community_events(
        ...     tnet, detect_fn, window_size=100, change_threshold=0.4
        ... ):
        ...     if event != "stable":
        ...         print(f"Event at [{t_start}, {t_end}]: {event} (change={change:.3f})")
    """
    for t_start, t_end, communities, change_score in streaming_community_change(
        temporal_network,
        community_detector,
        window_size,
        step,
    ):
        # Classify event based on change score
        # More sophisticated analysis could detect merges/splits based on
        # community membership transitions, but for now we use a simple threshold
        if change_score < change_threshold:
            event_type = "stable"
        else:
            event_type = "high_change"
        
        yield (t_start, t_end, event_type, change_score)
