"""Witness subgraph extraction for counterexamples.

This module implements ego subgraph extraction around violating nodes,
with support for multilayer networks and size limits.
"""

from typing import Any, Dict, List, Optional, Set, Tuple


def _parse_edge(edge: Any) -> Tuple[Any, Any, str, str, float]:
    """Parse edge tuple into components.

    Handles two formats:
    - ((src, src_layer), (tgt, tgt_layer), weight)
    - ((src, src_layer), (tgt, tgt_layer))

    Returns:
        Tuple of (src, tgt, src_layer, tgt_layer, weight)
    """
    src_tuple = edge[0]
    tgt_tuple = edge[1]

    src = src_tuple[0]
    src_layer = src_tuple[1]
    tgt = tgt_tuple[0]
    tgt_layer = tgt_tuple[1]

    weight = edge[2] if len(edge) > 2 else 1.0

    return src, tgt, src_layer, tgt_layer, weight


def ego_subgraph(
    network: Any,
    center_node: Any,
    center_layer: str,
    radius: int = 2,
    layers: Optional[List[str]] = None,
    max_nodes: Optional[int] = None,
    strategy: str = "top_neighbors",
) -> Any:
    """Extract ego subgraph around a center node.

    Args:
        network: py3plex multi_layer_network object
        center_node: Node identifier
        center_layer: Layer of center node
        radius: Radius of ego network (default: 2)
        layers: Layers to include (None = all layers where node appears)
        max_nodes: Maximum nodes in witness (enforces size limit)
        strategy: How to select nodes if max_nodes exceeded ("top_neighbors")

    Returns:
        New multi_layer_network containing the ego subgraph
    """
    from py3plex.core import multinet

    # Determine relevant layers
    if layers is None:
        # Use all layers where center node appears
        layers = _get_node_layers(network, center_node)

    # Collect nodes at each radius level
    nodes_by_distance = _bfs_multilayer(
        network, center_node, center_layer, radius, layers
    )

    # Flatten to set of (node, layer) tuples
    all_nodes = set()
    for distance, node_set in nodes_by_distance.items():
        all_nodes.update(node_set)

    # Enforce max_nodes limit if needed
    if max_nodes is not None and len(all_nodes) > max_nodes:
        all_nodes = _trim_nodes(
            network, all_nodes, center_node, center_layer, max_nodes, strategy
        )

    # Build witness subgraph
    witness = multinet.multi_layer_network(directed=network.directed)

    # Add nodes
    for node, layer in all_nodes:
        witness.add_nodes([{"source": node, "type": layer}])

    # Add edges between included nodes
    for edge in network.get_edges():
        src, tgt, src_layer, tgt_layer, weight = _parse_edge(edge)

        if (src, src_layer) in all_nodes and (tgt, tgt_layer) in all_nodes:
            edge_dict = {
                "source": src,
                "target": tgt,
                "source_type": src_layer,
                "target_type": tgt_layer,
                "weight": weight,
            }
            witness.add_edges([edge_dict])

    return witness


def _get_node_layers(network: Any, node: Any) -> List[str]:
    """Get all layers where a node appears.

    Args:
        network: py3plex multi_layer_network object
        node: Node identifier

    Returns:
        List of layer names
    """
    layers = set()
    for n in network.get_nodes():
        if n[0] == node:
            layers.add(n[1])
    return sorted(list(layers))


def _bfs_multilayer(
    network: Any,
    start_node: Any,
    start_layer: str,
    max_distance: int,
    layers: List[str],
) -> Dict[int, Set[Tuple[Any, str]]]:
    """BFS on multilayer network to find nodes at each distance.

    Args:
        network: py3plex multi_layer_network object
        start_node: Starting node
        start_layer: Starting layer
        max_distance: Maximum distance to explore
        layers: Layers to include

    Returns:
        Dict mapping distance -> set of (node, layer) tuples
    """
    from collections import deque

    # Convert layers to set for fast lookup
    layer_set = set(layers)

    # Track visited and distance
    visited = set()
    nodes_by_distance = {i: set() for i in range(max_distance + 1)}

    # BFS queue: (node, layer, distance)
    queue = deque([(start_node, start_layer, 0)])
    visited.add((start_node, start_layer))
    nodes_by_distance[0].add((start_node, start_layer))

    while queue:
        node, layer, dist = queue.popleft()

        if dist >= max_distance:
            continue

        # Explore neighbors in multilayer network
        for edge in network.get_edges():
            src, tgt, src_layer, tgt_layer, weight = _parse_edge(edge)

            # Check if this edge involves current node
            next_node = None
            next_layer = None

            if src == node and src_layer == layer:
                next_node = tgt
                next_layer = tgt_layer
            elif not network.directed and tgt == node and tgt_layer == layer:
                next_node = src
                next_layer = src_layer

            # Add to queue if valid and not visited
            if next_node is not None and next_layer in layer_set:
                key = (next_node, next_layer)
                if key not in visited:
                    visited.add(key)
                    nodes_by_distance[dist + 1].add(key)
                    queue.append((next_node, next_layer, dist + 1))

    return nodes_by_distance


def _trim_nodes(
    network: Any,
    nodes: Set[Tuple[Any, str]],
    center_node: Any,
    center_layer: str,
    max_nodes: int,
    strategy: str,
) -> Set[Tuple[Any, str]]:
    """Trim node set to meet size limit.

    Args:
        network: py3plex multi_layer_network object
        nodes: Set of (node, layer) tuples
        center_node: Center node (must keep)
        center_layer: Center layer
        max_nodes: Target size
        strategy: Selection strategy ("top_neighbors")

    Returns:
        Trimmed set of nodes
    """
    # Always keep center
    must_keep = {(center_node, center_layer)}
    candidates = nodes - must_keep

    if len(must_keep) + len(candidates) <= max_nodes:
        return nodes

    # Strategy: keep nodes with highest degree (weighted by edge weight if available)
    if strategy == "top_neighbors":
        # Score each candidate by its weighted degree
        scores = {}
        for node, layer in candidates:
            score = 0.0
            for edge in network.get_edges():
                src, tgt, src_layer, tgt_layer, weight = _parse_edge(edge)

                if (src == node and src_layer == layer) or (
                    tgt == node and tgt_layer == layer
                ):
                    score += weight

            scores[(node, layer)] = score

        # Sort by score descending, then by (node, layer) for determinism
        sorted_candidates = sorted(
            candidates, key=lambda x: (-scores[x], str(x[0]), x[1])
        )

        # Take top (max_nodes - 1) candidates
        keep_count = max_nodes - len(must_keep)
        kept = set(sorted_candidates[:keep_count])

        return must_keep | kept

    else:
        # Fallback: arbitrary but deterministic selection
        sorted_candidates = sorted(candidates, key=lambda x: (str(x[0]), x[1]))
        keep_count = max_nodes - len(must_keep)
        return must_keep | set(sorted_candidates[:keep_count])
