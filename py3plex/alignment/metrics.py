"""Metrics for multilayer network alignment and comparison.

This module provides functions to compute similarity metrics between nodes
and compare aligned multilayer networks.
"""

from typing import Dict, Hashable, Optional

import numpy as np

from py3plex.core import multinet


def cosine_similarity_matrix(A: np.ndarray, B: np.ndarray) -> np.ndarray:
    """
    Compute cosine similarity between rows of A and rows of B.

    Parameters
    ----------
    A : np.ndarray
        Shape (n_a, d), feature matrix for nodes of network A.
    B : np.ndarray
        Shape (n_b, d), feature matrix for nodes of network B.

    Returns
    -------
    S : np.ndarray
        Shape (n_a, n_b), where S[i, j] is the cosine similarity
        between A[i, :] and B[j, :].

    Notes
    -----
    - If a row has zero norm, treat its similarity with any other vector as 0.0.

    Examples
    --------
    >>> A = np.array([[1, 0], [0, 1]])
    >>> B = np.array([[1, 0], [1, 1]])
    >>> S = cosine_similarity_matrix(A, B)
    >>> S.shape
    (2, 2)
    >>> np.isclose(S[0, 0], 1.0)
    True
    """
    # Compute norms
    norms_A = np.linalg.norm(A, axis=1, keepdims=True)
    norms_B = np.linalg.norm(B, axis=1, keepdims=True)

    # Handle zero norms by replacing with 1 (will result in zero similarity)
    norms_A = np.where(norms_A == 0, 1.0, norms_A)
    norms_B = np.where(norms_B == 0, 1.0, norms_B)

    # Normalize rows
    A_norm = A / norms_A
    B_norm = B / norms_B

    # Set rows with originally zero norms to zero
    A_norm[np.linalg.norm(A, axis=1) == 0] = 0.0
    B_norm[np.linalg.norm(B, axis=1) == 0] = 0.0

    # Compute similarity matrix
    S = A_norm @ B_norm.T

    # Clamp to [-1, 1] to handle numerical noise
    S = np.clip(S, -1.0, 1.0)

    return S


def edge_agreement(
    net_a: "multinet.multi_layer_network",
    net_b: "multinet.multi_layer_network",
    node_mapping: Dict[Hashable, Hashable],
    layer_mapping: Optional[Dict[str, str]] = None,
) -> float:
    """
    Compute the edge agreement score between two aligned multilayer networks.

    Edge agreement measures the fraction of edges in network A that have a
    corresponding edge in network B under the given alignment.

    Parameters
    ----------
    net_a : multinet.multi_layer_network
        The first multilayer network.
    net_b : multinet.multi_layer_network
        The second multilayer network.
    node_mapping : Dict[Hashable, Hashable]
        Mapping from node IDs in network A to node IDs in network B.
    layer_mapping : Dict[str, str] | None
        Mapping from layer names in network A to layer names in network B.
        If None, uses identity mapping on the intersection of layer names.

    Returns
    -------
    score : float
        Edge agreement score in [0, 1]. Returns 0.0 if network A has no edges.

    Examples
    --------
    >>> from py3plex.core import multinet
    >>> net_a = multinet.multi_layer_network(directed=False)
    >>> net_a.add_edges([
    ...     {'source': 'A', 'target': 'B', 'source_type': 'L1', 'target_type': 'L1'},
    ... ])
    <multi_layer_network: type=multilayer, directed=False, nodes=2, edges=1, layers=1>
    >>> net_b = multinet.multi_layer_network(directed=False)
    >>> net_b.add_edges([
    ...     {'source': 'X', 'target': 'Y', 'source_type': 'L1', 'target_type': 'L1'},
    ... ])
    <multi_layer_network: type=multilayer, directed=False, nodes=2, edges=1, layers=1>
    >>> mapping = {'A': 'X', 'B': 'Y'}
    >>> score = edge_agreement(net_a, net_b, mapping)
    >>> score == 1.0
    True
    """
    # Build layer mapping if not provided
    if layer_mapping is None:
        layers_a = set(net_a.layers)
        layers_b = set(net_b.layers)
        common_layers = layers_a & layers_b
        layer_mapping = {layer: layer for layer in common_layers}

    # Build set of edges in network B for fast lookup
    edges_b = set()
    for edge in net_b.get_edges():
        source_node, target_node = edge[0], edge[1]
        if isinstance(source_node, tuple) and len(source_node) >= 2:
            src_id, src_layer = source_node[0], source_node[1]
        else:
            src_id, src_layer = source_node, None
        if isinstance(target_node, tuple) and len(target_node) >= 2:
            tgt_id, tgt_layer = target_node[0], target_node[1]
        else:
            tgt_id, tgt_layer = target_node, None

        # Store edge as frozenset for undirected comparison
        edges_b.add(frozenset([
            (src_id, src_layer),
            (tgt_id, tgt_layer),
        ]))

    # Count matching edges
    total_edges_a = 0
    matching_edges = 0

    for edge in net_a.get_edges():
        source_node, target_node = edge[0], edge[1]
        if isinstance(source_node, tuple) and len(source_node) >= 2:
            src_id, src_layer = source_node[0], source_node[1]
        else:
            src_id, src_layer = source_node, None
        if isinstance(target_node, tuple) and len(target_node) >= 2:
            tgt_id, tgt_layer = target_node[0], target_node[1]
        else:
            tgt_id, tgt_layer = target_node, None

        total_edges_a += 1

        # Map node IDs and layer
        mapped_src = node_mapping.get(src_id)
        mapped_tgt = node_mapping.get(tgt_id)
        mapped_src_layer = layer_mapping.get(src_layer) if src_layer else None
        mapped_tgt_layer = layer_mapping.get(tgt_layer) if tgt_layer else None

        if mapped_src is None or mapped_tgt is None:
            continue

        # Check if mapped edge exists in B
        mapped_edge = frozenset([
            (mapped_src, mapped_src_layer),
            (mapped_tgt, mapped_tgt_layer),
        ])

        if mapped_edge in edges_b:
            matching_edges += 1

    if total_edges_a == 0:
        return 0.0

    return matching_edges / total_edges_a


