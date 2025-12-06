"""
Explainable centrality for multilayer networks.

Provides human-readable explanations of why certain nodes have high/low
centrality scores by decomposing scores into interpretable components:
- Per-layer degree contributions
- Inter-layer connectivity
- Neighborhood structure

This is a heuristic approach focused on interpretability, not a full
Shapley analysis.

Authors: py3plex contributors
Date: 2025
"""

from typing import Any, Dict, Tuple, Union
from collections import defaultdict
import networkx as nx


def explain_node_centrality(
    graph: Any,
    node: Union[str, Tuple[str, str]],
    centrality_scores: Dict[Union[str, Tuple[str, str]], float],
    method: str = "degree",
) -> Dict[str, Any]:
    """
    Provide a structured explanation for a node's centrality.

    Args:
        graph: Multilayer network object (py3plex multi_layer_network)
        node: Node identifier (string or (node_id, layer) tuple)
        centrality_scores: Dictionary mapping nodes to centrality scores
        method: Centrality method used ("degree", "betweenness", "eigenvector", "pagerank")

    Returns:
        Dictionary with explanation fields:
            - "score": The node's centrality score
            - "layer_breakdown": Contribution estimate per layer {layer: value}
            - "degree_per_layer": Degree in each layer {layer: degree}
            - "num_interlayer_edges": Count of edges crossing layers
            - "local_motifs": Simple motif counts (e.g., triangles)
            - "rank": Rank among all nodes (1 = highest centrality)
            - "percentile": Percentile rank (0-100)

    Example:
        >>> from py3plex.core import multinet
        >>> net = multinet.multi_layer_network()
        >>> net.add_edges([['A', 'L1', 'B', 'L1', 1]], input_type='list')
        >>> scores = {'A': 0.5, 'B': 0.5}
        >>> explain_node_centrality(net, 'A', scores, method='degree')
        {
            'score': 0.5,
            'layer_breakdown': {'L1': 1},
            'degree_per_layer': {'L1': 1},
            'num_interlayer_edges': 0,
            'local_motifs': {'triangles': 0},
            'rank': 1,
            'percentile': 50.0
        }
    """
    # Validate inputs
    if node not in centrality_scores:
        raise ValueError(f"Node {node} not found in centrality_scores")

    score = centrality_scores[node]

    # Get core network for analysis
    if hasattr(graph, "core_network") and graph.core_network is not None:
        G = graph.core_network
    else:
        raise ValueError("Network has no core_network attribute")

    # Initialize explanation dictionary
    explanation = {
        "score": score,
        "layer_breakdown": {},
        "degree_per_layer": {},
        "num_interlayer_edges": 0,
        "local_motifs": {},
    }

    # Extract node information
    if isinstance(node, tuple):
        node_id, _ = node
    else:
        node_id = node

    # Analyze per-layer contributions
    explanation["degree_per_layer"] = _compute_degree_per_layer(G, node_id)
    explanation["layer_breakdown"] = _compute_layer_contributions(
        G, node_id, method, centrality_scores
    )
    explanation["num_interlayer_edges"] = _count_interlayer_edges(G, node_id)

    # Compute local motifs (triangles)
    explanation["local_motifs"] = _compute_local_motifs(G, node)

    # Compute ranking information
    # Sort by score descending, then by node for stable ordering
    sorted_items = sorted(centrality_scores.items(), key=lambda x: (-x[1], str(x[0])))

    # Find rank (handle ties by giving same rank to same scores)
    rank = 1
    for i, (n, s) in enumerate(sorted_items):
        if i > 0 and sorted_items[i - 1][1] != s:
            rank = i + 1
        if n == node:
            break

    # Percentile calculation
    num_nodes = len(centrality_scores)
    percentile = (num_nodes - rank) / num_nodes * 100 if num_nodes > 1 else 0.0

    explanation["rank"] = rank
    explanation["percentile"] = round(percentile, 2)

    return explanation


def explain_top_k_central_nodes(
    graph: Any,
    centrality_scores: Dict[Union[str, Tuple[str, str]], float],
    method: str = "degree",
    k: int = 5,
) -> Dict[Union[str, Tuple[str, str]], Dict[str, Any]]:
    """
    Return explanations for the top-k nodes by centrality.

    Args:
        graph: Multilayer network object
        centrality_scores: Dictionary mapping nodes to centrality scores
        method: Centrality method used ("degree", "betweenness", "eigenvector", "pagerank")
        k: Number of top nodes to explain (default: 5)

    Returns:
        Dictionary mapping node -> explanation_dict for top-k nodes

    Example:
        >>> from py3plex.core import multinet
        >>> net = multinet.multi_layer_network()
        >>> net.add_edges([['A', 'L1', 'B', 'L1', 1], ['B', 'L1', 'C', 'L1', 1]], input_type='list')
        >>> scores = {'A': 0.3, 'B': 0.6, 'C': 0.3}
        >>> explanations = explain_top_k_central_nodes(net, scores, k=2)
        >>> list(explanations.keys())
        ['B', 'A']  # or ['B', 'C'] depending on tie-breaking
    """
    # Sort nodes by centrality score (descending)
    sorted_nodes = sorted(centrality_scores.items(), key=lambda x: x[1], reverse=True)

    # Get top-k nodes
    top_k_nodes = sorted_nodes[:k]

    # Generate explanations for each top-k node
    explanations = {}
    for node, score in top_k_nodes:
        try:
            explanations[node] = explain_node_centrality(
                graph, node, centrality_scores, method
            )
        except Exception as e:
            # If explanation fails, still include basic info
            explanations[node] = {"score": score, "error": str(e)}

    return explanations


