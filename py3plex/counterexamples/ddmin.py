"""Delta debugging minimization for counterexample witnesses.

This module implements ddmin algorithm to minimize witness subgraphs
while preserving the violation property.
"""

from typing import Any, Callable, List, Set, Tuple


def _parse_edge(edge: Any) -> Tuple[Any, Any, str, str, float]:
    """Parse edge tuple into components.

    Handles format: ((src, src_layer), (tgt, tgt_layer), weight)

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


def minimize_edges(
    subgraph: Any,
    violation_tester: Callable[[Any], bool],
    max_tests: int = 200,
    seed: int = 42,
) -> Tuple[Any, int, bool]:
    """Minimize witness by removing edges using ddmin.

    Args:
        subgraph: py3plex multi_layer_network witness
        violation_tester: Function that checks if violation still exists
        max_tests: Maximum violation tests allowed
        seed: Random seed for tie-breaking (determinism)

    Returns:
        Tuple of (minimized_subgraph, tests_used, is_minimal)
    """

    # Get all edges in stable order
    edges = _get_edges_sorted(subgraph)

    if len(edges) == 0:
        # No edges to remove
        return subgraph, 0, True

    # Track tests used
    tests_used = [0]  # Use list to allow mutation in nested function

    def test_candidate(candidate_edges: List[Tuple]) -> bool:
        """Test if candidate edge set still violates."""
        if tests_used[0] >= max_tests:
            return False  # Budget exhausted

        tests_used[0] += 1

        # Build candidate subgraph
        candidate = _build_subgraph_from_edges(subgraph, candidate_edges)

        # Test violation
        return violation_tester(candidate)

    # Run ddmin
    minimal_edges = _ddmin(edges, test_candidate, max_tests - tests_used[0])

    # Check if we used all budget
    is_minimal = tests_used[0] < max_tests

    # Build final subgraph
    result = _build_subgraph_from_edges(subgraph, minimal_edges)

    return result, tests_used[0], is_minimal


def _get_edges_sorted(network: Any) -> List[Tuple]:
    """Get all edges from network in stable sorted order.

    Args:
        network: py3plex multi_layer_network object

    Returns:
        Sorted list of edge tuples
    """
    edges = []
    for edge in network.get_edges():
        # Parse and normalize
        src, tgt, src_layer, tgt_layer, weight = _parse_edge(edge)
        edges.append((src, tgt, src_layer, tgt_layer, weight))

    # Sort for determinism: by (src, tgt, src_layer, tgt_layer)
    edges.sort(key=lambda e: (str(e[0]), str(e[1]), e[2], e[3]))

    return edges


def _build_subgraph_from_edges(template: Any, edges: List[Tuple]) -> Any:
    """Build subgraph containing only specified edges.

    Args:
        template: Template network (for directedness)
        edges: List of edge tuples to include

    Returns:
        New multi_layer_network with specified edges
    """
    from py3plex.core import multinet

    # Collect nodes from edges
    nodes = set()
    for edge in edges:
        src, tgt, src_layer, tgt_layer = edge[0], edge[1], edge[2], edge[3]
        nodes.add((src, src_layer))
        nodes.add((tgt, tgt_layer))

    # Build network
    result = multinet.multi_layer_network(directed=template.directed)

    # Add nodes
    for node, layer in sorted(nodes, key=lambda x: (str(x[0]), x[1])):
        result.add_nodes([{"source": node, "type": layer}])

    # Add edges
    edge_dicts = []
    for edge in edges:
        src, tgt, src_layer, tgt_layer, weight = edge
        edge_dict = {
            "source": src,
            "target": tgt,
            "source_type": src_layer,
            "target_type": tgt_layer,
            "weight": weight,
        }
        edge_dicts.append(edge_dict)

    if edge_dicts:
        result.add_edges(edge_dicts)

    return result


def _ddmin(
    items: List[Any], test_fn: Callable[[List[Any]], bool], budget: int
) -> List[Any]:
    """Delta debugging algorithm for minimization.

    Args:
        items: List of items to minimize
        test_fn: Function that returns True if subset still satisfies property
        budget: Remaining test budget

    Returns:
        Minimal subset of items
    """
    if budget <= 0 or len(items) <= 1:
        return items

    n = len(items)
    chunk_size = max(1, n // 2)

    while chunk_size >= 1 and budget > 0:
        # Try removing each chunk
        chunks = _split_into_chunks(items, chunk_size)
        reduced = False

        for i, chunk in enumerate(chunks):
            # Create complement (all items except chunk)
            complement = []
            for j, other_chunk in enumerate(chunks):
                if j != i:
                    complement.extend(other_chunk)

            # Test complement
            if test_fn(complement):
                # Success: complement is sufficient
                items = complement
                budget -= 1
                reduced = True
                break  # Start over with new items

            budget -= 1
            if budget <= 0:
                return items

        if reduced:
            # Start over with smaller item set
            n = len(items)
            chunk_size = max(1, n // 2)
        else:
            # No reduction at this granularity; try finer chunks
            if chunk_size == 1:
                break  # Can't go finer
            chunk_size = max(1, chunk_size // 2)

    return items


def _split_into_chunks(items: List[Any], chunk_size: int) -> List[List[Any]]:
    """Split items into chunks of approximately chunk_size.

    Args:
        items: List of items
        chunk_size: Target chunk size

    Returns:
        List of chunks
    """
    chunks = []
    for i in range(0, len(items), chunk_size):
        chunks.append(items[i : i + chunk_size])
    return chunks


def minimize_nodes(
    subgraph: Any,
    violation_tester: Callable[[Any], bool],
    must_keep: Set[Tuple[Any, str]],
    max_tests: int = 200,
) -> Tuple[Any, int, bool]:
    """Minimize witness by removing nodes (and incident edges).

    Args:
        subgraph: py3plex multi_layer_network witness
        violation_tester: Function that checks if violation still exists
        must_keep: Set of (node, layer) tuples that must be kept
        max_tests: Maximum violation tests allowed

    Returns:
        Tuple of (minimized_subgraph, tests_used, is_minimal)
    """

    # Get all nodes except must_keep
    all_nodes = set()
    for node in subgraph.get_nodes():
        all_nodes.add((node[0], node[1]))

    removable = all_nodes - must_keep
    nodes_list = sorted(list(removable), key=lambda x: (str(x[0]), x[1]))

    if len(nodes_list) == 0:
        # No nodes to remove
        return subgraph, 0, True

    # Track tests
    tests_used = [0]

    def test_candidate(candidate_nodes: List[Tuple]) -> bool:
        """Test if candidate node set still violates."""
        if tests_used[0] >= max_tests:
            return False

        tests_used[0] += 1

        # Build subgraph with must_keep + candidate_nodes
        keep_set = must_keep | set(candidate_nodes)
        candidate = _build_subgraph_from_nodes(subgraph, keep_set)

        return violation_tester(candidate)

    # Run ddmin
    minimal_nodes = _ddmin(nodes_list, test_candidate, max_tests - tests_used[0])

    is_minimal = tests_used[0] < max_tests

    # Build final subgraph
    final_nodes = must_keep | set(minimal_nodes)
    result = _build_subgraph_from_nodes(subgraph, final_nodes)

    return result, tests_used[0], is_minimal


def _build_subgraph_from_nodes(template: Any, nodes: Set[Tuple[Any, str]]) -> Any:
    """Build subgraph containing only specified nodes and their edges.

    Args:
        template: Template network (for edges and directedness)
        nodes: Set of (node, layer) tuples to include

    Returns:
        New multi_layer_network with specified nodes
    """
    from py3plex.core import multinet

    result = multinet.multi_layer_network(directed=template.directed)

    # Add nodes
    for node, layer in sorted(nodes, key=lambda x: (str(x[0]), x[1])):
        result.add_nodes([{"source": node, "type": layer}])

    # Add edges between included nodes
    edge_dicts = []
    for edge in template.get_edges():
        src, tgt, src_layer, tgt_layer, weight = _parse_edge(edge)

        if (src, src_layer) in nodes and (tgt, tgt_layer) in nodes:
            edge_dict = {
                "source": src,
                "target": tgt,
                "source_type": src_layer,
                "target_type": tgt_layer,
                "weight": weight,
            }
            edge_dicts.append(edge_dict)

    if edge_dicts:
        result.add_edges(edge_dicts)

    return result