def degree_correlation(
    net_a: "multinet.multi_layer_network",
    net_b: "multinet.multi_layer_network",
    node_mapping: Dict[Hashable, Hashable],
) -> float:
    """
    Compute the Pearson correlation of node degrees between aligned networks.

    For each pair of aligned nodes (a, b), computes the correlation between
    their total degrees across both networks.

    Parameters
    ----------
    net_a : multinet.multi_layer_network
        The first multilayer network.
    net_b : multinet.multi_layer_network
        The second multilayer network.
    node_mapping : Dict[Hashable, Hashable]
        Mapping from node IDs in network A to node IDs in network B.

    Returns
    -------
    correlation : float
        Pearson correlation coefficient in [-1, 1]. Returns 0.0 if there are
        fewer than 2 aligned nodes or if variance is zero.

    Examples
    --------
    >>> from py3plex.core import multinet
    >>> net_a = multinet.multi_layer_network(directed=False)
    >>> net_a.add_edges([
    ...     {'source': 'A', 'target': 'B', 'source_type': 'L1', 'target_type': 'L1'},
    ...     {'source': 'B', 'target': 'C', 'source_type': 'L1', 'target_type': 'L1'},
    ... ])
    <multi_layer_network: type=multilayer, directed=False, nodes=3, edges=2, layers=1>
    >>> net_b = multinet.multi_layer_network(directed=False)
    >>> net_b.add_edges([
    ...     {'source': 'X', 'target': 'Y', 'source_type': 'L1', 'target_type': 'L1'},
    ...     {'source': 'Y', 'target': 'Z', 'source_type': 'L1', 'target_type': 'L1'},
    ... ])
    <multi_layer_network: type=multilayer, directed=False, nodes=3, edges=2, layers=1>
    >>> mapping = {'A': 'X', 'B': 'Y', 'C': 'Z'}
    >>> corr = degree_correlation(net_a, net_b, mapping)
    >>> corr == 1.0
    True
    """
    # Compute degrees for network A
    degrees_a: Dict[Hashable, int] = {}
    for edge in net_a.get_edges():
        source_node, target_node = edge[0], edge[1]
        if isinstance(source_node, tuple) and len(source_node) >= 2:
            src_id = source_node[0]
        else:
            src_id = source_node
        if isinstance(target_node, tuple) and len(target_node) >= 2:
            tgt_id = target_node[0]
        else:
            tgt_id = target_node

        degrees_a[src_id] = degrees_a.get(src_id, 0) + 1
        degrees_a[tgt_id] = degrees_a.get(tgt_id, 0) + 1

    # Compute degrees for network B
    degrees_b: Dict[Hashable, int] = {}
    for edge in net_b.get_edges():
        source_node, target_node = edge[0], edge[1]
        if isinstance(source_node, tuple) and len(source_node) >= 2:
            src_id = source_node[0]
        else:
            src_id = source_node
        if isinstance(target_node, tuple) and len(target_node) >= 2:
            tgt_id = target_node[0]
        else:
            tgt_id = target_node

        degrees_b[src_id] = degrees_b.get(src_id, 0) + 1
        degrees_b[tgt_id] = degrees_b.get(tgt_id, 0) + 1

    # Collect aligned degree pairs
    deg_pairs_a = []
    deg_pairs_b = []

    for node_a, node_b in node_mapping.items():
        deg_a = degrees_a.get(node_a, 0)
        deg_b = degrees_b.get(node_b, 0)
        deg_pairs_a.append(deg_a)
        deg_pairs_b.append(deg_b)

    if len(deg_pairs_a) < 2:
        return 0.0

    deg_arr_a = np.array(deg_pairs_a, dtype=np.float64)
    deg_arr_b = np.array(deg_pairs_b, dtype=np.float64)

    # Compute Pearson correlation
    std_a, std_b = deg_arr_a.std(), deg_arr_b.std()

    if std_a == 0 or std_b == 0:
        return 0.0

    correlation = np.corrcoef(deg_arr_a, deg_arr_b)[0, 1]

    # Handle NaN (can occur with constant arrays)
    if np.isnan(correlation):
        return 0.0

    return float(correlation)