# ============================================================================
# Helper Functions
# ============================================================================


def _compute_degree_per_layer(
    G: nx.Graph,
    node_id: str,
) -> Dict[str, int]:
    """
    Compute degree of a node in each layer.

    Args:
        G: NetworkX graph (core_network)
        node_id: Base node identifier

    Returns:
        Dictionary mapping layer -> degree
    """
    degree_per_layer = defaultdict(int)

    # Iterate through all edges to count per-layer degrees
    for node in G.nodes():
        if isinstance(node, tuple):
            n_id, n_layer = node
            if n_id == node_id:
                # Count edges in this layer
                neighbors = list(G.neighbors(node))
                layer_neighbors = [
                    n for n in neighbors if isinstance(n, tuple) and n[1] == n_layer
                ]
                degree_per_layer[n_layer] = len(layer_neighbors)
        else:
            # Single-layer or flat network
            if node == node_id:
                degree_per_layer["default"] = G.degree(node)

    return dict(degree_per_layer)


def _compute_layer_contributions(
    G: nx.Graph,
    node_id: str,
    method: str,
    centrality_scores: Dict[Union[str, Tuple[str, str]], float],
) -> Dict[str, float]:
    """
    Estimate per-layer contributions to centrality.

    This is a heuristic approximation:
    - For degree: exact per-layer degree
    - For betweenness: approximate by degree ratio
    - For eigenvector/pagerank: approximate by neighbor centrality

    Args:
        G: NetworkX graph
        node_id: Node identifier
        method: Centrality method
        centrality_scores: Full centrality scores

    Returns:
        Dictionary mapping layer -> contribution estimate
    """
    contributions = defaultdict(float)

    if method == "degree":
        # For degree, contributions are exact
        degree_per_layer = _compute_degree_per_layer(G, node_id)
        return degree_per_layer

    elif method == "betweenness":
        # Approximate: proportional to degree in each layer
        degree_per_layer = _compute_degree_per_layer(G, node_id)
        total_degree = sum(degree_per_layer.values())

        if total_degree > 0:
            for layer, degree in degree_per_layer.items():
                contributions[layer] = degree / total_degree
        return dict(contributions)

    elif method in ["eigenvector", "pagerank"]:
        # Approximate: sum of neighbor centralities per layer
        for node in G.nodes():
            if isinstance(node, tuple):
                n_id, n_layer = node
                if n_id == node_id:
                    neighbors = list(G.neighbors(node))
                    layer_neighbors = [
                        n for n in neighbors if isinstance(n, tuple) and n[1] == n_layer
                    ]
                    # Sum neighbor centralities
                    neighbor_sum = sum(
                        centrality_scores.get(n, 0) for n in layer_neighbors
                    )
                    contributions[n_layer] = neighbor_sum
            else:
                if node == node_id:
                    neighbors = list(G.neighbors(node))
                    neighbor_sum = sum(centrality_scores.get(n, 0) for n in neighbors)
                    contributions["default"] = neighbor_sum

    return dict(contributions)


def _count_interlayer_edges(G: nx.Graph, node_id: str) -> int:
    """
    Count edges that cross between layers for a given node.

    Args:
        G: NetworkX graph
        node_id: Node identifier

    Returns:
        Count of inter-layer edges
    """
    interlayer_count = 0

    for node in G.nodes():
        if isinstance(node, tuple):
            n_id, n_layer = node
            if n_id == node_id:
                for neighbor in G.neighbors(node):
                    if isinstance(neighbor, tuple):
                        neighbor_id, neighbor_layer = neighbor
                        # Inter-layer edge if layers differ
                        if neighbor_layer != n_layer:
                            interlayer_count += 1

    return interlayer_count


def _compute_local_motifs(
    G: nx.Graph,
    node: Union[str, Tuple[str, str]],
) -> Dict[str, int]:
    """
    Compute simple local motif counts (e.g., triangles).

    Args:
        G: NetworkX graph
        node: Node identifier

    Returns:
        Dictionary with motif counts (e.g., {'triangles': count})
    """
    motifs = {"triangles": 0}

    try:
        if node in G:
            # Count triangles involving this node
            # A triangle exists if two neighbors are also connected
            neighbors = set(G.neighbors(node))
            for n1 in neighbors:
                for n2 in neighbors:
                    if n1 != n2 and G.has_edge(n1, n2):
                        motifs["triangles"] += 1
            # Each triangle is counted 3 times (once per node), so divide by 2
            # (we only count from one direction)
            motifs["triangles"] = motifs["triangles"] // 2
    except Exception:
        # If triangle counting fails, return 0
        pass

    return motifs
