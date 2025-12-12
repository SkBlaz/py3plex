"""Streaming centrality algorithms for temporal networks.

This module provides incremental and streaming centrality computation
for temporal multilayer networks, enabling efficient analysis of
large-scale dynamic networks.
"""

from __future__ import annotations

from typing import Any, Dict, Iterator, Optional, Tuple

import networkx as nx
import numpy as np


def streaming_pagerank(
    temporal_network: Any,  # TemporalMultiLayerNetwork type hint avoided for circular import
    alpha: float = 0.85,
    damping: float = 0.85,
    initial_scores: Optional[Dict[Any, float]] = None,
    window_size: Optional[float] = None,
    step: Optional[float] = None,
    normalize: bool = True,
    max_iter_per_window: int = 10,
    tolerance: float = 1e-6,
) -> Iterator[Tuple[float, float, Dict[Any, float]]]:
    """Compute streaming approximate PageRank on a temporal multilayer network.
    
    This algorithm iterates over time windows and updates PageRank scores
    incrementally, using the previous window's scores as the starting point
    for the next window. This is much faster than recomputing from scratch
    for each window.
    
    Args:
        temporal_network: TemporalMultiLayerNetwork instance
        alpha: Damping factor (default: 0.85)
        damping: Alias for alpha (for compatibility)
        initial_scores: Optional initial node scores (default: uniform)
        window_size: Size of each time window (required)
        step: Step size between windows (defaults to window_size)
        normalize: Whether to normalize scores to sum to 1 (default: True)
        max_iter_per_window: Maximum power iterations per window (default: 10)
        tolerance: Convergence tolerance for power iteration (default: 1e-6)
        
    Yields:
        Tuples of (t_start, t_end, scores_dict) where scores_dict maps
        node IDs to PageRank scores for that window
        
    Example:
        >>> from py3plex.core.temporal_multinet import TemporalMultiLayerNetwork
        >>> from py3plex.algorithms.temporal import streaming_pagerank
        >>> 
        >>> # Create temporal network
        >>> tnet = TemporalMultiLayerNetwork()
        >>> tnet.add_edge('A', 'layer1', 'B', 'layer1', t=100.0)
        >>> tnet.add_edge('B', 'layer1', 'C', 'layer1', t=150.0)
        >>> tnet.add_edge('C', 'layer1', 'A', 'layer1', t=200.0)
        >>> 
        >>> # Compute streaming PageRank
        >>> for t_start, t_end, scores in streaming_pagerank(tnet, window_size=50):
        ...     print(f"Window [{t_start}, {t_end}]: Top node = {max(scores, key=scores.get)}")
    """
    if window_size is None:
        raise ValueError("window_size is required for streaming PageRank")
    
    # Use damping if alpha not explicitly set
    damping_factor = alpha if alpha != 0.85 else damping
    
    # Initialize scores
    scores = initial_scores.copy() if initial_scores else None
    
    # Iterate over windows
    for t_start, t_end, window_net in temporal_network.window_iter(
        window_size=window_size,
        step=step,
        return_type="snapshot",
    ):
        # Get the snapshot graph
        base_net = window_net if hasattr(window_net, 'core_network') else window_net
        graph = base_net.core_network if hasattr(base_net, 'core_network') else base_net
        
        # Get all nodes in this window
        nodes = list(graph.nodes())
        
        if not nodes:
            # Empty window
            yield (t_start, t_end, {})
            continue
        
        # Initialize scores if needed
        if scores is None or not scores:
            scores = {node: 1.0 / len(nodes) for node in nodes}
        else:
            # Add new nodes with small initial score
            for node in nodes:
                if node not in scores:
                    scores[node] = 1.0 / (len(nodes) * 10)
        
        # Run limited power iteration
        for _ in range(max_iter_per_window):
            new_scores = {}
            
            for node in nodes:
                # Compute incoming contribution
                incoming_score = 0.0
                for pred in graph.predecessors(node) if graph.is_directed() else graph.neighbors(node):
                    if pred in scores:
                        # Get out-degree of predecessor
                        out_degree = graph.out_degree(pred) if graph.is_directed() else graph.degree(pred)
                        if out_degree > 0:
                            incoming_score += scores[pred] / out_degree
                
                # Apply damping
                new_scores[node] = (1 - damping_factor) / len(nodes) + damping_factor * incoming_score
            
            # Check convergence
            if scores:
                max_change = max(abs(new_scores.get(n, 0) - scores.get(n, 0)) for n in nodes)
                if max_change < tolerance:
                    break
            
            scores = new_scores
        
        # Normalize if requested
        if normalize and scores:
            total = sum(scores.values())
            if total > 0:
                scores = {node: score / total for node, score in scores.items()}
        
        # Yield window results
        window_scores = {node: scores.get(node, 0.0) for node in nodes}
        yield (t_start, t_end, window_scores)


def streaming_degree_centrality(
    temporal_network: Any,
    window_size: Optional[float] = None,
    step: Optional[float] = None,
    normalize: bool = True,
) -> Iterator[Tuple[float, float, Dict[Any, float]]]:
    """Compute streaming degree centrality on a temporal multilayer network.
    
    This is a simpler streaming centrality that just counts degrees
    in each window. Useful as a baseline or for very large networks.
    
    Args:
        temporal_network: TemporalMultiLayerNetwork instance
        window_size: Size of each time window (required)
        step: Step size between windows (defaults to window_size)
        normalize: Whether to normalize by max possible degree (default: True)
        
    Yields:
        Tuples of (t_start, t_end, centrality_dict)
        
    Example:
        >>> for t_start, t_end, centrality in streaming_degree_centrality(tnet, window_size=50):
        ...     print(f"Window [{t_start}, {t_end}]: {len(centrality)} nodes")
    """
    if window_size is None:
        raise ValueError("window_size is required for streaming degree centrality")
    
    for t_start, t_end, window_net in temporal_network.window_iter(
        window_size=window_size,
        step=step,
        return_type="snapshot",
    ):
        # Get the snapshot graph
        base_net = window_net if hasattr(window_net, 'core_network') else window_net
        graph = base_net.core_network if hasattr(base_net, 'core_network') else base_net
        
        # Compute degree centrality
        if graph.number_of_nodes() == 0:
            yield (t_start, t_end, {})
            continue
        
        # Get degrees
        if graph.is_directed():
            degrees = {node: graph.out_degree(node) + graph.in_degree(node) 
                      for node in graph.nodes()}
        else:
            degrees = dict(graph.degree())
        
        # Normalize if requested
        if normalize and degrees:
            n = graph.number_of_nodes()
            max_degree = 2 * (n - 1) if not graph.is_directed() else (n - 1)
            if max_degree > 0:
                degrees = {node: deg / max_degree for node, deg in degrees.items()}
        
        yield (t_start, t_end, degrees)
