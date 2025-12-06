"""Alignment solvers for multilayer network alignment.

This module provides algorithms for computing node alignments between
two multilayer networks.
"""

from typing import Dict, Hashable, Iterable, List, Literal, NamedTuple, Optional

import numpy as np
from scipy.optimize import linear_sum_assignment

from py3plex.core import multinet

from .features import multilayer_node_features
from .metrics import cosine_similarity_matrix


class AlignmentResult(NamedTuple):
    """
    Result of aligning two multilayer networks.

    Attributes
    ----------
    node_mapping : Dict[Hashable, Hashable]
        Mapping from node IDs in network A to node IDs in network B.
        Keys are node identifiers from the first network, values from the second.

    layer_mapping : Optional[Dict[str, str]]
        Mapping from layer names in network A to layer names in network B.
        For the MVP, this is an identity mapping on the intersection
        of layer names, or None.

    score : float
        Overall alignment quality score (mean similarity of matched feature vectors).

    similarity_matrix : Optional[np.ndarray]
        Full similarity matrix between node features of net_a and net_b,
        shape (n_a, n_b). Useful for inspection and debugging.
    """

    node_mapping: Dict[Hashable, Hashable]
    layer_mapping: Optional[Dict[str, str]]
    score: float
    similarity_matrix: Optional[np.ndarray]


def align_networks(
    net_a: "multinet.multi_layer_network",
    net_b: "multinet.multi_layer_network",
    method: Literal["feature_hungarian"] = "feature_hungarian",
    layers: Optional[Iterable[str]] = None,
) -> AlignmentResult:
    """
    Align two multilayer networks using simple feature-based Hungarian matching.

    For method="feature_hungarian":
    --------------------------------
    1. Compute node features for net_a and net_b via `multilayer_node_features`.
    2. Stack features into matrices:
           F_a : (n_a, d)
           F_b : (n_b, d)
    3. Compute cosine similarity matrix S = cosine_similarity_matrix(F_a, F_b).
    4. Construct cost matrix C = -S (we want to maximize similarity).
    5. Solve assignment using scipy.optimize.linear_sum_assignment(C).
    6. Build a node_mapping:
           nodes_a[i] -> nodes_b[j] where (i, j) is in the assignment.
    7. Define score = mean of matched similarities S[i, j].
    8. For layer_mapping:
           Uses identity mapping for intersection of layer names.

    Parameters
    ----------
    net_a : multinet.multi_layer_network
        The first multilayer network.
    net_b : multinet.multi_layer_network
        The second multilayer network.
    method : Literal["feature_hungarian"]
        The alignment method to use. Currently only "feature_hungarian" is supported.
    layers : Optional[Iterable[str]]
        Layers to consider for feature computation. If None, uses all layers.

    Returns
    -------
    AlignmentResult
        Named tuple containing the node mapping, layer mapping, alignment score,
        and similarity matrix.

    Raises
    ------
    ValueError
        If the number of nodes in net_a does not equal the number of nodes in net_b.
        If an unsupported method is specified.

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
    >>> result = align_networks(net_a, net_b)
    >>> len(result.node_mapping)
    2
    >>> 0.0 <= result.score <= 1.0
    True
    """
    if method != "feature_hungarian":
        raise ValueError(
            f"Unsupported alignment method: '{method}'. "
            f"Currently only 'feature_hungarian' is supported."
        )

    # Determine layers to use
    if layers is None:
        # Use the union of layers from both networks for feature computation
        layers_a = set(net_a.layers)
        layers_b = set(net_b.layers)
        layer_list = sorted(layers_a | layers_b)
    else:
        layer_list = list(layers)

    # Compute node features
    features_a = multilayer_node_features(net_a, layers=layer_list)
    features_b = multilayer_node_features(net_b, layers=layer_list)

    # Get node lists
    nodes_a: List[Hashable] = list(features_a.keys())
    nodes_b: List[Hashable] = list(features_b.keys())

    n_a = len(nodes_a)
    n_b = len(nodes_b)

    # For MVP, require equal sizes
    if n_a != n_b:
        raise ValueError(
            f"Network size mismatch: net_a has {n_a} unique nodes, "
            f"net_b has {n_b} unique nodes. For the MVP version, "
            f"both networks must have the same number of nodes."
        )

    if n_a == 0:
        return AlignmentResult(
            node_mapping={},
            layer_mapping=None,
            score=0.0,
            similarity_matrix=None,
        )

    # Stack features into matrices
    F_a = np.vstack([features_a[node] for node in nodes_a])
    F_b = np.vstack([features_b[node] for node in nodes_b])

    # Compute cosine similarity matrix
    S = cosine_similarity_matrix(F_a, F_b)

    # Construct cost matrix (negate for maximization)
    C = -S

    # Solve Hungarian assignment
    row_ind, col_ind = linear_sum_assignment(C)

    # Build node mapping
    node_mapping: Dict[Hashable, Hashable] = {}
    matched_similarities: List[float] = []

    for i, j in zip(row_ind, col_ind):
        node_mapping[nodes_a[i]] = nodes_b[j]
        matched_similarities.append(S[i, j])

    # Compute alignment score
    score = float(np.mean(matched_similarities)) if matched_similarities else 0.0

    # Build layer mapping (identity on intersection)
    layers_a = set(net_a.layers)
    layers_b = set(net_b.layers)
    common_layers = layers_a & layers_b
    layer_mapping = {layer: layer for layer in common_layers} if common_layers else None

    return AlignmentResult(
        node_mapping=node_mapping,
        layer_mapping=layer_mapping,
        score=score,
        similarity_matrix=S,
    )
